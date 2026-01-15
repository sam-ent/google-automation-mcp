# Google Automation MCP

[![PyPI](https://img.shields.io/pypi/v/google-automation-mcp)](https://pypi.org/project/google-automation-mcp/)
[![Tests](https://github.com/sam-ent/google-automation-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sam-ent/google-automation-mcp/actions/workflows/test.yml)

**Google Workspace APIs for AI agents.** 50 tools for Gmail, Drive, Sheets, Calendar, Docs, and Apps Script — with zero GCP setup and credentials never exposed to AI.

## Why This MCP?

| | Direct Google APIs | This MCP |
|---|---|---|
| **Setup** | Create GCP project → Enable APIs → OAuth consent screen → Create credentials → Download JSON | `google-automation-mcp auth` — uses [clasp](https://github.com/google/clasp), no GCP project needed |
| **Credentials** | AI agent sees and handles tokens directly | AI never sees credentials — MCP handles auth internally |
| **API Surface** | AI can call any endpoint | AI limited to 50 curated, auditable operations |
| **Token Refresh** | Implement refresh logic per API call | Auth once, auto-refresh forever |
| **Multi-user** | Build credential storage yourself | Built-in per-user credential management |

**Summary:** Uses clasp for zero GCP setup. Auth once. AI never sees credentials. 50 curated tools.

## Quick Start

### 1. Install

```bash
uvx google-automation-mcp
```

### 2. Authenticate

```bash
uvx google-automation-mcp auth
```

Opens browser for Google sign-in. Tokens auto-refresh after that.

### 3. Configure Your MCP Client

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

## Zero GCP Setup with clasp

The main advantage: **authenticate without creating a GCP project.**

Traditional Google API setup:
1. Create GCP project
2. Enable APIs
3. Configure OAuth consent screen
4. Add test users
5. Create OAuth credentials
6. Download client_secret.json

With this MCP:
```bash
google-automation-mcp auth   # Uses clasp, done in 30 seconds
```

[clasp](https://github.com/google/clasp) is Google's official Apps Script CLI. It handles OAuth without requiring a GCP project, making it ideal for:
- Quick setup on new machines
- Server deployments where GCP configuration is impractical
- Multi-user scenarios with per-user credential storage

### Multi-User Credentials

All tools accept `user_google_email` for per-user isolation:

```python
# Each user's credentials stored separately in ~/.secrets/google-automation-mcp/credentials/
search_gmail_messages(user_google_email="alice@example.com", query="is:unread")
search_gmail_messages(user_google_email="bob@example.com", query="is:unread")
```

## Example: Apps Script Automation

Create and deploy a custom spreadsheet function:

```python
# 1. Create a script bound to a spreadsheet
create_script_project(
    user_google_email="user@example.com",
    title="Data Validator",
    parent_id="SPREADSHEET_ID"
)

# 2. Add custom function code
update_script_content(
    user_google_email="user@example.com",
    script_id="...",
    files=[{
        "name": "Code",
        "type": "SERVER_JS",
        "source": """
function VALIDATE_EMAIL(email) {
  return /^[^@]+@[^@]+\\.[^@]+$/.test(email);
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Validation')
    .addItem('Check All Emails', 'validateAllEmails')
    .addToUi();
}
"""
    }]
)

# 3. Generate trigger code if needed
generate_trigger_code(trigger_type="time_daily", function_name="dailyReport", schedule="9")
```

Now `=VALIDATE_EMAIL(A1)` works in the spreadsheet, and a custom menu appears.

## Available Tools (50)

### Gmail (5)
| Tool | Description |
|------|-------------|
| `search_gmail_messages` | Search with Gmail query syntax |
| `get_gmail_message` | Get message content by ID |
| `send_gmail_message` | Send email (plain or HTML) |
| `list_gmail_labels` | List all labels |
| `modify_gmail_labels` | Add/remove labels (archive, star, mark read) |

### Drive (10)
| Tool | Description |
|------|-------------|
| `search_drive_files` | Search with Drive query operators |
| `list_drive_items` | List folder contents |
| `get_drive_file_content` | Download/export file content |
| `create_drive_file` | Create new file |
| `create_drive_folder` | Create folder |
| `delete_drive_file` | Permanently delete |
| `trash_drive_file` | Move to trash |
| `share_drive_file` | Share with user |
| `list_drive_permissions` | List who has access |
| `remove_drive_permission` | Revoke access |

### Sheets (6)
| Tool | Description |
|------|-------------|
| `list_spreadsheets` | List spreadsheets |
| `get_sheet_values` | Read cell range |
| `update_sheet_values` | Write to cell range |
| `append_sheet_values` | Append rows |
| `create_spreadsheet` | Create new spreadsheet |
| `get_spreadsheet_metadata` | List sheets/tabs |

### Calendar (5)
| Tool | Description |
|------|-------------|
| `list_calendars` | List calendars |
| `get_events` | Get events |
| `create_event` | Create event |
| `update_event` | Modify event |
| `delete_event` | Delete event |

### Docs (5)
| Tool | Description |
|------|-------------|
| `search_docs` | Search by name |
| `get_doc_content` | Get text content |
| `create_doc` | Create document |
| `modify_doc_text` | Insert/replace text |
| `append_doc_text` | Append to end |

### Apps Script (17)
| Tool | Description |
|------|-------------|
| `list_script_projects` | List projects |
| `get_script_project` | Get project with files |
| `get_script_content` | Get file content |
| `create_script_project` | Create project (standalone or bound) |
| `update_script_content` | Update project files |
| `delete_script_project` | Delete project |
| `run_script_function` | Execute function (requires setup) |
| `create_deployment` | Deploy project |
| `list_deployments` | List deployments |
| `update_deployment` | Update deployment |
| `delete_deployment` | Delete deployment |
| `list_versions` | List versions |
| `create_version` | Create version |
| `get_version` | Get version details |
| `list_script_processes` | View executions |
| `get_script_metrics` | Execution analytics |
| `generate_trigger_code` | Generate trigger code |

### Auth (2)
| Tool | Description |
|------|-------------|
| `start_google_auth` | Start OAuth flow |
| `complete_google_auth` | Complete OAuth |

## Apps Script: When You Need It

Most automation uses Workspace tools directly. Apps Script is for extending Google Workspace UI — things REST APIs cannot do:

| Capability | Example |
|------------|---------|
| Custom spreadsheet functions | `=VALIDATE_EMAIL(A1)` in cells |
| Real-time `onEdit` trigger | React when user edits a cell |
| Real-time `onOpen` trigger | Run code when document opens |
| Custom menus | Add menu items to Sheets/Docs UI |
| Sidebar panels | Custom UI inside Google apps |
| Webhooks | `doGet`/`doPost` HTTP handlers |

### Bound Scripts

Attach scripts to specific documents:

```python
create_script_project(title="My Script", parent_id="SPREADSHEET_ID")
```

Bound scripts can use `onOpen`, `onEdit`, custom menus, and `SpreadsheetApp.getActiveSpreadsheet()`.

## Limitations

### run_script_function Setup

Executing Apps Script functions via API requires manual setup:

1. Open script at script.google.com
2. Project Settings → Change GCP project
3. Deploy → New deployment → API Executable

All other tools work without this.

### API Quotas

Google enforces [rate limits](https://developers.google.com/apps-script/guides/services/quotas) on API calls.

## Security

| Aspect | Direct API | MCP |
|--------|------------|-----|
| Credentials | AI handles tokens | AI never sees tokens |
| API access | Any endpoint | 50 curated tools only |
| Audit | Build your own | Every tool call logged |

## CLI Reference

```bash
google-automation-mcp           # Run server
google-automation-mcp setup     # Interactive setup
google-automation-mcp auth      # Authenticate (clasp)
google-automation-mcp auth --oauth21  # OAuth 2.1 for production
google-automation-mcp status    # Check auth status
google-automation-mcp version   # Show version
```

**Credentials:** `~/.secrets/google-automation-mcp/credentials/{email}.json`

## Production: OAuth 2.1

For multi-user deployments:

```bash
export GOOGLE_OAUTH_CLIENT_ID='...'
export GOOGLE_OAUTH_CLIENT_SECRET='...'
google-automation-mcp auth --oauth21
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
