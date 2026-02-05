# Project Research Summary

**Project:** Custom Odoo 18 Module - Hierarchical Budget Segments
**Domain:** Odoo ERP Custom Module Development
**Researched:** 2026-02-05
**Confidence:** HIGH

## Executive Summary

This project involves building a custom Odoo 18 module that adds hierarchical budget segments to sale orders, then automatically creates matching hierarchical project tasks when orders are confirmed. Research shows this domain is well-documented with established patterns: hierarchical models use `parent_id` with `_parent_store` optimization, model extension via `_inherit` is the standard approach, and automated actions handle workflow triggers.

The recommended approach uses Odoo's native hierarchical model pattern (parent_id/child_ids with _parent_store=True), extends sale.order and project.task via inheritance rather than modification, and implements the segment-to-task workflow using either automated actions or method overrides. The core stack is straightforward: Odoo 18.0 (Python 3.10+, PostgreSQL 15), Docker for development, and the ORM for all data operations. The module structure follows Odoo conventions with models, views, and security properly separated.

The primary risks center on hierarchical model performance and transaction management. Without `_parent_store`, tree queries degrade exponentially past 100 records. Computed fields for subtotals require complete `@api.depends` declarations or data becomes stale. Automated task creation must use savepoints to isolate batch operation failures. The extension of sale.order.line is particularly fragile - improper inheritance breaks onchange chains and the sales workflow. All these pitfalls are avoidable with proper patterns applied from the start.

## Key Findings

### Recommended Stack

**Odoo 18.0 with native hierarchical patterns provides the foundation.** Python 3.10+ is mandatory (Odoo 18 requirement), PostgreSQL 15 is recommended (12+ supported), and Docker Compose is the standard development environment. The key insight is that Odoo's built-in frameworks handle most complexity: the ORM manages data relationships, QWeb provides view templating, and Automated Actions handle workflow triggers without custom controllers.

**Core technologies:**
- **Odoo 18.0**: ERP framework with built-in ORM, workflow engine, UI framework — provides all standard modules (sale, project) and is the required base platform
- **Python 3.10+**: Backend language — minimum version 3.10 required by Odoo 18 for new language features
- **PostgreSQL 15**: Database — highly recommended for optimal performance and compatibility (versions 12-16 supported)
- **Docker 24.0+**: Containerization — standard for Odoo 18 development, provides environment consistency and zero local dependencies
- **Odoo ORM API**: Data layer — always use instead of raw SQL for safe operations, recordsets, computed fields, and automatic transactions
- **OWL 2**: Frontend framework — JavaScript UI framework for reactive components if custom web interfaces needed (standard views likely sufficient)

**Critical version constraints:**
- Python 3.7-3.9: NOT supported (use 3.10, 3.11, or 3.13)
- PostgreSQL 18: NOT supported (use 15 recommended, or 16)
- Deprecated Odoo patterns: `@api.one`, `@api.multi`, `name_get()`, `_sequence` attribute

### Expected Features

Research into hierarchical Odoo modules (product categories, project subtasks, analytic plans) reveals a consistent pattern of table stakes features and well-understood differentiation opportunities.

**Must have (table stakes):**
- **parent_id/child_ids relationship** — standard Odoo hierarchical pattern (Many2one parent_id, One2many child_ids) with circular reference prevention
- **Tree view with expand/collapse** — users expect visual hierarchy navigation with recursive tree view (recursive="1" attribute)
- **Automatic subtotal calculations** — parent segments must aggregate child values (products, hours, amounts) using computed fields with proper dependencies
- **Sequence ordering** — siblings need defined order within same parent level via sequence field
- **Smart button navigation** — quick access from parent to children and vice versa via filtered views

