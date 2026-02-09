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
        """Override to create hierarchical tasks from segments.

        CRITICAL: For orders with segments, disables native Odoo service_tracking task creation:
        - Prevents duplicate tasks (Odoo native + our segment tasks)
        - Prevents broken hierarchy (native tasks created as root instead of under segments)
        - Manually creates project if needed (since service_tracking='no' prevents project creation)

        Flow for orders WITH segments:
        1. Temporarily set service_tracking='no' on service products
        2. Call super() to handle order confirmation logic
        3. Manually create project if not exists
        4. Create hierarchical segment+product tasks
        5. Restore original service_tracking

        Flow for orders WITHOUT segments:
        - Normal Odoo flow (no changes)
        """
        # Identify orders with segments that need special handling
        orders_with_segments = self.filtered(lambda o: o.segment_ids)
        orders_without_segments = self - orders_with_segments

        # Store original service_tracking values for orders with segments
        tracking_backup = {}
        for order in orders_with_segments:
            for line in order.order_line:
                if line.product_id.type == 'service' and hasattr(line.product_id, 'service_tracking'):
                    tracking_backup[line.product_id.id] = line.product_id.service_tracking
                    # Temporarily disable to prevent native task creation
                    line.product_id.service_tracking = 'no'

        try:
            # Native Odoo confirmation flow
            res = super().action_confirm()

            # For orders with segments: create project + segment tasks
            for order in orders_with_segments:
                _logger.info(
                    'Processing order %s with %d segments',
                    order.name,
                    len(order.segment_ids)
                )

                # Create project if needed (native flow didn't create it due to tracking='no')
                project = order._ensure_project_exists()

                if project:
                    _logger.info(
                        'Project %s found/created for order %s, creating segment tasks',
                        project.name,
                        order.name
                    )
                    # Create hierarchical segment + product tasks
                    order._create_segment_tasks()
                else:
                    _logger.warning(
                        'Could not create or find project for order %s. Skipping segment tasks.',
                        order.name
                    )

            # Restore original service_tracking
            for product_id, original_tracking in tracking_backup.items():
                product = self.env['product.product'].browse(product_id)
                if product.exists():
                    product.service_tracking = original_tracking

        except Exception as e:
            # Restore tracking even on error
            for product_id, original_tracking in tracking_backup.items():
                product = self.env['product.product'].browse(product_id)
                if product.exists():
                    product.service_tracking = original_tracking
            raise

        return res

    def _ensure_project_exists(self):
        """Ensure project exists for this order. Create if needed.

        Returns:
            project.project: existing or newly created project
        """
        self.ensure_one()

        # Check if project already exists
        project = self._get_project()
        if project:
            return project

        # Get first service line to link
        service_line = self.order_line.filtered(
            lambda l: l.product_id.type == 'service'
        )[:1]

        # Create project for this order
        project = self.env['project.project'].create({
            'name': self.name,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'sale_line_id': service_line.id if service_line else False,
        })

        _logger.info(
            'Created project %s for order %s (order has segments, manual creation needed)',
            project.name,
            self.name
        )

        return project

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
        """Create hierarchical project tasks from segments and products.

        Process segments recursively:
        1. Create segment task
        2. Create product subtasks (one per line_ids)
        3. Recursively process child segments

        Uses savepoint isolation for each task creation to prevent cascading failures.
        Idempotent: checks for existing tasks before creating.

        Prevention mechanisms:
        - Checks if tasks already exist before creation
        - Uses context flag to prevent concurrent execution
        - Validates project state before processing
        """
        self.ensure_one()

        # Prevent concurrent/duplicate execution
        if self.env.context.get('_creating_segment_tasks'):
            _logger.debug(
                'Skipping _create_segment_tasks for %s - already in progress',
                self.name
            )
            return

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

        # Validate project is active
        if not project.active:
            _logger.warning(
                'Project %s for order %s is archived. Skipping segment task creation.',
                project.name,
                self.name
            )
            return

        # Check if segment tasks already created
        existing_segment_tasks = self.env['project.task'].search([
            ('segment_id', 'in', self.segment_ids.ids),
            ('project_id', '=', project.id)
        ])
        if len(existing_segment_tasks) >= len(self.segment_ids):
            _logger.info(
                'Segment tasks already created for order %s (%d tasks). Skipping.',
                self.name,
                len(existing_segment_tasks)
            )
            return

        _logger.info(
            'Creating tasks for segments in order %s (project: %s)',
            self.name,
            project.name
        )

        # Process root segments (level 1) recursively with context flag
        root_segments = self.segment_ids.filtered(lambda s: not s.parent_id)
        for segment in root_segments.sorted(key=lambda s: (s.sequence, s.id)):
            self.with_context(_creating_segment_tasks=True)._create_segment_tasks_recursive(
                segment, project, parent_task=None
            )

        _logger.info(
            'Successfully created segment and product tasks for order %s',
            self.name
        )

    def _create_segment_tasks_recursive(self, segment, project, parent_task=None):
        """Recursively create tasks for segment, its products, and child segments.

        Args:
            segment: sale.order.segment record
            project: project.project record
            parent_task: project.task record (parent task) or None for root

        Returns:
            project.task: created segment task or existing task
        """
        # 1. Create or get segment task
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
            segment_task = existing_task
        else:
            # Prepare segment task values
            task_values = {
                'name': segment.name,
                'project_id': project.id,
                'segment_id': segment.id,
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'sequence': segment.sequence,
            }

            # Set parent if this is a child segment
            if parent_task:
                task_values['parent_id'] = parent_task.id

            # Create segment task
            segment_task = self._create_task_with_savepoint(task_values, segment)
            if not segment_task:
                return None

        # 2. Create product subtasks (one per line_ids)
        for line in segment.line_ids:
            # Check if product task already exists
            existing_product_task = self.env['project.task'].search([
                ('name', '=', line.product_id.name),
                ('parent_id', '=', segment_task.id),
                ('project_id', '=', project.id),
                ('sale_line_id', '=', line.id)
            ], limit=1)

            if existing_product_task:
                _logger.debug(
                    'Product task already exists for line %s, skipping',
                    line.product_id.name
                )
                continue

            # Prepare product task values
            product_task_values = {
                'name': line.product_id.name,
                'project_id': project.id,
                'parent_id': segment_task.id,
                'sale_line_id': line.id,
                'allocated_hours': line.product_uom_qty,
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
            }

            # Add product description if exists
            if line.name or line.product_id.description_sale:
                product_task_values['description'] = line.name or line.product_id.description_sale

            # Create product task
            self._create_task_with_savepoint(product_task_values, segment, is_product=True)

        # 3. Recursively process child segments
        for child_segment in segment.child_ids.sorted(key=lambda s: (s.sequence, s.id)):
            self._create_segment_tasks_recursive(child_segment, project, parent_task=segment_task)

        return segment_task

    def _create_task_with_savepoint(self, task_values, segment, is_product=False):
        """Create task with savepoint isolation to prevent cascading failures.

        Args:
            task_values: dict for project.task.create()
            segment: sale.order.segment record (for logging context)
            is_product: bool, True if creating product task (for logging)

        Returns:
            project.task: created task or None if failed
        """
        try:
            with self.env.cr.savepoint():
                task = self.env['project.task'].create(task_values)
                if is_product:
                    _logger.info(
                        'Created product task "%s" under segment "%s"',
                        task.name,
                        segment.name
                    )
                else:
                    _logger.info(
                        'Created segment task "%s" (level %d)',
                        task.name,
                        segment.level
                    )
                return task
        except Exception as e:
            task_type = 'product' if is_product else 'segment'
            _logger.error(
                'Failed to create %s task "%s" for segment "%s": %s',
                task_type,
                task_values.get('name', 'unknown'),
                segment.name,
                str(e),
                exc_info=True
            )
            return None

    def check_task_creation_conflicts(self):
        """Check for modules/configurations that may conflict with segment task creation.

        Returns:
            dict: {
                'has_conflicts': bool,
                'conflicts': list of dict with details,
                'warnings': list of warning messages,
            }
        """
        conflicts = []
        warnings = []

        # Check for conflicting modules
        conflicting_modules = [
            'sale_project_task_custom',
            'jumo_spora_project_task_from_sale',
            'project_task_auto_create',
        ]

        installed_modules = self.env['ir.module.module'].search([
            ('name', 'in', conflicting_modules),
            ('state', '=', 'installed')
        ])

        if installed_modules:
            for module in installed_modules:
                conflicts.append({
                    'type': 'module',
                    'name': module.name,
                    'summary': module.summary,
                    'message': f'Module "{module.name}" may create tasks independently',
                })

        # Check for products with service_tracking enabled
        products_with_tracking = self.env['product.product'].search([
            ('type', '=', 'service'),
            ('sale_ok', '=', True),
            ('service_tracking', '!=', 'no'),
        ])

        if products_with_tracking:
            warnings.append({
                'type': 'product_tracking',
                'count': len(products_with_tracking),
                'message': f'{len(products_with_tracking)} service products have service_tracking enabled. '
                           f'This is normal - our module temporarily disables it during confirmation.',
                'sample_products': products_with_tracking[:5].mapped('name'),
            })

        return {
            'has_conflicts': bool(conflicts),
            'has_warnings': bool(warnings),
            'conflicts': conflicts,
            'warnings': warnings,
        }
