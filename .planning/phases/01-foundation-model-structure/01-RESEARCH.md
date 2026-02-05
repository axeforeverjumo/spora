# Phase 1: Foundation & Model Structure - Research

**Researched:** 2026-02-05
**Domain:** Odoo 18 hierarchical model (sale.order.segment) with parent_id, _parent_store, computed level, circular reference prevention, depth limit constraint
**Confidence:** HIGH

## Summary

Phase 1 creates the foundational `sale.order.segment` model with hierarchical parent-child relationships, automatic level computation, circular reference prevention, and a 4-level depth limit. This phase also scaffolds the Odoo module structure, defines minimal security (ir.model.access.csv), and establishes the testing framework.

The standard approach uses Odoo's native hierarchical model pattern: a `parent_id` Many2one self-reference with `_parent_store = True` for performance, a `parent_path` Char field for indexed hierarchy queries, and `_check_recursion()` for circular reference validation. The level field is computed from `parent_path` (counting separators), and the 4-level depth limit is enforced via `@api.constrains`. The `product.category` model in Odoo core is the canonical reference implementation for this pattern.

Key recommendations: (1) Enable `_parent_store = True` from the start -- retrofitting requires data migration. (2) Use `parent_path` to compute level efficiently (count slashes) instead of recursive parent traversal. (3) Use `@api.constrains('parent_id')` to validate both circular references and depth limit in a single constraint method. (4) Include `sequence` field from the start for sibling ordering. (5) Set up `ir.model.access.csv` before testing views to prevent access errors.

**Primary recommendation:** Follow the `product.category` pattern exactly -- it is the most battle-tested hierarchical model in Odoo and provides the template for parent_id, parent_path, _parent_store, complete_name, and _check_recursion.

## Standard Stack

The established libraries/tools for this phase:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Odoo | 18.0 | ERP framework + ORM | Required base platform. Provides the ORM with parent_store support, constraint decorators, computed fields, and view framework. |
| Python | 3.10+ | Backend language | Minimum version required by Odoo 18. Python 3.11 or 3.12 also acceptable. |
| PostgreSQL | 15 | Database | Recommended for Odoo 18. Handles parent_path indexing, CHECK constraints, and foreign key cascades. |
| Docker | 24.0+ | Development runtime | Already configured in project docker-compose.yml. Dev mode enabled with `--dev=all`. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| odoo.tests.TransactionCase | 18.0 | Unit testing base class | All model tests for segment creation, hierarchy validation, constraint verification |
| odoo.exceptions.ValidationError | 18.0 | Constraint error signaling | Raised by `@api.constrains` methods when validation fails (circular refs, depth limit) |
| odoo.tests.Form | 18.0 | Form view simulation in tests | Testing form behavior, onchange triggers, default values without browser |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `_parent_store = True` | No parent_store (raw parent_id only) | Raw is simpler but exponentially slower for `child_of`/`parent_of` queries on 100+ records. Use _parent_store always. |
| Level from parent_path (count slashes) | Recursive parent traversal to compute depth | Recursive traversal is O(depth) per record, parent_path counting is O(1). Use parent_path. |
| `@api.constrains` for depth limit | SQL CHECK constraint | SQL constraints cannot traverse relationships. Must use Python constraint. |
| `ondelete='cascade'` on parent_id | `ondelete='restrict'` | Cascade deletes children automatically. Restrict blocks parent deletion if children exist. Use cascade per HIER requirements (segments belong to parent). |

**Installation:**
```bash
# No additional packages -- all functionality comes from Odoo 18 ORM built-ins.
# Module is installed via Odoo's module manager after placing in addons path.
docker compose exec odoo odoo -d spora -i spora_segment --stop-after-init
```

## Architecture Patterns

### Recommended Module Structure (Phase 1 scope)
```
addons/spora_segment/
    __init__.py                          # imports models
    __manifest__.py                      # module metadata
    models/
        __init__.py                      # imports sale_order_segment
        sale_order_segment.py            # NEW: sale.order.segment model
    security/
        ir.model.access.csv             # access rights for segment model
    views/
        sale_order_segment_views.xml    # form + tree + search views
    tests/
        __init__.py                      # imports test modules
        test_sale_order_segment.py      # hierarchy, constraints, computed fields
```