**Should have (competitive advantage):**
- **Auto-create child tasks from segments** — THE core differentiator: maintains hierarchy structure when converting sale orders to project tasks with data transfer (products, hours, responsible, dates)
- **parent_store optimization** — set `_parent_store = True` for fast hierarchy queries on large datasets (>100 segments or >3 levels)
- **Full path/breadcrumb display** — computed "Segment A / Segment B / Current" field for context (product.category pattern)
- **Drag & drop reordering** — sequence field with handle widget in tree view, validate parent changes to prevent circular refs
- **Inherited field values from parent** — child segments inherit defaults (responsible, dates, project) using `@api.onchange` for parent_id

**Defer (v2+):**
- **Visual hierarchy indicators** — custom tree lines, icons (requires custom JS, low ROI initially)
- **Move subtree between parents** — edge case, manual move works (complex validation, rare use)
- **Hierarchy-aware search** — standard search sufficient initially (wait to see actual search patterns)
- **Export/import with hierarchy** — manual creation acceptable for MVP (complex import logic, edge cases)
- **Copy with hierarchy** — useful for templating but workaround exists (create manually)

### Architecture Approach

**Standard Odoo module architecture with three-layer separation.** Models contain business logic (Python classes with ORM definitions), Views define presentation (XML with QWeb templates and XPath inheritance), Security controls access (CSV for model permissions, XML for record rules). The module extends existing models via `_inherit` pattern rather than modifying core code, ensuring upgrade safety.

**Major components:**

1. **sale.order.segment (NEW model)** — Core hierarchical model with parent_id/child_ids self-reference, belongs to sale.order via Many2one, contains segment-specific data (name, sequence, products, hours). Responsibility: maintain hierarchy structure, validate circular references, compute subtotals.

2. **sale.order (EXTENDED)** — Adds segment_ids One2many relationship, extends action_confirm() to trigger automation. Responsibility: manage segment collection, coordinate task creation workflow on confirmation.

3. **sale.order.line (EXTENDED)** — Adds segment_id Many2one to link order lines to specific segments. Responsibility: enable product allocation to segments, support subtotal calculations.

4. **project.task (EXTENDED)** — Adds segment_id Many2one to link tasks back to originating segments. Responsibility: maintain traceability from project execution to sales segments.

5. **Automated Action or Method Override** — Triggers on sale.order state change to 'sale', creates project.project (if needed), recursively creates project.task for each segment maintaining hierarchy. Responsibility: workflow automation, data transfer from segments to tasks.

**Key architectural patterns:**
- **Model extension via _inherit**: Extends existing models without modifying core code (upgrade-safe)
- **Hierarchical model with parent_id**: Self-referential Many2one creates tree structures with native Odoo support
- **View inheritance via XPath**: Surgically adds fields to existing forms using specific selectors
- **Automated actions with Python**: Server-side triggers executing on record events (alternative: override methods with super())

**Recommended build order:**
1. Module scaffold + manifest (establishes structure, dependencies)
2. sale.order.segment model (core new model, no dependencies)
3. sale.order, sale.order.line, project.task extensions (all depend on segment model)
4. Security files (ir.model.access.csv, security.xml)
5. Views (segment, sale order, task views)
6. Automated action (workflow automation, depends on all models)

### Critical Pitfalls

Research identified seven critical pitfalls with specific prevention strategies. The top five most relevant to this project:

1. **Missing _parent_store for Hierarchical Models** — Without `_parent_store = True`, hierarchy queries become exponentially slower (10+ seconds with 100 records at 5+ levels). ALWAYS set `_parent_store = True`, `_parent_name = 'parent_id'`, and add indexed `parent_path` field when using parent_id relationships. Address in Phase 1: Model Definition.

2. **Incomplete @api.depends Declarations** — Stored computed fields don't recompute when dependent data changes, showing stale values. Users see incorrect totals until manual recomputation. ALWAYS declare complete dependency chains using dotted notation (e.g., `@api.depends('child_ids.amount', 'line_ids.product_id.price')`). Trace dependencies through Many2one relationships. Address in Phase 1: Model Definition with verification in Phase 3: Testing.

