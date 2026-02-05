# Phase 2: Sale Order Integration - Research

**Researched:** 2026-02-05
**Domain:** Odoo 18 sale.order and sale.order.line extension with _inherit, computed field patterns for recursive totals, inline tree views with hierarchy, smart buttons, context propagation
**Confidence:** HIGH

## Summary

Phase 2 integrates the foundational `sale.order.segment` model (from Phase 1) with Odoo's native `sale.order` and `sale.order.line` models. This phase establishes the bidirectional relationships needed for users to organize sale order line items into hierarchical segments and view calculated subtotals directly within the sale order form.

The standard approach uses Odoo's `_inherit` mechanism to extend existing models without modifying core code. For `sale.order`, we add a One2many field `segment_ids` pointing to segments. For `sale.order.line`, we add a Many2one field `segment_id` to assign products to specific segments. Computed fields with `@api.depends` handle recursive total calculations: `subtotal` (sum of own products) and `total` (subtotal + children totals). Inline tree views embedded in the sale order form display the segment hierarchy with expandable levels. Smart buttons with count badges provide navigation from sale order to filtered segment views. Context propagation ensures `order_id` defaults correctly when creating segments from the sale order form.

Key recommendations: (1) Use `@api.depends('line_ids.price_subtotal')` for segment subtotal computation with `store=True` for performance. (2) Implement recursive total calculation by walking `child_ids` in the compute method. (3) Embed inline tree view using `<field name="segment_ids"><tree></tree></field>` pattern within the sale order form. (4) Use computed Integer field for segment count with `search_count()` for smart button badge. (5) Pass default context `{'default_order_id': active_id}` in One2many field definition. (6) Add domain constraint on `segment_id` in sale.order.line: `[('order_id', '=', parent.order_id)]`.

**Primary recommendation:** Follow the standard Odoo invoice line aggregation pattern for subtotals (sum of related records) and the product.category complete_name pattern for hierarchical display with parent context.

## Standard Stack

The established libraries/tools for this phase:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Odoo | 18.0 | ERP framework + ORM | Required base platform. Provides `_inherit` mechanism, computed fields with dependencies, inline views, smart button patterns. |
| sale module | 18.0 (core) | Sale Order management | Core Odoo module being extended. Provides `sale.order` and `sale.order.line` models. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @api.depends | 18.0 (ORM) | Computed field dependency tracking | All computed fields (subtotal, total, segment_count). Triggers recomputation on field changes. |
| odoo.fields.Command | 18.0 | X2many field manipulation | Creating segments with related lines in tests or migrations. Provides `Command.create()`, `Command.link()`. |
| odoo.tests.Form | 18.0 | Form view simulation in tests | Testing One2many inline tree interactions, context propagation, domain restrictions. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `_inherit` for model extension | Direct modification of core `sale.py` | Core modification breaks upgradeability. `_inherit` is modular and upgrade-safe. Always use `_inherit`. |
| Computed fields with `store=True` | Real-time computation without storage | Real-time causes write amplification on every line change. `store=True` with proper `@api.depends` provides cached results. Use stored fields. |
| Inline tree view in form | Separate menu action for segments | Separate view requires navigation away from sale order. Inline tree keeps context and reduces clicks. Use inline. |
| Domain on Many2one field | Python `@api.constrains` validation | Domain filters dropdown choices at UI level (better UX). Constraints validate at save (backup). Use both: domain for UX, constraint for data integrity. |

**Installation:**
```bash
# No additional packages - all functionality from Odoo 18 built-ins.
# Module update after adding Phase 2 code:
docker compose exec odoo odoo -d spora -u spora_segment --stop-after-init
```

## Architecture Patterns

### Recommended Module Structure (Phase 2 additions)
```
addons/spora_segment/
    models/
        __init__.py                      # ADD: imports sale_order, sale_order_line
        sale_order_segment.py            # MODIFY: add order_id, line_ids, subtotal, total
        sale_order.py                    # NEW: extend sale.order with segment_ids
        sale_order_line.py               # NEW: extend sale.order.line with segment_id
    views/
        sale_order_segment_views.xml     # MODIFY: add inline tree for sale order form
        sale_order_views.xml             # NEW: inherit sale order form, add segment tree + smart button
```

