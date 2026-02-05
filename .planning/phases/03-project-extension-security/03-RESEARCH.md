# Phase 3: Project Extension & Security - Research

**Researched:** 2026-02-05
**Domain:** Odoo 18 model extension, Many2one relationships, security rules, field visibility
**Confidence:** HIGH

## Summary

Phase 3 extends the project.task model with a segment_id field to trace tasks back to their originating sale order segments, implementing cross-model validation and security rules. The research focused on Odoo 18's standard patterns for Many2one relationships, conditional field visibility, validation constraints, and security inheritance.

Key findings indicate that Odoo 18 provides robust built-in mechanisms for all required functionality: Many2one fields with ondelete behaviors, @api.constrains decorators for cross-model validation, conditional field visibility via invisible attributes in XML views, and security through ir.model.access.csv combined with record rules. The user decision to implement a "warning modal" for cross-order validation should use ValidationError (not UserError) as it relates to data integrity rather than business logic restrictions.

**Primary recommendation:** Extend project.task model via inheritance, use ValidationError for cross-order validation with modal blocking, implement field visibility with invisible attribute bound to project_id.sale_order_id, and leverage Odoo's automatic Many2one security inheritance for segment access control.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Odoo ORM | 18.0 | Model extension, field definitions, constraints | Official Odoo framework, used across all modules |
| odoo.exceptions | 18.0 | ValidationError, UserError | Standard exception handling for Odoo business logic |
| @api.constrains | 18.0 | Field validation decorator | Odoo's built-in constraint validation mechanism |
| ir.model.access.csv | 18.0 | Model-level security | Standard Odoo security configuration |
| ir.rule (record rules) | 18.0 | Record-level security | Fine-grained access control per record |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @api.ondelete | 18.0 | Prevent deletion with conditions | When deletion must be blocked based on business rules |
| _check_company_auto | 18.0 | Multi-company consistency | When models must respect company boundaries |
| RedirectWarning | 18.0 | Warning with action button | When user needs to be redirected to fix an issue |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ValidationError | UserError | ValidationError is semantically correct for data validation; UserError is for business logic restrictions |
| @api.constrains | Manual validation in create/write | Constrains decorator is cleaner and automatically triggered |
| invisible attribute | domains on fields | invisible is for UI hiding, domains are for filtering choices (different purposes) |

**Installation:**
```bash
# No external packages needed - uses Odoo 18 built-in features
# Module dependencies in __manifest__.py:
depends = ['sale', 'project']
```

## Architecture Patterns

### Recommended Project Structure
```
addons/
└── spora_segment/
    ├── models/
    │   ├── project_task.py          # Extend project.task with segment_id
    │   └── sale_order_segment.py    # Add deletion constraint for segments with tasks
    ├── views/
    │   └── project_task_views.xml   # Inherit task form view to add segment_id field
    ├── security/
    │   └── ir.model.access.csv      # Already exists from Phase 1/2, no changes needed
    └── __manifest__.py              # Add 'project' to depends
```

### Pattern 1: Many2one Field Extension with Conditional Visibility

**What:** Add a Many2one field to an existing model with visibility controlled by related field value
**When to use:** When extending core models with optional fields that only apply in certain contexts
**Example:**
```python
# Source: Context7 /websites/odoo_18_0_developer
from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    segment_id = fields.Many2one(
        'sale.order.segment',
        string='Budget Segment',
        index=True,
        ondelete='restrict',  # Prevent segment deletion if tasks exist
        help='Reference to the originating budget segment',
    )
```

```xml
<!-- Source: Context7 /websites/odoo_18_0_developer -->
<record id="project_task_form_inherit_segment" model="ir.ui.view">
    <field name="name">project.task.form.inherit.segment</field>
    <field name="model">project.task</field>
    <field name="inherit_id" ref="project.view_task_form2"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='project_id']" position="after">
            <field name="segment_id"
                   invisible="not project_id or not project_id.sale_order_id"
                   domain="[('order_id', '=', project_id.sale_order_id)]"/>
        </xpath>
    </field>
</record>
```

### Pattern 2: Cross-Model Validation with ValidationError

