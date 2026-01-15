"""
Gmail MCP Tools

Provides tools for searching, reading, and sending Gmail messages.

Adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Original: gmail/gmail_tools.py
Licensed under MIT License.
"""

import asyncio
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

from googleapiclient.errors import HttpError

from ..auth.service_adapter import with_gmail_service

logger = logging.getLogger(__name__)


def _handle_errors(func):
    """Decorator to handle API errors gracefully."""
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HttpError as e:
            error_msg = str(e)
            if e.resp.status == 401:
                return f"Authentication error: {error_msg}\n\nPlease run start_google_auth to authenticate."
            elif e.resp.status == 403:
                return f"Permission denied: {error_msg}"
            elif e.resp.status == 404:
                return f"Not found: {error_msg}"
            else:
                return f"API error: {error_msg}"
        except Exception as e:
            if "No valid credentials" in str(e):
                return str(e)
            logger.exception(f"Error in {func.__name__}")
            return f"Error: {str(e)}"

    return wrapper


@_handle_errors
@with_gmail_service
async def search_gmail_messages(
    service,
    user_google_email: str,
    query: str = "",
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
) -> str:
    """
    Search for Gmail messages matching a query.

    Args:
        user_google_email: The user's Google email address
        query: Gmail search query (e.g., "from:user@example.com subject:hello")
        max_results: Maximum number of messages to return (default: 10)
        label_ids: Optional list of label IDs to filter by

    Returns:
        str: Formatted list of matching messages
    """
    logger.info(f"[search_gmail_messages] User: {user_google_email}, Query: '{query}'")

    request_params = {
        "userId": "me",
        "maxResults": max_results,
    }
    if query:
        request_params["q"] = query
    if label_ids:
        request_params["labelIds"] = label_ids

    response = await asyncio.to_thread(
        service.users().messages().list(**request_params).execute
    )

    messages = response.get("messages", [])
    if not messages:
        return f"No messages found for query: '{query}'"

    output = [f"Found {len(messages)} messages for '{query}':"]

    # Get details for each message
    for msg in messages[:max_results]:
        msg_detail = await asyncio.to_thread(
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute
        )

        headers = {
            h["name"]: h["value"]
            for h in msg_detail.get("payload", {}).get("headers", [])
        }
        subject = headers.get("Subject", "(No Subject)")
        sender = headers.get("From", "Unknown")
        date = headers.get("Date", "Unknown")
        snippet = msg_detail.get("snippet", "")[:100]

        output.append(f"\n- ID: {msg['id']}")
        output.append(f"  From: {sender}")
        output.append(f"  Subject: {subject}")
        output.append(f"  Date: {date}")
        output.append(f"  Preview: {snippet}...")

    return "\n".join(output)


@_handle_errors
@with_gmail_service
async def get_gmail_message(
    service,
    user_google_email: str,
    message_id: str,
    format: str = "full",
) -> str:
    """
    Get a specific Gmail message by ID.

    Args:
        user_google_email: The user's Google email address
        message_id: The message ID to retrieve
        format: Message format - "full", "metadata", or "minimal"

    Returns:
        str: Formatted message content
    """
    logger.info(
        f"[get_gmail_message] User: {user_google_email}, Message ID: {message_id}"
    )

    msg = await asyncio.to_thread(
        service.users()
        .messages()
        .get(userId="me", id=message_id, format=format)
        .execute
    )

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    subject = headers.get("Subject", "(No Subject)")
    sender = headers.get("From", "Unknown")
    to = headers.get("To", "Unknown")
    date = headers.get("Date", "Unknown")

    output = [
        f"Message ID: {message_id}",
        f"From: {sender}",
        f"To: {to}",
        f"Subject: {subject}",
        f"Date: {date}",
        "",
    ]

    # Extract body
    body = ""
    payload = msg.get("payload", {})

    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    elif "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get(
                "data"
            ):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                break
            elif (
                part.get("mimeType") == "text/html"
                and part.get("body", {}).get("data")
                and not body
            ):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

    if body:
        output.append("--- Content ---")
        output.append(body[:5000])  # Limit body length
        if len(body) > 5000:
            output.append("... (truncated)")

    return "\n".join(output)


