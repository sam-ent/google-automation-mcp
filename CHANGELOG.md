# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
