from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestUxEnhancements(TransactionCase):
    """Tests for Phase 5 UX enhancements: full_path, child_depth, product_count."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create sale order for testing
        cls.partner = cls.env['res.partner'].create({'name': 'UX Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'UX Test Product',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

        # Create hierarchical segments: Root -> Child -> Grandchild
        cls.root_segment = cls.env['sale.order.segment'].create({
            'name': 'Root Segment',
            'order_id': cls.order.id,
        })
        cls.child_segment = cls.env['sale.order.segment'].create({
            'name': 'Child Segment',
            'order_id': cls.order.id,
            'parent_id': cls.root_segment.id,
        })
        cls.grandchild_segment = cls.env['sale.order.segment'].create({
            'name': 'Grandchild Segment',
            'order_id': cls.order.id,
            'parent_id': cls.child_segment.id,
        })

    def test_full_path_computation(self):
        """UX-02: full_path shows complete hierarchy with / separator."""
        self.assertEqual(self.root_segment.full_path, 'Root Segment')
        self.assertEqual(self.child_segment.full_path, 'Root Segment / Child Segment')
        self.assertEqual(
            self.grandchild_segment.full_path,
            'Root Segment / Child Segment / Grandchild Segment'
        )

    def test_full_path_cascade_on_parent_rename(self):
        """UX-02: full_path updates when ancestor name changes."""
        # Rename root segment
        self.root_segment.name = 'Renamed Root'

        # Invalidate cache to ensure recomputation
        self.child_segment.invalidate_recordset(['full_path'])
        self.grandchild_segment.invalidate_recordset(['full_path'])

        # Verify cascade
        self.assertEqual(self.child_segment.full_path, 'Renamed Root / Child Segment')
        self.assertEqual(
            self.grandchild_segment.full_path,
            'Renamed Root / Child Segment / Grandchild Segment'
        )

    def test_child_depth_computation(self):
        """UX-05: child_depth shows maximum descendant depth."""
        # Grandchild has no children -> depth = 0
        self.assertEqual(self.grandchild_segment.child_depth, 0)

        # Child has one level of children -> depth = 1
        self.assertEqual(self.child_segment.child_depth, 1)

        # Root has two levels of descendants -> depth = 2
        self.assertEqual(self.root_segment.child_depth, 2)

    def test_child_depth_updates_on_hierarchy_change(self):
        """UX-05: child_depth updates when adding/removing children."""
        # Add great-grandchild
        great_grandchild = self.env['sale.order.segment'].create({
            'name': 'Great-grandchild',
            'order_id': self.order.id,
            'parent_id': self.grandchild_segment.id,
        })

        # Invalidate and check cascade
        self.grandchild_segment.invalidate_recordset(['child_depth'])
        self.child_segment.invalidate_recordset(['child_depth'])
        self.root_segment.invalidate_recordset(['child_depth'])

        self.assertEqual(self.grandchild_segment.child_depth, 1)
        self.assertEqual(self.child_segment.child_depth, 2)
        self.assertEqual(self.root_segment.child_depth, 3)

        # Remove great-grandchild and verify depth decreases
        great_grandchild.unlink()

        self.grandchild_segment.invalidate_recordset(['child_depth'])
        self.child_segment.invalidate_recordset(['child_depth'])
        self.root_segment.invalidate_recordset(['child_depth'])

        self.assertEqual(self.grandchild_segment.child_depth, 0)
        self.assertEqual(self.child_segment.child_depth, 1)
        self.assertEqual(self.root_segment.child_depth, 2)

    def test_product_count_computation(self):
        """UX-06: product_count shows count of directly assigned products."""
        # Initially no products
        self.assertEqual(self.root_segment.product_count, 0)

        # Add order line to root segment
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'segment_id': self.root_segment.id,
        })

        # Invalidate and verify
        self.root_segment.invalidate_recordset(['product_count'])
        self.assertEqual(self.root_segment.product_count, 1)

        # Add another line
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 3,
            'segment_id': self.root_segment.id,
        })

        self.root_segment.invalidate_recordset(['product_count'])
        self.assertEqual(self.root_segment.product_count, 2)

    def test_product_count_only_direct_not_children(self):
        """UX-06: product_count counts only direct products, not children's."""
        # Add product to child segment
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'segment_id': self.child_segment.id,
        })

        # Root should have 0 (not counting child's products)
        self.root_segment.invalidate_recordset(['product_count'])
        self.assertEqual(self.root_segment.product_count, 0)

        # Child should have 1
        self.child_segment.invalidate_recordset(['product_count'])
        self.assertEqual(self.child_segment.product_count, 1)

    def test_child_count_stored(self):
        """UX: child_count is stored for instant reads."""
        # Verify child_count field has store=True by checking it's stored
        field = self.env['sale.order.segment']._fields['child_count']
        self.assertTrue(field.store, "child_count should be stored for performance")

    def test_full_path_stored(self):
        """UX-02: full_path is stored for sorting/filtering."""
        field = self.env['sale.order.segment']._fields['full_path']
        self.assertTrue(field.store, "full_path should be stored for performance")

    def test_child_depth_stored(self):
        """UX-05: child_depth is stored for instant reads."""
        field = self.env['sale.order.segment']._fields['child_depth']
        self.assertTrue(field.store, "child_depth should be stored for performance")
