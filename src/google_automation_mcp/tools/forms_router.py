"""Forms tools — Apps Script Router backend."""

import logging
from typing import Optional

from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def get_form(user_google_email: str, form_id: str) -> str:
    logger.info(f"[get_form] User: {user_google_email}, Form: {form_id}")
    result = await call_router(user_google_email, "get_form", {"form_id": form_id})
    output = [
        f"Form: {result.get('title', 'Untitled')}",
        f"ID: {result.get('form_id')}",
        f"URL: {result.get('url', 'N/A')}",
    ]
    if result.get("description"):
        output.append(f"Description: {result['description']}")
    items = result.get("items", [])
    if items:
        output.append(f"\nQuestions ({len(items)}):")
        for item in items:
            output.append(f"  {item['index']}. {item['title']} [{item.get('type', '')}] (ID: {item.get('item_id', '')})")
    return "\n".join(output)


@handle_errors
async def get_form_responses(
    user_google_email: str, form_id: str, max_results: int = 50,
) -> str:
    logger.info(f"[get_form_responses] User: {user_google_email}, Form: {form_id}")
    results = await call_router(user_google_email, "get_form_responses", {
        "form_id": form_id, "max_results": max_results,
    })
    if not results:
        return f"No responses found for form '{form_id}'."
    output = [f"Found {len(results)} responses:"]
    for resp in results:
        output.append(f"\n--- Response {resp.get('response_id', '')} (submitted: {resp.get('timestamp', '')}) ---")
        for ans in resp.get("answers", []):
            output.append(f"  {ans.get('question', '?')}: {ans.get('answer', '')}")
    return "\n".join(output)


@handle_errors
async def create_form(
    user_google_email: str, title: str, description: Optional[str] = None,
) -> str:
    logger.info(f"[create_form] User: {user_google_email}, Title: {title}")
    result = await call_router(user_google_email, "create_form", {
        "title": title, "description": description,
    })
    return (
        f"Created form: {result.get('title', title)}\n"
        f"ID: {result.get('form_id')}\n"
        f"Edit URL: {result.get('edit_url', 'N/A')}\n"
        f"Response URL: {result.get('url', 'N/A')}"
    )


@handle_errors
async def add_form_question(
    user_google_email: str, form_id: str, title: str,
    question_type: str = "TEXT", required: bool = False,
    choices: Optional[str] = None,
) -> str:
    logger.info(f"[add_form_question] User: {user_google_email}, Form: {form_id}")
    if question_type in ("MULTIPLE_CHOICE", "CHECKBOX", "DROP_DOWN") and not choices:
        return f"Question type '{question_type}' requires choices. Provide comma-separated options."
    result = await call_router(user_google_email, "add_form_question", {
        "form_id": form_id, "title": title,
        "question_type": question_type, "required": required, "choices": choices,
    })
    return f"Added question '{title}' ({result.get('type', question_type)}) to form {form_id}"
