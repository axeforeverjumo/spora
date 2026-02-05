from odoo import models, api
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.constrains('sale_order_id')
    def _check_sale_order_change_with_segments(self):
        """Prevent changing sale_order_id if tasks have segment references.

        Only blocks if sale_order_id already existed AND is being changed.
        Allows initial assignment (None -> SO) and clearing (SO -> None).
        """
        for project in self:
            if not project.sale_order_id:
                # Permitir limpiar sale_order_id
                continue

            # Detectar si es un cambio real (no una asignación inicial)
            if project._origin.sale_order_id and project._origin.sale_order_id != project.sale_order_id:
                task_with_segment = self.env['project.task'].search_count([
                    ('project_id', '=', project.id),
                    ('segment_id', '!=', False)
                ])
                if task_with_segment > 0:
                    raise ValidationError(
                        'No se puede cambiar el presupuesto del proyecto "%s" de "%s" a "%s" '
                        'porque contiene tareas vinculadas a segmentos. '
                        'Elimine las referencias a segmentos de las tareas primero.'
                        % (project.name, project._origin.sale_order_id.name, project.sale_order_id.name)
                    )
