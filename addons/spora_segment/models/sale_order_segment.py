import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

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
        domain="[('order_id', '=', order_id)]",
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

    # --- Sale order integration ---
    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        index=True,
        ondelete='cascade',
        required=True,
        help='The sale order this segment belongs to.',
    )
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        'sale.order.line',
        'segment_id',
        string='Order Lines',
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id',
        help='Sum of order lines directly assigned to this segment.',
    )
    total = fields.Monetary(
        string='Total',
        compute='_compute_total',
        store=True,
        currency_field='currency_id',
        help='Subtotal plus total of all child segments (recursive).',
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

    @api.depends('line_ids.price_subtotal')
    def _compute_subtotal(self):
        """Compute subtotal: sum of own order lines."""
        for segment in self:
            segment.subtotal = sum(segment.line_ids.mapped('price_subtotal'))

    @api.depends('subtotal', 'child_ids.total')
    def _compute_total(self):
        """Compute total recursively: own subtotal + children totals."""
        for segment in self:
            children_total = sum(segment.child_ids.mapped('total'))
            segment.total = segment.subtotal + children_total

    # --- Constraints ---
    @api.constrains('parent_id', 'order_id')
    def _check_parent_same_order(self):
        """Validate parent segment belongs to same order."""
        for segment in self:
            if segment.parent_id and segment.parent_id.order_id != segment.order_id:
                raise ValidationError(
                    'Error: Cannot set parent segment "%s" because it belongs '
                    'to a different sale order.' % segment.parent_id.name
                )

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

    # --- Display name ---
    def _compute_display_name(self):
        """Display as 'SO001 / Segment Name' for better identification in task form."""
        for segment in self:
            if segment.order_id:
                segment.display_name = '%s / %s' % (segment.order_id.name, segment.name)
            else:
                segment.display_name = segment.name

    # --- Deletion protection ---
    @api.ondelete(at_uninstall=False)
    def _unlink_if_no_tasks(self):
        """Prevent deletion if project tasks reference this segment."""
        task_count = self.env['project.task'].search_count([('segment_id', 'in', self.ids)])
        if task_count > 0:
            raise UserError(
                'No se puede eliminar segmento(s) porque están referenciados por tareas de proyecto. '
                'Elimine las referencias a segmentos de las tareas primero, o elimine las tareas.'
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
