"""
OAuth 2.0 Authentication for Apps Script MCP

Uses clasp (Google's official Apps Script CLI) for OAuth - no GCP project setup needed.
Tokens stored securely in ~/.secrets/appscript-mcp/ with restricted permissions.

Authentication priority:
1. ~/.secrets/appscript-mcp/token.json (secure storage)
2. ~/.clasprc.json (clasp tokens)
3. Legacy: environment variables + our OAuth flow (for advanced users)
"""

import json
import os
import pickle
import subprocess
import logging
import stat
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

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
    "https://www.googleapis.com/auth/script.metrics",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Secure token storage location
SECRETS_DIR = Path.home() / ".secrets" / "appscript-mcp"
SECURE_TOKEN_PATH = SECRETS_DIR / "token.json"

# Clasp token location
CLASP_RC_PATH = Path.home() / ".clasprc.json"

# Legacy storage (for backwards compatibility)
LEGACY_CREDS_DIR = Path.home() / ".appscript-mcp"
LEGACY_TOKEN_PATH = LEGACY_CREDS_DIR / "token.pickle"


# =============================================================================
# Clasp Integration
# =============================================================================


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
    Read tokens from clasp's credential file.

    Returns:
        Token dict with access_token, refresh_token, etc. or None if not available.
    """
    if not CLASP_RC_PATH.exists():
        return None

    try:
        with open(CLASP_RC_PATH, "r") as f:
            clasp_config = json.load(f)

        # Clasp stores tokens under "token" key
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


def run_clasp_login_headless() -> Optional[str]:
    """
    Start clasp login in a way that returns the auth URL for headless environments.

    Note: clasp doesn't have a native headless mode, so this is a workaround.
    Returns the auth URL if detected, None otherwise.
    """
    # clasp login doesn't have a clean headless mode
    # For headless, we fall back to our own OAuth flow
    return None


# =============================================================================
# Secure Token Storage
# =============================================================================


def ensure_secrets_dir() -> Path:
    """Create ~/.secrets/appscript-mcp/ with secure permissions."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    # Set directory permissions to 700 (owner only)
    os.chmod(SECRETS_DIR, stat.S_IRWXU)
    return SECRETS_DIR


