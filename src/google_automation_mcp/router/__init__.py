"""
Apps Script Web App Router

Deploys a bundled Apps Script as a Web App per user,
enabling Workspace tool calls via clasp auth only (no GCP project needed).
"""

from .client import call_router
from .deployer import ensure_router_deployed

__all__ = ["call_router", "ensure_router_deployed"]
