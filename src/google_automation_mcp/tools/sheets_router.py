"""Sheets tools — Apps Script Router backend."""

import logging
from typing import Optional, List

from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def list_spreadsheets(
    user_google_email: str, query: str = "", page_size: int = 20,
) -> str:
    logger.info(f"[list_spreadsheets] User: {user_google_email}")
    results = await call_router(user_google_email, "list_spreadsheets", {
        "query": query, "page_size": page_size,
    })
    if not results:
        return f"No spreadsheets found{' matching: ' + query if query else ''}."
    output = [f"Found {len(results)} spreadsheets{' matching: ' + query if query else ''}:"]
    for f in results:
        output.append(
            f"- {f['name']} (ID: {f['id']})\n"
            f"  Modified: {f.get('modified', 'N/A')}\n"
            f"  Link: {f.get('url', '#')}"
        )
    return "\n".join(output)


@handle_errors
async def get_sheet_values(
    user_google_email: str, spreadsheet_id: str,
    range: str = "Sheet1", value_render: str = "FORMATTED_VALUE",
) -> str:
    logger.info(f"[get_sheet_values] User: {user_google_email}, Sheet: {spreadsheet_id}")
    result = await call_router(user_google_email, "get_sheet_values", {
        "spreadsheet_id": spreadsheet_id, "range": range,
    })
    values = result.get("values", [])
    if not values:
        return f"No data found in range '{range}'."
    output = [
        f"Spreadsheet: {spreadsheet_id}", f"Range: {range}",
        f"Rows: {len(values)}", "", "--- DATA ---",
    ]
    for i, row in enumerate(values):
        row_str = " | ".join(str(cell) for cell in row)
        output.append(f"Row {i + 1}: {row_str}")
    output.append(f"\nLink: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    return "\n".join(output)


@handle_errors
async def update_sheet_values(
    user_google_email: str, spreadsheet_id: str, range: str,
    values: List[List[str]], value_input: str = "USER_ENTERED",
) -> str:
    logger.info(f"[update_sheet_values] User: {user_google_email}, Sheet: {spreadsheet_id}")
    result = await call_router(user_google_email, "update_sheet_values", {
        "spreadsheet_id": spreadsheet_id, "range": range, "values": values,
    })
    link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    return (
        f"Updated spreadsheet: {spreadsheet_id}\n"
        f"Range: {result.get('range', range)}\n"
        f"Cells updated: {result.get('updated_cells', 0)}\n"
        f"Rows updated: {result.get('updated_rows', 0)}\n"
        f"Link: {link}"
    )


@handle_errors
async def append_sheet_values(
    user_google_email: str, spreadsheet_id: str, range: str,
    values: List[List[str]], value_input: str = "USER_ENTERED",
) -> str:
    logger.info(f"[append_sheet_values] User: {user_google_email}, Sheet: {spreadsheet_id}")
    result = await call_router(user_google_email, "append_sheet_values", {
        "spreadsheet_id": spreadsheet_id, "range": range, "values": values,
    })
    link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    return (
        f"Appended to spreadsheet: {spreadsheet_id}\n"
        f"Range: {result.get('updated_range', range)}\n"
        f"Rows added: {result.get('updated_rows', 0)}\n"
        f"Cells added: {result.get('updated_cells', 0)}\n"
        f"Link: {link}"
    )


@handle_errors
async def create_spreadsheet(
    user_google_email: str, title: str,
    sheet_names: Optional[List[str]] = None,
) -> str:
    logger.info(f"[create_spreadsheet] User: {user_google_email}, Title: {title}")
    result = await call_router(user_google_email, "create_spreadsheet", {
        "title": title, "sheet_names": sheet_names,
    })
    sheets = result.get("sheets", ["Sheet1"])
    return (
        f"Created spreadsheet: {title}\n"
        f"ID: {result['spreadsheet_id']}\n"
        f"Sheets: {', '.join(sheets)}\n"
        f"Link: {result.get('url', '#')}"
    )


@handle_errors
async def get_spreadsheet_metadata(
    user_google_email: str, spreadsheet_id: str,
) -> str:
    logger.info(f"[get_spreadsheet_metadata] User: {user_google_email}, Sheet: {spreadsheet_id}")
    result = await call_router(user_google_email, "get_spreadsheet_metadata", {
        "spreadsheet_id": spreadsheet_id,
    })
    sheets = result.get("sheets", [])
    output = [
        f"Spreadsheet: {result.get('title', 'Untitled')}",
        f"ID: {spreadsheet_id}", f"Sheets ({len(sheets)}):",
    ]
    for s in sheets:
        output.append(f"  - {s['title']} (ID: {s.get('sheet_id', 'N/A')}, Rows: {s.get('rows', 'N/A')}, Cols: {s.get('cols', 'N/A')})")
    output.append(f"\nLink: {result.get('url', '#')}")
    return "\n".join(output)
