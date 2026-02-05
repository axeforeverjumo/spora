# Stack Research

**Domain:** Custom Odoo 18 Module Development
**Researched:** 2026-02-05
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Odoo | 18.0 | ERP Framework | Required base platform. Provides ORM, workflow engine, UI framework, and all standard modules (sale, project). Official release with LTS support. |
| Python | 3.10+ | Backend Language | **Minimum version 3.10 required** by Odoo 18. Python 3.11-3.13 also supported. Odoo 18 uses features introduced in Python 3.10+, making 3.7-3.9 incompatible. |
| PostgreSQL | 15.x | Database | **PostgreSQL 15 highly recommended** for Odoo 18. Versions 12.0+ supported, but 15 provides optimal performance and compatibility. PostgreSQL 16 works but PostgreSQL 18 not yet supported. |
| Docker | 24.0+ | Containerization | Standard for Odoo 18 development. Provides environment consistency, zero local dependencies, and simplified deployment. Official Odoo 18 Docker images available. |

### Odoo Framework Components

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| Odoo ORM API | 18.0 | Data Layer | **Always use instead of raw SQL**. Provides safe database operations, recordsets, computed fields, constraints, and automatic transactions. Core of all model development. |
| OWL 2 | 18.0 | Frontend Framework | JavaScript UI framework for reactive components. Required for custom web interfaces. Component-based architecture with React/Vue-like patterns. |
| QWeb | 18.0 | Template Engine | XML-based templating for views and reports. Standard for all UI definitions (tree, form, search views). |
| Automated Actions | 18.0 | Workflow Automation | Built-in system for triggering actions on record changes. Use for order confirmation workflows instead of custom code. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pylint-odoo | Python Linting | **OCA-maintained linting tool** specifically for Odoo. Enforces Odoo-specific coding standards beyond PEP8. Install via `pip install pylint-odoo`. |
| ruff | Fast Linting/Formatting | **10-100x faster than Flake8**. Can replace Flake8, Black, isort, pyupgrade. Use `ruff-odoo` variant for Odoo-specific rules. |
| pytest-odoo | Testing | Enables running Odoo's unittest-based tests with pytest CLI. Better for TDD workflows. Install: `pip install pytest-odoo`. |
| ESLint | JavaScript Linting | Standard JavaScript linter for OWL components and web client code. |

### Supporting Libraries (Odoo Built-ins)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg2 | 2.9.2-2.9.10 | PostgreSQL Adapter | **Included in Odoo**. No explicit install needed. Python-PostgreSQL interface. |
| lxml | 4.8.0-5.2.1 | XML Processing | **Included in Odoo**. Required for view inheritance, XPath operations. |
| Werkzeug | 2.0.2-3.0.1 | WSGI Toolkit | **Included in Odoo**. Web server interface. |
| Babel | 2.9.1-2.17.0 | Internationalization | **Included in Odoo**. Translation support. |

## Installation

### Docker Compose Setup (Recommended)

```bash
# Create project structure
mkdir -p custom_addons
touch docker-compose.yml .env odoo.conf

# docker-compose.yml
version: '3.8'
services:
  web:
    image: odoo:18.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - ./custom_addons:/mnt/extra-addons
      - ./odoo.conf:/etc/odoo/odoo.conf
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
    volumes:
      - odoo-db-data:/var/lib/postgresql/data

volumes:
  odoo-db-data:

# Launch
docker-compose up -d
```

### Development Tools

