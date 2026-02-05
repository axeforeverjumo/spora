---
phase: 03-project-extension-security
plan: 02
subsystem: testing
tags: [odoo, testing, integration, security, unittest]

# Dependency graph
requires:
  - phase: 03-project-extension-security
    plan: 01
    provides: project.task extension with segment_id, cross-model validations, security rules
provides:
  - Comprehensive test suite covering all PROJ and SEC requirements
  - Regression protection for Phase 1 and Phase 2 implementations
  - Security test coverage for Sales User and Sales Manager roles
  - Cross-order validation tests (onchange warning pattern)
affects: [04-automatic-task-creation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TransactionCase with @tagged('post_install', '-at_install') for integration tests"
    - "User context switching with .with_user() for security tests"
    - "Record creation via .new() for onchange testing (vs .create() which bypasses onchange)"
    - "Project-sale order linkage via sale_line_id (sale_order_id is related field)"

key-files:
  created:
    - addons/spora_segment/tests/test_project_task_segment.py
  modified:
    - addons/spora_segment/tests/__init__.py

key-decisions:
  - "Use sale_line_id to link projects to orders: project.sale_order_id is a readonly related field from sale_line_id.order_id"
  - "Set fields explicitly on .new() records for onchange tests: Ensures field resolution before calling onchange methods"
  - "Product type 'service' for project-related products: Standard Odoo pattern for products that create project tasks"

patterns-established:
  - "Integration test setup pattern: Create users with specific groups, orders with lines, projects via sale_line_id"
  - "Onchange test pattern: Use .new() + explicit field assignment + call onchange method directly"
  - "Security test pattern: Create multiple users in different groups, test CRUD operations with .with_user()"

# Metrics
duration: 4min
completed: 2026-02-05
---

# Phase 3 Plan 2: Project Task Segment Testing Summary

**Comprehensive test suite validating project.task segment integration, cross-order validation warnings, deletion protection, and role-based security with 64 passing tests across all phases**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-05T18:55:59Z
- **Completed:** 2026-02-05T19:00:12Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created comprehensive test suite with 20 test methods covering all PROJ and SEC requirements
- Fixed project-sale order linkage using sale_line_id (discovered sale_order_id is readonly related field)
- Validated all Phase 3 functionality: segment_id on tasks, cross-order warnings, deletion protection, security rules
- Achieved zero regressions: all 64 tests pass (Phase 1: 26, Phase 2: 18, Phase 3: 20)
- Verified implementation in actual Odoo 18 Docker environment

## Task Commits

Each task was committed atomically:

1. **Task 1: Write comprehensive tests for project task segment integration and security** - `58d2a3d` (test)
2. **Task 2: Execute all tests in Docker and fix any failures** - `5cbb0ca` (fix)

## Files Created/Modified
- `addons/spora_segment/tests/test_project_task_segment.py` - 20 test methods covering PROJ-01/02/03 and SEC-01/02/03/04
- `addons/spora_segment/tests/__init__.py` - Added import for new test module

## Decisions Made

**1. Project-sale order linkage via sale_line_id**
- Discovered project.sale_order_id is a readonly related field from sale_line_id.order_id
- Updated test setup to create sale.order.line and link projects via sale_line_id field
- This is the standard Odoo pattern for project-sale integration

**2. Explicit field assignment for onchange tests**
- When testing onchange methods, create record via .new() then set fields explicitly
- Pattern: `task = self.Task.new({'name': '...'}); task.project_id = project; task.segment_id = segment`
- Ensures fields are resolved before calling onchange method

**3. Product type 'service' for project-related products**
- Changed test product from 'consu' to 'service' type
- Standard Odoo convention for products that generate project tasks

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Project sale_order_id setup incorrect**
- **Found during:** Task 2 - test execution
- **Issue:** Tests failing because project.sale_order_id was False despite setting it in create()
- **Root cause:** sale_order_id is a readonly related field from sale_line_id.order_id, cannot be set directly
- **Fix:** Created sale.order.line records and linked projects via sale_line_id instead
- **Files modified:** addons/spora_segment/tests/test_project_task_segment.py
- **Commit:** 5cbb0ca

**2. [Rule 3 - Blocking] Onchange test not triggering warning**
- **Found during:** Task 2 - test execution
- **Issue:** test_cross_order_segment_onchange_warning failing - onchange returning None instead of warning
- **Root cause:** Fields passed via dict to .new() were not fully resolved before calling onchange
- **Fix:** Changed to explicit field assignment pattern (set fields after .new() creation)
- **Files modified:** addons/spora_segment/tests/test_project_task_segment.py (3 onchange tests)
- **Commit:** 5cbb0ca

## Issues Encountered

None after fixes applied. All tests pass on first Docker run after fixes.

## User Setup Required

None - tests execute in Docker environment with no external dependencies.

## Test Coverage Summary

**Phase 1 (Hierarchy) - 26 tests:**
- Parent-child relationships, circular reference prevention, depth limits, level computation, cascade deletion

**Phase 2 (Sale Integration) - 18 tests:**
- Sale order segments, line assignment, cross-order constraints, subtotal/total computation

**Phase 3 (Project Integration & Security) - 20 tests:**
- PROJ-01: segment_id field on project.task (4 tests)
- PROJ-02: Field visibility in task form (verified via module installation)
- PROJ-03: Cross-order segment warning (4 tests - onchange warning, can save, no warning for same order, no warning without sale_order)
- Display name format (2 tests)
- Deletion protection (2 tests)
- Project sale_order_id change constraint (2 tests)
- SEC-02: Sales User create/read (2 tests)
- SEC-03: Sales Manager full CRUD (1 test)
- SEC-04: Sales User write restrictions (1 test)
- Edge cases (2 tests)

**Total: 64 tests, 0 failures, 0 errors**

## Next Phase Readiness

**Ready for Phase 4 (Automatic Task Creation):**
- All Phase 3 functionality validated with comprehensive tests
- Cross-order warning pattern confirmed working (onchange advisory, not blocking)
- Security rules verified with actual user contexts
- Deletion protection prevents orphaning tasks
- Test patterns established for future phases

**No blockers or concerns.**

**For Phase 4 implementation:**
- Reference test_project_task_segment.py for patterns on creating tasks with segments
- Use sale_line_id to link projects to orders (not sale_order_id directly)
- Remember segment_id is optional on tasks (allow manual tasks)
- Test with both Sales User and Sales Manager roles

---
*Phase: 03-project-extension-security*
*Completed: 2026-02-05*
