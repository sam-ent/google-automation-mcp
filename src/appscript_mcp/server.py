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
    Create a new Apps Script project.

    Args:
        title: Project title
        parent_id: Optional Drive folder ID or bound container ID (e.g., Spreadsheet ID)
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
# Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    logger.info(f"Starting Apps Script MCP Server v{__version__}")
    mcp.run()


if __name__ == "__main__":
    main()
