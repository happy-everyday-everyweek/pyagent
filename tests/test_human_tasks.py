"""
PyAgent 人工任务系统测试
"""

import pytest
from datetime import datetime, timedelta

from human_tasks.task import HumanTask, Priority, SubTask, TaskStatus
from human_tasks.manager import TaskManager


class TestTaskStatus:
    """测试任务状态枚举"""

    def test_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_status_count(self):
        assert len(TaskStatus) == 4


class TestPriority:
    """测试优先级枚举"""

    def test_priority_values(self):
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.URGENT.value == "urgent"

    def test_priority_count(self):
        assert len(Priority) == 4


class TestSubTask:
    """测试子任务"""

    def test_subtask_creation(self):
        subtask = SubTask(title="Test subtask")
        assert subtask.title == "Test subtask"
        assert subtask.completed is False
        assert subtask.id is not None

    def test_subtask_to_dict(self):
        subtask = SubTask(title="Test subtask")
        data = subtask.to_dict()
        assert data["title"] == "Test subtask"
        assert data["completed"] is False

    def test_subtask_from_dict(self):
        data = {
            "id": "subtask_001",
            "title": "Test subtask",
            "completed": True,
            "created_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-02T00:00:00"
        }
        subtask = SubTask.from_dict(data)
        assert subtask.id == "subtask_001"
        assert subtask.title == "Test subtask"
        assert subtask.completed is True


class TestHumanTask:
    """测试人类任务"""

    def test_task_creation(self):
        task = HumanTask(
            title="Test Task",
            description="Test description"
        )
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.MEDIUM

    def test_task_with_due_date(self):
        due_date = datetime.now() + timedelta(days=1)
        task = HumanTask(
            title="Task with due date",
            due_date=due_date
        )
        assert task.due_date == due_date
        assert task.is_overdue() is False

    def test_task_overdue(self):
        past_date = datetime.now() - timedelta(days=1)
        task = HumanTask(
            title="Overdue task",
            due_date=past_date
        )
        assert task.is_overdue() is True

    def test_task_due_today(self):
        today = datetime.now().replace(hour=23, minute=59, second=59)
        task = HumanTask(
            title="Due today task",
            due_date=today
        )
        assert task.is_due_today() is True

    def test_task_status_checks(self):
        task = HumanTask(title="Test Task")

        assert task.is_pending() is True
        assert task.is_completed() is False
        assert task.is_cancelled() is False
        assert task.is_in_progress() is False

        task.mark_in_progress()
        assert task.is_in_progress() is True

        task.mark_completed()
        assert task.is_completed() is True

    def test_task_progress_no_subtasks(self):
        task = HumanTask(title="Test Task")

        assert task.get_progress() == 0.0

        task.mark_in_progress()
        assert task.get_progress() == 50.0

        task.mark_completed()
        assert task.get_progress() == 100.0

    def test_task_progress_with_subtasks(self):
        task = HumanTask(title="Test Task")
        task.add_subtask("Subtask 1")
        task.add_subtask("Subtask 2")

        assert task.get_progress() == 0.0

        task.complete_subtask(task.subtasks[0].id)
        assert task.get_progress() == 50.0

    def test_add_subtask(self):
        task = HumanTask(title="Test Task")
        subtask = task.add_subtask("New subtask")

        assert len(task.subtasks) == 1
        assert subtask.title == "New subtask"

    def test_remove_subtask(self):
        task = HumanTask(title="Test Task")
        subtask = task.add_subtask("Subtask to remove")

        result = task.remove_subtask(subtask.id)
        assert result is True
        assert len(task.subtasks) == 0

    def test_remove_nonexistent_subtask(self):
        task = HumanTask(title="Test Task")
        result = task.remove_subtask("nonexistent_id")
        assert result is False

    def test_complete_subtask(self):
        task = HumanTask(title="Test Task")
        subtask = task.add_subtask("Subtask")

        result = task.complete_subtask(subtask.id)
        assert result is True
        assert subtask.completed is True

    def test_mark_completed(self):
        task = HumanTask(title="Test Task")
        task.add_subtask("Subtask 1")
        task.add_subtask("Subtask 2")

        task.mark_completed()
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert all(st.completed for st in task.subtasks)

    def test_mark_cancelled(self):
        task = HumanTask(title="Test Task")
        task.mark_cancelled()
        assert task.status == TaskStatus.CANCELLED

    def test_update_task(self):
        task = HumanTask(title="Original Title")
        task.update(title="New Title", description="New description")

        assert task.title == "New Title"
        assert task.description == "New description"

    def test_task_to_dict(self):
        task = HumanTask(
            title="Test Task",
            description="Test description",
            priority=Priority.HIGH
        )
        data = task.to_dict()

        assert data["title"] == "Test Task"
        assert data["description"] == "Test description"
        assert data["priority"] == "high"
        assert data["status"] == "pending"

    def test_task_from_dict(self):
        data = {
            "task_id": "task_001",
            "title": "Test Task",
            "description": "Test description",
            "status": "pending",
            "priority": "high",
            "due_date": None,
            "reminder": None,
            "category": "work",
            "tags": ["tag1", "tag2"],
            "subtasks": [],
            "attachments": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "completed_at": None
        }
        task = HumanTask.from_dict(data)

        assert task.task_id == "task_001"
        assert task.title == "Test Task"
        assert task.priority == Priority.HIGH


