"""Tests for Calendar tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.calendar_router import (
    list_calendars,
    get_events,
    create_event,
    update_event,
    delete_event,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.calendar_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestCalendarRouterTools:
    async def test_list_calendars(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "primary", "name": "My Calendar", "is_primary": True},
            {"id": "work", "name": "Work", "is_primary": False},
        ]
        result = await list_calendars(user_google_email="t@t.com")
        assert "Found 2 calendars" in result
        assert "My Calendar" in result
        assert "(primary)" in result

    async def test_list_calendars_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await list_calendars(user_google_email="t@t.com")
        assert "No calendars found" in result

    async def test_get_events(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "e1", "summary": "Meeting", "start": "2026-04-17T10:00:00Z",
             "end": "2026-04-17T11:00:00Z", "location": "Room A", "all_day": False},
        ]
        result = await get_events(user_google_email="t@t.com")
        assert "Found 1 events" in result
        assert "Meeting" in result
        assert "Room A" in result

    async def test_get_events_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await get_events(user_google_email="t@t.com")
        assert "No events found" in result

    async def test_get_events_all_day(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "e2", "summary": "Holiday", "start": "2026-04-17",
             "end": "2026-04-18", "location": "", "all_day": True},
        ]
        result = await get_events(user_google_email="t@t.com")
        assert "All-day" in result

    async def test_create_event(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "e1", "summary": "Lunch", "start": "2026-04-17T12:00:00Z",
            "calendar_id": "primary",
        }
        result = await create_event(
            user_google_email="t@t.com", summary="Lunch",
            start_time="2026-04-17T12:00:00Z", end_time="2026-04-17T13:00:00Z",
        )
        assert "Created event: Lunch" in result

    async def test_update_event(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "e1", "summary": "Updated Meeting", "start": "2026-04-17T10:00:00Z",
            "calendar_id": "primary",
        }
        result = await update_event(
            user_google_email="t@t.com", event_id="e1", summary="Updated Meeting",
        )
        assert "Updated event: Updated Meeting" in result

    async def test_update_event_no_fields(self, mock_call_router):
        result = await update_event(user_google_email="t@t.com", event_id="e1")
        assert "No fields to update" in result
        mock_call_router.assert_not_called()

    async def test_delete_event(self, mock_call_router):
        mock_call_router.return_value = {"deleted": True}
        result = await delete_event(user_google_email="t@t.com", event_id="e1")
        assert "Deleted event: e1" in result
