from odoo import models, api
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.constrains('sale_order_id')
    def _check_sale_order_change_with_segments(self):
        """Prevent changing sale_order_id if tasks have segment references."""
        for project in self:
            # Only block if sale_order_id is being changed (not cleared completely)
            # We need to check if any tasks have segment_id set
            task_with_segment = self.env['project.task'].search_count([
                ('project_id', '=', project.id),
                ('segment_id', '!=', False)
            ])
            if task_with_segment > 0:
                raise ValidationError(
                    'No se puede cambiar el presupuesto del proyecto "%s" porque '
                    'contiene tareas vinculadas a segmentos. '
                    'Elimine las referencias a segmentos de las tareas primero.'
                    % project.name
                )
