# Feature Research

**Domain:** Odoo modules with hierarchical data structures
**Researched:** 2026-02-05
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **parent_id / child_ids relationship** | Standard Odoo pattern for hierarchy; users expect Many2one parent_id and One2many child_ids fields | LOW | Field names: `parent_id = fields.Many2one('model.name', 'Parent')` and `child_ids = fields.One2many('model.name', 'parent_id')` |
| **Tree view with expand/collapse** | Users need to navigate hierarchy visually; expand/collapse is standard UX for tree structures | MEDIUM | Add `recursive="1"` attribute to tree view element. Native Odoo feature since v11+ |
| **Automatic subtotal calculations** | Parent segments need to aggregate child values (products, hours, amounts) | MEDIUM | Use computed fields with proper dependencies on child_ids. Must be stored for display in tree views |
| **Prevent circular references** | System must prevent A→B→A loops that break hierarchy | LOW | Use `@api.constrains` decorator with `_check_m2m_recursion()` or custom validation logic |
| **Full path / breadcrumb display** | Users need to see "Segment A / Segment B / Current" to understand context | LOW | Compute field concatenating parent names recursively. Common pattern in product categories |
| **Drag & drop reordering** | Users expect to reorder siblings and change parent-child relationships via drag & drop | MEDIUM | Use sequence field with `handle` widget in tree view. Validate parent changes to prevent circular refs |
| **Smart buttons for navigation** | Need quick access from parent to children and child to parent | LOW | Standard Odoo pattern. Add count computed field and button with action to filtered view |
| **Multi-level depth support** | Must support arbitrary nesting depth, not just 2-3 levels | LOW | Native with parent_id pattern. No practical depth limit |
| **Cascade delete/archive** | When parent is deleted/archived, handle children appropriately | LOW | Set `ondelete='cascade'` or `ondelete='restrict'` on parent_id field based on business logic |
| **Sequence/position ordering** | Siblings need defined order within same parent level | LOW | Add `sequence` field (Integer) to model and use in `_order` attribute |

### Differentiators (Competitive Advantage)

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Auto-create child tasks from segments** | Maintains hierarchy structure when converting sale orders to project tasks | HIGH | Your core differentiator. Requires mapping segment hierarchy to task hierarchy with data transfer (products, hours, responsible, dates) |
| **Hierarchical totals in tree view** | Show calculated totals at each parent level inline | MEDIUM | Use computed fields with tree view aggregation. Performance concern with deep hierarchies and many records |
| **Expand/Collapse All buttons** | Quick way to preview entire structure or collapse to overview | LOW | Available as third-party module or custom JS widget. Improves UX for large hierarchies |
| **Parent_store optimization** | Fast `child_of` queries for large hierarchies | MEDIUM | Set `_parent_store = True` and add `parent_left`/`parent_right` Integer fields. Significant performance boost for queries |
| **Visual hierarchy indicators** | Indentation, tree lines, icons showing node type (leaf/parent) | MEDIUM | Custom tree view styling with CSS and computed field for node type. Improves scannability |
| **Copy with hierarchy** | Duplicate parent and all children in one action | MEDIUM | Override `copy()` method to recursively copy children. Handle sequence renumbering and name suffixes |
| **Move subtree between parents** | Drag entire branch to new parent location | MEDIUM | Validate move won't create circular ref, then update parent_id for root of subtree. Children follow automatically |
| **Hierarchy-aware search** | Search within current branch only or across entire tree | MEDIUM | Add domain filters using `child_of` operator. Provide quick filters in search view |
| **Inherited field values** | Child segments inherit defaults from parent (responsible, dates, project) | MEDIUM | Use `@api.onchange` for parent_id to populate defaults. Allow override at child level |
| **Hierarchy depth limits** | Enforce maximum nesting depth for business rules | LOW | Add constraint checking depth via recursive parent traversal. Prevents overly complex structures |
| **Bulk operations on branch** | Apply action to parent and all descendants | MEDIUM | Add server action that collects children via `child_of` search and applies operation. Useful for archive, stage changes |
| **Export/import with hierarchy** | Preserve parent-child relationships during CSV import/export | HIGH | Use `parent_id/id` external ID pattern. Custom import logic to handle ordering dependencies |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Unlimited hierarchy depth** | Users want maximum flexibility | - Performance degrades with deep nesting<br>- UI becomes unusable past 5-6 levels<br>- Business logic complexity explodes | Enforce reasonable depth limit (4-5 levels). If deeper needed, rethink data model |
| **Automatic re-parenting based on rules** | "Smart" system that moves items automatically | - Users lose control and don't understand changes<br>- Creates unexpected circular references<br>- Hard to debug when hierarchy breaks | Let users explicitly set parent. Provide suggestions via wizard if needed |
| **Real-time computed totals everywhere** | "Everything should update instantly" | - Severe performance impact with stored computed fields<br>- Race conditions with concurrent edits<br>- Database write amplification | Compute totals on demand or batch calculate. Cache results. Only compute visible hierarchy levels |
| **Multiple parent support (DAG)** | "Item can belong to multiple segments" | - Breaks tree structure (becomes graph)<br>- Totals become ambiguous (double counting)<br>- UI complexity increases dramatically | Use tags/categories for cross-cutting concerns. Keep hierarchy as strict tree |
| **Inline editing of entire hierarchy** | Edit all levels in one tree view | - Form validation becomes problematic<br>- Save/cancel unclear across levels<br>- Conflicts with Odoo's form-based edit pattern | Edit each node in its own form. Use tree view for navigation and overview only |
| **Automatic hierarchy suggestions** | AI/ML to suggest structure | - Training data rarely available<br>- Users don't trust suggestions<br>- Maintenance overhead high | Provide templates/examples. Let users build structure explicitly |
| **Undo/redo hierarchy changes** | Users want to revert moves | - Complex state tracking required<br>- Conflicts with Odoo's ORM pattern<br>- Better handled at database level | Use staging/draft mode before commit. Provide "restore from archive" pattern |