**What:** Validate that related records belong to the same parent using @api.constrains
**When to use:** When referential integrity needs enforcement beyond database foreign keys
**Example:**
```python
# Source: Context7 /websites/odoo_18_0_developer
from odoo import models, api
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.constrains('segment_id', 'project_id')
    def _check_segment_order(self):
        """Validate segment belongs to task's project sale order."""
        for task in self:
            if task.segment_id and task.project_id.sale_order_id:
                if task.segment_id.order_id != task.project_id.sale_order_id:
                    raise ValidationError(
                        'Warning: Segment "%s" does not belong to this project\'s sale order. '
                        'This may cause inconsistencies. Click OK to proceed anyway.'
                        % task.segment_id.name
                    )
```

### Pattern 3: Prevent Deletion with Related Records

**What:** Block deletion of parent records when child records exist
**When to use:** When data integrity requires parent records to remain if referenced
**Example:**
```python
# Source: Context7 /websites/odoo_18_0_developer
from odoo import models, api
from odoo.exceptions import UserError

class SaleOrderSegment(models.Model):
    _inherit = 'sale.order.segment'

    @api.ondelete(at_uninstall=False)
    def _unlink_if_no_tasks(self):
        """Prevent deletion if tasks reference this segment."""
        if self.env['project.task'].search([('segment_id', 'in', self.ids)]):
            raise UserError(
                'Cannot delete segment(s) with linked project tasks. '
                'Remove task references first.'
            )
```

### Pattern 4: Security Through Many2one Inheritance

**What:** Automatically inherit access rights from parent model via Many2one relationship
**When to use:** When child records should respect parent record access permissions
**Example:**
```python
# Source: Context7 /websites/odoo_18_0_developer + WebSearch results
# In project_task.py - No explicit code needed!
# Odoo automatically restricts task visibility if user cannot see the segment_id
# This is built-in behavior for Many2one fields

# Security is defined in ir.model.access.csv (already exists from Phase 1/2):
# access_sale_order_segment_user,sale.order.segment user,model_sale_order_segment,sales_team.group_sale_salesman,1,1,1,0
# access_sale_order_segment_manager,sale.order.segment manager,model_sale_order_segment,sales_team.group_sale_manager,1,1,1,1

# Tasks automatically inherit these restrictions via segment_id field
```

### Pattern 5: Readonly Field Based on Ownership

**What:** Make fields editable only for specific user groups using record rules
**When to use:** When Sales Users should see but not edit records owned by others
**Example:**
```xml
<!-- Source: Context7 /websites/odoo_18_0_developer -->
<record id="project_task_readonly_non_owner" model="ir.rule">
    <field name="name">Tasks: Sales Users can only edit their own</field>
    <field name="model_id" ref="project.model_project_task"/>
    <field name="groups" eval="[(4, ref('sales_team.group_sale_salesman'))]"/>
    <field name="perm_read" eval="1"/>
    <field name="perm_write" eval="1"/>
    <field name="perm_create" eval="1"/>
    <field name="perm_unlink" eval="0"/>
    <field name="domain_force">[
        '|',
        ('segment_id.order_id.user_id', '=', user.id),
        ('segment_id', '=', False)
    ]</field>
</record>
```

### Anti-Patterns to Avoid

- **Using readonly attribute for security**: The readonly XML attribute only provides UI-level restriction, not server-side security. Always use record rules for access control.
- **Mixing ValidationError and UserError semantics**: Use ValidationError for data validation issues (field values, constraints) and UserError for business logic restrictions (permissions, workflow rules). Don't interchange them.
- **Direct file editing without constraints**: Never rely on client-side validation alone. Always implement @api.constrains for data integrity.
- **Ignoring ondelete behavior**: Always specify ondelete='restrict' or ondelete='cascade' explicitly on Many2one fields to prevent orphaned records or unexpected cascading deletes.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-model validation | Manual checks in create/write | @api.constrains decorator | Automatically triggers on field changes, handles recordsets, cleaner error handling |
| Circular reference detection | Custom recursion check | _has_cycle() method (Odoo 18) | Built-in method specifically for parent_id hierarchies, more reliable |
| Company-based access control | Custom permission logic | _check_company_auto + check_company=True | Standard Odoo multi-company pattern, automatic validation |
| Modal warning dialogs | JavaScript custom dialogs | ValidationError/UserError exceptions | Server-side exceptions automatically render as modal dialogs in Odoo UI |
| Field visibility logic | JavaScript show/hide | invisible attribute in XML | Declarative, evaluated server-side, no custom JS needed |
| Record-level permissions | Custom access methods | ir.rule (record rules) | Standard Odoo security layer, respects ORM access checks |
| Deletion constraints | Override unlink() manually | @api.ondelete decorator | Cleaner, respects at_uninstall flag, standard pattern |

**Key insight:** Odoo's ORM and security framework are mature and comprehensive. Custom validation or access control logic should only be written when the built-in mechanisms are insufficient. The decorators (@api.constrains, @api.ondelete) and XML attributes (invisible, domain) handle 90% of common scenarios declaratively.

## Common Pitfalls

### Pitfall 1: ValidationError Modal Not Actually Blocking

**What goes wrong:** Developer implements ValidationError expecting a confirmation dialog, but it just blocks the action entirely
**Why it happens:** ValidationError is designed to prevent invalid data, not to prompt for user confirmation. It's a hard stop, not a soft warning.
**How to avoid:** For Phase 3, use ValidationError as specified (user must fix the issue). If true "click OK to proceed" behavior is needed later, that requires a wizard (TransientModel) with explicit confirmation step.
**Warning signs:** User cannot proceed even after reading the warning message; no "OK" or "Cancel" buttons in dialog

**Resolution for Phase 3:** Based on user context, the "modal warning bloqueante (usuario debe confirmar OK para continuar)" means the user must acknowledge and fix the issue before continuing. This is exactly what ValidationError does. The wording "Click OK to proceed anyway" should be removed from the error message, as ValidationError does not allow proceeding.

**Corrected implementation:**
```python
raise ValidationError(
    'Segment "%s" does not belong to this project\'s sale order. '
    'Please select a segment from the correct sale order.'
    % task.segment_id.name
)
```

### Pitfall 2: Invisible Field Still Allows Invalid Data

**What goes wrong:** Field is hidden with invisible attribute, but users can still set invalid values via RPC or API
**Why it happens:** invisible only controls UI visibility, not server-side validation
**How to avoid:** Always combine invisible with proper @api.constrains validation. Never rely on UI hiding for data integrity.
**Warning signs:** Invalid data appears in database despite field being hidden in form view

### Pitfall 3: ondelete='restrict' vs Constraint Timing

**What goes wrong:** ondelete='restrict' on Many2one prevents deletion at database level, but Python constraint might not run in time
**Why it happens:** Database constraints run during SQL execution, while Python constraints run during ORM operations
**How to avoid:** For Phase 3, use both: ondelete='restrict' on segment_id field (prevents orphaned tasks) and @api.ondelete on segment model (provides better error message)
**Warning signs:** Generic Odoo error messages about foreign key violations instead of user-friendly messages

### Pitfall 4: Domain vs Invisible Confusion

**What goes wrong:** Developer uses domain to hide fields instead of invisible, or vice versa
**Why it happens:** Both filter what users see, but serve different purposes
**How to avoid:**
- Use **invisible** to conditionally hide entire fields/groups from view
- Use **domain** to filter available choices in Many2one/Many2many dropdowns
- For segment_id field: use BOTH (invisible when no sale_order_id, domain to filter segments)
**Warning signs:** Field shows but with no selectable options, or field shows options from wrong context

### Pitfall 5: Security Rule Scope Creep

**What goes wrong:** Record rules become overly complex trying to handle all edge cases
**Why it happens:** Trying to implement read-only behavior through record rules gets complicated
**How to avoid:** For Phase 3, the user decision specifies "herencia de permisos vía relaciones" - let Odoo's Many2one automatic access control handle most security. Only add explicit record rules if testing reveals gaps.
**Warning signs:** Record rules with multiple OR conditions and nested domain logic

### Pitfall 6: Blocking sale_order_id Change Without Considering Empty Case

**What goes wrong:** Validation prevents changing sale_order_id even when segment_id is empty
**Why it happens:** Constraint checks for tasks with segment_id but doesn't handle NULL case
**How to avoid:**
```python
@api.constrains('sale_order_id')
def _check_sale_order_change(self):
    """Prevent changing sale_order_id if tasks with segment_id exist."""
    for project in self:
        if project.sale_order_id:
            # Only check if there are tasks WITH segment_id (not null)
            task_count = self.env['project.task'].search_count([
                ('project_id', '=', project.id),
                ('segment_id', '!=', False)
            ])
            if task_count > 0:
                raise ValidationError(
                    'Cannot change sale order when project has tasks '
                    'linked to budget segments.'
                )
```
**Warning signs:** Users cannot change sale_order_id on projects even when no segment-linked tasks exist

## Code Examples

Verified patterns from official sources:

### Complete Field Extension Pattern
```python
# Source: Context7 /websites/odoo_18_0_developer
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    segment_id = fields.Many2one(
        'sale.order.segment',
        string='Budget Segment',
        index=True,
        ondelete='restrict',
        help='Reference to the originating budget segment. '
             'Only visible for projects linked to sale orders.',
    )

    @api.constrains('segment_id', 'project_id')
    def _check_segment_order(self):
        """Validate segment belongs to project's sale order."""
        for task in self:
            if not task.segment_id or not task.project_id.sale_order_id:
                continue

            if task.segment_id.order_id != task.project_id.sale_order_id:
                raise ValidationError(
                    'Segment "%s" does not belong to this project\'s sale order. '
                    'Please select a segment from sale order: %s'
                    % (task.segment_id.name, task.project_id.sale_order_id.name)
                )
```

### Segment Deletion Protection
```python
# Source: Context7 /websites/odoo_18_0_developer
from odoo import models, api
from odoo.exceptions import UserError

class SaleOrderSegment(models.Model):
    _inherit = 'sale.order.segment'

    @api.ondelete(at_uninstall=False)
    def _unlink_if_no_tasks(self):
        """Prevent deletion if project tasks reference this segment."""
        if self.env['project.task'].search_count([('segment_id', 'in', self.ids)]) > 0:
            raise UserError(
                'Cannot delete segment(s) because they are referenced by project tasks. '
                'Remove the segment reference from tasks first, or delete the tasks.'
            )
```

### View Inheritance with Conditional Visibility
```xml
<!-- Source: Context7 /websites/odoo_18_0_developer -->
<record id="project_task_form_inherit_segment" model="ir.ui.view">
    <field name="name">project.task.form.inherit.segment</field>
    <field name="model">project.task</field>
    <field name="inherit_id" ref="project.view_task_form2"/>
    <field name="arch" type="xml">
        <!-- Add segment_id field near project_id in main section -->
        <xpath expr="//field[@name='project_id']" position="after">
            <field name="segment_id"
                   string="Budget Segment"
                   invisible="not project_id or not project_id.sale_order_id"
                   domain="[('order_id', '=', project_id.sale_order_id)]"
                   context="{'default_order_id': project_id.sale_order_id}"
                   options="{'no_create': True, 'no_open': True}"/>
        </xpath>
    </field>
</record>
```

