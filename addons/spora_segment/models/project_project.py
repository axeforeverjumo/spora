from odoo import models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def action_view_tasks(self):
        """Override to show only root tasks by default.

        When opening the tasks view from a project, filter to show only
        parent-level tasks (parent_id = False). This prevents overwhelming
        users with all subtasks in projects with deep hierarchies.

        Users can still:
        - Expand task rows to see subtasks (tree view expansion)
        - Remove the filter manually to see all tasks
        - Access subtasks through parent task form view

        Technical context:
        - Standard Odoo shows ALL tasks in a project (root + subtasks)
        - For projects with segment-based hierarchies, this can be 30+ tasks
        - This override adds context to activate a search filter for root tasks
        """
        result = super().action_view_tasks()

        # Add context to activate "root_tasks_only" filter by default
        # This filter is defined in project_task_views.xml
        if 'context' not in result:
            result['context'] = {}

        # Activate the root tasks filter
        result['context']['search_default_root_tasks_only'] = 1

        return result

    def write(self, vals):
        """Override write to prevent sale_order changes when tasks have segments.

        Intercepts write() to validate sale_line_id changes before they happen.
        Blocks changing the linked sale order if tasks reference segments.
        """
        # If sale_line_id is being changed, validate before write
        if 'sale_line_id' in vals:
            for project in self:
                origin_line = project.sale_line_id
                new_line_id = vals.get('sale_line_id')

                # Allow initial assignment (None -> line)
                if not origin_line:
                    continue

                # Allow clearing (line -> None)
                if not new_line_id:
                    continue

                # Get new line record
                new_line = self.env['sale.order.line'].browse(new_line_id)

                # Check if order is changing
                origin_order = origin_line.order_id
                new_order = new_line.order_id

                if origin_order != new_order:
                    # Order is changing, check for segment tasks
                    task_with_segment = self.env['project.task'].search_count([
                        ('project_id', '=', project.id),
                        ('segment_id', '!=', False)
                    ])

                    if task_with_segment > 0:
                        raise ValidationError(
                            'No se puede cambiar el presupuesto del proyecto "%s" de "%s" a "%s" '
                            'porque contiene tareas vinculadas a segmentos. '
                            'Elimine las referencias a segmentos de las tareas primero.'
                            % (project.name, origin_order.name, new_order.name)
                        )

        # Call super to execute the actual write
        return super().write(vals)
