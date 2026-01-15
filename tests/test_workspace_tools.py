"""
Unit tests for Google Workspace MCP tools

Tests Gmail, Drive, Sheets, Calendar, and Docs tools with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch


# Patch target for all service injections
SERVICE_PATCH = "google_automation_mcp.auth.service_adapter.get_service_for_user"


# ============================================================================
# Gmail Tests
# ============================================================================


class TestSearchGmailMessages:
    """Tests for search_gmail_messages."""

    @pytest.mark.asyncio
    async def test_search_messages_success(self):
        """Test searching Gmail messages returns formatted output."""
        mock_service = Mock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg123", "threadId": "thread123"}]
        }
        mock_service.users().messages().get().execute.return_value = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "2026-01-15"},
                ]
            },
            "snippet": "This is a test message preview",
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.gmail import search_gmail_messages

            result = await search_gmail_messages(
                user_google_email="user@example.com",
                query="from:sender@example.com",
            )

            assert "Found 1 messages" in result
            assert "Test Subject" in result
            assert "sender@example.com" in result

    @pytest.mark.asyncio
    async def test_search_messages_empty(self):
        """Test searching Gmail with no results."""
        mock_service = Mock()
        mock_service.users().messages().list().execute.return_value = {"messages": []}

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.gmail import search_gmail_messages

            result = await search_gmail_messages(
                user_google_email="user@example.com",
                query="nonexistent",
            )

            assert "No messages found" in result


class TestListGmailLabels:
    """Tests for list_gmail_labels."""

    @pytest.mark.asyncio
    async def test_list_labels_success(self):
        """Test listing Gmail labels."""
        mock_service = Mock()
        mock_service.users().labels().list().execute.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "Label_1", "name": "Custom Label", "type": "user"},
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.gmail import list_gmail_labels

            result = await list_gmail_labels(user_google_email="user@example.com")

            assert "Found 2 labels" in result
            assert "INBOX" in result
            assert "Custom Label" in result


class TestModifyGmailLabels:
    """Tests for modify_gmail_labels."""

    @pytest.mark.asyncio
    async def test_modify_labels_success(self):
        """Test modifying Gmail labels on a message."""
        mock_service = Mock()
        mock_service.users().messages().modify().execute.return_value = {
            "id": "msg123",
            "labelIds": ["STARRED", "IMPORTANT"],
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.gmail import modify_gmail_labels

            result = await modify_gmail_labels(
                user_google_email="user@example.com",
                message_id="msg123",
                add_labels=["STARRED", "IMPORTANT"],
                remove_labels=["UNREAD"],
            )

            assert "Modified message: msg123" in result
            assert "Added:" in result
            assert "Removed:" in result


# ============================================================================
# Drive Tests
# ============================================================================


class TestSearchDriveFiles:
    """Tests for search_drive_files."""

    @pytest.mark.asyncio
    async def test_search_files_success(self):
        """Test searching Drive files."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "file123",
                    "name": "Test Document",
                    "mimeType": "application/vnd.google-apps.document",
                    "modifiedTime": "2026-01-15T10:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/file123",
                }
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import search_drive_files

            result = await search_drive_files(
                user_google_email="user@example.com",
                query="test",
            )

            assert "Found 1 files" in result
            assert "Test Document" in result
            assert "file123" in result


class TestListDriveItems:
    """Tests for list_drive_items."""

    @pytest.mark.asyncio
    async def test_list_items_success(self):
        """Test listing Drive folder contents."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "folder456",
                    "name": "My Folder",
                    "mimeType": "application/vnd.google-apps.folder",
                },
                {
                    "id": "file789",
                    "name": "My File.txt",
                    "mimeType": "text/plain",
                    "size": "1024",
                },
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import list_drive_items

            result = await list_drive_items(
                user_google_email="user@example.com",
                folder_id="root",
            )

            assert "Found 2 items" in result
            assert "My Folder" in result
            assert "My File.txt" in result


class TestCreateDriveFolder:
    """Tests for create_drive_folder."""

    @pytest.mark.asyncio
    async def test_create_folder_success(self):
        """Test creating a Drive folder."""
        mock_service = Mock()
        mock_service.files().create().execute.return_value = {
            "id": "folder123",
            "name": "New Folder",
            "webViewLink": "https://drive.google.com/folder123",
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import create_drive_folder

            result = await create_drive_folder(
                user_google_email="user@example.com",
                folder_name="New Folder",
            )

            assert "Created folder" in result
            assert "folder123" in result


class TestDeleteDriveFile:
    """Tests for delete_drive_file."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Test permanently deleting a file."""
        mock_service = Mock()
        mock_service.files().delete().execute.return_value = None

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import delete_drive_file

            result = await delete_drive_file(
                user_google_email="user@example.com",
                file_id="file123",
            )

            assert "Permanently deleted" in result
            assert "file123" in result


