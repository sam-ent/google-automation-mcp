"""
CLI entry point for appscript-mcp.

Provides authentication commands and MCP server startup.
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

    if headless:
        _auth_headless()
    else:
        _auth_local()


def _auth_local():
    """Browser-based auth with local callback server."""
    from .auth import auth_interactive, get_credentials

    # Check if already authenticated
    existing = get_credentials()
    if existing:
        print("Already authenticated. Use --headless to re-authenticate.")
        print("Or delete ~/.appscript-mcp/token.pickle to start fresh.")
        return

    print("Opening browser for Google authentication...")
    print("(If browser doesn't open, use: appscript-mcp auth --headless)\n")

    try:
        auth_interactive()
        print("\n✓ Authentication successful. Token saved to ~/.appscript-mcp/")
    except FileNotFoundError as e:
        print(f"✗ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)


def _auth_headless():
    """Manual auth flow for headless environments (no local browser)."""
    from .auth import start_auth_flow, complete_auth_flow, get_credentials

    print("Headless authentication mode")
    print("=" * 40)
    print()

    # Check if already authenticated
    existing = get_credentials()
    if existing:
        response = (
            input("Already authenticated. Re-authenticate? [y/N]: ").strip().lower()
        )
        if response != "y":
            print("Keeping existing credentials.")
            return

    try:
        auth_url, flow = start_auth_flow()
    except FileNotFoundError as e:
        print(f"✗ {e}")
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
        print("\n✗ No URL provided")
        sys.exit(1)

    if not redirect_url.startswith("http://localhost"):
        print("\n✗ Invalid URL. Should start with http://localhost")
        sys.exit(1)

    try:
        complete_auth_flow(flow, redirect_url)
        print("\n✓ Authentication successful. Token saved to ~/.appscript-mcp/")
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
