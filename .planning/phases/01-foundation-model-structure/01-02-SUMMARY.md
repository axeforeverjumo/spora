---
phase: 01-foundation-model-structure
plan: 02
subsystem: testing
tags: [odoo, python, testing, unittest, hierarchy, validation]

# Dependency graph
requires:
  - phase: 01-foundation-model-structure
    plan: 01
    provides: sale.order.segment model with hierarchy logic
provides:
  - Comprehensive test suite (26 tests) for sale.order.segment model
  - Test coverage for all HIER-01 through HIER-10 requirements
  - Validation of level computation, circular reference prevention, depth limits
  - Verification of parent_path, child_ids, cascade delete, sequence ordering
  - Docker-verified test execution on Odoo 18
affects: [02-sale-order-integration, 03-product-association, 04-project-conversion]

# Tech tracking
tech-stack:
  added: [Odoo TransactionCase, @tagged decorator, unittest framework]
  patterns: [Odoo test structure, assertRaises for constraint validation, TransactionCase for database rollback]

key-files:
  created:
    - addons/spora_segment/tests/__init__.py
    - addons/spora_segment/tests/test_sale_order_segment.py
  modified:
    - addons/spora_segment/models/sale_order_segment.py
    - addons/spora_segment/views/sale_order_segment_views.xml
    - config/odoo.conf

key-decisions:
  - "Circular references caught by _parent_store as UserError, not ValidationError from _has_cycle()"
  - "child_count needs @api.depends('child_ids') for automatic recomputation"
  - "Odoo 18 requires <list> view type, not <tree>"
  - "Test execution via Odoo shell more reliable than --test-tags for development"

patterns-established:
  - "Odoo test pattern: TransactionCase + @tagged('at_install') + setUpClass"
  - "Test organization: one test per requirement + edge cases"
  - "assertRaises for constraint validation with clear error messages"
  - "Bug fix workflow: run tests, identify failures, fix code, re-run"

# Metrics
duration: 29min
completed: 2026-02-05
---

# Phase 01 Plan 02: Comprehensive Hierarchy Testing Summary

**26 passing tests validating all HIER requirements: level computation, circular reference prevention, depth limits, parent_path, cascade delete, sequence ordering - all verified on Odoo 18 Docker**

## Performance

- **Duration:** 29 min
- **Started:** 2026-02-05T15:12:48Z
- **Completed:** 2026-02-05T15:42:20Z
- **Tasks:** 2
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments
- Created comprehensive test suite with 26 test methods covering all HIER requirements
- All tests pass with 0 failures and 0 errors on Odoo 18 Docker
- Test coverage includes:
  - **HIER-01/02:** parent_id and child_ids relationships
  - **HIER-03:** parent_path population and format validation
  - **HIER-04:** Level computation at all depths (1-4) with reparenting
  - **HIER-05:** Circular reference prevention (direct, indirect, self-reference)
  - **HIER-06:** 4-level depth limit with critical subtree reparenting test
  - **HIER-07:** Sequence ordering
  - **HIER-08/09/10:** Segment flexibility (leaf, branch, both)
  - **Edge cases:** Cascade delete, child_count, active field, batch create
- Fixed 3 bugs discovered during testing:
  - Odoo 18 view syntax (<list> not <tree>)
  - Missing @api.depends on child_count
  - Circular reference exception type (UserError from _parent_store)
- Module installs cleanly and all tests execute successfully in Docker

## Task Commits

Each task and bug fix was committed atomically:

1. **Task 1: Write comprehensive hierarchy tests** - `5b2c53a` (test)
2. **Bug fix: Odoo 18 view syntax and db config** - `6f2850a` (fix)
3. **Bug fix: Test failures and child_count computation** - `c2409b7` (fix)

## Files Created/Modified
- `addons/spora_segment/tests/__init__.py` - Test package initialization
- `addons/spora_segment/tests/test_sale_order_segment.py` - 26 test methods (372 lines)
- `addons/spora_segment/models/sale_order_segment.py` - Added @api.depends to child_count
- `addons/spora_segment/views/sale_order_segment_views.xml` - Changed tree to list for Odoo 18
- `config/odoo.conf` - Added database connection settings for CLI commands

