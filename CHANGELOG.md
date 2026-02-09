# Changelog

All notable changes to the Spora project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-09

### Added

#### Task Creation System
- **Individual product subtasks**: Each product in a segment now creates its own task automatically
  - One task per `sale.order.line` in segment
  - Allocated hours pulled from product quantity
  - Product description included in task description
  - Linked to sale line via `sale_line_id` field

#### Hierarchical View Improvements
- **Smart button "Vista Jerárquica"**: Quick access to segment hierarchy from sale order
  - Badge shows total segment count
  - Opens filtered segment list view
  - Icon: fa-sitemap for visual consistency

#### UX Enhancements
- **Products Detail column**: New `product_list_preview` field in segment list view
  - Shows product names with quantities inline
  - Format: "Product A (3.0), Product B (5.0)"
  - Helps identify segment contents at a glance

#### Data Migration
- **28 sample products**: Created for testing complete workflows
  - Distributed across 6 segments in demo presupuesto S00001
  - Total task count: 14 (6 segments + 8 products)
  - Validates entire task creation pipeline

### Changed

#### Architecture
- **Task creation algorithm**: Replaced iterative BFS with recursive DFS
  - Method: `_create_segment_tasks_recursive()`
  - Processing order: segment → products → child segments
  - Cleaner code, easier to maintain
  - Better performance for deep hierarchies

#### Task Structure
- **Products are tasks, not descriptions**: Removed `_format_products_description()`
  - Previous: Products listed in segment task description
  - Current: Each product is its own subtask
  - Benefit: Proper time tracking per product

#### Configuration
- **Service tracking disabled**: Set `service_tracking='no'` on product tasks
  - Prevents duplicate task creation from native Odoo flow
  - Only segment-based task creation runs
  - Avoids conflicts between flows

### Fixed

#### Constraint C1 Enforcement
- **Sale line segment changes**: Now properly intercepted via `write()` override
  - Validates segment belongs to same order
  - Prevents cross-order line assignment
  - Added comprehensive test coverage

#### Archived Projects
- **Task creation skipped**: Sale order confirmation checks project.active
  - Warning logged if project archived
  - No errors during confirmation
  - Graceful degradation

#### Hierarchy Display
- **Parent-child relationships**: Task tree view correctly shows structure
  - Segments are parents
  - Products are children
  - Child segments are siblings
  - No orphaned tasks

### Technical

#### Code Quality
- **98 test methods**: Complete test coverage across 5 test files
  - `test_sale_order_segment.py`: Core segment functionality
  - `test_sale_order_line.py`: Line-segment relationship
  - `test_automated_task_creation.py`: Task creation pipeline
  - `test_project_task_segment.py`: Task-segment integration
  - `test_ux_enhancements.py`: UX features validation
- **2123 lines of test code**: Comprehensive validation

#### Logging
- **Enhanced debug messages**: Task creation now logs:
  - Segment task creation (with level)
  - Product task creation (with parent segment)
  - Skipped duplicates (idempotency checks)
  - Errors with full context

## [1.0.0] - 2026-02-05

### Added

#### Core Features
- **Hierarchical segment structure**: Up to 4 levels of depth
  - Automatic level calculation
  - Parent-child relationships
  - Sequence-based ordering
- **Budget organization**: Link sale order lines to segments
  - Many-to-one segment_id field on sale.order.line
  - Constraint: segment must belong to same order
- **Automatic task creation**: On sale order confirmation
  - One task per segment (hierarchical)
  - Project created by native Odoo flow
  - Idempotent (checks for existing tasks)
- **Recursive totals**: Subtotal and total calculation
  - Subtotal: Direct products in segment
  - Total: Subtotal + all descendant totals
  - Real-time updates on line changes

#### UX Features
- **Full path display**: Breadcrumb navigation (e.g., "Root / Child / Grandchild")
- **Depth indicators**: Visual hierarchy levels in list view
  - Level 1: Primary decoration (bold)
  - Level 2: Info decoration (blue)
  - Level 3: Muted decoration (gray)
  - Level 4: Warning decoration (orange)
- **Smart buttons**:
  - Segment count on sale order
  - Child segment count on segment form
  - Shows depth of deepest descendant
- **Product count badge**: Shows number of products in segment

#### Security
- **Access Control Lists**: Two permission levels
  - Sales User: Read-only access
  - Sales Manager: Full CRUD access
- **Record Rules**: Order-based data isolation
  - Users see segments from their orders only
  - Managers see all segments

#### Technical
- **Savepoint isolation**: Prevents cascading task creation failures
- **Comprehensive logging**: Info/warning/error levels for debugging
- **Data validation**: Constraints on depth, parent relationships
- **Test coverage**: Initial test suite (expanded to 98 tests in v1.1.0)

### Developer Info
- **Odoo Version**: 18.0 Community
- **Python Version**: 3.10+
- **Database**: PostgreSQL 14
- **License**: LGPL-3
- **Module Name**: `spora_segment`
- **Depends**: `sale`, `project`

---

**Legend**:
- Added: New features
- Changed: Changes to existing functionality
- Deprecated: Soon-to-be removed features
- Removed: Removed features
- Fixed: Bug fixes
- Security: Security-related changes
