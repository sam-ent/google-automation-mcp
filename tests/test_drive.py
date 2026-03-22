"""
Unit tests for Google Drive MCP tools

Tests all Drive tools with mocked API responses.
"""

import io
import pytest
from unittest.mock import MagicMock, patch

from google_automation_mcp.tools.drive import (
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
def mock_drive_service():
    """Create a mock Drive API service."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_get_service(mock_drive_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_drive_service,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestDriveTools:
    """Tests for all Drive tool functions."""

    async def test_search_drive_files_structured(self, mock_drive_service, mock_get_service):
        """Test search with structured query."""
        mock_drive_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "file123",
                    "name": "Test Sheet",
                    "mimeType": "application/vnd.google-apps.spreadsheet",
                    "webViewLink": "https://drive.google.com/link1",
                }
            ]
        }

        result = await search_drive_files(
            user_google_email="test@example.com", query="name contains 'Test'"
        )

        assert "Found 1 files" in result
        assert "Test Sheet" in result
        mock_drive_service.files().list.assert_called_with(
            q="name contains 'Test'",
            pageSize=10,
            fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )

    async def test_list_drive_items(self, mock_drive_service, mock_get_service):
        """Test listing items in a folder."""
        mock_drive_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "f1",
                    "name": "Folder A",
                    "mimeType": "application/vnd.google-apps.folder",
                },
                {
                    "id": "f2",
                    "name": "File B",
                    "mimeType": "text/plain",
                    "size": "1024",
                },
            ]
        }

        result = await list_drive_items(
            user_google_email="test@example.com", folder_id="root"
        )

        assert "Found 2 items" in result
        assert "Folder A" in result
        assert "File B" in result

    async def test_get_drive_file_content_doc(self, mock_drive_service, mock_get_service):
        """Test getting content of a Google Doc (export)."""
        mock_drive_service.files().get().execute.return_value = {
            "id": "doc123",
            "name": "My Doc",
            "mimeType": "application/vnd.google-apps.document",
            "webViewLink": "https://docs.google.com/link",
        }

        # Mock the export_media call
        mock_request = MagicMock()
        mock_drive_service.files().export_media.return_value = mock_request

        # Patch MediaIoBaseDownload to simulate downloading content
        with patch("google_automation_mcp.tools.drive.MediaIoBaseDownload") as mock_download_cls:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.return_value = (None, True)
            mock_download_cls.return_value = mock_downloader

            # Patch io.BytesIO to control the buffer content
            with patch("google_automation_mcp.tools.drive.io.BytesIO") as mock_bytesio:
                mock_fh = MagicMock()
                mock_bytesio.return_value = mock_fh
                mock_fh.getvalue.return_value = b"Hello World"

                result = await get_drive_file_content(
                    user_google_email="test@example.com", file_id="doc123"
                )

        assert 'File: "My Doc"' in result
        assert "Hello World" in result
        mock_drive_service.files().export_media.assert_called_with(
            fileId="doc123", mimeType="text/plain"
        )

    async def test_create_drive_file(self, mock_drive_service, mock_get_service):
        """Test creating a file with content."""
        mock_drive_service.files().create().execute.return_value = {
            "id": "new123",
            "name": "test.txt",
            "webViewLink": "https://link",
        }

        with patch("google_automation_mcp.tools.drive.MediaIoBaseUpload"):
            result = await create_drive_file(
                user_google_email="test@example.com",
                file_name="test.txt",
                content="Hello",
            )

        assert "Created file: test.txt" in result
        assert "ID: new123" in result
        mock_drive_service.files().create.assert_called()

    async def test_create_drive_folder(self, mock_drive_service, mock_get_service):
        """Test creating a folder."""
        mock_drive_service.files().create().execute.return_value = {
            "id": "folder123",
            "name": "New Folder",
        }

        result = await create_drive_folder(
            user_google_email="test@example.com", folder_name="New Folder"
        )

        assert "Created folder: New Folder" in result
        args, kwargs = mock_drive_service.files().create.call_args
        assert kwargs["body"]["mimeType"] == "application/vnd.google-apps.folder"

    async def test_delete_drive_file(self, mock_drive_service, mock_get_service):
        """Test permanent deletion."""
        mock_drive_service.files().delete().execute.return_value = {}

        result = await delete_drive_file(
            user_google_email="test@example.com", file_id="file123"
        )

        assert "Permanently deleted" in result
        mock_drive_service.files().delete.assert_called_with(
            fileId="file123", supportsAllDrives=True
        )

    async def test_trash_drive_file(self, mock_drive_service, mock_get_service):
        """Test moving to trash."""
        mock_drive_service.files().update().execute.return_value = {}

        result = await trash_drive_file(
            user_google_email="test@example.com", file_id="file123"
        )

        assert "Moved to trash" in result
        mock_drive_service.files().update.assert_called_with(
            fileId="file123", body={"trashed": True}, supportsAllDrives=True
        )

    async def test_share_drive_file(self, mock_drive_service, mock_get_service):
        """Test sharing a file."""
        mock_drive_service.permissions().create().execute.return_value = {
            "id": "perm789"
        }

        result = await share_drive_file(
            user_google_email="test@example.com",
            file_id="file123",
            email="user@example.com",
            role="writer",
        )

        assert "Shared file: file123" in result
        assert "Role: writer" in result
        mock_drive_service.permissions().create.assert_called()

    async def test_list_drive_permissions(self, mock_drive_service, mock_get_service):
        """Test listing permissions."""
        mock_drive_service.permissions().list().execute.return_value = {
            "permissions": [
                {
                    "id": "p1",
                    "type": "user",
                    "role": "owner",
                    "emailAddress": "owner@example.com",
                    "displayName": "Owner Name",
                },
                {"id": "p2", "type": "anyone", "role": "reader"},
            ]
        }

        result = await list_drive_permissions(
            user_google_email="test@example.com", file_id="file123"
        )

        assert "Permissions for file file123" in result
        assert "Owner Name (owner)" in result
        assert "Anyone with link (reader)" in result

    async def test_remove_drive_permission(self, mock_drive_service, mock_get_service):
        """Test removing a permission."""
        mock_drive_service.permissions().delete().execute.return_value = {}

        result = await remove_drive_permission(
            user_google_email="test@example.com",
            file_id="file123",
            permission_id="perm123",
        )

        assert "Removed permission perm123" in result
        mock_drive_service.permissions().delete.assert_called_with(
            fileId="file123", permissionId="perm123", supportsAllDrives=True
        )
