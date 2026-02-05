# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-05)

**Core value:** Conversión automática de estructura jerárquica de presupuesto a tareas de proyecto manteniendo relaciones padre-hijo
**Current focus:** Phase 4 - Automated Task Creation (context complete, ready for planning)

## Current Position

Phase: 4 of 5 (Automated Task Creation)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-05 — Completed 04-01-PLAN.md (Hierarchical task creation from segments)

Progress: [███████░░░] 70%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 7 min
- Total execution time: 0.83 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 - Foundation & Model Structure | 2 | 31 min | 16 min |
| 02 - Sale Order Integration | 2 | 7 min | 4 min |
| 03 - Project Extension & Security | 2 | 6 min | 3 min |
| 04 - Automated Task Creation | 1 | 6 min | 6 min |

**Recent Trend:**
- Last 5 plans: 02-02 (5min), 03-01 (2min), 03-02 (4min), 04-01 (6min)
- Trend: Consistent fast execution, average 4-6 min per plan

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Relación padre-hijo automática vs selector manual de nivel: Nivel se calcula automáticamente según parent_id
- Permitir productos en segmentos con hijos: Segmentos pueden tener productos Y sub-segmentos simultáneamente
- Conversión automática al confirmar: Workflow fluido sin pasos manuales
- Límite 4 niveles: Balance entre flexibilidad y complejidad
- Use _has_cycle() not _check_recursion(): Odoo 18 standard for circular reference detection (01-01)
- Compute level from parent_id.level: Avoids constraint timing issues with parent_path (01-01)
- Include order_id in Phase 1: Prevents model migration between phases (01-01)
- ondelete='cascade' on parent_id: Segments belong to parent conceptually (01-01)
- Circular refs caught by _parent_store as UserError: Framework behavior before constraint runs (01-02)
- child_count needs @api.depends('child_ids'): Required for automatic recomputation (01-02)
- Odoo 18 requires <list> not <tree>: View schema change in Odoo 18 (01-02)
- Test via Odoo shell not --test-tags: More reliable output in development (01-02)
- Use view_mode='list,form' not 'tree,form': Odoo 18 syntax consistency (02-01)
- store=True on computed Monetary fields: Performance with recursive totals (02-01)
- Domain + @api.constrains pattern: UI filtering + data integrity backup (02-01)
- Dotted path in @api.depends('line_ids.price_subtotal'): Tracks field changes, not just record add/remove (02-01)
- Recursive @api.depends('child_ids.total'): Creates cascade recomputation up hierarchy (02-01)
- currency_id as related field: Required for Monetary field rendering (02-01)
- Use Exception base class in assertRaises: For required field validation compatibility (02-02)
- Phase 1 tests updated with order_id: Required field from Phase 2 affects Phase 1 tests (02-02)
- View context uses 'id' not 'active_id': Form view compatibility in Odoo 18 (02-02)
- Onchange warning (not constraint) for cross-order segment: Soft validation allows user to proceed after acknowledgment (03-01)
- Separate read/write record rules for Sales Users: Enables read-all, write-own access pattern (03-01)
- segment_id ondelete='restrict': Database-level backup for Python @api.ondelete protection (03-01)
- segment_id positioned after project_id: Logical field grouping in task form (03-01)
- Use sale_line_id to link projects to orders: project.sale_order_id is readonly related field from sale_line_id.order_id (03-02)
- Set fields explicitly on .new() records for onchange tests: Ensures field resolution before calling onchange methods (03-02)
- Product type 'service' for project-related products: Standard Odoo pattern for products generating project tasks (03-02)
- Execute segment-to-task conversion BEFORE native Odoo flow: Full control prevents duplicates and unwanted tasks (04-context)
- Extend native Odoo flow, don't replace: Odoo already creates projects/tasks, we add hierarchical conversion (04-context)
- Products without segment_id handled by Odoo: Most products (90%+) will be in segments anyway (04-context)
- Idempotent task creation: Check existing segment_id tasks before creating to handle re-confirmation (04-context)
- Task description contains product listings: Format product descriptions in task.description field (04-context)
- Savepoints for isolated failures: Batch task creation with savepoints prevents one failure from blocking all (04-context)
- Use allocated_hours not planned_hours: Odoo 18 field rename (04-01)
- Call super().action_confirm() FIRST: Ensures project exists before creating segment tasks (04-01)
- BFS level-by-level segment processing: Guarantees parent tasks exist before children (04-01)
- segment_to_task mapping dict pattern: Enables parent_id resolution across hierarchy levels (04-01)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-05 20:03 UTC (plan execution)
Stopped at: Completed 04-01-PLAN.md - Automated hierarchical task creation from segments on sale order confirmation
Next step: Execute 04-02-PLAN.md (Integration testing and refinement) or continue to Phase 5
Resume file: None

---
*State initialized: 2026-02-05*
*Last updated: 2026-02-05 20:03 UTC*