### Pattern 1: Extending existing model with _inherit (One2many relationship)
**What:** Add a One2many relationship to an existing core model without modifying its source code.
**When to use:** Any time you need to add fields or methods to core Odoo models (`sale.order`, `res.partner`, etc.).
**Example:**
```python
# Source: Context7 - Odoo 18 Developer docs
# https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/12_inheritance
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    segment_ids = fields.One2many(
        'sale.order.segment',
        'order_id',
        string='Segments',
        help='Hierarchical organization of order lines into segments.',
    )

    segment_count = fields.Integer(
        string='Segment Count',
        compute='_compute_segment_count',
    )

    def _compute_segment_count(self):
        for order in self:
            order.segment_count = len(order.segment_ids)
```

### Pattern 2: Extending existing model with _inherit (Many2one relationship)
**What:** Add a Many2one relationship to an existing model to link records to another model.
**When to use:** When assigning existing records (like order lines) to categories or parent records (like segments).
**Example:**
```python
# Source: Context7 - Odoo 18 Developer docs
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    segment_id = fields.Many2one(
        'sale.order.segment',
        string='Segment',
        help='Assign this order line to a specific segment.',
        domain="[('order_id', '=', order_id)]",  # Only segments from same order
        index=True,
    )
```

### Pattern 3: Computed field with dotted path dependencies (sum of related records)
**What:** Compute a total by aggregating values from related One2many or Many2many records using dotted path notation.
**When to use:** Calculating subtotals, averages, or counts from related records (e.g., sum of order line prices).
**Example:**
```python
# Source: Context7 - Odoo 18 ORM API
# https://www.odoo.com/documentation/18.0/developer/reference/backend/orm
from odoo import models, fields, api

class SaleOrderSegment(models.Model):
    _inherit = 'sale.order.segment'

    line_ids = fields.One2many(
        'sale.order.line',
        'segment_id',
        string='Order Lines',
    )

    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        readonly=True,
    )

    @api.depends('line_ids.price_subtotal')
    def _compute_subtotal(self):
        """Sum of direct order lines assigned to this segment."""
        for segment in self:
            segment.subtotal = sum(segment.line_ids.mapped('price_subtotal'))
```

**Why dotted path:** `@api.depends('line_ids.price_subtotal')` tells Odoo to recompute when ANY line's price changes, not just when lines are added/removed. This handles quantity/price updates automatically.

### Pattern 4: Recursive computed field (total including children)
**What:** Compute a total that includes both direct values and recursive aggregation from child records.
**When to use:** Hierarchical totals (segment total = own subtotal + sum of children totals).
**Example:**
```python
# Source: Recursive pattern adapted from product.category complete_name
from odoo import models, fields, api

class SaleOrderSegment(models.Model):
    _inherit = 'sale.order.segment'

    total = fields.Monetary(
        string='Total',
        compute='_compute_total',
        store=True,
        currency_field='currency_id',
        help='Subtotal of own lines plus total of all child segments.',
    )

    @api.depends('subtotal', 'child_ids.total')
    def _compute_total(self):
        """Recursive total: own subtotal + sum of children totals."""
        for segment in self:
            children_total = sum(segment.child_ids.mapped('total'))
            segment.total = segment.subtotal + children_total
```

**Why recursive dependency:** `@api.depends('child_ids.total')` creates a cascade: when a grandchild's total changes, child recomputes, which triggers parent recomputation. This propagates changes up the hierarchy automatically.

**Performance consideration:** With `store=True`, totals are cached in database. Only recomputed when dependencies change, not on every read.

### Pattern 5: Inline tree view in form (One2many display with hierarchy)
**What:** Display a tree (list) view of related records directly within a parent form view, with custom columns and inline editing.
**When to use:** Showing One2many relationships where immediate visibility and context are important (e.g., segments within sale order).
**Example:**
```xml
<!-- Source: Context7 - Odoo 18 Developer docs - inline list view pattern -->
<!-- https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/11_sprinkles -->
<record id="sale_order_view_form_inherit_segment" model="ir.ui.view">
    <field name="name">sale.order.form.inherit.segment</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_order_form"/>
    <field name="arch" type="xml">
        <xpath expr="//notebook" position="inside">
            <page string="Segments" name="segments">
                <field name="segment_ids" context="{'default_order_id': active_id}">
                    <tree>
                        <field name="sequence" widget="handle"/>
                        <field name="name"/>
                        <field name="parent_id"/>
                        <field name="level"/>
                        <field name="subtotal" sum="Subtotal"/>
                        <field name="total" sum="Total"/>
                    </tree>
                </field>
            </page>
        </xpath>
    </field>
</record>
```

