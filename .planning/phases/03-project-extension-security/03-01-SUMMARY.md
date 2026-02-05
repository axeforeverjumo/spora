---
phase: 03-project-extension-security
plan: 01
subsystem: integration
tags: [odoo, project, security, many2one, record-rules]

# Dependency graph
requires:
  - phase: 02-sale-order-integration
    provides: sale.order.segment model with hierarchy and totals computation
provides:
  - project.task extension with segment_id Many2one field
  - Cross-model validations (deletion protection, sale_order_id change blocking)
  - Segment display_name computation (SO001 / Segment Name format)
  - Record-level security rules for segment access control
  - Task form view with conditional segment_id visibility
affects: [04-automatic-task-creation, testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Onchange warning pattern for soft validation (modal popup, user can proceed)"
    - "Deletion protection via @api.ondelete decorator"
    - "Record rules with separate read/write permissions for same group"
    - "Conditional field visibility in views (invisible attribute with related field checks)"

key-files:
  created:
    - addons/spora_segment/models/project_task.py
    - addons/spora_segment/models/project_project.py
    - addons/spora_segment/views/project_task_views.xml
    - addons/spora_segment/security/segment_security.xml
  modified:
    - addons/spora_segment/models/sale_order_segment.py
    - addons/spora_segment/models/__init__.py
    - addons/spora_segment/__manifest__.py

key-decisions:
  - "Onchange warning (not constraint) for cross-order segment: Soft validation allows user to proceed after acknowledgment"
  - "Separate read/write record rules for Sales Users: Enables read-all, write-own access pattern"
  - "segment_id ondelete='restrict': Database-level backup for Python @api.ondelete protection"
  - "segment_id positioned after project_id: Logical field grouping in task form"

patterns-established:
  - "Cross-model validation: Use @api.ondelete for deletion protection, @api.constrains for blocking changes"
  - "Soft validation pattern: @api.onchange returns warning dict for advisory messages"
  - "Security model: Read-all + write-filtered via separate ir.rule records for same group"

# Metrics
duration: 2min
completed: 2026-02-05
---

# Phase 3 Plan 1: Project Extension & Security Summary

**project.task extension with segment_id traceability, cross-model validations (deletion protection, sale_order change blocking), conditional form view visibility, and record-level security rules for sales team access control**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-05T18:51:15Z
- **Completed:** 2026-02-05T18:54:10Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extended project.task with segment_id Many2one field for budget traceability
- Implemented cross-model validations protecting data integrity (segment deletion, project sale_order change)
- Added segment display_name computation showing "SO001 / Segment Name" format
- Created task form view inheritance with conditional segment_id visibility (only when project has sale_order_id)
- Defined record-level security rules: Sales Users read all/write own, Sales Managers full CRUD

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project.task and project.project model extensions with segment validations** - `698c8aa` (feat)
2. **Task 2: Create task form view, security record rules, and update manifest** - `2f766e1` (feat)

## Files Created/Modified
- `addons/spora_segment/models/project_task.py` - project.task extension with segment_id field and cross-order warning onchange
- `addons/spora_segment/models/project_project.py` - project.project extension blocking sale_order_id changes when tasks have segments
- `addons/spora_segment/models/sale_order_segment.py` - Added _compute_display_name (SO001 / Name format) and _unlink_if_no_tasks deletion protection
- `addons/spora_segment/models/__init__.py` - Added imports for project_task and project_project
- `addons/spora_segment/views/project_task_views.xml` - Task form view inheritance with conditional segment_id field
- `addons/spora_segment/security/segment_security.xml` - Record rules for Sales User and Sales Manager access control
- `addons/spora_segment/__manifest__.py` - Added 'project' dependency and new data files

## Decisions Made

**1. Onchange warning (not constraint) for cross-order validation**
- Used @api.onchange returning warning dict instead of @api.constrains raising ValidationError
- Allows user to acknowledge and proceed after seeing modal warning
- Matches user decision for "Modal warning bloqueante" (modal with OK button, not hard block)

**2. Separate read/write record rules for Sales Users**
- Created two ir.rule records for group_sale_salesman instead of one combined rule
- Read rule: domain [(1, '=', 1)] with perm_read=1 only (access all segments)
- Write rule: domain filtering by order_id.user_id with perm_write=1, perm_create=1
- Enables "read all, write own" access pattern per user requirements

**3. segment_id field ondelete='restrict'**
- Database-level constraint backing up Python @api.ondelete decorator
- Provides defense-in-depth: if Python decorator bypassed, DB foreign key constraint catches deletion attempt
- Standard Odoo pattern for critical relationships

**4. Conditional field visibility using related field checks**
- Used inline expression `invisible="not project_id or not project_id.sale_order_id"` in view
- Leverages Odoo 18 syntax (not legacy attrs={} format)
- Domain filter `[('order_id', '=', project_id.sale_order_id)]` ensures dropdown shows only valid segments

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed as specified without problems.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 4 (Automatic Task Creation):**
- segment_id field established on project.task for traceability
- Display name format provides clear segment identification in UI
- Security rules ensure proper access control during task creation
- Deletion protection prevents orphaning tasks when segments deleted
- Cross-order validation warns users of potential issues

**No blockers or concerns.**

**For Phase 4 implementation:**
- Use segment.display_name for task identification (includes order reference)
- Respect segment_id optional nature (allow manual tasks without segments)
- Leverage onchange warning pattern for user-facing validations
- Test with both Sales User and Sales Manager roles to verify security rules

---
*Phase: 03-project-extension-security*
*Completed: 2026-02-05*
