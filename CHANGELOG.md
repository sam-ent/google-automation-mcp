# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-04-17

### Added
- **Apps Script Router**: All 41 Workspace tools (Gmail, Drive, Sheets, Calendar, Docs, Forms, Tasks) now work through a per-user Apps Script Web App using clasp auth only — no GCP project required
- Automatic backend selection: router when no OAuth credentials, REST API when configured
- `MCP_USE_ROUTER` env var to force a specific backend (`true`, `false`, `auto`)
- `gmcp auth` now deploys the router and prints the authorization URL
- `gmcp status` shows router deployment state
- Tasks implemented via `UrlFetchApp` REST calls (no advanced service dependency)

### Fixed
- clasp token parsing for new format (`{"tokens":{"default":{...}}}` vs `{"token":{...}}`)
- Apps Script API enablement check in `gmcp auth` and `gmcp status`

### Changed
- README: added "Two Backends" comparison section and updated Quick Start with setup steps

## [0.1.0] - 2026-01-14

### Added
- Initial release
- OAuth 2.0 authentication with headless flow support
- 11 Apps Script tools:
  - `list_script_projects` - List all accessible projects (via Drive API)
  - `get_script_project` - Get project details with all files
  - `get_script_content` - Get specific file content
  - `create_script_project` - Create new project
  - `update_script_content` - Update project files
  - `run_script_function` - Execute script functions
  - `create_deployment` - Create versioned deployment
  - `list_deployments` - List all deployments
  - `update_deployment` - Update deployment config
  - `delete_deployment` - Remove deployment
  - `list_script_processes` - View execution history
- 2 authentication tools:
  - `start_google_auth` - Initiate OAuth flow
  - `complete_google_auth` - Complete OAuth with redirect URL
- Unit tests with mocked API responses
- GitHub Actions CI for Python 3.10, 3.11, 3.12
