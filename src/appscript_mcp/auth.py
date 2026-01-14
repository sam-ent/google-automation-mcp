"""
OAuth 2.0 Authentication for Apps Script MCP

Provides OAuth 2.0 authentication with headless flow support for Google APIs.
"""

import os
import pickle
import logging
from pathlib import Path
from typing import Optional, Tuple

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
    "https://www.googleapis.com/auth/drive.readonly",  # For listing script projects
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def get_credentials_dir() -> Path:
    """Get the directory for storing credentials."""
    creds_dir = Path(os.environ.get("APPSCRIPT_CREDENTIALS_DIR", "~/.appscript-mcp")).expanduser()
    creds_dir.mkdir(parents=True, exist_ok=True)
    return creds_dir


def get_token_path() -> Path:
    """Get the path to the token file."""
    return get_credentials_dir() / "token.pickle"


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

    Returns:
        Tuple of (authorization_url, flow) for completing the auth.
    """
    client_secret_path = get_client_secret_path()

    if not client_secret_path.exists():
        raise FileNotFoundError(
            f"Client secret file not found at {client_secret_path}\n\n"
            "To configure OAuth credentials:\n"
            "1. Go to Google Cloud Console > APIs & Services > Credentials\n"
            "2. Create an OAuth 2.0 Client ID (Desktop application type)\n"
            "3. Download the JSON file\n"
            "4. Save it to one of these locations:\n"
            f"   - {get_credentials_dir() / 'client_secret.json'}\n"
            "   - ./client_secret.json\n"
            "   - ~/.secrets/client_secret.json\n"
            "   - Or set GOOGLE_CLIENT_SECRET_PATH environment variable"
        )

    # Allow http://localhost for OAuth (required for headless auth)
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
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
