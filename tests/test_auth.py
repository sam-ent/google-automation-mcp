"""
Tests for the authentication module.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCredentialStore:
    """Tests for SecureCredentialStore."""

    def test_store_and_retrieve_credential(self):
        """Test storing and retrieving credentials."""
        from google_automation_mcp.auth.credential_store import SecureCredentialStore

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a subdirectory to avoid chmod issues on /tmp
            cred_dir = Path(tmpdir) / "credentials"
            store = SecureCredentialStore(base_dir=cred_dir)

            # Create mock credentials
            mock_creds = MagicMock()
            mock_creds.token = "test_token"
            mock_creds.refresh_token = "test_refresh"
            mock_creds.token_uri = "https://oauth2.googleapis.com/token"
            mock_creds.client_id = "test_client_id"
            mock_creds.client_secret = "test_secret"
            mock_creds.scopes = ["https://www.googleapis.com/auth/script.projects"]
            mock_creds.expiry = None

            # Store
            result = store.store_credential("test@example.com", mock_creds)
            assert result is True

            # List users
            users = store.list_users()
            assert "test@example.com" in users

    def test_list_users_empty(self):
        """Test listing users when none exist."""
        from google_automation_mcp.auth.credential_store import SecureCredentialStore

        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            store = SecureCredentialStore(base_dir=cred_dir)
            users = store.list_users()
            assert users == []

    def test_delete_credential(self):
        """Test deleting credentials."""
        from google_automation_mcp.auth.credential_store import SecureCredentialStore

        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            cred_dir.mkdir(parents=True)
            store = SecureCredentialStore(base_dir=cred_dir)

            # Create a credential file manually using the store's path format
            safe_email = "delete_at_example_com"
            cred_file = cred_dir / f"{safe_email}.json"
            cred_file.write_text('{"token": "test"}')

            # Delete
            result = store.delete_credential("delete@example.com")
            assert result is True
            assert not cred_file.exists()


class TestOAuthConfig:
    """Tests for OAuthConfig."""

    def test_default_config(self):
        """Test default OAuth configuration."""
        from google_automation_mcp.auth.oauth_config import OAuthConfig

        config = OAuthConfig()
        assert config.base_uri == "http://localhost"
        assert config.port == 8000

    def test_env_override(self):
        """Test environment variable overrides."""
        from google_automation_mcp.auth.oauth_config import OAuthConfig

        with patch.dict(os.environ, {"APPSCRIPT_MCP_PORT": "9000"}):
            config = OAuthConfig()
            assert config.port == 9000

    def test_oauth21_detection(self):
        """Test OAuth 2.1 detection."""
        from google_automation_mcp.auth.oauth_config import OAuthConfig

        with patch.dict(os.environ, {"MCP_ENABLE_OAUTH21": "true"}):
            config = OAuthConfig()
            assert config.is_oauth21_enabled() is True

        with patch.dict(os.environ, {"MCP_ENABLE_OAUTH21": "false"}):
            config = OAuthConfig()
            assert config.is_oauth21_enabled() is False


class TestClaspIntegration:
    """Tests for clasp integration."""

    def test_clasp_rc_path(self):
        """Test clasp RC path is correct."""
        from google_automation_mcp.auth.google_auth import CLASP_RC_PATH

        assert CLASP_RC_PATH == Path.home() / ".clasprc.json"

    def test_is_clasp_authenticated_no_file(self):
        """Test clasp auth check when file doesn't exist."""
        from google_automation_mcp.auth.google_auth import is_clasp_authenticated

        with patch("google_automation_mcp.auth.google_auth.CLASP_RC_PATH") as mock_path:
            mock_path.exists.return_value = False
            assert is_clasp_authenticated() is False

    def test_get_clasp_tokens_no_file(self):
        """Test getting clasp tokens when file doesn't exist."""
        from google_automation_mcp.auth.google_auth import get_clasp_tokens

        with patch("google_automation_mcp.auth.google_auth.CLASP_RC_PATH") as mock_path:
            mock_path.exists.return_value = False
            assert get_clasp_tokens() is None

    def test_get_clasp_tokens_valid(self):
        """Test getting clasp tokens from valid file."""
        from google_automation_mcp.auth.google_auth import get_clasp_tokens

        mock_token_data = {
            "token": {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "scope": "https://www.googleapis.com/auth/script.projects",
                "token_type": "Bearer",
                "expiry_date": 1700000000000,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mock_token_data, f)
            temp_path = f.name

        try:
            with patch("google_automation_mcp.auth.google_auth.CLASP_RC_PATH", Path(temp_path)):
                tokens = get_clasp_tokens()
                assert tokens is not None
                assert tokens["access_token"] == "test_access"
                assert tokens["refresh_token"] == "test_refresh"
        finally:
            os.unlink(temp_path)


class TestScopes:
    """Tests for OAuth scopes."""

    def test_scopes_defined(self):
        """Test that required scopes are defined."""
        from google_automation_mcp.auth.scopes import SCOPES, SCRIPT_SCOPES, DRIVE_SCOPES

        assert len(SCOPES) > 0
        assert "https://www.googleapis.com/auth/script.projects" in SCRIPT_SCOPES
        assert "https://www.googleapis.com/auth/drive" in DRIVE_SCOPES

    def test_tool_scopes_map(self):
        """Test tool to scopes mapping."""
        from google_automation_mcp.auth.scopes import TOOL_SCOPES_MAP

        assert "appscript" in TOOL_SCOPES_MAP
        assert "drive" in TOOL_SCOPES_MAP
        assert "gmail" in TOOL_SCOPES_MAP

    def test_get_scopes_for_tools(self):
        """Test getting scopes for specific tools."""
        from google_automation_mcp.auth.scopes import get_scopes_for_tools

        scopes = get_scopes_for_tools(["appscript"])
        assert "https://www.googleapis.com/auth/script.projects" in scopes
