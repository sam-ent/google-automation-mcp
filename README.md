# Google Automation MCP

[![PyPI](https://img.shields.io/pypi/v/google-automation-mcp)](https://pypi.org/project/google-automation-mcp/) [![Tests](https://github.com/sam-ent/google-automation-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sam-ent/google-automation-mcp/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/sam-ent/google-automation-mcp/graph/badge.svg)](https://codecov.io/gh/sam-ent/google-automation-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io) [![Downloads](https://img.shields.io/pypi/dm/google-automation-mcp)](https://pypi.org/project/google-automation-mcp/) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Google Workspace APIs for AI agents - no GCP project required.**

Uses [clasp](https://github.com/google/clasp) for authentication. No GCP console, no OAuth consent screen, no client secrets. Just authenticate and go.

## Quick Start

```bash
uvx google-automation-mcp auth   # 1. Browser sign-in via clasp
uvx google-automation-mcp        # 4. Run server
```

First run walks you through three one-time steps:

1. **`gmcp auth`** - opens browser for Google sign-in (clasp OAuth)
2. **Enable Apps Script API** - `gmcp auth` checks and prompts you to toggle ON at https://script.google.com/home/usersettings (5 seconds)
3. **Authorize scopes** - `gmcp auth` deploys a Web App router and prints a URL. Open it, click "Allow" to grant Gmail/Drive/Sheets/Calendar/Docs/Forms/Tasks access
4. **Done** - run `gmcp` or `uvx google-automation-mcp` to start the server

Check status anytime: `gmcp status`

> **Tip:** Use the short alias `gmcp` after installing.

> **Re-authorization:** If a future update adds new scopes, revoke the app at [myaccount.google.com/permissions](https://myaccount.google.com/permissions) (find "MCP-Router"), then visit the Web App URL again from `gmcp status`.

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

**Claude Desktop (One-Click Install):**

Download [`google-automation-mcp.dxt`](https://github.com/sam-ent/google-automation-mcp/releases/latest) and open it. Claude Desktop will install automatically.

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

**Claude Desktop (Manual)** (`claude_desktop_config.json`):
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

Apps Script tools let you deploy code that runs inside Google apps - things REST APIs cannot do:

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

**`run_script_function`** requires one-time setup per script: Open script at script.google.com → Project Settings → Change GCP project → Deploy as API Executable. Once configured, functions can be called repeatedly. All other tools work without this setup.

**API quotas**: Google enforces [rate limits](https://developers.google.com/apps-script/guides/services/quotas).

## Production: OAuth 2.1

For multi-user deployments requiring your own OAuth credentials:

```bash
export GOOGLE_OAUTH_CLIENT_ID='...'
export GOOGLE_OAUTH_CLIENT_SECRET='...'
gmcp auth --oauth21
```

## Two Backends: Clasp Router vs REST API

Workspace tools (Gmail, Drive, Sheets, etc.) can operate in two modes:

| | **Clasp Router** (default) | **REST API** (with OAuth 2.1) |
|---|---|---|
| **Setup time** | ~2 min (browser sign-in + one toggle + one Allow click) | ~15 min (GCP project + enable APIs + OAuth consent screen + credentials) |
| **GCP project** | Not needed | Required |
| **How it works** | Deploys an Apps Script Web App per user; tool calls routed via HTTP POST | Calls Google REST APIs directly with OAuth tokens |
| **Latency** | ~1–3s per call (Apps Script execution overhead) | ~100–300ms per call |
| **Execution timeout** | 30s per call (Apps Script limit) | No per-call limit |
| **Best for** | Personal use, prototyping, AI agents | High-volume, production, low-latency apps |

### Daily quotas (free consumer Google account)

| Service | Clasp Router (Apps Script limits) | REST API limits |
|---------|----------------------------------|-----------------|
| **Gmail send** | 100 recipients/day | 500 emails/day (Gmail API) |
| **Gmail read** | 50,000 reads/day | 250 quota units/s per user |
| **Drive** | 90 min total runtime/day | 1 billion API calls/day (project) |
| **Sheets** | 90 min total runtime/day | 300 requests/min per project |
| **Calendar** | 5,000 events created/day | 1M queries/day per project |
| **Docs** | 90 min total runtime/day | 300 requests/min per project |
| **Forms** | 90 min total runtime/day | No published limit |
| **Tasks** | Same as REST (calls Tasks API via `UrlFetchApp`) | 50,000 requests/day |

> **Note:** Apps Script runtime limits are shared across all services. The 90 min/day limit applies to total execution time, not per-service. At ~2s per call, that's ~2,700 tool calls/day. [Full Apps Script quotas](https://developers.google.com/apps-script/guides/services/quotas)

### Backend selection

The backend is selected automatically: if `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are set, REST APIs are used. Otherwise, the clasp router handles Workspace calls.

Override with `MCP_USE_ROUTER=true` or `MCP_USE_ROUTER=false` to force a specific backend.

## CLI Reference

Short alias: `gmcp` (or full name: `google-automation-mcp`)

```bash
gmcp                 # Run server
gmcp setup           # Interactive setup wizard
gmcp auth            # Authenticate with clasp
gmcp auth --oauth21  # OAuth 2.1 for production
gmcp status          # Check auth status
gmcp version         # Show version
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
