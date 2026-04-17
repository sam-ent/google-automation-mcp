"""
Router Client

Makes HTTP POST calls to the deployed Apps Script Web App router.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .deployer import ensure_router_deployed

logger = logging.getLogger(__name__)

_TIMEOUT = 30  # Apps Script max execution time


class RouterError(Exception):
    """Raised when the router returns an error."""

    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code


async def call_router(
    user_email: str,
    action: str,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Call the Apps Script router for a user.

    Ensures the router is deployed, then makes an HTTP POST with the
    action and params. Returns the parsed result.

    Args:
        user_email: The user's Google email address
        action: The router action name (e.g., 'search_gmail')
        params: Parameters for the action

    Returns:
        The result from the Apps Script handler

    Raises:
        RouterError: If the router returns an error
        ValueError: If the user has no deployed router and deployment fails
    """
    state = await ensure_router_deployed(user_email)
    url = state["web_app_url"]
    secret = state["secret"]

    payload = json.dumps({
        "secret": secret,
        "action": action,
        "params": params or {},
    }).encode("utf-8")

    def _do_request():
        req = Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=_TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RouterError(f"HTTP {e.code}: {body}", e.code)
        except URLError as e:
            raise RouterError(f"Connection error: {e.reason}")

    result = await asyncio.to_thread(_do_request)

    if "error" in result:
        raise RouterError(
            result["error"],
            result.get("code", 500),
        )

    return result.get("result")
