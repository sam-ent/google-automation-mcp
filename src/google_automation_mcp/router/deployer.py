"""
Router Deployer

Creates and deploys the Apps Script Web App router per user.
Uses the Apps Script API (via clasp auth) — no GCP project needed.
"""

import asyncio
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any

from googleapiclient.errors import HttpError

from ..auth import get_script_service

logger = logging.getLogger(__name__)

ROUTER_STATE_DIR = Path.home() / ".secrets" / "google-automation-mcp" / "routers"
TEMPLATE_DIR = Path(__file__).parent


def _state_path(user_email: str) -> Path:
    safe = user_email.replace("@", "_at_").replace(".", "_")
    return ROUTER_STATE_DIR / f"{safe}.json"


def _load_state(user_email: str) -> Optional[Dict[str, Any]]:
    path = _state_path(user_email)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _save_state(user_email: str, state: Dict[str, Any]) -> None:
    ROUTER_STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = _state_path(user_email)
    path.write_text(json.dumps(state, indent=2))
    os.chmod(path, 0o600)


def _get_script_source(secret: str) -> str:
    template = (TEMPLATE_DIR / "script_template.js").read_text()
    return template.replace("{{MCP_SECRET}}", secret)


def _get_manifest() -> str:
    return (TEMPLATE_DIR / "manifest.json").read_text()


async def _create_script_project(title: str) -> str:
    service = get_script_service()
    body = {"title": title}
    try:
        project = await asyncio.to_thread(
            service.projects().create(body=body).execute
        )
    except HttpError as e:
        if "User has not enabled the Apps Script API" in str(e):
            raise RuntimeError(
                "Apps Script API is not enabled. "
                "Enable it at https://script.google.com/home/usersettings "
                "then retry."
            ) from None
        raise
    return project["scriptId"]


async def _upload_script_content(script_id: str, secret: str) -> None:
    service = get_script_service()
    body = {
        "files": [
            {
                "name": "Router",
                "type": "SERVER_JS",
                "source": _get_script_source(secret),
            },
            {
                "name": "appsscript",
                "type": "JSON",
                "source": _get_manifest(),
            },
        ]
    }
    await asyncio.to_thread(
        service.projects().updateContent(
            scriptId=script_id, body=body
        ).execute
    )


async def _create_version(script_id: str, description: str) -> int:
    service = get_script_service()
    body = {"description": description}
    version = await asyncio.to_thread(
        service.projects().versions().create(
            scriptId=script_id, body=body
        ).execute
    )
    return version["versionNumber"]


async def _create_web_app_deployment(script_id: str, version_number: int) -> str:
    service = get_script_service()
    body = {
        "versionNumber": version_number,
        "description": "MCP Router",
        "manifestFileName": "appsscript",
    }
    deployment = await asyncio.to_thread(
        service.projects().deployments().create(
            scriptId=script_id, body=body
        ).execute
    )
    deployment_id = deployment["deploymentId"]
    web_app_url = f"https://script.google.com/macros/s/{deployment_id}/exec"
    return web_app_url


async def _update_deployment(
    script_id: str, deployment_id: str, version_number: int
) -> str:
    service = get_script_service()
    body = {
        "deploymentConfig": {
            "versionNumber": version_number,
            "description": "MCP Router",
            "manifestFileName": "appsscript",
        }
    }
    await asyncio.to_thread(
        service.projects().deployments().update(
            scriptId=script_id, deploymentId=deployment_id, body=body
        ).execute
    )
    web_app_url = f"https://script.google.com/macros/s/{deployment_id}/exec"
    return web_app_url


async def deploy_router(user_email: str) -> Dict[str, Any]:
    """
    Deploy a fresh router for a user. Returns state dict with
    script_id, deployment_id, web_app_url, and secret.
    """
    secret = secrets.token_urlsafe(32)
    title = "MCP-Router"

    logger.info(f"Creating router script for {user_email}")
    script_id = await _create_script_project(title)

    logger.info(f"Uploading router code to {script_id}")
    await _upload_script_content(script_id, secret)

    logger.info(f"Creating version for {script_id}")
    version = await _create_version(script_id, "MCP Router v1")

    logger.info(f"Deploying web app for {script_id} v{version}")
    web_app_url = await _create_web_app_deployment(script_id, version)

    state = {
        "user_email": user_email,
        "script_id": script_id,
        "version": version,
        "web_app_url": web_app_url,
        "secret": secret,
    }
    _save_state(user_email, state)

    logger.info(f"Router deployed: {web_app_url}")
    return state


async def update_router(user_email: str) -> Dict[str, Any]:
    """
    Update an existing router's code and redeploy.
    """
    state = _load_state(user_email)
    if not state:
        return await deploy_router(user_email)

    script_id = state["script_id"]
    secret = state["secret"]

    logger.info(f"Updating router code for {script_id}")
    await _upload_script_content(script_id, secret)

    version = await _create_version(script_id, "MCP Router update")

    # Find existing deployment to update
    service = get_script_service()
    deployments = await asyncio.to_thread(
        service.projects().deployments().list(scriptId=script_id).execute
    )
    deployment_list = deployments.get("deployments", [])

    # Find the non-HEAD deployment
    deployment_id = None
    for d in deployment_list:
        config = d.get("deploymentConfig", {})
        if config.get("description") == "MCP Router":
            deployment_id = d["deploymentId"]
            break

    if deployment_id:
        web_app_url = await _update_deployment(script_id, deployment_id, version)
    else:
        web_app_url = await _create_web_app_deployment(script_id, version)

    state["version"] = version
    state["web_app_url"] = web_app_url
    _save_state(user_email, state)

    logger.info(f"Router updated: {web_app_url}")
    return state


async def ensure_router_deployed(user_email: str) -> Dict[str, Any]:
    """
    Ensure a router is deployed for the user. Returns state dict.
    Creates one if it doesn't exist.
    """
    state = _load_state(user_email)
    if state and state.get("web_app_url"):
        return state
    return await deploy_router(user_email)
