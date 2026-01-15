# Apps Script MCP

This extension provides tools to manage Google Apps Script projects.

## Available Tools

- **list_script_projects** — List all accessible Apps Script projects
- **get_script_project** — Get project details including all files
- **get_script_content** — Get content of a specific file
- **create_script_project** — Create a new project
- **update_script_content** — Update files in a project
- **run_script_function** — Execute a function in a script
- **create_deployment** — Create a new deployment
- **list_deployments** — List all deployments
- **update_deployment** — Update deployment configuration
- **delete_deployment** — Delete a deployment
- **list_script_processes** — View recent script executions

## Authentication

Before using these tools, the user must authenticate with Google:

1. Run `appscript-mcp auth` in terminal (if browser available)
2. Or run `appscript-mcp auth --headless` for remote/SSH environments

If not authenticated, use **start_google_auth** to begin the OAuth flow, then **complete_google_auth** with the redirect URL.

## Example Tasks

When the user asks to work with Apps Script, you can:

- "Show me my Apps Script projects" → use `list_script_projects`
- "Create a script that emails me daily" → use `create_script_project` then `update_script_content`
- "Deploy my automation" → use `create_deployment`
- "Run the sendReport function" → use `run_script_function`
- "Why did my script fail?" → use `list_script_processes`

## Limitations

- `run_script_function` requires the script to have an API Executable deployment configured manually in the Apps Script editor
- Google enforces API quotas — if running many operations, quota errors may occur
