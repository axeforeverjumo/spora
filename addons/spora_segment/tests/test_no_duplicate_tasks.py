"""Test to ensure no duplicate task creation when confirming orders with segments."""

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestNoDuplicateTasks(TransactionCase):
    """Test suite to prevent task duplication bugs."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderSegment = self.env['sale.order.segment']
        self.Product = self.env['product.product']
        self.Partner = self.env['res.partner']

        # Create test partner
        self.partner = self.Partner.create({
            'name': 'Test Customer',
        })

        # Create service products with service_tracking
        self.product_service_1 = self.Product.create({
            'name': 'Service Product 1',
            'type': 'service',
            'list_price': 100.0,
            'service_tracking': 'task_in_project',  # Native Odoo would create tasks
        })

        self.product_service_2 = self.Product.create({
            'name': 'Service Product 2',
            'type': 'service',
            'list_price': 200.0,
            'service_tracking': 'task_in_project',
        })

    def test_no_duplicate_tasks_with_segments(self):
        """Test that confirming order creates correct number of tasks without duplicates.

        Scenario:
        - 1 root segment
        - 2 child segments
        - 2 products assigned to child segments

        Expected tasks:
        - 3 segment tasks (1 root + 2 children)
        - 2 product tasks (under child segments)
        - Total: 5 tasks

        Common bug: Native Odoo creates 2 additional root tasks for products
        (due to service_tracking), resulting in 7 tasks with broken hierarchy.
        """
        # Create sale order
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })

        # Create segment hierarchy
        root_segment = self.SaleOrderSegment.create({
            'name': 'Root Segment',
            'order_id': order.id,
            'sequence': 1,
        })

        child_segment_1 = self.SaleOrderSegment.create({
            'name': 'Child Segment 1',
            'order_id': order.id,
            'parent_id': root_segment.id,
            'sequence': 1,
        })

        child_segment_2 = self.SaleOrderSegment.create({
            'name': 'Child Segment 2',
            'order_id': order.id,
            'parent_id': root_segment.id,
            'sequence': 2,
        })

        # Create order lines and assign to segments
        line1 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_service_1.id,
            'product_uom_qty': 5.0,
            'segment_id': child_segment_1.id,
        })

        line2 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_service_2.id,
            'product_uom_qty': 10.0,
            'segment_id': child_segment_2.id,
        })

        # Confirm order
        order.action_confirm()

        # Verify tasks created
        tasks = self.env['project.task'].search([('sale_order_id', '=', order.id)])

        # Expected: 3 segments + 2 products = 5 tasks
        self.assertEqual(
            len(tasks),
            5,
            f'Expected 5 tasks (3 segments + 2 products), got {len(tasks)}'
        )

        # Verify segment tasks
        segment_tasks = tasks.filtered(lambda t: t.segment_id)
        self.assertEqual(
            len(segment_tasks),
            3,
            f'Expected 3 segment tasks, got {len(segment_tasks)}'
        )

        # Verify product tasks
        product_tasks = tasks.filtered(lambda t: t.sale_line_id and not t.segment_id)
        self.assertEqual(
            len(product_tasks),
            2,
            f'Expected 2 product tasks, got {len(product_tasks)}'
        )

        # Verify hierarchy: all product tasks should have parent
        orphan_product_tasks = product_tasks.filtered(lambda t: not t.parent_id)
        self.assertEqual(
            len(orphan_product_tasks),
            0,
            f'Found {len(orphan_product_tasks)} orphan product tasks (should have segment parent)'
        )

        # Verify root tasks: only root segment should be root
        root_tasks = tasks.filtered(lambda t: not t.parent_id)
        self.assertEqual(
            len(root_tasks),
            1,
            f'Expected 1 root task (root segment), got {len(root_tasks)}'
        )
        self.assertEqual(
            root_tasks.name,
            'Root Segment',
            f'Root task should be "Root Segment", got "{root_tasks.name}"'
        )

    def test_no_tasks_without_segments(self):
        """Test that orders without segments don't create segment tasks.

        This ensures native Odoo behavior is preserved when segments are not used.
        """
        # Create sale order without segments
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })

        # Create order line
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_service_1.id,
            'product_uom_qty': 5.0,
        })

        # Confirm order
        order.action_confirm()

        # Verify no segment tasks created
        segment_tasks = self.env['project.task'].search([
            ('sale_order_id', '=', order.id),
            ('segment_id', '!=', False)
        ])

        self.assertEqual(
            len(segment_tasks),
            0,
            f'Expected 0 segment tasks for order without segments, got {len(segment_tasks)}'
        )

    def test_idempotent_task_creation(self):
        """Test that calling _create_segment_tasks multiple times doesn't duplicate tasks."""
        # Create sale order with segment
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })

        segment = self.SaleOrderSegment.create({
            'name': 'Test Segment',
            'order_id': order.id,
            'sequence': 1,
        })

        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_service_1.id,
            'product_uom_qty': 5.0,
            'segment_id': segment.id,
        })

        # Confirm order (creates tasks)
        order.action_confirm()

        # Count tasks after first creation
        tasks_after_first = self.env['project.task'].search([('sale_order_id', '=', order.id)])
        first_count = len(tasks_after_first)

        # Call _create_segment_tasks again (should be idempotent)
        order._create_segment_tasks()

        # Count tasks again
        tasks_after_second = self.env['project.task'].search([('sale_order_id', '=', order.id)])
        second_count = len(tasks_after_second)

        self.assertEqual(
            first_count,
            second_count,
            f'Task count changed after second call: {first_count} -> {second_count}'
        )

    def test_service_tracking_restored_after_confirm(self):
        """Test that service_tracking is restored after order confirmation."""
        # Verify initial service_tracking
        self.assertEqual(
            self.product_service_1.service_tracking,
            'task_in_project',
            'Initial service_tracking should be task_in_project'
        )

        # Create and confirm order
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })

        segment = self.SaleOrderSegment.create({
            'name': 'Test Segment',
            'order_id': order.id,
        })

        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_service_1.id,
            'product_uom_qty': 5.0,
            'segment_id': segment.id,
        })

        order.action_confirm()

        # Verify service_tracking restored
        self.product_service_1.invalidate_recordset(['service_tracking'])
        self.assertEqual(
            self.product_service_1.service_tracking,
            'task_in_project',
            'service_tracking should be restored after confirm'
        )
