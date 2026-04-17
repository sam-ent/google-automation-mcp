"""Tests for Sheets tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.sheets_router import (
    list_spreadsheets,
    get_sheet_values,
    update_sheet_values,
    append_sheet_values,
    create_spreadsheet,
    get_spreadsheet_metadata,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.sheets_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestSheetsRouterTools:
    async def test_list_spreadsheets(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "s1", "name": "Budget", "modified": "2026-04-17", "url": "https://..."}
        ]
        result = await list_spreadsheets(user_google_email="t@t.com")
        assert "Found 1 spreadsheets" in result
        assert "Budget" in result

    async def test_list_spreadsheets_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await list_spreadsheets(user_google_email="t@t.com")
        assert "No spreadsheets found" in result

    async def test_get_sheet_values(self, mock_call_router):
        mock_call_router.return_value = {
            "spreadsheet_id": "s1", "range": "Sheet1",
            "values": [["Name", "Age"], ["Alice", "30"]],
        }
        result = await get_sheet_values(user_google_email="t@t.com", spreadsheet_id="s1")
        assert "Row 1: Name | Age" in result
        assert "Row 2: Alice | 30" in result

    async def test_get_sheet_values_empty(self, mock_call_router):
        mock_call_router.return_value = {"spreadsheet_id": "s1", "range": "Sheet1", "values": []}
        result = await get_sheet_values(user_google_email="t@t.com", spreadsheet_id="s1")
        assert "No data found" in result

    async def test_update_sheet_values(self, mock_call_router):
        mock_call_router.return_value = {
            "range": "Sheet1!A1:B2", "updated_rows": 2, "updated_cells": 4,
        }
        result = await update_sheet_values(
            user_google_email="t@t.com", spreadsheet_id="s1",
            range="Sheet1!A1:B2", values=[["a", "b"], ["c", "d"]],
        )
        assert "Updated spreadsheet" in result
        assert "Cells updated: 4" in result

    async def test_append_sheet_values(self, mock_call_router):
        mock_call_router.return_value = {
            "updated_range": "Sheet1!A3", "updated_rows": 1, "updated_cells": 2,
        }
        result = await append_sheet_values(
            user_google_email="t@t.com", spreadsheet_id="s1",
            range="Sheet1", values=[["x", "y"]],
        )
        assert "Appended to spreadsheet" in result
        assert "Rows added: 1" in result

    async def test_create_spreadsheet(self, mock_call_router):
        mock_call_router.return_value = {
            "spreadsheet_id": "s1", "title": "New Sheet",
            "sheets": ["Sheet1", "Data"], "url": "https://...",
        }
        result = await create_spreadsheet(
            user_google_email="t@t.com", title="New Sheet", sheet_names=["Sheet1", "Data"]
        )
        assert "Created spreadsheet: New Sheet" in result
        assert "Sheet1, Data" in result

    async def test_get_spreadsheet_metadata(self, mock_call_router):
        mock_call_router.return_value = {
            "spreadsheet_id": "s1", "title": "Budget",
            "sheets": [{"title": "Sheet1", "sheet_id": 0, "rows": 100, "cols": 26}],
            "url": "https://...",
        }
        result = await get_spreadsheet_metadata(user_google_email="t@t.com", spreadsheet_id="s1")
        assert "Budget" in result
        assert "Sheet1" in result
        assert "Rows: 100" in result
