# -*- coding: utf-8 -*-
"""Test for project task filtering in task view.

This module tests that the action_view_tasks override correctly filters
to show only root-level tasks by default, improving UX for projects with
deep task hierarchies.
"""

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'spora_segment')
class TestProjectTaskFiltering(TransactionCase):
    """Test cases for project task view filtering."""

    def setUp(self):
        """Set up test data with hierarchical tasks."""
        super().setUp()

        # Create a project
        self.project = self.env['project.project'].create({
            'name': 'Test Project with Hierarchy'
        })

        # Create root tasks (parent_id = False)
        self.root_task_1 = self.env['project.task'].create({
            'name': 'Root Task 1',
            'project_id': self.project.id,
        })

        self.root_task_2 = self.env['project.task'].create({
            'name': 'Root Task 2',
            'project_id': self.project.id,
        })

        # Create subtasks (parent_id set)
        self.subtask_1_1 = self.env['project.task'].create({
            'name': 'Subtask 1.1',
            'project_id': self.project.id,
            'parent_id': self.root_task_1.id,
        })

        self.subtask_1_2 = self.env['project.task'].create({
            'name': 'Subtask 1.2',
            'project_id': self.project.id,
            'parent_id': self.root_task_1.id,
        })

        self.subtask_2_1 = self.env['project.task'].create({
            'name': 'Subtask 2.1',
            'project_id': self.project.id,
            'parent_id': self.root_task_2.id,
        })

        # Create level 2 subtask (grandchild)
        self.subtask_1_1_1 = self.env['project.task'].create({
            'name': 'Subtask 1.1.1',
            'project_id': self.project.id,
            'parent_id': self.subtask_1_1.id,
        })

    def test_action_view_tasks_filters_root_only(self):
        """Test that action_view_tasks returns domain filtering root tasks."""
        action = self.project.action_view_tasks()

        # Check that domain includes parent_id filter
        self.assertIn('domain', action, "Action should have domain")
        domain = action['domain']

        # Check for parent_id = False condition
        parent_filter_found = False
        for condition in domain:
            if isinstance(condition, (list, tuple)) and len(condition) == 3:
                field, operator, value = condition
                if field == 'parent_id' and operator == '=' and value is False:
                    parent_filter_found = True
                    break

        self.assertTrue(
            parent_filter_found,
            "Domain should filter parent_id = False"
        )

    def test_action_view_tasks_shows_only_root_tasks(self):
        """Test that resulting domain actually filters root tasks correctly."""
        action = self.project.action_view_tasks()
        domain = action['domain']

        # Execute the domain to get filtered tasks
        filtered_tasks = self.env['project.task'].search(domain)

        # Should only return root tasks (2 tasks)
        self.assertEqual(
            len(filtered_tasks),
            2,
            "Should return only 2 root tasks"
        )

        # Check that returned tasks are actually root tasks
        self.assertIn(
            self.root_task_1,
            filtered_tasks,
            "Root task 1 should be in results"
        )
        self.assertIn(
            self.root_task_2,
            filtered_tasks,
            "Root task 2 should be in results"
        )

        # Check that subtasks are NOT in results
        self.assertNotIn(
            self.subtask_1_1,
            filtered_tasks,
            "Subtask 1.1 should NOT be in results"
        )
        self.assertNotIn(
            self.subtask_2_1,
            filtered_tasks,
            "Subtask 2.1 should NOT be in results"
        )
        self.assertNotIn(
            self.subtask_1_1_1,
            filtered_tasks,
            "Grandchild subtask should NOT be in results"
        )

    def test_all_tasks_still_accessible(self):
        """Test that all tasks are still accessible without filter."""
        # Search all tasks in project without filter
        all_tasks = self.env['project.task'].search([
            ('project_id', '=', self.project.id)
        ])

        # Should return ALL 6 tasks (2 root + 4 subtasks)
        self.assertEqual(
            len(all_tasks),
            6,
            "Without filter, should return all 6 tasks"
        )

    def test_project_with_no_subtasks(self):
        """Test that filter works correctly for projects with no hierarchy."""
        # Create project with only root tasks
        simple_project = self.env['project.project'].create({
            'name': 'Simple Project'
        })

        task1 = self.env['project.task'].create({
            'name': 'Task 1',
            'project_id': simple_project.id,
        })

        task2 = self.env['project.task'].create({
            'name': 'Task 2',
            'project_id': simple_project.id,
        })

        action = simple_project.action_view_tasks()
        domain = action['domain']
        filtered_tasks = self.env['project.task'].search(domain)

        # Should return both tasks
        self.assertEqual(
            len(filtered_tasks),
            2,
            "Should return both root tasks"
        )
        self.assertIn(task1, filtered_tasks)
        self.assertIn(task2, filtered_tasks)

    def test_domain_preserves_project_filter(self):
        """Test that domain still filters by project correctly."""
        # Create another project with tasks
        other_project = self.env['project.project'].create({
            'name': 'Other Project'
        })

        other_task = self.env['project.task'].create({
            'name': 'Other Task',
            'project_id': other_project.id,
        })

        # Get action for original project
        action = self.project.action_view_tasks()
        domain = action['domain']
        filtered_tasks = self.env['project.task'].search(domain)

        # Should NOT include tasks from other project
        self.assertNotIn(
            other_task,
            filtered_tasks,
            "Should not include tasks from other project"
        )

        # Should only have original project's root tasks
        self.assertEqual(len(filtered_tasks), 2)
