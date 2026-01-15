"""
Apps Script MCP Server

MCP server for Google Apps Script with unified authentication.
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
    from .tools import generate_trigger_code as _gen_trigger
    return await _gen_trigger(trigger_type, function_name, schedule)


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    logger.info(f"Starting Apps Script MCP Server v{__version__}")
    logger.info("Authentication: clasp (recommended) or OAuth 2.0/2.1")
    logger.info("Run 'appscript-mcp setup' to configure authentication")
    mcp.run()


if __name__ == "__main__":
    main()
