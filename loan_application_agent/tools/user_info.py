"""User information collection tools for the onboarding use case.

These tools store and validate personal information collected during conversation.
All PII passes through the Trustwise LLM gateway where policies are enforced
automatically (masking, logging, compliance).
"""

from google.adk.tools import ToolContext

REQUIRED_FIELDS = ["full_name", "age", "email", "phone_number"]
OPTIONAL_FIELDS = ["address", "occupation"]


def collect_user_info(
    field_name: str,
    field_value: str,
    tool_context: ToolContext,
) -> dict:
    """Store a piece of user personal information collected during the onboarding conversation.

    Args:
        field_name: The type of information being collected.
            Required fields: full_name, age, email, phone_number.
            Optional fields: address, occupation.
        field_value: The actual value provided by the user.

    Returns:
        Confirmation of stored information with field name and status.
    """
    user_info = tool_context.state.get("user_info", {})
    user_info[field_name] = field_value
    tool_context.state["user_info"] = user_info

    return {
        "status": "stored",
        "field": field_name,
        "value": field_value,
        "total_collected": len(user_info),
    }


def validate_user_info(tool_context: ToolContext) -> dict:
    """Check which required user information fields have been collected and which are still missing.

    Returns:
        Dictionary with collected fields, missing required fields, and completion status.
    """
    user_info = tool_context.state.get("user_info", {})
    collected = dict(user_info)
    missing = [f for f in REQUIRED_FIELDS if f not in user_info]
    optional_collected = {k: v for k, v in user_info.items() if k in OPTIONAL_FIELDS}

    return {
        "collected": collected,
        "missing_required": missing,
        "optional_collected": optional_collected,
        "complete": len(missing) == 0,
        "required_fields": REQUIRED_FIELDS,
    }
