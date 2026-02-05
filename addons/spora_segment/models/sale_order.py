from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    segment_ids = fields.One2many(
        'sale.order.segment',
        'order_id',
        string='Segments',
        help='Hierarchical organization of order lines into segments.',
    )

    segment_count = fields.Integer(
        string='Segment Count',
        compute='_compute_segment_count',
    )

    def _compute_segment_count(self):
        """Count segments for smart button badge."""
        for order in self:
            order.segment_count = len(order.segment_ids)

    def action_view_segments(self):
        """Smart button action: open segment tree filtered to this order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Segments',
            'res_model': 'sale.order.segment',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }
