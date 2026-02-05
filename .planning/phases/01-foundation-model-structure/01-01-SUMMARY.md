---
phase: 01-foundation-model-structure
plan: 01
subsystem: database
tags: [odoo, python, postgresql, orm, hierarchy, parent-store]

# Dependency graph
requires:
  - phase: project-initialization
    provides: Docker environment, Odoo 18 instance, PostgreSQL 15
provides:
  - sale.order.segment model with parent_id/child_ids hierarchy
  - _parent_store=True with parent_path for O(1) hierarchy queries
  - Computed level field (1-4) with recursive recomputation
  - Constraint validation for circular references and 4-level depth limit
  - Subtree depth validation preventing reparenting violations
  - Security rules for Sales User and Sales Manager
  - Tree, form, and search views with Odoo 17+ syntax
  - Module structure ready for Phase 2 integration
affects: [02-sale-order-integration, 03-product-association, 04-project-conversion]

# Tech tracking
tech-stack:
  added: [spora_segment custom module, Odoo _parent_store pattern]
  patterns: [hierarchical model with parent_id/child_ids, _has_cycle() for circular ref detection, recursive computed fields, constraint methods walking parent chain]

key-files:
  created:
    - addons/spora_segment/__init__.py
    - addons/spora_segment/__manifest__.py
    - addons/spora_segment/models/__init__.py
    - addons/spora_segment/models/sale_order_segment.py
    - addons/spora_segment/security/ir.model.access.csv
    - addons/spora_segment/views/sale_order_segment_views.xml
  modified: []

key-decisions:
  - "Used _has_cycle() instead of deprecated _check_recursion() (Odoo 18 standard)"
  - "Computed level from parent_id.level with recursive=True (not parent_path) to avoid constraint timing issues"
  - "Included order_id field now (optional) to avoid migration in Phase 2"
  - "Used ondelete='cascade' on parent_id (segments belong to parent, delete together)"
  - "Walked descendant tree in constraint to prevent reparenting creating depth violations"

patterns-established:
  - "Hierarchical model pattern: _parent_store=True + explicit parent_path field"
  - "Constraint combining circular ref check + depth limit + subtree validation in single method"
  - "Odoo 17+ view syntax: invisible='expression' instead of attrs={}"
  - "Stat button pattern for child navigation with action_view_children method"

# Metrics
duration: 2min
completed: 2026-02-05
---

# Phase 01 Plan 01: Foundation & Model Structure Summary

**Odoo 18 sale.order.segment hierarchical model with _parent_store, computed level, circular reference prevention, 4-level depth constraint, and complete security/views**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-05T15:09:01Z
- **Completed:** 2026-02-05T15:10:50Z
- **Tasks:** 2
- **Files modified:** 6 (all created)

## Accomplishments
- Complete spora_segment Odoo module with hierarchical sale.order.segment model
- _parent_store=True with parent_path field for O(1) hierarchy queries
- Computed level field using recursive parent_id.level dependency
- Constraint validates circular references (_has_cycle) and 4-level depth limit
- Subtree depth validation prevents reparenting violations (walks descendants)
- Security rules: Sales User (CRUD minus delete), Sales Manager (full CRUD)
- Tree/form/search views using Odoo 17+ inline expression syntax
- order_id field included (optional) to avoid Phase 2 migration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create module scaffold and segment model with hierarchy logic** - `17201a2` (feat)
2. **Task 2: Create segment views (tree, form, search) and menu action** - `c52bd43` (feat)

## Files Created/Modified
- `addons/spora_segment/__init__.py` - Module initialization importing models
- `addons/spora_segment/__manifest__.py` - Module metadata, depends on 'sale', declares security and views
- `addons/spora_segment/models/__init__.py` - Models package initialization
- `addons/spora_segment/models/sale_order_segment.py` - sale.order.segment model with hierarchy, constraints, computed fields
- `addons/spora_segment/security/ir.model.access.csv` - Access rules for Sales User and Sales Manager
- `addons/spora_segment/views/sale_order_segment_views.xml` - Tree/form/search views and window action

## Decisions Made

**1. Use _has_cycle() instead of _check_recursion()**
- Rationale: _check_recursion() is deprecated in Odoo 18, _has_cycle() is the standard method with inverted semantics (returns True if cycle exists)

**2. Compute level from parent_id.level, not parent_path**
- Rationale: parent_path is recomputed AFTER @api.constrains fires, causing timing issues when constraint checks level. Recursive parent_id.level guarantees correct value at constraint time.

**3. Include order_id field in Phase 1**
- Rationale: Module already depends on 'sale', including optional order_id now avoids model migration between phases. Phase 2 will enforce required via view context.

**4. Walk descendant tree in constraint**
- Rationale: When reparenting a segment with children, only the moved segment triggers constraint (children's parent_id unchanged). Without subtree validation, deep hierarchies could exceed limit.

**5. Use ondelete='cascade' on parent_id**
- Rationale: Segments belong to their parent conceptually. Matches Odoo product.category behavior and prevents orphaned records.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - Python and XML syntax validated successfully, all verification checks passed.

## User Setup Required

None - no external service configuration required.

Module is ready for installation in Odoo:
```bash
docker compose exec odoo odoo -d spora -i spora_segment --stop-after-init
```

## Next Phase Readiness

**Ready for Phase 2:** sale.order.segment model is complete and ready for integration with sale.order.

**Phase 2 will:**
- Make order_id required on segment model
- Add segment_ids One2many to sale.order
- Add domain constraint ensuring parent_id belongs to same order
- Create segment tree view embedded in sale order form

**No blockers:** All foundation infrastructure (model, security, views) is in place.

**Technical debt:** None - followed Odoo 18 best practices from research (product.category pattern).

---
*Phase: 01-foundation-model-structure*
*Completed: 2026-02-05*
