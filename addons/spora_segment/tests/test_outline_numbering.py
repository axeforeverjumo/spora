import logging

from odoo.tests import tagged, TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestOutlineNumbering(TransactionCase):
    """Test suite for outline numbering functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env['sale.order']
        cls.Segment = cls.env['sale.order.segment']
        cls.Partner = cls.env['res.partner']

        # Create test partner
        cls.partner = cls.Partner.create({
            'name': 'Test Customer',
        })

        # Create test sale order
        cls.order = cls.SaleOrder.create({
            'partner_id': cls.partner.id,
        })

    def test_outline_number_root_segments(self):
        """Verify root segments get sequential numbers 1, 2, 3."""
        seg1 = self.Segment.create({
            'name': 'Fase 1',
            'order_id': self.order.id,
            'sequence': 10,
        })
        seg2 = self.Segment.create({
            'name': 'Fase 2',
            'order_id': self.order.id,
            'sequence': 20,
        })
        seg3 = self.Segment.create({
            'name': 'Fase 3',
            'order_id': self.order.id,
            'sequence': 30,
        })

        self.assertEqual(seg1.outline_number, '1', 'First root segment should be numbered 1')
        self.assertEqual(seg2.outline_number, '2', 'Second root segment should be numbered 2')
        self.assertEqual(seg3.outline_number, '3', 'Third root segment should be numbered 3')

    def test_outline_number_nested(self):
        """Verify nested segments get hierarchical numbers 1.1, 1.2."""
        parent = self.Segment.create({
            'name': 'Parent',
            'order_id': self.order.id,
            'sequence': 10,
        })
        child1 = self.Segment.create({
            'name': 'Child 1',
            'order_id': self.order.id,
            'parent_id': parent.id,
            'sequence': 10,
        })
        child2 = self.Segment.create({
            'name': 'Child 2',
            'order_id': self.order.id,
            'parent_id': parent.id,
            'sequence': 20,
        })

        self.assertEqual(parent.outline_number, '1', 'Parent should be numbered 1')
        self.assertEqual(child1.outline_number, '1.1', 'First child should be numbered 1.1')
        self.assertEqual(child2.outline_number, '1.2', 'Second child should be numbered 1.2')

    def test_outline_number_resequence(self):
        """Verify numbers update when sequence changes."""
        seg1 = self.Segment.create({
            'name': 'First',
            'order_id': self.order.id,
            'sequence': 10,
        })
        seg2 = self.Segment.create({
            'name': 'Second',
            'order_id': self.order.id,
            'sequence': 20,
        })

        # Initial state
        self.assertEqual(seg1.outline_number, '1', 'First segment should initially be 1')
        self.assertEqual(seg2.outline_number, '2', 'Second segment should initially be 2')

        # Swap order by changing sequence
        seg2.sequence = 5

        # Recompute outline numbers
        (seg1 | seg2).invalidate_recordset(['outline_number'])

        # Verify order changed
        self.assertEqual(seg2.outline_number, '1', 'After resequence, seg2 should be 1')
        self.assertEqual(seg1.outline_number, '2', 'After resequence, seg1 should be 2')

    def test_outline_number_three_levels(self):
        """Verify deep hierarchy 1.1.1, 1.1.2."""
        level1 = self.Segment.create({
            'name': 'L1',
            'order_id': self.order.id,
            'sequence': 10,
        })
        level2 = self.Segment.create({
            'name': 'L2',
            'order_id': self.order.id,
            'parent_id': level1.id,
            'sequence': 10,
        })
        level3_1 = self.Segment.create({
            'name': 'L3-1',
            'order_id': self.order.id,
            'parent_id': level2.id,
            'sequence': 10,
        })
        level3_2 = self.Segment.create({
            'name': 'L3-2',
            'order_id': self.order.id,
            'parent_id': level2.id,
            'sequence': 20,
        })

        self.assertEqual(level1.outline_number, '1', 'Level 1 should be 1')
        self.assertEqual(level2.outline_number, '1.1', 'Level 2 should be 1.1')
        self.assertEqual(level3_1.outline_number, '1.1.1', 'Level 3 first child should be 1.1.1')
        self.assertEqual(level3_2.outline_number, '1.1.2', 'Level 3 second child should be 1.1.2')

    def test_outline_number_multiple_trees(self):
        """Verify multiple root segments with children get correct numbering."""
        # First tree
        root1 = self.Segment.create({
            'name': 'Root 1',
            'order_id': self.order.id,
            'sequence': 10,
        })
        root1_child1 = self.Segment.create({
            'name': 'Root 1 - Child 1',
            'order_id': self.order.id,
            'parent_id': root1.id,
            'sequence': 10,
        })
        root1_child2 = self.Segment.create({
            'name': 'Root 1 - Child 2',
            'order_id': self.order.id,
            'parent_id': root1.id,
            'sequence': 20,
        })

        # Second tree
        root2 = self.Segment.create({
            'name': 'Root 2',
            'order_id': self.order.id,
            'sequence': 20,
        })
        root2_child1 = self.Segment.create({
            'name': 'Root 2 - Child 1',
            'order_id': self.order.id,
            'parent_id': root2.id,
            'sequence': 10,
        })

        # Verify first tree
        self.assertEqual(root1.outline_number, '1')
        self.assertEqual(root1_child1.outline_number, '1.1')
        self.assertEqual(root1_child2.outline_number, '1.2')

        # Verify second tree
        self.assertEqual(root2.outline_number, '2')
        self.assertEqual(root2_child1.outline_number, '2.1')

    def test_outline_number_display_name(self):
        """Verify display_name includes outline number."""
        segment = self.Segment.create({
            'name': 'Test Segment',
            'order_id': self.order.id,
            'sequence': 10,
        })

        # Force display_name computation
        segment.invalidate_recordset(['display_name'])

        expected_display = f'{self.order.name} / 1. Test Segment'
        self.assertEqual(
            segment.display_name,
            expected_display,
            f'Display name should include outline number. Got: {segment.display_name}'
        )

    def test_outline_number_ordering(self):
        """Verify segments are ordered by outline_number in searches."""
        # Create segments in non-sequential order
        seg3 = self.Segment.create({
            'name': 'Third',
            'order_id': self.order.id,
            'sequence': 30,
        })
        seg1 = self.Segment.create({
            'name': 'First',
            'order_id': self.order.id,
            'sequence': 10,
        })
        seg2 = self.Segment.create({
            'name': 'Second',
            'order_id': self.order.id,
            'sequence': 20,
        })

        # Search all segments for this order (should use _order)
        segments = self.Segment.search([('order_id', '=', self.order.id)])

        # Verify they come back in outline_number order
        self.assertEqual(segments[0], seg1, 'First segment should be seg1')
        self.assertEqual(segments[1], seg2, 'Second segment should be seg2')
        self.assertEqual(segments[2], seg3, 'Third segment should be seg3')