**Context propagation:** `context="{'default_order_id': active_id}"` ensures that when user clicks "Add a line" in the tree, the new segment automatically gets `order_id` set to current sale order.

**Sum attribute:** `sum="Subtotal"` displays a sum footer at the bottom of the column in the tree view.

### Pattern 6: Smart button with count and action
**What:** Clickable button in form header showing a count badge and opening a filtered view when clicked.
**When to use:** Navigation from parent record to related records with visual count indicator.
**Example:**
```xml
<!-- Source: Context7 - Odoo 18 Developer docs - stat button pattern -->
<!-- https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/11_sprinkles -->
<xpath expr="//div[@name='button_box']" position="inside">
    <button name="action_view_segments"
            type="object"
            class="oe_stat_button"
            icon="fa-sitemap"
            invisible="segment_count == 0">
        <field name="segment_count" widget="statinfo" string="Segments"/>
    </button>
</xpath>
```

**Python action method:**
```python
def action_view_segments(self):
    """Open tree view of segments filtered to this order."""
    self.ensure_one()
    return {
        'type': 'ir.actions.act_window',
        'name': 'Segments',
        'res_model': 'sale.order.segment',
        'view_mode': 'tree,form',
        'domain': [('order_id', '=', self.id)],
        'context': {'default_order_id': self.id},
    }
```

**Key components:**
- `segment_count` computed field (Integer)
- `oe_stat_button` CSS class for styling
- `statinfo` widget for count display
- Action method returning `ir.actions.act_window` dict with domain filter

