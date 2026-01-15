"""
Google Sheets MCP Tools

Provides tools for listing, reading, and writing spreadsheets.

Adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Original: gsheets/sheets_tools.py
Licensed under MIT License.
"""

import asyncio
import logging
from typing import Optional, List

from googleapiclient.errors import HttpError

from ..auth.service_adapter import with_sheets_service, with_drive_service

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
async def list_spreadsheets(
    service,
    user_google_email: str,
    query: str = "",
    page_size: int = 20,
) -> str:
    """
    List Google Sheets spreadsheets in Drive.

    Args:
        user_google_email: The user's Google email address
        query: Optional search query to filter spreadsheets
        page_size: Maximum number of spreadsheets to return (default: 20)

    Returns:
        str: Formatted list of spreadsheets
    """
    logger.info(f"[list_spreadsheets] User: {user_google_email}, Query: '{query}'")

    base_query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    if query:
        escaped_query = query.replace("'", "\\'")
        base_query = f"{base_query} and name contains '{escaped_query}'"

    results = await asyncio.to_thread(
        service.files()
        .list(
            q=base_query,
            pageSize=page_size,
            fields="files(id, name, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute
    )

    files = results.get("files", [])
    if not files:
        return f"No spreadsheets found{' matching: ' + query if query else ''}."

    output = [
        f"Found {len(files)} spreadsheets{' matching: ' + query if query else ''}:"
    ]
    for file in files:
        output.append(
            f"- {file['name']} (ID: {file['id']})\n"
            f"  Modified: {file.get('modifiedTime', 'N/A')}\n"
            f"  Link: {file.get('webViewLink', '#')}"
        )

    return "\n".join(output)


@_handle_errors
@with_sheets_service
async def get_sheet_values(
    service,
    user_google_email: str,
    spreadsheet_id: str,
    range: str = "Sheet1",
    value_render: str = "FORMATTED_VALUE",
) -> str:
    """
    Get values from a Google Sheet.

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
        range: A1 notation range (e.g., "Sheet1!A1:D10" or just "Sheet1")
        value_render: How values should be rendered:
                     - "FORMATTED_VALUE" (default) - as displayed in sheets
                     - "UNFORMATTED_VALUE" - raw values
                     - "FORMULA" - shows formulas

    Returns:
        str: Formatted cell values
    """
    logger.info(
        f"[get_sheet_values] User: {user_google_email}, Sheet: {spreadsheet_id}, Range: {range}"
    )

    result = await asyncio.to_thread(
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueRenderOption=value_render,
        )
        .execute
    )

    values = result.get("values", [])
    if not values:
        return f"No data found in range '{range}'."

    output = [
        f"Spreadsheet: {spreadsheet_id}",
        f"Range: {range}",
        f"Rows: {len(values)}",
        "",
        "--- DATA ---",
    ]

    # Format as table
    for i, row in enumerate(values):
        row_str = " | ".join(str(cell) for cell in row)
        output.append(f"Row {i + 1}: {row_str}")

    link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    output.append(f"\nLink: {link}")

    return "\n".join(output)


@_handle_errors
@with_sheets_service
async def update_sheet_values(
    service,
    user_google_email: str,
    spreadsheet_id: str,
    range: str,
    values: List[List[str]],
    value_input: str = "USER_ENTERED",
) -> str:
    """
    Update values in a Google Sheet.

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
        range: A1 notation range (e.g., "Sheet1!A1:D10")
        values: 2D array of values to write
                Example: [["Header1", "Header2"], ["Value1", "Value2"]]
        value_input: How input values should be interpreted:
                    - "USER_ENTERED" (default) - parsed as if typed in UI
                    - "RAW" - values are stored as-is

    Returns:
        str: Confirmation with updated range details
    """
    logger.info(
        f"[update_sheet_values] User: {user_google_email}, Sheet: {spreadsheet_id}, Range: {range}"
    )

    body = {"values": values}

    result = await asyncio.to_thread(
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption=value_input,
            body=body,
        )
        .execute
    )

    updated_cells = result.get("updatedCells", 0)
    updated_rows = result.get("updatedRows", 0)
    updated_range = result.get("updatedRange", range)

    link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

    return (
        f"Updated spreadsheet: {spreadsheet_id}\n"
        f"Range: {updated_range}\n"
        f"Cells updated: {updated_cells}\n"
        f"Rows updated: {updated_rows}\n"
        f"Link: {link}"
    )


