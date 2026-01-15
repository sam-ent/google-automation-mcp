"""
Google Drive MCP Tools

Provides tools for searching, listing, reading, and creating Drive files.

Adapted from google_workspace_mcp by Taylor Wilsdon:
https://github.com/taylorwilsdon/google_workspace_mcp
Original: gdrive/drive_tools.py
Licensed under MIT License.
"""

import asyncio
import io
import logging

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from ..auth.service_adapter import with_drive_service

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
async def search_drive_files(
    service,
    user_google_email: str,
    query: str,
    page_size: int = 10,
    include_shared_drives: bool = True,
) -> str:
    """
    Search for files and folders in Google Drive.

    Args:
        user_google_email: The user's Google email address
        query: Search query string. Supports Drive query operators:
               - name contains 'example'
               - mimeType = 'application/vnd.google-apps.spreadsheet'
               - fullText contains 'keyword'
               - modifiedTime > '2024-01-01'
        page_size: Maximum number of files to return (default: 10)
        include_shared_drives: Whether to include shared drive items (default: True)

    Returns:
        str: Formatted list of matching files
    """
    logger.info(f"[search_drive_files] User: {user_google_email}, Query: '{query}'")

    # Check if query looks like a structured Drive query
    is_structured = any(
        op in query.lower() for op in ["contains", "=", ">", "<", "in parents"]
    )

    if is_structured:
        final_query = query
    else:
        escaped_query = query.replace("'", "\\'")
        final_query = f"fullText contains '{escaped_query}'"

    results = await asyncio.to_thread(
        service.files()
        .list(
            q=final_query,
            pageSize=page_size,
            fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
            supportsAllDrives=include_shared_drives,
            includeItemsFromAllDrives=include_shared_drives,
        )
        .execute
    )

    files = results.get("files", [])
    if not files:
        return f"No files found for query: '{query}'"

    output = [f"Found {len(files)} files matching '{query}':"]
    for item in files:
        size_str = f", Size: {item.get('size', 'N/A')}" if "size" in item else ""
        output.append(
            f"- {item['name']} (ID: {item['id']})\n"
            f"  Type: {item['mimeType']}{size_str}\n"
            f"  Modified: {item.get('modifiedTime', 'N/A')}\n"
            f"  Link: {item.get('webViewLink', '#')}"
        )

    return "\n".join(output)


@_handle_errors
@with_drive_service
async def list_drive_items(
    service,
    user_google_email: str,
    folder_id: str = "root",
    page_size: int = 50,
    include_shared_drives: bool = True,
) -> str:
    """
    List files and folders in a Drive folder.

    Args:
        user_google_email: The user's Google email address
        folder_id: The folder ID to list (default: 'root' for My Drive root)
        page_size: Maximum number of items to return (default: 50)
        include_shared_drives: Whether to include shared drive items (default: True)

    Returns:
        str: Formatted list of items in the folder
    """
    logger.info(f"[list_drive_items] User: {user_google_email}, Folder: {folder_id}")

    query = f"'{folder_id}' in parents and trashed=false"

    results = await asyncio.to_thread(
        service.files()
        .list(
            q=query,
            pageSize=page_size,
            fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
            supportsAllDrives=include_shared_drives,
            includeItemsFromAllDrives=include_shared_drives,
            orderBy="folder,name",
        )
        .execute
    )

    files = results.get("files", [])
    if not files:
        return f"No items found in folder '{folder_id}'"

    output = [f"Found {len(files)} items in folder '{folder_id}':"]

    # Separate folders and files
    folders = [
        f for f in files if f.get("mimeType") == "application/vnd.google-apps.folder"
    ]
    non_folders = [
        f for f in files if f.get("mimeType") != "application/vnd.google-apps.folder"
    ]

    if folders:
        output.append("\nFolders:")
        for item in folders:
            output.append(f"  📁 {item['name']} (ID: {item['id']})")

    if non_folders:
        output.append("\nFiles:")
        for item in non_folders:
            size_str = f" [{item.get('size', 'N/A')} bytes]" if "size" in item else ""
            output.append(f"  📄 {item['name']}{size_str} (ID: {item['id']})")

    return "\n".join(output)