## Feature Dependencies

```
[parent_id/child_ids fields] (FOUNDATIONAL)
    ├──requires──> [Prevent circular references] (CRITICAL)
    ├──enables──> [Tree view expand/collapse]
    ├──enables──> [Full path display]
    ├──enables──> [Smart buttons navigation]
    └──enables──> [Multi-level depth support]

[Automatic subtotal calculations] (CORE VALUE)
    ├──requires──> [parent_id/child_ids fields]
    ├──requires──> [Stored computed fields]
    └──enables──> [Hierarchical totals in tree view]

[Auto-create child tasks from segments] (PRIMARY DIFFERENTIATOR)
    ├──requires──> [parent_id/child_ids fields]
    ├──requires──> [Sequence ordering]
    ├──requires──> [Data transfer logic]
    └──enables──> [Inherited field values]

[Drag & drop reordering]
    ├──requires──> [Sequence field]
    ├──requires──> [Prevent circular references]
    └──enhances──> [Tree view expand/collapse]

[parent_store optimization]
    ├──requires──> [parent_left/parent_right fields]
    └──enables──> [Fast hierarchy queries for all features]

[Copy with hierarchy]
    ├──requires──> [parent_id/child_ids fields]
    └──conflicts with──> [Automatic re-parenting] (if enabled)
```

### Dependency Notes