3. **Breaking sale.order.line Inheritance** — Adding fields to sale.order.line can break onchange chains (partner_id, product_id) causing "line has been modified" warnings and unusable sales orders. NEVER use both `_name` and `_inherit` (only `_inherit`), avoid required=True on custom fields that conflict with product_id logic, test complete sales workflow including partner changes. Address in Phase 2: Extension Development.

4. **Transaction Mismanagement in Automated Actions** — Processing 1,000 records where #999 fails rolls back all 999 previous records. Or manually calling cr.commit() causes data corruption on subsequent failures. NEVER call cr.commit() (let Odoo handle it), ALWAYS use savepoints for batch processing to isolate iteration failures, limit batch size (PostgreSQL slows after 64 savepoints). Address in Phase 2: Automated Actions.

5. **Missing Access Rights Definition** — Users get "Forbidden" errors even with correct views because every model needs explicit ir.model.access.csv. Developers testing as admin bypass ACL and forget to create access rights. ALWAYS create ir.model.access.csv with model definition, define access for each user group, order security files first in manifest. Address in Phase 1: Security Setup.

**Additional notable pitfalls:**
- **SQL Constraint Violations**: Adding UNIQUE constraints crashes on existing duplicate data (check data before adding, use migration scripts)
- **Over-Customization Breaking Upgrades**: Tight coupling with Odoo internals makes version upgrades difficult (minimize core modifications, follow documented APIs)

## Implications for Roadmap

Based on research findings, the roadmap should follow dependency order with early attention to performance and security patterns. The hierarchical model is foundational - everything depends on it being correct. Task automation comes last because it depends on all models being complete.

### Suggested Phase Structure

**Phase 1: Foundation & Hierarchy**
**Rationale:** The segment model is the foundation everything else builds on. Performance optimization (_parent_store) and validation (circular reference prevention) must be in place from the start - retrofitting is complex. Security setup prevents access errors during development.

**Delivers:**
- sale.order.segment model with parent_id/child_ids hierarchy
- _parent_store optimization for performance
- Circular reference prevention constraints
- Basic form and tree views for segment management
- Access rights (ir.model.access.csv)

**Addresses from FEATURES.md:**
- parent_id/child_ids relationship (table stakes)
- Prevent circular references (table stakes)
- Tree view with expand/collapse (table stakes)
- Multi-level depth support (table stakes)
- parent_store optimization (differentiator)

