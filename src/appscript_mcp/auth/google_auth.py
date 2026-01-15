"""
Google OAuth Authentication for appscript-mcp

Supports multiple authentication methods:
1. clasp - easiest, no GCP project needed, uses Google's official Apps Script CLI
2. OAuth 2.0 - legacy, requires GCP project
3. OAuth 2.1 with PKCE - production, multi-user

Tokens are stored per-user in ~/.secrets/appscript-mcp/credentials/

Forked from google_workspace_mcp/auth/google_auth.py with clasp additions.
"""

import json
import jwt
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from .scopes import get_current_scopes, SCOPES
from .credential_store import get_credential_store
from .oauth_config import get_oauth_config, is_oauth_configured

logger = logging.getLogger(__name__)

# =============================================================================
# clasp Integration
# =============================================================================

CLASP_RC_PATH = Path.home() / ".clasprc.json"


def is_clasp_installed() -> bool:
    """Check if clasp CLI is installed."""
    try:
        result = subprocess.run(
            ["npx", "@google/clasp", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_clasp_authenticated() -> bool:
    """Check if clasp has valid credentials."""
    return CLASP_RC_PATH.exists()


def get_clasp_tokens() -> Optional[Dict[str, Any]]:
    """
    Read tokens from clasp's credential file (~/.clasprc.json).

    Returns:
        Token dict with access_token, refresh_token, etc. or None if not available.
    """
    if not CLASP_RC_PATH.exists():
        return None

    try:
        with open(CLASP_RC_PATH, "r") as f:
            clasp_config = json.load(f)

        token_data = clasp_config.get("token")
        if not token_data:
            return None

        return token_data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read clasp tokens: {e}")
        return None


def run_clasp_login() -> bool:
    """
    Run clasp login interactively.

    Returns:
        True if login succeeded, False otherwise.
    """
    try:
        print("\nOpening browser for Google authentication...")
        print("(If browser doesn't open, check the terminal for a URL)\n")

        result = subprocess.run(
            ["npx", "@google/clasp", "login"],
            timeout=300,  # 5 minute timeout for user interaction
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("\nAuthentication timed out.")
        return False
    except FileNotFoundError:
        print("\nError: Node.js/npx not found. Please install Node.js first.")
        return False


def clasp_tokens_to_credentials(token_data: Dict[str, Any]) -> Optional[Credentials]:
    """
    Convert clasp token dict to Google Credentials object.

    Args:
        token_data: Dict with access_token, refresh_token, etc.

    Returns:
        Credentials object or None if conversion fails.
    """
    try:
        from datetime import datetime

        # Handle clasp token format (expiry_date in ms)
        expiry = None
        if "expiry_date" in token_data:
            expiry = datetime.fromtimestamp(token_data["expiry_date"] / 1000)

        # Parse scopes
        scopes = None
        if "scope" in token_data:
            scope_val = token_data["scope"]
            scopes = scope_val.split(" ") if isinstance(scope_val, str) else scope_val

        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=scopes,
            expiry=expiry,
        )
        return creds
    except Exception as e:
        logger.warning(f"Failed to convert clasp tokens to credentials: {e}")
        return None


def get_user_email_from_credentials(credentials: Credentials) -> Optional[str]:
    """
    Extract user email from credentials (via id_token or API call).

    Args:
        credentials: Google Credentials object

    Returns:
        User's email address or None
    """
    # Try to get from id_token first
    if hasattr(credentials, 'id_token') and credentials.id_token:
        try:
            decoded = jwt.decode(credentials.id_token, options={"verify_signature": False})
            return decoded.get("email")
        except Exception:
            pass

    # Fall back to userinfo API
    try:
        from googleapiclient.discovery import build
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info.get("email")
    except Exception as e:
        logger.warning(f"Could not get user email: {e}")
        return None


# =============================================================================
# Credential Loading (Multi-source)
# =============================================================================


def get_credentials_for_user(user_email: str) -> Optional[Credentials]:
    """
    Get credentials for a specific user from the credential store.

    Args:
        user_email: User's email address

    Returns:
        Credentials object if found and valid, None otherwise
    """
    store = get_credential_store()
    creds = store.get_credential(user_email)

    if creds is None:
        return None

    # Check if valid
    if creds.valid:
        return creds

    # Try to refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            store.store_credential(user_email, creds)
            logger.info(f"Refreshed credentials for {user_email}")
            return creds
        except RefreshError as e:
            logger.warning(f"Failed to refresh credentials for {user_email}: {e}")

    return None


def get_any_valid_credentials() -> Optional[Tuple[str, Credentials]]:
    """
    Get any valid credentials from the store (for single-user mode).

    Returns:
        Tuple of (user_email, Credentials) or None
    """
    store = get_credential_store()
    users = store.list_users()

    for user_email in users:
        creds = get_credentials_for_user(user_email)
        if creds:
            return (user_email, creds)

    return None


def get_credentials() -> Optional[Credentials]:
    """
    Get valid OAuth credentials from the best available source.

    Priority:
    1. Credential store (existing per-user credentials)
    2. clasp tokens (~/.clasprc.json)

    Returns:
        Credentials object if valid credentials exist, None otherwise.
    """
    # 1. Try credential store first
    result = get_any_valid_credentials()
    if result:
        user_email, creds = result
        logger.debug(f"Using credentials for {user_email} from store")
        return creds

    # 2. Try clasp tokens
    token_data = get_clasp_tokens()
    if token_data:
        creds = clasp_tokens_to_credentials(token_data)
        if creds:
            # Get user email and store in our credential store
            user_email = get_user_email_from_credentials(creds)
            if user_email:
                store = get_credential_store()
                store.store_credential(user_email, creds)
                logger.info(f"Imported clasp credentials for {user_email}")
            return creds

    return None


def store_credentials(credentials: Credentials, user_email: Optional[str] = None) -> bool:
    """
    Store credentials in the credential store.

    Args:
        credentials: Google Credentials object
        user_email: User's email (will be extracted from credentials if not provided)

    Returns:
        True if stored successfully
    """
    if user_email is None:
        user_email = get_user_email_from_credentials(credentials)

    if user_email is None:
        logger.error("Cannot store credentials: no user email available")
        return False

    store = get_credential_store()
    return store.store_credential(user_email, credentials)


# =============================================================================
# OAuth Flows
# =============================================================================


def get_client_config() -> Optional[Dict[str, Any]]:
    """Get OAuth client config from environment variables or file."""
    config = get_oauth_config()

    if config.client_id and config.client_secret:
        return {
            "installed": {
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": config.get_redirect_uris(),
            }
        }

    # Try client_secret.json file
    client_secret_paths = [
        Path(os.getenv("GOOGLE_CLIENT_SECRET_PATH", "")),
        Path.home() / ".secrets" / "client_secret.json",
        Path.home() / ".appscript-mcp" / "client_secret.json",
        Path("client_secret.json"),
    ]

    for path in client_secret_paths:
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

    return None


def create_oauth_flow(scopes: Optional[list] = None) -> Flow:
    """
    Create an OAuth flow for authentication.

    Args:
        scopes: OAuth scopes to request (defaults to all scopes)

    Returns:
        OAuth Flow object

    Raises:
        ValueError if no client config is available
    """
    if scopes is None:
        scopes = get_current_scopes()

    client_config = get_client_config()
    if client_config is None:
        raise ValueError(
            "No OAuth credentials found.\n\n"
            "Use clasp (easiest):\n"
            "  appscript-mcp setup\n\n"
            "Or set environment variables:\n"
            "  export GOOGLE_OAUTH_CLIENT_ID='your-client-id'\n"
            "  export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'"
        )

    config = get_oauth_config()
    return Flow.from_client_config(
        client_config,
        scopes=scopes,
        redirect_uri=config.redirect_uri,
    )


def start_auth_flow(scopes: Optional[list] = None) -> Tuple[str, Flow]:
    """
    Start the OAuth authorization flow.

    Args:
        scopes: OAuth scopes to request

    Returns:
        Tuple of (authorization_url, flow)
    """
    flow = create_oauth_flow(scopes)
    config = get_oauth_config()

    auth_params = {"prompt": "consent", "access_type": "offline"}

    # Add PKCE for OAuth 2.1
    if config.is_oauth21_enabled():
        auth_params["code_challenge_method"] = "S256"

    auth_url, _ = flow.authorization_url(**auth_params)
    return auth_url, flow


def complete_auth_flow(flow: Flow, authorization_response: str) -> Credentials:
    """
    Complete the OAuth flow with the authorization response.

    Args:
        flow: OAuth Flow object from start_auth_flow
        authorization_response: The redirect URL with authorization code

    Returns:
        Credentials object
    """
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    # Store credentials
    store_credentials(credentials)

    return credentials


def auth_interactive(scopes: Optional[list] = None, port: int = 8080) -> Credentials:
    """
    Run OAuth flow with local callback server (for environments with browser access).

    Args:
        scopes: OAuth scopes to request
        port: Local port for OAuth callback

    Returns:
        Credentials object
    """
    if scopes is None:
        scopes = get_current_scopes()

    client_config = get_client_config()
    if client_config is None:
        raise ValueError("No OAuth client configuration found")

    flow = InstalledAppFlow.from_client_config(client_config, scopes)
    credentials = flow.run_local_server(port=port, open_browser=True)

    # Store credentials
    store_credentials(credentials)

    return credentials


# =============================================================================
# Service Builders
# =============================================================================


def get_service(service_name: str, version: str, credentials: Optional[Credentials] = None):
    """
    Get an authenticated Google API service.

    Args:
        service_name: API service name (e.g., "script", "drive", "gmail")
        version: API version (e.g., "v1", "v3")
        credentials: Credentials to use (will fetch from store if not provided)

    Returns:
        Google API service object

    Raises:
        ValueError if no valid credentials available
    """
    from googleapiclient.discovery import build

    if credentials is None:
        credentials = get_credentials()

    if credentials is None:
        raise ValueError("No valid credentials. Run: appscript-mcp setup")

    return build(service_name, version, credentials=credentials)


def get_script_service(credentials: Optional[Credentials] = None):
    """Get an authenticated Google Apps Script API service."""
    return get_service("script", "v1", credentials)


def get_drive_service(credentials: Optional[Credentials] = None):
    """Get an authenticated Google Drive API service."""
    return get_service("drive", "v3", credentials)


def get_gmail_service(credentials: Optional[Credentials] = None):
    """Get an authenticated Gmail API service."""
    return get_service("gmail", "v1", credentials)


def get_sheets_service(credentials: Optional[Credentials] = None):
    """Get an authenticated Google Sheets API service."""
    return get_service("sheets", "v4", credentials)


def get_calendar_service(credentials: Optional[Credentials] = None):
    """Get an authenticated Google Calendar API service."""
    return get_service("calendar", "v3", credentials)


def get_docs_service(credentials: Optional[Credentials] = None):
    """Get an authenticated Google Docs API service."""
    return get_service("docs", "v1", credentials)


# =============================================================================
# Pending Flow Management (for in-conversation auth)
# =============================================================================

_pending_flow: Optional[Flow] = None


def set_pending_flow(flow: Flow) -> None:
    """Store a pending OAuth flow for later completion."""
    global _pending_flow
    _pending_flow = flow


def get_pending_flow() -> Optional[Flow]:
    """Get the pending OAuth flow."""
    return _pending_flow


def clear_pending_flow() -> None:
    """Clear the pending OAuth flow."""
    global _pending_flow
    _pending_flow = None