### Pattern 1: Hierarchical Model with _parent_store (product.category pattern)
**What:** Self-referential Many2one with indexed parent_path for O(1) hierarchy queries.
**When to use:** Any model with parent-child tree structure.
**Example:**
```python
# Source: Odoo 18 product.category model pattern + ORM API docs
# https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderSegment(models.Model):
    _name = 'sale.order.segment'
    _description = 'Sale Order Segment'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    parent_id = fields.Many2one(
        'sale.order.segment',
        string='Parent Segment',
        index=True,
        ondelete='cascade',
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'sale.order.segment',
        'parent_id',
        string='Child Segments',
    )
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        store=True,
        recursive=True,
    )

    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for segment in self:
            if segment.parent_id:
                segment.level = segment.parent_id.level + 1
            else:
                segment.level = 1

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError(
                'Error: You cannot create recursive segments. '
                'A segment cannot be its own ancestor.'
            )
        for segment in self:
            if segment.level > 4:
                raise ValidationError(
                    'Error: Maximum hierarchy depth is 4 levels. '
                    'Segment "%s" would be at level %d.' % (segment.name, segment.level)
                )
```

### Pattern 2: Level Computation via parent_path (alternative -- more efficient)
**What:** Compute level by counting separators in parent_path string instead of recursive parent traversal.
**When to use:** When level must be recomputed efficiently without depending on parent records.
**Example:**
```python
# Source: parent_path format documented in ORM API
# parent_path = "1/5/12/" means root(1) -> parent(5) -> self(12), depth = 3
@api.depends('parent_path')
def _compute_level(self):
    for segment in self:
        if segment.parent_path:
            # parent_path format: "1/5/12/" -- count slashes minus trailing
            segment.level = segment.parent_path.count('/') - segment.parent_path.rstrip('/').count('/') + segment.parent_path.strip('/').count('/') + 1
            # Simpler: count the IDs in the path
            segment.level = len(segment.parent_path.strip('/').split('/')) if segment.parent_path else 1
        else:
            segment.level = 1
```

**Trade-off analysis:** The recursive `parent_id.level` approach (Pattern 1) is conceptually cleaner and leverages Odoo's recursive recomputation. The `parent_path` approach (Pattern 2) is more efficient for reads but `parent_path` is populated AFTER `@api.constrains` runs, creating a chicken-and-egg problem for depth validation. **Recommendation: Use Pattern 1** (recursive parent_id.level) because it guarantees the level is correct at constraint validation time.

### Pattern 3: Constraint combining circular reference + depth limit
**What:** Single `@api.constrains('parent_id')` method that validates both circular references and depth limits.
**When to use:** When both validations trigger on the same field change.
**Example:**
```python
@api.constrains('parent_id')
def _check_hierarchy(self):
    # Step 1: Check circular references (built-in Odoo method)
    if not self._check_recursion():
        raise ValidationError(
            'Error: You cannot create recursive segments.'
        )
    # Step 2: Check depth limit
    for segment in self:
        # Walk up the hierarchy to count depth
        depth = 1
        current = segment
        while current.parent_id:
            depth += 1
            current = current.parent_id
            if depth > 4:
                raise ValidationError(
                    'Error: Maximum hierarchy depth is 4 levels. '
                    'Segment "%s" exceeds this limit.' % segment.name
                )
```

**Why walk the parent chain in the constraint:** At constraint evaluation time, the `parent_path` field may not yet be recomputed (it updates after the constraint). Walking the `parent_id` chain guarantees an accurate depth count regardless of parent_path timing.