**Avoids from PITFALLS.md:**
- Missing _parent_store (Critical Pitfall #1)
- Missing access rights (Critical Pitfall #5)

**Research flag:** Standard patterns - skip phase research (well-documented hierarchical model pattern)

---

**Phase 2: Sale Order Integration**
**Rationale:** Must extend sale.order to hold segments before segments can be useful. sale.order.line extension is fragile (Pitfall #3) so needs careful implementation and testing. Computed fields for subtotals require complete @api.depends (Pitfall #2).

**Delivers:**
- sale.order extension with segment_ids One2many
- sale.order.line extension with segment_id Many2one
- Computed subtotal fields with proper @api.depends
- View inheritance to show segments in sale order form
- Sequence ordering within segment levels

**Addresses from FEATURES.md:**
- Automatic subtotal calculations (table stakes)
- Sequence ordering (table stakes)
- Smart button navigation (table stakes)

**Uses from STACK.md:**
- Model inheritance via _inherit
- View inheritance via XPath
- Computed fields with @api.depends

**Avoids from PITFALLS.md:**
- Breaking sale.order.line inheritance (Critical Pitfall #3)
- Incomplete @api.depends declarations (Critical Pitfall #2)

**Research flag:** Standard patterns - skip phase research (established extension patterns)

---

**Phase 3: Project Task Extension**
**Rationale:** Extends project.task to link back to segments, enabling traceability from execution to planning. Simpler than sale.order.line extension because project.task has fewer onchange chains.

**Delivers:**
- project.task extension with segment_id Many2one
- View inheritance to show segment reference in task form
- Validation that segment belongs to task's sale order

**Addresses from FEATURES.md:**
- (Foundation for auto-create differentiator)

**Uses from STACK.md:**
- Model inheritance via _inherit
- View inheritance via XPath

**Avoids from PITFALLS.md:**
- (Lower risk than sale.order.line, but still test workflow)

**Research flag:** Standard patterns - skip phase research

---

**Phase 4: Automated Task Creation**
**Rationale:** This is the core differentiator but depends on all previous models being complete and tested. Automated action must handle batch creation with proper transaction isolation (Pitfall #4). Recursive hierarchy traversal requires careful implementation.

**Delivers:**
- Automated action or action_confirm() override
- Project creation from confirmed sale orders
- Recursive task creation maintaining segment hierarchy
- Data transfer (name, description, planned hours, dates)
- Error isolation with savepoints for batch processing

**Addresses from FEATURES.md:**
- Auto-create child tasks from segments (PRIMARY DIFFERENTIATOR)
- Cascade delete/archive behavior (table stakes)

**Uses from STACK.md:**
- Automated Actions (data/automated_actions.xml)
- OR method override with super() pattern
- Batch operations via ORM

**Implements from ARCHITECTURE.md:**
- Automation layer workflow
- Data flow: sale.order → segments → project.tasks

**Avoids from PITFALLS.md:**
- Transaction mismanagement (Critical Pitfall #4)
- Performance with batch operations

**Research flag:** May need phase research for complex recursive algorithms and transaction patterns if problems emerge during implementation

---

**Phase 5: Enhancement & Polish**
**Rationale:** Quality-of-life improvements once core functionality is validated. Full path display, inherited field values, and drag-drop reordering enhance UX but aren't blocking for validation.

**Delivers:**
- Full path/breadcrumb display (complete_name computed field)
- Inherited field values from parent (@api.onchange)
- Drag & drop reordering (handle widget)
- Additional smart buttons and filtered views

**Addresses from FEATURES.md:**
- Full path display (table stakes, deferred)
- Drag & drop reordering (table stakes, deferred)
- Inherited field values (differentiator)

**Research flag:** Standard patterns - skip phase research

### Phase Ordering Rationale

1. **Hierarchical model first** because everything depends on it being correct. Performance optimization and validation must be in place from the start - retrofitting _parent_store requires data migration.

2. **Sale order integration second** because segments must connect to orders before they can be useful. The sale.order.line extension is the most fragile part (onchange chains) so it needs dedicated focus and testing.

3. **Project task extension third** because it's simpler than sale order and enables the automation. Keeping it separate from sale order integration reduces complexity.

4. **Automation last** because it depends on all models being complete. Transaction management and recursive traversal are complex enough to deserve focused attention.

5. **Enhancements in final phase** as quality-of-life improvements that don't block validation of core functionality.

**Dependency chain alignment:**
- Phase 1 creates foundation (segment model)
- Phase 2-3 extend existing models (sale, project)
- Phase 4 connects them (automation)
- Phase 5 polishes (UX improvements)

**Pitfall avoidance:**
- Critical patterns (_parent_store, @api.depends, access rights) established in Phase 1-2
- Fragile extensions (sale.order.line) isolated in Phase 2 for focused testing
- Transaction management (savepoints) addressed in Phase 4 when automation is implemented
- Performance testing throughout ensures scale assumptions are validated

### Research Flags

**Phases with standard patterns (skip phase research):**
- **Phase 1 (Hierarchical Model):** Well-documented pattern in Odoo official docs, product.category reference implementation available
- **Phase 2 (Sale Integration):** Standard model inheritance and view inheritance patterns
- **Phase 3 (Task Extension):** Same inheritance patterns as Phase 2
- **Phase 5 (Enhancements):** All standard Odoo features (computed fields, onchange, widgets)

**Phase potentially needing deeper research:**
- **Phase 4 (Automated Task Creation):** May need targeted research if recursive hierarchy traversal or transaction patterns become problematic. Standard approach is documented, but the recursive nature with data transfer and error isolation is complex enough that `/gsd:research-phase` might be valuable if implementation issues arise. Recommend: start with documented patterns, trigger research only if blocked.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official Odoo 18 documentation, verified version requirements, established Docker setup |
| Features | MEDIUM | Strong consensus from multiple hierarchical module examples (product categories, project subtasks, analytic plans), but limited examples of exact segment→task workflow |
| Architecture | HIGH | Standard Odoo module patterns, official documentation for inheritance and automated actions, well-established component structure |
| Pitfalls | MEDIUM | Mix of official sources (Odoo docs, GitHub issues) and community resources (forums, blogs). Pitfalls verified across multiple sources but some prevention strategies from single sources |

**Overall confidence:** HIGH

The core patterns (hierarchical models, model inheritance, automated actions) are well-documented with official sources. The specific workflow (segments→tasks) is a novel combination but built from standard components. The main uncertainty is in edge cases and performance at scale, which is typical for custom Odoo modules and addressable through testing.

### Gaps to Address

**Gap 1: Performance at scale** — Research shows _parent_store is critical for >100 records but actual performance profile depends on specific query patterns and computed field complexity. Handle during Phase 1 by implementing _parent_store from start, then validate with load testing (500+ segments at 5 levels) during Phase 3.

**Gap 2: sale.order.line extension edge cases** — Documented pitfalls about onchange conflicts exist, but specific interactions with this project's segment_id field are unknown. Handle during Phase 2 by extensive testing of the complete sales workflow (partner change, product selection, pricing, discounts, invoicing) before considering phase complete.

**Gap 3: Recursive task creation transaction safety** — Savepoint pattern is documented but applying it to recursive hierarchy traversal with 1000+ tasks needs validation. Handle during Phase 4 by implementing savepoint isolation, then testing with intentional failures at various points in batch (record 1, record 50, record 100).

**Gap 4: Upgrade path to Odoo 19** — Odoo 18→19 migration guide mentions tax_id → tax_ids changes, but impact on this specific module is unknown. Handle during Phase 1 architecture by following documented APIs and minimizing core modifications, then plan for upgrade testing when Odoo 19 is released.

## Sources

### Primary (HIGH confidence)
- **Odoo 18.0 Official Documentation**: ORM API, Module structure, Inheritance patterns, Automated actions, Security, Constraints, Coding guidelines
- **Odoo 19.0 Official Documentation**: Computed fields, View records, Testing framework (Odoo 19 docs used where Odoo 18 docs were identical)
- **GitHub Odoo Repository**: requirements.txt for version dependencies, issue tracker for documented bugs (#37468 compute dependencies, #17618 One2many onchange, #25168 duplicate values, #28381 SQL constraints)
- **Official Odoo Tutorials**: Sub-tasks documentation, Analytic accounting, Server framework tutorials

### Secondary (MEDIUM confidence)
- **OCA (Odoo Community Association)**: pylint-odoo linting tool, pytest-odoo testing plugin
- **Verified Community Resources**: Error handling and logging guide (braincuber.com), hierarchical models guide (hynsys.com), _parent_store discussion (Odoo forum), working with savepoint blog
- **Odoo Apps Store**: recursive_tree_view, project_wbs_gantt, project_hierarchy_view modules for pattern validation
- **Odoo Forum Discussions**: Multiple threads on hierarchical views, parent-child relationships, stored computed fields, validation errors

### Tertiary (LOW confidence - needs validation)
- **Development best practices blogs**: General Odoo customization advice from silentinfotech, nerithonx, moldstud
- **Third-party tutorials**: Docker Compose setup (dev.to), Odoo 18→19 migration guide (ksolves.com), version upgrade tutorial (Medium)

---
*Research completed: 2026-02-05*
*Ready for roadmap: yes*