@_handle_errors
@with_drive_service
async def get_drive_file_content(
    service,
    user_google_email: str,
    file_id: str,
) -> str:
    """
    Get the content of a Google Drive file.

    Supports:
    - Google Docs → exported as plain text
    - Google Sheets → exported as CSV
    - Google Slides → exported as plain text
    - Other files → direct download (text files)

    Args:
        user_google_email: The user's Google email address
        file_id: The Drive file ID

    Returns:
        str: File content with metadata header
    """
    logger.info(f"[get_drive_file_content] User: {user_google_email}, File: {file_id}")

    # Get file metadata
    file_metadata = await asyncio.to_thread(
        service.files()
        .get(
            fileId=file_id,
            fields="id, name, mimeType, webViewLink",
            supportsAllDrives=True,
        )
        .execute
    )

    mime_type = file_metadata.get("mimeType", "")
    file_name = file_metadata.get("name", "Unknown")

    # Export MIME types for Google native files
    export_mime_map = {
        "application/vnd.google-apps.document": "text/plain",
        "application/vnd.google-apps.spreadsheet": "text/csv",
        "application/vnd.google-apps.presentation": "text/plain",
    }

    export_mime = export_mime_map.get(mime_type)

    if export_mime:
        request_obj = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request_obj = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request_obj)

    done = False
    while not done:
        _, done = await asyncio.to_thread(downloader.next_chunk)

    content_bytes = fh.getvalue()

    try:
        body_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        body_text = f"[Binary file - {len(content_bytes)} bytes]"

    header = (
        f'File: "{file_name}" (ID: {file_id})\n'
        f"Type: {mime_type}\n"
        f"Link: {file_metadata.get('webViewLink', '#')}\n\n"
        f"--- CONTENT ---\n"
    )

    return header + body_text


@_handle_errors
@with_drive_service
async def create_drive_file(
    service,
    user_google_email: str,
    file_name: str,
    content: str = "",
    folder_id: str = "root",
    mime_type: str = "text/plain",
) -> str:
    """
    Create a new file in Google Drive.

    Args:
        user_google_email: The user's Google email address
        file_name: Name for the new file
        content: File content (text)
        folder_id: Parent folder ID (default: 'root')
        mime_type: MIME type of the file (default: 'text/plain')

    Returns:
        str: Confirmation with file details
    """
    logger.info(f"[create_drive_file] User: {user_google_email}, Name: {file_name}")

    file_metadata = {
        "name": file_name,
        "parents": [folder_id],
        "mimeType": mime_type,
    }

    if content:
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype=mime_type,
            resumable=True,
        )

        created_file = await asyncio.to_thread(
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink",
                supportsAllDrives=True,
            )
            .execute
        )
    else:
        created_file = await asyncio.to_thread(
            service.files()
            .create(
                body=file_metadata,
                fields="id, name, webViewLink",
                supportsAllDrives=True,
            )
            .execute
        )

    return (
        f"Created file: {created_file.get('name')}\n"
        f"ID: {created_file.get('id')}\n"
        f"Link: {created_file.get('webViewLink', '#')}"
    )


@_handle_errors
@with_drive_service
async def create_drive_folder(
    service,
    user_google_email: str,
    folder_name: str,
    parent_id: str = "root",
) -> str:
    """
    Create a new folder in Google Drive.

    Args:
        user_google_email: The user's Google email address
        folder_name: Name for the new folder
        parent_id: Parent folder ID (default: 'root' for My Drive root)

    Returns:
        str: Confirmation with folder details
    """
    logger.info(f"[create_drive_folder] User: {user_google_email}, Name: {folder_name}")

    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }

    created_folder = await asyncio.to_thread(
        service.files()
        .create(
            body=file_metadata,
            fields="id, name, webViewLink",
            supportsAllDrives=True,
        )
        .execute
    )

    return (
        f"Created folder: {created_folder.get('name')}\n"
        f"ID: {created_folder.get('id')}\n"
        f"Link: {created_folder.get('webViewLink', '#')}"
    )


