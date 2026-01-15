"""
OAuth Configuration Management

Centralized OAuth-related configuration with environment variable support.
Supports OAuth 2.0, OAuth 2.1 with PKCE, and clasp authentication.

Forked from google_workspace_mcp/auth/oauth_config.py
"""

import os
from urllib.parse import urlparse
from typing import List, Optional, Dict, Any


class OAuthConfig:
    """
    Centralized OAuth configuration management.

    Provides a single source of truth for all OAuth-related configuration values.
    """

    def __init__(self):
        # Base server configuration
        self.base_uri = os.getenv("APPSCRIPT_MCP_BASE_URI", "http://localhost")
        self.port = int(os.getenv("PORT", os.getenv("APPSCRIPT_MCP_PORT", "8000")))
        self.base_url = f"{self.base_uri}:{self.port}"

        # External URL for reverse proxy scenarios
        self.external_url = os.getenv("APPSCRIPT_MCP_EXTERNAL_URL")

        # OAuth client configuration
        self.client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

        # OAuth 2.1 configuration
        self.oauth21_enabled = (
            os.getenv("MCP_ENABLE_OAUTH21", "false").lower() == "true"
        )
        self.pkce_required = self.oauth21_enabled  # PKCE is mandatory in OAuth 2.1
        self.supported_code_challenge_methods = (
            ["S256", "plain"] if not self.oauth21_enabled else ["S256"]
        )

        # clasp configuration
        self.clasp_enabled = (
            os.getenv("APPSCRIPT_MCP_CLASP_ENABLED", "true").lower() == "true"
        )

        # Transport mode (will be set at runtime)
        self._transport_mode = "stdio"  # Default

        # Redirect URI configuration
        self.redirect_uri = self._get_redirect_uri()
        self.redirect_path = self._get_redirect_path(self.redirect_uri)

    def _get_redirect_uri(self) -> str:
        """Get the OAuth redirect URI."""
        explicit_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
        if explicit_uri:
            return explicit_uri
        return f"{self.base_url}/oauth2callback"

    @staticmethod
    def _get_redirect_path(uri: str) -> str:
        """Extract the redirect path from a full redirect URI."""
        parsed = urlparse(uri)
        if parsed.scheme or parsed.netloc:
            path = parsed.path or "/oauth2callback"
        else:
            path = uri if uri.startswith("/") else f"/{uri}"
        return path or "/oauth2callback"

    def get_redirect_uris(self) -> List[str]:
        """Get all valid OAuth redirect URIs."""
        uris = [self.redirect_uri]

        # Custom redirect URIs from environment
        custom_uris = os.getenv("OAUTH_CUSTOM_REDIRECT_URIS")
        if custom_uris:
            uris.extend([uri.strip() for uri in custom_uris.split(",")])

        # Remove duplicates while preserving order
        return list(dict.fromkeys(uris))

    def is_configured(self) -> bool:
        """Check if OAuth is properly configured with GCP credentials."""
        return bool(self.client_id and self.client_secret)

    def get_oauth_base_url(self) -> str:
        """Get OAuth base URL for constructing OAuth endpoints."""
        if self.external_url:
            return self.external_url
        return self.base_url

    def set_transport_mode(self, mode: str) -> None:
        """Set the current transport mode."""
        self._transport_mode = mode

    def get_transport_mode(self) -> str:
        """Get the current transport mode."""
        return self._transport_mode

    def is_oauth21_enabled(self) -> bool:
        """Check if OAuth 2.1 mode is enabled."""
        return self.oauth21_enabled

    def is_clasp_enabled(self) -> bool:
        """Check if clasp authentication is enabled."""
        return self.clasp_enabled

    def get_environment_summary(self) -> dict:
        """Get a summary of the current OAuth configuration (excluding secrets)."""
        return {
            "base_url": self.base_url,
            "external_url": self.external_url,
            "effective_oauth_url": self.get_oauth_base_url(),
            "redirect_uri": self.redirect_uri,
            "client_configured": bool(self.client_id),
            "oauth21_enabled": self.oauth21_enabled,
            "clasp_enabled": self.clasp_enabled,
            "pkce_required": self.pkce_required,
            "transport_mode": self._transport_mode,
        }

    def get_authorization_server_metadata(
        self, scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get OAuth authorization server metadata per RFC 8414."""
        oauth_base = self.get_oauth_base_url()
        metadata = {
            "issuer": "https://accounts.google.com",
            "authorization_endpoint": f"{oauth_base}/oauth2/authorize",
            "token_endpoint": f"{oauth_base}/oauth2/token",
            "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
            "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
            "response_types_supported": ["code", "token"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
            ],
            "code_challenge_methods_supported": self.supported_code_challenge_methods,
        }

        if scopes is not None:
            metadata["scopes_supported"] = scopes

        if self.oauth21_enabled:
            metadata["pkce_required"] = True
            metadata["response_types_supported"] = ["code"]
            metadata["require_exact_redirect_uri"] = True

        return metadata


# =============================================================================
# Global Configuration Instance
# =============================================================================

_oauth_config: Optional[OAuthConfig] = None


def get_oauth_config() -> OAuthConfig:
    """Get the global OAuth configuration instance."""
    global _oauth_config
    if _oauth_config is None:
        _oauth_config = OAuthConfig()
    return _oauth_config


def reload_oauth_config() -> OAuthConfig:
    """Reload the OAuth configuration from environment variables."""
    global _oauth_config
    _oauth_config = OAuthConfig()
    return _oauth_config


# =============================================================================
# Convenience Functions
# =============================================================================


def get_oauth_base_url() -> str:
    """Get OAuth base URL."""
    return get_oauth_config().get_oauth_base_url()


def get_oauth_redirect_uri() -> str:
    """Get the primary OAuth redirect URI."""
    return get_oauth_config().redirect_uri


def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured with GCP credentials."""
    return get_oauth_config().is_configured()


def is_oauth21_enabled() -> bool:
    """Check if OAuth 2.1 is enabled."""
    return get_oauth_config().is_oauth21_enabled()


def is_clasp_enabled() -> bool:
    """Check if clasp authentication is enabled."""
    return get_oauth_config().is_clasp_enabled()


def set_transport_mode(mode: str) -> None:
    """Set the current transport mode."""
    get_oauth_config().set_transport_mode(mode)


def get_transport_mode() -> str:
    """Get the current transport mode."""
    return get_oauth_config().get_transport_mode()
