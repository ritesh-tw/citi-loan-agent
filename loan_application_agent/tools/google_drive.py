"""Google Drive tools - enabled only when GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is set.

Provides search, read, and list capabilities for Google Drive files.
Uses Google Drive API v3 with service account authentication.
"""

import io
import json
import os
from functools import lru_cache

from google.auth.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


@lru_cache(maxsize=1)
def _get_drive_service():
    """Build and cache the Google Drive API service."""
    creds_json = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON", "")
    if not creds_json:
        raise RuntimeError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON not configured")

    creds_data = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_data, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def search_drive_files(query: str, file_type: str = "") -> dict:
    """Search Google Drive files by name or content.

    Args:
        query: Search term to find files in Google Drive (searches file names and content).
        file_type: Optional file type filter. Options: 'document', 'spreadsheet', 'pdf',
            'presentation', 'folder'. Leave empty for all types.

    Returns:
        Dictionary with list of matching files (id, name, mimeType, modifiedTime).
    """
    service = _get_drive_service()

    q_parts = [f"name contains '{query}' or fullText contains '{query}'"]
    q_parts.append("trashed = false")

    mime_map = {
        "document": "application/vnd.google-apps.document",
        "spreadsheet": "application/vnd.google-apps.spreadsheet",
        "pdf": "application/pdf",
        "presentation": "application/vnd.google-apps.presentation",
        "folder": "application/vnd.google-apps.folder",
    }
    if file_type and file_type in mime_map:
        q_parts.append(f"mimeType = '{mime_map[file_type]}'")

    q_string = " and ".join(q_parts)

    results = (
        service.files()
        .list(
            q=q_string,
            pageSize=20,
            fields="files(id, name, mimeType, modifiedTime, size)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )

    files = results.get("files", [])
    return {
        "query": query,
        "file_type_filter": file_type or "all",
        "count": len(files),
        "files": [
            {
                "id": f["id"],
                "name": f["name"],
                "type": f["mimeType"],
                "modified": f.get("modifiedTime", ""),
            }
            for f in files
        ],
    }


def read_drive_file(file_id: str) -> dict:
    """Read the content of a Google Drive file by its ID.

    Supports Google Docs (exported as plain text), PDFs, and other text files.

    Args:
        file_id: The Google Drive file ID to read.

    Returns:
        Dictionary with file name, type, and text content.
    """
    service = _get_drive_service()

    file_meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
    name = file_meta["name"]
    mime = file_meta["mimeType"]

    # Google Docs → export as plain text
    if mime == "application/vnd.google-apps.document":
        content = (
            service.files()
            .export(fileId=file_id, mimeType="text/plain")
            .execute()
            .decode("utf-8")
        )
    # Google Sheets → export as CSV
    elif mime == "application/vnd.google-apps.spreadsheet":
        content = (
            service.files()
            .export(fileId=file_id, mimeType="text/csv")
            .execute()
            .decode("utf-8")
        )
    # Other files → download directly
    else:
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        content = buffer.getvalue().decode("utf-8", errors="replace")

    # Truncate very large files
    max_chars = 50000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... [truncated, {len(content)} total chars]"

    return {
        "file_id": file_id,
        "name": name,
        "type": mime,
        "content": content,
    }


def list_drive_folder(folder_id: str = "root") -> dict:
    """List files and subfolders in a Google Drive folder.

    Args:
        folder_id: The folder ID to list. Use 'root' for the top-level Drive folder.

    Returns:
        Dictionary with folder contents (files and subfolders).
    """
    service = _get_drive_service()

    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and trashed = false",
            pageSize=50,
            fields="files(id, name, mimeType, modifiedTime, size)",
            orderBy="name",
        )
        .execute()
    )

    files = results.get("files", [])
    return {
        "folder_id": folder_id,
        "count": len(files),
        "items": [
            {
                "id": f["id"],
                "name": f["name"],
                "type": f["mimeType"],
                "is_folder": f["mimeType"] == "application/vnd.google-apps.folder",
                "modified": f.get("modifiedTime", ""),
            }
            for f in files
        ],
    }
