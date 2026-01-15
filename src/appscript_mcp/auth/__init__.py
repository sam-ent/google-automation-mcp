"""
Authentication system for appscript-mcp.

Supports multiple auth methods:
- clasp (easiest, no GCP project needed)
- OAuth 2.0 (legacy, requires GCP project)
- OAuth 2.1 with PKCE (production, multi-user)

Forked from google_workspace_mcp with attribution.
"""

from .scopes import (
    SCOPES,
    get_scopes_for_tools,
    set_enabled_tools,
    TOOL_SCOPES_MAP,
)
from .credential_store import (
    CredentialStore,
    get_credential_store,
    set_credential_store,
)
from .oauth_config import (
    OAuthConfig,
    get_oauth_config,
    is_oauth_configured,
    is_oauth21_enabled,
    is_clasp_enabled,
)
from .clasp import (
    is_clasp_installed,
    is_clasp_authenticated,
    get_clasp_tokens,
    run_clasp_login,
    run_clasp_logout,
    install_clasp_global,
    detect_clasp_environment,
)
from .google_auth import (
    get_credentials,
    get_credentials_for_user,
    store_credentials,
    start_auth_flow,
    complete_auth_flow,
    auth_interactive,
    get_service,
    get_script_service,
    get_drive_service,
    get_gmail_service,
    get_sheets_service,
    get_calendar_service,
    get_docs_service,
    # Pending flow management for in-conversation auth
    set_pending_flow,
    get_pending_flow,
    clear_pending_flow,
)

__all__ = [
    # Scopes
    "SCOPES",
    "get_scopes_for_tools",
    "set_enabled_tools",
    "TOOL_SCOPES_MAP",
    # Credential Store
    "CredentialStore",
    "get_credential_store",
    "set_credential_store",
    # OAuth Config
    "OAuthConfig",
    "get_oauth_config",
    "is_oauth_configured",
    "is_oauth21_enabled",
    "is_clasp_enabled",
    # clasp
    "is_clasp_installed",
    "is_clasp_authenticated",
    "get_clasp_tokens",
    "run_clasp_login",
    "run_clasp_logout",
    "install_clasp_global",
    "detect_clasp_environment",
    # Google Auth
    "get_credentials",
    "get_credentials_for_user",
    "store_credentials",
    "start_auth_flow",
    "complete_auth_flow",
    "auth_interactive",
    "get_service",
    "get_script_service",
    "get_drive_service",
    "get_gmail_service",
    "get_sheets_service",
    "get_calendar_service",
    "get_docs_service",
    # Pending flow management
    "set_pending_flow",
    "get_pending_flow",
    "clear_pending_flow",
]