@_handle_errors
@with_gmail_service
async def send_gmail_message(
    service,
    user_google_email: str,
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
) -> str:
    """
    Send a Gmail message.

    Args:
        user_google_email: The user's Google email address
        to: Recipient email address(es), comma-separated
        subject: Email subject
        body: Email body content
        cc: Optional CC recipients, comma-separated
        bcc: Optional BCC recipients, comma-separated
        html: If True, body is treated as HTML

    Returns:
        str: Confirmation with sent message ID
    """
    logger.info(
        f"[send_gmail_message] User: {user_google_email}, To: {to}, Subject: {subject}"
    )

    if html:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body, "html"))
    else:
        message = MIMEText(body)

    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    sent_message = await asyncio.to_thread(
        service.users().messages().send(userId="me", body={"raw": raw}).execute
    )

    return f"Message sent successfully!\nMessage ID: {sent_message.get('id')}\nTo: {to}\nSubject: {subject}"


@_handle_errors
@with_gmail_service
async def list_gmail_labels(
    service,
    user_google_email: str,
) -> str:
    """
    List all Gmail labels for the user.

    Args:
        user_google_email: The user's Google email address

    Returns:
        str: Formatted list of labels
    """
    logger.info(f"[list_gmail_labels] User: {user_google_email}")

    response = await asyncio.to_thread(
        service.users().labels().list(userId="me").execute
    )

    labels = response.get("labels", [])
    if not labels:
        return "No labels found."

    output = [f"Found {len(labels)} labels:"]

    # Separate system and user labels
    system_labels = []
    user_labels = []

    for label in labels:
        label_type = label.get("type", "user")
        if label_type == "system":
            system_labels.append(label)
        else:
            user_labels.append(label)

    if system_labels:
        output.append("\nSystem Labels:")
        for label in sorted(system_labels, key=lambda x: x.get("name", "")):
            output.append(f"  - {label.get('name')} (ID: {label.get('id')})")

    if user_labels:
        output.append("\nUser Labels:")
        for label in sorted(user_labels, key=lambda x: x.get("name", "")):
            output.append(f"  - {label.get('name')} (ID: {label.get('id')})")

    return "\n".join(output)


@_handle_errors
@with_gmail_service
async def modify_gmail_labels(
    service,
    user_google_email: str,
    message_id: str,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
) -> str:
    """
    Modify labels on a Gmail message.

    Common label IDs:
    - INBOX - Message in inbox
    - UNREAD - Message is unread
    - STARRED - Message is starred
    - TRASH - Message in trash
    - SPAM - Message in spam
    - IMPORTANT - Message marked important

    Args:
        user_google_email: The user's Google email address
        message_id: The message ID to modify
        add_labels: List of label IDs to add (e.g., ["STARRED", "IMPORTANT"])
        remove_labels: List of label IDs to remove (e.g., ["UNREAD", "INBOX"])

    Returns:
        str: Confirmation with updated labels

    Examples:
        - Archive: remove_labels=["INBOX"]
        - Mark read: remove_labels=["UNREAD"]
        - Mark unread: add_labels=["UNREAD"]
        - Star: add_labels=["STARRED"]
        - Move to trash: add_labels=["TRASH"]
    """
    logger.info(
        f"[modify_gmail_labels] User: {user_google_email}, Message: {message_id}"
    )

    body = {}
    if add_labels:
        body["addLabelIds"] = add_labels
    if remove_labels:
        body["removeLabelIds"] = remove_labels

    if not body:
        return "No labels to modify. Provide add_labels or remove_labels."

    result = await asyncio.to_thread(
        service.users().messages().modify(userId="me", id=message_id, body=body).execute
    )

    current_labels = result.get("labelIds", [])

    output = [
        f"Modified message: {message_id}",
    ]
    if add_labels:
        output.append(f"Added: {', '.join(add_labels)}")
    if remove_labels:
        output.append(f"Removed: {', '.join(remove_labels)}")
    output.append(f"Current labels: {', '.join(current_labels)}")

    return "\n".join(output)
