"""
Service Adapter for Tool Functions

Provides a simple decorator that injects authenticated Google services
into tool functions. Compatible with both single-user (clasp) and
multi-user (OAuth 2.1) modes.

Usage:
    @with_gmail_service
    async def list_messages(service, user_google_email: str):
        return service.users().messages().list(userId="me").execute()

    @with_drive_service
    async def list_files(service, user_google_email: str):
        return service.files().list().execute()
"""

import logging
from functools import wraps
from typing import Optional, Callable, Any

from googleapiclient.discovery import build

from .credential_store import get_credential_store
from .google_auth import get_credentials, get_credentials_for_user

logger = logging.getLogger(__name__)


def get_service_for_user(
    service_name: str, version: str, user_email: Optional[str] = None
) -> Any:
    """
    Get an authenticated Google API service for a user.

    Args:
        service_name: API service name (e.g., "gmail", "drive")
        version: API version (e.g., "v1", "v3")
        user_email: User's email (optional, will use any available credentials if not provided)

    Returns:
        Authenticated Google API service

    Raises:
        ValueError if no valid credentials available
    """
    credentials = None

    if user_email:
        credentials = get_credentials_for_user(user_email)
        if credentials is None:
            raise ValueError(f"No credentials found for user: {user_email}")
    else:
        credentials = get_credentials()
        if credentials is None:
            raise ValueError("No valid credentials. Run: google-automation-mcp setup")

    return build(service_name, version, credentials=credentials)


def with_service(service_name: str, version: str):
    """
    Decorator that injects an authenticated Google service into a function.

    The decorated function must accept:
    - service: The authenticated Google API service (injected)
    - user_google_email: str (passed by caller or extracted from credentials)

    Example:
        @with_service("gmail", "v1")
        async def get_message(service, user_google_email: str, message_id: str):
            return service.users().messages().get(userId="me", id=message_id).execute()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_google_email from kwargs
            user_email = kwargs.get("user_google_email")

            # Get authenticated service
            try:
                service = get_service_for_user(service_name, version, user_email)
            except ValueError as e:
                return f"Authentication error: {e}"

            # If no user_email provided, try to determine it
            if not user_email:
                store = get_credential_store()
                users = store.list_users()
                if users:
                    user_email = users[0]
                    kwargs["user_google_email"] = user_email

            # Call the wrapped function with injected service
            return await func(service, *args, **kwargs)

        return wrapper

    return decorator


# Convenience decorators for common services
def with_gmail_service(func: Callable) -> Callable:
    """Decorator that injects authenticated Gmail service."""
    return with_service("gmail", "v1")(func)


def with_drive_service(func: Callable) -> Callable:
    """Decorator that injects authenticated Drive service."""
    return with_service("drive", "v3")(func)


def with_sheets_service(func: Callable) -> Callable:
    """Decorator that injects authenticated Sheets service."""
    return with_service("sheets", "v4")(func)


def with_calendar_service(func: Callable) -> Callable:
    """Decorator that injects authenticated Calendar service."""
    return with_service("calendar", "v3")(func)


def with_docs_service(func: Callable) -> Callable:
    """Decorator that injects authenticated Docs service."""
    return with_service("docs", "v1")(func)


def with_script_service(func: Callable) -> Callable:
    """Decorator that injects authenticated Apps Script service."""
    return with_service("script", "v1")(func)
