from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    segment_id = fields.Many2one(
        'sale.order.segment',
        string='Budget Segment',
        index=True,
        ondelete='restrict',
        domain="[('order_id', '=', project_id.sale_order_id)]",
        help='Reference to the originating budget segment. '
             'Only visible for projects linked to sale orders.',
    )

    @api.onchange('segment_id', 'project_id')
    def _onchange_segment_order_warning(self):
        """Warn user when segment does not belong to project's sale order.

        Returns a warning dict that Odoo displays as a modal popup with
        an OK button. User clicks OK, warning disappears, and the save
        proceeds normally. This is NOT a hard block — it's advisory.
        """
        if self.segment_id and self.project_id and self.project_id.sale_order_id:
            if self.segment_id.order_id != self.project_id.sale_order_id:
                return {
                    'warning': {
                        'title': 'Advertencia: Segmento de otro presupuesto',
                        'message': (
                            'El segmento "%s" no pertenece al presupuesto de este proyecto. '
                            'Esto puede causar inconsistencias.'
                        ) % self.segment_id.display_name,
                    }
                }

    @api.constrains('segment_id', 'project_id')
    def _check_segment_order_match(self):
        """Hard constraint: Segment MUST belong to project's sale order.

        This prevents data corruption by blocking saves when segment
        does not match project's sale order. Complements the onchange warning.
        """
        for task in self:
            if task.segment_id and task.project_id and task.project_id.sale_order_id:
                if task.segment_id.order_id != task.project_id.sale_order_id:
                    raise ValidationError(
                        'Error: El segmento "%s" no pertenece al presupuesto del proyecto "%s". '
                        'Solo puedes asignar segmentos del presupuesto "%s".'
                        % (task.segment_id.display_name, task.project_id.name, task.project_id.sale_order_id.name)
                    )
