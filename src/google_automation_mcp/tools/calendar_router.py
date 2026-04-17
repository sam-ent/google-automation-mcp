"""Calendar tools — Apps Script Router backend."""

import logging
from typing import Optional

from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def list_calendars(user_google_email: str) -> str:
    logger.info(f"[list_calendars] User: {user_google_email}")
    results = await call_router(user_google_email, "list_calendars", {})
    if not results:
        return "No calendars found."
    output = [f"Found {len(results)} calendars:"]
    for cal in results:
        primary = " (primary)" if cal.get("is_primary") else ""
        output.append(f"- {cal.get('name', 'Untitled')}{primary}\n  ID: {cal.get('id')}")
    return "\n".join(output)


@handle_errors
async def get_events(
    user_google_email: str, calendar_id: str = "primary",
    max_results: int = 10, time_min: Optional[str] = None,
    time_max: Optional[str] = None, query: Optional[str] = None,
) -> str:
    logger.info(f"[get_events] User: {user_google_email}, Calendar: {calendar_id}")
    results = await call_router(user_google_email, "get_events", {
        "calendar_id": calendar_id, "max_results": max_results,
        "time_min": time_min, "time_max": time_max, "query": query,
    })
    if not results:
        return f"No events found in calendar '{calendar_id}' for the specified time range."
    output = [f"Found {len(results)} events in '{calendar_id}':"]
    for ev in results:
        entry = [f"\n- {ev.get('summary', '(No title)')}", f"  ID: {ev['id']}"]
        if ev.get("all_day"):
            entry.append(f"  Time: All-day: {ev['start']}")
        else:
            entry.append(f"  Time: {ev['start']} - {ev.get('end', '')}")
        if ev.get("location"):
            entry.append(f"  Location: {ev['location']}")
        output.extend(entry)
    return "\n".join(output)


@handle_errors
async def create_event(
    user_google_email: str, summary: str, start_time: str, end_time: str,
    calendar_id: str = "primary", description: Optional[str] = None,
    location: Optional[str] = None, attendees: Optional[str] = None,
    all_day: bool = False,
) -> str:
    logger.info(f"[create_event] User: {user_google_email}, Summary: {summary}")
    result = await call_router(user_google_email, "create_event", {
        "summary": summary, "start_time": start_time, "end_time": end_time,
        "calendar_id": calendar_id, "description": description,
        "location": location, "attendees": attendees, "all_day": all_day,
    })
    output = [
        f"Created event: {result.get('summary', summary)}",
        f"ID: {result['id']}", f"Calendar: {calendar_id}",
        f"Start: {result.get('start', start_time)}",
    ]
    return "\n".join(output)


@handle_errors
async def update_event(
    user_google_email: str, event_id: str, calendar_id: str = "primary",
    summary: Optional[str] = None, start_time: Optional[str] = None,
    end_time: Optional[str] = None, description: Optional[str] = None,
    location: Optional[str] = None, attendees: Optional[str] = None,
    all_day: bool = False,
) -> str:
    logger.info(f"[update_event] User: {user_google_email}, Event: {event_id}")
    if not any([summary, start_time, end_time, description, location, attendees]):
        return "No fields to update. Provide at least one field to modify."
    result = await call_router(user_google_email, "update_event", {
        "event_id": event_id, "calendar_id": calendar_id,
        "summary": summary, "start_time": start_time, "end_time": end_time,
        "description": description, "location": location, "attendees": attendees,
    })
    output = [
        f"Updated event: {result.get('summary', '')}",
        f"ID: {result['id']}", f"Calendar: {calendar_id}",
        f"Start: {result.get('start', '')}",
    ]
    return "\n".join(output)


@handle_errors
async def delete_event(
    user_google_email: str, event_id: str, calendar_id: str = "primary",
) -> str:
    logger.info(f"[delete_event] User: {user_google_email}, Event: {event_id}")
    await call_router(user_google_email, "delete_event", {
        "event_id": event_id, "calendar_id": calendar_id,
    })
    return f"Deleted event: {event_id} from calendar: {calendar_id}"
