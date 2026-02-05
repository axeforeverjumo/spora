# Pitfalls Research: Odoo Custom Module Development

**Domain:** Odoo ERP Custom Module Development
**Researched:** 2026-02-05
**Confidence:** MEDIUM

Focus areas: Hierarchical models with parent_id, computed fields with store=True, extending sale.order.line, automated task creation, tree views, and integration with standard workflows.

## Critical Pitfalls

### Pitfall 1: Missing _parent_store for Hierarchical Models

**What goes wrong:**
When using parent_id for hierarchical relationships without enabling _parent_store, database queries become recursive and exponentially slower as the tree depth increases. With 100+ records at 5+ levels deep, queries can take 10+ seconds, causing UI timeouts.

**Why it happens:**
Developers assume Odoo handles hierarchy optimization automatically. The framework provides parent_id relationships by default, but performance optimization requires explicit configuration.

**How to avoid:**
Always set `_parent_store = True` on models with parent_id relationships and add the parent_path field with index=True:

```python
class MyHierarchicalModel(models.Model):
    _name = 'my.hierarchical.model'
    _parent_store = True
    _parent_name = 'parent_id'  # Optional, defaults to 'parent_id'

    parent_id = fields.Many2one('my.hierarchical.model', string='Parent', index=True)
    parent_path = fields.Char(index=True)  # Auto-computed by _parent_store
    child_ids = fields.One2many('my.hierarchical.model', 'parent_id', string='Children')
```

**Warning signs:**
- Slow loading of tree views (>2 seconds)
- Database query logs show recursive CTEs
- child_of or parent_of domain operators take >1 second
- PostgreSQL query planner shows sequential scans on large tables

**Phase to address:**
Phase 1: Model Definition - Set up _parent_store from the beginning. Retrofitting is complex because it requires data migration.

