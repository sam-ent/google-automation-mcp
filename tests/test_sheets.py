"""
Unit tests for Google Sheets MCP tools

Tests all Sheets tools with mocked API responses.
"""

import pytest
from unittest.mock import MagicMock, patch

from google_automation_mcp.tools.sheets import (
    list_spreadsheets,
    get_sheet_values,
    update_sheet_values,
    create_spreadsheet,
    append_sheet_values,
    get_spreadsheet_metadata,
)


@pytest.fixture
def mock_service():
    """Create a mock Google API service.

    The same mock is used for both Drive and Sheets APIs since
    get_service_for_user returns whichever mock we configure here,
    and MagicMock handles any attribute chain transparently.
    """
    return MagicMock()


@pytest.fixture
def mock_get_service(mock_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_service,
    ) as mock:
        yield mock


class TestListSpreadsheets:
    """Tests for list_spreadsheets tool."""

    @pytest.mark.asyncio
    async def test_list_spreadsheets_success(self, mock_service, mock_get_service):
        mock_response = {
            "files": [
                {
                    "id": "sheet123",
                    "name": "Project Budget",
                    "modifiedTime": "2024-03-20T10:00:00Z",
                    "webViewLink": "https://docs.google.com/spreadsheets/d/sheet123",
                }
            ]
        }
        mock_service.files().list().execute.return_value = mock_response

        result = await list_spreadsheets(
            user_google_email="user@gmail.com", query="Budget"
        )

        assert "Found 1 spreadsheets matching: Budget" in result
        assert "Project Budget (ID: sheet123)" in result
        assert "Modified: 2024-03-20T10:00:00Z" in result

    @pytest.mark.asyncio
    async def test_list_spreadsheets_no_results(self, mock_service, mock_get_service):
        mock_service.files().list().execute.return_value = {"files": []}

        result = await list_spreadsheets(
            user_google_email="user@gmail.com", query="Missing"
        )
        assert "No spreadsheets found matching: Missing" in result


class TestGetSheetValues:
    """Tests for get_sheet_values tool."""

    @pytest.mark.asyncio
    async def test_get_values_success(self, mock_service, mock_get_service):
        mock_response = {
            "values": [["Name", "Role"], ["Alice", "Admin"], ["Bob", "User"]]
        }
        mock_service.spreadsheets().values().get().execute.return_value = mock_response

        result = await get_sheet_values(
            user_google_email="user@gmail.com",
            spreadsheet_id="id123",
            range="A1:B3",
        )

        assert "Spreadsheet: id123" in result
        assert "Rows: 3" in result
        assert "Row 2: Alice | Admin" in result
        assert "Row 3: Bob | User" in result


class TestUpdateSheetValues:
    """Tests for update_sheet_values tool."""

    @pytest.mark.asyncio
    async def test_update_values_success(self, mock_service, mock_get_service):
        mock_response = {
            "updatedCells": 4,
            "updatedRows": 2,
            "updatedRange": "Sheet1!A1:B2",
        }
        mock_service.spreadsheets().values().update().execute.return_value = (
            mock_response
        )

        values = [["X", "Y"], ["1", "2"]]
        result = await update_sheet_values(
            user_google_email="user@gmail.com",
            spreadsheet_id="id123",
            range="A1:B2",
            values=values,
        )

        assert "Cells updated: 4" in result
        assert "Rows updated: 2" in result
        assert "Range: Sheet1!A1:B2" in result


class TestCreateSpreadsheet:
    """Tests for create_spreadsheet tool."""

    @pytest.mark.asyncio
    async def test_create_spreadsheet_success(self, mock_service, mock_get_service):
        mock_response = {
            "spreadsheetId": "new_sheet_789",
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/new_sheet_789/edit",
            "sheets": [
                {"properties": {"title": "Summary"}},
                {"properties": {"title": "Data"}},
            ],
        }
        mock_service.spreadsheets().create().execute.return_value = mock_response

        result = await create_spreadsheet(
            user_google_email="user@gmail.com",
            title="New Report",
            sheet_names=["Summary", "Data"],
        )

        assert "Created spreadsheet: New Report" in result
        assert "ID: new_sheet_789" in result
        assert "Sheets: Summary, Data" in result


class TestAppendSheetValues:
    """Tests for append_sheet_values tool."""

    @pytest.mark.asyncio
    async def test_append_values_success(self, mock_service, mock_get_service):
        mock_response = {
            "updates": {
                "updatedRange": "Sheet1!A10:B10",
                "updatedRows": 1,
                "updatedCells": 2,
            }
        }
        mock_service.spreadsheets().values().append().execute.return_value = (
            mock_response
        )

        result = await append_sheet_values(
            user_google_email="user@gmail.com",
            spreadsheet_id="id123",
            range="Sheet1",
            values=[["New", "Item"]],
        )

        assert "Appended to spreadsheet: id123" in result
        assert "Rows added: 1" in result
        assert "Cells added: 2" in result


class TestGetSpreadsheetMetadata:
    """Tests for get_spreadsheet_metadata tool."""

    @pytest.mark.asyncio
    async def test_get_metadata_success(self, mock_service, mock_get_service):
        mock_response = {
            "properties": {"title": "Company Metrics"},
            "sheets": [
                {
                    "properties": {
                        "title": "Q1",
                        "sheetId": 0,
                        "gridProperties": {"rowCount": 100, "columnCount": 10},
                    }
                }
            ],
        }
        mock_service.spreadsheets().get().execute.return_value = mock_response

        result = await get_spreadsheet_metadata(
            user_google_email="user@gmail.com", spreadsheet_id="id123"
        )

        assert "Spreadsheet: Company Metrics" in result
        assert "Sheets (1):" in result
        assert "Q1 (ID: 0, Rows: 100, Cols: 10)" in result
