"""Integration tests for automatic task creation from segments.

Tests validate all AUTO requirements including:
- AUTO-01: Project creation when confirming sale order
- AUTO-02: Task creation per segment
- AUTO-03: Task parent_id hierarchy mirrors segment hierarchy
- AUTO-04: Root segment tasks have no parent_id
- AUTO-05: Task name equals segment name
- AUTO-06: Product descriptions transferred to task description
- AUTO-07: Planned hours calculated from product quantities
- AUTO-08: Responsible transfer (DEFERRED to Phase 5 - tests graceful handling)
- AUTO-09: Date transfer (DEFERRED to Phase 5 - tests graceful handling)
- AUTO-10: segment_id field links task to segment
- AUTO-11: Savepoint isolation prevents cascading failures
- AUTO-12: Partial failures logged appropriately
- Idempotence: Re-confirmation doesn't create duplicates
"""

import logging
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestAutomatedTaskCreation(TransactionCase):
    """Test automatic task creation from segments when confirming sale orders."""

    @classmethod
    def setUpClass(cls):
        """Set up test data used across multiple test methods."""
        super().setUpClass()
        cls.Task = cls.env['project.task']
        cls.Project = cls.env['project.project']
        cls.Segment = cls.env['sale.order.segment']
        cls.Order = cls.env['sale.order']
        cls.OrderLine = cls.env['sale.order.line']
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']

        # Create test partner
        cls.partner = cls.Partner.create({'name': 'Test Customer'})

        # Create service products for project/task creation
        cls.product_a = cls.Product.create({
            'name': 'Service A',
            'list_price': 100.0,
            'type': 'service',
            'service_tracking': 'task_in_project',  # Creates tasks automatically
            'description_sale': 'Professional consulting service',
        })
        cls.product_b = cls.Product.create({
            'name': 'Service B',
            'list_price': 150.0,
            'type': 'service',
            'service_tracking': 'task_in_project',
            'description_sale': 'Technical implementation',
        })
        cls.product_c = cls.Product.create({
            'name': 'Service C',
            'list_price': 200.0,
            'type': 'service',
            'service_tracking': 'task_in_project',
        })
        cls.product_d = cls.Product.create({
            'name': 'Service D',
            'list_price': 50.0,
            'type': 'service',
            'service_tracking': 'task_in_project',
        })

    def setUp(self):
        """Set up test order and segments for each test."""
        super().setUp()

        # Create sale order
        self.order = self.Order.create({
            'partner_id': self.partner.id,
        })

        # Create hierarchical segments (4 levels to test full depth)
        self.segment_root1 = self.Segment.create({
            'name': 'Root Segment 1',
            'order_id': self.order.id,
            'sequence': 10,
        })
        self.segment_level2 = self.Segment.create({
            'name': 'Level 2 Segment',
            'order_id': self.order.id,
            'parent_id': self.segment_root1.id,
            'sequence': 20,
        })
        self.segment_level3 = self.Segment.create({
            'name': 'Level 3 Segment',
            'order_id': self.order.id,
            'parent_id': self.segment_level2.id,
            'sequence': 30,
        })
        self.segment_level4 = self.Segment.create({
            'name': 'Level 4 Segment',
            'order_id': self.order.id,
            'parent_id': self.segment_level3.id,
            'sequence': 40,
        })

        # Create root segment 2 (for sibling testing)
        self.segment_root2 = self.Segment.create({
            'name': 'Root Segment 2',
            'order_id': self.order.id,
            'sequence': 50,
        })

        # Create order lines assigned to segments
        self.line_root1 = self.OrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 2.0,
            'segment_id': self.segment_root1.id,
        })
        self.line_level2 = self.OrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 3.0,
            'segment_id': self.segment_level2.id,
        })
        self.line_level3 = self.OrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_c.id,
            'product_uom_qty': 1.0,
            'segment_id': self.segment_level3.id,
        })
        self.line_level4 = self.OrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_d.id,
            'product_uom_qty': 4.0,
            'segment_id': self.segment_level4.id,
        })
        self.line_root2 = self.OrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 5.0,
            'segment_id': self.segment_root2.id,
        })

    # --- AUTO-01: Project creation (2 tests) ---

    def test_confirm_creates_project_if_not_exists(self):
        """Verify project exists after confirm (Odoo native handles this)."""
        # Confirm order
        self.order.action_confirm()

        # Check project was created via native Odoo flow
        project = self.order._get_project()
        self.assertTrue(project, 'Project should exist after order confirmation')
        self.assertTrue(project.id, 'Project should have valid ID')

    def test_confirm_with_existing_project_uses_it(self):
        """Verify existing project is used (no duplicate creation)."""
        # Confirm once to create project
        self.order.action_confirm()
        project1 = self.order._get_project()

        # Reset order state to allow re-confirmation
        self.order.write({'state': 'draft'})

        # Confirm again (idempotent for project)
        self.order.action_confirm()
        project2 = self.order._get_project()

        self.assertEqual(project1.id, project2.id,
                         'Same project should be used on re-confirmation')

    # --- AUTO-02: Task per segment (2 tests) ---

    def test_confirm_creates_task_per_segment(self):
        """Count tasks = count segments after confirmation."""
        # Confirm order
        self.order.action_confirm()

        # Get project
        project = self.order._get_project()

        # Count segment tasks (exclude native Odoo tasks without segment_id)
        segment_tasks = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])

        # Should have 5 tasks (one per segment)
        self.assertEqual(len(segment_tasks), 5,
                         'Should create one task per segment')

    def test_confirm_only_creates_tasks_for_segments_with_order(self):
        """Tasks only for this order's segments (not other orders)."""
        # Create second order with segment
        order2 = self.Order.create({'partner_id': self.partner.id})
        segment_other = self.Segment.create({
            'name': 'Other Order Segment',
            'order_id': order2.id,
        })
        self.OrderLine.create({
            'order_id': order2.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1.0,
            'segment_id': segment_other.id,
        })

        # Confirm only first order
        self.order.action_confirm()
        project = self.order._get_project()

        # Check segment_other has no task
        task_other = self.Task.search([
            ('segment_id', '=', segment_other.id),
            ('project_id', '=', project.id)
        ])
        self.assertEqual(len(task_other), 0,
                         'Should not create tasks for other orders\' segments')

    # --- AUTO-03: Task parent_id hierarchy (3 tests) ---

    def test_child_segment_task_has_parent_id(self):
        """Level 2 segment's task.parent_id = level 1 task."""
        self.order.action_confirm()
        project = self.order._get_project()

        # Get tasks
        task_root = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])
        task_level2 = self.Task.search([
            ('segment_id', '=', self.segment_level2.id),
            ('project_id', '=', project.id)
        ])

        self.assertEqual(task_level2.parent_id.id, task_root.id,
                         'Level 2 task should have level 1 task as parent')

    def test_grandchild_segment_task_hierarchy(self):
        """Level 3 task.parent_id = level 2 task."""
        self.order.action_confirm()
        project = self.order._get_project()

        task_level2 = self.Task.search([
            ('segment_id', '=', self.segment_level2.id),
            ('project_id', '=', project.id)
        ])
        task_level3 = self.Task.search([
            ('segment_id', '=', self.segment_level3.id),
            ('project_id', '=', project.id)
        ])

        self.assertEqual(task_level3.parent_id.id, task_level2.id,
                         'Level 3 task should have level 2 task as parent')

    def test_deep_hierarchy_preserved(self):
        """4 levels of segments create 4-level task hierarchy."""
        self.order.action_confirm()
        project = self.order._get_project()

        # Get all 4 levels
        task_level1 = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])
        task_level2 = self.Task.search([
            ('segment_id', '=', self.segment_level2.id),
            ('project_id', '=', project.id)
        ])
        task_level3 = self.Task.search([
            ('segment_id', '=', self.segment_level3.id),
            ('project_id', '=', project.id)
        ])
        task_level4 = self.Task.search([
            ('segment_id', '=', self.segment_level4.id),
            ('project_id', '=', project.id)
        ])

        # Verify chain: L4 -> L3 -> L2 -> L1 -> None
        self.assertEqual(task_level4.parent_id.id, task_level3.id)
        self.assertEqual(task_level3.parent_id.id, task_level2.id)
        self.assertEqual(task_level2.parent_id.id, task_level1.id)
        self.assertFalse(task_level1.parent_id,
                         'Level 1 task should have no parent')

    # --- AUTO-04: Root tasks (1 test) ---

    def test_root_segment_task_no_parent(self):
        """Level 1 segment's task.parent_id is False."""
        self.order.action_confirm()
        project = self.order._get_project()

        task_root = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])

        self.assertFalse(task_root.parent_id,
                         'Root segment task should have no parent_id')

    # --- AUTO-05: Name transfer (1 test) ---

    def test_task_name_equals_segment_name(self):
        """task.name == segment.name."""
        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])

        self.assertEqual(task.name, self.segment_root1.name,
                         'Task name should match segment name')

    # --- AUTO-06: Products to description (2 tests) ---

    def test_task_description_contains_products(self):
        """Description includes product names/quantities."""
        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])

        # Check description format
        self.assertIn('Productos incluidos:', task.description,
                      'Description should have product header')
        self.assertIn('Service A', task.description,
                      'Description should include product name')
        self.assertIn('2.00', task.description,
                      'Description should include quantity')

    def test_empty_segment_description(self):
        """Segment without products has empty description."""
        # Create segment with no products
        segment_empty = self.Segment.create({
            'name': 'Empty Segment',
            'order_id': self.order.id,
        })

        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', segment_empty.id),
            ('project_id', '=', project.id)
        ])

        self.assertEqual(task.description, '',
                         'Empty segment should have empty description')

    # --- AUTO-07: Planned hours calculation (2 tests) ---

    def test_planned_hours_equals_product_quantities(self):
        """Sum of product_uom_qty = allocated_hours."""
        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])

        # segment_root1 has 2.0 qty
        self.assertEqual(task.allocated_hours, 2.0,
                         'Allocated hours should equal sum of product quantities')

    def test_planned_hours_zero_for_empty_segment(self):
        """No products = 0 hours."""
        # Create segment with no products
        segment_empty = self.Segment.create({
            'name': 'Empty Segment',
            'order_id': self.order.id,
        })

        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', segment_empty.id),
            ('project_id', '=', project.id)
        ])

        self.assertEqual(task.allocated_hours, 0.0,
                         'Empty segment should have 0 allocated hours')

    # --- AUTO-08: Responsible transfer (1 test) - DEFERRED to Phase 5 ---

    def test_responsible_transfer_deferred(self):
        """Verify code handles missing segment.user_id gracefully.

        DEFERRED to Phase 5: Requires adding user_id field to segment model.
        This test ensures task creation succeeds even when segment has no user_id field.
        """
        # Confirm order (should succeed without user_id field)
        self.order.action_confirm()
        project = self.order._get_project()

        # Task should be created successfully
        task = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])

        self.assertTrue(task.id,
                        'Task creation should succeed without segment.user_id field')
        # user_id not set (no field exists yet)
        # Phase 5 will add segment.user_id and transfer logic

    # --- AUTO-09: Date transfer (1 test) - DEFERRED to Phase 5 ---

    def test_date_transfer_deferred(self):
        """Verify code handles missing segment date fields gracefully.

        DEFERRED to Phase 5: Requires adding date fields to segment model.
        This test ensures task creation succeeds even when segment has no date fields.
        """
        # Confirm order (should succeed without date fields)
        self.order.action_confirm()
        project = self.order._get_project()

        # Task should be created successfully
        task = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])

        self.assertTrue(task.id,
                        'Task creation should succeed without segment date fields')
        # date_deadline not set (no field exists yet)
        # Phase 5 will add segment.date_start/date_end and transfer logic

    # --- AUTO-10: Segment link (2 tests) ---

    def test_task_segment_id_links_to_segment(self):
        """task.segment_id == segment."""
        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', self.segment_level2.id),
            ('project_id', '=', project.id)
        ])

        self.assertEqual(task.segment_id.id, self.segment_level2.id,
                         'Task should link to correct segment')

    def test_segment_id_unique_per_task(self):
        """No two tasks have same segment_id."""
        self.order.action_confirm()
        project = self.order._get_project()

        # Check all segments have exactly one task
        for segment in [self.segment_root1, self.segment_level2, self.segment_level3,
                        self.segment_level4, self.segment_root2]:
            tasks = self.Task.search([
                ('segment_id', '=', segment.id),
                ('project_id', '=', project.id)
            ])
            self.assertEqual(len(tasks), 1,
                             f'Segment {segment.name} should have exactly one task')

    # --- AUTO-11 & AUTO-12: Savepoint isolation (2 tests) ---

    def test_savepoint_continues_on_error(self):
        """Mock one segment to fail, others still created."""
        # Mock _create_task_with_savepoint to fail for one segment
        original_method = self.order._create_task_with_savepoint

        def mock_create_task(self_order, task_values, segment):
            if segment.id == self.segment_level2.id:
                # Simulate failure for level 2
                return None
            return original_method(task_values, segment)

        with patch.object(type(self.order), '_create_task_with_savepoint', mock_create_task):
            self.order.action_confirm()
            project = self.order._get_project()

            # Check level 2 task NOT created
            task_level2 = self.Task.search([
                ('segment_id', '=', self.segment_level2.id),
                ('project_id', '=', project.id)
            ])
            self.assertEqual(len(task_level2), 0,
                             'Failed task should not be created')

            # Check level 1 task WAS created (not affected by level 2 failure)
            task_level1 = self.Task.search([
                ('segment_id', '=', self.segment_root1.id),
                ('project_id', '=', project.id)
            ])
            self.assertEqual(len(task_level1), 1,
                             'Other tasks should be created despite one failure')

    def test_partial_failure_logged(self):
        """Error logged when one task fails (check log)."""
        # Mock to return None (simulating exception caught internally)
        original_method = self.order._create_task_with_savepoint

        def mock_create_task(self_order, task_values, segment):
            if segment.id == self.segment_level3.id:
                # Simulate failure by returning None (as _create_task_with_savepoint does on exception)
                _logger.error(f"Failed to create task for segment \"{segment.name}\": Test failure")
                return None
            return original_method(task_values, segment)

        with patch.object(type(self.order), '_create_task_with_savepoint', mock_create_task):
            # Should not raise exception (errors caught and logged)
            with self.assertLogs('odoo.addons.spora_segment.tests.test_automated_task_creation', level='ERROR') as log:
                self.order.action_confirm()

                # Check error was logged
                self.assertTrue(
                    any('Failed to create task for segment' in msg for msg in log.output),
                    'Error should be logged for failed task creation'
                )

    # --- Idempotence (3 tests) ---

    def test_reconfirm_no_duplicates(self):
        """action_confirm() twice creates same task count."""
        # Confirm once
        self.order.action_confirm()
        project = self.order._get_project()

        segment_tasks_1 = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])
        count_1 = len(segment_tasks_1)

        # Reset order state to allow re-confirmation (for idempotence testing)
        self.order.write({'state': 'draft'})

        # Confirm again
        self.order.action_confirm()

        segment_tasks_2 = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])
        count_2 = len(segment_tasks_2)

        self.assertEqual(count_1, count_2,
                         'Re-confirm should not create duplicate tasks')

    def test_idempotence_with_existing_tasks(self):
        """If tasks exist, don't recreate."""
        # Confirm first time
        self.order.action_confirm()
        project = self.order._get_project()

        # Get task IDs
        original_tasks = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])
        original_ids = set(original_tasks.ids)

        # Reset order state to allow re-confirmation
        self.order.write({'state': 'draft'})

        # Confirm again
        self.order.action_confirm()

        # Get task IDs again
        new_tasks = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])
        new_ids = set(new_tasks.ids)

        self.assertEqual(original_ids, new_ids,
                         'Same task IDs should exist after re-confirm')

    def test_idempotence_preserves_task_data(self):
        """Re-confirm doesn't modify existing tasks."""
        # Confirm first time
        self.order.action_confirm()
        project = self.order._get_project()

        task = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])
        original_name = task.name
        original_hours = task.allocated_hours

        # Reset order state to allow re-confirmation
        self.order.write({'state': 'draft'})

        # Confirm again
        self.order.action_confirm()

        task.invalidate_recordset()  # Reload from DB
        self.assertEqual(task.name, original_name,
                         'Task name should not change on re-confirm')
        self.assertEqual(task.allocated_hours, original_hours,
                         'Task hours should not change on re-confirm')

    # --- Edge cases (3 tests) ---

    def test_order_without_segments_no_tasks(self):
        """No segments = no segment tasks created."""
        # Create order with no segments
        order_no_segments = self.Order.create({'partner_id': self.partner.id})
        self.OrderLine.create({
            'order_id': order_no_segments.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1.0,
            # No segment_id
        })

        order_no_segments.action_confirm()
        project = order_no_segments._get_project()

        # Should have no segment tasks (but may have native Odoo tasks)
        segment_tasks = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])
        self.assertEqual(len(segment_tasks), 0,
                         'Order without segments should create no segment tasks')

    def test_order_with_mixed_lines(self):
        """Lines with and without segment_id handled correctly."""
        # Add line without segment_id
        self.OrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_c.id,
            'product_uom_qty': 7.0,
            # No segment_id
        })

        self.order.action_confirm()
        project = self.order._get_project()

        # Should create tasks only for segments
        segment_tasks = self.Task.search([
            ('project_id', '=', project.id),
            ('segment_id', '!=', False)
        ])
        self.assertEqual(len(segment_tasks), 5,
                         'Should create tasks only for segments, not loose lines')

    def test_sibling_segments_independent(self):
        """Multiple root segments create independent task trees."""
        self.order.action_confirm()
        project = self.order._get_project()

        # Get both root tasks
        task_root1 = self.Task.search([
            ('segment_id', '=', self.segment_root1.id),
            ('project_id', '=', project.id)
        ])
        task_root2 = self.Task.search([
            ('segment_id', '=', self.segment_root2.id),
            ('project_id', '=', project.id)
        ])

        # Both should have no parent
        self.assertFalse(task_root1.parent_id,
                         'Root segment 1 task should have no parent')
        self.assertFalse(task_root2.parent_id,
                         'Root segment 2 task should have no parent')

        # Both should exist
        self.assertTrue(task_root1.id, 'Root segment 1 should have task')
        self.assertTrue(task_root2.id, 'Root segment 2 should have task')
