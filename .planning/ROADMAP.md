# Roadmap: Spora - Presupuestos Jerárquicos

## Overview

This roadmap builds a custom Odoo 18 module that transforms flat sale order line items into hierarchical budget segments (up to 4 levels deep), then automatically converts that structure into matching parent-child project tasks when the order is confirmed. Starting with the foundational segment model and hierarchy logic, we progressively integrate with sale orders, extend project tasks for traceability, implement the core automation workflow, and polish the user experience.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Model Structure** - Create segment model with hierarchy and validation
- [x] **Phase 2: Sale Order Integration** - Connect segments to sale orders with computed totals
- [x] **Phase 3: Project Extension & Security** - Extend project tasks and define access rights
- [ ] **Phase 4: Automated Task Creation** - Implement segment-to-task conversion workflow
- [ ] **Phase 5: User Experience & Polish** - Enhance navigation, ordering, and visual feedback

## Phase Details

### Phase 1: Foundation & Model Structure
**Goal**: Users can create and manage hierarchical segment structures with automatic validation
**Depends on**: Nothing (first phase)
**Requirements**: HIER-01, HIER-02, HIER-03, HIER-04, HIER-05, HIER-06, HIER-07, HIER-08, HIER-09, HIER-10
**Success Criteria** (what must be TRUE):
  1. User can create segment with parent-child relationships via parent_id field
  2. System automatically calculates segment level (1-4) based on depth in hierarchy
  3. System prevents circular references (segment cannot be its own ancestor)
  4. System blocks creation of segments deeper than 4 levels
  5. User can create segments with products only, sub-segments only, or both simultaneously
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md -- Module scaffold, segment model with hierarchy logic, security, and views
- [ ] 01-02-PLAN.md -- Comprehensive hierarchy tests and Docker verification

### Phase 2: Sale Order Integration
**Goal**: Users can organize sale order line items into hierarchical segments with automatic subtotal calculations
**Depends on**: Phase 1
**Requirements**: SALE-01, SALE-02, SALE-03, SALE-04, SALE-05, SALE-06, SALE-07, SALE-08, SALE-09, SALE-10, SALE-11
**Success Criteria** (what must be TRUE):
  1. User can create segments directly from sale order form view
  2. User can assign order lines (products) to specific segments
  3. User sees expandable tree view of all segments within sale order
  4. System displays subtotal for each segment (sum of direct products)
  5. System displays total for each segment (subtotal + all sub-segment totals)
  6. User can expand/collapse hierarchy levels to navigate structure
  7. Smart button on sale order shows segment count and opens filtered view
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md -- Model extensions (sale.order, sale.order.line, segment computed totals) and views (smart button, segment tab, inline lists)
- [ ] 02-02-PLAN.md -- Integration tests for all SALE requirements and Docker verification

### Phase 3: Project Extension & Security
**Goal**: Project tasks can trace back to originating segments with proper access controls
**Depends on**: Phase 2
**Requirements**: PROJ-01, PROJ-02, PROJ-03, SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. User sees segment reference field when viewing project task
  2. System validates that referenced segment belongs to task's linked sale order
  3. Sales User can read and create segments for their quotations
  4. Sales Manager can create, read, update, and delete segments
  5. Segment permissions automatically respect parent sale order access rights
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md -- Model extensions (project.task segment_id, segment display_name, deletion protection, project constraint, views, security rules)
- [x] 03-02-PLAN.md -- Comprehensive tests for all PROJ and SEC requirements and Docker verification

### Phase 4: Automated Task Creation
**Goal**: Confirming a sale order automatically creates project with hierarchical tasks matching segment structure
**Depends on**: Phase 3
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05, AUTO-06, AUTO-07, AUTO-08, AUTO-09, AUTO-10, AUTO-11, AUTO-12
**Success Criteria** (what must be TRUE):
  1. User confirms sale order and project is created automatically (if not exists)
  2. System creates one task per segment maintaining parent-child hierarchy
  3. Top-level segments create tasks with no parent_id (root tasks)
  4. Child segment tasks have parent_id pointing to parent segment's task
  5. Task receives segment name, products as description, calculated hours from product quantities
  6. Task receives assigned user and date range from segment (if defined)
  7. Task links back to originating segment via segment_id field
  8. If one task creation fails, other tasks in batch are not affected (transaction isolation)
**Plans**: TBD

Plans:
- [ ] 04-01: [To be planned]

### Phase 5: User Experience & Polish
**Goal**: Users navigate segment hierarchies efficiently with visual feedback and intuitive ordering
**Depends on**: Phase 4
**Requirements**: UX-01, UX-02, UX-03, UX-04, UX-05, UX-06
**Success Criteria** (what must be TRUE):
  1. Tree view displays hierarchical indentation showing segment depth visually
  2. User sees full path breadcrumb for segment (e.g., "Phase 1 / Materials / Flyers")
  3. User can reorder sibling segments via drag-and-drop handle
  4. Segment form shows smart button to child segments with count
  5. Tree view displays product count for each segment
**Plans**: TBD

Plans:
- [ ] 05-01: [To be planned]

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Model Structure | 2/2 | Complete | 2026-02-05 |
| 2. Sale Order Integration | 2/2 | Complete | 2026-02-05 |
| 3. Project Extension & Security | 2/2 | Complete | 2026-02-05 |
| 4. Automated Task Creation | 0/TBD | Not started | - |
| 5. User Experience & Polish | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-05*
*Last updated: 2026-02-05*
