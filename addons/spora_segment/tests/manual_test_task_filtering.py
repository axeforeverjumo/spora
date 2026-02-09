#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manual test script for project task filtering.

This script can be executed from Odoo shell to manually verify that
action_view_tasks correctly filters root tasks.

Usage:
    docker compose exec -T odoo odoo shell -d spora --no-http

Then in the shell:
    exec(open('/mnt/extra-addons/spora_segment/tests/manual_test_task_filtering.py').read())
"""

import logging

_logger = logging.getLogger(__name__)


def test_task_filtering():
    """Manual test for task filtering functionality."""
    Project = env['project.project']
    Task = env['project.task']

    _logger.info("=" * 80)
    _logger.info("MANUAL TEST: Project Task Filtering")
    _logger.info("=" * 80)

    # Find or create test project
    project = Project.search([('name', '=', 'Test Filtering Project')], limit=1)
    if not project:
        _logger.info("Creating test project...")
        project = Project.create({'name': 'Test Filtering Project'})
    else:
        _logger.info("Using existing test project: %s", project.name)

    # Clear existing tasks
    existing_tasks = Task.search([('project_id', '=', project.id)])
    if existing_tasks:
        _logger.info("Cleaning up %d existing tasks...", len(existing_tasks))
        existing_tasks.unlink()

    # Create root tasks
    _logger.info("\nCreating 3 root tasks...")
    root1 = Task.create({
        'name': 'Root Task 1',
        'project_id': project.id,
    })
    _logger.info("  - Created: %s (ID: %s)", root1.name, root1.id)

    root2 = Task.create({
        'name': 'Root Task 2',
        'project_id': project.id,
    })
    _logger.info("  - Created: %s (ID: %s)", root2.name, root2.id)

    root3 = Task.create({
        'name': 'Root Task 3',
        'project_id': project.id,
    })
    _logger.info("  - Created: %s (ID: %s)", root3.name, root3.id)

    # Create subtasks under root1
    _logger.info("\nCreating 2 subtasks under Root Task 1...")
    sub1_1 = Task.create({
        'name': 'Subtask 1.1',
        'project_id': project.id,
        'parent_id': root1.id,
    })
    _logger.info("  - Created: %s (ID: %s, parent: %s)", sub1_1.name, sub1_1.id, root1.name)

    sub1_2 = Task.create({
        'name': 'Subtask 1.2',
        'project_id': project.id,
        'parent_id': root1.id,
    })
    _logger.info("  - Created: %s (ID: %s, parent: %s)", sub1_2.name, sub1_2.id, root1.name)

    # Create subtasks under root2
    _logger.info("\nCreating 3 subtasks under Root Task 2...")
    sub2_1 = Task.create({
        'name': 'Subtask 2.1',
        'project_id': project.id,
        'parent_id': root2.id,
    })
    _logger.info("  - Created: %s (ID: %s, parent: %s)", sub2_1.name, sub2_1.id, root2.name)

    sub2_2 = Task.create({
        'name': 'Subtask 2.2',
        'project_id': project.id,
        'parent_id': root2.id,
    })
    _logger.info("  - Created: %s (ID: %s, parent: %s)", sub2_2.name, sub2_2.id, root2.name)

    sub2_3 = Task.create({
        'name': 'Subtask 2.3',
        'project_id': project.id,
        'parent_id': root2.id,
    })
    _logger.info("  - Created: %s (ID: %s, parent: %s)", sub2_3.name, sub2_3.id, root2.name)

    # Create level 2 subtask (grandchild)
    _logger.info("\nCreating 1 grandchild task under Subtask 1.1...")
    sub1_1_1 = Task.create({
        'name': 'Subtask 1.1.1',
        'project_id': project.id,
        'parent_id': sub1_1.id,
    })
    _logger.info("  - Created: %s (ID: %s, parent: %s)", sub1_1_1.name, sub1_1_1.id, sub1_1.name)

    # Total: 3 root + 5 subtasks + 1 grandchild = 9 tasks
    total_tasks = Task.search_count([('project_id', '=', project.id)])
    _logger.info("\n" + "=" * 80)
    _logger.info("Total tasks created: %d", total_tasks)
    _logger.info("  - Root tasks: 3")
    _logger.info("  - Subtasks: 5")
    _logger.info("  - Grandchild tasks: 1")
    _logger.info("=" * 80)

    # Test action_view_tasks
    _logger.info("\nTesting project.action_view_tasks()...")
    action = project.action_view_tasks()

    _logger.info("\nAction result:")
    _logger.info("  - Type: %s", action.get('type'))
    _logger.info("  - Model: %s", action.get('res_model'))
    _logger.info("  - View mode: %s", action.get('view_mode'))

    _logger.info("\nDomain filter:")
    domain = action.get('domain', [])
    for condition in domain:
        _logger.info("  - %s", condition)

    # Execute domain to see filtered results
    _logger.info("\nExecuting domain to get filtered tasks...")
    filtered_tasks = Task.search(domain)
    _logger.info("  - Filtered tasks count: %d", len(filtered_tasks))

    if len(filtered_tasks) == 3:
        _logger.info("  - ✅ SUCCESS: Only root tasks returned")
    else:
        _logger.error("  - ❌ FAILURE: Expected 3 root tasks, got %d", len(filtered_tasks))

    _logger.info("\nFiltered tasks:")
    for task in filtered_tasks:
        parent_info = f" (parent: {task.parent_id.name})" if task.parent_id else " (ROOT)"
        _logger.info("  - %s (ID: %s)%s", task.name, task.id, parent_info)

    # Verify root tasks are included
    _logger.info("\nVerifying root tasks are included:")
    for root in [root1, root2, root3]:
        if root in filtered_tasks:
            _logger.info("  - ✅ %s is in filtered results", root.name)
        else:
            _logger.error("  - ❌ %s is MISSING from filtered results", root.name)

    # Verify subtasks are excluded
    _logger.info("\nVerifying subtasks are excluded:")
    for sub in [sub1_1, sub1_2, sub2_1, sub2_2, sub2_3, sub1_1_1]:
        if sub not in filtered_tasks:
            _logger.info("  - ✅ %s is correctly excluded", sub.name)
        else:
            _logger.error("  - ❌ %s should be excluded but appears in results", sub.name)

    _logger.info("\n" + "=" * 80)
    _logger.info("TEST COMPLETED")
    _logger.info("=" * 80)

    return {
        'project': project,
        'total_tasks': total_tasks,
        'filtered_tasks': len(filtered_tasks),
        'expected_filtered': 3,
        'success': len(filtered_tasks) == 3
    }


# Run the test if executed directly
if __name__ == '__main__':
    result = test_task_filtering()
    print("\nTest Result:", result)
