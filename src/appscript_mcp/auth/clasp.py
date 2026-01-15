"""
clasp Integration for appscript-mcp

clasp is Google's official Apps Script CLI. We use it as the easiest
authentication method - no GCP project setup needed.

https://github.com/google/clasp
"""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

CLASP_RC_PATH = Path.home() / ".clasprc.json"


def is_npm_installed() -> bool:
    """Check if npm is available."""
    return shutil.which("npm") is not None


def is_npx_installed() -> bool:
    """Check if npx is available."""
    return shutil.which("npx") is not None


def is_node_installed() -> bool:
    """Check if Node.js is available."""
    return shutil.which("node") is not None


def is_clasp_installed() -> bool:
    """
    Check if clasp CLI is installed and accessible.

    Returns:
        True if clasp can be executed, False otherwise.
    """
    if not is_npx_installed():
        return False

    try:
        result = subprocess.run(
            ["npx", "@google/clasp", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def get_clasp_version() -> Optional[str]:
    """Get the installed clasp version."""
    try:
        result = subprocess.run(
            ["npx", "@google/clasp", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def is_clasp_authenticated() -> bool:
    """Check if clasp has valid credentials stored."""
    if not CLASP_RC_PATH.exists():
        return False

    try:
        with open(CLASP_RC_PATH, "r") as f:
            config = json.load(f)
        return "token" in config and config["token"].get("access_token")
    except (json.JSONDecodeError, IOError):
        return False


def get_clasp_tokens() -> Optional[Dict[str, Any]]:
    """
    Read tokens from clasp's credential file (~/.clasprc.json).

    clasp token format:
    {
        "token": {
            "access_token": "...",
            "refresh_token": "...",
            "scope": "https://www.googleapis.com/auth/... ...",
            "token_type": "Bearer",
            "expiry_date": 1234567890000,  // milliseconds
            "client_id": "...",
            "client_secret": "..."
        }
    }

    Returns:
        Token dict or None if not available.
    """
    if not CLASP_RC_PATH.exists():
        return None

    try:
        with open(CLASP_RC_PATH, "r") as f:
            config = json.load(f)
        return config.get("token")
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read clasp tokens: {e}")
        return None


def get_clasp_user_email() -> Optional[str]:
    """
    Get the email of the user authenticated with clasp.

    Note: clasp doesn't store the email directly, so we need to
    extract it from the tokens via the userinfo API.
    """
    tokens = get_clasp_tokens()
    if not tokens:
        return None

    # Try to get from ID token if present
    # clasp tokens usually don't have id_token, so we'll need to make an API call
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(
            token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=tokens.get("client_id"),
            client_secret=tokens.get("client_secret"),
        )

        service = build("oauth2", "v2", credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info.get("email")
    except Exception as e:
        logger.debug(f"Could not get clasp user email: {e}")
        return None


def install_clasp_global() -> Tuple[bool, str]:
    """
    Install clasp globally via npm.

    Returns:
        Tuple of (success, message)
    """
    if not is_npm_installed():
        return False, "npm not found. Please install Node.js first: https://nodejs.org/"

    print("Installing clasp globally...")

    try:
        result = subprocess.run(
            ["npm", "install", "-g", "@google/clasp"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, "clasp installed successfully!"
        else:
            # Try with sudo on Linux/macOS
            if "EACCES" in result.stderr or "permission" in result.stderr.lower():
                print("Retrying with sudo...")
                result = subprocess.run(
                    ["sudo", "npm", "install", "-g", "@google/clasp"],
                    timeout=120,
                )
                if result.returncode == 0:
                    return True, "clasp installed successfully (with sudo)!"

            return False, f"npm install failed: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Installation timed out"
    except FileNotFoundError:
        return False, "npm not found"
    except OSError as e:
        return False, f"Installation error: {e}"


def run_clasp_login() -> Tuple[bool, str]:
    """
    Run clasp login interactively.

    This opens a browser for OAuth consent and stores tokens in ~/.clasprc.json.

    Returns:
        Tuple of (success, message)
    """
    if not is_clasp_installed():
        return False, "clasp is not installed"

    print("\nOpening browser for Google authentication...")
    print("(If browser doesn't open, check the terminal for a URL)\n")

    try:
        result = subprocess.run(
            ["npx", "@google/clasp", "login"],
            timeout=300,  # 5 minute timeout for user interaction
        )

        if result.returncode == 0:
            return True, "Authentication successful!"
        else:
            return False, "Authentication failed or was cancelled"

    except subprocess.TimeoutExpired:
        return False, "Authentication timed out (5 minutes)"
    except FileNotFoundError:
        return False, "npx not found"
    except OSError as e:
        return False, f"Error running clasp: {e}"


def run_clasp_logout() -> Tuple[bool, str]:
    """
    Run clasp logout to clear stored credentials.

    Returns:
        Tuple of (success, message)
    """
    if not is_clasp_installed():
        return False, "clasp is not installed"

    try:
        result = subprocess.run(
            ["npx", "@google/clasp", "logout"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, "Logged out successfully"
        else:
            return False, f"Logout failed: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Logout timed out"
    except (FileNotFoundError, OSError) as e:
        return False, f"Error: {e}"


def detect_clasp_environment() -> Dict[str, Any]:
    """
    Detect the clasp environment and return status information.

    Returns:
        Dict with environment detection results
    """
    return {
        "node_installed": is_node_installed(),
        "npm_installed": is_npm_installed(),
        "npx_installed": is_npx_installed(),
        "clasp_installed": is_clasp_installed(),
        "clasp_version": get_clasp_version(),
        "clasp_authenticated": is_clasp_authenticated(),
        "clasp_user_email": get_clasp_user_email() if is_clasp_authenticated() else None,
        "clasprc_path": str(CLASP_RC_PATH),
        "clasprc_exists": CLASP_RC_PATH.exists(),
    }