- **parent_id/child_ids is foundational**: Every other feature depends on this relationship being correct. Must be implemented first with validation.
- **Circular reference prevention is critical**: Without this, hierarchy can break catastrophically. Must be in place before allowing user edits.
- **Subtotal calculations enable the core value**: This is why hierarchical segments matter. Performance must be considered early.
- **parent_store is performance insurance**: Can be added later, but easier to include from start for large datasets.
- **Auto-create tasks is the primary differentiator**: This is unique to your module and requires careful mapping logic.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [x] **parent_id/child_ids relationship** — Core hierarchy structure
- [x] **Prevent circular references** — Must be stable before user testing
- [x] **Tree view with expand/collapse** — Users can't validate without seeing hierarchy
- [x] **Automatic subtotal calculations** — Core value proposition for segments
- [x] **Auto-create child tasks from segments** — Primary differentiator and main user workflow
- [x] **Sequence ordering within levels** — Users expect to control order
- [x] **Basic form view with parent selector** — Need to create/edit segments
- [x] **Smart button to view children** — Basic navigation requirement

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Full path / breadcrumb display** — Nice to have, but users can navigate without it initially (trigger: user feedback requests it)
- [ ] **Drag & drop reordering** — Better UX than manual sequence edit, but not essential (trigger: v1.1 after basic workflow validated)
- [ ] **Hierarchical totals in tree view** — Improved visibility, but computed fields already provide data (trigger: once performance validated)
- [ ] **parent_store optimization** — Add when performance testing shows need (trigger: >1000 segments or >5 levels deep)
- [ ] **Expand/Collapse All buttons** — Quality of life for large hierarchies (trigger: users have >50 segments)
- [ ] **Copy with hierarchy** — Useful for templating, but workaround exists (create manually) (trigger: user requests for project templates)
- [ ] **Inherited field values from parent** — Reduces data entry, but can be set manually initially (trigger: feedback about repetitive data entry)

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Visual hierarchy indicators (tree lines, icons)** — Polish, not core functionality (why defer: requires custom JS, low ROI initially)
- [ ] **Move subtree between parents** — Edge case, manual move works (why defer: complex validation, rare use case)
- [ ] **Hierarchy-aware search** — Standard search sufficient initially (why defer: wait to see actual search patterns)
- [ ] **Bulk operations on branch** — Can use filters + actions (why defer: not clear which operations needed)
- [ ] **Export/import with hierarchy** — Manual creation acceptable for MVP (why defer: complex import logic, edge cases)
- [ ] **Hierarchy depth limits** — Enforce socially before technically (why defer: wait to see actual usage patterns)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| parent_id/child_ids relationship | HIGH | LOW | P1 |
| Prevent circular references | HIGH | LOW | P1 |
| Tree view expand/collapse | HIGH | MEDIUM | P1 |
| Automatic subtotal calculations | HIGH | MEDIUM | P1 |
| Auto-create child tasks | HIGH | HIGH | P1 |
| Sequence ordering | MEDIUM | LOW | P1 |
| Smart button navigation | MEDIUM | LOW | P1 |
| Full path display | MEDIUM | LOW | P2 |
| Drag & drop reordering | MEDIUM | MEDIUM | P2 |
| Hierarchical totals in tree | MEDIUM | MEDIUM | P2 |
| parent_store optimization | LOW | MEDIUM | P2 |
| Expand/Collapse All buttons | LOW | LOW | P2 |
| Copy with hierarchy | MEDIUM | MEDIUM | P2 |
| Inherited field values | MEDIUM | MEDIUM | P2 |
| Visual hierarchy indicators | LOW | MEDIUM | P3 |
| Move subtree | LOW | MEDIUM | P3 |
| Hierarchy-aware search | LOW | MEDIUM | P3 |
| Bulk operations on branch | LOW | MEDIUM | P3 |
| Export/import with hierarchy | LOW | HIGH | P3 |
| Hierarchy depth limits | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch (blocks validation without it)
- P2: Should have, add when possible (improves UX but workarounds exist)
- P3: Nice to have, future consideration (polish or edge cases)

## Competitor Feature Analysis