```bash
# Install linting/testing tools
pip install pylint-odoo
pip install ruff
pip install pytest-odoo

# Optional: Install ruff-odoo for Odoo-specific rules
pip install ruff-odoo
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PostgreSQL 15 | PostgreSQL 16 | Works with Odoo 18 but not as tested. Use only if infrastructure requires it. |
| Docker | Direct Installation | Only for production servers where Docker overhead is unacceptable. Never for development. |
| Odoo ORM | Raw SQL | **Only for complex queries** with proven performance issues. Always try ORM first (search, read, write methods). |
| OWL 2 | jQuery/Legacy JS | **Never use**. jQuery approach deprecated in Odoo 18. All new UI should use OWL components. |
| Automated Actions | Custom Python Triggers | Use automated actions for simple workflows (send email, update field). Use Python only for complex business logic. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Python 3.7-3.9 | **Not supported by Odoo 18**. Odoo 18 requires Python 3.10+ for new language features and performance. | Python 3.10, 3.11, or 3.13 |
| PostgreSQL 18 | **Not yet supported** as of early 2026. Known compatibility issues reported. | PostgreSQL 15 (recommended) or 16 |
| `@api.one`, `@api.multi` | **Deprecated decorators**. Removed in modern Odoo. Old API pattern. | Use recordset methods directly. No decorator needed. |
| `name_get()` | **Deprecated in Odoo 18**. Method being phased out. | Use `display_name` field instead |
| `_sequence` attribute | **Removed in Odoo 18**. PostgreSQL handles primary key sequences automatically. | Remove from models. Let PostgreSQL manage. |
| Direct core module modification | **Breaks upgrades**. Makes system unmaintainable. | Use inheritance (`_inherit`, `inherit_id`) to extend modules |
| Raw SQL queries | **Bypasses ORM safety**. Breaks abstraction, security, and caching. | Use ORM: `search()`, `read()`, `write()`, `create()` |
| Monolithic modules | **Creates technical debt**. One module doing everything is hard to maintain. | Create focused modules solving single business problems |

## Stack Patterns by Use Case

### If building hierarchical models (like segments):

- Use **`parent_id` Many2one** field referencing same model
- Set **`_parent_store = True`** for performance
- Adds indexed `parent_path` field automatically
- Enables fast `child_of` and `parent_of` domain operators
- Use **tree view** with `parent_id` in XML for UI

### If extending sale.order:

- Use **model inheritance** with `_inherit = 'sale.order'`
- Add custom fields directly to inherited class
- Use **view inheritance** with `inherit_id` in XML
- Use **XPath** to position new fields: `position="after"`, `position="inside"`, etc.
- Always call `super()` when overriding methods

### If extending project.task:

- Same inheritance pattern as sale.order
- Use **computed fields** with `@api.depends()` decorator
- Use **onchange methods** with `@api.onchange()` for form reactivity
- Use **constraints** with `@api.constrains()` for validation

### If triggering actions on order confirmation:

- Use **Automated Actions** (Settings → Technical → Automated Actions)
- Trigger type: "On Update" when state changes to 'sale'
- Action: Python code or create records
- Alternative: Override `action_confirm()` method with `super()` call

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Odoo 18.0 | PostgreSQL 12.0-16 | PostgreSQL 15 recommended, 18 not supported |
| Odoo 18.0 | Python 3.10-3.13 | Python 3.10 minimum required |
| psycopg2 2.9.2-2.9.10 | PostgreSQL 15 | Version varies by Python version |
| lxml 4.8.0-5.2.1 | Python 3.10-3.13 | Version varies by Python version |
| OWL 2 | Odoo 18.0+ | Component-based framework, replaces jQuery patterns |

## Module Structure

```
custom_module/
├── __init__.py              # Python package initialization
├── __manifest__.py          # Module metadata and dependencies
├── models/                  # Python model definitions
│   ├── __init__.py
│   ├── segment.py          # Custom models
│   ├── sale_order.py       # sale.order extension
│   └── project_task.py     # project.task extension
├── views/                   # XML view definitions
│   ├── segment_views.xml   # Tree, form, search views
│   ├── sale_order_views.xml # View inheritance
│   └── project_task_views.xml
├── data/                    # Data files (automated actions, etc.)
│   └── automated_actions.xml
├── security/                # Access control
│   ├── ir.model.access.csv  # Model permissions
│   └── security.xml         # Record rules
├── static/                  # Web assets
│   ├── src/
│   │   ├── js/             # OWL components
│   │   └── scss/           # Styles
│   └── description/        # Module icon and description
└── tests/                   # Unit tests
    ├── __init__.py
    └── test_segment.py
```

## Key Dependencies in __manifest__.py

```python
{
    'name': 'Custom Module Name',
    'version': '18.0.1.0.0',
    'category': 'Sales/Project',
    'depends': [
        'sale_management',     # For sale.order extension
        'project',             # For project.task extension
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/segment_views.xml',
        'views/sale_order_views.xml',
        'views/project_task_views.xml',
        'data/automated_actions.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

## Sources

**HIGH Confidence (Official Documentation):**
- [Odoo 18.0 Source Install](https://www.odoo.com/documentation/18.0/administration/on_premise/source.html) - Python and PostgreSQL requirements
- [Odoo 18.0 ORM API](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html) - ORM patterns and decorators
- [Odoo 18.0 Module Manifests](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html) - __manifest__.py structure
- [Odoo 18.0 Testing](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html) - Testing framework
- [Odoo 18.0 Coding Guidelines](https://www.odoo.com/documentation/18.0/contributing/development/coding_guidelines.html) - Code standards
- [Odoo 18.0 OWL Components](https://www.odoo.com/documentation/18.0/developer/tutorials/discover_js_framework/01_owl_components.html) - Frontend framework
- [Odoo 18.0 Inheritance Tutorial](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/12_inheritance.html) - Model and view inheritance
- [Odoo 18.0 Automated Actions](https://www.odoo.com/documentation/18.0/applications/studio/automated_actions.html) - Workflow automation
- [Odoo 18.0 Changelog](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm/changelog.html) - Deprecated features
- [Odoo GitHub requirements.txt](https://github.com/odoo/odoo/blob/18.0/requirements.txt) - Python dependencies

**MEDIUM Confidence (Community/Verified):**
- [OCA pylint-odoo](https://github.com/OCA/pylint-odoo) - Linting tool
- [pytest-odoo](https://github.com/camptocamp/pytest-odoo) - Testing plugin
- [Odoo 18 Docker Compose Guide](https://dev.to/treekon_ventures/streamlined-odoo-18-development-with-docker-compose-a-developers-guide-4ph1) - Docker setup
- [Python Version for Odoo 18](https://www.webbycrown.com/python-version-for-odoo-18/) - Python requirements
- [Odoo 18 OWL Improvements](https://pysquad.com/blogs/odoo-18-owl-js-key-improvements-over-odoo-17) - OWL 2 features
- [Odoo Development Best Practices](https://nerithonx.com/blog/odoo-development-best-practices/) - Best practices guide
- [Odoo Customization Mistakes](https://silentinfotech.com/blog/odoo-1/8-mistakes-to-avoid-in-odoo-erp-customization-211) - Anti-patterns

---
*Stack research for: Custom Odoo 18 Module Development*
*Researched: 2026-02-05*
