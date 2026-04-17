"""Tests for Drive tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.drive_router import (
    search_drive_files,
    list_drive_items,
    get_drive_file_content,
    create_drive_file,
    create_drive_folder,
    delete_drive_file,
    trash_drive_file,
    share_drive_file,
    list_drive_permissions,
    remove_drive_permission,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.drive_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestDriveRouterTools:
    async def test_search_drive_files_success(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "f1", "name": "doc.txt", "mime_type": "text/plain",
             "size": 1024, "modified": "2026-04-17T00:00:00Z", "url": "https://..."}
        ]
        result = await search_drive_files(user_google_email="t@t.com", query="doc")
        assert "Found 1 files" in result
        assert "doc.txt" in result

    async def test_search_drive_files_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await search_drive_files(user_google_email="t@t.com", query="nope")
        assert "No files found" in result

    async def test_list_drive_items(self, mock_call_router):
        mock_call_router.return_value = {
            "folders": [{"id": "d1", "name": "Folder1"}],
            "files": [{"id": "f1", "name": "file.txt", "size": 100}],
        }
        result = await list_drive_items(user_google_email="t@t.com")
        assert "Found 2 items" in result
        assert "Folder1" in result
        assert "file.txt" in result

    async def test_list_drive_items_empty(self, mock_call_router):
        mock_call_router.return_value = {"folders": [], "files": []}
        result = await list_drive_items(user_google_email="t@t.com")
        assert "No items found" in result

    async def test_get_drive_file_content(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "f1", "name": "readme.txt", "mime_type": "text/plain",
            "url": "https://...", "content": "Hello world",
        }
        result = await get_drive_file_content(user_google_email="t@t.com", file_id="f1")
        assert "readme.txt" in result
        assert "Hello world" in result

    async def test_create_drive_file(self, mock_call_router):
        mock_call_router.return_value = {"id": "f1", "name": "new.txt", "url": "https://..."}
        result = await create_drive_file(user_google_email="t@t.com", file_name="new.txt")
        assert "Created file: new.txt" in result

    async def test_create_drive_folder(self, mock_call_router):
        mock_call_router.return_value = {"id": "d1", "name": "NewFolder", "url": "https://..."}
        result = await create_drive_folder(user_google_email="t@t.com", folder_name="NewFolder")
        assert "Created folder: NewFolder" in result

    async def test_delete_drive_file(self, mock_call_router):
        mock_call_router.return_value = {"deleted": True}
        result = await delete_drive_file(user_google_email="t@t.com", file_id="f1")
        assert "Permanently deleted" in result

    async def test_trash_drive_file(self, mock_call_router):
        mock_call_router.return_value = {"trashed": True}
        result = await trash_drive_file(user_google_email="t@t.com", file_id="f1")
        assert "Moved to trash" in result

    async def test_share_drive_file(self, mock_call_router):
        mock_call_router.return_value = {"shared": True}
        result = await share_drive_file(
            user_google_email="t@t.com", file_id="f1", email="b@b.com", role="writer"
        )
        assert "Shared file" in result
        assert "b@b.com" in result

    async def test_list_drive_permissions(self, mock_call_router):
        mock_call_router.return_value = {
            "file_id": "f1",
            "permissions": [{"email": "a@a.com", "role": "writer"}],
        }
        result = await list_drive_permissions(user_google_email="t@t.com", file_id="f1")
        assert "a@a.com" in result
        assert "writer" in result

    async def test_list_drive_permissions_empty(self, mock_call_router):
        mock_call_router.return_value = {"file_id": "f1", "permissions": []}
        result = await list_drive_permissions(user_google_email="t@t.com", file_id="f1")
        assert "No permissions found" in result

    async def test_remove_drive_permission(self, mock_call_router):
        mock_call_router.return_value = {"removed": True}
        result = await remove_drive_permission(
            user_google_email="t@t.com", file_id="f1", permission_id="p1"
        )
        assert "Removed permission p1" in result