@_handle_errors
@with_drive_service
async def delete_drive_file(
    service,
    user_google_email: str,
    file_id: str,
) -> str:
    """
    Permanently delete a file from Google Drive.

    WARNING: This permanently deletes the file. Use trash_drive_file for recoverable deletion.

    Args:
        user_google_email: The user's Google email address
        file_id: The file ID to delete

    Returns:
        str: Confirmation message
    """
    logger.info(f"[delete_drive_file] User: {user_google_email}, File: {file_id}")

    await asyncio.to_thread(
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute
    )

    return f"Permanently deleted file: {file_id}"


@_handle_errors
@with_drive_service
async def trash_drive_file(
    service,
    user_google_email: str,
    file_id: str,
) -> str:
    """
    Move a file to trash in Google Drive (recoverable).

    Args:
        user_google_email: The user's Google email address
        file_id: The file ID to trash

    Returns:
        str: Confirmation message
    """
    logger.info(f"[trash_drive_file] User: {user_google_email}, File: {file_id}")

    await asyncio.to_thread(
        service.files()
        .update(fileId=file_id, body={"trashed": True}, supportsAllDrives=True)
        .execute
    )

    return f"Moved to trash: {file_id}"


@_handle_errors
@with_drive_service
async def share_drive_file(
    service,
    user_google_email: str,
    file_id: str,
    email: str,
    role: str = "reader",
    send_notification: bool = True,
) -> str:
    """
    Share a file or folder with a user.

    Args:
        user_google_email: The user's Google email address
        file_id: The file or folder ID to share
        email: Email address of the user to share with
        role: Permission role - "reader", "writer", "commenter", or "owner"
        send_notification: Whether to send an email notification (default: True)

    Returns:
        str: Confirmation with permission details
    """
    logger.info(
        f"[share_drive_file] User: {user_google_email}, File: {file_id}, Share with: {email}"
    )

    permission = {
        "type": "user",
        "role": role,
        "emailAddress": email,
    }

    result = await asyncio.to_thread(
        service.permissions()
        .create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=send_notification,
            supportsAllDrives=True,
        )
        .execute
    )

    return (
        f"Shared file: {file_id}\n"
        f"With: {email}\n"
        f"Role: {role}\n"
        f"Permission ID: {result.get('id')}"
    )


@_handle_errors
@with_drive_service
async def list_drive_permissions(
    service,
    user_google_email: str,
    file_id: str,
) -> str:
    """
    List all permissions on a file or folder.

    Args:
        user_google_email: The user's Google email address
        file_id: The file or folder ID

    Returns:
        str: Formatted list of permissions
    """
    logger.info(f"[list_drive_permissions] User: {user_google_email}, File: {file_id}")

    result = await asyncio.to_thread(
        service.permissions()
        .list(
            fileId=file_id,
            fields="permissions(id, type, role, emailAddress, displayName)",
            supportsAllDrives=True,
        )
        .execute
    )

    permissions = result.get("permissions", [])
    if not permissions:
        return f"No permissions found for file: {file_id}"

    output = [f"Permissions for file {file_id}:"]

    for perm in permissions:
        perm_type = perm.get("type", "unknown")
        role = perm.get("role", "unknown")
        email = perm.get("emailAddress", "")
        name = perm.get("displayName", "")
        perm_id = perm.get("id", "")

        if perm_type == "user":
            output.append(f"  - {name or email} ({role}) [ID: {perm_id}]")
        elif perm_type == "anyone":
            output.append(f"  - Anyone with link ({role}) [ID: {perm_id}]")
        else:
            output.append(f"  - {perm_type}: {name or email} ({role}) [ID: {perm_id}]")

    return "\n".join(output)


@_handle_errors
@with_drive_service
async def remove_drive_permission(
    service,
    user_google_email: str,
    file_id: str,
    permission_id: str,
) -> str:
    """
    Remove a permission from a file or folder.

    Args:
        user_google_email: The user's Google email address
        file_id: The file or folder ID
        permission_id: The permission ID to remove (from list_drive_permissions)

    Returns:
        str: Confirmation message
    """
    logger.info(
        f"[remove_drive_permission] User: {user_google_email}, File: {file_id}, Permission: {permission_id}"
    )

    await asyncio.to_thread(
        service.permissions()
        .delete(fileId=file_id, permissionId=permission_id, supportsAllDrives=True)
        .execute
    )

    return f"Removed permission {permission_id} from file {file_id}"
