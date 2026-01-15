"""
Credential Store for appscript-mcp

Provides a standardized interface for credential storage and retrieval,
supporting per-user credentials with secure file permissions.

Forked from google_workspace_mcp/auth/credential_store.py
"""

import os
import json
import stat
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

# Secure credentials directory
DEFAULT_CREDENTIALS_DIR = Path.home() / ".secrets" / "appscript-mcp" / "credentials"


class CredentialStore(ABC):
    """Abstract base class for credential storage."""

    @abstractmethod
    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """
        Get credentials for a user by email.

        Args:
            user_email: User's email address

        Returns:
            Google Credentials object or None if not found
        """
        pass

    @abstractmethod
    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """
        Store credentials for a user.

        Args:
            user_email: User's email address
            credentials: Google Credentials object to store

        Returns:
            True if successfully stored, False otherwise
        """
        pass

    @abstractmethod
    def delete_credential(self, user_email: str) -> bool:
        """
        Delete credentials for a user.

        Args:
            user_email: User's email address

        Returns:
            True if successfully deleted, False otherwise
        """
        pass

    @abstractmethod
    def list_users(self) -> List[str]:
        """
        List all users with stored credentials.

        Returns:
            List of user email addresses
        """
        pass


class SecureCredentialStore(CredentialStore):
    """
    Credential store that uses local JSON files with secure permissions (600).

    Stores credentials in ~/.secrets/appscript-mcp/credentials/{email}.json
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the secure credential store.

        Args:
            base_dir: Base directory for credential files. If None, uses
                     ~/.secrets/appscript-mcp/credentials/
        """
        if base_dir is None:
            # Check for environment variable override
            env_dir = os.getenv("APPSCRIPT_MCP_CREDENTIALS_DIR")
            if env_dir:
                base_dir = Path(env_dir)
            else:
                base_dir = DEFAULT_CREDENTIALS_DIR

        self.base_dir = Path(base_dir)
        self._ensure_directory()
        logger.info(f"SecureCredentialStore initialized at: {self.base_dir}")

    def _ensure_directory(self) -> None:
        """Ensure the credentials directory exists with secure permissions."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Set directory permissions to 700 (owner only)
        os.chmod(self.base_dir, stat.S_IRWXU)
        # Also secure parent directories
        parent = self.base_dir.parent
        if parent.exists():
            os.chmod(parent, stat.S_IRWXU)

    def _get_credential_path(self, user_email: str) -> Path:
        """Get the file path for a user's credentials."""
        # Sanitize email for filename (replace @ and . with _)
        safe_email = user_email.replace("@", "_at_").replace(".", "_")
        return self.base_dir / f"{safe_email}.json"

    def _secure_file(self, path: Path) -> None:
        """Set secure permissions (600) on a file."""
        if path.exists():
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials from local JSON file."""
        creds_path = self._get_credential_path(user_email)

        if not creds_path.exists():
            logger.debug(f"No credential file found for {user_email}")
            return None

        try:
            with open(creds_path, "r") as f:
                creds_data = json.load(f)

            # Parse expiry if present
            expiry = None
            if creds_data.get("expiry"):
                try:
                    expiry = datetime.fromisoformat(creds_data["expiry"])
                    # Ensure timezone-naive datetime for Google auth library compatibility
                    if expiry.tzinfo is not None:
                        expiry = expiry.replace(tzinfo=None)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse expiry time for {user_email}: {e}")

            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes"),
                expiry=expiry,
            )

            logger.debug(f"Loaded credentials for {user_email}")
            return credentials

        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading credentials for {user_email}: {e}")
            return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to local JSON file with secure permissions."""
        creds_path = self._get_credential_path(user_email)

        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri or "https://oauth2.googleapis.com/token",
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else None,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            "user_email": user_email,
            "stored_at": datetime.utcnow().isoformat(),
        }

        try:
            with open(creds_path, "w") as f:
                json.dump(creds_data, f, indent=2)

            # Set secure permissions
            self._secure_file(creds_path)

            logger.info(f"Stored credentials for {user_email}")
            return True
        except IOError as e:
            logger.error(f"Error storing credentials for {user_email}: {e}")
            return False

    def delete_credential(self, user_email: str) -> bool:
        """Delete credential file for a user."""
        creds_path = self._get_credential_path(user_email)

        try:
            if creds_path.exists():
                creds_path.unlink()
                logger.info(f"Deleted credentials for {user_email}")
            return True
        except IOError as e:
            logger.error(f"Error deleting credentials for {user_email}: {e}")
            return False

    def list_users(self) -> List[str]:
        """List all users with credential files."""
        if not self.base_dir.exists():
            return []

        users = []
        try:
            for filepath in self.base_dir.glob("*.json"):
                # Convert filename back to email
                email = filepath.stem.replace("_at_", "@").replace("_", ".")
                users.append(email)
            logger.debug(f"Found {len(users)} users with credentials")
        except OSError as e:
            logger.error(f"Error listing credential files: {e}")

        return sorted(users)


# =============================================================================
# Global Credential Store Instance
# =============================================================================

_credential_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """
    Get the global credential store instance.

    Returns:
        Configured credential store instance
    """
    global _credential_store

    if _credential_store is None:
        _credential_store = SecureCredentialStore()
        logger.info(f"Initialized credential store: {type(_credential_store).__name__}")

    return _credential_store


def set_credential_store(store: CredentialStore) -> None:
    """
    Set the global credential store instance.

    Args:
        store: Credential store instance to use
    """
    global _credential_store
    _credential_store = store
    logger.info(f"Set credential store: {type(store).__name__}")
