"""
Apps Script MCP Server

MCP server for Google Apps Script and Google Workspace with unified authentication.
Supports clasp (no GCP project needed), OAuth 2.0, and OAuth 2.1.
"""

import logging

from fastmcp import FastMCP

from . import __version__
from .tools import (
    # Authentication
    start_google_auth,
    complete_google_auth,
    # Projects
    list_script_projects,
    get_script_project,
    get_script_content,
    create_script_project,
    delete_script_project,
    update_script_content,
    run_script_function,
    # Deployments
    create_deployment,
    list_deployments,
    update_deployment,
    delete_deployment,
    # Versions
    list_versions,
    create_version,
    get_version,
    # Processes
    list_script_processes,
    # Metrics
    get_script_metrics,
)

# Google Workspace Tools
from .tools import (
    # Gmail
    search_gmail_messages,
    get_gmail_message,
    send_gmail_message,
    list_gmail_labels,
    modify_gmail_labels,
    # Drive
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
    # Sheets
    list_spreadsheets,
    get_sheet_values,
    update_sheet_values,
    create_spreadsheet,
    append_sheet_values,
    get_spreadsheet_metadata,
    # Calendar
    list_calendars,
    get_events,
    create_event,
    delete_event,
    update_event,
    # Docs
    search_docs,
    get_doc_content,
    create_doc,
    modify_doc_text,
    append_doc_text,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("Apps Script MCP")


# ============================================================================
# Authentication Tools
# ============================================================================


@mcp.tool()
async def start_google_auth_tool() -> str:
    """
    Start Google OAuth authentication flow.

    Returns an authorization URL that must be opened in a browser.
    After authorizing, call complete_google_auth with the redirect URL.
    """
    return await start_google_auth()


@mcp.tool()
async def complete_google_auth_tool(redirect_url: str) -> str:
    """
    Complete the Google OAuth flow with the redirect URL.

    Args:
        redirect_url: The full URL from the browser after authorization
                      (looks like: http://localhost/?code=4/0A...&scope=...)
    """
    return await complete_google_auth(redirect_url)


# ============================================================================
# Project Tools
# ============================================================================


@mcp.tool()
async def list_script_projects_tool(
    page_size: int = 50,
    page_token: str = "",
) -> str:
    """
    List Google Apps Script projects accessible to the user.

    Args:
        page_size: Number of results per page (default: 50)
        page_token: Token for pagination (optional)
    """
    return await list_script_projects(
        page_size=page_size,
        page_token=page_token if page_token else None,
    )


@mcp.tool()
async def get_script_project_tool(script_id: str) -> str:
    """
    Retrieve complete project details including all source files.

    Args:
        script_id: The script project ID
    """
    return await get_script_project(script_id)


@mcp.tool()
async def get_script_content_tool(script_id: str, file_name: str) -> str:
    """
    Retrieve content of a specific file within a project.

    Args:
        script_id: The script project ID
        file_name: Name of the file to retrieve (e.g., "Code", "appsscript")
    """
    return await get_script_content(script_id, file_name)


@mcp.tool()
async def create_script_project_tool(
    title: str,
    parent_id: str = "",
) -> str:
    """
    Create a new Apps Script project (standalone or bound to a document).

    Args:
        title: Project title
        parent_id: Optional - the Google Drive ID of a container document to bind to.
                   Leave empty for standalone scripts.

                   To create a BOUND script, pass the ID of:
                   - Google Sheet (from the URL: docs.google.com/spreadsheets/d/{ID}/edit)
                   - Google Doc (from the URL: docs.google.com/document/d/{ID}/edit)
                   - Google Form (from the URL: docs.google.com/forms/d/{ID}/edit)
                   - Google Slides (from the URL: docs.google.com/presentation/d/{ID}/edit)

                   Bound scripts can use document-specific features like custom menus,
                   onOpen triggers, and getActiveSpreadsheet().
    """
    return await create_script_project(
        title=title,
        parent_id=parent_id if parent_id else None,
    )


@mcp.tool()
async def delete_script_project_tool(script_id: str) -> str:
    """
    Delete an Apps Script project.

    WARNING: This permanently deletes the script project. The action cannot be undone.

    Args:
        script_id: The script project ID to delete
    """
    return await delete_script_project(script_id)


@mcp.tool()
async def update_script_content_tool(
    script_id: str,
    files: list,
) -> str:
    """
    Update or create files in a script project.

    Args:
        script_id: The script project ID
        files: List of file objects, each with:
               - name: File name (e.g., "Code", "Utils")
               - type: File type ("SERVER_JS", "HTML", or "JSON")
               - source: File content as string

    Example files parameter:
        [{"name": "Code", "type": "SERVER_JS", "source": "function main() { Logger.log('Hello'); }"}]
    """
    return await update_script_content(script_id, files)


@mcp.tool()
async def run_script_function_tool(
    script_id: str,
    function_name: str,
    parameters: list = None,
    dev_mode: bool = False,
) -> str:
    """
    Execute a function in a deployed script.

    Note: Requires the script to be deployed as "API Executable" in the Apps Script editor.
    See README for setup instructions.

    Args:
        script_id: The script project ID
        function_name: Name of function to execute
        parameters: Optional list of parameters to pass to the function
        dev_mode: If True, run latest code; if False, run deployed version
    """
    return await run_script_function(script_id, function_name, parameters, dev_mode)


# ============================================================================
# Deployment Tools
# ============================================================================


@mcp.tool()
async def create_deployment_tool(
    script_id: str,
    description: str,
    version_description: str = "",
) -> str:
    """
    Create a new deployment of the script.

    Args:
        script_id: The script project ID
        description: Deployment description
        version_description: Optional version description (defaults to deployment description)
    """
    return await create_deployment(
        script_id=script_id,
        description=description,
        version_description=version_description if version_description else None,
    )


@mcp.tool()
async def list_deployments_tool(script_id: str) -> str:
    """
    List all deployments for a script project.

    Args:
        script_id: The script project ID
    """
    return await list_deployments(script_id)


@mcp.tool()
async def update_deployment_tool(
    script_id: str,
    deployment_id: str,
    description: str = "",
) -> str:
    """
    Update an existing deployment configuration.

    Args:
        script_id: The script project ID
        deployment_id: The deployment ID to update
        description: New description for the deployment
    """
    return await update_deployment(
        script_id=script_id,
        deployment_id=deployment_id,
        description=description if description else None,
    )


@mcp.tool()
async def delete_deployment_tool(script_id: str, deployment_id: str) -> str:
    """
    Delete a deployment.

    Args:
        script_id: The script project ID
        deployment_id: The deployment ID to delete
    """
    return await delete_deployment(script_id, deployment_id)


# ============================================================================
# Version Tools
# ============================================================================


@mcp.tool()
async def list_versions_tool(script_id: str) -> str:
    """
    List all versions of a script project.

    Versions are immutable snapshots of your script code.
    They are created when you deploy or explicitly create a version.

    Args:
        script_id: The script project ID
    """
    return await list_versions(script_id)


@mcp.tool()
async def create_version_tool(
    script_id: str,
    description: str = "",
) -> str:
    """
    Create a new immutable version of a script project.

    Versions capture a snapshot of the current script code.
    Once created, versions cannot be modified.

    Args:
        script_id: The script project ID
        description: Optional description for this version
    """
    return await create_version(
        script_id=script_id,
        description=description if description else None,
    )


@mcp.tool()
async def get_version_tool(script_id: str, version_number: int) -> str:
    """
    Get details of a specific version.

    Args:
        script_id: The script project ID
        version_number: The version number to retrieve (1, 2, 3, etc.)
    """
    return await get_version(script_id, version_number)


# ============================================================================
# Process Tools
# ============================================================================


@mcp.tool()
async def list_script_processes_tool(
    page_size: int = 50,
    script_id: str = "",
) -> str:
    """
    List recent execution processes for user's scripts.

    Args:
        page_size: Number of results (default: 50)
        script_id: Optional filter by script ID
    """
    return await list_script_processes(
        page_size=page_size,
        script_id=script_id if script_id else None,
    )


# ============================================================================
# Metrics Tools
# ============================================================================


@mcp.tool()
async def get_script_metrics_tool(
    script_id: str,
    metrics_granularity: str = "DAILY",
) -> str:
    """
    Get execution metrics for a script project.

    Returns analytics data including active users, total executions,
    and failed executions over time.

    Args:
        script_id: The script project ID
        metrics_granularity: Granularity of metrics - "DAILY" or "WEEKLY"
    """
    return await get_script_metrics(
        script_id=script_id,
        metrics_granularity=metrics_granularity,
    )


# ============================================================================
# Trigger Helper Tools
# ============================================================================


@mcp.tool()
async def generate_trigger_code(
    trigger_type: str,
    function_name: str,
    schedule: str = "",
) -> str:
    """
    Generate Apps Script code for creating triggers.

    The Apps Script API cannot create triggers directly - they must be created
    from within Apps Script itself. This tool generates the code you need.

    Args:
        trigger_type: Type of trigger. One of:
                      - "time_minutes" (run every N minutes: 1, 5, 10, 15, 30)
                      - "time_hours" (run every N hours: 1, 2, 4, 6, 8, 12)
                      - "time_daily" (run daily at a specific hour: 0-23)
                      - "time_weekly" (run weekly on a specific day)
                      - "on_open" (simple trigger - runs when document opens)
                      - "on_edit" (simple trigger - runs when user edits)
                      - "on_form_submit" (runs when form is submitted)
                      - "on_change" (runs when content changes)

        function_name: The function to run when trigger fires (e.g., "sendDailyReport")

        schedule: Schedule details (depends on trigger_type):
                  - For time_minutes: "1", "5", "10", "15", or "30"
                  - For time_hours: "1", "2", "4", "6", "8", or "12"
                  - For time_daily: hour as "0"-"23" (e.g., "9" for 9am)
                  - For time_weekly: "MONDAY", "TUESDAY", etc.
                  - For simple triggers (on_open, on_edit): not needed

    Returns:
        Apps Script code to create the trigger. User should add this to their script
        and run the setup function once to install the trigger.
    """
    from .appscript_tools import generate_trigger_code as _gen_trigger

    return await _gen_trigger(trigger_type, function_name, schedule)


# ============================================================================
# Gmail Tools
# ============================================================================


@mcp.tool()
async def search_gmail_messages_tool(
    user_google_email: str,
    query: str = "",
    max_results: int = 10,
) -> str:
    """
    Search for Gmail messages matching a query.

    Args:
        user_google_email: The user's Google email address
        query: Gmail search query (e.g., "from:user@example.com subject:hello")
        max_results: Maximum number of messages to return (default: 10)
    """
    return await search_gmail_messages(
        user_google_email=user_google_email,
        query=query,
        max_results=max_results,
    )


@mcp.tool()
async def get_gmail_message_tool(
    user_google_email: str,
    message_id: str,
    format: str = "full",
) -> str:
    """
    Get a specific Gmail message by ID.

    Args:
        user_google_email: The user's Google email address
        message_id: The message ID to retrieve
        format: Message format - "full", "metadata", or "minimal"
    """
    return await get_gmail_message(
        user_google_email=user_google_email,
        message_id=message_id,
        format=format,
    )


@mcp.tool()
async def send_gmail_message_tool(
    user_google_email: str,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    html: bool = False,
) -> str:
    """
    Send a Gmail message.

    Args:
        user_google_email: The user's Google email address
        to: Recipient email address(es), comma-separated
        subject: Email subject
        body: Email body content
        cc: Optional CC recipients, comma-separated
        bcc: Optional BCC recipients, comma-separated
        html: If True, body is treated as HTML
    """
    return await send_gmail_message(
        user_google_email=user_google_email,
        to=to,
        subject=subject,
        body=body,
        cc=cc if cc else None,
        bcc=bcc if bcc else None,
        html=html,
    )


@mcp.tool()
async def list_gmail_labels_tool(user_google_email: str) -> str:
    """
    List all Gmail labels for the user.

    Args:
        user_google_email: The user's Google email address
    """
    return await list_gmail_labels(user_google_email=user_google_email)


@mcp.tool()
async def modify_gmail_labels_tool(
    user_google_email: str,
    message_id: str,
    add_labels: list = None,
    remove_labels: list = None,
) -> str:
    """
    Modify labels on a Gmail message.

    Common label IDs:
    - INBOX - Message in inbox
    - UNREAD - Message is unread
    - STARRED - Message is starred
    - TRASH - Message in trash
    - SPAM - Message in spam
    - IMPORTANT - Message marked important

    Args:
        user_google_email: The user's Google email address
        message_id: The message ID to modify
        add_labels: List of label IDs to add (e.g., ["STARRED", "IMPORTANT"])
        remove_labels: List of label IDs to remove (e.g., ["UNREAD", "INBOX"])

    Examples:
        - Archive: remove_labels=["INBOX"]
        - Mark read: remove_labels=["UNREAD"]
        - Mark unread: add_labels=["UNREAD"]
        - Star: add_labels=["STARRED"]
        - Move to trash: add_labels=["TRASH"]
    """
    return await modify_gmail_labels(
        user_google_email=user_google_email,
        message_id=message_id,
        add_labels=add_labels,
        remove_labels=remove_labels,
    )


# ============================================================================
# Drive Tools
# ============================================================================


@mcp.tool()
async def search_drive_files_tool(
    user_google_email: str,
    query: str,
    page_size: int = 10,
) -> str:
    """
    Search for files and folders in Google Drive.

    Args:
        user_google_email: The user's Google email address
        query: Search query string. Supports Drive query operators:
               - name contains 'example'
               - mimeType = 'application/vnd.google-apps.spreadsheet'
               - fullText contains 'keyword'
               - modifiedTime > '2024-01-01'
        page_size: Maximum number of files to return (default: 10)
    """
    return await search_drive_files(
        user_google_email=user_google_email,
        query=query,
        page_size=page_size,
    )


@mcp.tool()
async def list_drive_items_tool(
    user_google_email: str,
    folder_id: str = "root",
    page_size: int = 50,
) -> str:
    """
    List files and folders in a Drive folder.

    Args:
        user_google_email: The user's Google email address
        folder_id: The folder ID to list (default: 'root' for My Drive root)
        page_size: Maximum number of items to return (default: 50)
    """
    return await list_drive_items(
        user_google_email=user_google_email,
        folder_id=folder_id,
        page_size=page_size,
    )


@mcp.tool()
async def get_drive_file_content_tool(
    user_google_email: str,
    file_id: str,
) -> str:
    """
    Get the content of a Google Drive file.

    Supports Google Docs (→ text), Sheets (→ CSV), Slides (→ text), and text files.

    Args:
        user_google_email: The user's Google email address
        file_id: The Drive file ID
    """
    return await get_drive_file_content(
        user_google_email=user_google_email,
        file_id=file_id,
    )


@mcp.tool()
async def create_drive_file_tool(
    user_google_email: str,
    file_name: str,
    content: str = "",
    folder_id: str = "root",
    mime_type: str = "text/plain",
) -> str:
    """
    Create a new file in Google Drive.

    Args:
        user_google_email: The user's Google email address
        file_name: Name for the new file
        content: File content (text)
        folder_id: Parent folder ID (default: 'root')
        mime_type: MIME type of the file (default: 'text/plain')
    """
    return await create_drive_file(
        user_google_email=user_google_email,
        file_name=file_name,
        content=content,
        folder_id=folder_id,
        mime_type=mime_type,
    )


@mcp.tool()
async def create_drive_folder_tool(
    user_google_email: str,
    folder_name: str,
    parent_id: str = "root",
) -> str:
    """
    Create a new folder in Google Drive.

    Args:
        user_google_email: The user's Google email address
        folder_name: Name for the new folder
        parent_id: Parent folder ID (default: 'root' for My Drive root)
    """
    return await create_drive_folder(
        user_google_email=user_google_email,
        folder_name=folder_name,
        parent_id=parent_id,
    )


@mcp.tool()
async def delete_drive_file_tool(
    user_google_email: str,
    file_id: str,
) -> str:
    """
    Permanently delete a file from Google Drive.

    WARNING: This permanently deletes the file. Use trash_drive_file for recoverable deletion.

    Args:
        user_google_email: The user's Google email address
        file_id: The file ID to delete
    """
    return await delete_drive_file(
        user_google_email=user_google_email,
        file_id=file_id,
    )


@mcp.tool()
async def trash_drive_file_tool(
    user_google_email: str,
    file_id: str,
) -> str:
    """
    Move a file to trash in Google Drive (recoverable).

    Args:
        user_google_email: The user's Google email address
        file_id: The file ID to trash
    """
    return await trash_drive_file(
        user_google_email=user_google_email,
        file_id=file_id,
    )


@mcp.tool()
async def share_drive_file_tool(
    user_google_email: str,
    file_id: str,
    email: str,
    role: str = "reader",
    send_notification: bool = True,
) -> str:
    """
    Share a file or folder with a user.

    Args:
        user_google_email: The user's Google email address
        file_id: The file or folder ID to share
        email: Email address of the user to share with
        role: Permission role - "reader", "writer", "commenter", or "owner"
        send_notification: Whether to send an email notification (default: True)
    """
    return await share_drive_file(
        user_google_email=user_google_email,
        file_id=file_id,
        email=email,
        role=role,
        send_notification=send_notification,
    )


@mcp.tool()
async def list_drive_permissions_tool(
    user_google_email: str,
    file_id: str,
) -> str:
    """
    List all permissions on a file or folder.

    Args:
        user_google_email: The user's Google email address
        file_id: The file or folder ID
    """
    return await list_drive_permissions(
        user_google_email=user_google_email,
        file_id=file_id,
    )


@mcp.tool()
async def remove_drive_permission_tool(
    user_google_email: str,
    file_id: str,
    permission_id: str,
) -> str:
    """
    Remove a permission from a file or folder.

    Args:
        user_google_email: The user's Google email address
        file_id: The file or folder ID
        permission_id: The permission ID to remove (from list_drive_permissions)
    """
    return await remove_drive_permission(
        user_google_email=user_google_email,
        file_id=file_id,
        permission_id=permission_id,
    )


# ============================================================================
# Sheets Tools
# ============================================================================


@mcp.tool()
async def list_spreadsheets_tool(
    user_google_email: str,
    query: str = "",
    page_size: int = 20,
) -> str:
    """
    List Google Sheets spreadsheets in Drive.

    Args:
        user_google_email: The user's Google email address
        query: Optional search query to filter spreadsheets
        page_size: Maximum number of spreadsheets to return (default: 20)
    """
    return await list_spreadsheets(
        user_google_email=user_google_email,
        query=query,
        page_size=page_size,
    )


@mcp.tool()
async def get_sheet_values_tool(
    user_google_email: str,
    spreadsheet_id: str,
    range: str = "Sheet1",
    value_render: str = "FORMATTED_VALUE",
) -> str:
    """
    Get values from a Google Sheet.

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
        range: A1 notation range (e.g., "Sheet1!A1:D10" or just "Sheet1")
        value_render: How values should be rendered - "FORMATTED_VALUE", "UNFORMATTED_VALUE", or "FORMULA"
    """
    return await get_sheet_values(
        user_google_email=user_google_email,
        spreadsheet_id=spreadsheet_id,
        range=range,
        value_render=value_render,
    )


@mcp.tool()
async def update_sheet_values_tool(
    user_google_email: str,
    spreadsheet_id: str,
    range: str,
    values: list,
    value_input: str = "USER_ENTERED",
) -> str:
    """
    Update values in a Google Sheet.

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
        range: A1 notation range (e.g., "Sheet1!A1:D10")
        values: 2D array of values to write. Example: [["Header1", "Header2"], ["Value1", "Value2"]]
        value_input: How input values should be interpreted - "USER_ENTERED" or "RAW"
    """
    return await update_sheet_values(
        user_google_email=user_google_email,
        spreadsheet_id=spreadsheet_id,
        range=range,
        values=values,
        value_input=value_input,
    )


@mcp.tool()
async def create_spreadsheet_tool(
    user_google_email: str,
    title: str,
    sheet_names: list = None,
) -> str:
    """
    Create a new Google Spreadsheet.

    Args:
        user_google_email: The user's Google email address
        title: Title for the new spreadsheet
        sheet_names: Optional list of sheet names to create (default: ["Sheet1"])
    """
    return await create_spreadsheet(
        user_google_email=user_google_email,
        title=title,
        sheet_names=sheet_names,
    )


@mcp.tool()
async def append_sheet_values_tool(
    user_google_email: str,
    spreadsheet_id: str,
    range: str,
    values: list,
    value_input: str = "USER_ENTERED",
) -> str:
    """
    Append values to a Google Sheet (adds rows after existing data).

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
        range: A1 notation range to append to (e.g., "Sheet1!A:D" or "Sheet1")
        values: 2D array of values to append. Example: [["Value1", "Value2"], ["Value3", "Value4"]]
        value_input: How input values should be interpreted - "USER_ENTERED" or "RAW"
    """
    return await append_sheet_values(
        user_google_email=user_google_email,
        spreadsheet_id=spreadsheet_id,
        range=range,
        values=values,
        value_input=value_input,
    )


@mcp.tool()
async def get_spreadsheet_metadata_tool(
    user_google_email: str,
    spreadsheet_id: str,
) -> str:
    """
    Get metadata about a spreadsheet including all sheet names and properties.

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
    """
    return await get_spreadsheet_metadata(
        user_google_email=user_google_email,
        spreadsheet_id=spreadsheet_id,
    )


# ============================================================================
# Calendar Tools
# ============================================================================


@mcp.tool()
async def list_calendars_tool(user_google_email: str) -> str:
    """
    List all calendars accessible to the user.

    Args:
        user_google_email: The user's Google email address
    """
    return await list_calendars(user_google_email=user_google_email)


@mcp.tool()
async def get_events_tool(
    user_google_email: str,
    calendar_id: str = "primary",
    max_results: int = 10,
    time_min: str = "",
    time_max: str = "",
    query: str = "",
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
    """
    return await get_events(
        user_google_email=user_google_email,
        calendar_id=calendar_id,
        max_results=max_results,
        time_min=time_min if time_min else None,
        time_max=time_max if time_max else None,
        query=query if query else None,
    )


@mcp.tool()
async def create_event_tool(
    user_google_email: str,
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: str = "",
    location: str = "",
    attendees: str = "",
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
    """
    return await create_event(
        user_google_email=user_google_email,
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        calendar_id=calendar_id,
        description=description if description else None,
        location=location if location else None,
        attendees=attendees if attendees else None,
        all_day=all_day,
    )


@mcp.tool()
async def delete_event_tool(
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
    """
    return await delete_event(
        user_google_email=user_google_email,
        event_id=event_id,
        calendar_id=calendar_id,
    )


@mcp.tool()
async def update_event_tool(
    user_google_email: str,
    event_id: str,
    calendar_id: str = "primary",
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
    attendees: str = "",
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
    """
    return await update_event(
        user_google_email=user_google_email,
        event_id=event_id,
        calendar_id=calendar_id,
        summary=summary if summary else None,
        start_time=start_time if start_time else None,
        end_time=end_time if end_time else None,
        description=description if description else None,
        location=location if location else None,
        attendees=attendees if attendees else None,
        all_day=all_day,
    )


# ============================================================================
# Docs Tools
# ============================================================================


@mcp.tool()
async def search_docs_tool(
    user_google_email: str,
    query: str,
    page_size: int = 10,
) -> str:
    """
    Search for Google Docs by name.

    Args:
        user_google_email: The user's Google email address
        query: Search query string
        page_size: Maximum number of docs to return (default: 10)
    """
    return await search_docs(
        user_google_email=user_google_email,
        query=query,
        page_size=page_size,
    )


@mcp.tool()
async def get_doc_content_tool(
    user_google_email: str,
    document_id: str,
) -> str:
    """
    Get the content of a Google Doc.

    Args:
        user_google_email: The user's Google email address
        document_id: The document ID
    """
    return await get_doc_content(
        user_google_email=user_google_email,
        document_id=document_id,
    )


@mcp.tool()
async def create_doc_tool(
    user_google_email: str,
    title: str,
    content: str = "",
) -> str:
    """
    Create a new Google Doc.

    Args:
        user_google_email: The user's Google email address
        title: Document title
        content: Optional initial content
    """
    return await create_doc(
        user_google_email=user_google_email,
        title=title,
        content=content,
    )


@mcp.tool()
async def modify_doc_text_tool(
    user_google_email: str,
    document_id: str,
    text: str,
    index: int = 1,
    replace_text: str = "",
) -> str:
    """
    Modify text in a Google Doc.

    Args:
        user_google_email: The user's Google email address
        document_id: The document ID
        text: Text to insert (or replace with)
        index: Position to insert text (default: 1, start of document)
        replace_text: If provided, find and replace this text with 'text'
    """
    return await modify_doc_text(
        user_google_email=user_google_email,
        document_id=document_id,
        text=text,
        index=index,
        replace_text=replace_text if replace_text else None,
    )


@mcp.tool()
async def append_doc_text_tool(
    user_google_email: str,
    document_id: str,
    text: str,
) -> str:
    """
    Append text to the end of a Google Doc.

    Args:
        user_google_email: The user's Google email address
        document_id: The document ID
        text: Text to append to the end of the document
    """
    return await append_doc_text(
        user_google_email=user_google_email,
        document_id=document_id,
        text=text,
    )


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    logger.info(f"Starting Apps Script MCP Server v{__version__}")
    logger.info("Authentication: clasp (recommended) or OAuth 2.0/2.1")
    logger.info("Run 'google-automation-mcp setup' to configure authentication")
    mcp.run()


if __name__ == "__main__":
    main()
