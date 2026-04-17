"""Tests for the router client and deployer."""

import json
from unittest.mock import patch, AsyncMock, MagicMock
from urllib.error import URLError, HTTPError
import pytest

from google_automation_mcp.router.client import call_router, RouterError
from google_automation_mcp.router.deployer import (
    _load_state,
    _save_state,
    _get_script_source,
    _get_manifest,
    _create_script_project,
    _upload_script_content,
    _create_version,
    _create_web_app_deployment,
    _update_deployment,
    deploy_router,
    update_router,
    ensure_router_deployed,
)


# =============================================================================
# Router Client Tests
# =============================================================================


class TestRouterClient:
    @pytest.mark.asyncio
    async def test_call_router_success(self):
        mock_state = {
            "web_app_url": "https://script.google.com/macros/s/test/exec",
            "secret": "test-secret",
        }
        mock_response = json.dumps({"result": [{"id": "1", "name": "test"}]})

        with patch(
            "google_automation_mcp.router.client.ensure_router_deployed",
            new_callable=AsyncMock,
            return_value=mock_state,
        ), patch(
            "google_automation_mcp.router.client.urlopen",
        ) as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_response.encode()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            result = await call_router("t@t.com", "list_drive", {"folder_id": "root"})
            assert result == [{"id": "1", "name": "test"}]

    @pytest.mark.asyncio
    async def test_call_router_error_response(self):
        mock_state = {
            "web_app_url": "https://script.google.com/macros/s/test/exec",
            "secret": "test-secret",
        }
        mock_response = json.dumps({"error": "not found", "code": 404})

        with patch(
            "google_automation_mcp.router.client.ensure_router_deployed",
            new_callable=AsyncMock,
            return_value=mock_state,
        ), patch(
            "google_automation_mcp.router.client.urlopen",
        ) as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_response.encode()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            with pytest.raises(RouterError, match="not found"):
                await call_router("t@t.com", "bad_action", {})

    @pytest.mark.asyncio
    async def test_call_router_http_error(self):
        mock_state = {
            "web_app_url": "https://script.google.com/macros/s/test/exec",
            "secret": "test-secret",
        }

        with patch(
            "google_automation_mcp.router.client.ensure_router_deployed",
            new_callable=AsyncMock,
            return_value=mock_state,
        ), patch(
            "google_automation_mcp.router.client.urlopen",
        ) as mock_urlopen:
            err = HTTPError(
                "https://...", 403, "Forbidden", {}, MagicMock(read=lambda: b"denied")
            )
            mock_urlopen.side_effect = err

            with pytest.raises(RouterError, match="HTTP 403"):
                await call_router("t@t.com", "test", {})

    @pytest.mark.asyncio
    async def test_call_router_url_error(self):
        mock_state = {
            "web_app_url": "https://script.google.com/macros/s/test/exec",
            "secret": "test-secret",
        }

        with patch(
            "google_automation_mcp.router.client.ensure_router_deployed",
            new_callable=AsyncMock,
            return_value=mock_state,
        ), patch(
            "google_automation_mcp.router.client.urlopen",
        ) as mock_urlopen:
            mock_urlopen.side_effect = URLError("timeout")

            with pytest.raises(RouterError, match="Connection error"):
                await call_router("t@t.com", "test", {})


# =============================================================================
# Router Deployer Tests
# =============================================================================


