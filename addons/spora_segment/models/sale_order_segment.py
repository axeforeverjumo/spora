import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

MAX_HIERARCHY_DEPTH = 4


class SaleOrderSegment(models.Model):
    _name = 'sale.order.segment'
    _description = 'Sale Order Segment'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'name'
    _order = 'sequence, id'

    # --- Core fields ---
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    description = fields.Text(
        string='Description',
        help='Optional notes or description for this segment',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Used to order segments within the same level.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # --- Hierarchy fields ---
    parent_id = fields.Many2one(
        'sale.order.segment',
        string='Parent Segment',
        index=True,
        ondelete='cascade',
    )
    parent_path = fields.Char(
        index=True,
        unaccent=False,
    )
    child_ids = fields.One2many(
        'sale.order.segment',
        'parent_id',
        string='Child Segments',
    )

    # --- Future integration field (Phase 2) ---
    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        index=True,
        ondelete='cascade',
        required=False,
        help='The sale order this segment belongs to. Will be required in Phase 2.',
    )

    # --- Computed fields ---
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        store=True,
        recursive=True,
        help='Hierarchy level: 1 for root segments, 2 for children of root, etc.',
    )
    child_count = fields.Integer(
        string='Sub-segment Count',
        compute='_compute_child_count',
        help='Number of direct child segments',
    )

    # --- Computed methods ---
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for segment in self:
            if segment.parent_id:
                segment.level = segment.parent_id.level + 1
            else:
                segment.level = 1

    @api.depends('child_ids')
    def _compute_child_count(self):
        for segment in self:
            segment.child_count = len(segment.child_ids)

    # --- Constraints ---
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        """Validate no circular references and max depth of 4 levels."""
        # Step 1: Check circular references (Odoo 18 method)
        if self._has_cycle():
            raise ValidationError(
                'Error: You cannot create recursive segments. '
                'A segment cannot be its own ancestor.'
            )

        # Step 2: Check depth limit for each segment
        for segment in self:
            # Walk UP to count depth of this segment
            depth = 1
            current = segment
            while current.parent_id:
                depth += 1
                current = current.parent_id
                if depth > MAX_HIERARCHY_DEPTH:
                    raise ValidationError(
                        'Error: Maximum hierarchy depth is %d levels. '
                        'Segment "%s" would exceed this limit.'
                        % (MAX_HIERARCHY_DEPTH, segment.name)
                    )

            # Step 3: Walk DOWN to check maximum depth of subtree
            # This prevents moving a deep subtree under a high-level parent
            max_child_depth = self._get_max_descendant_depth(segment)
            if depth + max_child_depth > MAX_HIERARCHY_DEPTH:
                raise ValidationError(
                    'Error: Moving "%s" here would create hierarchy '
                    'of %d levels (max %d).' % (
                        segment.name,
                        depth + max_child_depth,
                        MAX_HIERARCHY_DEPTH,
                    )
                )

    def _get_max_descendant_depth(self, segment):
        """Return maximum depth of descendants below this segment."""
        if not segment.child_ids:
            return 0
        return 1 + max(
            self._get_max_descendant_depth(child)
            for child in segment.child_ids
        )

    # --- Action methods ---
    def action_view_children(self):
        """Open view of child segments (for stat button in form view)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub-segments',
            'res_model': 'sale.order.segment',
            'view_mode': 'tree,form',
            'domain': [('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id},
        }
