"""
Interactive Setup for google-automation-mcp

Guides users through authentication setup with environment detection
and sensible defaults.
"""

import os
import sys
from typing import Dict, Any

from .auth.clasp import (
    install_clasp_global,
    run_clasp_login,
    detect_clasp_environment,
)
from .auth.oauth_config import is_oauth_configured, get_oauth_config
from .auth.credential_store import get_credential_store
from .auth.google_auth import store_credentials, get_user_email_from_credentials


def detect_environment() -> Dict[str, Any]:
    """
    Detect the current environment and available authentication options.

    Returns:
        Dict with environment detection results
    """
    # Check for interactive terminal
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()

    # Check for browser availability (DISPLAY on Linux, assume available on macOS/Windows)
    has_display = bool(os.environ.get("DISPLAY")) or sys.platform in ("darwin", "win32")

    # clasp environment
    clasp_env = detect_clasp_environment()

    # OAuth environment
    oauth_configured = is_oauth_configured()
    oauth_config = get_oauth_config()

    # Existing credentials
    store = get_credential_store()
    existing_users = store.list_users()

    return {
        "is_interactive": is_interactive,
        "has_display": has_display,
        "has_browser": has_display and is_interactive,
        # clasp
        "node_installed": clasp_env["node_installed"],
        "npm_installed": clasp_env["npm_installed"],
        "clasp_installed": clasp_env["clasp_installed"],
        "clasp_authenticated": clasp_env["clasp_authenticated"],
        "clasp_user": clasp_env["clasp_user_email"],
        # OAuth
        "oauth_configured": oauth_configured,
        "oauth21_enabled": oauth_config.is_oauth21_enabled(),
        # Existing
        "existing_users": existing_users,
        "has_credentials": len(existing_users) > 0,
    }


def print_detection_results(env: Dict[str, Any]) -> None:
    """Print environment detection results."""
    print("\nDetecting environment...")

    # Terminal
    if env["is_interactive"]:
        print("✓ Interactive terminal")
    else:
        print("✗ Non-interactive terminal")

    # Browser
    if env["has_browser"]:
        print("✓ Browser available")
    else:
        print("✗ No browser (DISPLAY not set)")

    # Node.js / clasp
    if env["node_installed"]:
        print("✓ Node.js installed")
    else:
        print("✗ Node.js not installed")

    if env["clasp_installed"]:
        print("✓ clasp installed")
    else:
        print("✗ clasp not installed")

    if env["clasp_authenticated"]:
        print(f"✓ clasp authenticated ({env['clasp_user']})")

    # OAuth
    if env["oauth_configured"]:
        print("✓ GCP OAuth credentials configured")

    # Existing credentials
    if env["has_credentials"]:
        print(f"✓ Existing credentials found ({len(env['existing_users'])} user(s))")

    print()


def get_recommended_choice(env: Dict[str, Any]) -> int:
    """
    Determine the recommended setup choice based on environment.

    Returns:
        1 = Local/CLI (clasp)
        2 = Server/Multi-user (OAuth 2.1)
        3 = Both
    """
    # If already have clasp credentials, recommend local
    if env["clasp_authenticated"]:
        return 1

    # If OAuth 2.1 configured but no clasp, recommend server mode
    if (
        env["oauth_configured"]
        and env["oauth21_enabled"]
        and not env["clasp_installed"]
    ):
        return 2

    # If both configured, recommend both
    if env["oauth_configured"] and env["clasp_installed"]:
        return 3

    # If no browser, must use server mode
    if not env["has_browser"]:
        return 2

    # Default to local/CLI for interactive terminals
    return 1


def prompt_setup_choice(env: Dict[str, Any]) -> int:
    """
    Prompt user to choose setup mode.

    Returns:
        1 = Local/CLI
        2 = Server/Multi-user
        3 = Both
    """
    recommended = get_recommended_choice(env)

    print("How will you use this MCP?\n")

    # Option 1: Local/CLI
    rec1 = " (Recommended)" if recommended == 1 else ""
    note1 = ""
    if env["clasp_authenticated"]:
        note1 = f"    ↳ clasp already authenticated as {env['clasp_user']}"
    elif env["clasp_installed"]:
        note1 = "    ↳ clasp installed, ready to authenticate"
    elif not env["has_browser"]:
        note1 = "    ↳ Requires browser - not detected in this environment"
    else:
        note1 = "    ↳ Uses clasp (easiest, no GCP project needed)"

    print(f"  [1] Local/CLI{rec1}")
    print(note1)
    print()

    # Option 2: Server/Multi-user
    rec2 = " (Recommended)" if recommended == 2 else ""
    note2 = ""
    if env["oauth_configured"]:
        note2 = "    ↳ OAuth credentials detected in environment"
    elif not env["has_browser"]:
        note2 = "    ↳ Best for headless environments"
    else:
        note2 = "    ↳ Multiple users, headless deployment, OAuth 2.1"

    print(f"  [2] Server/Multi-user{rec2}")
    print(note2)
    print()

    # Option 3: Both
    rec3 = " (Recommended)" if recommended == 3 else ""
    print(f"  [3] Both{rec3}")
    print("    ↳ clasp for local dev, OAuth 2.1 for production")
    print()

    # Get user choice
    try:
        choice_str = input(f"Choice [{recommended}]: ").strip()
        if not choice_str:
            return recommended
        choice = int(choice_str)
        if choice in (1, 2, 3):
            return choice
        print(f"Invalid choice: {choice}. Using default.")
        return recommended
    except (ValueError, EOFError, KeyboardInterrupt):
        print()
        return recommended


