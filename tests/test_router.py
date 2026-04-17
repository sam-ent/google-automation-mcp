"""Tests for the router client and deployer."""

import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from google_automation_mcp.router.client import call_router, RouterError
from google_automation_mcp.router.deployer import (
    _load_state,
    _save_state,
    _get_script_source,
    ensure_router_deployed,
)


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


class TestRouterDeployer:
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

    @pytest.mark.asyncio
    async def test_ensure_router_deployed_existing(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path):
            state = {
                "user_email": "t@t.com",
                "script_id": "abc",
                "web_app_url": "https://script.google.com/macros/s/abc/exec",
                "secret": "s",
            }
            _save_state("t@t.com", state)
            result = await ensure_router_deployed("t@t.com")
            assert result["script_id"] == "abc"

    @pytest.mark.asyncio
    async def test_ensure_router_deployed_new(self, tmp_path):
        with patch("google_automation_mcp.router.deployer.ROUTER_STATE_DIR", tmp_path), \
             patch(
                 "google_automation_mcp.router.deployer.deploy_router",
                 new_callable=AsyncMock,
                 return_value={"script_id": "new", "web_app_url": "https://...", "secret": "s"},
             ) as mock_deploy:
            result = await ensure_router_deployed("new@example.com")
            assert result["script_id"] == "new"
            mock_deploy.assert_called_once_with("new@example.com")