## Decisions Made

**1. Expect UserError for circular references, not ValidationError**
- Rationale: Odoo's _parent_store._parent_store_update() raises UserError("Recursion Detected") before our @api.constrains('parent_id') runs. This is Odoo framework behavior, not a bug.

**2. child_count requires @api.depends('child_ids')**
- Rationale: Without @api.depends, computed field is not automatically recomputed when child_ids changes. Test failure revealed this bug.

**3. Odoo 18 uses <list> view type, not <tree>**
- Rationale: Odoo 18 changed XML schema. view_mode also changes from "tree,form" to "list,form". Module installation error revealed this.

**4. Use Odoo shell for test execution in development**
- Rationale: --test-tags flag in docker run hangs or produces no output. Odoo shell with unittest runner provides immediate verbose feedback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Odoo 18 view type incompatibility**
- **Found during:** Task 2 - module installation
- **Issue:** Module installation failed with "Invalid view type: 'tree'". Odoo 18 requires <list> instead of <tree>.
- **Fix:** Changed all `<tree>` tags to `<list>` and view_mode from "tree,form" to "list,form"
- **Files modified:** addons/spora_segment/views/sale_order_segment_views.xml
- **Commit:** 6f2850a

**2. [Rule 1 - Bug] Missing @api.depends on child_count**
- **Found during:** Task 2 - test execution
- **Issue:** test_child_count_computed failed with "0 != 3". child_count was not recomputing when children were added.
- **Fix:** Added `@api.depends('child_ids')` decorator to `_compute_child_count` method
- **Files modified:** addons/spora_segment/models/sale_order_segment.py
- **Commit:** c2409b7

**3. [Rule 1 - Bug] Wrong exception type in circular reference tests**
- **Found during:** Task 2 - test execution
- **Issue:** Tests expected ValidationError but Odoo _parent_store raises UserError for circular references
- **Fix:** Changed assertRaises(ValidationError) to assertRaises(UserError) in 3 tests
- **Files modified:** addons/spora_segment/tests/test_sale_order_segment.py
- **Commit:** c2409b7

**4. [Rule 1 - Bug] Incorrect test scenario in test_depth_limit_reparent_blocked**
- **Found during:** Task 2 - test execution
- **Issue:** Test scenario (L2 parent + 2-level subtree) results in L3->L4 which is allowed, not blocked
- **Fix:** Changed to L3 parent + 2-level subtree = L4->L5->L6 which correctly exceeds limit
- **Files modified:** addons/spora_segment/tests/test_sale_order_segment.py
- **Commit:** c2409b7

**5. [Rule 3 - Blocking] Added database config to odoo.conf**
- **Found during:** Task 2 - CLI command execution
- **Issue:** `odoo` CLI commands in Docker container couldn't connect to database (socket error)
- **Fix:** Added db_host, db_port, db_user, db_password to config/odoo.conf
- **Files modified:** config/odoo.conf
- **Commit:** 6f2850a

## Issues Encountered

**Docker test execution challenges**
- **Issue:** `--test-tags` flag produced no output or hung in docker run
- **Workaround:** Used Odoo shell with Python unittest runner for verbose test output
- **Impact:** Testing workflow requires Odoo shell, not CLI --test-tags flag
- **Future:** Consider running tests via pytest or test runner script

## User Setup Required

None - all testing infrastructure is automated via Docker.

## Next Phase Readiness

**Ready for Phase 2:** sale.order.segment model is fully tested and validated on Odoo 18.

**Phase 2 will:**
- Integrate segment model with sale.order
- Add segment tree view to sale order form
- Add domain constraint for parent_id (same order_id)

**Test suite provides:**
- Regression protection for Phase 2 changes
- Living documentation of expected behavior
- Confidence in hierarchy logic correctness

**No blockers:** All hierarchy requirements validated and passing.

**Technical observations:**
- Odoo _parent_store provides circular reference detection automatically (UserError)
- Our _check_hierarchy constraint provides depth limit validation (ValidationError)
- Both mechanisms work together correctly

---
*Phase: 01-foundation-model-structure*
*Completed: 2026-02-05*
