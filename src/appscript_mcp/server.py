"""
Apps Script MCP Server

FastMCP server for Google Apps Script operations.
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
    update_script_content,
    run_script_function,
    # Deployments
    create_deployment,
    list_deployments,
    update_deployment,
    delete_deployment,
    # Processes
    list_script_processes,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the MCP server
mcp = FastMCP("Apps Script MCP")


# ============================================================================
# Register Authentication Tools
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
# Register Project Tools
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
# Register Deployment Tools
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
# Register Process Tools
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
    code_lines = []

    if trigger_type == "on_open":
        code_lines = [
            f"// Simple trigger - just rename your function to 'onOpen'",
            f"// This runs automatically when the document is opened",
            f"function onOpen(e) {{",
            f"  {function_name}();",
            f"}}",
        ]
    elif trigger_type == "on_edit":
        code_lines = [
            f"// Simple trigger - just rename your function to 'onEdit'",
            f"// This runs automatically when a user edits the spreadsheet",
            f"function onEdit(e) {{",
            f"  {function_name}();",
            f"}}",
        ]
    elif trigger_type == "time_minutes":
        interval = schedule or "5"
        code_lines = [
            f"// Run this function ONCE to install the trigger",
            f"function createTimeTrigger_{function_name}() {{",
            f"  // Delete existing triggers for this function first",
            f"  const triggers = ScriptApp.getProjectTriggers();",
            f"  triggers.forEach(trigger => {{",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            f"      ScriptApp.deleteTrigger(trigger);",
            f"    }}",
            f"  }});",
            f"",
            f"  // Create new trigger - runs every {interval} minutes",
            f"  ScriptApp.newTrigger('{function_name}')",
            f"    .timeBased()",
            f"    .everyMinutes({interval})",
            f"    .create();",
            f"",
            f"  Logger.log('Trigger created: {function_name} will run every {interval} minutes');",
            f"}}",
        ]
    elif trigger_type == "time_hours":
        interval = schedule or "1"
        code_lines = [
            f"// Run this function ONCE to install the trigger",
            f"function createTimeTrigger_{function_name}() {{",
            f"  // Delete existing triggers for this function first",
            f"  const triggers = ScriptApp.getProjectTriggers();",
            f"  triggers.forEach(trigger => {{",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            f"      ScriptApp.deleteTrigger(trigger);",
            f"    }}",
            f"  }});",
            f"",
            f"  // Create new trigger - runs every {interval} hour(s)",
            f"  ScriptApp.newTrigger('{function_name}')",
            f"    .timeBased()",
            f"    .everyHours({interval})",
            f"    .create();",
            f"",
            f"  Logger.log('Trigger created: {function_name} will run every {interval} hour(s)');",
            f"}}",
        ]
    elif trigger_type == "time_daily":
        hour = schedule or "9"
        code_lines = [
            f"// Run this function ONCE to install the trigger",
            f"function createDailyTrigger_{function_name}() {{",
            f"  // Delete existing triggers for this function first",
            f"  const triggers = ScriptApp.getProjectTriggers();",
            f"  triggers.forEach(trigger => {{",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            f"      ScriptApp.deleteTrigger(trigger);",
            f"    }}",
            f"  }});",
            f"",
            f"  // Create new trigger - runs daily at {hour}:00",
            f"  ScriptApp.newTrigger('{function_name}')",
            f"    .timeBased()",
            f"    .atHour({hour})",
            f"    .everyDays(1)",
            f"    .create();",
            f"",
            f"  Logger.log('Trigger created: {function_name} will run daily at {hour}:00');",
            f"}}",
        ]
    elif trigger_type == "time_weekly":
        day = schedule.upper() if schedule else "MONDAY"
        code_lines = [
            f"// Run this function ONCE to install the trigger",
            f"function createWeeklyTrigger_{function_name}() {{",
            f"  // Delete existing triggers for this function first",
            f"  const triggers = ScriptApp.getProjectTriggers();",
            f"  triggers.forEach(trigger => {{",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            f"      ScriptApp.deleteTrigger(trigger);",
            f"    }}",
            f"  }});",
            f"",
            f"  // Create new trigger - runs weekly on {day}",
            f"  ScriptApp.newTrigger('{function_name}')",
            f"    .timeBased()",
            f"    .onWeekDay(ScriptApp.WeekDay.{day})",
            f"    .atHour(9)",
            f"    .create();",
            f"",
            f"  Logger.log('Trigger created: {function_name} will run every {day} at 9:00');",
            f"}}",
        ]
    elif trigger_type == "on_form_submit":
        code_lines = [
            f"// Run this function ONCE to install the trigger",
            f"// This must be run from a script BOUND to the Google Form",
            f"function createFormSubmitTrigger_{function_name}() {{",
            f"  // Delete existing triggers for this function first",
            f"  const triggers = ScriptApp.getProjectTriggers();",
            f"  triggers.forEach(trigger => {{",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            f"      ScriptApp.deleteTrigger(trigger);",
            f"    }}",
            f"  }});",
            f"",
            f"  // Create new trigger - runs when form is submitted",
            f"  ScriptApp.newTrigger('{function_name}')",
            f"    .forForm(FormApp.getActiveForm())",
            f"    .onFormSubmit()",
            f"    .create();",
            f"",
            f"  Logger.log('Trigger created: {function_name} will run on form submit');",
            f"}}",
        ]
    elif trigger_type == "on_change":
        code_lines = [
            f"// Run this function ONCE to install the trigger",
            f"// This must be run from a script BOUND to a Google Sheet",
            f"function createChangeTrigger_{function_name}() {{",
            f"  // Delete existing triggers for this function first",
            f"  const triggers = ScriptApp.getProjectTriggers();",
            f"  triggers.forEach(trigger => {{",
            f"    if (trigger.getHandlerFunction() === '{function_name}') {{",
            f"      ScriptApp.deleteTrigger(trigger);",
            f"    }}",
            f"  }});",
            f"",
            f"  // Create new trigger - runs when spreadsheet changes",
            f"  ScriptApp.newTrigger('{function_name}')",
            f"    .forSpreadsheet(SpreadsheetApp.getActive())",
            f"    .onChange()",
            f"    .create();",
            f"",
            f"  Logger.log('Trigger created: {function_name} will run on spreadsheet change');",
            f"}}",
        ]
    else:
        return (
            f"Unknown trigger type: {trigger_type}\n\n"
            "Valid types: time_minutes, time_hours, time_daily, time_weekly, "
            "on_open, on_edit, on_form_submit, on_change"
        )

    code = "\n".join(code_lines)

    instructions = []
    if trigger_type.startswith("on_"):
        if trigger_type in ("on_open", "on_edit"):
            instructions = [
                "SIMPLE TRIGGER",
                "=" * 50,
                "",
                "Add this code to your script. Simple triggers run automatically",
                "when the event occurs - no setup function needed.",
                "",
                "Note: Simple triggers have limitations:",
                "- Cannot access services that require authorization",
                "- Cannot run longer than 30 seconds",
                "- Cannot make external HTTP requests",
                "",
                "For more capabilities, use an installable trigger instead.",
                "",
                "CODE TO ADD:",
                "-" * 50,
            ]
        else:
            instructions = [
                "INSTALLABLE TRIGGER",
                "=" * 50,
                "",
                "1. Add this code to your script",
                f"2. Run the setup function once: createFormSubmitTrigger_{function_name}() or similar",
                "3. The trigger will then run automatically",
                "",
                "CODE TO ADD:",
                "-" * 50,
            ]
    else:
        instructions = [
            "INSTALLABLE TRIGGER",
            "=" * 50,
            "",
            "1. Add this code to your script using update_script_content",
            f"2. Run the setup function ONCE (manually in Apps Script editor or via run_script_function)",
            "3. The trigger will then run automatically on schedule",
            "",
            "To check installed triggers: Apps Script editor → Triggers (clock icon)",
            "",
            "CODE TO ADD:",
            "-" * 50,
        ]

    return "\n".join(instructions) + "\n\n" + code


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    logger.info(f"Starting Apps Script MCP Server v{__version__}")
    mcp.run()


if __name__ == "__main__":
    main()
