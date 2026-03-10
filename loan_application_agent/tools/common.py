"""Common utility tools available to all agents."""

from datetime import datetime


def get_current_time(timezone: str = "UTC") -> dict:
    """Get the current date and time.

    Args:
        timezone: Timezone name (e.g., 'UTC', 'US/Eastern'). Defaults to UTC.

    Returns:
        Dictionary with current date, time, and timezone.
    """
    now = datetime.utcnow()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": timezone,
        "formatted": now.strftime("%B %d, %Y at %I:%M %p UTC"),
    }
