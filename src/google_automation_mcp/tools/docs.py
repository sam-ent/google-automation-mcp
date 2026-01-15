"""
Google Docs MCP Tools

Provides tools for searching, reading, and modifying Google Docs.

Adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Original: gdocs/docs_tools.py
Licensed under MIT License.
"""

import asyncio
import logging
from typing import Optional

from googleapiclient.errors import HttpError

from ..auth.service_adapter import with_docs_service, with_drive_service

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
@with_drive_service
async def search_docs(
    service,
    user_google_email: str,
    query: str,
    page_size: int = 10,
) -> str:
    """
    Search for Google Docs by name.

    Args:
        user_google_email: The user's Google email address
        query: Search query string
        page_size: Maximum number of docs to return (default: 10)

    Returns:
        str: Formatted list of matching documents
    """
    logger.info(f"[search_docs] User: {user_google_email}, Query: '{query}'")

    escaped_query = query.replace("'", "\\'")
    final_query = f"name contains '{escaped_query}' and mimeType='application/vnd.google-apps.document' and trashed=false"

    results = await asyncio.to_thread(
        service.files()
        .list(
            q=final_query,
            pageSize=page_size,
            fields="files(id, name, createdTime, modifiedTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute
    )

    files = results.get("files", [])
    if not files:
        return f"No Google Docs found matching '{query}'."

    output = [f"Found {len(files)} Google Docs matching '{query}':"]
    for doc in files:
        output.append(
            f"- {doc['name']} (ID: {doc['id']})\n"
            f"  Modified: {doc.get('modifiedTime', 'N/A')}\n"
            f"  Link: {doc.get('webViewLink', '#')}"
        )

    return "\n".join(output)


@_handle_errors
@with_docs_service
async def get_doc_content(
    service,
    user_google_email: str,
    document_id: str,
) -> str:
    """
    Get the content of a Google Doc.

    Args:
        user_google_email: The user's Google email address
        document_id: The document ID

    Returns:
        str: Document content with metadata header
    """
    logger.info(f"[get_doc_content] User: {user_google_email}, Doc: {document_id}")

    doc = await asyncio.to_thread(
        service.documents().get(documentId=document_id).execute
    )

    title = doc.get("title", "Untitled")

    # Extract text from document body
    body = doc.get("body", {})
    content = body.get("content", [])

    text_parts = []

    def extract_text(elements):
        """Recursively extract text from document elements."""
        for element in elements:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for elem in paragraph.get("elements", []):
                    text_run = elem.get("textRun", {})
                    if text_run and "content" in text_run:
                        text_parts.append(text_run["content"])
            elif "table" in element:
                table = element["table"]
                for row in table.get("tableRows", []):
                    for cell in row.get("tableCells", []):
                        extract_text(cell.get("content", []))

    extract_text(content)

    body_text = "".join(text_parts)

    link = f"https://docs.google.com/document/d/{document_id}/edit"
    header = f"Document: {title}\nID: {document_id}\nLink: {link}\n\n--- CONTENT ---\n"

    return header + body_text


@_handle_errors
@with_docs_service
async def create_doc(
    service,
    user_google_email: str,
    title: str,
    content: str = "",
) -> str:
    """
    Create a new Google Doc.

    Args:
        user_google_email: The user's Google email address
        title: Document title
        content: Optional initial content

    Returns:
        str: Confirmation with document details
    """
    logger.info(f"[create_doc] User: {user_google_email}, Title: {title}")

    doc = await asyncio.to_thread(
        service.documents().create(body={"title": title}).execute
    )

    document_id = doc.get("documentId")

    # Insert content if provided
    if content:
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": content,
                }
            }
        ]
        await asyncio.to_thread(
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute
        )

    link = f"https://docs.google.com/document/d/{document_id}/edit"

    return f"Created Google Doc: {title}\nID: {document_id}\nLink: {link}"


@_handle_errors
@with_docs_service
async def modify_doc_text(
    service,
    user_google_email: str,
    document_id: str,
    text: str,
    index: int = 1,
    replace_text: Optional[str] = None,
) -> str:
    """
    Modify text in a Google Doc.

    Args:
        user_google_email: The user's Google email address
        document_id: The document ID
        text: Text to insert (or replace with)
        index: Position to insert text (default: 1, start of document)
        replace_text: If provided, find and replace this text with 'text'

    Returns:
        str: Confirmation with document link
    """
    logger.info(f"[modify_doc_text] User: {user_google_email}, Doc: {document_id}")

    requests = []

    if replace_text:
        # Find and replace
        requests.append(
            {
                "replaceAllText": {
                    "containsText": {
                        "text": replace_text,
                        "matchCase": False,
                    },
                    "replaceText": text,
                }
            }
        )
    else:
        # Insert at position
        actual_index = max(1, index)  # Can't insert at 0
        requests.append(
            {
                "insertText": {
                    "location": {"index": actual_index},
                    "text": text,
                }
            }
        )

    result = await asyncio.to_thread(
        service.documents()
        .batchUpdate(documentId=document_id, body={"requests": requests})
        .execute
    )

    link = f"https://docs.google.com/document/d/{document_id}/edit"

    if replace_text:
        # Check number of replacements
        replies = result.get("replies", [])
        replacements = 0
        if replies:
            replacements = (
                replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
            )
        return (
            f"Replaced {replacements} occurrence(s) of '{replace_text}' with '{text}'\n"
            f"Document: {document_id}\n"
            f"Link: {link}"
        )
    else:
        return f"Inserted text at index {index}\nDocument: {document_id}\nLink: {link}"


@_handle_errors
@with_docs_service
async def append_doc_text(
    service,
    user_google_email: str,
    document_id: str,
    text: str,
) -> str:
    """
    Append text to the end of a Google Doc.

    Args:
        user_google_email: The user's Google email address
        document_id: The document ID
        text: Text to append to the end of the document

    Returns:
        str: Confirmation with document link
    """
    logger.info(f"[append_doc_text] User: {user_google_email}, Doc: {document_id}")

    # First get the document to find the end index
    doc = await asyncio.to_thread(
        service.documents().get(documentId=document_id).execute
    )

    # Get the end index of the document body
    body = doc.get("body", {})
    content = body.get("content", [])

    # Find the last content element's end index
    end_index = 1
    if content:
        last_element = content[-1]
        end_index = (
            last_element.get("endIndex", 1) - 1
        )  # -1 to insert before final newline

    # Insert at the end
    requests = [
        {
            "insertText": {
                "location": {"index": end_index},
                "text": text,
            }
        }
    ]

    await asyncio.to_thread(
        service.documents()
        .batchUpdate(documentId=document_id, body={"requests": requests})
        .execute
    )

    link = f"https://docs.google.com/document/d/{document_id}/edit"

    return f"Appended text to document\nDocument: {document_id}\nLink: {link}"
