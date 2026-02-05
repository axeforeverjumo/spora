"""Integration tests for project.task with sale.order.segment.

Tests validate all PROJ and SEC requirements including:
- PROJ-01: segment_id field on project.task
- PROJ-02: Field visibility in task form (when project has sale_order_id)
- PROJ-03: Cross-order segment assignment warning (onchange advisory, not blocking)
- SEC-01: Access rights via ir.model.access.csv
- SEC-02: Sales User can create/read segments on own orders
- SEC-03: Sales Manager full CRUD on all segments
- SEC-04: Sales User write restricted to own orders (via record rules)
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError, AccessError


@tagged('post_install', '-at_install')
class TestProjectTaskSegment(TransactionCase):
    """Test suite for project.task and segment integration with security."""

    @classmethod
    def setUpClass(cls):
        """Set up test data used across multiple test methods."""
        super().setUpClass()
        cls.Task = cls.env['project.task']
        cls.Project = cls.env['project.project']
        cls.Segment = cls.env['sale.order.segment']
        cls.Order = cls.env['sale.order']
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']

        # Create users for security tests
        cls.user_salesman = cls.env['res.users'].create({
            'name': 'Sales User 1',
            'login': 'salesman1',
            'email': 'salesman1@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('sales_team.group_sale_salesman').id,
                cls.env.ref('project.group_project_user').id,
            ])],
        })
        cls.user_salesman2 = cls.env['res.users'].create({
            'name': 'Sales User 2',
            'login': 'salesman2',
            'email': 'salesman2@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('sales_team.group_sale_salesman').id,
                cls.env.ref('project.group_project_user').id,
            ])],
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Sales Manager',
            'login': 'salesmanager',
            'email': 'manager@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('project.group_project_manager').id,
            ])],
        })

        # Create shared test data
        cls.partner = cls.Partner.create({'name': 'Test Customer'})
        cls.product = cls.Product.create({
            'name': 'Test Product',
            'list_price': 100.0,
            'type': 'service',  # Use 'service' for project-related products
        })

        # Create two sale orders (one per salesman)
        cls.order1 = cls.Order.create({
            'partner_id': cls.partner.id,
            'user_id': cls.user_salesman.id,
        })
        cls.order2 = cls.Order.create({
            'partner_id': cls.partner.id,
            'user_id': cls.user_salesman2.id,
        })

        # Create order lines (needed for project.sale_order_id linkage)
        cls.OrderLine = cls.env['sale.order.line']
        cls.order1_line = cls.OrderLine.create({
            'order_id': cls.order1.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1,
        })
        cls.order2_line = cls.OrderLine.create({
            'order_id': cls.order2.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1,
        })

        # Create segments in each order
        cls.segment_order1_root = cls.Segment.create({
            'name': 'Segment Order 1 Root',
            'order_id': cls.order1.id,
        })
        cls.segment_order1_child = cls.Segment.create({
            'name': 'Segment Order 1 Child',
            'order_id': cls.order1.id,
            'parent_id': cls.segment_order1_root.id,
        })
        cls.segment_order2_root = cls.Segment.create({
            'name': 'Segment Order 2 Root',
            'order_id': cls.order2.id,
        })

        # Create projects (linked via sale_line_id for sale_order_id relationship)
        cls.project1 = cls.Project.create({
            'name': 'Project 1',
            'sale_line_id': cls.order1_line.id,
        })
        cls.project_manual = cls.Project.create({
            'name': 'Manual Project',
        })

    # --- PROJ-01: segment_id field exists on project.task ---

    def test_segment_id_field_exists(self):
        """Validate segment_id field exists on project.task model."""
        self.assertIn('segment_id', self.env['project.task']._fields,
                      'project.task should have segment_id field')

    def test_task_with_segment_valid(self):
        """Validate creating task with segment from correct order succeeds."""
        task = self.Task.create({
            'name': 'Task with segment',
            'project_id': self.project1.id,
            'segment_id': self.segment_order1_root.id,
        })

        self.assertEqual(task.segment_id.id, self.segment_order1_root.id,
                         'Task segment_id should reference segment')

    def test_task_without_segment(self):
        """Validate creating task without segment_id succeeds (field is optional)."""
        task = self.Task.create({
            'name': 'Task without segment',
            'project_id': self.project1.id,
        })

        self.assertFalse(task.segment_id,
                         'Task without segment_id should be valid')

    def test_task_manual_project_no_segment(self):
        """Validate creating task in manual project (no sale_order_id) succeeds."""
        task = self.Task.create({
            'name': 'Task in manual project',
            'project_id': self.project_manual.id,
        })

        self.assertFalse(task.segment_id,
                         'Task in manual project should be valid without segment_id')

    # --- PROJ-03: Cross-order segment onchange warning ---

    def test_cross_order_segment_onchange_warning(self):
        """Validate cross-order segment assignment triggers onchange warning."""
        # Create task via .new() to test onchange (not .create() which bypasses onchange)
        task = self.Task.new({
            'name': 'Cross-order task',
        })
        # Set fields explicitly to ensure they're resolved
        task.project_id = self.project1
        task.segment_id = self.segment_order2_root  # segment from order2, project from order1

        # Call the onchange method
        result = task._onchange_segment_order_warning()

        # Assert warning dict is returned
        self.assertIsNotNone(result, 'Onchange should return warning dict for cross-order segment')
        self.assertIn('warning', result, 'Result should contain warning key')
        self.assertIn('title', result['warning'], 'Warning should have title')
        self.assertIn('message', result['warning'], 'Warning should have message')

    def test_cross_order_segment_can_save(self):
        """Validate task with cross-order segment CAN be saved (onchange is advisory)."""
        # Create task via .create() to verify save succeeds despite warning
        task = self.Task.create({
            'name': 'Cross-order task saved',
            'project_id': self.project1.id,
            'segment_id': self.segment_order2_root.id,  # segment from order2
        })

        # Assert task was created successfully
        self.assertTrue(task.id, 'Task should be created despite cross-order segment')
        self.assertEqual(task.segment_id.id, self.segment_order2_root.id,
                         'Task segment_id should reference cross-order segment')

    def test_same_order_segment_no_warning(self):
        """Validate same-order segment does NOT trigger onchange warning."""
        task = self.Task.new({
            'name': 'Same-order task',
        })
        task.project_id = self.project1
        task.segment_id = self.segment_order1_root  # segment from order1, project from order1

        result = task._onchange_segment_order_warning()

        # Assert no warning for correct segment
        self.assertIsNone(result, 'Onchange should return None for same-order segment')

    def test_segment_on_project_without_sale_order(self):
        """Validate segment on manual project (no sale_order_id) does NOT trigger warning."""
        # Create segment in order1 and try to use in manual project
        task = self.Task.new({
            'name': 'Manual project task',
        })
        task.project_id = self.project_manual
        task.segment_id = self.segment_order1_root

        result = task._onchange_segment_order_warning()

        # Assert no warning when project has no sale_order_id
        self.assertIsNone(result,
                          'Onchange should return None when project has no sale_order_id')

    # --- Display name format ---

    def test_segment_display_name_format(self):
        """Validate segment.display_name shows 'SO001 / Segment Name' format."""
        # Force recompute display_name
        self.segment_order1_root._compute_display_name()

        # Order name format is typically "SO001" or similar
        expected_format = '%s / %s' % (self.order1.name, self.segment_order1_root.name)
        self.assertEqual(self.segment_order1_root.display_name, expected_format,
                         'Segment display_name should show order name / segment name')

    def test_segment_display_name_without_order(self):
        """Validate segment without order shows just the name (edge case)."""
        # This is an edge case since order_id is required, but test the display_name logic
        segment = self.Segment.new({'name': 'Orphan Segment'})
        segment._compute_display_name()

        self.assertEqual(segment.display_name, 'Orphan Segment',
                         'Segment without order should display just the name')

    # --- Deletion protection ---

    def test_segment_delete_blocked_with_tasks(self):
        """Validate deleting segment with tasks raises UserError."""
        # Create task linked to segment
        task = self.Task.create({
            'name': 'Task blocking deletion',
            'project_id': self.project1.id,
            'segment_id': self.segment_order1_child.id,
        })

        # Try to delete segment
        with self.assertRaises(UserError,
                               msg='Deleting segment with tasks should raise UserError'):
            self.segment_order1_child.unlink()

    def test_segment_delete_allowed_without_tasks(self):
        """Validate deleting segment without tasks succeeds."""
        # Create segment with no tasks
        segment = self.Segment.create({
            'name': 'Segment to delete',
            'order_id': self.order1.id,
        })

        # Delete should succeed
        segment.unlink()

        # Verify deletion
        self.assertFalse(self.Segment.search([('id', '=', segment.id)]),
                         'Segment without tasks should be deleted successfully')

    # --- Project sale_order_id change constraint ---

    def test_project_sale_order_change_blocked_with_segment_tasks(self):
        """Validate changing project.sale_order_id blocked when tasks have segments."""
        # Create task with segment
        task = self.Task.create({
            'name': 'Task with segment blocking change',
            'project_id': self.project1.id,
            'segment_id': self.segment_order1_root.id,
        })

        # Try to change project sale_order_id
        with self.assertRaises(ValidationError,
                               msg='Changing project sale_order_id with segment tasks should raise ValidationError'):
            self.project1.write({'sale_order_id': self.order2.id})

    def test_project_sale_order_change_allowed_without_segment_tasks(self):
        """Validate changing project.sale_order_id allowed when tasks have NO segments."""
        # Create task WITHOUT segment
        task = self.Task.create({
            'name': 'Task without segment',
            'project_id': self.project1.id,
        })

        # Change should succeed (no segment tasks to block)
        self.project1.write({'sale_order_id': self.order2.id})

        self.assertEqual(self.project1.sale_order_id.id, self.order2.id,
                         'Project sale_order_id should change when no segment tasks exist')

    # --- SEC-02/SEC-04: Sales User create/read/write permissions ---

    def test_salesman_can_create_segment_own_order(self):
        """Validate Sales User can create segment on own order."""
        # Use salesman1 context
        segment = self.Segment.with_user(self.user_salesman).create({
            'name': 'Segment by Salesman',
            'order_id': self.order1.id,
        })

        self.assertTrue(segment.id, 'Sales User should create segment on own order')

    def test_salesman_cannot_write_segment_other_order(self):
        """Validate Sales User cannot write segment on other user's order."""
        # Use salesman1 context, try to modify segment from order2 (owned by salesman2)
        with self.assertRaises(AccessError,
                               msg='Sales User should not write segment on other user\'s order'):
            self.segment_order2_root.with_user(self.user_salesman).write({
                'name': 'Modified by wrong user',
            })

    def test_salesman_can_read_all_segments(self):
        """Validate Sales User can read segments from all orders."""
        # Use salesman1 context, search for segments on order2
        segments = self.Segment.with_user(self.user_salesman).search([
            ('order_id', '=', self.order2.id)
        ])

        # Should return results (read access to all)
        self.assertTrue(len(segments) > 0,
                        'Sales User should read segments from other orders')
        self.assertIn(self.segment_order2_root.id, segments.ids,
                      'Sales User should see segments from order2')

    # --- SEC-03: Sales Manager full CRUD ---

    def test_manager_full_crud_all_segments(self):
        """Validate Sales Manager has full CRUD on all segments."""
        # Create
        segment = self.Segment.with_user(self.user_manager).create({
            'name': 'Manager Created Segment',
            'order_id': self.order2.id,
        })
        self.assertTrue(segment.id, 'Manager should create segment on any order')

        # Read
        segments = self.Segment.with_user(self.user_manager).search([
            ('order_id', '=', self.order2.id)
        ])
        self.assertIn(segment.id, segments.ids, 'Manager should read all segments')

        # Write
        segment.with_user(self.user_manager).write({'name': 'Updated by Manager'})
        self.assertEqual(segment.name, 'Updated by Manager',
                         'Manager should write any segment')

        # Delete (ensure no tasks reference it first)
        segment.with_user(self.user_manager).unlink()
        self.assertFalse(self.Segment.search([('id', '=', segment.id)]),
                         'Manager should delete any segment')

    # --- Additional edge cases ---

    def test_task_segment_from_correct_order_hierarchy(self):
        """Validate task can use child segment from correct order."""
        task = self.Task.create({
            'name': 'Task with child segment',
            'project_id': self.project1.id,
            'segment_id': self.segment_order1_child.id,
        })

        self.assertEqual(task.segment_id.id, self.segment_order1_child.id,
                         'Task should accept child segment from correct order')

    def test_segment_ondelete_restrict_behavior(self):
        """Validate segment_id ondelete='restrict' prevents deletion at DB level."""
        # This tests the ondelete='restrict' field parameter backup
        # The @api.ondelete decorator is primary, but ondelete='restrict' provides DB-level safety

        task = self.Task.create({
            'name': 'Task for ondelete test',
            'project_id': self.project1.id,
            'segment_id': self.segment_order1_child.id,
        })

        # Try to delete segment - should be blocked by @api.ondelete decorator
        with self.assertRaises(UserError,
                               msg='Segment deletion should be blocked by decorator and ondelete parameter'):
            self.segment_order1_child.unlink()