### Pattern 4: TransactionCase test structure
**What:** Unit tests validating model behavior, constraints, and computed fields.
**When to use:** All model-level tests in Odoo 18.
**Example:**
```python
# Source: https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('at_install')
class TestSaleOrderSegment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Segment = cls.env['sale.order.segment']
        cls.segment_root = cls.Segment.create({
            'name': 'Root Segment',
        })

    def test_level_root(self):
        """Root segment should have level 1."""
        self.assertEqual(self.segment_root.level, 1)

    def test_level_child(self):
        """Child segment should have level 2."""
        child = self.Segment.create({
            'name': 'Child',
            'parent_id': self.segment_root.id,
        })
        self.assertEqual(child.level, 2)

    def test_circular_reference_blocked(self):
        """Circular reference should raise ValidationError."""
        child = self.Segment.create({
            'name': 'Child',
            'parent_id': self.segment_root.id,
        })
        with self.assertRaises(ValidationError):
            self.segment_root.write({'parent_id': child.id})

    def test_depth_limit_4_levels(self):
        """Creating segment at level 5 should raise ValidationError."""
        l2 = self.Segment.create({'name': 'L2', 'parent_id': self.segment_root.id})
        l3 = self.Segment.create({'name': 'L3', 'parent_id': l2.id})
        l4 = self.Segment.create({'name': 'L4', 'parent_id': l3.id})
        with self.assertRaises(ValidationError):
            self.Segment.create({'name': 'L5', 'parent_id': l4.id})

    def test_level_4_allowed(self):
        """Creating segment at level 4 should succeed."""
        l2 = self.Segment.create({'name': 'L2', 'parent_id': self.segment_root.id})
        l3 = self.Segment.create({'name': 'L3', 'parent_id': l2.id})
        l4 = self.Segment.create({'name': 'L4', 'parent_id': l3.id})
        self.assertEqual(l4.level, 4)
```

### Anti-Patterns to Avoid
- **Using raw SQL for hierarchy queries:** Bypass the ORM and you lose constraint validation, computed field triggers, and access control. Always use `self.env['model'].search()` with `child_of`/`parent_of` operators.
- **Computing level without `recursive=True`:** If the `level` field depends on `parent_id.level` but lacks `recursive=True`, Odoo will not recompute correctly when ancestor records change.
- **Forgetting `parent_path` field declaration:** Even though `_parent_store = True` implies parent_path, the field MUST be explicitly declared in the model with `index=True`.
- **Using `@api.depends('parent_path')` for level in constraint context:** The `parent_path` may not be updated yet when `@api.constrains('parent_id')` fires. Use recursive parent traversal instead for constraint validation.
- **Not indexing `parent_id`:** Always set `index=True` on the parent_id field for join performance.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Circular reference detection | Custom recursive check traversing parent_id chain | `self._check_recursion()` (built into Odoo ORM) | Handles edge cases (multi-record writes, concurrent updates) that custom code misses |
| Hierarchy path storage | Custom parent_path computation logic | `_parent_store = True` + `parent_path = fields.Char(index=True)` | Odoo ORM maintains parent_path automatically on every write. Handles reparenting, deletion, and batch operations |
| Fast hierarchy queries (child_of/parent_of) | Custom recursive SQL or CTE queries | `self.env['model'].search([('id', 'child_of', parent_id)])` | Uses indexed parent_path for O(1) lookups instead of recursive queries |
| Record ordering with drag-drop | Custom JS sort implementation | `sequence = fields.Integer()` + `_order = 'sequence, id'` + `handle` widget in tree view | Native Odoo pattern, works out of the box with tree views |
| Module scaffold | Manual file creation | `odoo scaffold module_name addons_path` | Generates correct directory structure, __init__.py, __manifest__.py with proper format |
| Test infrastructure | Custom test runner | `odoo.tests.TransactionCase` + `--test-tags` CLI | Odoo's test framework handles database setup/teardown, transaction isolation, and module dependency loading |

**Key insight:** Odoo's ORM provides `_check_recursion()`, `_parent_store`, and `parent_path` specifically for hierarchical models. These handle concurrent writes, batch operations, and edge cases that hand-rolled solutions inevitably miss.

## Common Pitfalls

### Pitfall 1: Forgetting _parent_store from the start
**What goes wrong:** Hierarchy queries (child_of, parent_of) become exponentially slower as records grow past 100. Adding _parent_store later requires a data migration to populate parent_path for existing records.
**Why it happens:** Developers build the model with just parent_id and child_ids, test with 5-10 records (works fine), then discover performance issues in production.
**How to avoid:** Set `_parent_store = True` and declare `parent_path = fields.Char(index=True, unaccent=False)` in the initial model definition. Never add it "later".
**Warning signs:** Tree views loading slowly, timeout errors on hierarchy-related searches.

### Pitfall 2: parent_path not declared explicitly
**What goes wrong:** Module installation fails with "field parent_path not found" error even though `_parent_store = True` is set.
**Why it happens:** `_parent_store = True` tells the ORM to USE parent_path, but the field must still be explicitly declared in the model class.
**How to avoid:** Always include `parent_path = fields.Char(index=True, unaccent=False)` in the model definition alongside `_parent_store = True`.
**Warning signs:** Installation error on module update.

