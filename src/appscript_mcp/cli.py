"""
CLI entry point for appscript-mcp.

Provides authentication commands and MCP server startup.
Uses clasp (Google's official Apps Script CLI) for OAuth by default.
"""

import sys


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]

    # No args or non-auth command: run MCP server
    if not args or args[0] != "auth":
        from .server import main as server_main

        server_main()
        return

    # Auth command
    headless = "--headless" in args
    legacy = "--legacy" in args

    if legacy:
        # Use our own OAuth flow (requires GCP project)
        if headless:
            _auth_headless_legacy()
        else:
            _auth_local_legacy()
    else:
        # Use clasp (no GCP project needed)
        _auth_clasp(headless=headless)


def _auth_clasp(headless: bool = False):
    """Authenticate using clasp (recommended - no GCP project needed)."""
    from .auth import (
        get_credentials,
        is_clasp_installed,
        run_clasp_login,
        SECURE_TOKEN_PATH,
    )

    print("Apps Script MCP Authentication")
    print("=" * 40)
    print()

    # Check if already authenticated
    existing = get_credentials()
    if existing:
        print("Already authenticated.")
        print(f"Token location: {SECURE_TOKEN_PATH}")
        print()
        response = input("Re-authenticate? [y/N]: ").strip().lower()
        if response != "y":
            print("Keeping existing credentials.")
            return
        print()

    # Check if clasp is installed
    if not is_clasp_installed():
        print("clasp (Google's Apps Script CLI) is not installed.")
        print()
        print("Install it with:")
        print("  npm install -g @google/clasp")
        print()
        print("Or with npx (no global install):")
        print("  npx @google/clasp login")
        print()

        if headless:
            print("For headless environments without npm, use:")
            print("  appscript-mcp auth --legacy --headless")
            print()
            print("This requires a GCP project with OAuth credentials.")
        else:
            response = input("Try to install clasp now? [Y/n]: ").strip().lower()
            if response != "n":
                _install_clasp()
                if not is_clasp_installed():
                    print("\nclasp installation failed. Please install manually.")
                    sys.exit(1)
            else:
                print("\nTo authenticate without clasp, use:")
                print("  appscript-mcp auth --legacy")
                sys.exit(1)
        return

    # clasp is installed, run login
    print("Using clasp for authentication (no GCP project needed)")
    print()

    if headless:
        print("Note: clasp requires a browser for OAuth.")
        print("Run 'clasp login' on a machine with browser access,")
        print("then copy ~/.clasprc.json to this machine.")
        print()
        print("Alternatively, use --legacy for headless OAuth:")
        print("  appscript-mcp auth --legacy --headless")
        return

    if run_clasp_login():
        # Verify credentials were obtained
        creds = get_credentials()
        if creds:
            print()
            print("Authentication successful!")
            print(f"Token saved to: {SECURE_TOKEN_PATH}")
        else:
            print()
            print("Authentication may have succeeded but credentials not found.")
            print("Try running 'clasp login' manually.")
            sys.exit(1)
    else:
        print()
        print("Authentication failed. Please try again or use --legacy mode.")
        sys.exit(1)


def _install_clasp():
    """Attempt to install clasp via npm."""
    import subprocess

    print("Installing clasp...")
    print()

    try:
        result = subprocess.run(
            ["npm", "install", "-g", "@google/clasp"],
            timeout=120,
        )
        if result.returncode == 0:
            print()
            print("clasp installed successfully!")
        else:
            print()
            print("npm install failed. Trying with sudo...")
            subprocess.run(
                ["sudo", "npm", "install", "-g", "@google/clasp"],
                timeout=120,
            )
    except FileNotFoundError:
        print("npm not found. Please install Node.js first:")
        print("  https://nodejs.org/")
    except subprocess.TimeoutExpired:
        print("Installation timed out.")


def _auth_local_legacy():
    """Browser-based auth with local callback server (legacy method)."""
    from .auth import auth_interactive, get_credentials, SECURE_TOKEN_PATH

    # Check if already authenticated
    existing = get_credentials()
    if existing:
        print("Already authenticated.")
        print(f"Token location: {SECURE_TOKEN_PATH}")
        print()
        print("To re-authenticate, delete the token file and try again.")
        return

    print("Legacy authentication (requires GCP project)")
    print("=" * 40)
    print()
    print("Opening browser for Google authentication...")
    print("(If browser doesn't open, use: appscript-mcp auth --legacy --headless)\n")

    try:
        auth_interactive()
        print()
        print("Authentication successful!")
        print(f"Token saved to: {SECURE_TOKEN_PATH}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print()
        print("For easier setup without GCP project, use clasp:")
        print("  npm install -g @google/clasp")
        print("  appscript-mcp auth")
        sys.exit(1)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)


def _auth_headless_legacy():
    """Manual auth flow for headless environments (legacy method)."""
    from .auth import start_auth_flow, complete_auth_flow, get_credentials, SECURE_TOKEN_PATH

    print("Legacy headless authentication (requires GCP project)")
    print("=" * 40)
    print()

    # Check if already authenticated
    existing = get_credentials()
    if existing:
        print("Already authenticated.")
        print(f"Token location: {SECURE_TOKEN_PATH}")
        print()
        response = input("Re-authenticate? [y/N]: ").strip().lower()
        if response != "y":
            print("Keeping existing credentials.")
            return

    try:
        auth_url, flow = start_auth_flow()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print()
        print("You need OAuth credentials from a GCP project.")
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

    if not redirect_url.startswith("http://localhost"):
        print("\nInvalid URL. Should start with http://localhost")
        sys.exit(1)

    try:
        complete_auth_flow(flow, redirect_url)
        print()
        print("Authentication successful!")
        print(f"Token saved to: {SECURE_TOKEN_PATH}")
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
