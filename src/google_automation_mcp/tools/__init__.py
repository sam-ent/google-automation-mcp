"""
MCP Tools for google-automation-mcp

Provides Apps Script tools and Google Workspace tools (Gmail, Drive, Sheets, Calendar, Docs).

Google Workspace tools are adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Licensed under MIT License.
"""

# Authentication tools - imported directly, not from appscript_tools to avoid circular imports
from .auth_tools import (
    start_google_auth,
    complete_google_auth,
)

# Gmail tools
from .gmail import (
    search_gmail_messages,
    get_gmail_message,
    send_gmail_message,
    list_gmail_labels,
    modify_gmail_labels,
)

# Drive tools
from .drive import (
    search_drive_files,
    list_drive_items,
    get_drive_file_content,
    create_drive_file,
    create_drive_folder,
    delete_drive_file,
    trash_drive_file,
    share_drive_file,
    list_drive_permissions,
    remove_drive_permission,
)

# Sheets tools
from .sheets import (
    list_spreadsheets,
    get_sheet_values,
    update_sheet_values,
    create_spreadsheet,
    append_sheet_values,
    get_spreadsheet_metadata,
)

# Calendar tools
from .calendar import (
    list_calendars,
    get_events,
    create_event,
    delete_event,
    update_event,
)

# Docs tools
from .docs import (
    search_docs,
    get_doc_content,
    create_doc,
    modify_doc_text,
    append_doc_text,
)


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
    # Auth
    "start_google_auth",
    "complete_google_auth",
    # Apps Script Projects
    "list_script_projects",
    "get_script_project",
    "get_script_content",
    "create_script_project",
    "delete_script_project",
    "update_script_content",
    "run_script_function",
    # Deployments
    "create_deployment",
    "list_deployments",
    "update_deployment",
    "delete_deployment",
    # Versions
    "list_versions",
    "create_version",
    "get_version",
    # Processes
    "list_script_processes",
    # Metrics
    "get_script_metrics",
    # Gmail
    "search_gmail_messages",
    "get_gmail_message",
    "send_gmail_message",
    "list_gmail_labels",
    "modify_gmail_labels",
    # Drive
    "search_drive_files",
    "list_drive_items",
    "get_drive_file_content",
    "create_drive_file",
    "create_drive_folder",
    "delete_drive_file",
    "trash_drive_file",
    "share_drive_file",
    "list_drive_permissions",
    "remove_drive_permission",
    # Sheets
    "list_spreadsheets",
    "get_sheet_values",
    "update_sheet_values",
    "create_spreadsheet",
    "append_sheet_values",
    "get_spreadsheet_metadata",
    # Calendar
    "list_calendars",
    "get_events",
    "create_event",
    "delete_event",
    "update_event",
    # Docs
    "search_docs",
    "get_doc_content",
    "create_doc",
    "modify_doc_text",
    "append_doc_text",
]
