"""
CLI entry point for google-automation-mcp.

Provides:
- setup: Interactive setup with environment detection
- auth: Quick authentication (clasp or legacy)
- server: Run MCP server (default)
"""

import sys


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]

    # No args: run MCP server
    if not args:
        _run_server()
        return

    command = args[0]

    if command == "setup":
        _run_setup()
    elif command == "auth":
        _run_auth(args[1:])
    elif command == "status":
        _run_status()
    elif command in ("--help", "-h", "help"):
        _print_help()
    elif command in ("--version", "-v", "version"):
        _print_version()
    else:
        # Unknown command, might be server args
        _run_server()


def _run_server():
    """Run the MCP server."""
    from .server import main as server_main

    server_main()


def _run_setup():
    """Run interactive setup."""
    from .setup import run_setup

    success = run_setup()
    sys.exit(0 if success else 1)


def _run_auth(args: list):
    """Run authentication command."""
    headless = "--headless" in args
    legacy = "--legacy" in args
    oauth21 = "--oauth21" in args

    if legacy or oauth21:
        if headless:
            _auth_headless_legacy()
        else:
            _auth_local_legacy()
    else:
        # Default: clasp
        _auth_clasp(headless=headless)


def _run_status():
    """Show authentication status."""
    from .setup import detect_environment

    print("\ngoogle-automation-mcp Status")
    print("=" * 40)

    env = detect_environment()

    print("\nAuthentication:")
    if env["has_credentials"]:
        print(f"  ✓ Authenticated users: {', '.join(env['existing_users'])}")
    else:
        print("  ✗ No credentials found")

    print("\nclasp:")
    if env["clasp_installed"]:
        print("  ✓ Installed")
        if env["clasp_authenticated"]:
            print(f"  ✓ Authenticated as {env['clasp_user']}")
        else:
            print("  ✗ Not authenticated")
    else:
        print("  ✗ Not installed")

    print("\nOAuth:")
    if env["oauth_configured"]:
        print("  ✓ GCP credentials configured")
        if env["oauth21_enabled"]:
            print("  ✓ OAuth 2.1 enabled")
    else:
        print("  ✗ GCP credentials not configured")

    print()


def _print_help():
    """Print help message."""
    print("""
google-automation-mcp - Google Workspace MCP for AI

Commands:
  setup      Interactive setup with environment detection (recommended)
  auth       Quick authentication
  status     Show authentication status
  version    Show version
  help       Show this help message

Auth options:
  auth                  Use clasp (easiest, no GCP project needed)
  auth --headless       clasp info for headless environments
  auth --legacy         Use GCP OAuth (requires project setup)
  auth --legacy --headless  GCP OAuth for headless environments
  auth --oauth21        Use OAuth 2.1 (multi-user, production)

Examples:
  google-automation-mcp setup           # Interactive setup
  google-automation-mcp auth            # Quick clasp authentication
  google-automation-mcp                 # Run MCP server

For more info: https://github.com/sam-ent/google-automation-mcp
""")


def _print_version():
    """Print version."""
    try:
        from importlib.metadata import version

        v = version("google-automation-mcp")
    except Exception:
        v = "unknown"
    print(f"google-automation-mcp {v}")


def _auth_clasp(headless: bool = False):
    """Authenticate using clasp."""
    from .auth import (
        get_credentials,
        is_clasp_installed,
        run_clasp_login,
    )
    from .auth.credential_store import get_credential_store

    print("google-automation-mcp Authentication")
    print("=" * 40)
    print()

    # Check existing credentials
    creds = get_credentials()
    if creds:
        store = get_credential_store()
        users = store.list_users()
        if users:
            print(f"Already authenticated: {', '.join(users)}")
            print()
            response = input("Re-authenticate? [y/N]: ").strip().lower()
            if response != "y":
                print("Keeping existing credentials.")
                return
            print()

    # Check clasp
    if not is_clasp_installed():
        print("clasp (Google's Apps Script CLI) is not installed.")
        print()
        print("Install it with:")
        print("  npm install -g @google/clasp")
        print()
        print("Or run interactive setup:")
        print("  google-automation-mcp setup")
        print()

        if headless:
            print("For headless environments, use:")
            print("  google-automation-mcp auth --legacy --headless")
        return

    if headless:
        print("clasp requires a browser for OAuth.")
        print()
        print("Options:")
        print("1. Run 'clasp login' on a machine with browser access,")
        print("   then copy ~/.clasprc.json to this machine.")
        print()
        print("2. Use legacy OAuth (requires GCP project):")
        print("   google-automation-mcp auth --legacy --headless")
        return

    # Run clasp login
    print("Using clasp for authentication (no GCP project needed)")
    print()

    success, message = run_clasp_login()
    print(message)

    if success:
        # Import credentials
        from .setup import _import_clasp_credentials

        _import_clasp_credentials()


def _auth_local_legacy():
    """Browser-based auth with local callback server (legacy method)."""
    from .auth import auth_interactive
    from .auth.credential_store import get_credential_store

    store = get_credential_store()
    existing = store.list_users()

    if existing:
        print(f"Already authenticated: {', '.join(existing)}")
        print()
        print("To re-authenticate, use: google-automation-mcp setup")
        return

    print("Legacy OAuth Authentication (requires GCP project)")
    print("=" * 40)
    print()
    print("Opening browser for Google authentication...")
    print("(If browser doesn't open, use --headless)")
    print()

    try:
        auth_interactive()
        print()
        print("✓ Authentication successful!")
    except ValueError as e:
        print(f"Error: {e}")
        print()
        print("For easier setup without GCP project:")
        print("  google-automation-mcp setup")
        sys.exit(1)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)


def _auth_headless_legacy():
    """Manual auth flow for headless environments (legacy method)."""
    from .auth import start_auth_flow, complete_auth_flow
    from .auth.credential_store import get_credential_store

    print("Legacy Headless Authentication (requires GCP project)")
    print("=" * 40)
    print()

    store = get_credential_store()
    existing = store.list_users()

    if existing:
        print(f"Already authenticated: {', '.join(existing)}")
        print()
        response = input("Re-authenticate? [y/N]: ").strip().lower()
        if response != "y":
            print("Keeping existing credentials.")
            return

    try:
        auth_url, flow = start_auth_flow()
    except ValueError as e:
        print(f"Error: {e}")
        print()
        print("For easier setup, use clasp on a machine with browser access:")
        print("  npm install -g @google/clasp")
        print("  clasp login")
        print("Then copy ~/.clasprc.json to this machine.")
        sys.exit(1)

    print("1. Open this URL in any browser:\n")
    print(f"   {auth_url}\n")
    print("2. Sign in with your Google account\n")
    print("3. Authorize the application\n")
    print("4. You'll be redirected to a page that won't load (http://localhost/...)")
    print("   This is expected.\n")
    print("5. Copy the FULL URL from your browser's address bar\n")

    redirect_url = input("Paste the redirect URL here: ").strip()

    if not redirect_url:
        print("\nNo URL provided")
        sys.exit(1)

    if not redirect_url.startswith("http"):
        print("\nInvalid URL. Should start with http")
        sys.exit(1)

    try:
        complete_auth_flow(flow, redirect_url)
        print()
        print("✓ Authentication successful!")
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