class TestTaskManager:
    """测试任务管理器"""

    def setup_method(self):
        import tempfile
        import os
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TaskManager(data_dir=self.temp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_task(self):
        task = self.manager.create_task(
            title="Test Task",
            description="Test description"
        )
        assert task.title == "Test Task"
        assert task.task_id.startswith("htask_")

    def test_create_task_with_subtasks(self):
        task = self.manager.create_task(
            title="Task with subtasks",
            subtasks=["Subtask 1", "Subtask 2"]
        )
        assert len(task.subtasks) == 2

    def test_update_task(self):
        task = self.manager.create_task(title="Original Title")

        updated = self.manager.update_task(
            task.task_id,
            title="New Title",
            description="New description"
        )
        assert updated is not None
        assert updated.title == "New Title"

    def test_update_nonexistent_task(self):
        result = self.manager.update_task("nonexistent", title="New Title")
        assert result is None

    def test_delete_task(self):
        task = self.manager.create_task(title="Task to delete")

        result = self.manager.delete_task(task.task_id)
        assert result is True
        assert self.manager.get_task(task.task_id) is None

    def test_delete_nonexistent_task(self):
        result = self.manager.delete_task("nonexistent")
        assert result is False

    def test_complete_task(self):
        task = self.manager.create_task(title="Task to complete")

        completed = self.manager.complete_task(task.task_id)
        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED

    def test_cancel_task(self):
        task = self.manager.create_task(title="Task to cancel")

        cancelled = self.manager.cancel_task(task.task_id)
        assert cancelled is not None
        assert cancelled.status == TaskStatus.CANCELLED

    def test_start_task(self):
        task = self.manager.create_task(title="Task to start")

        started = self.manager.start_task(task.task_id)
        assert started is not None
        assert started.status == TaskStatus.IN_PROGRESS

    def test_get_task(self):
        task = self.manager.create_task(title="Test Task")

        retrieved = self.manager.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.title == "Test Task"

    def test_list_tasks(self):
        self.manager.create_task(title="Task 1")
        self.manager.create_task(title="Task 2")

        tasks = self.manager.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_with_filter(self):
        self.manager.create_task(
            title="Task 1",
            priority=Priority.HIGH
        )
        self.manager.create_task(
            title="Task 2",
            priority=Priority.LOW
        )

        tasks = self.manager.list_tasks(priority=Priority.HIGH)
        assert len(tasks) == 1

    def test_search_tasks(self):
        self.manager.create_task(title="Python Task")
        self.manager.create_task(title="Java Task")
        self.manager.create_task(title="JavaScript Task")

        results = self.manager.search_tasks("Python")
        assert len(results) == 1
        assert results[0].title == "Python Task"

    def test_get_overdue_tasks(self):
        past_date = datetime.now() - timedelta(days=1)

        self.manager.create_task(
            title="Overdue Task",
            due_date=past_date
        )
        self.manager.create_task(
            title="Normal Task",
            due_date=datetime.now() + timedelta(days=1)
        )

        overdue = self.manager.get_overdue_tasks()
        assert len(overdue) == 1
        assert overdue[0].title == "Overdue Task"

    def test_get_tasks_due_today(self):
        today = datetime.now().replace(hour=23, minute=59, second=59)
        tomorrow = datetime.now() + timedelta(days=1)

        self.manager.create_task(
            title="Due Today",
            due_date=today
        )
        self.manager.create_task(
            title="Due Tomorrow",
            due_date=tomorrow
        )

        due_today = self.manager.get_tasks_due_today()
        assert len(due_today) == 1

    def test_get_statistics(self):
        self.manager.create_task(title="Task 1")
        self.manager.create_task(title="Task 2", priority=Priority.HIGH)

        task3 = self.manager.create_task(title="Task 3")
        self.manager.complete_task(task3.task_id)

        stats = self.manager.get_statistics()
        assert stats["total_tasks"] == 3
        assert stats["status_distribution"]["completed"] == 1

    def test_add_subtask_to_task(self):
        task = self.manager.create_task(title="Task with subtask")

        updated = self.manager.add_subtask(task.task_id, "New subtask")
        assert updated is not None
        assert len(updated.subtasks) == 1

    def test_complete_subtask(self):
        task = self.manager.create_task(
            title="Task",
            subtasks=["Subtask 1"]
        )

        subtask_id = task.subtasks[0].id
        updated = self.manager.complete_subtask(task.task_id, subtask_id)
        assert updated is not None
        assert updated.subtasks[0].completed is True
