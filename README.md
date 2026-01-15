# Google Automation MCP

[![PyPI](https://img.shields.io/pypi/v/google-automation-mcp)](https://pypi.org/project/google-automation-mcp/)
[![Tests](https://github.com/sam-ent/google-automation-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sam-ent/google-automation-mcp/actions/workflows/test.yml)

**Google Workspace APIs for AI agents — no GCP project required.**

Uses [clasp](https://github.com/google/clasp) for authentication. No GCP console, no OAuth consent screen, no client secrets. Just authenticate and go.

## Quick Start

```bash
# 1. Install
uvx google-automation-mcp

# 2. Authenticate (opens browser once, then tokens auto-refresh)
uvx google-automation-mcp auth

# 3. Add to your MCP client config and start using
```

That's it. No GCP project setup.

## Why No GCP Project?

Traditional Google API setup requires:
1. Create GCP project
2. Enable APIs
3. Configure OAuth consent screen
4. Add test users
5. Create OAuth credentials
6. Download client_secret.json

This MCP uses **clasp** (Google's official Apps Script CLI) which handles OAuth without a GCP project. Same Google authentication, zero configuration.

## Security: AI Never Sees Credentials

| | Direct API | This MCP |
|---|---|---|
| **Credentials** | AI handles tokens directly | AI never sees tokens |
| **API access** | Any endpoint | 50 curated tools only |
| **Audit** | Build your own | Every tool call logged |

The MCP acts as a security boundary. Your AI agent calls tools; the MCP handles authentication internally.

## MCP Client Configuration

**Claude Code** (`~/.mcp.json`):
```json
{
  "mcpServers": {
    "google": {
      "type": "stdio",
      "command": "uvx",
      "args": ["google-automation-mcp"]
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "google": {
      "command": "uvx",
      "args": ["google-automation-mcp"]
    }
  }
}
```

**Gemini CLI:**
```bash
gemini extensions install github:sam-ent/google-automation-mcp
```

## Available Tools (50)

### Gmail (5)
`search_gmail_messages` · `get_gmail_message` · `send_gmail_message` · `list_gmail_labels` · `modify_gmail_labels`

### Drive (10)
`search_drive_files` · `list_drive_items` · `get_drive_file_content` · `create_drive_file` · `create_drive_folder` · `delete_drive_file` · `trash_drive_file` · `share_drive_file` · `list_drive_permissions` · `remove_drive_permission`

### Sheets (6)
`list_spreadsheets` · `get_sheet_values` · `update_sheet_values` · `append_sheet_values` · `create_spreadsheet` · `get_spreadsheet_metadata`

### Calendar (5)
`list_calendars` · `get_events` · `create_event` · `update_event` · `delete_event`

### Docs (5)
`get_doc_content` · `search_docs` · `create_doc` · `modify_doc_text` · `append_doc_text`

### Apps Script (17)
`list_script_projects` · `get_script_project` · `get_script_content` · `create_script_project` · `update_script_content` · `delete_script_project` · `run_script_function` · `create_deployment` · `list_deployments` · `update_deployment` · `delete_deployment` · `list_versions` · `create_version` · `get_version` · `list_script_processes` · `get_script_metrics` · `generate_trigger_code`

### Auth (2)
`start_google_auth` · `complete_google_auth`

## Multi-User Support

All tools accept `user_google_email` for per-user credential isolation:

```python
search_gmail_messages(user_google_email="alice@example.com", query="is:unread")
search_gmail_messages(user_google_email="bob@example.com", query="is:unread")
```

Credentials stored separately: `~/.secrets/google-automation-mcp/credentials/{email}.json`

## Apps Script: Extending Google Workspace

Apps Script tools let you deploy code that runs inside Google apps — things REST APIs cannot do:

| Capability | Example |
|------------|---------|
| Custom spreadsheet functions | `=VALIDATE_EMAIL(A1)` in cells |
| Real-time triggers | `onEdit`, `onOpen` |
| Custom menus | Add menu items to Sheets/Docs |
| Webhooks | `doGet`/`doPost` handlers |

```python
# Create a bound script with custom function
create_script_project(title="Validator", parent_id="SPREADSHEET_ID")
update_script_content(script_id="...", files=[{
    "name": "Code",
    "type": "SERVER_JS",
    "source": "function VALIDATE_EMAIL(e) { return /^[^@]+@[^@]+\\.[^@]+$/.test(e); }"
}])
```

## Limitations

**`run_script_function`** requires manual setup: Open script at script.google.com → Project Settings → Change GCP project → Deploy as API Executable. All other tools work without this.

**API quotas**: Google enforces [rate limits](https://developers.google.com/apps-script/guides/services/quotas).

## Production: OAuth 2.1

For multi-user deployments requiring your own OAuth credentials:

```bash
export GOOGLE_OAUTH_CLIENT_ID='...'
export GOOGLE_OAUTH_CLIENT_SECRET='...'
google-automation-mcp auth --oauth21
```

## CLI Reference

```bash
google-automation-mcp           # Run server
google-automation-mcp setup     # Interactive setup wizard
google-automation-mcp auth      # Authenticate with clasp
google-automation-mcp auth --oauth21  # OAuth 2.1 for production
google-automation-mcp status    # Check auth status
google-automation-mcp version   # Show version
```

## Development

```bash
git clone https://github.com/sam-ent/google-automation-mcp.git
cd google-automation-mcp
uv sync
uv run pytest tests/ -v  # 45 tests
```

## Acknowledgments

Built on [google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) by Taylor Wilsdon (MIT License).

## License

MIT
