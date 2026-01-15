# Apps Script MCP

[![Tests](https://github.com/sam-ent/appscript-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sam-ent/appscript-mcp/actions/workflows/test.yml)

**AI-powered Google Apps Script management for Claude, Cursor, and other MCP clients**

Google's vision: *"Automate & extend Google Workspace"* and *"Power your scripts with AI."*
This MCP makes that real — manage, write, deploy, and execute Apps Script projects through natural conversation.

## Why This Exists

| Traditional Workflow | With Apps Script MCP |
|---------------------|---------------------|
| Open browser → script.google.com → find project → edit code → save → deploy → test → repeat | *"Add error handling to my form processor and deploy it"* |
| Context-switch between IDE, docs, and console | Stay in your AI workflow |
| Manual copy-paste between ChatGPT and editor | AI writes directly to your scripts |

## What You Can Do

```
"Show me my Apps Script projects"
"Create a script that sends weekly expense reports from my spreadsheet"
"Add a time-based trigger to run syncData every morning at 9am"
"Deploy my automation to production"
"Why did my last execution fail?"
```

## Features

- **Project Management** — List, create, read, and update Apps Script projects
- **Code Editing** — View and modify script files (JavaScript, HTML, JSON)
- **Execution** — Run script functions with parameters
- **Deployments** — Create, list, update, and delete deployments
- **Monitoring** — View recent script executions and their status

## Tested With

- **Claude Desktop** — macOS, Windows
- **Claude Code** — CLI
- **Cursor** — IDE

Should work with any MCP-compatible client.

## Quick Start

### 1. Install

```bash
git clone https://github.com/sam-ent/appscript-mcp.git
cd appscript-mcp
uv sync  # or: pip install -e .
```

### 2. Setup Google Cloud (One-Time)

<details>
<summary><strong>Click to expand setup steps</strong></summary>

1. **[Enable APIs](https://console.cloud.google.com/flows/enableapi?apiid=script.googleapis.com,drive.googleapis.com)** — Click link, select your project, enable.

2. **[Create OAuth Credentials](https://console.cloud.google.com/apis/credentials)** → Create Credentials → OAuth client ID → Desktop app → Download JSON

3. **Save credentials:**
   ```bash
   mkdir -p ~/.appscript-mcp
   mv ~/Downloads/client_secret_*.json ~/.appscript-mcp/client_secret.json
   ```

4. **[Add yourself as test user](https://console.cloud.google.com/apis/credentials/consent)** — OAuth consent screen → Test users → Add your email

</details>

### 3. Authenticate

**If you have a browser** (local machine, X11, etc.):
```bash
appscript-mcp auth
```
Opens your browser, you consent, done.

**If headless** (SSH, remote server, container):
```bash
appscript-mcp auth --headless
```
Prints a URL. Open it in any browser, consent, paste the redirect URL back.

### 4. Configure MCP Client

**Claude Desktop** — Add to config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "appscript": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/appscript-mcp", "appscript-mcp"]
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
      "command": "/path/to/appscript-mcp/.venv/bin/python",
      "args": ["-m", "appscript_mcp.server"],
      "env": {
        "MCP_TIMEOUT": "30000",
        "MCP_TOOL_TIMEOUT": "90000"
      }
    }
  }
}
```

### 5. Start Using

```
"List my Apps Script projects"
"Create a new script called 'Daily Report'"
"Show me the code in my Daily Report script"
```

## Authentication Reference

Three ways to authenticate, all produce the same result:

| Method | When to Use |
|--------|-------------|
| `appscript-mcp auth` | Local machine with browser access |
| `appscript-mcp auth --headless` | SSH/remote without local browser |
| In-conversation (`start_google_auth`) | When you forgot to auth before starting |

Credentials are cached in `~/.appscript-mcp/token.pickle` for future sessions.

## Available Tools

### Authentication
| Tool | Description |
|------|-------------|
| `start_google_auth` | Start OAuth flow, returns authorization URL |
| `complete_google_auth` | Complete OAuth with redirect URL |

### Project Management
| Tool | Description |
|------|-------------|
| `list_script_projects` | List all accessible Apps Script projects |
| `get_script_project` | Get project details including all files |
| `get_script_content` | Get content of a specific file |
| `create_script_project` | Create a new project |
| `update_script_content` | Update files in a project |

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

### Monitoring
| Tool | Description |
|------|-------------|
| `list_script_processes` | View recent script executions |

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
