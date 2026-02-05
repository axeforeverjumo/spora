import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


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

    def action_confirm(self):
        """Override to create hierarchical tasks from segments after native flow creates project."""
        # FIRST: Native Odoo flow - creates project, handles service products
        res = super().action_confirm()

        # THEN: Create segment tasks (project now guaranteed to exist)
        for order in self:
            if order.segment_ids:
                order._create_segment_tasks()

        return res

    def _get_project(self):
        """Get project for this sale order. Called after super().action_confirm() so project exists."""
        self.ensure_one()
        # Find project linked via any order line with service product
        project = self.env['project.project'].search([
            ('sale_line_id.order_id', '=', self.id)
        ], limit=1)
        if not project:
            # Fallback: via tasks (in case tasks created manually or via different path)
            task = self.env['project.task'].search([
                ('sale_order_id', '=', self.id)
            ], limit=1)
            if task:
                project = task.project_id
        return project

    def _create_segment_tasks(self):
        """Create hierarchical project tasks from segments level-by-level.

        Process segments level-by-level (BFS) to ensure parent tasks exist before children.
        Uses savepoint isolation for each task creation to prevent cascading failures.
        Idempotent: checks for existing tasks with same segment_id before creating.
        """
        self.ensure_one()

        # Get project created by super().action_confirm()
        project = self._get_project()
        if not project:
            _logger.warning(
                'No project found for order %s after confirmation. '
                'Segment tasks will not be created. '
                'This is expected if order has no service products.',
                self.name
            )
            return

        # Map segment.id -> task.id for parent_id resolution
        segment_to_task = {}

        # Get all segments ordered by level (BFS: process level 1, then 2, then 3, then 4)
        all_segments = self.segment_ids.sorted(key=lambda s: (s.level, s.sequence, s.id))

        _logger.info(
            'Creating tasks for %d segments in order %s (project: %s)',
            len(all_segments),
            self.name,
            project.name
        )

        for segment in all_segments:
            # Idempotence check: skip if task already exists for this segment
            existing_task = self.env['project.task'].search([
                ('segment_id', '=', segment.id),
                ('project_id', '=', project.id)
            ], limit=1)

            if existing_task:
                _logger.debug(
                    'Task already exists for segment %s (task: %s), skipping creation',
                    segment.name,
                    existing_task.name
                )
                segment_to_task[segment.id] = existing_task.id
                continue

            # Prepare task values
            task_values = self._prepare_task_values(segment, project, segment_to_task)

            # Create task with savepoint isolation
            task = self._create_task_with_savepoint(task_values, segment)
            if task:
                segment_to_task[segment.id] = task.id

        _logger.info(
            'Successfully created %d tasks for order %s',
            len(segment_to_task),
            self.name
        )

    def _prepare_task_values(self, segment, project, segment_to_task):
        """Build task creation dict with segment data.

        Args:
            segment: sale.order.segment record
            project: project.project record
            segment_to_task: dict mapping segment.id -> task.id for parent resolution

        Returns:
            dict: values for project.task.create()
        """
        values = {
            'name': segment.name,
            'project_id': project.id,
            'segment_id': segment.id,
            'description': self._format_products_description(segment),
            'planned_hours': sum(segment.line_ids.mapped('product_uom_qty')),
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'sequence': segment.sequence,
        }

        # Set parent_id if segment has parent and parent's task exists
        if segment.parent_id and segment.parent_id.id in segment_to_task:
            values['parent_id'] = segment_to_task[segment.parent_id.id]

        return values

    def _format_products_description(self, segment):
        """Format product list as task description.

        Args:
            segment: sale.order.segment record

        Returns:
            str: formatted product description with quantities
        """
        if not segment.line_ids:
            return ''

        lines = ['Productos incluidos:']
        for line in segment.line_ids:
            # Format: • Product Name (qty.00 unit)
            lines.append(
                '• %s (%.2f %s)' % (
                    line.product_id.name,
                    line.product_uom_qty,
                    line.product_uom.name
                )
            )
            # Add product description if exists
            if line.product_id.description_sale:
                lines.append('  %s' % line.product_id.description_sale)

        return '\n'.join(lines)

    def _create_task_with_savepoint(self, task_values, segment):
        """Create task with savepoint isolation to prevent cascading failures.

        Args:
            task_values: dict for project.task.create()
            segment: sale.order.segment record (for logging)

        Returns:
            project.task: created task or None if failed
        """
        try:
            with self.env.cr.savepoint():
                task = self.env['project.task'].create(task_values)
                _logger.info(
                    'Created task "%s" for segment "%s" (level %d)',
                    task.name,
                    segment.name,
                    segment.level
                )
                return task
        except Exception as e:
            _logger.error(
                'Failed to create task for segment "%s": %s',
                segment.name,
                str(e),
                exc_info=True
            )
            return None
