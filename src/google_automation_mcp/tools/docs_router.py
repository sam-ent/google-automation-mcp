"""Docs tools — Apps Script Router backend."""

import logging
from typing import Optional

from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def search_docs(
    user_google_email: str, query: str, page_size: int = 10,
) -> str:
    logger.info(f"[search_docs] User: {user_google_email}, Query: '{query}'")
    results = await call_router(user_google_email, "search_docs", {
        "query": query, "page_size": page_size,
    })
    if not results:
        return f"No Google Docs found matching '{query}'."
    output = [f"Found {len(results)} Google Docs matching '{query}':"]
    for doc in results:
        output.append(
            f"- {doc['name']} (ID: {doc['id']})\n"
            f"  Modified: {doc.get('modified', 'N/A')}\n"
            f"  Link: {doc.get('url', '#')}"
        )
    return "\n".join(output)


@handle_errors
async def get_doc_content(user_google_email: str, document_id: str) -> str:
    logger.info(f"[get_doc_content] User: {user_google_email}, Doc: {document_id}")
    result = await call_router(user_google_email, "get_doc_content", {
        "document_id": document_id,
    })
    link = result.get("url", f"https://docs.google.com/document/d/{document_id}/edit")
    header = f"Document: {result.get('title', 'Untitled')}\nID: {document_id}\nLink: {link}\n\n--- CONTENT ---\n"
    return header + result.get("content", "")


@handle_errors
async def create_doc(
    user_google_email: str, title: str, content: str = "",
) -> str:
    logger.info(f"[create_doc] User: {user_google_email}, Title: {title}")
    result = await call_router(user_google_email, "create_doc", {
        "title": title, "content": content,
    })
    link = result.get("url", f"https://docs.google.com/document/d/{result['document_id']}/edit")
    return f"Created Google Doc: {title}\nID: {result['document_id']}\nLink: {link}"


@handle_errors
async def modify_doc_text(
    user_google_email: str, document_id: str, text: str,
    index: int = 1, replace_text: Optional[str] = None,
) -> str:
    logger.info(f"[modify_doc_text] User: {user_google_email}, Doc: {document_id}")
    result = await call_router(user_google_email, "modify_doc_text", {
        "document_id": document_id, "text": text,
        "index": index, "replace_text": replace_text,
    })
    link = result.get("url", f"https://docs.google.com/document/d/{document_id}/edit")
    if replace_text:
        return f"Replaced text in document\nDocument: {document_id}\nLink: {link}"
    return f"Inserted text at index {index}\nDocument: {document_id}\nLink: {link}"


@handle_errors
async def append_doc_text(
    user_google_email: str, document_id: str, text: str,
) -> str:
    logger.info(f"[append_doc_text] User: {user_google_email}, Doc: {document_id}")
    result = await call_router(user_google_email, "append_doc_text", {
        "document_id": document_id, "text": text,
    })
    link = result.get("url", f"https://docs.google.com/document/d/{document_id}/edit")
    return f"Appended text to document\nDocument: {document_id}\nLink: {link}"
