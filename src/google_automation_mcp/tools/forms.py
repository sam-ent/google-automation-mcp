"""
Google Forms MCP Tools

Provides tools for creating forms, managing questions, and retrieving responses.
"""

import asyncio
import logging
from typing import Optional

from ..auth.service_adapter import with_forms_service
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
@with_forms_service
async def get_form(
    service,
    user_google_email: str,
    form_id: str,
) -> str:
    """
    Get a Google Form's structure and questions.

    Args:
        user_google_email: The user's Google email address
        form_id: The form ID

    Returns:
        str: Formatted form details and questions
    """
    logger.info(f"[get_form] User: {user_google_email}, Form: {form_id}")

    form = await asyncio.to_thread(service.forms().get(formId=form_id).execute)

    info = form.get("info", {})
    output = [
        f"Form: {info.get('title', 'Untitled')}",
        f"ID: {form.get('formId')}",
        f"URL: {form.get('responderUri', 'N/A')}",
    ]

    if info.get("description"):
        output.append(f"Description: {info['description']}")

    items = form.get("items", [])
    if items:
        output.append(f"\nQuestions ({len(items)}):")
        for i, item in enumerate(items, 1):
            title = item.get("title", "(No title)")
            item_id = item.get("itemId", "")
            q = item.get("questionItem", {}).get("question", {})
            required = "required" if q.get("required") else "optional"
            output.append(f"  {i}. {title} [{required}] (ID: {item_id})")

    return "\n".join(output)


@handle_errors
@with_forms_service
async def get_form_responses(
    service,
    user_google_email: str,
    form_id: str,
    max_results: int = 50,
) -> str:
    """
    Get responses submitted to a Google Form.

    Args:
        user_google_email: The user's Google email address
        form_id: The form ID
        max_results: Maximum number of responses to return (default: 50)

    Returns:
        str: Formatted list of form responses
    """
    logger.info(f"[get_form_responses] User: {user_google_email}, Form: {form_id}")

    response = await asyncio.to_thread(
        service.forms()
        .responses()
        .list(formId=form_id, pageSize=max_results)
        .execute
    )

    responses = response.get("responses", [])
    if not responses:
        return f"No responses found for form '{form_id}'."

    output = [f"Found {len(responses)} responses:"]
    for resp in responses:
        resp_id = resp.get("responseId", "Unknown")
        submitted = resp.get("lastSubmittedTime", "Unknown")
        answers = resp.get("answers", {})

        output.append(f"\n--- Response {resp_id} (submitted: {submitted}) ---")
        for question_id, answer_data in answers.items():
            text_answers = answer_data.get("textAnswers", {}).get("answers", [])
            values = [a.get("value", "") for a in text_answers]
            output.append(f"  Q({question_id}): {', '.join(values)}")

    return "\n".join(output)


@handle_errors
@with_forms_service
async def create_form(
    service,
    user_google_email: str,
    title: str,
    description: Optional[str] = None,
) -> str:
    """
    Create a new Google Form.

    Args:
        user_google_email: The user's Google email address
        title: Form title
        description: Optional form description

    Returns:
        str: Confirmation with form details and URL
    """
    logger.info(f"[create_form] User: {user_google_email}, Title: {title}")

    body = {"info": {"title": title}}
    if description:
        body["info"]["description"] = description

    form = await asyncio.to_thread(service.forms().create(body=body).execute)

    output = [
        f"Created form: {form.get('info', {}).get('title')}",
        f"ID: {form.get('formId')}",
        f"Edit URL: https://docs.google.com/forms/d/{form.get('formId')}/edit",
        f"Response URL: {form.get('responderUri', 'N/A')}",
    ]

    return "\n".join(output)


@handle_errors
@with_forms_service
async def add_form_question(
    service,
    user_google_email: str,
    form_id: str,
    title: str,
    question_type: str = "TEXT",
    required: bool = False,
    choices: Optional[str] = None,
) -> str:
    """
    Add a question to a Google Form.

    Args:
        user_google_email: The user's Google email address
        form_id: The form ID
        title: Question text
        question_type: Type - "TEXT", "PARAGRAPH", "MULTIPLE_CHOICE",
                       "CHECKBOX", "DROP_DOWN", "SCALE" (default: "TEXT")
        required: Whether the question is required (default: False)
        choices: Comma-separated list of choices (for MULTIPLE_CHOICE,
                 CHECKBOX, DROP_DOWN types)

    Returns:
        str: Confirmation message
    """
    logger.info(f"[add_form_question] User: {user_google_email}, Form: {form_id}")

    question = {"required": required}

    if question_type in ("MULTIPLE_CHOICE", "CHECKBOX", "DROP_DOWN"):
        if not choices:
            return (
                f"Question type '{question_type}' requires choices. "
                "Provide comma-separated options."
            )
        option_list = [{"value": c.strip()} for c in choices.split(",")]
        choice_type = {
            "MULTIPLE_CHOICE": "RADIO",
            "CHECKBOX": "CHECKBOX",
            "DROP_DOWN": "DROP_DOWN",
        }[question_type]
        question["choiceQuestion"] = {
            "type": choice_type,
            "options": option_list,
        }
    elif question_type == "PARAGRAPH":
        question["textQuestion"] = {"paragraph": True}
    elif question_type == "SCALE":
        question["scaleQuestion"] = {"low": 1, "high": 5}
    else:
        question["textQuestion"] = {"paragraph": False}

    request_body = {
        "requests": [
            {
                "createItem": {
                    "item": {
                        "title": title,
                        "questionItem": {"question": question},
                    },
                    "location": {"index": 0},
                }
            }
        ]
    }

    await asyncio.to_thread(
        service.forms()
        .batchUpdate(formId=form_id, body=request_body)
        .execute
    )

    return f"Added question '{title}' ({question_type}) to form {form_id}"
