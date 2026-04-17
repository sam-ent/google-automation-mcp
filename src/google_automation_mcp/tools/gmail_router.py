"""
Gmail Tools — Apps Script Router Backend

Same interface as gmail.py but routes through the Apps Script Web App
instead of calling Gmail REST API directly. Works with clasp auth only,
no GCP project needed.
"""

import logging
from typing import Optional, List

from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def search_gmail_messages(
    user_google_email: str,
    query: str = "",
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
) -> str:
    logger.info(f"[search_gmail_messages] User: {user_google_email}, Query: '{query}'")

    results = await call_router(user_google_email, "search_gmail", {
        "query": query,
        "max_results": max_results,
    })

    if not results:
        return f"No messages found for query: '{query}'"

    output = [f"Found {len(results)} messages for '{query}':"]
    for msg in results:
        output.append(f"\n- ID: {msg['message_id']}")
        output.append(f"  From: {msg['from']}")
        output.append(f"  Subject: {msg['subject']}")
        output.append(f"  Date: {msg['date']}")
        output.append(f"  Preview: {msg.get('snippet', '')[:100]}...")
        if msg.get("labels"):
            output.append(f"  Labels: {', '.join(msg['labels'])}")

    return "\n".join(output)


@handle_errors
async def get_gmail_message(
    user_google_email: str,
    message_id: str,
    format: str = "full",
) -> str:
    logger.info(
        f"[get_gmail_message] User: {user_google_email}, Message ID: {message_id}"
    )

    msg = await call_router(user_google_email, "get_gmail_message", {
        "message_id": message_id,
    })

    output = [
        f"Message ID: {msg['id']}",
        f"From: {msg['from']}",
        f"To: {msg['to']}",
        f"Subject: {msg['subject']}",
        f"Date: {msg['date']}",
    ]
    if msg.get("cc"):
        output.append(f"CC: {msg['cc']}")
    if msg.get("attachments"):
        output.append(f"Attachments: {len(msg['attachments'])}")
        for att in msg["attachments"]:
            output.append(f"  - {att['name']} ({att['type']}, {att['size']} bytes)")

    output.append("")
    if msg.get("body"):
        output.append("--- Content ---")
        output.append(msg["body"][:5000])
        if len(msg.get("body", "")) > 5000:
            output.append("... (truncated)")

    return "\n".join(output)


@handle_errors
async def send_gmail_message(
    user_google_email: str,
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
) -> str:
    logger.info(
        f"[send_gmail_message] User: {user_google_email}, To: {to}, Subject: {subject}"
    )

    await call_router(user_google_email, "send_gmail", {
        "to": to,
        "subject": subject,
        "body": body,
        "cc": cc,
        "bcc": bcc,
        "html": html,
    })

    return f"Message sent successfully!\nTo: {to}\nSubject: {subject}"


@handle_errors
async def list_gmail_labels(
    user_google_email: str,
) -> str:
    logger.info(f"[list_gmail_labels] User: {user_google_email}")

    result = await call_router(user_google_email, "list_gmail_labels", {})

    user_labels = result.get("user_labels", [])
    note = result.get("note", "")

    output = [f"Found {len(user_labels)} user labels:"]

    if user_labels:
        output.append("\nUser Labels:")
        for label in sorted(user_labels, key=lambda x: x.get("name", "")):
            output.append(f"  - {label['name']}")

    if note:
        output.append(f"\nNote: {note}")

    return "\n".join(output)


@handle_errors
async def modify_gmail_labels(
    user_google_email: str,
    message_id: str,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
) -> str:
    logger.info(
        f"[modify_gmail_labels] User: {user_google_email}, Message: {message_id}"
    )

    if not add_labels and not remove_labels:
        return "No labels to modify. Provide add_labels or remove_labels."

    result = await call_router(user_google_email, "modify_gmail_labels", {
        "message_id": message_id,
        "add_labels": add_labels or [],
        "remove_labels": remove_labels or [],
    })

    output = [f"Modified message: {result['message_id']}"]
    if result.get("added"):
        output.append(f"Added: {', '.join(result['added'])}")
    if result.get("removed"):
        output.append(f"Removed: {', '.join(result['removed'])}")

    return "\n".join(output)
