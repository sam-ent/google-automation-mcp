"""
Unit tests for Gmail MCP tools

Tests all Gmail tools with mocked API responses.
"""

import pytest
import base64
from unittest.mock import MagicMock, patch

from google_automation_mcp.tools.gmail import (
    search_gmail_messages,
    get_gmail_message,
    send_gmail_message,
    list_gmail_labels,
    modify_gmail_labels,
)


@pytest.fixture
def mock_gmail_service():
    """Create a mock Gmail API service."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_get_service(mock_gmail_service):
    """Patch get_service_for_user to return the mock service."""
    with patch(
        "google_automation_mcp.auth.service_adapter.get_service_for_user",
        return_value=mock_gmail_service,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestGmailTools:
    """Tests for all Gmail tool functions."""

    async def test_search_gmail_messages_success(self, mock_gmail_service, mock_get_service):
        """Test searching for messages returns formatted output."""
        # Mock list response
        mock_gmail_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg123"}]
        }
        # Mock get response for details
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": "msg123",
            "snippet": "Test snippet content",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "Sender <sender@example.com>"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 10:00:00 +0000"},
                ]
            },
        }

        result = await search_gmail_messages(
            user_google_email="test@example.com", query="test query"
        )

        assert "Found 1 messages" in result
        assert "ID: msg123" in result
        assert "Subject: Test Subject" in result
        assert "Preview: Test snippet content" in result
        mock_gmail_service.users().messages().list.assert_called()

    async def test_search_gmail_messages_no_results(self, mock_gmail_service, mock_get_service):
        """Test search when no messages are found."""
        mock_gmail_service.users().messages().list().execute.return_value = {}

        result = await search_gmail_messages(
            user_google_email="test@example.com", query="empty query"
        )

        assert "No messages found" in result

    async def test_get_gmail_message_full(self, mock_gmail_service, mock_get_service):
        """Test getting a specific message by ID."""
        body_text = "This is the message body."
        encoded_body = base64.urlsafe_b64encode(body_text.encode("utf-8")).decode(
            "utf-8"
        )

        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Hello"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024"},
                ],
                "body": {"data": encoded_body},
            },
        }

        result = await get_gmail_message(
            user_google_email="test@example.com", message_id="msg123"
        )

        assert "Message ID: msg123" in result
        assert "Subject: Hello" in result
        assert "--- Content ---" in result
        assert body_text in result

    async def test_get_gmail_message_multipart(self, mock_gmail_service, mock_get_service):
        """Test getting a multipart message (e.g. text/plain + text/html)."""
        plain_text = "Plain text body"
        encoded_plain = base64.urlsafe_b64encode(plain_text.encode("utf-8")).decode(
            "utf-8"
        )

        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": "msg123",
            "payload": {
                "headers": [],
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": encoded_plain}},
                    {
                        "mimeType": "text/html",
                        "body": {"data": "PGgxPkhUTUw8L2gxPg=="},
                    },
                ],
            },
        }

        result = await get_gmail_message(
            user_google_email="test@example.com", message_id="msg123"
        )

        assert plain_text in result

    async def test_send_gmail_message_success(self, mock_gmail_service, mock_get_service):
        """Test sending a plain text email."""
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "sent123"
        }

        result = await send_gmail_message(
            user_google_email="test@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
        )

        assert "Message sent successfully!" in result
        assert "Message ID: sent123" in result
        mock_gmail_service.users().messages().send.assert_called()

    async def test_send_gmail_message_html(self, mock_gmail_service, mock_get_service):
        """Test sending an HTML email."""
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "html123"
        }

        result = await send_gmail_message(
            user_google_email="test@example.com",
            to="recipient@example.com",
            subject="HTML Subject",
            body="<h1>Hello</h1>",
            html=True,
        )

        assert "Message sent successfully!" in result
        mock_gmail_service.users().messages().send.assert_called()

    async def test_list_gmail_labels(self, mock_gmail_service, mock_get_service):
        """Test listing Gmail labels."""
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "SENT", "name": "SENT", "type": "system"},
                {"id": "label_work", "name": "Work", "type": "user"},
            ]
        }

        result = await list_gmail_labels(user_google_email="test@example.com")

        assert "Found 3 labels" in result
        assert "System Labels:" in result
        assert "- INBOX" in result
        assert "User Labels:" in result
        assert "- Work" in result

    async def test_modify_gmail_labels_success(self, mock_gmail_service, mock_get_service):
        """Test adding and removing labels from a message."""
        mock_gmail_service.users().messages().modify().execute.return_value = {
            "id": "msg123",
            "labelIds": ["STARRED", "IMPORTANT"],
        }

        result = await modify_gmail_labels(
            user_google_email="test@example.com",
            message_id="msg123",
            add_labels=["STARRED"],
            remove_labels=["UNREAD"],
        )

        assert "Modified message: msg123" in result
        assert "Added: STARRED" in result
        assert "Removed: UNREAD" in result
        assert "Current labels: STARRED, IMPORTANT" in result

        mock_gmail_service.users().messages().modify.assert_called_with(
            userId="me",
            id="msg123",
            body={"addLabelIds": ["STARRED"], "removeLabelIds": ["UNREAD"]},
        )

    async def test_modify_gmail_labels_none(self, mock_gmail_service, mock_get_service):
        """Test calling modify labels without providing any labels."""
        result = await modify_gmail_labels(
            user_google_email="test@example.com", message_id="msg123"
        )

        assert "No labels to modify" in result
