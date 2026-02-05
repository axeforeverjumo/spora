"""Comprehensive tests for sale.order.segment hierarchical model.

Tests validate all HIER-01 through HIER-10 requirements including:
- Parent-child relationships and inverse relationships
- Parent path population and format
- Level computation at all depths (1-4)
- Circular reference prevention (direct, indirect, self-reference)
- 4-level depth limit enforcement (including subtree reparenting)
- Sequence ordering
- Cascade deletion
- Segment flexibility (leaf, branch, both)
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError


@tagged('at_install')
class TestSaleOrderSegment(TransactionCase):
    """Test suite for sale.order.segment hierarchical behavior."""

    @classmethod
    def setUpClass(cls):
        """Set up test data used across multiple test methods."""
        super().setUpClass()
        cls.Segment = cls.env['sale.order.segment']

        # Create a test sale order for segments (required in Phase 2)
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    # --- HIER-01: parent_id field relationship ---

    def test_create_segment_with_parent(self):
        """Validate parent_id relationship - child correctly references parent."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})

        self.assertEqual(child.parent_id.id, root.id,
                         'Child parent_id should reference root segment')

    # --- HIER-02: child_ids inverse relationship ---

    def test_child_ids_inverse(self):
        """Validate child_ids inverse - parent tracks all children."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child1 = self.Segment.create({'name': 'Child 1', 'order_id': self.order.id, 'parent_id': root.id})
        child2 = self.Segment.create({'name': 'Child 2', 'order_id': self.order.id, 'parent_id': root.id})

        self.assertEqual(len(root.child_ids), 2,
                         'Root should have 2 children in child_ids')
        self.assertIn(child1.id, root.child_ids.ids,
                      'Child 1 should be in root.child_ids')
        self.assertIn(child2.id, root.child_ids.ids,
                      'Child 2 should be in root.child_ids')

    # --- HIER-03: parent_path with _parent_store ---

    def test_parent_path_populated(self):
        """Validate parent_path is automatically populated for all segments."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})

        self.assertTrue(root.parent_path,
                        'Root parent_path should be populated')
        self.assertTrue(child.parent_path,
                        'Child parent_path should be populated')

    def test_parent_path_format(self):
        """Validate parent_path format contains segment IDs in hierarchy."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})

        # Parent path format is "id1/id2/id3/" with trailing slash
        self.assertIn(str(root.id), root.parent_path,
                      'Root parent_path should contain root ID')
        self.assertIn(str(root.id), child.parent_path,
                      'Child parent_path should contain root ID')
        self.assertIn(str(child.id), child.parent_path,
                      'Child parent_path should contain child ID')

    # --- HIER-04: computed level field ---

    def test_level_root(self):
        """Validate root segment (no parent) has level=1."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        self.assertEqual(root.level, 1, 'Root segment should have level=1')

    def test_level_child(self):
        """Validate direct child has level=2."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})

        self.assertEqual(child.level, 2,
                         'Child of root should have level=2')

    def test_level_grandchild(self):
        """Validate grandchild has level=3."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})
        grandchild = self.Segment.create({'name': 'Grandchild', 'order_id': self.order.id, 'parent_id': child.id})

        self.assertEqual(grandchild.level, 3,
                         'Grandchild should have level=3')

    def test_level_great_grandchild(self):
        """Validate great-grandchild has level=4 (maximum depth)."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})
        grandchild = self.Segment.create({'name': 'Grandchild', 'order_id': self.order.id, 'parent_id': child.id})
        great_grandchild = self.Segment.create({'name': 'Great-Grandchild', 'order_id': self.order.id, 'parent_id': grandchild.id})

        self.assertEqual(great_grandchild.level, 4,
                         'Great-grandchild should have level=4')

    def test_level_updates_on_reparent(self):
        """Validate level recalculates when segment is moved to different parent."""
        root1 = self.Segment.create({'name': 'Root 1', 'order_id': self.order.id})
        root2 = self.Segment.create({'name': 'Root 2', 'order_id': self.order.id})
        child2 = self.Segment.create({'name': 'Child of Root 2', 'order_id': self.order.id, 'parent_id': root2.id})
        segment = self.Segment.create({'name': 'Movable', 'order_id': self.order.id, 'parent_id': root1.id})

        self.assertEqual(segment.level, 2, 'Initially at level 2')

        # Move segment from Root 1 to Child of Root 2
        segment.write({'parent_id': child2.id})

        self.assertEqual(segment.level, 3,
                         'After reparenting, level should be 3')

    # --- HIER-05: circular reference prevention with _has_cycle() ---

    def test_circular_reference_direct(self):
        """Validate direct circular reference (A->B, then B->A) is blocked."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})

        with self.assertRaises(UserError,
                               msg='Setting root.parent_id = child should raise UserError (Recursion Detected)'):
            root.write({'parent_id': child.id})

    def test_circular_reference_indirect(self):
        """Validate indirect circular reference (A->B->C, then A->C) is blocked."""
        a = self.Segment.create({'name': 'A', 'order_id': self.order.id})
        b = self.Segment.create({'name': 'B', 'order_id': self.order.id, 'parent_id': a.id})
        c = self.Segment.create({'name': 'C', 'order_id': self.order.id, 'parent_id': b.id})

        with self.assertRaises(UserError,
                               msg='Creating indirect cycle should raise UserError (Recursion Detected)'):
            a.write({'parent_id': c.id})

    def test_self_parent_blocked(self):
        """Validate self-reference (segment as its own parent) is blocked."""
        segment = self.Segment.create({'name': 'Self-Ref Test', 'order_id': self.order.id})

        with self.assertRaises(UserError,
                               msg='Setting segment.parent_id = segment.id should raise UserError (Recursion Detected)'):
            segment.write({'parent_id': segment.id})

    # --- HIER-06: 4-level depth limit ---

    def test_depth_limit_4_allowed(self):
        """Validate 4-level deep hierarchy is allowed."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})
        grandchild = self.Segment.create({'name': 'Grandchild', 'order_id': self.order.id, 'parent_id': child.id})
        great_grandchild = self.Segment.create({'name': 'Great-Grandchild', 'order_id': self.order.id, 'parent_id': grandchild.id})

        # If we reach here without exception, test passes
        self.assertEqual(great_grandchild.level, 4,
                         '4-level deep segment should be created successfully')

    def test_depth_limit_5_blocked(self):
        """Validate 5-level deep hierarchy is blocked."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})
        grandchild = self.Segment.create({'name': 'Grandchild', 'order_id': self.order.id, 'parent_id': child.id})
        great_grandchild = self.Segment.create({'name': 'Great-Grandchild', 'order_id': self.order.id, 'parent_id': grandchild.id})

        with self.assertRaises(ValidationError,
                               msg='Creating 5th level should raise ValidationError'):
            self.Segment.create({'name': 'Level 5', 'order_id': self.order.id, 'parent_id': great_grandchild.id})

    def test_depth_limit_reparent_blocked(self):
        """Validate reparenting that would exceed depth limit is blocked."""
        # Create a level-3 parent (L1->L2->L3)
        root1 = self.Segment.create({'name': 'Root 1', 'order_id': self.order.id})
        parent_l2 = self.Segment.create({'name': 'Parent L2', 'order_id': self.order.id, 'parent_id': root1.id})
        parent_l3 = self.Segment.create({'name': 'Parent L3', 'order_id': self.order.id, 'parent_id': parent_l2.id})

        # Create a 2-level deep subtree elsewhere (L1->L2->L3)
        root2 = self.Segment.create({'name': 'Root 2', 'order_id': self.order.id})
        subtree_l2 = self.Segment.create({'name': 'Subtree L2', 'order_id': self.order.id, 'parent_id': root2.id})
        subtree_l3 = self.Segment.create({'name': 'Subtree L3', 'order_id': self.order.id, 'parent_id': subtree_l2.id})

        # Try to move subtree_l2 under parent_l3 (would create L4->L5->L6, exceeds limit)
        with self.assertRaises(ValidationError,
                               msg='Reparenting subtree that would exceed depth should raise ValidationError'):
            subtree_l2.write({'parent_id': parent_l3.id})

    def test_reparent_subtree_exceeds_depth(self):
        """CRITICAL: Validate reparenting a deep subtree exceeds depth limit.

        Create A(L1)->B(L2)->C(L3)->D(L4) and X(L1)->Y(L2)->Z(L3).
        Move B under Z. Should raise ValidationError because:
        - B becomes L4
        - C becomes L5 (exceeds limit)
        - D becomes L6 (exceeds limit)

        This validates that constraint checks entire subtree depth, not just the moved segment.
        """
        # Create first tree: A(L1) -> B(L2) -> C(L3) -> D(L4)
        a = self.Segment.create({'name': 'A', 'order_id': self.order.id})
        b = self.Segment.create({'name': 'B', 'order_id': self.order.id, 'parent_id': a.id})
        c = self.Segment.create({'name': 'C', 'order_id': self.order.id, 'parent_id': b.id})
        d = self.Segment.create({'name': 'D', 'order_id': self.order.id, 'parent_id': c.id})

        # Verify initial levels
        self.assertEqual(b.level, 2)
        self.assertEqual(c.level, 3)
        self.assertEqual(d.level, 4)

        # Create second tree: X(L1) -> Y(L2) -> Z(L3)
        x = self.Segment.create({'name': 'X', 'order_id': self.order.id})
        y = self.Segment.create({'name': 'Y', 'order_id': self.order.id, 'parent_id': x.id})
        z = self.Segment.create({'name': 'Z', 'order_id': self.order.id, 'parent_id': y.id})

        self.assertEqual(z.level, 3)

        # Try to move B under Z - this would make B=L4, C=L5, D=L6
        with self.assertRaises(ValidationError,
                               msg='Moving B under Z should fail because subtree would exceed depth'):
            b.write({'parent_id': z.id})

    # --- HIER-07: sequence field and ordering ---

    def test_sequence_default(self):
        """Validate new segment has default sequence=10."""
        segment = self.Segment.create({'name': 'Test Sequence', 'order_id': self.order.id})
        self.assertEqual(segment.sequence, 10,
                         'New segment should have sequence=10 by default')

    def test_ordering_by_sequence(self):
        """Validate segments are ordered by sequence field (model._order)."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child_c = self.Segment.create({'name': 'Child C', 'order_id': self.order.id, 'parent_id': root.id, 'sequence': 30})
        child_a = self.Segment.create({'name': 'Child A', 'order_id': self.order.id, 'parent_id': root.id, 'sequence': 10})
        child_b = self.Segment.create({'name': 'Child B', 'order_id': self.order.id, 'parent_id': root.id, 'sequence': 20})

        # Search children - should be ordered by sequence
        children = self.Segment.search([('parent_id', '=', root.id)])

        self.assertEqual(children[0].id, child_a.id,
                         'First child should be Child A (sequence 10)')
        self.assertEqual(children[1].id, child_b.id,
                         'Second child should be Child B (sequence 20)')
        self.assertEqual(children[2].id, child_c.id,
                         'Third child should be Child C (sequence 30)')

    # --- HIER-08/09/10: segment flexibility (leaf, branch, both) ---

    def test_segment_without_children(self):
        """Validate segment without children is valid (leaf segment for products only)."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        leaf = self.Segment.create({'name': 'Leaf Segment', 'order_id': self.order.id, 'parent_id': root.id})

        self.assertEqual(len(leaf.child_ids), 0,
                         'Leaf segment should have no children')
        # No exception means leaf segments are valid (HIER-09)

    def test_segment_with_children_no_restriction(self):
        """Validate segment with children is valid (can have sub-segments).

        Also validates that model does NOT block having both children and products.
        Product assignment is tested in Phase 2 via sale.order.line.segment_id.
        """
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        branch = self.Segment.create({'name': 'Branch Segment', 'order_id': self.order.id, 'parent_id': root.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': branch.id})

        self.assertEqual(len(branch.child_ids), 1,
                         'Branch segment should have 1 child')
        # No exception means branch segments are valid (HIER-10)
        # Phase 2 will test HIER-08 (products in branch segment) via sale.order.line

    # --- Additional edge cases ---

    def test_cascade_delete(self):
        """Validate deleting parent cascades to all children (ondelete='cascade')."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': root.id})
        grandchild = self.Segment.create({'name': 'Grandchild', 'order_id': self.order.id, 'parent_id': child.id})

        child_id = child.id
        grandchild_id = grandchild.id

        # Delete root
        root.unlink()

        # Children should be deleted too
        self.assertFalse(self.Segment.search([('id', '=', child_id)]),
                         'Child should be deleted when parent is deleted')
        self.assertFalse(self.Segment.search([('id', '=', grandchild_id)]),
                         'Grandchild should be deleted when root is deleted')

    def test_child_count_computed(self):
        """Validate child_count computed field matches len(child_ids)."""
        root = self.Segment.create({'name': 'Root', 'order_id': self.order.id})
        self.assertEqual(root.child_count, 0,
                         'Root with no children should have child_count=0')

        self.Segment.create({'name': 'Child 1', 'order_id': self.order.id, 'parent_id': root.id})
        self.Segment.create({'name': 'Child 2', 'order_id': self.order.id, 'parent_id': root.id})
        self.Segment.create({'name': 'Child 3', 'order_id': self.order.id, 'parent_id': root.id})

        self.assertEqual(root.child_count, 3,
                         'Root with 3 children should have child_count=3')

    def test_active_field_default(self):
        """Validate new segment has active=True by default."""
        segment = self.Segment.create({'name': 'Active Test', 'order_id': self.order.id})
        self.assertTrue(segment.active,
                        'New segment should have active=True by default')

    # --- Optional but recommended edge cases ---

    def test_parent_path_updates_on_reparent(self):
        """Validate parent_path updates when segment is moved to different parent."""
        root1 = self.Segment.create({'name': 'Root 1', 'order_id': self.order.id})
        root2 = self.Segment.create({'name': 'Root 2', 'order_id': self.order.id})
        segment = self.Segment.create({'name': 'Movable', 'order_id': self.order.id, 'parent_id': root1.id})

        original_path = segment.parent_path

        # Move to different parent
        segment.write({'parent_id': root2.id})

        self.assertNotEqual(segment.parent_path, original_path,
                            'parent_path should change after reparenting')
        self.assertIn(str(root2.id), segment.parent_path,
                      'New parent_path should contain new parent ID')

    def test_level_updates_cascade_on_reparent(self):
        """Validate level updates cascade to children when parent is moved."""
        root1 = self.Segment.create({'name': 'Root 1', 'order_id': self.order.id})
        root2 = self.Segment.create({'name': 'Root 2', 'order_id': self.order.id})
        child_of_root2 = self.Segment.create({'name': 'Child of Root 2', 'order_id': self.order.id, 'parent_id': root2.id})

        # Create subtree under root1
        parent = self.Segment.create({'name': 'Parent', 'order_id': self.order.id, 'parent_id': root1.id})
        child = self.Segment.create({'name': 'Child', 'order_id': self.order.id, 'parent_id': parent.id})

        self.assertEqual(parent.level, 2)
        self.assertEqual(child.level, 3)

        # Move parent from root1 (L2) to child_of_root2 (L3)
        parent.write({'parent_id': child_of_root2.id})

        # Levels should cascade
        self.assertEqual(parent.level, 3,
                         'Parent level should update to 3')
        self.assertEqual(child.level, 4,
                         'Child level should cascade to 4')

    def test_batch_create_segments(self):
        """Validate creating multiple segments in single create() call."""
        segments = self.Segment.create([
            {'name': 'Segment 1', 'order_id': self.order.id},
            {'name': 'Segment 2', 'order_id': self.order.id},
            {'name': 'Segment 3', 'order_id': self.order.id},
        ])

        self.assertEqual(len(segments), 3,
                         'Batch create should create 3 segments')
        self.assertEqual(segments[0].level, 1,
                         'All batch created root segments should have level=1')
