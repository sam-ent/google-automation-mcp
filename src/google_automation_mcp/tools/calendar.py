"""
Google Calendar MCP Tools

Provides tools for listing calendars, getting events, and creating events.

Adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Original: gcalendar/calendar_tools.py
Licensed under MIT License.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from googleapiclient.errors import HttpError

from ..auth.service_adapter import with_calendar_service

logger = logging.getLogger(__name__)


def _handle_errors(func):
    """Decorator to handle API errors gracefully."""
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HttpError as e:
            error_msg = str(e)
            if e.resp.status == 401:
                return f"Authentication error: {error_msg}\n\nPlease run start_google_auth to authenticate."
            elif e.resp.status == 403:
                return f"Permission denied: {error_msg}"
            elif e.resp.status == 404:
                return f"Not found: {error_msg}"
            else:
                return f"API error: {error_msg}"
        except Exception as e:
            if "No valid credentials" in str(e):
                return str(e)
            logger.exception(f"Error in {func.__name__}")
            return f"Error: {str(e)}"

    return wrapper


@_handle_errors
@with_calendar_service
async def list_calendars(
    service,
    user_google_email: str,
) -> str:
    """
    List all calendars accessible to the user.

    Args:
        user_google_email: The user's Google email address

    Returns:
        str: Formatted list of calendars
    """
    logger.info(f"[list_calendars] User: {user_google_email}")

    response = await asyncio.to_thread(service.calendarList().list().execute)

    calendars = response.get("items", [])
    if not calendars:
        return "No calendars found."

    output = [f"Found {len(calendars)} calendars:"]

    for cal in calendars:
        is_primary = " (primary)" if cal.get("primary") else ""
        access_role = cal.get("accessRole", "unknown")
        output.append(
            f"- {cal.get('summary', 'Untitled')}{is_primary}\n"
            f"  ID: {cal.get('id')}\n"
            f"  Access: {access_role}"
        )

    return "\n".join(output)


@_handle_errors
@with_calendar_service
async def get_events(
    service,
    user_google_email: str,
    calendar_id: str = "primary",
    max_results: int = 10,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    query: Optional[str] = None,
) -> str:
    """
    Get events from a calendar.

    Args:
        user_google_email: The user's Google email address
        calendar_id: Calendar ID (default: 'primary')
        max_results: Maximum number of events to return (default: 10)
        time_min: Start time in ISO format (default: now)
        time_max: End time in ISO format (default: 7 days from now)
        query: Optional search query string

    Returns:
        str: Formatted list of events
    """
    logger.info(f"[get_events] User: {user_google_email}, Calendar: {calendar_id}")

    # Default time range: now to 7 days from now
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    if not time_max:
        time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

    request_params = {
        "calendarId": calendar_id,
        "timeMin": time_min,
        "timeMax": time_max,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    if query:
        request_params["q"] = query

    response = await asyncio.to_thread(service.events().list(**request_params).execute)

    events = response.get("items", [])
    if not events:
        return (
            f"No events found in calendar '{calendar_id}' for the specified time range."
        )

    output = [f"Found {len(events)} events in '{calendar_id}':"]

    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})

        # Handle all-day vs timed events
        if "date" in start:
            start_str = start["date"]
            end_str = end.get("date", "")
            time_str = f"All-day: {start_str}"
            if end_str and end_str != start_str:
                time_str = f"All-day: {start_str} to {end_str}"
        else:
            start_str = start.get("dateTime", "Unknown")
            end_str = end.get("dateTime", "")
            time_str = f"{start_str}"
            if end_str:
                time_str = f"{start_str} - {end_str}"

        summary = event.get("summary", "(No title)")
        location = event.get("location", "")
        event_id = event.get("id", "Unknown")

        entry = [f"\n- {summary}", f"  ID: {event_id}", f"  Time: {time_str}"]
        if location:
            entry.append(f"  Location: {location}")
        if event.get("htmlLink"):
            entry.append(f"  Link: {event.get('htmlLink')}")

        output.extend(entry)

    return "\n".join(output)


@_handle_errors
@with_calendar_service
async def create_event(
    service,
    user_google_email: str,
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[str] = None,
    all_day: bool = False,
) -> str:
    """
    Create a new calendar event.

    Args:
        user_google_email: The user's Google email address
        summary: Event title
        start_time: Start time in ISO format (e.g., "2024-01-15T09:00:00") or date for all-day (e.g., "2024-01-15")
        end_time: End time in ISO format (e.g., "2024-01-15T10:00:00") or date for all-day (e.g., "2024-01-16")
        calendar_id: Calendar ID (default: 'primary')
        description: Optional event description
        location: Optional event location
        attendees: Optional comma-separated list of attendee emails
        all_day: If True, create an all-day event (use date format for start/end)

    Returns:
        str: Confirmation with event details
    """
    logger.info(f"[create_event] User: {user_google_email}, Summary: {summary}")

    event_body = {
        "summary": summary,
    }

    if all_day:
        event_body["start"] = {"date": start_time}
        event_body["end"] = {"date": end_time}
    else:
        event_body["start"] = {"dateTime": start_time}
        event_body["end"] = {"dateTime": end_time}

    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location

    if attendees:
        attendee_list = [email.strip() for email in attendees.split(",")]
        event_body["attendees"] = [{"email": email} for email in attendee_list]

    created_event = await asyncio.to_thread(
        service.events().insert(calendarId=calendar_id, body=event_body).execute
    )

    output = [
        f"Created event: {created_event.get('summary')}",
        f"ID: {created_event.get('id')}",
        f"Calendar: {calendar_id}",
    ]

    start = created_event.get("start", {})
    if "date" in start:
        output.append(f"Date: {start['date']}")
    else:
        output.append(f"Start: {start.get('dateTime')}")

    if created_event.get("htmlLink"):
        output.append(f"Link: {created_event.get('htmlLink')}")

    return "\n".join(output)


@_handle_errors
@with_calendar_service
async def delete_event(
    service,
    user_google_email: str,
    event_id: str,
    calendar_id: str = "primary",
) -> str:
    """
    Delete a calendar event.

    Args:
        user_google_email: The user's Google email address
        event_id: The event ID to delete
        calendar_id: Calendar ID (default: 'primary')

    Returns:
        str: Confirmation message
    """
    logger.info(f"[delete_event] User: {user_google_email}, Event: {event_id}")

    await asyncio.to_thread(
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute
    )

    return f"Deleted event: {event_id} from calendar: {calendar_id}"


@_handle_errors
@with_calendar_service
async def update_event(
    service,
    user_google_email: str,
    event_id: str,
    calendar_id: str = "primary",
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[str] = None,
    all_day: bool = False,
) -> str:
    """
    Update an existing calendar event.

    Args:
        user_google_email: The user's Google email address
        event_id: The event ID to update
        calendar_id: Calendar ID (default: 'primary')
        summary: New event title (optional)
        start_time: New start time in ISO format (optional)
        end_time: New end time in ISO format (optional)
        description: New description (optional)
        location: New location (optional)
        attendees: New comma-separated list of attendee emails (optional)
        all_day: If True and updating times, use date format

    Returns:
        str: Confirmation with updated event details
    """
    logger.info(f"[update_event] User: {user_google_email}, Event: {event_id}")

    # Build patch body with only provided fields
    patch_body = {}

    if summary is not None:
        patch_body["summary"] = summary
    if description is not None:
        patch_body["description"] = description
    if location is not None:
        patch_body["location"] = location

    if start_time is not None:
        if all_day:
            patch_body["start"] = {"date": start_time}
        else:
            patch_body["start"] = {"dateTime": start_time}

    if end_time is not None:
        if all_day:
            patch_body["end"] = {"date": end_time}
        else:
            patch_body["end"] = {"dateTime": end_time}

    if attendees is not None:
        attendee_list = [email.strip() for email in attendees.split(",")]
        patch_body["attendees"] = [{"email": email} for email in attendee_list]

    if not patch_body:
        return "No fields to update. Provide at least one field to modify."

    updated_event = await asyncio.to_thread(
        service.events()
        .patch(calendarId=calendar_id, eventId=event_id, body=patch_body)
        .execute
    )

    output = [
        f"Updated event: {updated_event.get('summary')}",
        f"ID: {updated_event.get('id')}",
        f"Calendar: {calendar_id}",
    ]

    start = updated_event.get("start", {})
    if "date" in start:
        output.append(f"Date: {start['date']}")
    else:
        output.append(f"Start: {start.get('dateTime')}")

    if updated_event.get("htmlLink"):
        output.append(f"Link: {updated_event.get('htmlLink')}")

    return "\n".join(output)
