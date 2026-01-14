# Apps Script MCP

MCP server for Google Apps Script - create, manage, and execute Apps Script projects through natural language.

## Features

- **Project Management**: List, create, read, and update Apps Script projects
- **Code Editing**: View and modify script files (JavaScript, HTML, JSON)
- **Execution**: Run script functions with parameters
- **Deployments**: Create, list, update, and delete deployments
- **Monitoring**: View recent script executions and their status

## Installation

```bash
# Clone the repository
git clone https://github.com/sam-ent/appscript-mcp.git
cd appscript-mcp

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Prerequisites

### 1. Google Cloud Project Setup

Before using the MCP server, configure your Google Cloud project:

**Enable Required APIs**

Enable these APIs in your Google Cloud Console:
- [Apps Script API](https://console.cloud.google.com/flows/enableapi?apiid=script.googleapis.com)
- [Google Drive API](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com)

**Create OAuth Credentials**

1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop application" as the application type
4. Download the JSON file

**Save Credentials**

Save the downloaded JSON file to one of these locations:
- `~/.appscript-mcp/client_secret.json` (recommended)
- `./client_secret.json` (current directory)
- `~/.secrets/client_secret.json`

Or set the environment variable:
```bash
export GOOGLE_CLIENT_SECRET_PATH=/path/to/client_secret.json
```

**Configure OAuth Consent Screen**

1. Go to [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. Add yourself as a test user (required for unverified apps)

### 2. Configure MCP Client

**Claude Desktop**

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

**Claude Code**

Add to `~/.mcp.json`:

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

## Authentication

On first use, authenticate with Google:

1. Ask the assistant to "authenticate with Google" or use `start_google_auth`
2. Open the provided URL in your browser
3. Sign in and authorize the application
4. Copy the redirect URL (the page will not load - that's expected)
5. Provide the redirect URL to `complete_google_auth`

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

## Usage Examples

### List Projects
```
"Show me my Apps Script projects"
```

### Create a Project
```
"Create a new Apps Script project called 'Email Automation'"
```

### Add Code to a Project
```
"Add a function to my Email Automation script that sends a daily summary email"
```

### Execute a Function
```
"Run the sendDailySummary function in my Email Automation script"
```

### Deploy
```
"Create a production deployment for my Email Automation script"
```

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
