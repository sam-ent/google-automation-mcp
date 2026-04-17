"""Tests for Forms tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.forms_router import (
    get_form,
    get_form_responses,
    create_form,
    add_form_question,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.forms_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestFormsRouterTools:
    async def test_get_form(self, mock_call_router):
        mock_call_router.return_value = {
            "form_id": "f1", "title": "Survey", "description": "A survey",
            "url": "https://...", "edit_url": "https://...",
            "items": [{"index": 1, "title": "Name?", "item_id": "q1", "type": "TEXT"}],
        }
        result = await get_form(user_google_email="t@t.com", form_id="f1")
        assert "Survey" in result
        assert "Name?" in result

    async def test_get_form_responses(self, mock_call_router):
        mock_call_router.return_value = [
            {"response_id": "r1", "timestamp": "2026-04-17T00:00:00Z",
             "answers": [{"question": "Name?", "answer": "Alice"}]},
        ]
        result = await get_form_responses(user_google_email="t@t.com", form_id="f1")
        assert "Found 1 responses" in result
        assert "Alice" in result

    async def test_get_form_responses_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await get_form_responses(user_google_email="t@t.com", form_id="f1")
        assert "No responses found" in result

    async def test_create_form(self, mock_call_router):
        mock_call_router.return_value = {
            "form_id": "f1", "title": "New Form",
            "url": "https://...", "edit_url": "https://...",
        }
        result = await create_form(user_google_email="t@t.com", title="New Form")
        assert "Created form: New Form" in result

    async def test_add_form_question_text(self, mock_call_router):
        mock_call_router.return_value = {"form_id": "f1", "title": "Email?", "type": "TEXT"}
        result = await add_form_question(
            user_google_email="t@t.com", form_id="f1", title="Email?",
        )
        assert "Added question 'Email?'" in result

    async def test_add_form_question_choice_missing(self, mock_call_router):
        result = await add_form_question(
            user_google_email="t@t.com", form_id="f1", title="Pick one",
            question_type="MULTIPLE_CHOICE",
        )
        assert "requires choices" in result
        mock_call_router.assert_not_called()

    async def test_add_form_question_choice(self, mock_call_router):
        mock_call_router.return_value = {
            "form_id": "f1", "title": "Color?", "type": "MULTIPLE_CHOICE",
        }
        result = await add_form_question(
            user_google_email="t@t.com", form_id="f1", title="Color?",
            question_type="MULTIPLE_CHOICE", choices="Red,Blue,Green",
        )
        assert "Added question 'Color?'" in result
