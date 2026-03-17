"""
Google Tasks MCP Tools

Provides tools for managing task lists and tasks.
"""

import asyncio
import logging
from typing import Optional

from ..auth.service_adapter import with_tasks_service
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
@with_tasks_service
async def list_task_lists(
    service,
    user_google_email: str,
    max_results: int = 20,
) -> str:
    """
    List all task lists for the user.

    Args:
        user_google_email: The user's Google email address
        max_results: Maximum number of task lists to return (default: 20)

    Returns:
        str: Formatted list of task lists
    """
    logger.info(f"[list_task_lists] User: {user_google_email}")

    response = await asyncio.to_thread(
        service.tasklists().list(maxResults=max_results).execute
    )

    task_lists = response.get("items", [])
    if not task_lists:
        return "No task lists found."

    output = [f"Found {len(task_lists)} task lists:"]
    for tl in task_lists:
        output.append(
            f"- {tl.get('title', 'Untitled')}\n"
            f"  ID: {tl.get('id')}\n"
            f"  Updated: {tl.get('updated', 'Unknown')}"
        )

    return "\n".join(output)


@handle_errors
@with_tasks_service
async def get_tasks(
    service,
    user_google_email: str,
    tasklist_id: str = "@default",
    max_results: int = 20,
    show_completed: bool = True,
    show_hidden: bool = False,
) -> str:
    """
    Get tasks from a task list.

    Args:
        user_google_email: The user's Google email address
        tasklist_id: Task list ID (default: '@default' for the user's default list)
        max_results: Maximum number of tasks to return (default: 20)
        show_completed: Whether to include completed tasks (default: True)
        show_hidden: Whether to include hidden tasks (default: False)

    Returns:
        str: Formatted list of tasks
    """
    logger.info(f"[get_tasks] User: {user_google_email}, List: {tasklist_id}")

    response = await asyncio.to_thread(
        service.tasks()
        .list(
            tasklist=tasklist_id,
            maxResults=max_results,
            showCompleted=show_completed,
            showHidden=show_hidden,
        )
        .execute
    )

    tasks = response.get("items", [])
    if not tasks:
        return f"No tasks found in list '{tasklist_id}'."

    output = [f"Found {len(tasks)} tasks:"]
    for task in tasks:
        status = "✓" if task.get("status") == "completed" else "○"
        title = task.get("title", "(No title)")
        due = task.get("due", "")
        notes = task.get("notes", "")
        task_id = task.get("id", "Unknown")

        entry = [f"\n{status} {title}", f"  ID: {task_id}"]
        if due:
            entry.append(f"  Due: {due}")
        if notes:
            entry.append(f"  Notes: {notes[:100]}")

        output.extend(entry)

    return "\n".join(output)


@handle_errors
@with_tasks_service
async def create_task(
    service,
    user_google_email: str,
    title: str,
    tasklist_id: str = "@default",
    notes: Optional[str] = None,
    due: Optional[str] = None,
) -> str:
    """
    Create a new task.

    Args:
        user_google_email: The user's Google email address
        title: Task title
        tasklist_id: Task list ID (default: '@default')
        notes: Optional task notes/description
        due: Optional due date in RFC 3339 format (e.g., "2024-01-15T00:00:00.000Z")

    Returns:
        str: Confirmation with task details
    """
    logger.info(f"[create_task] User: {user_google_email}, Title: {title}")

    body = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        body["due"] = due

    created = await asyncio.to_thread(
        service.tasks().insert(tasklist=tasklist_id, body=body).execute
    )

    output = [
        f"Created task: {created.get('title')}",
        f"ID: {created.get('id')}",
        f"List: {tasklist_id}",
        f"Status: {created.get('status')}",
    ]
    if created.get("due"):
        output.append(f"Due: {created.get('due')}")

    return "\n".join(output)


@handle_errors
@with_tasks_service
async def update_task(
    service,
    user_google_email: str,
    task_id: str,
    tasklist_id: str = "@default",
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """
    Update an existing task.

    Args:
        user_google_email: The user's Google email address
        task_id: The task ID to update
        tasklist_id: Task list ID (default: '@default')
        title: New task title (optional)
        notes: New notes/description (optional)
        due: New due date in RFC 3339 format (optional)
        status: New status - "needsAction" or "completed" (optional)

    Returns:
        str: Confirmation with updated task details
    """
    logger.info(f"[update_task] User: {user_google_email}, Task: {task_id}")

    # Fetch existing task first
    existing = await asyncio.to_thread(
        service.tasks().get(tasklist=tasklist_id, task=task_id).execute
    )

    if title is not None:
        existing["title"] = title
    if notes is not None:
        existing["notes"] = notes
    if due is not None:
        existing["due"] = due
    if status is not None:
        existing["status"] = status

    updated = await asyncio.to_thread(
        service.tasks()
        .update(tasklist=tasklist_id, task=task_id, body=existing)
        .execute
    )

    output = [
        f"Updated task: {updated.get('title')}",
        f"ID: {updated.get('id')}",
        f"Status: {updated.get('status')}",
    ]
    if updated.get("due"):
        output.append(f"Due: {updated.get('due')}")

    return "\n".join(output)


@handle_errors
@with_tasks_service
async def delete_task(
    service,
    user_google_email: str,
    task_id: str,
    tasklist_id: str = "@default",
) -> str:
    """
    Delete a task.

    Args:
        user_google_email: The user's Google email address
        task_id: The task ID to delete
        tasklist_id: Task list ID (default: '@default')

    Returns:
        str: Confirmation message
    """
    logger.info(f"[delete_task] User: {user_google_email}, Task: {task_id}")

    await asyncio.to_thread(
        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute
    )

    return f"Deleted task: {task_id} from list: {tasklist_id}"


@handle_errors
@with_tasks_service
async def complete_task(
    service,
    user_google_email: str,
    task_id: str,
    tasklist_id: str = "@default",
) -> str:
    """
    Mark a task as completed.

    Args:
        user_google_email: The user's Google email address
        task_id: The task ID to complete
        tasklist_id: Task list ID (default: '@default')

    Returns:
        str: Confirmation message
    """
    logger.info(f"[complete_task] User: {user_google_email}, Task: {task_id}")

    existing = await asyncio.to_thread(
        service.tasks().get(tasklist=tasklist_id, task=task_id).execute
    )
    existing["status"] = "completed"

    updated = await asyncio.to_thread(
        service.tasks()
        .update(tasklist=tasklist_id, task=task_id, body=existing)
        .execute
    )

    return f"Completed task: {updated.get('title')} (ID: {updated.get('id')})"
