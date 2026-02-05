# Architecture Research: Odoo Custom Module

**Domain:** Odoo custom module extending sale and project
**Researched:** 2026-02-05
**Confidence:** HIGH

## Standard Odoo Module Architecture

### Module Directory Structure

```
custom_module/
├── __init__.py                 # Python package initializer (imports models, controllers)
├── __manifest__.py             # Module metadata and dependencies
├── models/                     # Business logic layer
│   ├── __init__.py            # Imports all model files
│   ├── sale_order_segment.py # New model definition
│   ├── sale_order.py          # sale.order inheritance/extension
│   ├── sale_order_line.py     # sale.order.line inheritance/extension
│   └── project_task.py        # project.task inheritance/extension
├── views/                      # Presentation layer
│   ├── sale_order_segment_views.xml
│   ├── sale_order_views.xml   # View inheritance for sale.order
│   ├── sale_order_line_views.xml
│   ├── project_task_views.xml
│   └── menu_items.xml         # Menu structure
├── security/                   # Access control layer
│   ├── ir.model.access.csv    # Model-level permissions
│   └── security.xml           # Record rules (row-level security)
├── data/                       # Initial/demo data
│   ├── automated_actions.xml  # Server actions/automations
│   └── initial_data.xml       # Seed data (optional)
├── static/                     # Frontend assets
│   └── description/           # Module icon and screenshots
│       └── icon.png
└── README.md                   # Documentation
```

### Component Responsibilities

| Component | Responsibility | Files |
|-----------|----------------|-------|
| **Models** | Data structure, business logic, ORM definitions | `models/*.py` |
| **Views** | UI presentation, forms, trees, search filters | `views/*.xml` |
| **Security** | Access rights, record rules, user groups | `security/*.csv`, `security/*.xml` |
| **Data** | Initial records, automated actions, workflows | `data/*.xml` |
| **Controllers** | HTTP routes, API endpoints (if needed) | `controllers/*.py` |
| **Static** | JavaScript, CSS, images | `static/src/*` |

## Recommended Architecture for This Project

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (Views)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Sale Order   │  │ Segment Tree │  │ Project Task │          │
│  │ Form + Tree  │  │    View      │  │   Form       │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
├─────────┴──────────────────┴──────────────────┴──────────────────┤
│                    BUSINESS LOGIC LAYER (Models)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ sale.order (extended)                                       │ │
│  │  - Original Odoo fields + methods                          │ │
│  │  - segment_ids: One2many → sale.order.segment             │ │
│  │  - _confirm_action_hook() → triggers automation           │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                            │
│  ┌─────────────────┴──────────────┐  ┌─────────────────────┐   │
│  │ sale.order.segment (NEW)       │  │ sale.order.line     │   │
│  │  - name, parent_id, child_ids  │  │  - segment_id FK    │   │
│  │  - order_id: Many2one          │  │                     │   │
│  │  - Hierarchical tree structure │  └─────────────────────┘   │
│  └────────────────────────────────┘                             │
│                      │                                            │
│  ┌─────────────────┴──────────────┐                             │
│  │ project.task (extended)         │                             │
│  │  - segment_id: Many2one         │                             │
│  │  - Links task back to segment   │                             │
│  └─────────────────────────────────┘                             │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                    AUTOMATION LAYER (Actions)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Automated Action: On sale.order confirm                     │ │
│  │  Trigger: state changes to 'sale'                          │ │
│  │  Action: Execute Python code                               │ │
│  │         1. Create project.project (if needed)              │ │
│  │         2. For each segment → create project.task          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                    DATA LAYER (PostgreSQL)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ sale_order   │  │ sale_order_  │  │ project_task │          │
│  │              │  │   segment    │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Architectural Patterns

### Pattern 1: Model Extension via _inherit

**What:** Extends existing Odoo models without modifying core code.

**When to use:** Adding fields, methods, or overriding behavior of standard models (sale.order, project.task).

**Trade-offs:**
- PRO: Modular, upgrade-safe, follows Odoo conventions
- CON: Must understand existing model structure and inheritance chain

**Example:**
```python
# models/sale_order.py
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Add new field
    segment_ids = fields.One2many(
        'sale.order.segment',
        'order_id',
        string='Segments'
    )

    # Override or extend existing method
    def action_confirm(self):
        """Extended to create project + tasks from segments"""
        result = super(SaleOrder, self).action_confirm()
        # Custom logic after confirmation
        self._create_project_from_segments()
        return result
```

