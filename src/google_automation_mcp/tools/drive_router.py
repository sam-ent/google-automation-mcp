"""Drive tools — Apps Script Router backend."""

import logging
from ..router.client import call_router
from .error_handler import handle_errors

logger = logging.getLogger(__name__)


@handle_errors
async def search_drive_files(
    user_google_email: str, query: str, page_size: int = 10,
    include_shared_drives: bool = True,
) -> str:
    logger.info(f"[search_drive_files] User: {user_google_email}, Query: '{query}'")
    results = await call_router(user_google_email, "search_drive", {
        "query": query, "page_size": page_size,
    })
    if not results:
        return f"No files found for query: '{query}'"
    output = [f"Found {len(results)} files matching '{query}':"]
    for item in results:
        size_str = f", Size: {item.get('size', 'N/A')}" if item.get("size") else ""
        output.append(
            f"- {item['name']} (ID: {item['id']})\n"
            f"  Type: {item.get('mime_type', 'N/A')}{size_str}\n"
            f"  Modified: {item.get('modified', 'N/A')}\n"
            f"  Link: {item.get('url', '#')}"
        )
    return "\n".join(output)


@handle_errors
async def list_drive_items(
    user_google_email: str, folder_id: str = "root", page_size: int = 50,
    include_shared_drives: bool = True,
) -> str:
    logger.info(f"[list_drive_items] User: {user_google_email}, Folder: {folder_id}")
    result = await call_router(user_google_email, "list_drive", {
        "folder_id": folder_id, "page_size": page_size,
    })
    folders = result.get("folders", [])
    files = result.get("files", [])
    total = len(folders) + len(files)
    if total == 0:
        return f"No items found in folder '{folder_id}'"
    output = [f"Found {total} items in folder '{folder_id}':"]
    if folders:
        output.append("\nFolders:")
        for f in folders:
            output.append(f"  📁 {f['name']} (ID: {f['id']})")
    if files:
        output.append("\nFiles:")
        for f in files:
            size_str = f" [{f.get('size', 'N/A')} bytes]" if f.get("size") else ""
            output.append(f"  📄 {f['name']}{size_str} (ID: {f['id']})")
    return "\n".join(output)


@handle_errors
async def get_drive_file_content(user_google_email: str, file_id: str) -> str:
    logger.info(f"[get_drive_file_content] User: {user_google_email}, File: {file_id}")
    result = await call_router(user_google_email, "get_drive_content", {
        "file_id": file_id,
    })
    header = (
        f'File: "{result["name"]}" (ID: {result["id"]})\n'
        f"Type: {result.get('mime_type', 'N/A')}\n"
        f"Link: {result.get('url', '#')}\n\n"
        f"--- CONTENT ---\n"
    )
    return header + result.get("content", "")


@handle_errors
async def create_drive_file(
    user_google_email: str, file_name: str, content: str = "",
    folder_id: str = "root", mime_type: str = "text/plain",
) -> str:
    logger.info(f"[create_drive_file] User: {user_google_email}, Name: {file_name}")
    result = await call_router(user_google_email, "create_drive_file", {
        "file_name": file_name, "content": content,
        "folder_id": folder_id, "mime_type": mime_type,
    })
    return f"Created file: {result['name']}\nID: {result['id']}\nLink: {result.get('url', '#')}"


@handle_errors
async def create_drive_folder(
    user_google_email: str, folder_name: str, parent_id: str = "root",
) -> str:
    logger.info(f"[create_drive_folder] User: {user_google_email}, Name: {folder_name}")
    result = await call_router(user_google_email, "create_drive_folder", {
        "folder_name": folder_name, "parent_id": parent_id,
    })
    return f"Created folder: {result['name']}\nID: {result['id']}\nLink: {result.get('url', '#')}"


@handle_errors
async def delete_drive_file(user_google_email: str, file_id: str) -> str:
    logger.info(f"[delete_drive_file] User: {user_google_email}, File: {file_id}")
    await call_router(user_google_email, "delete_drive_file", {"file_id": file_id})
    return f"Permanently deleted file: {file_id}"


@handle_errors
async def trash_drive_file(user_google_email: str, file_id: str) -> str:
    logger.info(f"[trash_drive_file] User: {user_google_email}, File: {file_id}")
    await call_router(user_google_email, "trash_drive_file", {"file_id": file_id})
    return f"Moved to trash: {file_id}"


@handle_errors
async def share_drive_file(
    user_google_email: str, file_id: str, email: str,
    role: str = "reader", send_notification: bool = True,
) -> str:
    logger.info(f"[share_drive_file] User: {user_google_email}, File: {file_id}")
    await call_router(user_google_email, "share_drive_file", {
        "file_id": file_id, "email": email, "role": role,
    })
    return f"Shared file: {file_id}\nWith: {email}\nRole: {role}"


@handle_errors
async def list_drive_permissions(user_google_email: str, file_id: str) -> str:
    logger.info(f"[list_drive_permissions] User: {user_google_email}, File: {file_id}")
    result = await call_router(user_google_email, "list_drive_permissions", {
        "file_id": file_id,
    })
    perms = result.get("permissions", [])
    if not perms:
        return f"No permissions found for file: {file_id}"
    output = [f"Permissions for file {file_id}:"]
    for p in perms:
        output.append(f"  - {p.get('email', 'unknown')} ({p.get('role', 'unknown')})")
    return "\n".join(output)


@handle_errors
async def remove_drive_permission(
    user_google_email: str, file_id: str, permission_id: str,
) -> str:
    logger.info(f"[remove_drive_permission] User: {user_google_email}, File: {file_id}")
    await call_router(user_google_email, "remove_drive_permission", {
        "file_id": file_id, "permission_id": permission_id,
    })
    return f"Removed permission {permission_id} from file {file_id}"
