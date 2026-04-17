"""Tests for Docs tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.docs_router import (
    search_docs,
    get_doc_content,
    create_doc,
    modify_doc_text,
    append_doc_text,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.docs_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestDocsRouterTools:
    async def test_search_docs(self, mock_call_router):
        mock_call_router.return_value = [
            {"id": "d1", "name": "My Doc", "modified": "2026-04-17", "url": "https://..."}
        ]
        result = await search_docs(user_google_email="t@t.com", query="My")
        assert "Found 1 Google Docs" in result
        assert "My Doc" in result

    async def test_search_docs_empty(self, mock_call_router):
        mock_call_router.return_value = []
        result = await search_docs(user_google_email="t@t.com", query="nope")
        assert "No Google Docs found" in result

    async def test_get_doc_content(self, mock_call_router):
        mock_call_router.return_value = {
            "document_id": "d1", "title": "My Doc",
            "content": "Hello world", "url": "https://...",
        }
        result = await get_doc_content(user_google_email="t@t.com", document_id="d1")
        assert "My Doc" in result
        assert "Hello world" in result

    async def test_create_doc(self, mock_call_router):
        mock_call_router.return_value = {
            "document_id": "d1", "title": "New Doc", "url": "https://...",
        }
        result = await create_doc(user_google_email="t@t.com", title="New Doc")
        assert "Created Google Doc: New Doc" in result

    async def test_modify_doc_text_replace(self, mock_call_router):
        mock_call_router.return_value = {
            "document_id": "d1", "action": "replace", "url": "https://...",
        }
        result = await modify_doc_text(
            user_google_email="t@t.com", document_id="d1",
            text="new", replace_text="old",
        )
        assert "Replaced text" in result

    async def test_modify_doc_text_insert(self, mock_call_router):
        mock_call_router.return_value = {
            "document_id": "d1", "action": "insert", "index": 1, "url": "https://...",
        }
        result = await modify_doc_text(
            user_google_email="t@t.com", document_id="d1", text="inserted",
        )
        assert "Inserted text at index 1" in result

    async def test_append_doc_text(self, mock_call_router):
        mock_call_router.return_value = {
            "document_id": "d1", "url": "https://...",
        }
        result = await append_doc_text(
            user_google_email="t@t.com", document_id="d1", text="appended",
        )
        assert "Appended text to document" in result