### Pattern 2: Hierarchical Model with parent_id

**What:** Self-referential Many2one relationship creating tree structures.

**When to use:** Representing hierarchies (categories, organizational units, segments).

**Trade-offs:**
- PRO: Native Odoo pattern, supports parent_path optimization, built-in UI support
- CON: Requires careful constraint management to prevent cycles

**Example:**
```python
# models/sale_order_segment.py
from odoo import models, fields, api

class SaleOrderSegment(models.Model):
    _name = 'sale.order.segment'
    _description = 'Sale Order Segment'
    _parent_name = 'parent_id'
    _parent_store = True  # Enables performance optimization

    name = fields.Char(string='Segment Name', required=True)
    parent_id = fields.Many2one(
        'sale.order.segment',
        string='Parent Segment',
        index=True,
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True)  # Auto-managed hierarchy path
    child_ids = fields.One2many(
        'sale.order.segment',
        'parent_id',
        string='Child Segments'
    )
    order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        required=True,
        ondelete='cascade'
    )

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        """Prevent circular references"""
        if not self._check_recursion():
            raise ValidationError('Error! You cannot create recursive segments.')
```

### Pattern 3: View Inheritance via XPath

**What:** Extends existing views by targeting specific elements with XPath selectors.

**When to use:** Adding fields to existing forms, modifying layout, inserting tabs/pages.

**Trade-offs:**
- PRO: Surgical modifications, multiple modules can extend same view
- CON: Fragile if XPath selector is too generic or core view structure changes

**Example:**
```xml
<!-- views/sale_order_views.xml -->
<odoo>
    <record id="view_order_form_segment" model="ir.ui.view">
        <field name="name">sale.order.form.segment</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">
            <!-- Add tab after order lines -->
            <xpath expr="//notebook" position="inside">
                <page string="Segments" name="segments">
                    <field name="segment_ids">
                        <tree editable="bottom">
                            <field name="name"/>
                            <field name="parent_id"/>
                        </tree>
                    </field>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

**XPath Position Attributes:**
- `inside` (default): Insert content inside matched element
- `after`: Insert after matched element
- `before`: Insert before matched element
- `replace`: Replace matched element entirely
- `attributes`: Modify attributes of matched element

**Best practices for XPath:**
- Use specific selectors: `//field[@name='order_line']` not `//notebook`
- Anchor to stable elements (named fields, pages) not generic groups
- Test with multiple inheritance scenarios

### Pattern 4: Automated Actions with Python Code

**What:** Triggered server-side actions executing Python code on record events.

**When to use:** Workflow automation (creating records, sending emails, updating fields).

**Trade-offs:**
- PRO: No custom module needed (can use Studio), configurable via UI
- CON: Limited debugging, performance concerns with complex logic

**Example:**
```xml
<!-- data/automated_actions.xml -->
<odoo>
    <record id="action_create_project_on_confirm" model="base.automation">
        <field name="name">Create Project and Tasks on SO Confirmation</field>
        <field name="model_id" ref="sale.model_sale_order"/>
        <field name="trigger">on_state_set</field>
        <field name="state">sale</field>
        <field name="code">
# Available variables: record, env, model, time, datetime, dateutil
if record.segment_ids:
    # Create project
    project = env['project.project'].create({
        'name': f"Project - {record.name}",
        'partner_id': record.partner_id.id,
    })

    # Create tasks from segments
    for segment in record.segment_ids:
        env['project.task'].create({
            'name': segment.name,
            'project_id': project.id,
            'partner_id': record.partner_id.id,
            'segment_id': segment.id,
        })
        </field>
    </record>
</odoo>
```

**Alternative: Override Python method (more robust)**
```python
# models/sale_order.py
def action_confirm(self):
    result = super(SaleOrder, self).action_confirm()
    if self.segment_ids:
        self._create_project_from_segments()
    return result

def _create_project_from_segments(self):
    """Create project and tasks from segments"""
    project = self.env['project.project'].create({
        'name': f"Project - {self.name}",
        'partner_id': self.partner_id.id,
    })

    for segment in self.segment_ids:
        self.env['project.task'].create({
            'name': segment.name,
            'project_id': project.id,
            'segment_id': segment.id,
        })
```

## Data Flow

### Request Flow: Sale Order Confirmation

