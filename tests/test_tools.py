"""
Unit tests for Apps Script MCP tools

Tests all tools with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_script_service():
    """Create a mock Script API service."""
    return Mock()


@pytest.fixture
def mock_drive_service():
    """Create a mock Drive API service."""
    return Mock()


class TestListScriptProjects:
    """Tests for list_script_projects."""

    @pytest.mark.asyncio
    async def test_list_projects_success(self, mock_drive_service):
        """Test listing projects returns formatted output."""
        mock_response = {
            "files": [
                {
                    "id": "test123",
                    "name": "Test Project",
                    "createdTime": "2025-01-10T10:00:00Z",
                    "modifiedTime": "2026-01-12T15:30:00Z",
                },
            ]
        }
        mock_drive_service.files().list().execute.return_value = mock_response

        with patch(
            "google_automation_mcp.appscript_tools.get_drive_service",
            return_value=mock_drive_service,
        ):
            from google_automation_mcp.appscript_tools import list_script_projects

            result = await list_script_projects()

            assert "Found 1 Apps Script projects" in result
            assert "Test Project" in result
            assert "test123" in result

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, mock_drive_service):
        """Test listing projects when none exist."""
        mock_drive_service.files().list().execute.return_value = {"files": []}

        with patch(
            "google_automation_mcp.appscript_tools.get_drive_service",
            return_value=mock_drive_service,
        ):
            from google_automation_mcp.appscript_tools import list_script_projects

            result = await list_script_projects()

            assert "No Apps Script projects found" in result


class TestGetScriptProject:
    """Tests for get_script_project."""

    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_script_service):
        """Test retrieving project details."""
        mock_response = {
            "scriptId": "test123",
            "title": "Test Project",
            "creator": {"email": "creator@example.com"},
            "createTime": "2025-01-10T10:00:00Z",
            "updateTime": "2026-01-12T15:30:00Z",
            "files": [
                {
                    "name": "Code",
                    "type": "SERVER_JS",
                    "source": "function test() { return 'hello'; }",
                }
            ],
        }
        mock_script_service.projects().get().execute.return_value = mock_response

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import get_script_project

            result = await get_script_project("test123")

            assert "Test Project" in result
            assert "creator@example.com" in result
            assert "Code" in result


class TestCreateScriptProject:
    """Tests for create_script_project."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_script_service):
        """Test creating a new project."""
        mock_response = {"scriptId": "new123", "title": "New Project"}
        mock_script_service.projects().create().execute.return_value = mock_response

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import create_script_project

            result = await create_script_project("New Project")

            assert "Script ID: new123" in result
            assert "New Project" in result


class TestUpdateScriptContent:
    """Tests for update_script_content."""

    @pytest.mark.asyncio
    async def test_update_content_success(self, mock_script_service):
        """Test updating script content."""
        files_to_update = [
            {"name": "Code", "type": "SERVER_JS", "source": "function main() {}"}
        ]
        mock_response = {"files": files_to_update}
        mock_script_service.projects().updateContent().execute.return_value = (
            mock_response
        )

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import update_script_content

            result = await update_script_content("test123", files_to_update)

            assert "Updated script project: test123" in result
            assert "Code" in result


class TestRunScriptFunction:
    """Tests for run_script_function."""

    @pytest.mark.asyncio
    async def test_run_function_success(self, mock_script_service):
        """Test executing a script function."""
        mock_response = {"response": {"result": "Success"}}
        mock_script_service.scripts().run().execute.return_value = mock_response

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import run_script_function

            result = await run_script_function("test123", "myFunction", dev_mode=True)

            assert "Execution successful" in result
            assert "myFunction" in result


class TestCreateDeployment:
    """Tests for create_deployment."""

    @pytest.mark.asyncio
    async def test_create_deployment_success(self, mock_script_service):
        """Test creating a deployment."""
        # Mock version creation (called first)
        mock_version_response = {"versionNumber": 1}
        mock_script_service.projects().versions().create().execute.return_value = (
            mock_version_response
        )

        # Mock deployment creation (called second)
        mock_deploy_response = {
            "deploymentId": "deploy123",
            "deploymentConfig": {},
        }
        mock_script_service.projects().deployments().create().execute.return_value = (
            mock_deploy_response
        )

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import create_deployment

            result = await create_deployment("test123", "Test deployment")

            assert "Deployment ID: deploy123" in result
            assert "Test deployment" in result
            assert "Version: 1" in result


class TestListDeployments:
    """Tests for list_deployments."""

    @pytest.mark.asyncio
    async def test_list_deployments_success(self, mock_script_service):
        """Test listing deployments."""
        mock_response = {
            "deployments": [
                {
                    "deploymentId": "deploy123",
                    "description": "Production",
                    "updateTime": "2026-01-12T15:30:00Z",
                }
            ]
        }
        mock_script_service.projects().deployments().list().execute.return_value = (
            mock_response
        )

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import list_deployments

            result = await list_deployments("test123")

            assert "Production" in result
            assert "deploy123" in result


class TestDeleteDeployment:
    """Tests for delete_deployment."""

    @pytest.mark.asyncio
    async def test_delete_deployment_success(self, mock_script_service):
        """Test deleting a deployment."""
        mock_script_service.projects().deployments().delete().execute.return_value = {}

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import delete_deployment

            result = await delete_deployment("test123", "deploy123")

            assert "Deleted deployment: deploy123" in result


class TestListScriptProcesses:
    """Tests for list_script_processes."""

    @pytest.mark.asyncio
    async def test_list_processes_success(self, mock_script_service):
        """Test listing script processes."""
        mock_response = {
            "processes": [
                {
                    "functionName": "myFunction",
                    "processStatus": "COMPLETED",
                    "startTime": "2026-01-12T15:30:00Z",
                    "duration": "5s",
                }
            ]
        }
        mock_script_service.processes().list().execute.return_value = mock_response

        with patch(
            "google_automation_mcp.appscript_tools.get_script_service",
            return_value=mock_script_service,
        ):
            from google_automation_mcp.appscript_tools import list_script_processes

            result = await list_script_processes()

            assert "myFunction" in result
            assert "COMPLETED" in result