def save_tokens_securely(token_data: Dict[str, Any]) -> None:
    """
    Save tokens to ~/.secrets/appscript-mcp/token.json with secure permissions.

    Args:
        token_data: Dict containing access_token, refresh_token, etc.
    """
    ensure_secrets_dir()

    with open(SECURE_TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

    # Set file permissions to 600 (owner read/write only)
    os.chmod(SECURE_TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)
    logger.info(f"Tokens saved securely to {SECURE_TOKEN_PATH}")


def load_secure_tokens() -> Optional[Dict[str, Any]]:
    """Load tokens from secure storage."""
    if not SECURE_TOKEN_PATH.exists():
        return None

    try:
        with open(SECURE_TOKEN_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load secure tokens: {e}")
        return None


def tokens_to_credentials(token_data: Dict[str, Any]) -> Optional[Credentials]:
    """
    Convert token dict to Google Credentials object.

    Args:
        token_data: Dict with access_token, refresh_token, etc.

    Returns:
        Credentials object or None if conversion fails.
    """
    try:
        # Handle clasp token format (expiry_date in ms) vs standard (expiry as ISO string)
        expiry = None
        if "expiry_date" in token_data:
            # Clasp format: milliseconds since epoch
            expiry = datetime.fromtimestamp(token_data["expiry_date"] / 1000)
        elif "expiry" in token_data:
            # Standard format: ISO string
            expiry = datetime.fromisoformat(token_data["expiry"].replace("Z", "+00:00"))

        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scope", "").split(" ") if isinstance(token_data.get("scope"), str) else token_data.get("scope"),
            expiry=expiry,
        )
        return creds
    except Exception as e:
        logger.warning(f"Failed to convert tokens to credentials: {e}")
        return None


def credentials_to_tokens(creds: Credentials) -> Dict[str, Any]:
    """Convert Credentials object to token dict for storage."""
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scope": " ".join(creds.scopes) if creds.scopes else "",
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


# =============================================================================
# Main Credential Loading
# =============================================================================


def get_credentials() -> Optional[Credentials]:
    """
    Get valid OAuth credentials from the best available source.

    Priority:
    1. Secure storage (~/.secrets/appscript-mcp/token.json)
    2. Clasp tokens (~/.clasprc.json)
    3. Legacy storage (~/.appscript-mcp/token.pickle)

    Returns:
        Credentials object if valid credentials exist, None otherwise.
    """
    creds = None
    source = None

    # 1. Try secure storage first
    token_data = load_secure_tokens()
    if token_data:
        creds = tokens_to_credentials(token_data)
        source = "secure storage"

    # 2. Try clasp tokens
    if creds is None:
        token_data = get_clasp_tokens()
        if token_data:
            creds = tokens_to_credentials(token_data)
            source = "clasp"
            # Copy to secure storage for future use
            if creds:
                save_tokens_securely(token_data)

    # 3. Try legacy storage
    if creds is None and LEGACY_TOKEN_PATH.exists():
        try:
            with open(LEGACY_TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)
            source = "legacy storage"
            # Migrate to secure storage
            if creds:
                save_tokens_securely(credentials_to_tokens(creds))
                logger.info("Migrated legacy tokens to secure storage")
        except Exception as e:
            logger.warning(f"Failed to load legacy credentials: {e}")

    if creds is None:
        return None

    # Check if credentials are valid
    if creds.valid:
        logger.debug(f"Using valid credentials from {source}")
        return creds

    # Try to refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_tokens_securely(credentials_to_tokens(creds))
            logger.info(f"Refreshed expired credentials from {source}")
            return creds
        except Exception as e:
            logger.warning(f"Failed to refresh credentials: {e}")

    return None


# =============================================================================
# Authentication Flows
# =============================================================================


def authenticate() -> Credentials:
    """
    Main authentication entry point.

    Uses clasp if available, falls back to custom OAuth if needed.

    Returns:
        Valid Credentials object.

    Raises:
        Exception if authentication fails.
    """
    # Check if already authenticated
    creds = get_credentials()
    if creds:
        return creds

    # Try clasp authentication
    if is_clasp_installed():
        print("Using clasp for authentication (no GCP project needed)...")
        if run_clasp_login():
            creds = get_credentials()
            if creds:
                return creds

    # Fall back to custom OAuth
    raise Exception(
        "Authentication required. Options:\n\n"
        "1. Install clasp and login (easiest):\n"
        "   npm install -g @google/clasp\n"
        "   clasp login\n\n"
        "2. Or run: appscript-mcp auth\n"
    )


def auth_with_clasp_or_prompt() -> Optional[Credentials]:
    """
    Authenticate using clasp, prompting for installation if needed.

    Returns:
        Credentials if successful, None if user needs to take action.
    """
    # Already authenticated?
    creds = get_credentials()
    if creds:
        print("Already authenticated.")
        return creds

    # Check if clasp is installed
    if not is_clasp_installed():
        print("clasp not found. Install it with:\n")
        print("  npm install -g @google/clasp\n")
        print("Then run: appscript-mcp auth")
        return None

    # Run clasp login
    print("Authenticating with clasp (no GCP project needed)...\n")
    if run_clasp_login():
        creds = get_credentials()
        if creds:
            print("\n✓ Authentication successful!")
            return creds

    print("\n✗ Authentication failed. Please try again.")
    return None


# =============================================================================
# Legacy OAuth Flow (for advanced users or headless)
# =============================================================================


def get_client_config_from_env() -> Optional[Dict[str, Any]]:
    """Get OAuth client config from environment variables."""
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
    env_path = os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    if env_path:
        return Path(env_path)

    default_paths = [
        LEGACY_CREDS_DIR / "client_secret.json",
        Path("client_secret.json"),
        Path.home() / ".secrets" / "client_secret.json",
    ]

    for path in default_paths:
        if path.exists():
            return path

    return default_paths[0]


def _create_oauth_flow() -> InstalledAppFlow:
    """Create an OAuth flow from env vars or client secret file."""
    client_config = get_client_config_from_env()
    if client_config:
        logger.info("Using OAuth credentials from environment variables")
        return InstalledAppFlow.from_client_config(client_config, SCOPES)

    client_secret_path = get_client_secret_path()

    if not client_secret_path.exists():
        raise FileNotFoundError(
            "No OAuth credentials found.\n\n"
            "Recommended: Use clasp (no GCP project needed):\n"
            "  npm install -g @google/clasp\n"
            "  clasp login\n\n"
            "Or set environment variables:\n"
            "  export GOOGLE_OAUTH_CLIENT_ID='your-client-id'\n"
            "  export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'\n"
        )

    logger.info(f"Using OAuth credentials from {client_secret_path}")
    return InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)


# Global flow storage for completing auth across tool calls
_pending_flow: Optional[InstalledAppFlow] = None


def start_auth_flow() -> Tuple[str, InstalledAppFlow]:
    """Start the OAuth authorization flow for headless environments."""
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = _create_oauth_flow()
    flow.redirect_uri = "http://localhost"
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url, flow


def complete_auth_flow(flow: InstalledAppFlow, redirect_url: str) -> Credentials:
    """Complete the OAuth flow with the redirect URL."""
    flow.fetch_token(authorization_response=redirect_url)
    creds = flow.credentials
    save_tokens_securely(credentials_to_tokens(creds))
    return creds


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
    """OAuth with local callback server for environments with browser access."""
    flow = _create_oauth_flow()
    creds = flow.run_local_server(port=port, open_browser=True)
    save_tokens_securely(credentials_to_tokens(creds))
    return creds


# =============================================================================
# API Service Builders
# =============================================================================


def get_script_service(creds: Optional[Credentials] = None):
    """Get an authenticated Google Apps Script API service."""
    if creds is None:
        creds = get_credentials()

    if creds is None:
        raise Exception(
            "No valid credentials. Run: appscript-mcp auth"
        )

    return build("script", "v1", credentials=creds)


def get_drive_service(creds: Optional[Credentials] = None):
    """Get an authenticated Google Drive API service."""
    if creds is None:
        creds = get_credentials()

    if creds is None:
        raise Exception(
            "No valid credentials. Run: appscript-mcp auth"
        )

    return build("drive", "v3", credentials=creds)