class TestTrashDriveFile:
    """Tests for trash_drive_file."""

    @pytest.mark.asyncio
    async def test_trash_file_success(self):
        """Test moving a file to trash."""
        mock_service = Mock()
        mock_service.files().update().execute.return_value = {"trashed": True}

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import trash_drive_file

            result = await trash_drive_file(
                user_google_email="user@example.com",
                file_id="file123",
            )

            assert "Moved to trash" in result
            assert "file123" in result


class TestShareDriveFile:
    """Tests for share_drive_file."""

    @pytest.mark.asyncio
    async def test_share_file_success(self):
        """Test sharing a file."""
        mock_service = Mock()
        mock_service.permissions().create().execute.return_value = {
            "id": "perm123",
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import share_drive_file

            result = await share_drive_file(
                user_google_email="user@example.com",
                file_id="file123",
                email="other@example.com",
                role="writer",
            )

            assert "Shared file" in result
            assert "other@example.com" in result
            assert "writer" in result


class TestListDrivePermissions:
    """Tests for list_drive_permissions."""

    @pytest.mark.asyncio
    async def test_list_permissions_success(self):
        """Test listing file permissions."""
        mock_service = Mock()
        mock_service.permissions().list().execute.return_value = {
            "permissions": [
                {
                    "id": "perm1",
                    "type": "user",
                    "role": "owner",
                    "emailAddress": "owner@example.com",
                },
                {
                    "id": "perm2",
                    "type": "user",
                    "role": "reader",
                    "emailAddress": "viewer@example.com",
                },
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.drive import list_drive_permissions

            result = await list_drive_permissions(
                user_google_email="user@example.com",
                file_id="file123",
            )

            assert "Permissions for file" in result
            assert "owner" in result
            assert "reader" in result


# ============================================================================
# Sheets Tests
# ============================================================================


class TestGetSheetValues:
    """Tests for get_sheet_values."""

    @pytest.mark.asyncio
    async def test_get_values_success(self):
        """Test getting spreadsheet values."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Name", "Age", "City"],
                ["Alice", "30", "NYC"],
                ["Bob", "25", "LA"],
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.sheets import get_sheet_values

            result = await get_sheet_values(
                user_google_email="user@example.com",
                spreadsheet_id="sheet123",
                range="Sheet1!A1:C3",
            )

            assert "Rows: 3" in result
            assert "Name" in result
            assert "Alice" in result


class TestCreateSpreadsheet:
    """Tests for create_spreadsheet."""

    @pytest.mark.asyncio
    async def test_create_spreadsheet_success(self):
        """Test creating a new spreadsheet."""
        mock_service = Mock()
        mock_service.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "new_sheet_123",
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/new_sheet_123",
            "sheets": [{"properties": {"title": "Sheet1"}}],
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.sheets import create_spreadsheet

            result = await create_spreadsheet(
                user_google_email="user@example.com",
                title="My New Spreadsheet",
            )

            assert "Created spreadsheet" in result
            assert "new_sheet_123" in result


class TestAppendSheetValues:
    """Tests for append_sheet_values."""

    @pytest.mark.asyncio
    async def test_append_values_success(self):
        """Test appending rows to a spreadsheet."""
        mock_service = Mock()
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {
                "updatedRange": "Sheet1!A10:B11",
                "updatedRows": 2,
                "updatedCells": 4,
            }
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.sheets import append_sheet_values

            result = await append_sheet_values(
                user_google_email="user@example.com",
                spreadsheet_id="sheet123",
                range="Sheet1",
                values=[["Row1Col1", "Row1Col2"], ["Row2Col1", "Row2Col2"]],
            )

            assert "Appended to spreadsheet" in result
            assert "Rows added: 2" in result


class TestGetSpreadsheetMetadata:
    """Tests for get_spreadsheet_metadata."""

    @pytest.mark.asyncio
    async def test_get_metadata_success(self):
        """Test getting spreadsheet metadata."""
        mock_service = Mock()
        mock_service.spreadsheets().get().execute.return_value = {
            "properties": {"title": "My Spreadsheet"},
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Sheet1",
                        "gridProperties": {"rowCount": 1000, "columnCount": 26},
                    }
                },
                {
                    "properties": {
                        "sheetId": 1,
                        "title": "Data",
                        "gridProperties": {"rowCount": 500, "columnCount": 10},
                    }
                },
            ],
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.sheets import get_spreadsheet_metadata

            result = await get_spreadsheet_metadata(
                user_google_email="user@example.com",
                spreadsheet_id="sheet123",
            )

            assert "My Spreadsheet" in result
            assert "Sheets (2)" in result
            assert "Sheet1" in result
            assert "Data" in result


# ============================================================================
# Calendar Tests
# ============================================================================


class TestListCalendars:
    """Tests for list_calendars."""

    @pytest.mark.asyncio
    async def test_list_calendars_success(self):
        """Test listing calendars."""
        mock_service = Mock()
        mock_service.calendarList().list().execute.return_value = {
            "items": [
                {
                    "id": "primary",
                    "summary": "My Calendar",
                    "primary": True,
                    "accessRole": "owner",
                },
                {"id": "work@example.com", "summary": "Work", "accessRole": "reader"},
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.calendar import list_calendars

            result = await list_calendars(user_google_email="user@example.com")

            assert "Found 2 calendars" in result
            assert "My Calendar" in result
            assert "(primary)" in result


class TestGetEvents:
    """Tests for get_events."""

    @pytest.mark.asyncio
    async def test_get_events_success(self):
        """Test getting calendar events."""
        mock_service = Mock()
        mock_service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "event123",
                    "summary": "Team Meeting",
                    "start": {"dateTime": "2026-01-15T10:00:00Z"},
                    "end": {"dateTime": "2026-01-15T11:00:00Z"},
                    "htmlLink": "https://calendar.google.com/event?eid=event123",
                }
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.calendar import get_events

            result = await get_events(user_google_email="user@example.com")

            assert "Found 1 events" in result
            assert "Team Meeting" in result
            assert "event123" in result


class TestUpdateEvent:
    """Tests for update_event."""

    @pytest.mark.asyncio
    async def test_update_event_success(self):
        """Test updating a calendar event."""
        mock_service = Mock()
        mock_service.events().patch().execute.return_value = {
            "id": "event123",
            "summary": "Updated Meeting",
            "start": {"dateTime": "2026-01-15T11:00:00Z"},
            "htmlLink": "https://calendar.google.com/event?eid=event123",
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.calendar import update_event

            result = await update_event(
                user_google_email="user@example.com",
                event_id="event123",
                summary="Updated Meeting",
                start_time="2026-01-15T11:00:00Z",
            )

            assert "Updated event" in result
            assert "Updated Meeting" in result


# ============================================================================
# Docs Tests
# ============================================================================


class TestSearchDocs:
    """Tests for search_docs."""

    @pytest.mark.asyncio
    async def test_search_docs_success(self):
        """Test searching Google Docs."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "doc123",
                    "name": "Project Proposal",
                    "modifiedTime": "2026-01-15T10:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc123",
                }
            ]
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.docs import search_docs

            result = await search_docs(
                user_google_email="user@example.com",
                query="proposal",
            )

            assert "Found 1 Google Docs" in result
            assert "Project Proposal" in result


class TestGetDocContent:
    """Tests for get_doc_content."""

    @pytest.mark.asyncio
    async def test_get_doc_content_success(self):
        """Test getting Google Doc content."""
        mock_service = Mock()
        mock_service.documents().get().execute.return_value = {
            "title": "My Document",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Hello, World!\n"}}]
                        }
                    }
                ]
            },
        }

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.docs import get_doc_content

            result = await get_doc_content(
                user_google_email="user@example.com",
                document_id="doc123",
            )

            assert "My Document" in result
            assert "Hello, World!" in result


class TestCreateDoc:
    """Tests for create_doc."""

    @pytest.mark.asyncio
    async def test_create_doc_success(self):
        """Test creating a new Google Doc."""
        mock_service = Mock()
        mock_service.documents().create().execute.return_value = {
            "documentId": "new_doc_123",
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.docs import create_doc

            result = await create_doc(
                user_google_email="user@example.com",
                title="New Document",
                content="Initial content",
            )

            assert "Created Google Doc" in result
            assert "new_doc_123" in result


class TestAppendDocText:
    """Tests for append_doc_text."""

    @pytest.mark.asyncio
    async def test_append_text_success(self):
        """Test appending text to a Google Doc."""
        mock_service = Mock()
        mock_service.documents().get().execute.return_value = {
            "body": {
                "content": [
                    {"endIndex": 100},
                ]
            }
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        with patch(SERVICE_PATCH, return_value=mock_service):
            from google_automation_mcp.tools.docs import append_doc_text

            result = await append_doc_text(
                user_google_email="user@example.com",
                document_id="doc123",
                text="Appended text",
            )

            assert "Appended text to document" in result
            assert "doc123" in result
