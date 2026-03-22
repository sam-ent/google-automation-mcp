"""
Unit tests for Google Docs MCP tools

Tests all Docs tools with mocked API responses.
"""

import pytest
from unittest.mock import MagicMock, patch

from google_automation_mcp.tools.docs import (
    search_docs,
    get_doc_content,
    create_doc,
    modify_doc_text,
    append_doc_text,
)


@pytest.fixture
def mock_service():
    """Mock Google API service."""
    return MagicMock()


@pytest.fixture
def mock_get_service(mock_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_service,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestGoogleDocsTools:
    """Tests for Google Docs MCP tools."""

    user_email = "test@example.com"
    doc_id = "test_doc_id"

    async def test_search_docs_success(self, mock_service, mock_get_service):
        mock_response = {
            "files": [
                {
                    "id": "doc123",
                    "name": "Test Document",
                    "modifiedTime": "2026-03-22T12:00:00Z",
                    "webViewLink": "https://docs.google.com/doc123",
                }
            ]
        }
        mock_service.files().list().execute.return_value = mock_response

        result = await search_docs(
            user_google_email=self.user_email, query="test query", page_size=5
        )

        assert "Found 1 Google Docs matching 'test query':" in result
        assert "Test Document (ID: doc123)" in result
        assert "Modified: 2026-03-22T12:00:00Z" in result
        assert "Link: https://docs.google.com/doc123" in result

        args, kwargs = mock_service.files().list.call_args
        assert "name contains 'test query'" in kwargs["q"]
        assert kwargs["pageSize"] == 5

    async def test_search_docs_empty(self, mock_service, mock_get_service):
        mock_service.files().list().execute.return_value = {"files": []}

        result = await search_docs(
            user_google_email=self.user_email, query="nothing"
        )

        assert "No Google Docs found matching 'nothing'." in result

    async def test_get_doc_content(self, mock_service, mock_get_service):
        mock_doc = {
            "title": "Document Title",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Hello "}},
                                {"textRun": {"content": "World!"}},
                            ]
                        }
                    },
                    {
                        "table": {
                            "tableRows": [
                                {
                                    "tableCells": [
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "elements": [
                                                            {
                                                                "textRun": {
                                                                    "content": "Table cell"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                ]
            },
        }
        mock_service.documents().get().execute.return_value = mock_doc

        result = await get_doc_content(
            user_google_email=self.user_email, document_id=self.doc_id
        )

        assert "Document: Document Title" in result
        assert "ID: test_doc_id" in result
        assert "Hello World!" in result
        assert "Table cell" in result
        mock_service.documents().get.assert_called_with(documentId=self.doc_id)

    async def test_create_doc_with_content(self, mock_service, mock_get_service):
        mock_service.documents().create().execute.return_value = {
            "documentId": "new_id"
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = await create_doc(
            user_google_email=self.user_email,
            title="My New Doc",
            content="Initial content",
        )

        assert "Created Google Doc: My New Doc" in result
        assert "ID: new_id" in result
        mock_service.documents().create.assert_called_with(
            body={"title": "My New Doc"}
        )
        mock_service.documents().batchUpdate.assert_called()

        args, kwargs = mock_service.documents().batchUpdate.call_args
        assert kwargs["documentId"] == "new_id"
        assert (
            kwargs["body"]["requests"][0]["insertText"]["text"] == "Initial content"
        )

    async def test_modify_doc_text_insert(self, mock_service, mock_get_service):
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = await modify_doc_text(
            user_google_email=self.user_email,
            document_id=self.doc_id,
            text="New Text",
            index=5,
        )

        assert "Inserted text at index 5" in result
        mock_service.documents().batchUpdate.assert_called()
        args, kwargs = mock_service.documents().batchUpdate.call_args
        assert (
            kwargs["body"]["requests"][0]["insertText"]["location"]["index"] == 5
        )

    async def test_modify_doc_text_replace(self, mock_service, mock_get_service):
        mock_service.documents().batchUpdate().execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 3}}]
        }

        result = await modify_doc_text(
            user_google_email=self.user_email,
            document_id=self.doc_id,
            text="new",
            replace_text="old",
        )

        assert "Replaced 3 occurrence(s) of 'old' with 'new'" in result
        mock_service.documents().batchUpdate.assert_called()
        args, kwargs = mock_service.documents().batchUpdate.call_args
        req = kwargs["body"]["requests"][0]["replaceAllText"]
        assert req["replaceText"] == "new"
        assert req["containsText"]["text"] == "old"

    async def test_append_doc_text(self, mock_service, mock_get_service):
        mock_service.documents().get().execute.return_value = {
            "body": {"content": [{"endIndex": 100}]}
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = await append_doc_text(
            user_google_email=self.user_email,
            document_id=self.doc_id,
            text="Appending this",
        )

        assert "Appended text to document" in result
        mock_service.documents().get.assert_called_with(documentId=self.doc_id)
        mock_service.documents().batchUpdate.assert_called()
        args, kwargs = mock_service.documents().batchUpdate.call_args
        # endIndex 100 -> index 99
        assert (
            kwargs["body"]["requests"][0]["insertText"]["location"]["index"] == 99
        )
