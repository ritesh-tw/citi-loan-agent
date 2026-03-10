"""Google Docs tools - enabled only when GOOGLE_DOCS_SERVICE_ACCOUNT_JSON is set.

Provides read and create capabilities for Google Docs.
Uses Google Docs API v1 with service account authentication.
"""

import json
import os
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


@lru_cache(maxsize=1)
def _get_docs_service():
    """Build and cache the Google Docs API service."""
    creds_json = os.getenv("GOOGLE_DOCS_SERVICE_ACCOUNT_JSON", "")
    if not creds_json:
        raise RuntimeError("GOOGLE_DOCS_SERVICE_ACCOUNT_JSON not configured")

    creds_data = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_data, scopes=SCOPES
    )
    return build("docs", "v1", credentials=credentials)


def _extract_text_from_doc(document: dict) -> str:
    """Extract plain text from a Google Docs document body."""
    text_parts = []
    body = document.get("body", {})
    content = body.get("content", [])

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))

    return "".join(text_parts)


def read_google_doc(document_id: str) -> dict:
    """Read the full text content of a Google Docs document.

    Args:
        document_id: The Google Docs document ID (from the URL or Drive search).

    Returns:
        Dictionary with document title and full text content.
    """
    service = _get_docs_service()
    document = service.documents().get(documentId=document_id).execute()

    title = document.get("title", "Untitled")
    content = _extract_text_from_doc(document)

    max_chars = 50000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... [truncated, {len(content)} total chars]"

    return {
        "document_id": document_id,
        "title": title,
        "content": content,
        "character_count": len(content),
    }


def create_google_doc(title: str, content: str) -> dict:
    """Create a new Google Docs document with the given title and content.

    Args:
        title: The title for the new document.
        content: The text content to insert into the document.

    Returns:
        Dictionary with the new document ID, title, and URL.
    """
    service = _get_docs_service()

    # Create the document
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

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
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()

    return {
        "document_id": doc_id,
        "title": title,
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
        "status": "created",
    }