### Pitfall 3: Level constraint timing with parent_path
**What goes wrong:** Using `@api.depends('parent_path')` for the level field and then checking level in `@api.constrains('parent_id')` -- the level may still show the OLD value during constraint evaluation because parent_path recomputation happens after constraints.
**Why it happens:** Odoo processes `@api.constrains` before recomputing stored computed fields that depend on parent_path. The execution order is: field write -> constraints -> stored compute recomputation.
**How to avoid:** In the constraint method, walk the parent_id chain directly to count depth instead of relying on the computed level field. OR use `@api.depends('parent_id', 'parent_id.level')` with `recursive=True` so level is computed via the parent relationship, not parent_path.
**Warning signs:** Depth limit constraint not firing when creating deeply nested segments, or firing incorrectly on valid segments.

### Pitfall 4: Missing ir.model.access.csv blocks non-admin users
**What goes wrong:** Admin can create and view segments perfectly. Any other user gets "Access Denied" or blank views.
**Why it happens:** Developers test exclusively as admin (which bypasses ACL). Every new model requires explicit access rights in ir.model.access.csv.
**How to avoid:** Create ir.model.access.csv in Phase 1 alongside the model. Use at minimum `base.group_user` for read access. List security files BEFORE view files in __manifest__.py `data` list.
**Warning signs:** "You are not allowed to access" errors when switching from admin to regular user.

### Pitfall 5: ondelete='cascade' vs 'restrict' on parent_id
**What goes wrong:** With `cascade`, deleting a parent silently deletes all children. With `restrict`, users cannot delete any parent segment, even when intentional.
**Why it happens:** Default behavior choice made early without considering user workflow.
**How to avoid:** Use `ondelete='cascade'` for parent_id (HIER requirements specify segments belong to their parent). This matches Odoo's product.category behavior. When a parent is removed, its children go with it.
**Warning signs:** Users surprised by mass deletion (cascade) or unable to clean up segments (restrict).

### Pitfall 6: _order attribute missing or wrong
**What goes wrong:** Segments display in random order in tree views, making hierarchy hard to read.
**Why it happens:** Developers forget to set `_order` on the model, so Odoo defaults to `id` ordering.
**How to avoid:** Set `_order = 'sequence, id'` on the model class. This respects the user's ordering preference (sequence field) with id as tiebreaker.
**Warning signs:** Segments appear in creation order, not in the user-defined order.

## Code Examples

Verified patterns from official sources:

### Complete sale.order.segment model (Phase 1 scope)
```python
# models/sale_order_segment.py
# Source: product.category pattern + ORM API docs
# https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

MAX_HIERARCHY_DEPTH = 4


class SaleOrderSegment(models.Model):
    _name = 'sale.order.segment'
    _description = 'Sale Order Segment'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'sequence, id'

    # --- Core fields ---
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Used to order segments within the same level.',
    )
    active = fields.Boolean(default=True)

    # --- Hierarchy fields ---
    parent_id = fields.Many2one(
        'sale.order.segment',
        string='Parent Segment',
        index=True,
        ondelete='cascade',
    )
    parent_path = fields.Char(
        index=True,
        unaccent=False,
    )
    child_ids = fields.One2many(
        'sale.order.segment',
        'parent_id',
        string='Child Segments',
    )

    # --- Computed fields ---
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        store=True,
        recursive=True,
    )
    child_count = fields.Integer(
        string='Sub-segment Count',
        compute='_compute_child_count',
    )

    # --- Computed methods ---
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for segment in self:
            if segment.parent_id:
                segment.level = segment.parent_id.level + 1
            else:
                segment.level = 1

    def _compute_child_count(self):
        for segment in self:
            segment.child_count = len(segment.child_ids)

    # --- Constraints ---
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        """Validate no circular references and max depth of 4 levels."""
        if not self._check_recursion():
            raise ValidationError(
                'Error: You cannot create recursive segments. '
                'A segment cannot be its own ancestor.'
            )
        for segment in self:
            # Walk parent chain to count actual depth
            depth = 1
            current = segment
            while current.parent_id:
                depth += 1
                current = current.parent_id
                if depth > MAX_HIERARCHY_DEPTH:
                    raise ValidationError(
                        'Error: Maximum hierarchy depth is %d levels. '
                        'Segment "%s" would exceed this limit.'
                        % (MAX_HIERARCHY_DEPTH, segment.name)
                    )
```

