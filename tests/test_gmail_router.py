"""Tests for Gmail tools backed by the Apps Script router."""

from unittest.mock import patch, AsyncMock

import pytest

from google_automation_mcp.tools.gmail_router import (
    search_gmail_messages,
    get_gmail_message,
    send_gmail_message,
    list_gmail_labels,
    modify_gmail_labels,
)


@pytest.fixture
def mock_call_router():
    with patch(
        "google_automation_mcp.tools.gmail_router.call_router",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.mark.asyncio
class TestGmailRouterTools:
    async def test_search_gmail_messages_success(self, mock_call_router):
        mock_call_router.return_value = [
            {
                "id": "thread1",
                "message_id": "msg1",
                "subject": "Test Subject",
                "from": "sender@example.com",
                "to": "me@example.com",
                "date": "2026-04-15T10:00:00.000Z",
                "snippet": "This is a test email",
                "labels": ["INBOX"],
                "unread": True,
                "message_count": 1,
            }
        ]

        result = await search_gmail_messages(
            user_google_email="test@example.com", query="test"
        )

        assert "Found 1 messages" in result
        assert "msg1" in result
        assert "Test Subject" in result
        assert "sender@example.com" in result
        mock_call_router.assert_called_once_with(
            "test@example.com",
            "search_gmail",
            {"query": "test", "max_results": 10},
        )

    async def test_search_gmail_messages_empty(self, mock_call_router):
        mock_call_router.return_value = []

        result = await search_gmail_messages(
            user_google_email="test@example.com", query="nonexistent"
        )

        assert "No messages found" in result

    async def test_get_gmail_message_success(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "msg1",
            "thread_id": "thread1",
            "subject": "Test Subject",
            "from": "sender@example.com",
            "to": "me@example.com",
            "cc": "",
            "bcc": "",
            "date": "2026-04-15T10:00:00.000Z",
            "body": "Hello, this is the email body.",
            "is_html": False,
            "starred": False,
            "unread": True,
            "attachments": [],
        }

        result = await get_gmail_message(
            user_google_email="test@example.com", message_id="msg1"
        )

        assert "msg1" in result
        assert "Test Subject" in result
        assert "Hello, this is the email body." in result
        mock_call_router.assert_called_once_with(
            "test@example.com",
            "get_gmail_message",
            {"message_id": "msg1"},
        )

    async def test_get_gmail_message_with_attachments(self, mock_call_router):
        mock_call_router.return_value = {
            "id": "msg2",
            "thread_id": "thread2",
            "subject": "With Attachment",
            "from": "sender@example.com",
            "to": "me@example.com",
            "cc": "cc@example.com",
            "bcc": "",
            "date": "2026-04-15T10:00:00.000Z",
            "body": "See attached.",
            "is_html": False,
            "starred": False,
            "unread": False,
            "attachments": [
                {"name": "doc.pdf", "type": "application/pdf", "size": 12345}
            ],
        }

        result = await get_gmail_message(
            user_google_email="test@example.com", message_id="msg2"
        )

        assert "Attachments: 1" in result
        assert "doc.pdf" in result

    async def test_send_gmail_message_success(self, mock_call_router):
        mock_call_router.return_value = {
            "sent": True,
            "to": "recipient@example.com",
            "subject": "Hello",
        }

        result = await send_gmail_message(
            user_google_email="test@example.com",
            to="recipient@example.com",
            subject="Hello",
            body="Hi there!",
        )

        assert "Message sent successfully" in result
        assert "recipient@example.com" in result
        mock_call_router.assert_called_once_with(
            "test@example.com",
            "send_gmail",
            {
                "to": "recipient@example.com",
                "subject": "Hello",
                "body": "Hi there!",
                "cc": None,
                "bcc": None,
                "html": False,
            },
        )

    async def test_list_gmail_labels_success(self, mock_call_router):
        mock_call_router.return_value = {
            "user_labels": [
                {"name": "Work"},
                {"name": "Personal"},
            ],
            "note": "System labels not available via Apps Script",
        }

        result = await list_gmail_labels(user_google_email="test@example.com")

        assert "Found 2 user labels" in result
        assert "Work" in result
        assert "Personal" in result
        assert "Note:" in result

    async def test_modify_gmail_labels_add(self, mock_call_router):
        mock_call_router.return_value = {
            "message_id": "msg1",
            "added": ["STARRED"],
            "removed": [],
        }

        result = await modify_gmail_labels(
            user_google_email="test@example.com",
            message_id="msg1",
            add_labels=["STARRED"],
        )

        assert "Modified message: msg1" in result
        assert "Added: STARRED" in result

    async def test_modify_gmail_labels_remove(self, mock_call_router):
        mock_call_router.return_value = {
            "message_id": "msg1",
            "added": [],
            "removed": ["UNREAD", "INBOX"],
        }

        result = await modify_gmail_labels(
            user_google_email="test@example.com",
            message_id="msg1",
            remove_labels=["UNREAD", "INBOX"],
        )

        assert "Removed: UNREAD, INBOX" in result

    async def test_modify_gmail_labels_no_changes(self, mock_call_router):
        result = await modify_gmail_labels(
            user_google_email="test@example.com",
            message_id="msg1",
        )

        assert "No labels to modify" in result
        mock_call_router.assert_not_called()