```
[User clicks "Confirm" on Sale Order]
    ↓
[sale.order.action_confirm() called]
    ↓
[Odoo ORM: Update state to 'sale']
    ↓
[Automated Action Trigger: on_state_set = 'sale']
    ↓
[Execute Python code / call custom method]
    ↓
[Create project.project record] ──→ [PostgreSQL INSERT]
    ↓
[For each segment in segment_ids]
    ↓
[Create project.task record with segment_id FK] ──→ [PostgreSQL INSERT]
    ↓
[Commit transaction]
    ↓
[Refresh UI / Show project/tasks]
```

### Model Relationship Flow

```
sale.order (1)
    ↓ (One2many: segment_ids)
sale.order.segment (Many) [Hierarchical: parent_id/child_ids]
    ↓ (inverse Many2one)
project.task (Many)
    ↑ (Many2one: segment_id)

sale.order.line (Many)
    ↓ (Many2one: segment_id)
sale.order.segment (1)
```

### Module Loading Order (Manifest)

```python
# __manifest__.py
{
    'name': 'Sale Order Segments',
    'version': '1.0',
    'depends': ['sale', 'project'],  # CRITICAL: Load dependencies first
    'data': [
        'security/ir.model.access.csv',      # 1. Security first
        'security/security.xml',             # 2. Record rules
        'views/sale_order_segment_views.xml',# 3. Views
        'views/sale_order_views.xml',
        'views/project_task_views.xml',
        'data/automated_actions.xml',        # 4. Data/actions last
    ],
    'installable': True,
    'application': False,
}
```

**Load order reasoning:**
1. Security MUST load before views (views reference groups)
2. Views MUST load before data (data may reference views)
3. Automated actions reference models/views, load last

## Component Build Order

### Recommended Implementation Sequence

