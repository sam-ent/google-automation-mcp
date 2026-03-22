"""
Unit tests for Google Forms MCP tools

Tests all tools with mocked API responses.
"""

import pytest
from unittest.mock import MagicMock, patch

from google_automation_mcp.tools.forms import (
    get_form,
    get_form_responses,
    create_form,
    add_form_question,
)


@pytest.fixture
def mock_forms_service():
    """Create a mock Google Forms API service."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_get_service(mock_forms_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_forms_service,
    ) as mock:
        yield mock


class TestFormsTools:
    """Tests for Google Forms MCP tools."""

    @pytest.mark.asyncio
    async def test_get_form_success(self, mock_forms_service, mock_get_service):
        """Test retrieving form details and questions."""
        mock_response = {
            "formId": "form123",
            "info": {
                "title": "Test Form",
                "description": "A test form description",
            },
            "responderUri": "https://docs.google.com/forms/d/form123/viewform",
            "items": [
                {
                    "itemId": "item1",
                    "title": "What is your name?",
                    "questionItem": {"question": {"required": True}},
                }
            ],
        }
        mock_forms_service.forms().get().execute.return_value = mock_response

        result = await get_form(
            user_google_email="user@example.com", form_id="form123"
        )

        assert "Form: Test Form" in result
        assert "ID: form123" in result
        assert "Description: A test form description" in result
        assert "Questions (1):" in result
        assert "What is your name? [required] (ID: item1)" in result

    @pytest.mark.asyncio
    async def test_get_form_responses_success(self, mock_forms_service, mock_get_service):
        """Test retrieving form responses."""
        mock_response = {
            "responses": [
                {
                    "responseId": "resp1",
                    "lastSubmittedTime": "2026-03-22T10:00:00Z",
                    "answers": {
                        "q1": {
                            "textAnswers": {
                                "answers": [{"value": "John Doe"}]
                            }
                        }
                    },
                }
            ]
        }
        mock_forms_service.forms().responses().list().execute.return_value = (
            mock_response
        )

        result = await get_form_responses(
            user_google_email="user@example.com", form_id="form123"
        )

        assert "Found 1 responses:" in result
        assert "Response resp1" in result
        assert "John Doe" in result

    @pytest.mark.asyncio
    async def test_get_form_responses_empty(self, mock_forms_service, mock_get_service):
        """Test handling of no responses."""
        mock_forms_service.forms().responses().list().execute.return_value = {}

        result = await get_form_responses(
            user_google_email="user@example.com", form_id="form123"
        )

        assert "No responses found for form 'form123'." in result

    @pytest.mark.asyncio
    async def test_create_form_success(self, mock_forms_service, mock_get_service):
        """Test creating a new form."""
        mock_response = {
            "formId": "new_form_456",
            "info": {"title": "New Survey"},
            "responderUri": "https://docs.google.com/forms/d/new_form_456/viewform",
        }
        mock_forms_service.forms().create().execute.return_value = mock_response

        result = await create_form(
            user_google_email="user@example.com",
            title="New Survey",
            description="A description",
        )

        assert "Created form: New Survey" in result
        assert "ID: new_form_456" in result
        assert "edit" in result

    @pytest.mark.asyncio
    async def test_add_form_question_text(self, mock_forms_service, mock_get_service):
        """Test adding a text question."""
        mock_forms_service.forms().batchUpdate().execute.return_value = {}

        result = await add_form_question(
            user_google_email="user@example.com",
            form_id="form123",
            title="Your Email",
            question_type="TEXT",
        )

        assert "Added question 'Your Email' (TEXT)" in result
        mock_forms_service.forms().batchUpdate.assert_called()

        # Verify the structure of the request
        call_args = mock_forms_service.forms().batchUpdate.call_args
        body = call_args.kwargs["body"]
        item = body["requests"][0]["createItem"]["item"]
        assert item["title"] == "Your Email"
        assert "textQuestion" in item["questionItem"]["question"]

    @pytest.mark.asyncio
    async def test_add_form_question_choice(self, mock_forms_service, mock_get_service):
        """Test adding a multiple choice question."""
        mock_forms_service.forms().batchUpdate().execute.return_value = {}

        result = await add_form_question(
            user_google_email="user@example.com",
            form_id="form123",
            title="Pick a color",
            question_type="MULTIPLE_CHOICE",
            choices="Red, Blue, Green",
        )

        assert "Added question 'Pick a color' (MULTIPLE_CHOICE)" in result

        call_args = mock_forms_service.forms().batchUpdate.call_args
        question = call_args.kwargs["body"]["requests"][0]["createItem"]["item"][
            "questionItem"
        ]["question"]
        assert question["choiceQuestion"]["type"] == "RADIO"
        assert len(question["choiceQuestion"]["options"]) == 3
        assert question["choiceQuestion"]["options"][0]["value"] == "Red"

    @pytest.mark.asyncio
    async def test_add_form_question_choice_missing_options(
        self, mock_forms_service, mock_get_service
    ):
        """Test error when choice type is missing choices string."""
        result = await add_form_question(
            user_google_email="user@example.com",
            form_id="form123",
            title="Pick",
            question_type="MULTIPLE_CHOICE",
            choices=None,
        )

        assert "requires choices" in result