class TestDeployerHelpers:
    def test_load_state_missing(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            assert _load_state("nobody@example.com") is None

    def test_save_and_load_state(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            state = {"script_id": "abc", "web_app_url": "https://...", "secret": "s"}
            _save_state("test@example.com", state)
            loaded = _load_state("test@example.com")
            assert loaded["script_id"] == "abc"

    def test_get_script_source(self):
        source = _get_script_source("my-secret-token")
        assert "my-secret-token" in source
        assert "{{MCP_SECRET}}" not in source
        assert "function doPost" in source

    def test_get_manifest(self):
        manifest = _get_manifest()
        parsed = json.loads(manifest)
        assert "webapp" in parsed
        assert parsed["webapp"]["access"] == "ANYONE_ANONYMOUS"


@pytest.fixture
def mock_script_service():
    service = MagicMock()
    with patch(
        "google_automation_mcp.router.deployer.get_script_service",
        return_value=service,
    ):
        yield service


class TestDeployerApiCalls:
    @pytest.mark.asyncio
    async def test_create_script_project(self, mock_script_service):
        mock_script_service.projects().create().execute.return_value = {
            "scriptId": "new-script-id"
        }
        result = await _create_script_project("Test")
        assert result == "new-script-id"

    @pytest.mark.asyncio
    async def test_create_script_project_api_disabled(self, mock_script_service):
        from googleapiclient.errors import HttpError

        resp = MagicMock(status=403)
        err = HttpError(resp, b"User has not enabled the Apps Script API")
        mock_script_service.projects().create().execute.side_effect = err

        with pytest.raises(RuntimeError, match="Apps Script API is not enabled"):
            await _create_script_project("Test")

    @pytest.mark.asyncio
    async def test_upload_script_content(self, mock_script_service):
        mock_script_service.projects().updateContent().execute.return_value = {}
        await _upload_script_content("script-id", "secret-token")
        mock_script_service.projects().updateContent.assert_called()

    @pytest.mark.asyncio
    async def test_create_version(self, mock_script_service):
        mock_script_service.projects().versions().create().execute.return_value = {
            "versionNumber": 3
        }
        result = await _create_version("script-id", "v3")
        assert result == 3

    @pytest.mark.asyncio
    async def test_create_web_app_deployment(self, mock_script_service):
        mock_script_service.projects().deployments().create().execute.return_value = {
            "deploymentId": "deploy-123"
        }
        result = await _create_web_app_deployment("script-id", 1)
        assert "deploy-123" in result
        assert result.startswith("https://script.google.com/macros/s/")

    @pytest.mark.asyncio
    async def test_update_deployment(self, mock_script_service):
        mock_script_service.projects().deployments().update().execute.return_value = {}
        result = await _update_deployment("script-id", "deploy-123", 2)
        assert "deploy-123" in result


class TestDeployRouter:
    @pytest.mark.asyncio
    async def test_deploy_router(self, tmp_path, mock_script_service):
        mock_script_service.projects().create().execute.return_value = {
            "scriptId": "new-id"
        }
        mock_script_service.projects().updateContent().execute.return_value = {}
        mock_script_service.projects().versions().create().execute.return_value = {
            "versionNumber": 1
        }
        mock_script_service.projects().deployments().create().execute.return_value = {
            "deploymentId": "dep-1"
        }

        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            state = await deploy_router("user@test.com")

        assert state["script_id"] == "new-id"
        assert "dep-1" in state["web_app_url"]
        assert len(state["secret"]) > 20
        assert _load_state.__wrapped__ if hasattr(_load_state, "__wrapped__") else True

    @pytest.mark.asyncio
    async def test_update_router_existing(self, tmp_path, mock_script_service):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            _save_state("user@test.com", {
                "script_id": "existing-id", "secret": "old-secret",
                "web_app_url": "https://old", "version": 1,
            })

            mock_script_service.projects().updateContent().execute.return_value = {}
            mock_script_service.projects().versions().create().execute.return_value = {
                "versionNumber": 2
            }
            mock_script_service.projects().deployments().list().execute.return_value = {
                "deployments": [
                    {"deploymentId": "dep-1", "deploymentConfig": {"description": "MCP Router"}}
                ]
            }
            mock_script_service.projects().deployments().update().execute.return_value = {}

            state = await update_router("user@test.com")

        assert state["version"] == 2
        assert "dep-1" in state["web_app_url"]

    @pytest.mark.asyncio
    async def test_update_router_no_existing_deployment(self, tmp_path, mock_script_service):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            _save_state("user@test.com", {
                "script_id": "existing-id", "secret": "old-secret",
                "web_app_url": "https://old", "version": 1,
            })

            mock_script_service.projects().updateContent().execute.return_value = {}
            mock_script_service.projects().versions().create().execute.return_value = {
                "versionNumber": 2
            }
            mock_script_service.projects().deployments().list().execute.return_value = {
                "deployments": []
            }
            mock_script_service.projects().deployments().create().execute.return_value = {
                "deploymentId": "dep-new"
            }

            state = await update_router("user@test.com")

        assert "dep-new" in state["web_app_url"]

    @pytest.mark.asyncio
    async def test_update_router_no_state_falls_back_to_deploy(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path), \
             patch(
                 "google_automation_mcp.router.deployer.deploy_router",
                 new_callable=AsyncMock,
                 return_value={"script_id": "fresh", "web_app_url": "https://new", "secret": "s"},
             ) as mock_deploy:
            state = await update_router("new@test.com")
            assert state["script_id"] == "fresh"
            mock_deploy.assert_called_once()


class TestEnsureRouterDeployed:
    @pytest.mark.asyncio
    async def test_existing_state(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            _save_state("t@t.com", {
                "script_id": "abc", "web_app_url": "https://...", "secret": "s",
            })
            result = await ensure_router_deployed("t@t.com")
            assert result["script_id"] == "abc"

    @pytest.mark.asyncio
    async def test_no_state_triggers_deploy(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path), \
             patch(
                 "google_automation_mcp.router.deployer.deploy_router",
                 new_callable=AsyncMock,
                 return_value={"script_id": "new", "web_app_url": "https://...", "secret": "s"},
             ) as mock_deploy:
            result = await ensure_router_deployed("new@example.com")
            assert result["script_id"] == "new"
            mock_deploy.assert_called_once()
