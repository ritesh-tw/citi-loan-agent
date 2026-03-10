"""Conditional tool registration based on environment variables.

Tools are only registered when their required credentials are present.
This allows the agent to gracefully handle missing integrations —
e.g., if Google Drive credentials aren't configured, Drive tools
simply won't be available to the agent.
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_registered_tools() -> list:
    """Return list of tool functions based on available credentials in env."""
    tools = []

    # Always available tools
    from .common import get_current_time
    from .user_info import collect_user_info, validate_user_info

    tools.extend([get_current_time, collect_user_info, validate_user_info])
    logger.info("Registered core tools: get_current_time, collect_user_info, validate_user_info")

    # Google Drive — only if service account JSON is configured
    if os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON"):
        from .google_drive import search_drive_files, read_drive_file, list_drive_folder

        tools.extend([search_drive_files, read_drive_file, list_drive_folder])
        logger.info("Registered Google Drive tools: search_drive_files, read_drive_file, list_drive_folder")
    else:
        logger.info("Google Drive tools DISABLED (GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON not set)")

    # Google Docs — only if service account JSON is configured
    if os.getenv("GOOGLE_DOCS_SERVICE_ACCOUNT_JSON"):
        from .google_docs import read_google_doc, create_google_doc

        tools.extend([read_google_doc, create_google_doc])
        logger.info("Registered Google Docs tools: read_google_doc, create_google_doc")
    else:
        logger.info("Google Docs tools DISABLED (GOOGLE_DOCS_SERVICE_ACCOUNT_JSON not set)")

    # Google Sheets — only if service account JSON is configured
    if os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON"):
        from .google_sheets import read_sheet, query_sheet

        tools.extend([read_sheet, query_sheet])
        logger.info("Registered Google Sheets tools: read_sheet, query_sheet")
    else:
        logger.info("Google Sheets tools DISABLED (GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON not set)")

    logger.info(f"Total tools registered: {len(tools)}")
    return tools


def get_qa_tools() -> list:
    """Return tools suitable for the Q&A agent (excludes user_info tools)."""
    from .common import get_current_time

    tools = [get_current_time]

    if os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON"):
        from .google_drive import search_drive_files, read_drive_file, list_drive_folder

        tools.extend([search_drive_files, read_drive_file, list_drive_folder])

    if os.getenv("GOOGLE_DOCS_SERVICE_ACCOUNT_JSON"):
        from .google_docs import read_google_doc, create_google_doc

        tools.extend([read_google_doc, create_google_doc])

    if os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON"):
        from .google_sheets import read_sheet, query_sheet

        tools.extend([read_sheet, query_sheet])

    return tools