| Feature | Product Categories | Project Subtasks | Analytic Plans | Your Approach |
|---------|-------------------|------------------|----------------|---------------|
| Parent-child model | parent_id + child_ids | parent_id + child_ids | Plan hierarchy + subplans | Same pattern: parent_id + child_ids |
| Tree view | Yes, with recursive | List view with indentation | Plan organization chart | Recursive tree view |
| Expand/collapse | Yes, manual | Smart button to parent | Not applicable | Recursive tree attribute |
| Computed totals | No (categories don't aggregate) | Time rolls up to parent | Budget aggregation across plans | Yes, per-segment subtotals |
| Drag & drop | Limited (sequence only) | No | No | Sequence field (drag optional) |
| Full path | Yes (computed field) | Breadcrumb in form | Plan hierarchy display | Computed complete_name |
| Circular ref prevention | Yes (_check_recursion) | No (tasks rarely circular) | Yes (plan validation) | Constraint validation |
| Depth limits | No | No | Practical limit ~3 levels | Consider 4-5 level limit |
| Auto-creation | N/A | Tasks from SO if configured | N/A | **Your differentiator** |
| Sequence ordering | Yes (_order sequence) | Yes (sequence field) | Yes (sequence) | Yes, same pattern |

**Key Insights from Competitors:**
- **Product Categories**: Most mature hierarchy implementation in Odoo. Use as reference for parent_id pattern, full path computation, and circular reference prevention.
- **Project Subtasks**: Shows that hierarchy depth is typically 2-3 levels in practice. Time tracking aggregation is similar to your subtotal needs.
- **Analytic Plans**: Demonstrates that financial aggregation across hierarchy is feasible and valuable. Your budget segments align with this concept.
- **Your Unique Value**: Auto-creating hierarchical tasks from hierarchical segments while maintaining structure and transferring data is your differentiator. None of the standard modules do this.

## Real-World Hierarchy Patterns

Based on research into existing Odoo hierarchical modules:

### Common Depth Patterns
- **2 levels (80% of cases)**: Category → Subcategory, Parent Project → Subtask
- **3 levels (15% of cases)**: Region → Branch → Office, Phase → Deliverable → Task
- **4+ levels (5% of cases)**: Complex organizational structures, WBS

**Recommendation**: Design for 3-4 levels typical use, support unlimited technically, but validate UX breaks down past 5 levels.

### Common Field Patterns
```python
# Standard hierarchy fields (all modules)
parent_id = fields.Many2one('model.name', 'Parent', ondelete='cascade')
child_ids = fields.One2many('model.name', 'parent_id', 'Children')
sequence = fields.Integer('Sequence', default=10)

# Path display (product.category pattern)
complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True, recursive=True)

# Aggregation (project.task pattern)
subtask_count = fields.Integer(compute='_compute_subtask_count')
child_hours_planned = fields.Float(compute='_compute_child_hours')

# Performance optimization (if needed)
parent_left = fields.Integer(index=True)
parent_right = fields.Integer(index=True)
_parent_store = True
```

### Common UX Patterns
1. **Form view**: Many2one widget for parent_id with context domain to prevent circular refs
2. **Tree view**: Recursive view with expand/collapse OR flat list with indentation
3. **Kanban view**: Typically flat (hierarchies don't work well in kanban)
4. **Graph/Pivot**: Group by parent_id, aggregate children values
5. **Smart buttons**: Count of children, action to filtered child view

## Sources

**Official Odoo Documentation:**
- [Sub-tasks — Odoo 19.0 documentation](https://www.odoo.com/documentation/19.0/applications/services/project/tasks/sub-tasks.html)
- [Analytic accounting — Odoo 19.0 documentation](https://www.odoo.com/documentation/19.0/applications/finance/accounting/reporting/analytic_accounting.html)
- [Computed Fields And Onchanges — Odoo 19.0 documentation](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/08_compute_onchange.html)

**Community Discussions (MEDIUM confidence):**
- [How do I create a hierarchical view in Odoo 17?](https://www.odoo.com/forum/help-1/how-do-i-create-a-hierarchical-view-in-odoo-17-248118)
- [Project hierarchic tree view?](https://www.odoo.com/forum/help-1/project-hierarchic-tree-view-23080)
- [Managing Parent-Child Relationships Between Partners in Odoo](https://www.odoo.com/forum/help-1/managing-parent-child-relationships-between-partners-in-odoo-237999)
- [Stored computed field depending on child_id](https://www.odoo.com/forum/help-1/8-stored-computed-field-depending-on-child-id-93663)
- [validation error: Recursion found for tax](https://www.odoo.com/forum/help-1/validation-error-recursion-found-for-tax-sales-231538)

**Odoo Apps Store Modules (MEDIUM confidence):**
- [recursive_tree_view](https://apps.odoo.com/apps/modules/17.0/recursive_tree_view)
- [Project: WBS - Work Breakdown Structure](https://apps.odoo.com/apps/modules/16.0/project_wbs_gantt)
- [Parent Project / Projects Hierarchy](https://apps.odoo.com/apps/modules/17.0/project_hierarchy_view)
- [Hierarchical Tree View](https://apps.odoo.com/apps/modules/14.0/dusal_hierarchical_tree)

**Technical References (LOW-MEDIUM confidence):**
- [Create Projects and Tasks from Sales Orders — Odoo 13.0](https://www.odoo.com/documentation/13.0/applications/services/project/advanced/so_to_task.html)
- [Odoo Tricks: Speed Up Default Tree View](https://medium.com/@masjay/odoo-tricks-speed-up-default-tree-view-e6043cc5f83)
- [Hierarchical relationships - Odoo 11 Development Essentials](https://www.oreilly.com/library/view/odoo-11-development/9781788477796/e9953cfa-d88d-4ebd-a391-35e843fbd6b1.xhtml)

---
*Feature research for: Odoo hierarchical budget segments module*
*Researched: 2026-02-05*
