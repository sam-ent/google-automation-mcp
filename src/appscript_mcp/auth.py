"""
OAuth 2.0 Authentication for Apps Script MCP

Provides OAuth 2.0 authentication with headless flow support for Google APIs.

Supports two credential sources (env vars take precedence):
1. Environment variables: GOOGLE_OAUTH_CLIENT_ID + GOOGLE_OAUTH_CLIENT_SECRET
2. JSON file: client_secret.json in standard locations
"""

import os
import pickle
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# OAuth scopes required for Apps Script operations
SCOPES = [
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.projects.readonly",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/script.deployments.readonly",
    "https://www.googleapis.com/auth/script.processes",
    "https://www.googleapis.com/auth/script.metrics",  # For script analytics
    "https://www.googleapis.com/auth/drive.file",  # For listing and deleting script projects
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def get_credentials_dir() -> Path:
    """Get the directory for storing credentials."""
    creds_dir = Path(
        os.environ.get("APPSCRIPT_CREDENTIALS_DIR", "~/.appscript-mcp")
    ).expanduser()
    creds_dir.mkdir(parents=True, exist_ok=True)
    return creds_dir


def get_token_path() -> Path:
    """Get the path to the token file."""
    return get_credentials_dir() / "token.pickle"


def get_client_config_from_env() -> Optional[Dict[str, Any]]:
    """
    Get OAuth client config from environment variables.

    Returns:
        Client config dict if env vars are set, None otherwise.
    """
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

    if client_id and client_secret:
        return {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
    return None


def get_client_secret_path() -> Path:
    """Get the path to the client secret file."""
    # Check environment variable first
    env_path = os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    if env_path:
        return Path(env_path)

    # Default locations to check
    default_paths = [
        get_credentials_dir() / "client_secret.json",
        Path("client_secret.json"),
        Path.home() / ".secrets" / "client_secret.json",
    ]

    for path in default_paths:
        if path.exists():
            return path

    # Return the first default path (will fail later with helpful message)
    return default_paths[0]


def _create_oauth_flow() -> InstalledAppFlow:
    """
    Create an OAuth flow from env vars or client secret file.

    Env vars take precedence over file.

    Returns:
        Configured InstalledAppFlow

    Raises:
        FileNotFoundError: If no credentials source is available
    """
    # Try env vars first
    client_config = get_client_config_from_env()
    if client_config:
        logger.info("Using OAuth credentials from environment variables")
        return InstalledAppFlow.from_client_config(client_config, SCOPES)

    # Fall back to JSON file
    client_secret_path = get_client_secret_path()

    if not client_secret_path.exists():
        raise FileNotFoundError(
            f"No OAuth credentials found.\n\n"
            "Option 1: Set environment variables:\n"
            "  export GOOGLE_OAUTH_CLIENT_ID='your-client-id'\n"
            "  export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'\n\n"
            "Option 2: Use a client_secret.json file:\n"
            "  1. Go to Google Cloud Console > APIs & Services > Credentials\n"
            "  2. Create an OAuth 2.0 Client ID (Desktop application type)\n"
            "  3. Download the JSON file\n"
            "  4. Save it to one of these locations:\n"
            f"     - {get_credentials_dir() / 'client_secret.json'}\n"
            "     - ./client_secret.json\n"
            "     - ~/.secrets/client_secret.json\n"
            "     - Or set GOOGLE_CLIENT_SECRET_PATH environment variable"
        )

    logger.info(f"Using OAuth credentials from {client_secret_path}")
    return InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)


def get_credentials() -> Optional[Credentials]:
    """
    Get valid OAuth credentials, loading from cache if available.

    Returns:
        Credentials object if valid credentials exist, None otherwise.
    """
    token_path = get_token_path()

    if not token_path.exists():
        return None

    try:
        with open(token_path, "rb") as token_file:
            creds = pickle.load(token_file)

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)
            return creds
    except Exception as e:
        logger.warning(f"Failed to load credentials: {e}")

    return None


def save_credentials(creds: Credentials) -> None:
    """Save credentials to the token file."""
    token_path = get_token_path()
    with open(token_path, "wb") as token_file:
        pickle.dump(creds, token_file)
    logger.info(f"Credentials saved to {token_path}")


def start_auth_flow() -> Tuple[str, InstalledAppFlow]:
    """
    Start the OAuth authorization flow.

    Uses env vars (GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET) if set,
    otherwise falls back to client_secret.json file.

    Returns:
        Tuple of (authorization_url, flow) for completing the auth.
    """
    # Allow http://localhost for OAuth (required for headless auth)
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = _create_oauth_flow()
    flow.redirect_uri = "http://localhost"

    auth_url, _ = flow.authorization_url(prompt="consent")

    return auth_url, flow


def complete_auth_flow(flow: InstalledAppFlow, redirect_url: str) -> Credentials:
    """
    Complete the OAuth flow with the redirect URL.

    Args:
        flow: The OAuth flow object from start_auth_flow
        redirect_url: The full redirect URL from the browser

    Returns:
        Valid Credentials object
    """
    flow.fetch_token(authorization_response=redirect_url)
    creds = flow.credentials
    save_credentials(creds)
    return creds


def get_script_service(creds: Optional[Credentials] = None):
    """
    Get an authenticated Google Apps Script API service.

    Args:
        creds: Optional credentials. If not provided, loads from cache.

    Returns:
        Google Apps Script API service object

    Raises:
        Exception if no valid credentials available
    """
    if creds is None:
        creds = get_credentials()

    if creds is None:
        raise Exception(
            "No valid credentials found. Please authenticate first using start_google_auth."
        )

    return build("script", "v1", credentials=creds)


def get_drive_service(creds: Optional[Credentials] = None):
    """
    Get an authenticated Google Drive API service.

    Args:
        creds: Optional credentials. If not provided, loads from cache.

    Returns:
        Google Drive API service object

    Raises:
        Exception if no valid credentials available
    """
    if creds is None:
        creds = get_credentials()

    if creds is None:
        raise Exception(
            "No valid credentials found. Please authenticate first using start_google_auth."
        )

    return build("drive", "v3", credentials=creds)


# Global flow storage for completing auth across tool calls
_pending_flow: Optional[InstalledAppFlow] = None


def set_pending_flow(flow: InstalledAppFlow) -> None:
    """Store a pending OAuth flow for later completion."""
    global _pending_flow
    _pending_flow = flow


def get_pending_flow() -> Optional[InstalledAppFlow]:
    """Get the pending OAuth flow."""
    return _pending_flow


def clear_pending_flow() -> None:
    """Clear the pending OAuth flow."""
    global _pending_flow
    _pending_flow = None


def auth_interactive(port: int = 8080) -> Credentials:
    """
    OAuth with local callback server for environments with browser access.

    Opens the default browser, runs a temporary local server to capture
    the OAuth callback, and saves the credentials automatically.

    Uses env vars (GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET) if set,
    otherwise falls back to client_secret.json file.

    Use this when a browser can open on the local machine (native, X11, etc.).
    For headless environments, use start_auth_flow() + complete_auth_flow() instead.

    Args:
        port: Local port for the callback server (default: 8080)

    Returns:
        Valid Credentials object

    Raises:
        FileNotFoundError: If no credentials source is available
    """
    flow = _create_oauth_flow()
    creds = flow.run_local_server(port=port, open_browser=True)
    save_credentials(creds)
    return creds
