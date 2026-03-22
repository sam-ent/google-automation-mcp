"""
Unit tests for Google Calendar MCP tools

Tests all Calendar tools with mocked API responses.
"""

import pytest
from unittest.mock import MagicMock, patch

from google_automation_mcp.tools.calendar import (
    list_calendars,
    get_events,
    create_event,
    delete_event,
    update_event,
)


@pytest.fixture
def mock_calendar_service():
    """Create a mock Calendar API service."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_get_service(mock_calendar_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_calendar_service,
    ) as mock:
        yield mock


class TestCalendarTools:
    """Tests for Google Calendar MCP tools."""

    @pytest.mark.asyncio
    async def test_list_calendars_success(self, mock_calendar_service, mock_get_service):
        """Test listing calendars returns formatted output."""
        mock_response = {
            "items": [
                {
                    "id": "primary",
                    "summary": "Primary Calendar",
                    "primary": True,
                    "accessRole": "owner",
                },
                {
                    "id": "cal_123",
                    "summary": "Work Calendar",
                    "accessRole": "reader",
                },
            ]
        }
        mock_calendar_service.calendarList().list().execute.return_value = mock_response

        result = await list_calendars(user_google_email="test@example.com")

        assert "Found 2 calendars" in result
        assert "Primary Calendar (primary)" in result
        assert "Work Calendar" in result
        assert "Access: owner" in result
        assert "Access: reader" in result

    @pytest.mark.asyncio
    async def test_list_calendars_empty(self, mock_calendar_service, mock_get_service):
        """Test listing calendars when none are found."""
        mock_calendar_service.calendarList().list().execute.return_value = {
            "items": []
        }

        result = await list_calendars(user_google_email="test@example.com")
        assert "No calendars found." in result

    @pytest.mark.asyncio
    async def test_get_events_success(self, mock_calendar_service, mock_get_service):
        """Test retrieving events from a calendar."""
        mock_response = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Team Sync",
                    "start": {"dateTime": "2024-01-15T10:00:00Z"},
                    "end": {"dateTime": "2024-01-15T11:00:00Z"},
                    "location": "Conference Room A",
                    "htmlLink": "https://calendar.google.com/event1",
                },
                {
                    "id": "event2",
                    "summary": "Vacation",
                    "start": {"date": "2024-01-16"},
                    "end": {"date": "2024-01-17"},
                },
            ]
        }
        mock_calendar_service.events().list().execute.return_value = mock_response

        result = await get_events(
            user_google_email="test@example.com", calendar_id="primary"
        )

        assert "Found 2 events in 'primary'" in result
        assert "Team Sync" in result
        assert "Location: Conference Room A" in result
        assert "All-day: 2024-01-16 to 2024-01-17" in result
        assert "https://calendar.google.com/event1" in result

    @pytest.mark.asyncio
    async def test_get_events_with_query(self, mock_calendar_service, mock_get_service):
        """Test retrieving events with a search query."""
        mock_calendar_service.events().list().execute.return_value = {"items": []}

        result = await get_events(
            user_google_email="test@example.com", query="Lunch"
        )

        # Verify query parameter was passed to API
        args, kwargs = mock_calendar_service.events().list.call_args
        assert kwargs["q"] == "Lunch"

    @pytest.mark.asyncio
    async def test_create_event_timed(self, mock_calendar_service, mock_get_service):
        """Test creating a timed calendar event."""
        mock_response = {
            "id": "new_event_123",
            "summary": "New Meeting",
            "start": {"dateTime": "2024-01-15T09:00:00Z"},
            "htmlLink": "https://calendar.google.com/new",
        }
        mock_calendar_service.events().insert().execute.return_value = mock_response

        result = await create_event(
            user_google_email="test@example.com",
            summary="New Meeting",
            start_time="2024-01-15T09:00:00Z",
            end_time="2024-01-15T10:00:00Z",
            description="Project kickoff",
            location="Remote",
            attendees="user1@example.com, user2@example.com",
        )

        assert "Created event: New Meeting" in result
        assert "ID: new_event_123" in result

        # Verify body construction
        args, kwargs = mock_calendar_service.events().insert.call_args
        body = kwargs["body"]
        assert body["summary"] == "New Meeting"
        assert body["start"] == {"dateTime": "2024-01-15T09:00:00Z"}
        assert len(body["attendees"]) == 2
        assert body["attendees"][0]["email"] == "user1@example.com"

    @pytest.mark.asyncio
    async def test_create_event_all_day(self, mock_calendar_service, mock_get_service):
        """Test creating an all-day calendar event."""
        mock_response = {
            "id": "allday_123",
            "summary": "Holiday",
            "start": {"date": "2024-12-25"},
        }
        mock_calendar_service.events().insert().execute.return_value = mock_response

        result = await create_event(
            user_google_email="test@example.com",
            summary="Holiday",
            start_time="2024-12-25",
            end_time="2024-12-26",
            all_day=True,
        )

        assert "Date: 2024-12-25" in result
        args, kwargs = mock_calendar_service.events().insert.call_args
        assert kwargs["body"]["start"] == {"date": "2024-12-25"}

    @pytest.mark.asyncio
    async def test_delete_event(self, mock_calendar_service, mock_get_service):
        """Test deleting an event."""
        mock_calendar_service.events().delete().execute.return_value = {}

        result = await delete_event(
            user_google_email="test@example.com",
            event_id="evt_123",
            calendar_id="primary",
        )

        assert "Deleted event: evt_123 from calendar: primary" in result
        mock_calendar_service.events().delete.assert_called_with(
            calendarId="primary", eventId="evt_123"
        )

    @pytest.mark.asyncio
    async def test_update_event_success(self, mock_calendar_service, mock_get_service):
        """Test updating an existing event."""
        mock_response = {
            "id": "evt_123",
            "summary": "Updated Meeting",
            "start": {"dateTime": "2024-01-15T11:00:00Z"},
        }
        mock_calendar_service.events().patch().execute.return_value = mock_response

        result = await update_event(
            user_google_email="test@example.com",
            event_id="evt_123",
            summary="Updated Meeting",
            location="New Room",
        )

        assert "Updated event: Updated Meeting" in result

        # Verify patch body
        args, kwargs = mock_calendar_service.events().patch.call_args
        assert kwargs["calendarId"] == "primary"
        assert kwargs["eventId"] == "evt_123"
        assert kwargs["body"]["summary"] == "Updated Meeting"
        assert kwargs["body"]["location"] == "New Room"

    @pytest.mark.asyncio
    async def test_update_event_no_fields(self, mock_calendar_service, mock_get_service):
        """Test update call with no fields provided."""
        result = await update_event(
            user_google_email="test@example.com", event_id="evt_123"
        )
        assert "No fields to update" in result
