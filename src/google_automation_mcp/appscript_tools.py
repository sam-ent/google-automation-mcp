"""
Google Apps Script MCP Tools

All 11 Apps Script tools plus authentication helpers.
"""

import asyncio
import functools
import logging
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from .auth import (
    get_script_service,
    get_drive_service,
    start_auth_flow,
    complete_auth_flow,
    set_pending_flow,
    get_pending_flow,
    clear_pending_flow,
)

logger = logging.getLogger(__name__)


def handle_errors(func):
    """Decorator to handle API errors gracefully."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HttpError as e:
            error_msg = str(e)
            if e.resp.status == 401:
                return f"Authentication error: {error_msg}\n\nPlease run start_google_auth to authenticate."
            elif e.resp.status == 403:
                if "accessNotConfigured" in error_msg:
                    return (
                        f"API not enabled: {error_msg}\n\n"
                        "Please enable the Apps Script API and Drive API in your Google Cloud Console:\n"
                        "- https://console.cloud.google.com/flows/enableapi?apiid=script.googleapis.com\n"
                        "- https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com"
                    )
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


# ============================================================================
# Authentication Tools
# ============================================================================


async def start_google_auth() -> str:
    """
    Start Google OAuth authentication flow.

    Returns an authorization URL that must be opened in a browser.
    After authorizing, call complete_google_auth with the redirect URL.

    Returns:
        str: Instructions with the authorization URL
    """
    try:
        auth_url, flow = start_auth_flow()
        set_pending_flow(flow)

        return (
            "Google OAuth Authentication\n"
            "============================\n\n"
            "1. Open this URL in your browser:\n\n"
            f"   {auth_url}\n\n"
            "2. Sign in and authorize the application\n\n"
            "3. You will be redirected to http://localhost (page will not load)\n\n"
            "4. Copy the FULL URL from your browser address bar\n"
            "   (looks like: http://localhost/?code=4/0A...&scope=...)\n\n"
            "5. Call complete_google_auth with the redirect URL"
        )
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Failed to start authentication: {str(e)}"


async def complete_google_auth(redirect_url: str) -> str:
    """
    Complete the Google OAuth flow with the redirect URL.

    Args:
        redirect_url: The full URL from the browser after authorization

    Returns:
        str: Success or error message
    """
    flow = get_pending_flow()
    if flow is None:
        return "No pending authentication flow. Please run start_google_auth first."

    try:
        creds = complete_auth_flow(flow, redirect_url)
        clear_pending_flow()

        # Get user email to confirm
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests

            info = id_token.verify_oauth2_token(
                creds.id_token, requests.Request(), creds.client_id
            )
            email = info.get("email", "unknown")
        except Exception:
            email = "authenticated user"

        return f"Authentication successful for {email}.\n\nYou can now use all Apps Script tools."
    except Exception as e:
        clear_pending_flow()
        return f"Authentication failed: {str(e)}\n\nPlease run start_google_auth to try again."


# ============================================================================
# Apps Script Project Tools
# ============================================================================


@handle_errors
async def list_script_projects(
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> str:
    """
    List Google Apps Script projects accessible to the user.

    Uses Drive API to find Apps Script files.

    Args:
        page_size: Number of results per page (default: 50)
        page_token: Token for pagination (optional)

    Returns:
        str: Formatted list of script projects
    """
    service = get_drive_service()

    query = "mimeType='application/vnd.google-apps.script' and trashed=false"
    request_params = {
        "q": query,
        "pageSize": page_size,
        "fields": "nextPageToken, files(id, name, createdTime, modifiedTime)",
        "orderBy": "modifiedTime desc",
    }
    if page_token:
        request_params["pageToken"] = page_token

    response = await asyncio.to_thread(service.files().list(**request_params).execute)

    files = response.get("files", [])

    if not files:
        return "No Apps Script projects found."

    output = [f"Found {len(files)} Apps Script projects:"]
    for file in files:
        title = file.get("name", "Untitled")
        script_id = file.get("id", "Unknown ID")
        create_time = file.get("createdTime", "Unknown")
        update_time = file.get("modifiedTime", "Unknown")

        output.append(
            f"- {title} (ID: {script_id}) Created: {create_time} Modified: {update_time}"
        )

    if "nextPageToken" in response:
        output.append(f"\nNext page token: {response['nextPageToken']}")

    return "\n".join(output)


@handle_errors
async def get_script_project(script_id: str) -> str:
    """
    Retrieve complete project details including all source files.

    Args:
        script_id: The script project ID

    Returns:
        str: Formatted project details with all file contents
    """
    service = get_script_service()

    project = await asyncio.to_thread(
        service.projects().get(scriptId=script_id).execute
    )

    title = project.get("title", "Untitled")
    project_script_id = project.get("scriptId", "Unknown")
    creator = project.get("creator", {}).get("email", "Unknown")
    create_time = project.get("createTime", "Unknown")
    update_time = project.get("updateTime", "Unknown")

    output = [
        f"Project: {title} (ID: {project_script_id})",
        f"Creator: {creator}",
        f"Created: {create_time}",
        f"Modified: {update_time}",
        "",
        "Files:",
    ]

    files = project.get("files", [])
    for i, file in enumerate(files, 1):
        file_name = file.get("name", "Untitled")
        file_type = file.get("type", "Unknown")
        source = file.get("source", "")

        output.append(f"{i}. {file_name} ({file_type})")
        if source:
            output.append(f"   {source[:200]}{'...' if len(source) > 200 else ''}")
            output.append("")

    return "\n".join(output)


@handle_errors
async def get_script_content(script_id: str, file_name: str) -> str:
    """
    Retrieve content of a specific file within a project.

    Args:
        script_id: The script project ID
        file_name: Name of the file to retrieve

    Returns:
        str: File content as string
    """
    service = get_script_service()

    project = await asyncio.to_thread(
        service.projects().get(scriptId=script_id).execute
    )

    files = project.get("files", [])
    target_file = None

    for file in files:
        if file.get("name") == file_name:
            target_file = file
            break

    if not target_file:
        return f"File '{file_name}' not found in project {script_id}"

    source = target_file.get("source", "")
    file_type = target_file.get("type", "Unknown")

    output = [f"File: {file_name} ({file_type})", "", source]

    return "\n".join(output)


@handle_errors
async def create_script_project(
    title: str,
    parent_id: Optional[str] = None,
) -> str:
    """
    Create a new Apps Script project.

    Args:
        title: Project title
        parent_id: Optional Drive folder ID or bound container ID

    Returns:
        str: Formatted string with new project details
    """
    service = get_script_service()

    request_body = {"title": title}

    if parent_id:
        request_body["parentId"] = parent_id

    project = await asyncio.to_thread(
        service.projects().create(body=request_body).execute
    )

    script_id = project.get("scriptId", "Unknown")
    edit_url = f"https://script.google.com/d/{script_id}/edit"

    output = [
        f"Created Apps Script project: {title}",
        f"Script ID: {script_id}",
        f"Edit URL: {edit_url}",
    ]

    return "\n".join(output)


@handle_errors
async def delete_script_project(script_id: str) -> str:
    """
    Delete an Apps Script project.

    This permanently deletes the script project. The action cannot be undone.

    Args:
        script_id: The script project ID to delete

    Returns:
        str: Confirmation message
    """
    service = get_drive_service()

    # Apps Script projects are stored as Drive files
    await asyncio.to_thread(service.files().delete(fileId=script_id).execute)

    return f"Deleted Apps Script project: {script_id}"


@handle_errors
async def update_script_content(
    script_id: str,
    files: List[Dict[str, str]],
) -> str:
    """
    Update or create files in a script project.

    Args:
        script_id: The script project ID
        files: List of file objects with name, type, and source
               Example: [{"name": "Code", "type": "SERVER_JS", "source": "function main() {}"}]

    Returns:
        str: Formatted string confirming update with file list
    """
    service = get_script_service()

    request_body = {"files": files}

    updated_content = await asyncio.to_thread(
        service.projects().updateContent(scriptId=script_id, body=request_body).execute
    )

    output = [f"Updated script project: {script_id}", "", "Modified files:"]

    for file in updated_content.get("files", []):
        file_name = file.get("name", "Untitled")
        file_type = file.get("type", "Unknown")
        output.append(f"- {file_name} ({file_type})")

    return "\n".join(output)


@handle_errors
async def run_script_function(
    script_id: str,
    function_name: str,
    parameters: Optional[List[Any]] = None,
    dev_mode: bool = False,
) -> str:
    """
    Execute a function in a deployed script.

    Note: Requires the script to be deployed as "API Executable" in the Apps Script editor.

    Args:
        script_id: The script project ID
        function_name: Name of function to execute
        parameters: Optional list of parameters to pass
        dev_mode: Whether to run latest code vs deployed version

    Returns:
        str: Formatted string with execution result or error
    """
    service = get_script_service()

    request_body = {"function": function_name, "devMode": dev_mode}

    if parameters:
        request_body["parameters"] = parameters

    try:
        response = await asyncio.to_thread(
            service.scripts().run(scriptId=script_id, body=request_body).execute
        )

        if "error" in response:
            error_details = response["error"]
            error_message = error_details.get("message", "Unknown error")
            return (
                f"Execution failed\nFunction: {function_name}\nError: {error_message}"
            )

        result = response.get("response", {}).get("result")
        output = [
            "Execution successful",
            f"Function: {function_name}",
            f"Result: {result}",
        ]

        return "\n".join(output)

    except Exception as e:
        return f"Execution failed\nFunction: {function_name}\nError: {str(e)}"


# ============================================================================
# Deployment Tools
# ============================================================================


@handle_errors
async def create_deployment(
    script_id: str,
    description: str,
    version_description: Optional[str] = None,
) -> str:
    """
    Create a new deployment of the script.

    Args:
        script_id: The script project ID
        description: Deployment description
        version_description: Optional version description

    Returns:
        str: Formatted string with deployment details
    """
    service = get_script_service()

    # First, create a new version
    version_body = {"description": version_description or description}
    version = await asyncio.to_thread(
        service.projects()
        .versions()
        .create(scriptId=script_id, body=version_body)
        .execute
    )
    version_number = version.get("versionNumber")

    # Now create the deployment with the version number
    deployment_body = {
        "versionNumber": version_number,
        "description": description,
    }

    deployment = await asyncio.to_thread(
        service.projects()
        .deployments()
        .create(scriptId=script_id, body=deployment_body)
        .execute
    )

    deployment_id = deployment.get("deploymentId", "Unknown")

    output = [
        f"Created deployment for script: {script_id}",
        f"Deployment ID: {deployment_id}",
        f"Version: {version_number}",
        f"Description: {description}",
    ]

    return "\n".join(output)


@handle_errors
async def list_deployments(script_id: str) -> str:
    """
    List all deployments for a script project.

    Args:
        script_id: The script project ID

    Returns:
        str: Formatted string with deployment list
    """
    service = get_script_service()

    response = await asyncio.to_thread(
        service.projects().deployments().list(scriptId=script_id).execute
    )

    deployments = response.get("deployments", [])

    if not deployments:
        return f"No deployments found for script: {script_id}"

    output = [f"Deployments for script: {script_id}", ""]

    for i, deployment in enumerate(deployments, 1):
        deployment_id = deployment.get("deploymentId", "Unknown")
        description = deployment.get("description", "No description")
        update_time = deployment.get("updateTime", "Unknown")

        output.append(f"{i}. {description} ({deployment_id})")
        output.append(f"   Updated: {update_time}")
        output.append("")

    return "\n".join(output)


@handle_errors
async def update_deployment(
    script_id: str,
    deployment_id: str,
    description: Optional[str] = None,
) -> str:
    """
    Update an existing deployment configuration.

    Args:
        script_id: The script project ID
        deployment_id: The deployment ID to update
        description: Optional new description

    Returns:
        str: Formatted string confirming update
    """
    service = get_script_service()

    request_body = {}
    if description:
        request_body["description"] = description

    deployment = await asyncio.to_thread(
        service.projects()
        .deployments()
        .update(scriptId=script_id, deploymentId=deployment_id, body=request_body)
        .execute
    )

    output = [
        f"Updated deployment: {deployment_id}",
        f"Script: {script_id}",
        f"Description: {deployment.get('description', 'No description')}",
    ]

    return "\n".join(output)


@handle_errors
async def delete_deployment(script_id: str, deployment_id: str) -> str:
    """
    Delete a deployment.

    Args:
        script_id: The script project ID
        deployment_id: The deployment ID to delete

    Returns:
        str: Confirmation message
    """
    service = get_script_service()

    await asyncio.to_thread(
        service.projects()
        .deployments()
        .delete(scriptId=script_id, deploymentId=deployment_id)
        .execute
    )

    return f"Deleted deployment: {deployment_id} from script: {script_id}"


# ============================================================================
# Process Monitoring Tools
# ============================================================================


# ============================================================================
# Version Tools
# ============================================================================


@handle_errors
async def list_versions(script_id: str) -> str:
    """
    List all versions of a script project.

    Args:
        script_id: The script project ID

    Returns:
        str: Formatted string with version list
    """
    service = get_script_service()

    response = await asyncio.to_thread(
        service.projects().versions().list(scriptId=script_id).execute
    )

    versions = response.get("versions", [])

    if not versions:
        return f"No versions found for script: {script_id}"

    output = [f"Versions for script: {script_id}", ""]

    for version in versions:
        version_number = version.get("versionNumber", "Unknown")
        description = version.get("description", "No description")
        create_time = version.get("createTime", "Unknown")

        output.append(f"Version {version_number}: {description}")
        output.append(f"   Created: {create_time}")
        output.append("")

    return "\n".join(output)


@handle_errors
async def create_version(
    script_id: str,
    description: Optional[str] = None,
) -> str:
    """
    Create a new immutable version of a script project.

    Args:
        script_id: The script project ID
        description: Optional version description

    Returns:
        str: Formatted string with new version details
    """
    service = get_script_service()

    request_body = {}
    if description:
        request_body["description"] = description

    version = await asyncio.to_thread(
        service.projects()
        .versions()
        .create(scriptId=script_id, body=request_body)
        .execute
    )

    version_number = version.get("versionNumber", "Unknown")
    create_time = version.get("createTime", "Unknown")

    output = [
        f"Created version {version_number} for script: {script_id}",
        f"Description: {description or 'No description'}",
        f"Created: {create_time}",
    ]

    return "\n".join(output)


@handle_errors
async def get_version(script_id: str, version_number: int) -> str:
    """
    Get details of a specific version.

    Args:
        script_id: The script project ID
        version_number: The version number to retrieve

    Returns:
        str: Formatted string with version details
    """
    service = get_script_service()

    version = await asyncio.to_thread(
        service.projects()
        .versions()
        .get(scriptId=script_id, versionNumber=version_number)
        .execute
    )

    ver_num = version.get("versionNumber", "Unknown")
    description = version.get("description", "No description")
    create_time = version.get("createTime", "Unknown")

    output = [
        f"Version {ver_num} of script: {script_id}",
        f"Description: {description}",
        f"Created: {create_time}",
    ]

    return "\n".join(output)


# ============================================================================
# Process Monitoring Tools
# ============================================================================


@handle_errors
async def list_script_processes(
    page_size: int = 50,
    script_id: Optional[str] = None,
) -> str:
    """
    List recent execution processes for user's scripts.

    Args:
        page_size: Number of results (default: 50)
        script_id: Optional filter by script ID

    Returns:
        str: Formatted string with process list
    """
    service = get_script_service()

    request_params = {"pageSize": page_size}
    if script_id:
        request_params["scriptId"] = script_id

    response = await asyncio.to_thread(
        service.processes().list(**request_params).execute
    )

    processes = response.get("processes", [])

    if not processes:
        return "No recent script executions found."

    output = ["Recent script executions:", ""]

    for i, process in enumerate(processes, 1):
        function_name = process.get("functionName", "Unknown")
        process_status = process.get("processStatus", "Unknown")
        start_time = process.get("startTime", "Unknown")
        duration = process.get("duration", "Unknown")

        output.append(f"{i}. {function_name}")
        output.append(f"   Status: {process_status}")
        output.append(f"   Started: {start_time}")
        output.append(f"   Duration: {duration}")
        output.append("")

    return "\n".join(output)


# ============================================================================
# Metrics Tools
# ============================================================================


@handle_errors
async def get_script_metrics(
    script_id: str,
    metrics_granularity: str = "DAILY",
) -> str:
    """
    Get execution metrics for a script project.

    Args:
        script_id: The script project ID
        metrics_granularity: Granularity of metrics - "DAILY" or "WEEKLY"

    Returns:
        str: Formatted string with metrics data
    """
    service = get_script_service()

    # Build the metrics filter
    request_params = {
        "scriptId": script_id,
        "metricsGranularity": metrics_granularity,
    }

    response = await asyncio.to_thread(
        service.projects().getMetrics(**request_params).execute
    )

    output = [
        f"Metrics for script: {script_id}",
        f"Granularity: {metrics_granularity}",
        "",
    ]

    # Active users
    active_users = response.get("activeUsers", [])
    if active_users:
        output.append("Active Users:")
        for metric in active_users:
            start_time = metric.get("startTime", "Unknown")
            end_time = metric.get("endTime", "Unknown")
            value = metric.get("value", "0")
            output.append(f"  {start_time} to {end_time}: {value} users")
        output.append("")

    # Total executions
    total_executions = response.get("totalExecutions", [])
    if total_executions:
        output.append("Total Executions:")
        for metric in total_executions:
            start_time = metric.get("startTime", "Unknown")
            end_time = metric.get("endTime", "Unknown")
            value = metric.get("value", "0")
            output.append(f"  {start_time} to {end_time}: {value} executions")
        output.append("")

    # Failed executions
    failed_executions = response.get("failedExecutions", [])
    if failed_executions:
        output.append("Failed Executions:")
        for metric in failed_executions:
            start_time = metric.get("startTime", "Unknown")
            end_time = metric.get("endTime", "Unknown")
            value = metric.get("value", "0")
            output.append(f"  {start_time} to {end_time}: {value} failures")
        output.append("")

    if not active_users and not total_executions and not failed_executions:
        output.append("No metrics data available for this script.")

    return "\n".join(output)


# ============================================================================
# Trigger Code Generator
# ============================================================================


async def generate_trigger_code(
    trigger_type: str,
    function_name: str,
    schedule: str = "",
) -> str:
    """
    Generate Apps Script code for creating triggers.

    The Apps Script API cannot create triggers directly - they must be created
    from within Apps Script itself. This generates code to push via update_script_content,
    then run the setup function via run_script_function or manually.

    Args:
        trigger_type: Type of trigger:
            - "time_minutes" (1, 5, 10, 15, 30)
            - "time_hours" (1, 2, 4, 6, 8, 12)
            - "time_daily" (hour 0-23)
            - "time_weekly" (MONDAY, TUESDAY, etc.)
            - "on_open" (document open)
            - "on_edit" (user edit)
            - "on_form_submit" (form submission)
            - "on_change" (content change)
        function_name: Function to call when trigger fires
        schedule: Schedule value (depends on trigger_type)

    Returns:
        str: Apps Script code to add to project and run once
    """
    trigger_type = trigger_type.lower()

    # Build the trigger creation code based on type
    if trigger_type == "time_minutes":
        minutes = schedule or "5"
        valid_minutes = ["1", "5", "10", "15", "30"]
        if minutes not in valid_minutes:
            return f"Error: time_minutes schedule must be one of {valid_minutes}"
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .timeBased()
      .everyMinutes({minutes})
      .create();"""

    elif trigger_type == "time_hours":
        hours = schedule or "1"
        valid_hours = ["1", "2", "4", "6", "8", "12"]
        if hours not in valid_hours:
            return f"Error: time_hours schedule must be one of {valid_hours}"
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .timeBased()
      .everyHours({hours})
      .create();"""

    elif trigger_type == "time_daily":
        hour = schedule or "9"
        try:
            hour_int = int(hour)
            if not 0 <= hour_int <= 23:
                raise ValueError()
        except ValueError:
            return "Error: time_daily schedule must be hour 0-23"
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .timeBased()
      .atHour({hour})
      .everyDays(1)
      .create();"""

    elif trigger_type == "time_weekly":
        day = (schedule or "MONDAY").upper()
        valid_days = [
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
            "SATURDAY",
            "SUNDAY",
        ]
        if day not in valid_days:
            return f"Error: time_weekly schedule must be one of {valid_days}"
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .timeBased()
      .onWeekDay(ScriptApp.WeekDay.{day})
      .create();"""

    elif trigger_type == "on_open":
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .forSpreadsheet(SpreadsheetApp.getActive())
      .onOpen()
      .create();"""

    elif trigger_type == "on_edit":
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .forSpreadsheet(SpreadsheetApp.getActive())
      .onEdit()
      .create();"""

    elif trigger_type == "on_form_submit":
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .forForm(FormApp.getActiveForm())
      .onFormSubmit()
      .create();"""

    elif trigger_type == "on_change":
        trigger_code = f"""ScriptApp.newTrigger('{function_name}')
      .forSpreadsheet(SpreadsheetApp.getActive())
      .onChange()
      .create();"""

    else:
        return f"Error: Unknown trigger_type '{trigger_type}'. Valid types: time_minutes, time_hours, time_daily, time_weekly, on_open, on_edit, on_form_submit, on_change"

    # Generate complete setup code
    setup_code = f"""/**
 * Setup trigger for {function_name}
 * Run this function ONCE to install the trigger.
 * After running, you can delete this function.
 */
function setupTrigger_{function_name}() {{
  // Remove existing triggers for this function first
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {{
    if (triggers[i].getHandlerFunction() === '{function_name}') {{
      ScriptApp.deleteTrigger(triggers[i]);
    }}
  }}

  // Create new trigger
  {trigger_code}

  Logger.log('Trigger created for {function_name}');
}}
"""

    return (
        f"Generated trigger setup code for '{function_name}' ({trigger_type}):\n\n"
        f"```javascript\n{setup_code}```\n\n"
        f"**Next steps:**\n"
        f"1. Use update_script_content to add this code to your project\n"
        f"2. Run setupTrigger_{function_name}() once via run_script_function (requires API Executable deployment) or manually in the Apps Script editor"
    )
