import pytest
import asyncio
from unittest.mock import MagicMock, patch
from google_automation_mcp.tools.tasks import (
    list_task_lists,
    get_tasks,
    create_task,
    update_task,
    delete_task,
    complete_task,
)

@pytest.fixture
def mock_tasks_service():
    """Create a mock Google Tasks service."""
    service = MagicMock()
    return service

@pytest.fixture
def mock_get_service(mock_tasks_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_tasks_service,
    ) as mock:
        yield mock

class TestGoogleTasksTools:
    """Tests for Google Tasks MCP tools."""

    @pytest.mark.asyncio
    async def test_list_task_lists_success(self, mock_tasks_service, mock_get_service):
        """Test listing task lists returns formatted output."""
        mock_response = {
            "items": [
                {
                    "id": "list1",
                    "title": "My List",
                    "updated": "2024-01-01T12:00:00.000Z"
                }
            ]
        }
        mock_tasks_service.tasklists().list().execute.return_value = mock_response

        result = await list_task_lists(user_google_email="test@gmail.com")

        assert "Found 1 task lists" in result
        assert "My List" in result
        assert "ID: list1" in result
        mock_tasks_service.tasklists().list.assert_called_with(maxResults=20)

    @pytest.mark.asyncio
    async def test_list_task_lists_empty(self, mock_tasks_service, mock_get_service):
        """Test listing task lists when none are found."""
        mock_tasks_service.tasklists().list().execute.return_value = {"items": []}

        result = await list_task_lists(user_google_email="test@gmail.com")

        assert "No task lists found." == result

    @pytest.mark.asyncio
    async def test_get_tasks_success(self, mock_tasks_service, mock_get_service):
        """Test getting tasks from a list."""
        mock_response = {
            "items": [
                {
                    "id": "task1",
                    "title": "Do laundry",
                    "status": "needsAction",
                    "due": "2024-01-02T00:00:00.000Z",
                    "notes": "Use cold water"
                }
            ]
        }
        mock_tasks_service.tasks().list().execute.return_value = mock_response

        result = await get_tasks(
            user_google_email="test@gmail.com",
            tasklist_id="list1",
            max_results=10
        )

        assert "Found 1 tasks" in result
        assert "○ Do laundry" in result
        assert "ID: task1" in result
        assert "Due: 2024-01-02T00:00:00.000Z" in result
        assert "Notes: Use cold water" in result
        mock_tasks_service.tasks().list.assert_called_with(
            tasklist="list1",
            maxResults=10,
            showCompleted=True,
            showHidden=False
        )

    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_tasks_service, mock_get_service):
        """Test creating a new task."""
        mock_created = {
            "id": "new_task_id",
            "title": "Buy milk",
            "status": "needsAction",
            "due": "2024-01-03T00:00:00.000Z"
        }
        mock_tasks_service.tasks().insert().execute.return_value = mock_created

        result = await create_task(
            user_google_email="test@gmail.com",
            title="Buy milk",
            notes="Organic if possible",
            due="2024-01-03T00:00:00.000Z"
        )

        assert "Created task: Buy milk" in result
        assert "ID: new_task_id" in result
        assert "Status: needsAction" in result
        assert "Due: 2024-01-03T00:00:00.000Z" in result
        
        expected_body = {
            "title": "Buy milk",
            "notes": "Organic if possible",
            "due": "2024-01-03T00:00:00.000Z"
        }
        mock_tasks_service.tasks().insert.assert_called_with(
            tasklist="@default",
            body=expected_body
        )

    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_tasks_service, mock_get_service):
        """Test updating an existing task."""
        mock_existing = {
            "id": "task1",
            "title": "Old title",
            "notes": "Old notes",
            "status": "needsAction"
        }
        mock_updated = {
            "id": "task1",
            "title": "New title",
            "status": "completed"
        }
        
        mock_tasks_service.tasks().get().execute.return_value = mock_existing
        mock_tasks_service.tasks().update().execute.return_value = mock_updated

        result = await update_task(
            user_google_email="test@gmail.com",
            task_id="task1",
            title="New title",
            status="completed"
        )

        assert "Updated task: New title" in result
        assert "Status: completed" in result
        
        # Verify get was called
        mock_tasks_service.tasks().get.assert_called_with(
            tasklist="@default",
            task="task1"
        )
        
        # Verify update was called with merged body
        expected_body = {
            "id": "task1",
            "title": "New title",
            "notes": "Old notes",
            "status": "completed"
        }
        mock_tasks_service.tasks().update.assert_called_with(
            tasklist="@default",
            task="task1",
            body=expected_body
        )

    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_tasks_service, mock_get_service):
        """Test deleting a task."""
        mock_tasks_service.tasks().delete().execute.return_value = {}

        result = await delete_task(
            user_google_email="test@gmail.com",
            task_id="task1",
            tasklist_id="list1"
        )

        assert "Deleted task: task1 from list: list1" in result
        mock_tasks_service.tasks().delete.assert_called_with(
            tasklist="list1",
            task="task1"
        )

    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_tasks_service, mock_get_service):
        """Test marking a task as completed."""
        mock_existing = {
            "id": "task1",
            "title": "Finish report",
            "status": "needsAction"
        }
        mock_updated = {
            "id": "task1",
            "title": "Finish report",
            "status": "completed"
        }
        
        mock_tasks_service.tasks().get().execute.return_value = mock_existing
        mock_tasks_service.tasks().update().execute.return_value = mock_updated

        result = await complete_task(
            user_google_email="test@gmail.com",
            task_id="task1"
        )

        assert "Completed task: Finish report (ID: task1)" in result
        
        # Verify update was called with status="completed"
        args, kwargs = mock_tasks_service.tasks().update.call_args
        assert kwargs["body"]["status"] == "completed"
        assert kwargs["task"] == "task1"
