# Apps Script MCP

[![PyPI](https://img.shields.io/pypi/v/appscript-mcp)](https://pypi.org/project/appscript-mcp/)
[![Tests](https://github.com/sam-ent/appscript-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sam-ent/appscript-mcp/actions/workflows/test.yml)

**Built for AI.** Give Claude a remote control to your Google account. Create, deploy, and run Apps Script automations directly — no copy-paste, no manual setup.

> **Tip:** View on [GitHub](https://github.com/sam-ent/appscript-mcp) for copy buttons on code blocks.

## Why This Exists

Direct Google APIs are designed for software. This MCP is designed for AI.

| | Direct APIs (You code) | This MCP (Claude codes) |
|---|---|---|
| **Setup** | Local dev environment, OAuth libraries | One-time auth, Claude handles the rest |
| **Runtime** | Scripts run on your machine | Scripts run in Google's cloud |
| **Workflow** | Claude writes → you copy → you debug | Claude writes → Claude deploys → Claude tests |
| **Triggers** | Need a server running 24/7 | Native Apps Script triggers in the cloud |
| **Scope** | Limited to specific APIs | Full Apps Script (MailApp, DriveApp, etc.) |

## What You Can Build

```
"Every day at 9 AM, scan my Invoices folder in Drive, extract totals to this Sheet, and email me a summary"
"When someone submits my Google Form, generate a Doc from a template and email it to them"
"Add a custom function to my spreadsheet that validates email formats"
"Archive Drive files older than 90 days to a backup folder every week"
```

Claude writes the code, deploys it to Google's cloud, and sets up triggers — all running 24/7 without your computer on.

## Features

**Apps Script Management:**
- **CRUD** — Create, read, update, delete Apps Script projects
- **Code Editing** — View and modify script files (JavaScript, HTML, JSON)
- **Execution** — Run script functions with parameters
- **Deployments** — Create, list, update, and delete deployments
- **Versions** — Create and manage immutable version snapshots
- **Monitoring** — View executions, metrics, and analytics

**Google Workspace Context** (via [workspace-mcp](https://github.com/taylorwilsdon/google_workspace_mcp)):
- **Gmail** — Read emails, search, send, manage labels
- **Drive** — List files, read content, search
- **Sheets** — Read/write spreadsheet data
- **Calendar** — View and create events
- **Docs** — Read and create documents

Claude can see your actual Gmail, Drive, and Sheets data while building automations — no guessing.

**OAuth & Credentials:**
- **clasp authentication** — No GCP project needed, uses Google's official CLI
- **Automatic token refresh** — Tokens refresh automatically when expired
- **Secure storage** — Tokens stored in `~/.secrets/appscript-mcp/` with restricted permissions
- **Legacy support** — Environment variables or JSON file for advanced users

## Tested With

- **Claude Desktop** — macOS, Windows
- **Claude Code** — CLI
- **Cursor** — IDE
- **Gemini CLI** — Google's AI CLI

Should work with any MCP-compatible client.

## Quick Start

### 1. Install

**Instant (no clone needed):**
```bash
uvx appscript-mcp  # runs directly from PyPI
```

**Global install:**
```bash
uv tool install appscript-mcp  # installs 'appscript-mcp' command
```

**Gemini CLI:**
```bash
gemini extensions install github:sam-ent/appscript-mcp
```

**From source:**
```bash
git clone https://github.com/sam-ent/appscript-mcp.git
cd appscript-mcp
uv sync  # then use 'uv run appscript-mcp'
```

### 2. Authenticate

**With clasp (recommended — no GCP project needed):**
```bash
uvx appscript-mcp auth
```

This uses [clasp](https://github.com/google/clasp), Google's official Apps Script CLI. If clasp isn't installed, the command will offer to install it for you.

The authentication flow:
1. Opens your browser for Google OAuth
2. You consent to the required permissions
3. Tokens are saved securely to `~/.secrets/appscript-mcp/`

That's it. No GCP project, no API enabling, no client secrets.

<details>
<summary><strong>Alternative: Legacy OAuth (advanced users)</strong></summary>

If you need headless authentication or want to use your own GCP project:

1. **[Enable APIs](https://console.cloud.google.com/flows/enableapi?apiid=script.googleapis.com,drive.googleapis.com)** — Click link, select your project, enable.

2. **[Create OAuth Credentials](https://console.cloud.google.com/apis/credentials)** → Create Credentials → OAuth client ID → Desktop app → Download JSON

3. **Configure credentials** (choose one):

   **Option A: Environment variables**
   ```bash
   export GOOGLE_OAUTH_CLIENT_ID='your-client-id'
   export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'
   ```

   **Option B: JSON file**
   ```bash
   mkdir -p ~/.appscript-mcp
   mv ~/Downloads/client_secret_*.json ~/.appscript-mcp/client_secret.json
   ```

4. **[Add yourself as test user](https://console.cloud.google.com/apis/credentials/consent)** — OAuth consent screen → Test users → Add your email

5. **Authenticate:**
   ```bash
   # With browser
   uvx appscript-mcp auth --legacy

   # Headless (SSH, remote server)
   uvx appscript-mcp auth --legacy --headless
   ```

</details>

### 3. Configure MCP Client

**Claude Desktop** — Add to config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "appscript": {
      "command": "uvx",
      "args": ["appscript-mcp"]
    }
  }
}
```

**Claude Code** — Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "appscript": {
      "type": "stdio",
      "command": "uvx",
      "args": ["appscript-mcp"],
      "env": {
        "MCP_TIMEOUT": "30000",
        "MCP_TOOL_TIMEOUT": "90000"
      }
    }
  }
}
```

### 4. Start Using

```
"List my Apps Script projects"
"Create a new script called 'Daily Report'"
"Show me the code in my Daily Report script"
```

## Authentication Reference

| Method | When to Use |
|--------|-------------|
| `appscript-mcp auth` | Default — uses clasp, no GCP project needed |
| `appscript-mcp auth --legacy` | Use your own GCP OAuth credentials |
| `appscript-mcp auth --legacy --headless` | Headless environments with custom credentials |
| In-conversation (`start_google_auth`) | Re-authenticate without leaving the conversation |

**Token storage:**
- Primary: `~/.secrets/appscript-mcp/token.json` (secure, 600 permissions)
- clasp tokens: Read from `~/.clasprc.json` and copied to secure storage
- Legacy: `~/.appscript-mcp/token.pickle` (auto-migrated to secure storage)

## Available Tools

### Authentication
| Tool | Description |
|------|-------------|
| `start_google_auth` | Start OAuth flow, returns authorization URL |
| `complete_google_auth` | Complete OAuth with redirect URL |

### CRUD
| Tool | Description |
|------|-------------|
| `list_script_projects` | List all accessible Apps Script projects |
| `get_script_project` | Get project details including all files |
| `get_script_content` | Get content of a specific file |
| `create_script_project` | Create a new project (standalone or bound to Sheet/Doc/Form/Slides) |
| `update_script_content` | Update files in a project |
| `delete_script_project` | Delete a project (permanent) |

### Execution
| Tool | Description |
|------|-------------|
| `run_script_function` | Execute a function in a script |

### Deployments
| Tool | Description |
|------|-------------|
| `create_deployment` | Create a new deployment |
| `list_deployments` | List all deployments |
| `update_deployment` | Update deployment configuration |
| `delete_deployment` | Delete a deployment |

### Versions
| Tool | Description |
|------|-------------|
| `list_versions` | List all versions of a script |
| `create_version` | Create an immutable version snapshot |
| `get_version` | Get details of a specific version |

### Monitoring
| Tool | Description |
|------|-------------|
| `list_script_processes` | View recent script executions |
| `get_script_metrics` | Get execution analytics (active users, executions, failures) |

### Triggers
| Tool | Description |
|------|-------------|
| `generate_trigger_code` | Generate Apps Script code for time-based or event triggers |

## Bound Scripts

Create scripts attached to Google Sheets, Docs, Forms, or Slides:

```
"Create a script bound to my spreadsheet https://docs.google.com/spreadsheets/d/ABC123/edit"
```

Pass the document ID as `parent_id` to `create_script_project`. Bound scripts can:
- Add custom menus to the document
- Use `onOpen` and `onEdit` simple triggers
- Access `SpreadsheetApp.getActiveSpreadsheet()` directly

## Triggers

The Apps Script REST API cannot create triggers directly. Use `generate_trigger_code` to get code you can add to your script:

```
"Generate code for a daily trigger that runs sendReport at 9am"
```

**Supported trigger types:**
- `time_minutes` — Run every 1, 5, 10, 15, or 30 minutes
- `time_hours` — Run every 1, 2, 4, 6, 8, or 12 hours
- `time_daily` — Run daily at a specific hour
- `time_weekly` — Run weekly on a specific day
- `on_open` — Run when document opens (simple trigger)
- `on_edit` — Run when user edits (simple trigger)
- `on_form_submit` — Run when form is submitted
- `on_change` — Run when spreadsheet changes

## Limitations

### run_script_function Requires API Executable Deployment

The `run_script_function` tool requires manual configuration in the Apps Script editor:

1. Open the script in the Apps Script editor
2. Go to Project Settings (gear icon)
3. Under "Google Cloud Platform (GCP) Project", click "Change project"
4. Enter your GCP project number
5. Click "Deploy" > "New deployment"
6. Select type: "API Executable"
7. Set "Who has access" to "Anyone" or "Anyone with Google account"
8. Click "Deploy"

All other tools work without this manual step.

### API Quotas

Google enforces rate limits on the Apps Script API. If running many operations, you may encounter quota errors. See [Apps Script Quotas](https://developers.google.com/apps-script/guides/services/quotas) for details.

## Roadmap

- [x] Trigger code generation (time-based, event-driven)
- [x] Bound scripts support (Sheets, Docs, Forms, Slides)
- [x] Version management (create, list, get versions)
- [x] Execution metrics and analytics
- [x] PyPI package (`uvx appscript-mcp`)
- [x] Google Workspace context (Gmail, Drive, Sheets, Calendar, Docs)
- [x] clasp authentication (no GCP project needed)
- [x] Secure token storage (`~/.secrets/` with 600 permissions)
- [ ] Claude Desktop one-click install (DXT)

See [Issues](https://github.com/sam-ent/appscript-mcp/issues) to request features or report bugs.

## Development

### Run Tests
```bash
uv run pytest tests/ -v
```

### Run Server Directly
```bash
uv run appscript-mcp
```

## License

MIT License - see LICENSE file
