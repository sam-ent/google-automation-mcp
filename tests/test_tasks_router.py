"""Tests for Tasks tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.tasks_router import (
    list_task_lists,
    get_tasks,
    create_task,
    update_task,
    delete_task,
    complete_task,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.tasks_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestTasksRouterTools:
    async def test_list_task_lists(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "tl1", "title": "My Tasks", "updated": "2026-04-17T00:00:00Z"},
        ]
        result = await list_task_lists(user_google_email="t@t.com")
        assert "Found 1 task lists" in result
        assert "My Tasks" in result

    async def test_list_task_lists_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await list_task_lists(user_google_email="t@t.com")
        assert "No task lists found" in result

    async def test_get_tasks(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "t1", "title": "Buy milk", "status": "needsAction",
             "due": "2026-04-18T00:00:00Z", "notes": "2%"},
            {"id": "t2", "title": "Done thing", "status": "completed",
             "due": None, "notes": None},
        ]
        result = await get_tasks(user_google_email="t@t.com")
        assert "Found 2 tasks" in result
        assert "○ Buy milk" in result
        assert "✓ Done thing" in result
        assert "Due:" in result

    async def test_get_tasks_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await get_tasks(user_google_email="t@t.com")
        assert "No tasks found" in result

    async def test_create_task(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "t1", "title": "New task", "status": "needsAction", "due": None,
        }
        result = await create_task(user_google_email="t@t.com", title="New task")
        assert "Created task: New task" in result

    async def test_create_task_with_due(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "t1", "title": "Deadline task", "status": "needsAction",
            "due": "2026-04-20T00:00:00Z",
        }
        result = await create_task(
            user_google_email="t@t.com", title="Deadline task",
            due="2026-04-20T00:00:00Z",
        )
        assert "Due:" in result

    async def test_update_task(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "t1", "title": "Updated", "status": "needsAction", "due": None,
        }
        result = await update_task(
            user_google_email="t@t.com", task_id="t1", title="Updated",
        )
        assert "Updated task: Updated" in result

    async def test_delete_task(self, mock_call_router):
        mock_call_router.return_value = {"deleted": True}
        result = await delete_task(user_google_email="t@t.com", task_id="t1")
        assert "Deleted task: t1" in result

    async def test_complete_task(self, mock_call_router):
        mock_call_router.return_value = {"id": "t1", "title": "Done", "status": "completed"}
        result = await complete_task(user_google_email="t@t.com", task_id="t1")
        assert "Completed task: Done" in result
