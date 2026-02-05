---
phase: 02-sale-order-integration
plan: 01
subsystem: sale-integration
tags: [odoo, python, xml, sale-order, computed-fields, one2many, many2one]

# Dependency graph
requires:
  - phase: 01-foundation-model-structure
    provides: sale.order.segment model with hierarchy
provides:
  - sale.order extension with segment_ids One2many and segment_count computed field
  - sale.order.line extension with segment_id Many2one and cross-order validation
  - sale.order.segment with order_id (required), currency_id, line_ids, subtotal, total
  - Computed subtotal from line_ids.price_subtotal with store=True
  - Computed total recursively from subtotal + child_ids.total with store=True
  - Smart button on sale order form with segment count badge
  - Segments tab in sale order form with inline editable list
  - Order Lines tab in segment form showing assigned products
affects: [03-project-extension-security, 04-automated-task-creation]

# Tech tracking
tech-stack:
  added: []
  patterns: [model inheritance with _inherit, computed Monetary fields with recursive dependencies, inline list views with context propagation, smart buttons with action_view methods, domain constraints for referential integrity]

key-files:
  created:
    - addons/spora_segment/models/sale_order.py
    - addons/spora_segment/models/sale_order_line.py
    - addons/spora_segment/views/sale_order_views.xml
  modified:
    - addons/spora_segment/models/sale_order_segment.py
    - addons/spora_segment/models/__init__.py
    - addons/spora_segment/__manifest__.py
    - addons/spora_segment/views/sale_order_segment_views.xml

key-decisions:
  - "Use view_mode='list,form' not 'tree,form' (Odoo 18 syntax from Phase 1)"
  - "store=True on computed Monetary fields for performance with recursive totals"
  - "Domain on Many2one fields for UX + @api.constrains for data integrity backup"
  - "Context propagation with {'default_order_id': active_id} for automatic field population"
  - "Dotted path in @api.depends('line_ids.price_subtotal') to track price changes, not just line add/remove"
  - "Recursive dependency @api.depends('child_ids.total') creates cascade recomputation up hierarchy"
  - "currency_id as related field from order_id.currency_id required for Monetary field rendering"
  - "optional='hide' on segment_id in order line tree to avoid cluttering default view"

patterns-established:
  - "Model extension pattern: _inherit with One2many/Many2one bidirectional relationships"
  - "Computed field pattern: @api.depends with dotted paths for related record fields"
  - "Recursive aggregation: sum(recordset.mapped('field')) for totals"
  - "Smart button pattern: computed count + oe_stat_button + action_view method returning ir.actions.act_window"
  - "Inline list view: <field><list>...</list></field> within parent form with context propagation"
  - "Domain constraint pattern: UI domain filter + Python @api.constrains validation"

# Metrics
duration: 2min
completed: 2026-02-05
---

# Phase 02 Plan 01: Sale Order Integration Summary

**Bidirectional integration between sale.order.segment, sale.order, and sale.order.line with computed subtotals/totals, smart button navigation, and inline segment management tab**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-05T17:02:03Z
- **Completed:** 2026-02-05T17:04:24Z
- **Tasks:** 2
- **Files modified:** 7 (3 created, 4 modified)

## Accomplishments

- Extended sale.order with segment_ids (One2many), segment_count (computed), action_view_segments method
- Extended sale.order.line with segment_id (Many2one) and cross-order validation constraint
- Modified sale.order.segment: order_id now required, added currency_id, line_ids, subtotal, total fields
- Implemented computed subtotal (@api.depends('line_ids.price_subtotal')) with store=True
- Implemented recursive computed total (@api.depends('subtotal', 'child_ids.total')) with cascade recomputation
- Added parent_same_order constraint and domain filter on parent_id to prevent cross-order hierarchy
- Created sale_order_views.xml with smart button (fa-sitemap icon) and Segments tab (inline list)
- Updated sale_order_segment_views.xml with subtotal/total columns and Order Lines tab
- Module updates cleanly in Odoo 18 Docker without errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create model extensions and modify segment model** - `1074fbc` (feat)
2. **Task 2: Create and update XML views for sale order integration** - `1667316` (feat)

## Files Created/Modified

**Created:**
- `addons/spora_segment/models/sale_order.py` - sale.order extension with segment_ids, segment_count, action_view_segments
- `addons/spora_segment/models/sale_order_line.py` - sale.order.line extension with segment_id and constraint
- `addons/spora_segment/views/sale_order_views.xml` - Smart button and Segments tab inheritance

**Modified:**
- `addons/spora_segment/models/sale_order_segment.py` - Added order_id (required), currency_id, line_ids, subtotal, total, parent_same_order constraint, parent_id domain
- `addons/spora_segment/models/__init__.py` - Imported sale_order and sale_order_line
- `addons/spora_segment/__manifest__.py` - Added sale_order_views.xml to data list
- `addons/spora_segment/views/sale_order_segment_views.xml` - Added subtotal, total, order_id columns in list; Order Lines tab in form

## Decisions Made

**1. Use dotted path in @api.depends for line field changes**
- Rationale: `@api.depends('line_ids.price_subtotal')` triggers recomputation when ANY line's price changes, not just when lines are added/removed. Handles quantity/price updates automatically.

**2. Recursive dependency with child_ids.total**
- Rationale: `@api.depends('child_ids.total')` creates cascade: when grandchild total changes, child recomputes, triggering parent recomputation. Propagates changes up hierarchy automatically.

**3. Store computed Monetary fields**
- Rationale: With `store=True`, totals are cached in database. Only recompute when dependencies change, not on every read. Critical for performance with hierarchical aggregation.

**4. Domain on Many2one + Python constraint for referential integrity**
- Rationale: Domain filters UI dropdown (better UX - users don't see invalid choices). Python constraint validates at database level (data integrity - catches API/import violations).

**5. Currency field as related from order_id**
- Rationale: Monetary field type requires a related currency_id field on same model. Segment doesn't inherit from sale.order, so must explicitly relate currency_id.

**6. Context propagation with active_id**
- Rationale: `context="{'default_order_id': active_id}"` auto-populates order_id when creating segment from sale order form. Works with quick-create and full form.

**7. optional="hide" on segment_id in order line tree**
- Rationale: Avoids cluttering default order line view. Column available via toggle menu when needed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - Python and XML syntax validated successfully, module update in Docker completed without errors.

## User Setup Required

None - no external service configuration required.

Module update command:
```bash
docker compose exec odoo odoo -d spora -u spora_segment --stop-after-init
```

## Next Phase Readiness

**Ready for Phase 3:** Sale order integration is complete and functional.

**Phase 3 will:**
- Extend project.task with segment_id field for traceability
- Add segment-to-order validation constraint on tasks
- Define security rules for segment access (Sales User, Sales Manager)
- Ensure segment permissions respect parent sale order access rights

**No blockers:** All sale order integration infrastructure (models, views, computed fields) is in place.

**Technical debt:** None - followed Odoo 18 best practices from Phase 2 research.

**Known behavior:**
- Subtotal and total fields are computed and stored. Changes to line prices or child segment totals trigger automatic recomputation via @api.depends cascade.
- Smart button only appears when segment_count > 0 (invisible="segment_count == 0").
- Domain constraints prevent cross-order segment hierarchy and line assignment at UI level. Python constraints provide backup validation.

---
*Phase: 02-sale-order-integration*
*Completed: 2026-02-05*
