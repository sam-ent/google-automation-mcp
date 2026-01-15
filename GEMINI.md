# Apps Script MCP

This extension provides tools to manage Google Apps Script projects.

## Available Tools

- **list_script_projects** — List all accessible Apps Script projects
- **get_script_project** — Get project details including all files
- **get_script_content** — Get content of a specific file
- **create_script_project** — Create a new project (standalone or bound to Sheet/Doc/Form/Slides)
- **update_script_content** — Update files in a project
- **delete_script_project** — Delete a project (permanent, cannot be undone)
- **run_script_function** — Execute a function in a script
- **create_deployment** — Create a new deployment
- **list_deployments** — List all deployments
- **update_deployment** — Update deployment configuration
- **delete_deployment** — Delete a deployment
- **list_versions** — List all versions of a script
- **create_version** — Create an immutable version snapshot
- **get_version** — Get details of a specific version
- **list_script_processes** — View recent script executions
- **get_script_metrics** — Get execution analytics (active users, executions, failures)
- **generate_trigger_code** — Generate Apps Script code for triggers

## Authentication

Before using these tools, the user must authenticate with Google:

1. Run `appscript-mcp auth` in terminal (if browser available)
2. Or run `appscript-mcp auth --headless` for remote/SSH environments

If not authenticated, use **start_google_auth** to begin the OAuth flow, then **complete_google_auth** with the redirect URL.

## Bound Scripts

To create a script attached to a Google Sheet, Doc, Form, or Slides:

- Use `create_script_project` with the document ID as `parent_id`
- Extract the ID from the document URL (e.g., `docs.google.com/spreadsheets/d/{ID}/edit`)

Bound scripts can use `onOpen`, `onEdit` triggers and access document-specific APIs.

## Triggers

The API cannot create triggers directly. Use `generate_trigger_code` to generate Apps Script code:

- **time_minutes** / **time_hours** / **time_daily** / **time_weekly** — Scheduled triggers
- **on_open** / **on_edit** — Simple triggers (just add the code)
- **on_form_submit** / **on_change** — Event triggers

The generated code includes a setup function the user runs once to install the trigger.

## Example Tasks

When the user asks to work with Apps Script, you can:

- "Show me my Apps Script projects" → use `list_script_projects`
- "Create a script that emails me daily" → use `create_script_project` then `update_script_content`
- "Create a script bound to this spreadsheet" → use `create_script_project` with `parent_id`
- "Set up a daily trigger for sendReport at 9am" → use `generate_trigger_code`
- "Deploy my automation" → use `create_deployment`
- "Run the sendReport function" → use `run_script_function`
- "Why did my script fail?" → use `list_script_processes`
- "Create a version snapshot before I deploy" → use `create_version`
- "Show me all versions of this script" → use `list_versions`
- "How many people are using my script?" → use `get_script_metrics`

## Limitations

- `run_script_function` requires the script to have an API Executable deployment configured manually in the Apps Script editor
- Triggers cannot be created via API — use `generate_trigger_code` and add the code to the script
- Google enforces API quotas — if running many operations, quota errors may occur