@_handle_errors
@with_sheets_service
async def create_spreadsheet(
    service,
    user_google_email: str,
    title: str,
    sheet_names: Optional[List[str]] = None,
) -> str:
    """
    Create a new Google Spreadsheet.

    Args:
        user_google_email: The user's Google email address
        title: Title for the new spreadsheet
        sheet_names: Optional list of sheet names to create (default: ["Sheet1"])

    Returns:
        str: Confirmation with spreadsheet details
    """
    logger.info(f"[create_spreadsheet] User: {user_google_email}, Title: {title}")

    sheets = []
    if sheet_names:
        for i, name in enumerate(sheet_names):
            sheets.append(
                {
                    "properties": {
                        "sheetId": i,
                        "title": name,
                        "index": i,
                    }
                }
            )
    else:
        sheets.append(
            {
                "properties": {
                    "sheetId": 0,
                    "title": "Sheet1",
                    "index": 0,
                }
            }
        )

    body = {
        "properties": {"title": title},
        "sheets": sheets,
    }

    spreadsheet = await asyncio.to_thread(
        service.spreadsheets().create(body=body).execute
    )

    spreadsheet_id = spreadsheet.get("spreadsheetId")
    created_sheets = [
        s.get("properties", {}).get("title", "Unknown")
        for s in spreadsheet.get("sheets", [])
    ]
    link = spreadsheet.get(
        "spreadsheetUrl",
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
    )

    return (
        f"Created spreadsheet: {title}\n"
        f"ID: {spreadsheet_id}\n"
        f"Sheets: {', '.join(created_sheets)}\n"
        f"Link: {link}"
    )


@_handle_errors
@with_sheets_service
async def append_sheet_values(
    service,
    user_google_email: str,
    spreadsheet_id: str,
    range: str,
    values: List[List[str]],
    value_input: str = "USER_ENTERED",
) -> str:
    """
    Append values to a Google Sheet (adds rows after existing data).

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID
        range: A1 notation range to append to (e.g., "Sheet1!A:D" or "Sheet1")
        values: 2D array of values to append
                Example: [["Value1", "Value2"], ["Value3", "Value4"]]
        value_input: How input values should be interpreted:
                    - "USER_ENTERED" (default) - parsed as if typed in UI
                    - "RAW" - values are stored as-is

    Returns:
        str: Confirmation with appended range details
    """
    logger.info(
        f"[append_sheet_values] User: {user_google_email}, Sheet: {spreadsheet_id}, Range: {range}"
    )

    body = {"values": values}

    result = await asyncio.to_thread(
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption=value_input,
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute
    )

    updates = result.get("updates", {})
    updated_range = updates.get("updatedRange", range)
    updated_rows = updates.get("updatedRows", 0)
    updated_cells = updates.get("updatedCells", 0)

    link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

    return (
        f"Appended to spreadsheet: {spreadsheet_id}\n"
        f"Range: {updated_range}\n"
        f"Rows added: {updated_rows}\n"
        f"Cells added: {updated_cells}\n"
        f"Link: {link}"
    )


@_handle_errors
@with_sheets_service
async def get_spreadsheet_metadata(
    service,
    user_google_email: str,
    spreadsheet_id: str,
) -> str:
    """
    Get metadata about a spreadsheet including all sheet names and properties.

    Args:
        user_google_email: The user's Google email address
        spreadsheet_id: The spreadsheet ID

    Returns:
        str: Spreadsheet metadata including title and sheet list
    """
    logger.info(
        f"[get_spreadsheet_metadata] User: {user_google_email}, Sheet: {spreadsheet_id}"
    )

    result = await asyncio.to_thread(
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="properties,sheets.properties")
        .execute
    )

    props = result.get("properties", {})
    title = props.get("title", "Untitled")
    sheets = result.get("sheets", [])

    output = [
        f"Spreadsheet: {title}",
        f"ID: {spreadsheet_id}",
        f"Sheets ({len(sheets)}):",
    ]

    for sheet in sheets:
        sheet_props = sheet.get("properties", {})
        sheet_title = sheet_props.get("title", "Unknown")
        sheet_id = sheet_props.get("sheetId", "N/A")
        row_count = sheet_props.get("gridProperties", {}).get("rowCount", "N/A")
        col_count = sheet_props.get("gridProperties", {}).get("columnCount", "N/A")
        output.append(
            f"  - {sheet_title} (ID: {sheet_id}, Rows: {row_count}, Cols: {col_count})"
        )

    link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    output.append(f"\nLink: {link}")

    return "\n".join(output)