**Sources:**
- [Odoo _parent_store documentation](https://www.odoo.com/forum/help-1/what-is-parent-store-214936) - MEDIUM confidence
- [Hierarchical Models in Odoo](https://www.hynsys.com/blog/odoo-development-5/hierarchical-models-in-odoo-6) - MEDIUM confidence

---

### Pitfall 2: Incomplete @api.depends Declarations for Computed Fields

**What goes wrong:**
Stored computed fields (store=True) don't recompute when dependent data changes. Users see stale data, reports show incorrect values, and the only fix is manually triggering recomputation or reinstalling the module.

**Why it happens:**
Developers forget to declare all dependencies, especially:
- Related fields through many2one relationships
- Fields on related models (dotted paths)
- Non-stored computed fields that feed into stored fields
- Dependencies across multiple model hops

**How to avoid:**
Always declare complete dependency chains using dotted notation:

```python
@api.depends('line_ids.product_id.weight', 'line_ids.quantity')
def _compute_total_weight(self):
    for record in self:
        record.total_weight = sum(
            line.product_id.weight * line.quantity
            for line in record.line_ids
        )
```

**Critical rules:**
1. For store=True fields, ALWAYS use @api.depends
2. Trace dependencies through many2one relationships using dots
3. If depending on computed fields, ensure they also have complete @api.depends
4. Test by modifying each dependent field and verifying recomputation

**Warning signs:**
- Computed field shows correct value on create but not on update
- Changing related record doesn't update computed field
- Need to manually trigger "Recompute" action
- Inconsistent values between form view and list view

**Phase to address:**
Phase 1: Model Definition - Define dependencies during initial field creation. Phase 3: Testing - Verify all dependency chains trigger recomputation.

**Known limitation:**
A stored compute field A that depends on a non-stored compute field B which has no @api.depends will NOT trigger recomputation when B's data changes (Odoo v12-v14 documented issue).

**Sources:**
- [Odoo Computed Fields Documentation](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/08_compute_onchange.html) - HIGH confidence
- [GitHub Issue #37468: Non-stored compute field dependencies](https://github.com/odoo/odoo/issues/37468) - HIGH confidence

---

### Pitfall 3: Breaking sale.order.line Inheritance with Field Conflicts

**What goes wrong:**
Adding Many2one fields to sale.order.line causes "The line has been modified, your changes will be discarded" warnings, onchange events break, or child values duplicate on edit. The sales order becomes unusable.

**Why it happens:**
sale.order.line has complex onchange chains (product_id, price_unit, taxes, discounts) and tight coupling with sale.order. Adding fields that conflict with existing required fields or trigger competing onchange methods breaks these chains.

**How to avoid:**
1. **Never use both _name and _inherit** - only use _inherit for extensions
2. **Check for required field conflicts** - Don't make custom fields required if they compete with product_id
3. **Test onchange chains** - Verify partner_id onchange still works after adding fields
4. **Use proper inheritance syntax:**

```python
class SaleOrderLineExtension(models.Model):
    _inherit = 'sale.order.line'  # NOT _name

    custom_field = fields.Many2one('custom.model', string='Custom')
    # Avoid: required=True if it conflicts with product_id logic
```

4. **For One2many additions**, ensure inverse_name is correctly set and test edit operations thoroughly

**Warning signs:**
- "Type of related field is inconsistent" errors
- Partner changes don't update order lines
- Duplicated values in child records after saving
- Order line creation triggers validation errors

**Phase to address:**
Phase 2: Extension Development - Test sales workflow end-to-end before deploying. Phase 3: Integration Testing - Verify compatibility with sale_management, sale_stock, and other standard modules.

**Sources:**
- [Extending sale.order.line forum discussion](https://www.odoo.com/forum/help-1/extending-the-sales-order-line-not-working-as-expected-194467) - MEDIUM confidence
- [GitHub Issue #17618: One2many breaks onchange](https://github.com/odoo/odoo/issues/17618) - HIGH confidence
- [GitHub Issue #25168: Duplicate values on edit](https://github.com/odoo/odoo/issues/25168) - HIGH confidence

---

### Pitfall 4: Transaction Mismanagement in Automated Actions

**What goes wrong:**
An automated action processes 1,000 records, record #999 fails, and all 999 previous records roll back. Or worse, calling cr.commit() manually causes data corruption when subsequent operations fail.

**Why it happens:**
Odoo wraps each HTTP request in a transaction. Developers either:
- Ignore transaction boundaries and lose all work on single failure
- Manually call cr.commit() trying to "save progress" and break Odoo's transaction management

**How to avoid:**
Use savepoints for batch processing to isolate each iteration:

```python
def process_batch_with_error_isolation(self):
    for record in self.search([]):
        try:
            with self.env.cr.savepoint():  # Creates savepoint
                record.complex_operation()
                record.create_related_tasks()
                # If error occurs, only THIS iteration rolls back
        except UserError as e:
            _logger.warning(f"Failed to process {record.name}: {e}")
            # Log and continue - other records still processed
        except Exception as e:
            _logger.error(f"Unexpected error for {record.name}: {e}", exc_info=True)
            # Continue processing remaining records
```

**Critical rules:**
1. **NEVER call cr.commit()** unless you created your own cursor (rare)
2. **NEVER call cr.rollback()** - let Odoo handle it
3. **Use savepoints for batch operations** to prevent cascading failures
4. **Limit batch size** - PostgreSQL slows after 64 savepoints in one transaction
5. **Catch specific exceptions** - UserError vs ValidationError vs Exception
6. **Log failures** - track which records failed and why

**Warning signs:**
- Batch operations are all-or-nothing (1 failure = 1000 rollbacks)
- "InFailedSqlTransaction" errors
- Data corruption after partial processing
- Savepoint performance degradation (>64 in one transaction)

**Phase to address:**
Phase 2: Automated Actions - Implement savepoint strategy from the start. Phase 3: Error Handling - Add comprehensive exception catching and logging.

**Sources:**
- [Error Handling and Logging in Odoo](https://www.braincuber.com/tutorial/error-handling-logging-odoo-custom-code-production-ready-techniques) - HIGH confidence
- [Working with Savepoint blog](http://blog.odooist.com/posts/working-with-savepoint/) - MEDIUM confidence
- [Odoo Coding Guidelines](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html) - HIGH confidence

---

### Pitfall 5: Missing Access Rights Definition

**What goes wrong:**
Users get cryptic "Forbidden" errors even though views and menu items are correctly defined. Records are visible but can't be edited. Operations work for admin but fail for regular users.

**Why it happens:**
Developers test as admin (bypass ACL) and forget that every model needs explicit access rights in ir.model.access.csv. Without access rights, NO ONE except admin can access the model.

**How to avoid:**
1. **Always create ir.model.access.csv** for custom models
2. **Define access for each group** that needs model access
3. **Order security files first** in __manifest__.py data list

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_my_model_user,my.model user,model_my_model,base.group_user,1,1,1,0
access_my_model_manager,my.model manager,model_my_model,base.group_system,1,1,1,1
```

4. **Model ID format**: For model 'my.model', use 'model_my_model' (replace dots with underscores)
5. **Reference security.xml before views.xml** in manifest to avoid group reference errors

```python
'data': [
    'security/groups.xml',       # Define groups first
    'security/ir.model.access.csv',  # Then access rights
    'views/my_views.xml',        # Finally views
],
```

**Warning signs:**
- "You are not allowed to access" errors for non-admin users
- Records visible in list but can't open form
- Create button exists but raises error
- Automated actions fail with access rights errors

**Phase to address:**
Phase 1: Model Definition - Create ir.model.access.csv when defining the model. Phase 2: Security Configuration - Define granular group-based permissions. Phase 3: Testing - Test as non-admin user.

**Sources:**
- [Security in Odoo Documentation](https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html) - HIGH confidence
- [Security Access Rights forum discussion](https://www.odoo.com/forum/help-1/security-access-rights-error-for-a-custom-module-72983) - MEDIUM confidence

---

### Pitfall 6: SQL Constraint Violations on Existing Data

**What goes wrong:**
Adding a UNIQUE constraint to a field crashes module upgrade with "IntegrityError: duplicate key value violates unique constraint" because production database has duplicate values. Module can't install or upgrade.

**Why it happens:**
SQL constraints are validated against existing database data. If data violates the constraint, PostgreSQL rejects it. Module update fails and leaves the system in a broken state.

**How to avoid:**
1. **Check for duplicates BEFORE adding constraint:**

```python
# In Python shell or migration script
duplicates = self.env['my.model'].read_group(
    [],
    ['field_to_constrain'],
    ['field_to_constrain'],
    having=[('__count', '>', 1)]
)
```

2. **Use migration scripts** (pre-migrate.py) to clean data:

```python
def migrate(cr, version):
    """Clean duplicates before adding constraint"""
    cr.execute("""
        DELETE FROM my_model
        WHERE id NOT IN (
            SELECT MIN(id) FROM my_model GROUP BY field_to_constrain
        )
    """)
```

3. **Add constraints in stages:**
   - Phase 1: Add field without constraint
   - Phase 2: Clean data
   - Phase 3: Add constraint via module update

4. **Provide user-friendly error messages:**

```python
_sql_constraints = [
    ('unique_code', 'UNIQUE(code)', 'The code must be unique! Duplicate found.')
]
```

**Warning signs:**
- Module upgrade fails on production but works on dev
- psycopg2.IntegrityError during installation
- "unable to add constraint" errors in logs
- Can't install module after database has data

**Phase to address:**
Phase 1: Data Validation - Validate data model assumptions. Phase 2: Migration Strategy - Create pre-migrate scripts for production deployment. Phase 4: Deployment - Test upgrade path with production-like data.

**Sources:**
- [Odoo Constraints Documentation](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/10_constraints.html) - HIGH confidence
- [GitHub Issue #28381: SQL constraints crash](https://github.com/odoo/odoo/issues/28381) - HIGH confidence

---

### Pitfall 7: Over-Customization Breaking Upgrade Path

**What goes wrong:**
Odoo releases new version (e.g., 18.0 → 19.0) with breaking changes. Custom module that modifies core models fails to upgrade. Tax fields changed from tax_id to tax_ids, UoM fields changed from product_uom to product_uom_id. Module breaks and requires full rewrite.

**Why it happens:**
Odoo evolves rapidly with breaking API changes between major versions. Over-customization creates tight coupling with specific Odoo internals. The more you modify core behavior, the harder upgrades become.

**How to avoid:**
1. **Minimize core modifications** - use extension patterns, not modifications
2. **Follow Odoo upgrade guidelines** - check release notes for breaking changes
3. **Use stable API patterns** - prefer documented APIs over internal methods
4. **Test upgrades early** - try new Odoo version in staging before release
5. **Plan for common breaking changes:**
   - Field renames (tax_id → tax_ids)
   - Method signature changes
   - View inheritance structure changes
   - Workflow engine modifications

**Known breaking changes (18.0 → 19.0):**
- `tax_id` → `tax_ids` (many2one → many2many)
- `product_uom` → `product_uom_id` (better relational integrity)
- UoM category changes (simplified hierarchy)

**Warning signs:**
- Modifications to compute methods in core models
- Overriding entire methods instead of calling super()
- Hardcoded references to internal fields
- No test coverage for upgrade compatibility

**Phase to address:**
Phase 1: Architecture Planning - Design for upgradability from start. Phase 2: Development - Use extension patterns, minimize core touches. Phase 4: Upgrade Testing - Allocate budget for version upgrades.

**Sources:**
- [Odoo 19.0 Upgrade Documentation](https://www.odoo.com/documentation/19.0/administration/upgrade.html) - HIGH confidence
- [Odoo 18→19 Migration Guide](https://www.ksolves.com/blog/odoo/how-to-migrate-from-odoo-18-to-odoo-19-step-by-step-guide) - MEDIUM confidence
- [Upgrade Tutorial Medium](https://mehedi-khan.medium.com/upgrading-an-odoo-module-from-version-15-to-version-18-a-step-by-step-tutorial-with-example-00d2fc1bfd69) - LOW confidence

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| No @api.depends on computed fields | Faster development | Stale data, manual recomputation | Never - always use @api.depends |
| Skip ir.model.access.csv | Works for admin testing | Broken for real users | Never - create with model |
| Manual cr.commit() in loops | "Saves progress" | Data corruption, broken transactions | Only with separate cursor (rare) |
| Copy-paste core method instead of super() | Avoid parent logic | Upgrade failures, duplicate code | Never - use inheritance properly |
| No _parent_store on hierarchies | Quick prototype | 10x+ slower at scale | Flat structures only (<3 levels) |
| Duplicate code in multiple modules | Avoid shared dependency | Inconsistent behavior, hard to fix bugs | Never - create shared module |
| Store=False to avoid dependencies | Skip @api.depends complexity | Slow performance (recompute every access) | Read-only summary fields |

## Integration Gotchas

Common mistakes when extending or integrating with standard Odoo modules.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| sale.order.line extension | Using both _name and _inherit | Only use _inherit = 'sale.order.line' |
| product.product | Not testing variant handling | Test with product.template AND product.product |
| stock.move | Not handling split/merge operations | Override _prepare_move_split_vals |
| account.move.line | Breaking reconciliation logic | Call super() and preserve reconcile_model_id |
| project.task | Breaking stage_id transitions | Use write() instead of direct SQL updates |
| res.partner | Ignoring parent_id company relationships | Test with parent companies and contacts |
| mail.thread | Not calling message_post correctly | Use _message_log for system notes vs user messages |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No _parent_store on hierarchies | Tree views slow | Set _parent_store = True | >100 records, >3 levels |
| search([]) in loops | Each loop hits database | search_fetch() or read_group() | >100 iterations |
| Stored computed without proper depends | Need manual recomputation | Complete @api.depends chains | Production data changes |
| >64 savepoints in transaction | PostgreSQL slowdown | Batch size limits, scheduled jobs | >64 records processed |
| Computed fields with store=False in list views | Every page load recomputes all | store=True with dependencies | >500 records in view |
| ORM write() in loops | N+1 query problem | Batch write() with recordsets | >50 updates |
| SQL queries without indexes | Sequential scans | Add indexes to foreign keys, search fields | >10k records in table |
| Related fields without delegate | Extra JOINs on every access | Use delegate=True or compute with store | >1000 related accesses |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| No ir.model.access.csv | All users blocked except admin | Create access rights with model |
| Group references before definition | Installation fails | Order: groups.xml → ir.model.access.csv → views |
| Public methods without ACL checks | Privilege escalation via RPC | Add @api.model decorator, check user permissions |
| SQL queries with user input | SQL injection | Use parameterized queries: cr.execute(query, params) |
| Record rules on wrong model | Data leak across companies | Test with multi-company setup |
| Sudo() without context check | Bypass all security | Only use sudo() when absolutely necessary |
| Password fields without encrypted=True | Plaintext passwords in database | Use fields.Char(encrypted=True) for sensitive data |

## UX Pitfalls

Common user experience mistakes in Odoo custom modules.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No default view order | Random record order | Add _order = 'name' to model |
| Long computed field operations in form view | 5+ second form load | Use store=True or background job |
| No onchange feedback | Save fails with validation error | Add @api.onchange with warning message |
| Tree view without search filters | Users can't find records | Add search_default filters in search view |
| No status bar for workflow | Users don't know current state | Add statusbar_visible to state field |
| Many2one without name_search override | Can't search by useful fields | Override name_search to add search fields |
| Form view with 50+ fields | Overwhelming interface | Use notebook (tabs) to organize fields |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Computed fields**: Tested that modifying each @api.depends field triggers recomputation
- [ ] **Hierarchical models**: Verified _parent_store is enabled and parent_path field exists
- [ ] **Access rights**: Tested as non-admin user in each group
- [ ] **sale.order.line extension**: Tested partner_id onchange still works after customization
- [ ] **Automated actions**: Verified error in one record doesn't rollback others (savepoint test)
- [ ] **SQL constraints**: Checked production database has no existing violations
- [ ] **Onchange methods**: Tested that required fields are properly set before save
- [ ] **Tree views with parent_id**: Tested with 100+ records at 5+ levels depth
- [ ] **Many2one fields**: Verified name_search finds records by all relevant fields
- [ ] **Computed with store=True**: Confirmed field shows in database table (not just in view)
- [ ] **Module upgrade**: Tested upgrade path from previous version with real data
- [ ] **Multi-company**: Tested with company-specific record rules enabled

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Missing @api.depends | LOW | Add depends, click "Update Module List", manual recompute if needed |
| No _parent_store | MEDIUM | Add _parent_store=True, run migration script to populate parent_path |
| Missing ir.model.access | LOW | Create CSV file, add to manifest, update module |
| Broken sale.order.line | HIGH | May need to remove field, clean data, re-add with correct structure |
| Transaction commit() called | HIGH | Refactor to use savepoints, extensive testing required |
| SQL constraint on dirty data | MEDIUM | Write pre-migrate script to clean data, then add constraint |
| No savepoints in batch | MEDIUM | Add savepoint wrapper, test with intentional failures |
| Over-customization blocks upgrade | HIGH | Refactor to use inheritance, may require partial rewrite |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Missing _parent_store | Phase 1: Model Definition | Load test with 500+ records at 5 levels |
| Incomplete @api.depends | Phase 1: Model Definition | Modify each dependency, verify recomputation |
| sale.order.line conflicts | Phase 2: Extension Development | Test complete sales workflow including invoicing |
| No transaction isolation | Phase 2: Automated Actions | Test batch processing with intentional error at record 50/100 |
| Missing access rights | Phase 1: Security Setup | Login as non-admin user, attempt all CRUD operations |
| SQL constraint violations | Phase 4: Deployment | Run constraint check query on production copy before migration |
| Upgrade compatibility | Phase 1: Architecture Planning | Document Odoo version, test upgrade path in Phase 4 |
| Performance with scale | Phase 3: Load Testing | Test with 10x expected production data volume |

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Hierarchical model creation | Forgetting _parent_store | Add _parent_store=True in model definition, create parent_path field |
| Computed field definition | Missing @api.depends | Document all dependencies before coding, review with checklist |
| Extending sale.order.line | Using _name with _inherit | Code review: verify only _inherit is used, test onchange behavior |
| Creating automated actions | No error isolation | Implement savepoint pattern from start, test with failures |
| Defining SQL constraints | Production has existing violations | Always check data before adding constraint, write migration script |
| Tree view implementation | No performance optimization | Enable _parent_store, test with large datasets (500+ records) |
| Access rights definition | Ordering security files wrong | Put security files first in manifest data list |
| Module upgrade | Breaking changes in new Odoo version | Check release notes, test upgrade in staging before production |

## Sources

### High Confidence (Official Documentation & Verified Issues)
- [Odoo 19.0 Computed Fields Documentation](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/08_compute_onchange.html)
- [Odoo 19.0 Security Documentation](https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html)
- [Odoo 19.0 Coding Guidelines](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html)
- [Odoo 19.0 Constraints Documentation](https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/10_constraints.html)
- [GitHub Issue #37468: Non-stored compute dependencies](https://github.com/odoo/odoo/issues/37468)
- [GitHub Issue #17618: One2many breaks onchange](https://github.com/odoo/odoo/issues/17618)
- [GitHub Issue #25168: Duplicate values on edit](https://github.com/odoo/odoo/issues/25168)
- [GitHub Issue #28381: SQL constraints crash](https://github.com/odoo/odoo/issues/28381)

### Medium Confidence (Community Resources & Forum Discussions)
- [Error Handling and Logging in Odoo Custom Code](https://www.braincuber.com/tutorial/error-handling-logging-odoo-custom-code-production-ready-techniques)
- [Hierarchical Models in Odoo](https://www.hynsys.com/blog/odoo-development-5/hierarchical-models-in-odoo-6)
- [What is _parent_store? Forum Discussion](https://www.odoo.com/forum/help-1/what-is-parent-store-214936)
- [Working with Savepoint Blog](http://blog.odooist.com/posts/working-with-savepoint/)
- [Extending sale.order.line Forum](https://www.odoo.com/forum/help-1/extending-the-sales-order-line-not-working-as-expected-194467)
- [Security Access Rights Forum](https://www.odoo.com/forum/help-1/security-access-rights-error-for-a-custom-module-72983)
- [Odoo Customization Mistakes Guide](https://silentinfotech.com/blog/odoo-1/8-mistakes-to-avoid-in-odoo-erp-customization-211)
- [How to Migrate Odoo 18 to 19](https://www.ksolves.com/blog/odoo/how-to-migrate-from-odoo-18-to-odoo-19-step-by-step-guide)

### Low Confidence (Unverified or Single-Source)
- [Odoo Development Best Practices](https://nerithonx.com/blog/odoo-development-best-practices/)
- [Master Custom Module Development](https://moldstud.com/articles/p-master-custom-module-development-in-odoo-for-success)

---
*Pitfalls research for: Odoo Custom Module Development*
*Researched: 2026-02-05*
*Focus: Hierarchical data, computed fields, sale.order.line extension, automated actions, performance optimization*