def setup_clasp(env: Dict[str, Any]) -> bool:
    """
    Set up clasp authentication.

    Returns:
        True if successful
    """
    print("\n" + "=" * 50)
    print("clasp Setup (Local/CLI)")
    print("=" * 50 + "\n")

    # Already authenticated?
    if env["clasp_authenticated"]:
        print(f"Already authenticated as: {env['clasp_user']}")
        response = input("Re-authenticate? [y/N]: ").strip().lower()
        if response != "y":
            # Import existing clasp credentials
            _import_clasp_credentials()
            return True
        print()

    # Install clasp if needed
    if not env["clasp_installed"]:
        if not env["node_installed"]:
            print("Node.js is required for clasp.")
            print("Install from: https://nodejs.org/")
            return False

        response = input("clasp not installed. Install now? [Y/n]: ").strip().lower()
        if response == "n":
            print("Skipping clasp setup.")
            return False

        success, message = install_clasp_global()
        print(message)
        if not success:
            return False
        print()

    # Run clasp login
    print("Running clasp login...")
    success, message = run_clasp_login()
    print(message)

    if success:
        # Import credentials to our store
        _import_clasp_credentials()

    return success


def _import_clasp_credentials() -> bool:
    """Import clasp credentials into our credential store."""
    from .auth.clasp import get_clasp_tokens
    from .auth.google_auth import clasp_tokens_to_credentials

    tokens = get_clasp_tokens()
    if not tokens:
        return False

    creds = clasp_tokens_to_credentials(tokens)
    if not creds:
        return False

    user_email = get_user_email_from_credentials(creds)
    if user_email:
        store_credentials(creds, user_email)
        print(f"\n✓ Credentials stored for {user_email}")
        return True

    return False


def setup_oauth(env: Dict[str, Any]) -> bool:
    """
    Set up OAuth 2.1 authentication.

    Returns:
        True if successful
    """
    print("\n" + "=" * 50)
    print("OAuth 2.1 Setup (Server/Multi-user)")
    print("=" * 50 + "\n")

    if env["oauth_configured"]:
        print("OAuth credentials already configured via environment variables.")
        print("✓ GOOGLE_OAUTH_CLIENT_ID is set")
        print("✓ GOOGLE_OAUTH_CLIENT_SECRET is set")
        return True

    print("OAuth 2.1 requires a Google Cloud project with OAuth credentials.\n")
    print("Setup steps:")
    print("1. Create a GCP project: https://console.cloud.google.com/projectcreate")
    print(
        "2. Enable APIs: https://console.cloud.google.com/flows/enableapi?apiid=script.googleapis.com,drive.googleapis.com,gmail.googleapis.com,sheets.googleapis.com,calendar-json.googleapis.com,docs.googleapis.com"
    )
    print("3. Create OAuth client (Web application type)")
    print("4. Add redirect URI: http://localhost:8000/oauth2callback")
    print()

    response = input("Do you have OAuth credentials ready? [y/N]: ").strip().lower()
    if response != "y":
        print("\nPlease complete the GCP setup steps above, then run setup again.")
        return False

    # Get credentials
    print()
    client_id = input("Enter Client ID: ").strip()
    client_secret = input("Enter Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Client ID and Client Secret are required.")
        return False

    # Save to environment (for this session)
    os.environ["GOOGLE_OAUTH_CLIENT_ID"] = client_id
    os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = client_secret

    print("\n✓ OAuth credentials configured for this session")
    print()
    print("To make permanent, add to your shell profile:")
    print(f'  export GOOGLE_OAUTH_CLIENT_ID="{client_id}"')
    print(f'  export GOOGLE_OAUTH_CLIENT_SECRET="{client_secret}"')
    print()
    print("Or add to your MCP config with env section.")

    return True


def run_setup() -> bool:
    """
    Run the interactive setup process.

    Returns:
        True if setup completed successfully
    """
    print("\n" + "=" * 50)
    print("Google Workspace MCP Setup")
    print("=" * 50)

    # Detect environment
    env = detect_environment()
    print_detection_results(env)

    # Check if already set up
    if env["has_credentials"]:
        print(f"Found existing credentials for: {', '.join(env['existing_users'])}")
        response = input("Set up additional authentication? [y/N]: ").strip().lower()
        if response != "y":
            print("\nUsing existing credentials. Setup complete!")
            return True
        print()

    # Get user choice
    choice = prompt_setup_choice(env)

    success = True

    if choice == 1:
        # Local/CLI only
        success = setup_clasp(env)
    elif choice == 2:
        # Server/Multi-user only
        success = setup_oauth(env)
    elif choice == 3:
        # Both
        print("\nSetting up both authentication methods...\n")
        clasp_ok = setup_clasp(env)
        oauth_ok = setup_oauth(env)
        success = clasp_ok or oauth_ok

    if success:
        print("\n" + "=" * 50)
        print("Setup Complete!")
        print("=" * 50)
        print("\nYou can now use google-automation-mcp with your MCP client.")
        print("Example prompts:")
        print('  "List my Apps Script projects"')
        print('  "Show my recent Gmail messages"')
        print('  "List files in my Google Drive"')
    else:
        print("\n" + "=" * 50)
        print("Setup Incomplete")
        print("=" * 50)
        print("\nRun 'google-automation-mcp setup' again to complete setup.")

    return success
