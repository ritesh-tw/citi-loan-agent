"""Google Sheets tools - enabled only when GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON is set.

Provides read and query capabilities for Google Sheets.
Uses Google Sheets API v4 with service account authentication.
"""

import json
import os
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


@lru_cache(maxsize=1)
def _get_sheets_service():
    """Build and cache the Google Sheets API service."""
    creds_json = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", "")
    if not creds_json:
        raise RuntimeError("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON not configured")

    creds_data = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_data, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials)


def read_sheet(spreadsheet_id: str, range: str = "Sheet1") -> dict:
    """Read data from a specific range in a Google Sheets spreadsheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID (from the URL).
        range: The A1 notation range to read (e.g., 'Sheet1!A1:D10', 'Sheet1').
            Defaults to 'Sheet1' (entire first sheet).

    Returns:
        Dictionary with spreadsheet title, range, headers, and row data.
    """
    service = _get_sheets_service()

    # Get spreadsheet metadata
    spreadsheet = (
        service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    )
    title = spreadsheet.get("properties", {}).get("title", "Untitled")

    # Get values
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range)
        .execute()
    )

    values = result.get("values", [])

    if not values:
        return {
            "spreadsheet_id": spreadsheet_id,
            "title": title,
            "range": range,
            "headers": [],
            "rows": [],
            "row_count": 0,
        }

    headers = values[0] if values else []
    rows = values[1:] if len(values) > 1 else []

    # Convert rows to dicts using headers
    row_dicts = []
    for row in rows[:500]:  # Limit to 500 rows
        row_dict = {}
        for i, header in enumerate(headers):
            row_dict[header] = row[i] if i < len(row) else ""
        row_dicts.append(row_dict)

    return {
        "spreadsheet_id": spreadsheet_id,
        "title": title,
        "range": range,
        "headers": headers,
        "rows": row_dicts,
        "row_count": len(row_dicts),
    }


def query_sheet(spreadsheet_id: str, sheet_name: str = "Sheet1") -> dict:
    """Read all data from a specific sheet tab in a Google Sheets spreadsheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        sheet_name: The name of the sheet tab to read. Defaults to 'Sheet1'.

    Returns:
        Dictionary with sheet metadata, headers, and all row data.
    """
    return read_sheet(spreadsheet_id, range=sheet_name)
