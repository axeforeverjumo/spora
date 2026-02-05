---
phase: 04-automated-task-creation
plan: 01
subsystem: automation
tags: [odoo, sale, project, task-automation, hierarchy, bfs]

# Dependency graph
requires:
  - phase: 03-project-extension-security
    provides: project.task.segment_id field with onchange warning and record rules
  - phase: 02-sale-order-integration
    provides: sale.order with segment_ids and computed totals
  - phase: 01-foundation-model-structure
    provides: sale.order.segment model with hierarchy and level computation

provides:
  - Automatic hierarchical task creation from segments on sale order confirmation
  - Level-by-level BFS processing ensuring parent tasks exist before children
  - Idempotent task creation (re-confirm doesn't duplicate)
  - Savepoint-isolated task creation for error resilience
  - Product-to-task description formatting

affects: [05-testing-refinement, task-tracking, project-management, reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BFS level-by-level hierarchy processing (avoids Python recursion limits)"
    - "Savepoint isolation per task creation (prevents cascading rollbacks)"
    - "Idempotence via search-before-create pattern"
    - "Super-first pattern: let Odoo create project, then add segment tasks"

key-files:
  created: []
  modified:
    - addons/spora_segment/models/sale_order.py

key-decisions:
  - "Use allocated_hours not planned_hours for Odoo 18 compatibility"
  - "Call super().action_confirm() FIRST to ensure project exists before creating segment tasks"
  - "Process segments level-by-level (BFS) to guarantee parent tasks exist"
  - "Check for existing segment_id tasks before creating (idempotence)"
  - "Wrap each task creation in savepoint for error isolation"
  - "Format product descriptions with bullet list in task.description"

patterns-established:
  - "action_confirm override: super() first, then custom logic"
  - "segment_to_task mapping dict for parent_id resolution across levels"
  - "Savepoint pattern: with self.env.cr.savepoint() for isolated transactions"
  - "_get_project() searches via sale_line_id.order_id (project created by native Odoo)"

# Metrics
duration: 6min
completed: 2026-02-05
---

# Phase 04 Plan 01: Automated Task Creation Summary

**Hierarchical project tasks auto-created from sale order segments on confirmation with BFS level processing and idempotent savepoint-isolated creation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-05T19:57:53Z
- **Completed:** 2026-02-05T20:03:51Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Sale order confirmation now creates one project task per segment automatically
- Task hierarchy mirrors segment hierarchy (child task.parent_id = root task.id)
- Tasks populated with segment data: name, allocated hours, product descriptions
- Idempotent: re-confirming order doesn't create duplicate tasks
- Error-isolated: savepoint per task prevents one failure from blocking others

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement action_confirm override with segment-to-task conversion** - `fc34ba3` (feat)
   - Followed by field name fix: `f7b91c0` (fix) - changed planned_hours to allocated_hours for Odoo 18
2. **Task 2: Manual integration verification via Odoo shell** - `1ef8cc7` (test)

**Plan metadata:** (will be committed separately)

## Files Created/Modified

- `addons/spora_segment/models/sale_order.py` - Extended with action_confirm override and 6 helper methods for hierarchical task creation from segments

## Decisions Made

**Use allocated_hours not planned_hours for Odoo 18:**
- Odoo 18 renamed the task hours field from planned_hours to allocated_hours
- Discovered during shell testing when task creation failed with "Invalid field 'planned_hours'"
- Changed _prepare_task_values() to use allocated_hours

**Super-first pattern for action_confirm:**
- Rationale: Native Odoo creates project via super().action_confirm(), we create tasks after
- "Dejar que Odoo lo cree" (project) + "Nosotros controlamos" (tasks) = super() first
- Ensures project exists when _create_segment_tasks() runs

**BFS level-by-level processing:**
- Process level 1 segments, then level 2, then level 3, then level 4
- Guarantees parent task exists before processing children
- Avoids Python recursion limits for deep hierarchies

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Changed planned_hours to allocated_hours**
- **Found during:** Task 2 (Manual shell testing)
- **Issue:** Task creation failed with "Invalid field 'planned_hours' on model 'project.task'"
- **Fix:** Changed field name to allocated_hours in _prepare_task_values() method
- **Files modified:** addons/spora_segment/models/sale_order.py
- **Verification:** Shell test created tasks successfully with allocated_hours populated
- **Committed in:** f7b91c0 (separate fix commit after initial feat commit)

---

**Total deviations:** 1 auto-fixed (1 blocking - field name compatibility)
**Impact on plan:** Essential fix for Odoo 18 compatibility. Field rename is standard Odoo upgrade pattern. No scope creep.

## Issues Encountered

**Odoo 18 field rename from planned_hours to allocated_hours:**
- Problem: Plan specified planned_hours (correct for Odoo 14-17), but Odoo 18 uses allocated_hours
- Solution: Checked available fields via shell (fields_get()), found allocated_hours
- Resolution: Updated _prepare_task_values() method
- Time impact: ~2 minutes for discovery and fix

**Initial shell tests showed no project created:**
- Problem: Service products without service_tracking='task_in_project' don't auto-create projects
- Solution: Created test products with correct service_tracking setting
- Resolution: Shell test confirmed project creation and task hierarchy
- Time impact: ~1 minute for test adjustment

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 05 (Testing & Refinement):**
- Core automation complete: segments → tasks on confirmation
- Hierarchy mapping working: parent_id references correct
- Idempotence verified: safe to re-confirm orders
- Error isolation working: savepoint pattern in place

**Foundation solid for:**
- Integration tests (create order, add segments, confirm, verify tasks)
- Edge case testing (empty segments, deep hierarchies, missing products)
- UI testing (view tasks in project, segment references)
- Performance testing (large segment trees, batch confirmations)

**No blockers or concerns.**

---
*Phase: 04-automated-task-creation*
*Completed: 2026-02-05*
