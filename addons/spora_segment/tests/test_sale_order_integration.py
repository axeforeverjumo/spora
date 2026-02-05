"""Integration tests for sale.order.segment with sale.order models.

Tests validate all SALE-01 through SALE-11 requirements including:
- Sale order segment_ids relationship (SALE-01)
- Sale order line segment_id assignment (SALE-02)
- Cross-order parent constraints (SALE-04/05)
- Cross-order line assignment constraints (SALE-06)
- Segment subtotal computation (SALE-07)
- Segment recursive total computation (SALE-08)
- Smart button segment_count and action (SALE-11)
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestSaleOrderSegmentIntegration(TransactionCase):
    """Test suite for sale order and segment integration."""

    @classmethod
    def setUpClass(cls):
        """Set up test data used across multiple test methods."""
        super().setUpClass()
        cls.Segment = cls.env['sale.order.segment']
        cls.Order = cls.env['sale.order']
        cls.OrderLine = cls.env['sale.order.line']
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']

        # Create shared test data
        cls.partner = cls.Partner.create({'name': 'Test Customer'})
        cls.product_a = cls.Product.create({
            'name': 'Product A',
            'list_price': 100.0,
            'type': 'consu',
        })
        cls.product_b = cls.Product.create({
            'name': 'Product B',
            'list_price': 200.0,
            'type': 'consu',
        })
        cls.product_c = cls.Product.create({
            'name': 'Product C',
            'list_price': 50.0,
            'type': 'consu',
        })

    # --- SALE-01: Sale order has segment_ids ---

    def test_sale_order_has_segment_ids(self):
        """Validate order.segment_ids contains all segments linked to order."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment1 = self.Segment.create({
            'name': 'Segment 1',
            'order_id': order.id,
        })
        segment2 = self.Segment.create({
            'name': 'Segment 2',
            'order_id': order.id,
        })

        self.assertEqual(len(order.segment_ids), 2,
                         'Order should have 2 segments in segment_ids')
        self.assertIn(segment1.id, order.segment_ids.ids,
                      'Segment 1 should be in order.segment_ids')
        self.assertIn(segment2.id, order.segment_ids.ids,
                      'Segment 2 should be in order.segment_ids')

    # --- SALE-02: Sale order line has segment_id ---

    def test_sale_order_line_has_segment_id(self):
        """Validate line.segment_id correctly references assigned segment."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment = self.Segment.create({
            'name': 'Test Segment',
            'order_id': order.id,
        })
        line = self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'segment_id': segment.id,
        })

        self.assertEqual(line.segment_id.id, segment.id,
                         'Order line segment_id should reference segment')

    def test_sale_order_line_segment_optional(self):
        """Validate line.segment_id is optional (not required field)."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        line = self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
        })

        self.assertFalse(line.segment_id,
                         'Line without segment_id should be valid')

    # --- SALE-04/05: Create segment with parent from sale order ---

    def test_create_segment_with_parent_same_order(self):
        """Validate creating segment with parent from same order succeeds."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        root = self.Segment.create({
            'name': 'Root Segment',
            'order_id': order.id,
        })
        child = self.Segment.create({
            'name': 'Child Segment',
            'order_id': order.id,
            'parent_id': root.id,
        })

        self.assertEqual(child.parent_id.id, root.id,
                         'Child parent_id should reference root segment')
        # No exception means same-order parent is valid

    def test_create_segment_cross_order_parent_blocked(self):
        """Validate creating segment with parent from different order fails."""
        order1 = self.Order.create({
            'partner_id': self.partner.id,
        })
        order2 = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment_order1 = self.Segment.create({
            'name': 'Segment Order 1',
            'order_id': order1.id,
        })

        with self.assertRaises(ValidationError,
                               msg='Creating segment with parent from different order should raise ValidationError'):
            self.Segment.create({
                'name': 'Segment Order 2',
                'order_id': order2.id,
                'parent_id': segment_order1.id,
            })

    # --- SALE-06: Assign products to segments ---

    def test_assign_line_to_segment(self):
        """Validate assigning line to segment succeeds and line appears in segment.line_ids."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment = self.Segment.create({
            'name': 'Test Segment',
            'order_id': order.id,
        })
        line = self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'segment_id': segment.id,
        })

        self.assertIn(line.id, segment.line_ids.ids,
                      'Line should appear in segment.line_ids')

    def test_assign_line_cross_order_blocked(self):
        """Validate assigning line to segment from different order fails."""
        order1 = self.Order.create({
            'partner_id': self.partner.id,
        })
        order2 = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment_order1 = self.Segment.create({
            'name': 'Segment Order 1',
            'order_id': order1.id,
        })

        with self.assertRaises(ValidationError,
                               msg='Creating line with segment from different order should raise ValidationError'):
            self.OrderLine.create({
                'order_id': order2.id,
                'product_id': self.product_a.id,
                'product_uom_qty': 1,
                'segment_id': segment_order1.id,
            })

    # --- SALE-07: Subtotal computation ---

    def test_segment_subtotal_sum_of_lines(self):
        """Validate segment.subtotal equals sum of line price_subtotals."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment = self.Segment.create({
            'name': 'Test Segment',
            'order_id': order.id,
        })
        # Product A: qty=2, price=100 -> subtotal=200
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 2,
            'price_unit': 100.0,
            'segment_id': segment.id,
        })
        # Product B: qty=1, price=200 -> subtotal=200
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 1,
            'price_unit': 200.0,
            'segment_id': segment.id,
        })

        # Total expected: 200 + 200 = 400
        self.assertEqual(segment.subtotal, 400.0,
                         'Segment subtotal should equal sum of line price_subtotals (400)')

    def test_segment_subtotal_zero_no_lines(self):
        """Validate segment.subtotal is 0 when no lines assigned."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment = self.Segment.create({
            'name': 'Empty Segment',
            'order_id': order.id,
        })

        self.assertEqual(segment.subtotal, 0.0,
                         'Segment with no lines should have subtotal=0')

    def test_segment_subtotal_updates_on_line_change(self):
        """Validate segment.subtotal recomputes when line quantity changes."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment = self.Segment.create({
            'name': 'Test Segment',
            'order_id': order.id,
        })
        line = self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'price_unit': 100.0,
            'segment_id': segment.id,
        })

        self.assertEqual(segment.subtotal, 100.0,
                         'Initial subtotal should be 100')

        # Change quantity to 3
        line.write({'product_uom_qty': 3})

        self.assertEqual(segment.subtotal, 300.0,
                         'Subtotal should update to 300 after qty change')

    # --- SALE-08: Total computation (recursive) ---

    def test_segment_total_no_children(self):
        """Validate segment.total equals subtotal when no children."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        segment = self.Segment.create({
            'name': 'Leaf Segment',
            'order_id': order.id,
        })
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 2,
            'price_unit': 100.0,
            'segment_id': segment.id,
        })

        self.assertEqual(segment.total, 200.0,
                         'Total should equal subtotal (200) when no children')

    def test_segment_total_includes_children(self):
        """Validate segment.total includes own subtotal plus children totals."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        parent = self.Segment.create({
            'name': 'Parent',
            'order_id': order.id,
        })
        child = self.Segment.create({
            'name': 'Child',
            'order_id': order.id,
            'parent_id': parent.id,
        })

        # Parent line: qty=1, price=100 -> subtotal=100
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'price_unit': 100.0,
            'segment_id': parent.id,
        })
        # Child line: qty=1, price=200 -> subtotal=200
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 1,
            'price_unit': 200.0,
            'segment_id': child.id,
        })

        self.assertEqual(child.total, 200.0,
                         'Child total should equal own subtotal (200)')
        self.assertEqual(parent.total, 300.0,
                         'Parent total should equal own subtotal (100) + child total (200) = 300')

    def test_segment_total_three_levels(self):
        """Validate segment.total propagates correctly through 3 levels."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        grandparent = self.Segment.create({
            'name': 'Grandparent',
            'order_id': order.id,
        })
        parent = self.Segment.create({
            'name': 'Parent',
            'order_id': order.id,
            'parent_id': grandparent.id,
        })
        child = self.Segment.create({
            'name': 'Child',
            'order_id': order.id,
            'parent_id': parent.id,
        })

        # Grandparent line: qty=1, price=50 -> subtotal=50
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_c.id,
            'product_uom_qty': 1,
            'price_unit': 50.0,
            'segment_id': grandparent.id,
        })
        # Parent line: qty=1, price=100 -> subtotal=100
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'price_unit': 100.0,
            'segment_id': parent.id,
        })
        # Child line: qty=1, price=200 -> subtotal=200
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 1,
            'price_unit': 200.0,
            'segment_id': child.id,
        })

        self.assertEqual(child.total, 200.0,
                         'Child total should be 200')
        self.assertEqual(parent.total, 300.0,
                         'Parent total should be 100 (own) + 200 (child) = 300')
        self.assertEqual(grandparent.total, 350.0,
                         'Grandparent total should be 50 (own) + 300 (parent tree) = 350')

    def test_segment_total_updates_cascade(self):
        """Validate parent.total updates when child line is added/modified."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        parent = self.Segment.create({
            'name': 'Parent',
            'order_id': order.id,
        })
        child = self.Segment.create({
            'name': 'Child',
            'order_id': order.id,
            'parent_id': parent.id,
        })

        # Initial: parent has 1 line (100), child has 1 line (200)
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'price_unit': 100.0,
            'segment_id': parent.id,
        })
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 1,
            'price_unit': 200.0,
            'segment_id': child.id,
        })

        self.assertEqual(parent.total, 300.0,
                         'Initial parent total should be 300')

        # Add another line to child
        self.OrderLine.create({
            'order_id': order.id,
            'product_id': self.product_c.id,
            'product_uom_qty': 1,
            'price_unit': 50.0,
            'segment_id': child.id,
        })

        self.assertEqual(child.total, 250.0,
                         'Child total should update to 250')
        self.assertEqual(parent.total, 350.0,
                         'Parent total should cascade update to 350')

    # --- SALE-11: Smart button segment_count ---

    def test_segment_count_zero(self):
        """Validate order.segment_count is 0 when no segments exist."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })

        self.assertEqual(order.segment_count, 0,
                         'New order with no segments should have segment_count=0')

    def test_segment_count_reflects_all_segments(self):
        """Validate order.segment_count counts all segments including children."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        root = self.Segment.create({
            'name': 'Root',
            'order_id': order.id,
        })
        child1 = self.Segment.create({
            'name': 'Child 1',
            'order_id': order.id,
            'parent_id': root.id,
        })
        child2 = self.Segment.create({
            'name': 'Child 2',
            'order_id': order.id,
            'parent_id': root.id,
        })

        self.assertEqual(order.segment_count, 3,
                         'Order should count all 3 segments (root + 2 children)')

    def test_action_view_segments_returns_action(self):
        """Validate order.action_view_segments() returns proper action dict."""
        order = self.Order.create({
            'partner_id': self.partner.id,
        })
        self.Segment.create({
            'name': 'Test Segment',
            'order_id': order.id,
        })

        action = order.action_view_segments()

        self.assertEqual(action['type'], 'ir.actions.act_window',
                         'Action type should be ir.actions.act_window')
        self.assertEqual(action['res_model'], 'sale.order.segment',
                         'Action res_model should be sale.order.segment')
        self.assertIn('domain', action,
                      'Action should contain domain filter')
        self.assertIn(('order_id', '=', order.id), action['domain'],
                      'Domain should filter by order ID')

    # --- Edge case: order_id required ---

    def test_segment_requires_order_id(self):
        """Validate creating segment without order_id raises error."""
        # Odoo 18 required field raises error when creating via ORM
        with self.assertRaises(Exception,
                               msg='Creating segment without order_id should raise error'):
            self.Segment.create({
                'name': 'Orphan Segment',
            })