### __manifest__.py for Phase 1
```python
# addons/spora_segment/__manifest__.py
{
    'name': 'Spora - Hierarchical Budget Segments',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Hierarchical budget segments for sale orders',
    'description': """
        Adds hierarchical segment structure to sale orders
        with automatic level calculation and depth validation.
    """,
    'author': 'Spora',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_segment_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

### ir.model.access.csv (minimal for Phase 1)
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sale_order_segment_user,sale.order.segment user,model_sale_order_segment,sales_team.group_sale_salesman,1,1,1,0
access_sale_order_segment_manager,sale.order.segment manager,model_sale_order_segment,sales_team.group_sale_manager,1,1,1,1
```

### __init__.py files
```python
# addons/spora_segment/__init__.py
from . import models

# addons/spora_segment/models/__init__.py
from . import sale_order_segment
```

### Basic views (tree + form + search)
```xml
<!-- views/sale_order_segment_views.xml -->
<odoo>
    <!-- Tree View -->
    <record id="sale_order_segment_view_tree" model="ir.ui.view">
        <field name="name">sale.order.segment.tree</field>
        <field name="model">sale.order.segment</field>
        <field name="arch" type="xml">
            <tree>
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="parent_id"/>
                <field name="level"/>
                <field name="child_count"/>
            </tree>
        </field>
    </record>

    <!-- Form View -->
    <record id="sale_order_segment_view_form" model="ir.ui.view">
        <field name="name">sale.order.segment.form</field>
        <field name="model">sale.order.segment</field>
        <field name="arch" type="xml">
            <form string="Segment">
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_view_children"
                                type="object"
                                class="oe_stat_button"
                                icon="fa-sitemap"
                                invisible="child_count == 0">
                            <field name="child_count" widget="statinfo" string="Sub-segments"/>
                        </button>
                    </div>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="parent_id"/>
                        </group>
                        <group>
                            <field name="sequence"/>
                            <field name="level"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Sub-segments" name="children">
                            <field name="child_ids">
                                <tree>
                                    <field name="sequence" widget="handle"/>
                                    <field name="name"/>
                                    <field name="level"/>
                                </tree>
                            </field>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Search View -->
    <record id="sale_order_segment_view_search" model="ir.ui.view">
        <field name="name">sale.order.segment.search</field>
        <field name="model">sale.order.segment</field>
        <field name="arch" type="xml">
            <search string="Segments">
                <field name="name"/>
                <field name="parent_id"/>
                <filter string="Root Segments" name="root"
                        domain="[('parent_id', '=', False)]"/>
                <group expand="0" string="Group By">
                    <filter string="Parent" name="group_parent"
                            context="{'group_by': 'parent_id'}"/>
                    <filter string="Level" name="group_level"
                            context="{'group_by': 'level'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- Action -->
    <record id="sale_order_segment_action" model="ir.actions.act_window">
        <field name="name">Segments</field>
        <field name="res_model">sale.order.segment</field>
        <field name="view_mode">tree,form</field>
        <field name="search_view_id" ref="sale_order_segment_view_search"/>
        <field name="context">{'search_default_root': 1}</field>
    </record>
</odoo>
```

