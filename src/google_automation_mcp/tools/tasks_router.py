"""Tasks tools — Apps Script Router backend."""

import logging
from typing import Optional

from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def list_task_lists(
    user_google_email: str, max_results: int = 20,
) -> str:
    logger.info(f"[list_task_lists] User: {user_google_email}")
    results = await call_router(user_google_email, "list_task_lists", {
        "max_results": max_results,
    })
    if not results:
        return "No task lists found."
    output = [f"Found {len(results)} task lists:"]
    for tl in results:
        output.append(
            f"- {tl.get('title', 'Untitled')}\n"
            f"  ID: {tl.get('id')}\n"
            f"  Updated: {tl.get('updated', 'Unknown')}"
        )
    return "\n".join(output)


@handle_errors
async def get_tasks(
    user_google_email: str, tasklist_id: str = "@default",
    max_results: int = 20, show_completed: bool = True,
    show_hidden: bool = False,
) -> str:
    logger.info(f"[get_tasks] User: {user_google_email}, List: {tasklist_id}")
    results = await call_router(user_google_email, "get_tasks", {
        "tasklist_id": tasklist_id, "max_results": max_results,
        "show_completed": show_completed, "show_hidden": show_hidden,
    })
    if not results:
        return f"No tasks found in list '{tasklist_id}'."
    output = [f"Found {len(results)} tasks:"]
    for task in results:
        status = "✓" if task.get("status") == "completed" else "○"
        entry = [f"\n{status} {task.get('title', '(No title)')}", f"  ID: {task.get('id', 'Unknown')}"]
        if task.get("due"):
            entry.append(f"  Due: {task['due']}")
        if task.get("notes"):
            entry.append(f"  Notes: {task['notes'][:100]}")
        output.extend(entry)
    return "\n".join(output)


@handle_errors
async def create_task(
    user_google_email: str, title: str, tasklist_id: str = "@default",
    notes: Optional[str] = None, due: Optional[str] = None,
) -> str:
    logger.info(f"[create_task] User: {user_google_email}, Title: {title}")
    result = await call_router(user_google_email, "create_task", {
        "title": title, "tasklist_id": tasklist_id, "notes": notes, "due": due,
    })
    output = [
        f"Created task: {result.get('title', title)}",
        f"ID: {result.get('id')}", f"List: {tasklist_id}",
        f"Status: {result.get('status', 'needsAction')}",
    ]
    if result.get("due"):
        output.append(f"Due: {result['due']}")
    return "\n".join(output)


@handle_errors
async def update_task(
    user_google_email: str, task_id: str, tasklist_id: str = "@default",
    title: Optional[str] = None, notes: Optional[str] = None,
    due: Optional[str] = None, status: Optional[str] = None,
) -> str:
    logger.info(f"[update_task] User: {user_google_email}, Task: {task_id}")
    result = await call_router(user_google_email, "update_task", {
        "task_id": task_id, "tasklist_id": tasklist_id,
        "title": title, "notes": notes, "due": due, "status": status,
    })
    output = [
        f"Updated task: {result.get('title', '')}",
        f"ID: {result.get('id')}", f"Status: {result.get('status', '')}",
    ]
    if result.get("due"):
        output.append(f"Due: {result['due']}")
    return "\n".join(output)


@handle_errors
async def delete_task(
    user_google_email: str, task_id: str, tasklist_id: str = "@default",
) -> str:
    logger.info(f"[delete_task] User: {user_google_email}, Task: {task_id}")
    await call_router(user_google_email, "delete_task", {
        "task_id": task_id, "tasklist_id": tasklist_id,
    })
    return f"Deleted task: {task_id} from list: {tasklist_id}"


@handle_errors
async def complete_task(
    user_google_email: str, task_id: str, tasklist_id: str = "@default",
) -> str:
    logger.info(f"[complete_task] User: {user_google_email}, Task: {task_id}")
    result = await call_router(user_google_email, "complete_task", {
        "task_id": task_id, "tasklist_id": tasklist_id,
    })
    return f"Completed task: {result.get('title', '')} (ID: {result.get('id', task_id)})"
