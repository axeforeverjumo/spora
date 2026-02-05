from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    segment_id = fields.Many2one(
        'sale.order.segment',
        string='Segment',
        help='Assign this order line to a specific segment.',
        domain="[('order_id', '=', order_id)]",
        index=True,
    )

    @api.constrains('segment_id', 'order_id')
    def _check_segment_order(self):
        """Validate segment belongs to same order as line."""
        for line in self:
            if line.segment_id and line.segment_id.order_id != line.order_id:
                raise ValidationError(
                    'Error: Cannot assign line to segment "%s" because it '
                    'belongs to a different sale order. Segment\'s order: "%s", '
                    'Line\'s order: "%s".' % (
                        line.segment_id.name,
                        line.segment_id.order_id.name,
                        line.order_id.name,
                    )
                )