### Running tests in Docker
```bash
# Run all tests for the module
docker compose exec odoo odoo --test-tags /spora_segment -d spora --stop-after-init

# Run with log output visible
docker compose exec odoo odoo --test-tags /spora_segment -d spora --stop-after-init --log-level=test
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `parent_left`/`parent_right` (MPTT) | `parent_path` string | Odoo 12+ | parent_path is simpler, more resilient to concurrent updates, and easier to debug. MPTT fields are deprecated. |
| `@api.one` / `@api.multi` | Direct recordset iteration | Odoo 13+ | Removed. Always iterate `self` in compute/constraint methods. |
| `name_get()` method | `_rec_name` / `display_name` field | Odoo 17+ | `name_get()` deprecated. Use `_rec_name` attribute or computed `display_name`. |
| `_sequence` attribute | Automatic PostgreSQL sequences | Odoo 18 | Removed. PostgreSQL handles ID sequences automatically. |
| `attrs` XML attribute for visibility | `invisible`/`readonly`/`required` attributes directly | Odoo 17+ | `attrs` dict syntax replaced with inline boolean expressions in Odoo 17+. |

**Deprecated/outdated:**
- `parent_left` / `parent_right` Integer fields: Replaced by `parent_path` Char field. Do not use.
- `@api.one`: Removed entirely. Iterate `self` directly.
- `attrs={'invisible': [('field', '=', value)]}` in XML: Use `invisible="field == value"` directly on the element.

## Open Questions

Things that could not be fully resolved:

1. **order_id field: include now or defer to Phase 2?**
   - What we know: The segment model needs a `Many2one('sale.order')` field eventually (Phase 2). Including it now would make Phase 2 simpler but requires the `sale` dependency from Phase 1.
   - What is unclear: Whether to include `order_id` as an optional field now or add it strictly in Phase 2.
   - Recommendation: Include `order_id` in Phase 1 since the module already depends on `sale` (per manifest). Make it optional (`required=False`) now; Phase 2 will make it required via form view context. This avoids a model migration between phases.

2. **Domain restriction on parent_id (same order)**
   - What we know: In Phase 2, parent_id should only allow segments from the same sale.order. In Phase 1, there is no order_id yet (or it is optional).
   - What is unclear: Whether to add a domain filter on parent_id now or wait.
   - Recommendation: If `order_id` is included in Phase 1, add `@api.constrains('parent_id', 'order_id')` to validate parent belongs to same order. If deferred, add domain in Phase 2.

3. **Module technical name: `spora_segment` vs `spora_budget_segment` vs `spora`**
   - What we know: Module names should be descriptive, lowercase, underscored. The project is called "spora".
   - Recommendation: Use `spora_segment` for now. Short, descriptive, and allows for future `spora_*` companion modules if needed.

## Sources

### Primary (HIGH confidence)
- [Odoo 18.0 ORM API - _parent_store, parent_path, _check_recursion](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html) - Hierarchical model attributes, parent_path format ("42/63/84/"), _check_recursion method
- [Odoo 18.0 Testing Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html) - TransactionCase, test tags, --test-tags CLI
- [Odoo 18.0 Constraints Tutorial](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/10_constraints.html) - @api.constrains, _sql_constraints, ValidationError
- [Odoo 18.0 Computed Fields Tutorial](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/08_compute_onchange.html) - @api.depends, recursive=True, store=True
- [Odoo 18.0 Module Manifests](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html) - __manifest__.py format, version "18.0.1.0.0"
- [Odoo 18.0 CLI Reference](https://www.odoo.com/documentation/18.0/developer/reference/cli.html) - --test-tags, --test-enable, --stop-after-init

### Secondary (MEDIUM confidence)
- [product.category model pattern](https://www.odoo.com/forum/help-1/how-do-i-make-a-field-that-has-a-hierarchy-such-as-the-product-category-field-of-the-product-model-208190) - Canonical hierarchical model implementation with complete_name, _parent_store
- [Hierarchical Models in Odoo](https://www.hynsys.com/blog/odoo-development-5/hierarchical-models-in-odoo-6) - _parent_store explanation, parent_path mechanics
- [_parent_store forum discussion](https://www.odoo.com/forum/help-1/what-is-parent-store-214936) - Community verification of _parent_store behavior
- [Odoo GitHub PR #22558](https://github.com/odoo/odoo/pull/22558) - New implementation for child_of/parent_of using parent_path
- [Programmatically test constraints](https://www.odoo.com/forum/help-1/programatically-test-constraints-validation-191188) - assertRaises pattern for constraint testing

### Tertiary (LOW confidence)
- [Odoo Development Best Practices - constraints](https://odoo-development.readthedocs.io/en/latest/dev/py/constraints.html) - General constraint patterns (older docs, patterns still valid)
- [GitHub Issue #31010](https://github.com/odoo/odoo/issues/31010) - parent_path not computed for pre-existing entries when adding _parent_store (edge case to know about)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Odoo 18 documentation, verified Docker setup already in project
- Architecture: HIGH - product.category is canonical reference, pattern unchanged across Odoo 12-18
- Pitfalls: HIGH - Multiple sources confirm each pitfall (ORM docs + GitHub issues + community reports)
- Testing: HIGH - Official Odoo 18 testing docs, well-documented TransactionCase API
- Level computation approach: MEDIUM - Two valid approaches (recursive parent_id vs parent_path counting), recommendation based on constraint timing analysis that needs validation during implementation

**Research date:** 2026-02-05
**Valid until:** 2026-04-05 (Odoo 18 is stable LTS, patterns unlikely to change within 60 days)