### Project Sale Order Change Constraint
```python
# Source: Context7 /websites/odoo_18_0_developer + Phase 3 requirements
from odoo import models, api
from odoo.exceptions import ValidationError

class Project(models.Model):
    _inherit = 'project.project'

    @api.constrains('sale_order_id')
    def _check_sale_order_change_with_segments(self):
        """Prevent changing sale_order_id if tasks have segment references."""
        for project in self:
            if not project.sale_order_id:
                continue  # Clearing sale_order_id is always allowed

            # Check if any tasks have segment_id set
            task_with_segment = self.env['project.task'].search_count([
                ('project_id', '=', project.id),
                ('segment_id', '!=', False)
            ], limit=1)

            if task_with_segment > 0:
                raise ValidationError(
                    'Cannot change the sale order for project "%s" because '
                    'it contains tasks linked to budget segments. '
                    'Remove segment references from tasks first.'
                    % project.name
                )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| @api.one decorator | Direct recordset iteration | Odoo 11+ | @api.one is deprecated; use `for record in self:` pattern |
| _check_recursion() | _has_cycle() | Odoo 18 | New method name for circular reference detection in hierarchies |
| attrs={'invisible': [()]} | invisible="condition" | Odoo 14+ | Simpler Python expression syntax instead of domain tuples |
| Manual company checks | _check_company_auto | Odoo 13+ | Automatic multi-company validation with less boilerplate |

**Deprecated/outdated:**
- **@api.multi and @api.one decorators**: Removed in Odoo 13. All methods now work with recordsets by default.
- **old-style domains in XML attributes**: attrs={'invisible': [('field', '=', False)]} is legacy, use invisible="not field" instead
- **_check_recursion()**: Renamed to _has_cycle() in Odoo 18 for parent_id circular reference detection

## Open Questions

Things that couldn't be fully resolved:

1. **Display format for segment_id in task form**
   - What we know: User wants "Nombre + orden" format (e.g., "SO001 / Implantación PaP")
   - What's unclear: Whether this requires a custom name_get() override or display_name computed field on sale.order.segment
   - Recommendation: Test default Many2one display first. If it shows segment.name only, add display_name computed field combining order + name

2. **Exact behavior when user confirms validation warning**
   - What we know: User wants "modal warning bloqueante" where user confirms to proceed
   - What's unclear: ValidationError does NOT allow proceeding; it blocks. True confirmation requires wizard (TransientModel)
   - Recommendation: Use ValidationError as pure block for Phase 3 (user must fix). If "click OK to continue anyway" is truly required, defer to Phase 4 or separate enhancement as it requires wizard implementation

3. **Project tree/list view segment_id column**
   - What we know: segment_id should be visible in task form
   - What's unclear: Whether it should also appear in task list/kanban views for projects linked to sale orders
   - Recommendation: Add to form view only for Phase 3. Evaluate list/kanban visibility based on user testing feedback

4. **Handling of archived segments**
   - What we know: segment model has active field (from Phase 1/2 code)
   - What's unclear: Should tasks be able to reference archived segments? Should segment_id domain filter active=True?
   - Recommendation: Add domain="[('order_id', '=', project_id.sale_order_id), ('active', '=', True)]" to prevent selecting archived segments for new tasks. Existing tasks keep their references.

## Sources

### Primary (HIGH confidence)
- [Context7: Odoo 18.0 Developer Documentation](/websites/odoo_18_0_developer) - Many2one fields, constraints, security, view inheritance
  - Topics: field relationships, validation patterns, security model, conditional visibility
- [Odoo 18.0 Official Documentation - Multi-company Guidelines](https://www.odoo.com/documentation/18.0/developer/howtos/company.html) - check_company pattern
- [Odoo 18.0 Official Documentation - Error Handling](https://www.odoo.com/documentation/18.0/developer/reference/frontend/error_handling.html) - Exception types and behavior
- [Odoo 18.0 Official Documentation - Security](https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html) - Access rights and record rules

### Secondary (MEDIUM confidence)
- [Ondelete Restrict and Ondelete Cascade in Odoo](https://freewebsnippets.com/blog/ondelete-restrict-and-ondelete-cascade-in-odoo.html) - ondelete behaviors verified with official docs
- [Use ValidationError & UserError in Odoo](https://www.devintellecs.com/blog/odoo-technical-4/how-to-use-validationerror-and-usererror-in-odoo-124) - Exception semantic differences verified with official docs
- [Cybrosys: Dynamic Domain for Relational Fields in Odoo 18](https://www.cybrosys.com/blog/how-to-apply-dynamic-domain-for-relational-fields-in-odoo-18) - Domain patterns verified with Context7

### Tertiary (LOW confidence)
- Multiple Odoo forum discussions on Many2one ondelete, record rules, and field domains (used only to identify common questions, verified answers with official docs)
- Note: WebSearch results about "automatic permission inheritance from parent model" found LIMITED support - Odoo does NOT automatically inherit full CRUD permissions from Many2one parent. Access is restricted (user cannot see task if cannot see segment), but explicit permissions still needed.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All features are documented in official Odoo 18 docs and Context7
- Architecture: HIGH - Patterns extracted directly from Context7 code examples and official documentation
- Pitfalls: MEDIUM-HIGH - Based on Context7 docs and validated patterns, plus one correction needed for ValidationError behavior
- Security inheritance: MEDIUM - WebSearch revealed Odoo does NOT fully inherit parent permissions automatically, only enforces visibility restriction

**Research date:** 2026-02-05
**Valid until:** 2026-04-05 (60 days - Odoo has stable release cycle, 18.0 patterns unlikely to change)

**Phase-specific notes:**
- User decisions from CONTEXT.md have been incorporated as constraints
- ValidationError vs confirmation wizard clarification is critical for implementation
- Security approach relies on implicit Many2one access restriction + existing Phase 1/2 ir.model.access.csv rules
- No new security groups needed; Sales User vs Sales Manager distinction already exists
