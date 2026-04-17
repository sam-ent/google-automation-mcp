"""
MCP Tools for google-automation-mcp

Provides Apps Script tools and Google Workspace tools (Gmail, Drive, Sheets, Calendar, Docs).

Google Workspace tools are adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Licensed under MIT License.
"""

import importlib
import os

# Authentication tools - imported directly, not from appscript_tools to avoid circular imports
from .auth_tools import (
    start_google_auth,
    complete_google_auth,
)


def _use_router() -> bool:
    override = os.getenv("MCP_USE_ROUTER", "auto")
    if override == "true":
        return True
    if override == "false":
        return False
    from ..auth.oauth_config import is_oauth_configured

    return not is_oauth_configured()


_ROUTER = _use_router()


def _mod(router_name: str, rest_name: str, use_router: bool = _ROUTER):
    return importlib.import_module(
        f".{router_name}" if use_router else f".{rest_name}", __package__
    )


# Gmail
_m = _mod("gmail_router", "gmail")
search_gmail_messages = _m.search_gmail_messages
get_gmail_message = _m.get_gmail_message
send_gmail_message = _m.send_gmail_message
list_gmail_labels = _m.list_gmail_labels
modify_gmail_labels = _m.modify_gmail_labels

# Drive
_m = _mod("drive_router", "drive")
search_drive_files = _m.search_drive_files
list_drive_items = _m.list_drive_items
get_drive_file_content = _m.get_drive_file_content
create_drive_file = _m.create_drive_file
create_drive_folder = _m.create_drive_folder
delete_drive_file = _m.delete_drive_file
trash_drive_file = _m.trash_drive_file
share_drive_file = _m.share_drive_file
list_drive_permissions = _m.list_drive_permissions
remove_drive_permission = _m.remove_drive_permission

# Sheets
_m = _mod("sheets_router", "sheets")
list_spreadsheets = _m.list_spreadsheets
get_sheet_values = _m.get_sheet_values
update_sheet_values = _m.update_sheet_values
create_spreadsheet = _m.create_spreadsheet
append_sheet_values = _m.append_sheet_values
get_spreadsheet_metadata = _m.get_spreadsheet_metadata

# Calendar
_m = _mod("calendar_router", "calendar")
list_calendars = _m.list_calendars
get_events = _m.get_events
create_event = _m.create_event
delete_event = _m.delete_event
update_event = _m.update_event

# Docs
_m = _mod("docs_router", "docs")
search_docs = _m.search_docs
get_doc_content = _m.get_doc_content
create_doc = _m.create_doc
modify_doc_text = _m.modify_doc_text
append_doc_text = _m.append_doc_text

# Tasks
_m = _mod("tasks_router", "tasks")
list_task_lists = _m.list_task_lists
get_tasks = _m.get_tasks
create_task = _m.create_task
update_task = _m.update_task
delete_task = _m.delete_task
complete_task = _m.complete_task

# Forms
_m = _mod("forms_router", "forms")
get_form = _m.get_form
get_form_responses = _m.get_form_responses
create_form = _m.create_form
add_form_question = _m.add_form_question

del _m, _ROUTER


# Lazy imports for Apps Script tools to avoid circular imports
def __getattr__(name):
    """Lazy import Apps Script tools to avoid circular dependencies."""
    _appscript_tools = [
        "list_script_projects",
        "get_script_project",
        "get_script_content",
        "create_script_project",
        "delete_script_project",
        "update_script_content",
        "run_script_function",
        "create_deployment",
        "list_deployments",
        "update_deployment",
        "delete_deployment",
        "list_versions",
        "create_version",
        "get_version",
        "list_script_processes",
        "get_script_metrics",
    ]
    if name in _appscript_tools:
        from .. import appscript_tools

        return getattr(appscript_tools, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "start_google_auth", "complete_google_auth",
    "list_script_projects", "get_script_project", "get_script_content",
    "create_script_project", "delete_script_project", "update_script_content",
    "run_script_function", "create_deployment", "list_deployments",
    "update_deployment", "delete_deployment", "list_versions", "create_version",
    "get_version", "list_script_processes", "get_script_metrics",
    "search_gmail_messages", "get_gmail_message", "send_gmail_message",
    "list_gmail_labels", "modify_gmail_labels",
    "search_drive_files", "list_drive_items", "get_drive_file_content",
    "create_drive_file", "create_drive_folder", "delete_drive_file",
    "trash_drive_file", "share_drive_file", "list_drive_permissions",
    "remove_drive_permission",
    "list_spreadsheets", "get_sheet_values", "update_sheet_values",
    "create_spreadsheet", "append_sheet_values", "get_spreadsheet_metadata",
    "list_calendars", "get_events", "create_event", "delete_event", "update_event",
    "search_docs", "get_doc_content", "create_doc", "modify_doc_text", "append_doc_text",
    "list_task_lists", "get_tasks", "create_task", "update_task", "delete_task", "complete_task",
    "get_form", "get_form_responses", "create_form", "add_form_question",
]
