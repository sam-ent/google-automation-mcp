"""
Shared Error Handler for MCP Tools

Provides a common error handling decorator used across all tool modules.
"""

import functools
import logging
from typing import Callable, TypeVar, Any

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """
    Decorator to handle API errors gracefully.

    Handles common Google API errors (401, 403, 404) with user-friendly messages.
    Also catches credential errors and provides appropriate guidance.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HttpError as e:
            error_msg = str(e)
            if e.resp.status == 401:
                return f"Authentication error: {error_msg}\n\nPlease run start_google_auth to authenticate."
            elif e.resp.status == 403:
                if "accessNotConfigured" in error_msg:
                    return (
                        f"API not enabled: {error_msg}\n\n"
                        "Please enable the required API in your Google Cloud Console."
                    )
                return f"Permission denied: {error_msg}"
            elif e.resp.status == 404:
                return f"Not found: {error_msg}"
            else:
                return f"API error: {error_msg}"
        except Exception as e:
            if "No valid credentials" in str(e):
                return str(e)
            logger.exception(f"Error in {func.__name__}")
            return f"Error: {str(e)}"

    return wrapper  # type: ignore
