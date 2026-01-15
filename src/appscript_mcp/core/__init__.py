"""
Core utilities for appscript-mcp.

Forked from google_workspace_mcp with attribution.
"""

from .context import (
    get_injected_oauth_credentials,
    set_injected_oauth_credentials,
    get_fastmcp_session_id,
    set_fastmcp_session_id,
)

__all__ = [
    "get_injected_oauth_credentials",
    "set_injected_oauth_credentials",
    "get_fastmcp_session_id",
    "set_fastmcp_session_id",
]