**Source references:**
- [How to Create Smart Buttons in Odoo 18](https://www.devintellecs.com/blog/odoo-technical-4/how-to-create-smart-buttons-in-odoo-18-110)
- [How to Add Smart Buttons in Odoo 18](https://www.cybrosys.com/blog/how-to-add-smart-buttons-in-odoo-18)

### Pattern 7: Domain constraint on Many2one field based on parent record
**What:** Restrict dropdown choices in a Many2one field to records that match criteria from the parent record.
**When to use:** Ensuring referential integrity (e.g., segment must belong to same sale order as the line).
**Example:**
```xml
<!-- XML domain (filters dropdown in UI) -->
<field name="segment_id" domain="[('order_id', '=', order_id)]"/>
```

```python
# Python constraint (validates at save - data integrity backup)
from odoo import models, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('segment_id', 'order_id')
    def _check_segment_order(self):
        """Segment must belong to same order as the line."""
        for line in self:
            if line.segment_id and line.segment_id.order_id != line.order_id:
                raise ValidationError(
                    'Segment "%s" does not belong to order "%s". '
                    'Cannot assign line to segment from different order.'
                    % (line.segment_id.name, line.order_id.name)
                )
```

**Why both domain and constraint:**
- **Domain:** Filters UI dropdown, prevents user from seeing invalid choices (better UX)
- **Constraint:** Validates at database level, catches API/import violations (data integrity)

**Domain syntax:** String-based domain in XML references field names directly. Odoo evaluates `order_id` as the current record's order_id value.

**Source references:**
- [Use a domain filter on many2one field - Odoo Forum](https://www.odoo.com/forum/help-1/use-a-domain-filter-on-many2one-field-46554)
- [How to filter Many2one field according to the parent - Odoo Forum](https://www.odoo.com/forum/help-1/how-to-filter-many2one-field-according-to-the-parent-184539)

### Pattern 8: Context propagation for default field values
**What:** Pass default values from parent record to child records created via One2many form.
**When to use:** Auto-populating fields when creating related records (e.g., segment created from sale order should default order_id).
**Example:**
```xml
<!-- In sale.order form view -->
<field name="segment_ids" context="{'default_order_id': active_id, 'default_currency_id': currency_id}"/>
```

```python
# In sale.order.segment model - optional default_get override for complex defaults
from odoo import models, api

class SaleOrderSegment(models.Model):
    _inherit = 'sale.order.segment'

    @api.model
    def default_get(self, fields_list):
        """Override to set complex defaults from context."""
        defaults = super().default_get(fields_list)

        # Context set from parent form
        if self.env.context.get('default_order_id'):
            order_id = self.env.context['default_order_id']
            order = self.env['sale.order'].browse(order_id)

            # Set additional defaults based on order
            defaults['currency_id'] = order.currency_id.id
            # Could set other fields based on order context

        return defaults
```

**Context keys:**
- `default_<field_name>`: Sets default value for field in new record form
- `active_id`: ID of current record (parent)
- Custom keys: Pass any data to child form via context

**When to use default_get:** Most defaults handled by `context={'default_field': value}` in XML. Use `default_get` override only for complex logic that depends on multiple context values or requires database lookups.

**Source references:**
- [Set default value in child form by sending context from parent form - Odoo Forum](https://www.odoo.com/forum/help-1/set-default-value-in-child-form-by-sending-context-from-parent-form-218730)
- [How to Set default value while creating record from one2many field - Odoo Forum](https://www.odoo.com/forum/help-1/how-to-set-default-value-while-creating-record-from-one2many-field-139969)

### Anti-Patterns to Avoid
- **Not using `store=True` on computed totals:** Real-time computation causes write amplification. Every line change triggers recomputation. Store results for performance.
- **Forgetting currency_field on Monetary fields:** Monetary fields require `currency_field='currency_id'` parameter to display with correct currency symbol.
- **Domain in Python model instead of XML view:** Domains should be in XML (UI-level filtering) with Python constraints as backup. Python-only domains don't filter dropdowns.
- **Hardcoding order_id in segment creation:** Use context propagation `{'default_order_id': active_id}` instead of manual field assignment. Works with quick-create and full form.
- **Not handling empty recordsets in computed fields:** Always iterate `for record in self:` even for single-record computes. Empty recordsets cause errors.
- **Missing `@api.depends` on computed fields:** Without proper dependencies, fields won't recompute when source data changes. Critical for cached (stored) fields.
- **Using `sum()` on recordset without `mapped()`:** `sum(recordset.field)` doesn't work. Use `sum(recordset.mapped('field'))` to extract field values first.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Aggregating related record values | Custom SQL query or manual loop | `@api.depends('relation.field')` + `sum(records.mapped('field'))` | ORM handles caching, triggers recomputation on changes, respects security rules. SQL bypasses all of this. |
| Filtering Many2one dropdown by parent field | Custom onchange method that hides invalid choices | Domain on field: `domain="[('parent_field', '=', field)]"` | Native domain filtering is UI-native, faster, and works with quick-create forms. Onchange is heavier. |
| Propagating defaults from parent to child | Custom JavaScript or onchange logic | Context in XML: `context="{'default_field': value}"` | Built into framework, works with all form types (popup, inline, full form). JS is fragile across updates. |
| Counting related records for badge | SQL query or `len()` call in view | Computed Integer field with `len(self.relation)` | Computed field is cached, can be used in searches/filters. Direct `len()` in view isn't cached. |
| Displaying hierarchy in form | Custom tree widget or JavaScript | Standard One2many with inline `<tree>` definition | Native pattern, no custom code, upgrade-safe. Custom widgets break on Odoo updates. |
| Smart button action | Custom route and controller | Standard `ir.actions.act_window` dict returned from button method | Native action handling, integrates with breadcrumbs, back button, access control. Custom routes bypass framework. |

**Key insight:** Odoo's `_inherit` mechanism and computed field system handle model extension and reactive calculations better than any custom implementation. The framework provides domain filtering, context propagation, and inline view embedding out of the box.

## Common Pitfalls

### Pitfall 1: Computed fields without proper dependencies
**What goes wrong:** Subtotal or total fields show stale values. Changing line prices or adding/removing lines doesn't update segment totals.
**Why it happens:** Missing or incorrect `@api.depends()` decorator. Odoo doesn't know WHEN to recompute the field.
**How to avoid:**
- For subtotal: `@api.depends('line_ids.price_subtotal')` (dotted path to track line field changes)
- For total: `@api.depends('subtotal', 'child_ids.total')` (depends on own subtotal AND children's totals for recursion)
**Warning signs:** Totals don't update after editing lines, need to reload page to see correct values.

### Pitfall 2: Recursive computed field without child_ids dependency
**What goes wrong:** Parent segment total doesn't update when child segment total changes (e.g., child gets new products).
**Why it happens:** `@api.depends('child_ids.total')` is missing. Parent doesn't know children's totals changed.
**How to avoid:** Always include `child_ids.<computed_field>` in recursive dependencies. This creates cascade: child recomputes → parent dependency triggers → parent recomputes.
**Warning signs:** Parent totals only update when parent's own lines change, not when descendant lines change.

### Pitfall 3: Forgetting to add currency_id relation to segment
**What goes wrong:** Monetary fields (subtotal, total) display without currency symbol or with wrong currency.
**Why it happens:** Monetary field type requires a related currency_id field on the same model. Segment doesn't inherit this from sale.order automatically.
**How to avoid:** Add `currency_id = fields.Many2one(related='order_id.currency_id', store=True, readonly=True)` to segment model. Reference it in Monetary fields: `currency_field='currency_id'`.
**Warning signs:** Totals display as raw numbers without currency symbol, or show "False" in form view.

### Pitfall 4: Domain constraint but no XML domain on Many2one
**What goes wrong:** User can select invalid segments from dropdown (e.g., segment from different order), gets error only when saving.
**Why it happens:** Python `@api.constrains` validates at save time, but doesn't filter UI dropdown. Poor user experience.
**How to avoid:** Add both: (1) XML domain `domain="[('order_id', '=', order_id)]"` on field to filter dropdown, AND (2) Python constraint as data integrity backup for API/imports.
**Warning signs:** Users complain about confusing validation errors after filling form, dropdown shows too many irrelevant choices.

### Pitfall 5: Missing context in One2many field definition
**What goes wrong:** Creating segment from sale order form doesn't auto-populate order_id. User must manually select order from dropdown.
**Why it happens:** No context passed from parent (sale order) to child form (segment creation form).
**How to avoid:** In sale.order form view XML: `<field name="segment_ids" context="{'default_order_id': active_id}"/>`. The `active_id` refers to current sale order ID.
**Warning signs:** order_id field is empty when creating new segment, user must fill manually (shouldn't happen).

### Pitfall 6: Not inheriting sale.order form correctly
**What goes wrong:** Adding segment tree to form doesn't appear, or creates duplicate form definition.
**Why it happens:** Using `<field name="arch">` with full form reproduction instead of `<xpath>` to inject into specific location.
**How to avoid:** Use `inherit_id` pointing to original view and `<xpath expr="//notebook" position="inside">` to ADD a page, not replace entire form.
**Warning signs:** Original sale order tabs disappear, or segment tab doesn't show, or update fails with "duplicate view" error.

### Pitfall 7: Storing computed field without store=True
**What goes wrong:** Performance degrades. Subtotal/total computed on EVERY read (every time form opens, every search, every report).
**Why it happens:** Developer thinks "computed field" means don't store. Actually, stored computed fields are cached and only recomputed when dependencies change.
**How to avoid:** Always use `store=True` on computed Monetary fields used for display or filtering. Exceptions: fields that depend on context (like current user) or external data (like current date).
**Warning signs:** Slow form loads, database CPU spikes when opening sale orders with many segments.

### Pitfall 8: Sum attribute in tree view without stored field
**What goes wrong:** Tree view footer shows "Sum: 0.00" or incorrect values.
**Why it happens:** `sum="Label"` attribute in tree view XML works best with stored fields. Unstored computed fields may not aggregate correctly in list views.
**How to avoid:** Use `store=True` on fields that will be summed in tree views. Odoo needs database values to aggregate efficiently.
**Warning signs:** Footer sum is always zero, or shows sum of only visible records (pagination issue).

## Code Examples

Verified patterns from official sources and web research:

### Complete sale.order extension (Phase 2)
```python
# models/sale_order.py
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    segment_ids = fields.One2many(
        'sale.order.segment',
        'order_id',
        string='Segments',
        help='Hierarchical organization of order lines into segments.',
    )

    segment_count = fields.Integer(
        string='Segment Count',
        compute='_compute_segment_count',
    )

    def _compute_segment_count(self):
        """Count segments for smart button badge."""
        for order in self:
            order.segment_count = len(order.segment_ids)

    def action_view_segments(self):
        """Smart button action: open segment tree filtered to this order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Segments',
            'res_model': 'sale.order.segment',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {
                'default_order_id': self.id,
                'default_currency_id': self.currency_id.id,
            },
        }
```

### Complete sale.order.line extension (Phase 2)
```python
# models/sale_order_line.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    segment_id = fields.Many2one(
        'sale.order.segment',
        string='Segment',
        help='Assign this order line to a specific segment.',
        domain="[('order_id', '=', order_id)]",
        index=True,
    )

    @api.constrains('segment_id', 'order_id')
    def _check_segment_order(self):
        """Validate segment belongs to same order as line."""
        for line in self:
            if line.segment_id and line.segment_id.order_id != line.order_id:
                raise ValidationError(
                    'Error: Cannot assign line to segment "%s" because it '
                    'belongs to a different sale order. Segment\'s order: "%s", '
                    'Line\'s order: "%s".' % (
                        line.segment_id.name,
                        line.segment_id.order_id.name,
                        line.order_id.name,
                    )
                )
```

### Complete sale.order.segment additions (Phase 2)
```python
# models/sale_order_segment.py (modifications to Phase 1 model)
from odoo import models, fields, api

class SaleOrderSegment(models.Model):
    _inherit = 'sale.order.segment'

    # New field: order relationship
    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        index=True,
        ondelete='cascade',
    )

    # New field: currency (needed for Monetary fields)
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        readonly=True,
    )

    # New field: order lines assigned to this segment
    line_ids = fields.One2many(
        'sale.order.line',
        'segment_id',
        string='Order Lines',
    )

    # New computed field: subtotal of own lines
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id',
        help='Sum of order lines directly assigned to this segment (not including children).',
    )

    # New computed field: total including children
    total = fields.Monetary(
        string='Total',
        compute='_compute_total',
        store=True,
        currency_field='currency_id',
        help='Subtotal of own lines plus total of all child segments (recursive).',
    )

    @api.depends('line_ids.price_subtotal')
    def _compute_subtotal(self):
        """Compute subtotal: sum of own order lines."""
        for segment in self:
            segment.subtotal = sum(segment.line_ids.mapped('price_subtotal'))

    @api.depends('subtotal', 'child_ids.total')
    def _compute_total(self):
        """Compute total recursively: own subtotal + children totals."""
        for segment in self:
            children_total = sum(segment.child_ids.mapped('total'))
            segment.total = segment.subtotal + children_total

    @api.constrains('parent_id', 'order_id')
    def _check_parent_same_order(self):
        """Validate parent segment belongs to same order."""
        for segment in self:
            if segment.parent_id and segment.parent_id.order_id != segment.order_id:
                raise ValidationError(
                    'Error: Cannot set parent segment "%s" because it belongs '
                    'to a different sale order.' % segment.parent_id.name
                )
```

### Sale order form view inheritance (Phase 2)
```xml
<!-- views/sale_order_views.xml -->
<odoo>
    <!-- Inherit sale.order form to add segments tab and smart button -->
    <record id="sale_order_view_form_inherit_segment" model="ir.ui.view">
        <field name="name">sale.order.form.inherit.segment</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">

            <!-- Add smart button to header -->
            <xpath expr="//div[@name='button_box']" position="inside">
                <button name="action_view_segments"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-sitemap"
                        invisible="segment_count == 0">
                    <field name="segment_count" widget="statinfo" string="Segments"/>
                </button>
            </xpath>

            <!-- Add segments tab to notebook -->
            <xpath expr="//notebook" position="inside">
                <page string="Segments" name="segments">
                    <field name="segment_ids"
                           context="{'default_order_id': active_id}">
                        <tree>
                            <field name="sequence" widget="handle"/>
                            <field name="name"/>
                            <field name="parent_id"/>
                            <field name="level"/>
                            <field name="subtotal" sum="Subtotal"/>
                            <field name="total" sum="Total"/>
                        </tree>
                    </field>
                </page>
            </xpath>

        </field>
    </record>
</odoo>
```

### Sale order line form view inheritance (add segment field)
```xml
<!-- views/sale_order_views.xml (additional inheritance) -->
<record id="sale_order_line_view_form_inherit_segment" model="ir.ui.view">
    <field name="name">sale.order.line.form.inherit.segment</field>
    <field name="model">sale.order.line</field>
    <field name="inherit_id" ref="sale.view_order_line_form"/>
    <field name="arch" type="xml">
        <field name="product_id" position="after">
            <field name="segment_id"
                   options="{'no_create': True, 'no_open': True}"
                   domain="[('order_id', '=', order_id)]"/>
        </field>
    </field>
</record>
```

### Test: Computed subtotal and total
```python
# tests/test_sale_order_segment.py (additions)
from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestSaleOrderSegmentIntegration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderLine = cls.env['sale.order.line']
        cls.Segment = cls.env['sale.order.segment']
        cls.Product = cls.env['product.product']

        # Create test data
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.product_a = cls.Product.create({
            'name': 'Product A',
            'list_price': 100.0,
        })
        cls.product_b = cls.Product.create({
            'name': 'Product B',
            'list_price': 200.0,
        })

        cls.order = cls.SaleOrder.create({
            'partner_id': cls.partner.id,
        })

    def test_segment_subtotal_sum_of_lines(self):
        """Segment subtotal = sum of assigned order lines."""
        segment = self.Segment.create({
            'name': 'Test Segment',
            'order_id': self.order.id,
        })

        # Add two lines to segment
        line_a = self.SaleOrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 2,  # 2 * 100 = 200
            'segment_id': segment.id,
        })
        line_b = self.SaleOrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 1,  # 1 * 200 = 200
            'segment_id': segment.id,
        })

        # Subtotal should be 400 (200 + 200)
        self.assertEqual(segment.subtotal, 400.0)

    def test_segment_total_includes_children(self):
        """Segment total = own subtotal + children totals (recursive)."""
        parent = self.Segment.create({
            'name': 'Parent',
            'order_id': self.order.id,
        })
        child = self.Segment.create({
            'name': 'Child',
            'parent_id': parent.id,
            'order_id': self.order.id,
        })

        # Parent has one line: 100
        self.SaleOrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,  # 1 * 100 = 100
            'segment_id': parent.id,
        })

        # Child has one line: 200
        self.SaleOrderLine.create({
            'order_id': self.order.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 1,  # 1 * 200 = 200
            'segment_id': child.id,
        })

        # Parent subtotal: 100 (own line)
        self.assertEqual(parent.subtotal, 100.0)
        # Parent total: 100 (own) + 200 (child) = 300
        self.assertEqual(parent.total, 300.0)

        # Child subtotal: 200
        self.assertEqual(child.subtotal, 200.0)
        # Child total: 200 (no children)
        self.assertEqual(child.total, 200.0)

    def test_segment_domain_prevents_cross_order_assignment(self):
        """Cannot assign line to segment from different order."""
        order2 = self.SaleOrder.create({'partner_id': self.partner.id})
        segment2 = self.Segment.create({
            'name': 'Segment Order 2',
            'order_id': order2.id,
        })

        # Try to assign line from order1 to segment from order2
        with self.assertRaises(ValidationError):
            self.SaleOrderLine.create({
                'order_id': self.order.id,
                'product_id': self.product_a.id,
                'segment_id': segment2.id,  # Wrong order!
            })

    def test_smart_button_count(self):
        """Segment count shows correct number for smart button."""
        self.assertEqual(self.order.segment_count, 0)

        seg1 = self.Segment.create({'name': 'Seg 1', 'order_id': self.order.id})
        self.assertEqual(self.order.segment_count, 1)

        seg2 = self.Segment.create({'name': 'Seg 2', 'order_id': self.order.id})
        self.assertEqual(self.order.segment_count, 2)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Compute totals in onchange methods | `@api.depends()` with `store=True` | Odoo 13+ | Stored computed fields cache results, trigger only on dependency changes. Onchange is client-side only. |
| `attrs={'invisible': [...]}` dict syntax | `invisible="expression"` inline | Odoo 17+ | Cleaner XML, Python expressions instead of domain syntax. Old attrs still works but deprecated. |
| Manual _sql_constraints for foreign keys | Use `ondelete='cascade'` on Many2one | Always available | Cascade handled by ORM, no SQL needed. More maintainable. |
| sum() in tree view via custom widget | Native `sum="Label"` attribute | Odoo 10+ | Built-in aggregation, no custom code needed. Works with pagination. |
| Button actions via controller routes | Return `ir.actions.act_window` dict from button method | Standard pattern | Integrated with framework, access control, breadcrumbs. Routes are overkill. |

**Deprecated/outdated:**
- `@api.onchange` for calculations that should be stored: Use `@api.depends` with `store=True` instead
- Computing totals without `store=True`: Causes performance issues on reads
- Not using dotted path in dependencies: `@api.depends('line_ids')` won't trigger on line field changes, need `line_ids.price_subtotal`

## Open Questions

Things that couldn't be fully resolved:

1. **Tree view expandable hierarchy in inline context**
   - What we know: Standard tree views support hierarchy with parent_id. Inline tree views (within One2many) display records flat by default.
   - What's unclear: Whether inline tree automatically supports expand/collapse for hierarchical data, or requires additional attributes/widgets.
   - Recommendation: Test with basic inline tree first. If hierarchy doesn't expand, investigate `parent_key` attribute or custom tree widget. Phase 1 research mentioned `field_parent` but didn't find Odoo 18 docs confirming syntax.
   - **Action:** Prototype inline tree in Phase 2 implementation. If flat, research Phase 5 UX requirements (UX-01) for `recursive="1"` attribute.

2. **Performance of recursive total computation with deep hierarchies**
   - What we know: `@api.depends('child_ids.total')` creates cascade recomputation. With 4 levels max and stored fields, should be acceptable.
   - What's unclear: Actual performance impact with 50+ segments and 200+ lines per order. Database query count for cascade recomputation.
   - Recommendation: Implement as designed (stored computed fields). Monitor performance in Phase 2 testing. If slow, investigate: (1) batch recomputation, (2) SQL aggregation as alternative, (3) denormalized total storage pattern.

3. **Inline tree view editability for segments**
   - What we know: Inline trees can be editable (quick-create). Users should be able to add segments directly from sale order form.
   - What's unclear: Whether inline tree should allow editing segment fields inline, or always open form popup.
   - Recommendation: Start with non-editable tree (`editable="false"` or omit attribute). Users click "Add a line" → opens form popup with context. Inline editing of hierarchy fields is complex UX. Evaluate in Phase 5 UX requirements.

4. **Smart button icon choice**
   - What we know: Font Awesome icons available via `icon="fa-iconname"`. Common choices: `fa-sitemap` (hierarchy), `fa-list` (list), `fa-folder-tree` (tree).
   - Recommendation: Use `icon="fa-sitemap"` (network/hierarchy visual). Matches mental model of segment hierarchy better than generic list icon.

## Sources

### Primary (HIGH confidence)
- [Odoo 18.0 Developer - Model Inheritance](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/12_inheritance) - Context7 verified: `_inherit` pattern, adding fields to existing models
- [Odoo 18.0 Developer - Relations Between Models](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/07_relations) - Context7 verified: One2many/Many2one definitions, inverse relationships
- [Odoo 18.0 Developer - Computed Fields](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/08_compute_onchange) - Context7 verified: `@api.depends`, dotted path dependencies, `store=True`
- [Odoo 18.0 ORM API - Computed Fields](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm) - Context7 verified: dotted path for related field dependencies, recursive computation
- [Odoo 18.0 Developer - Inline Views](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/11_sprinkles) - Context7 verified: inline list view pattern within One2many fields
- [Odoo 18.0 Developer - Testing](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing) - Context7 verified: Form tests for One2many manipulation

### Secondary (MEDIUM confidence)
- [How to Create Smart Buttons in Odoo 18 - Devintellecs](https://www.devintellecs.com/blog/odoo-technical-4/how-to-create-smart-buttons-in-odoo-18-110) - WebSearch: Smart button implementation with computed count field, `oe_stat_button` class, `statinfo` widget
- [How to Add Smart Buttons in Odoo 18 - Cybrosys](https://www.cybrosys.com/blog/how-to-add-smart-buttons-in-odoo-18) - WebSearch: Smart button pattern with action window return dict
- [Set default value in child form by sending context - Odoo Forum](https://www.odoo.com/forum/help-1/set-default-value-in-child-form-by-sending-context-from-parent-form-218730) - WebSearch: Context propagation with `default_` prefix, `active_id` usage
- [How to filter Many2one field according to the parent - Odoo Forum](https://www.odoo.com/forum/help-1/how-to-filter-many2one-field-according-to-the-parent-184539) - WebSearch: Domain syntax for parent-based filtering
- [How to display 'total' under a column in tree view - Odoo Forum](https://www.odoo.com/forum/help-1/how-to-display-total-under-a-column-containing-numeric-values-in-tree-view-83371) - WebSearch: `sum="Label"` attribute in tree view XML

### Tertiary (LOW confidence)
- [Odoo tree view expandable hierarchy - WebSearch](https://www.odoo.com/forum/help-1/project-hierarchic-tree-view-23080) - Community discussion: mentions `parent_left`/`parent_right` (deprecated), `field_parent` attribute (not verified for Odoo 18)
- [Computed field recursive tree sum - GitHub Issue #35557](https://github.com/odoo/odoo/issues/35557) - WebSearch: Sum attribute only computes current page (pagination issue), stored fields recommended

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Odoo 18 documentation via Context7, verified inheritance and computed field patterns
- Architecture patterns: HIGH - Context7 verified all core patterns (inherit, depends, inline views, domains)
- Smart buttons: MEDIUM - Web search sources (Devintellecs, Cybrosys) show consistent pattern, not official docs but reliable
- Context propagation: MEDIUM - Forum sources with community verification, pattern consistent across Odoo 14-18
- Tree view hierarchy: LOW - WebSearch found references but no Odoo 18 official docs on expandable inline trees. Needs implementation testing.

**Research date:** 2026-02-05
**Valid until:** 2026-04-05 (Odoo 18 stable, patterns unlikely to change within 60 days)