| Phase | Component | Rationale |
|-------|-----------|-----------|
| 1 | **Module scaffold + manifest** | Establishes structure, dependencies |
| 2 | **sale.order.segment model** | Core new model, no dependencies |
| 3 | **sale.order extension** | Adds segment_ids field (depends on #2) |
| 4 | **sale.order.line extension** | Adds segment_id FK (depends on #2) |
| 5 | **project.task extension** | Adds segment_id FK (depends on #2) |
| 6 | **Security (ir.model.access.csv)** | Required before views can be tested |
| 7 | **Views (segment, sale order)** | UI to create/manage segments |
| 8 | **Automated action** | Workflow automation (depends on all models) |

**Rationale for order:**
- Models before views (views reference models)
- New model before extensions (extensions reference new model)
- Security before views (prevents access errors during load)
- Automated actions last (references all components)

### Dependency Chain

```
sale.order.segment (new model)
    ↓
sale.order (extends) + sale.order.line (extends) + project.task (extends)
    ↓
Security (access rights)
    ↓
Views (UI)
    ↓
Automated Actions (workflow)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct Database Manipulation

**What people do:** Use `env.cr.execute()` for CRUD operations.

**Why it's wrong:**
- Bypasses ORM validation, computed fields, constraints
- No audit trail (mail tracking, activity log)
- Security rules ignored
- Hard to maintain, breaks on schema changes

**Do this instead:**
```python
# BAD
env.cr.execute("INSERT INTO project_task (name, project_id) VALUES (%s, %s)",
               (task_name, project_id))

# GOOD
env['project.task'].create({
    'name': task_name,
    'project_id': project_id,
})
```

### Anti-Pattern 2: Generic XPath Selectors

**What people do:** Use vague XPath like `//group` or `//notebook`.

**Why it's wrong:**
- Breaks when any module adds groups/notebooks
- Multiple modules targeting same generic selector cause conflicts
- Hard to debug which inheritance chain failed

**Do this instead:**
```xml
<!-- BAD -->
<xpath expr="//notebook" position="inside">

<!-- GOOD -->
<xpath expr="//field[@name='order_line']" position="after">
<xpath expr="//page[@name='other_information']" position="before">
```

### Anti-Pattern 3: Circular Dependencies in Manifest

**What people do:** Module A depends on Module B, which depends on Module A.

**Why it's wrong:**
- Module installation fails
- Odoo can't determine load order
- Indicates poor module boundary design

**Do this instead:**
- Extract shared functionality to Module C (base module)
- A and B both depend on C
- Use abstract models for shared behavior

### Anti-Pattern 4: Compute Without Store on Large Datasets

**What people do:** Define computed fields without `store=True` that are expensive to calculate.

**Why it's wrong:**
- Recomputed on every read (performance hit)
- Can't search/filter on the field
- Tree views become slow with 100+ records

**Do this instead:**
```python
# If field needs filtering/sorting or is expensive
total_segments = fields.Integer(
    compute='_compute_total_segments',
    store=True  # Store result in database
)

# For cheap, always-fresh computations
display_name = fields.Char(
    compute='_compute_display_name'
    # No store - recompute on demand
)
```

### Anti-Pattern 5: No Transaction Batching in Automated Actions

**What people do:** Create 1000 tasks in a loop with individual `create()` calls.

**Why it's wrong:**
- Slow (N database round-trips)
- Blocks worker thread
- May hit timeout on large datasets

**Do this instead:**
```python
# BAD
for segment in segments:
    env['project.task'].create({'name': segment.name, ...})

# GOOD (batch create)
task_vals = [{'name': seg.name, 'project_id': project.id}
             for seg in segments]
env['project.task'].create(task_vals)
```

## Integration Points

### External Module Integration

| Module | Integration Pattern | Notes |
|--------|---------------------|-------|
| **sale** | Model inheritance (_inherit) | Extend sale.order, sale.order.line |
| **project** | Model inheritance (_inherit) | Extend project.task, optionally project.project |
| **mail** | Inherit mail.thread | Add chatter to segment model (optional) |
| **account** | Relation via sale.order | Invoicing inherits from sale automatically |

### Internal Component Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Models ↔ Views** | XML field references | Views use `<field name="..."/>` |
| **Models ↔ Security** | ir.model.access references | CSV uses model technical name |
| **Sale Order ↔ Segment** | One2many/Many2one | Bidirectional navigation |
| **Segment ↔ Task** | Many2one FK | Task references segment (optional inverse) |
| **Automated Action ↔ Models** | Python code via `env['model']` | Full ORM access in server action code |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-1k orders** | Standard architecture works. Automated action on confirm is fine. |
| **1k-10k orders** | Add database indexes on FKs (segment_id, order_id). Use `_parent_store=True` for segment hierarchy. Consider cron job instead of instant automation. |
| **10k+ orders** | Batch task creation (create multiple in one call). Add search indexes on commonly filtered fields. Consider async job queue (odoo-queue or celery). Cache computed fields with `store=True`. |

### Performance Optimization

**Hierarchy Performance:**
- Always use `_parent_store=True` for hierarchical models
- Enables O(1) `child_of` domain queries instead of recursive SQL
- Automatically maintains `parent_path` field

**Database Indexes:**
```python
# models/sale_order_segment.py
parent_id = fields.Many2one('sale.order.segment', index=True)  # Index FK
order_id = fields.Many2one('sale.order', index=True)  # Index FK
```

**Batch Operations:**
```python
# Create multiple tasks at once
task_vals_list = [{'name': s.name, 'project_id': p.id} for s in segments]
self.env['project.task'].create(task_vals_list)
```

## Sources

**Official Odoo Documentation (HIGH confidence):**
- [Building a Module - Odoo 19.0](https://www.odoo.com/documentation/19.0/developer/tutorials/backend.html)
- [Chapter 12: Inheritance - Odoo 19.0](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/12_inheritance.html)
- [View Records - Odoo 19.0](https://www.odoo.com/documentation/19.0/developer/reference/user_interface/view_records.html)
- [Module Manifests - Odoo 19.0](https://www.odoo.com/documentation/19.0/developer/reference/backend/module.html)
- [Automation Rules - Odoo 19.0](https://www.odoo.com/documentation/19.0/applications/studio/automated_actions.html)
- [Coding Guidelines - Odoo 19.0](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html)
- [Define Module Data - Odoo 19.0](https://www.odoo.com/documentation/19.0/developer/tutorials/define_module_data.html)

**Community Resources (MEDIUM confidence):**
- [Automated Actions Create Tasks - Odoo Tricks](https://odootricks.tips/about/automated-actions/automated-actions-create-tasks-sales-order-lines/)
- [Odoo Forum - Extending sale.order](https://www.odoo.com/forum/help-1/extend-an-existing-model-by-inheriting-another-131340)
- [Hierarchical Tree View](https://www.odoo.com/forum/help-1/solved-how-to-create-hierarchy-tree-view-in-odoo-11-136004)

---
*Architecture research for: Odoo custom module extending sale and project*
*Researched: 2026-02-05*
