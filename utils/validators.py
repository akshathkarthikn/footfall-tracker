"""
Input validation and spike detection utilities.
"""

from database.db import get_setting


def validate_footfall_count(count: int) -> tuple[bool, str]:
    """
    Validate a footfall count value.
    Returns (is_valid, error_message).
    """
    if count is None:
        return False, "Count cannot be empty"

    try:
        count = int(count)
    except (ValueError, TypeError):
        return False, "Count must be a number"

    if count < 0:
        return False, "Count cannot be negative"

    max_value = int(get_setting('max_footfall_value', '10000'))
    if count > max_value:
        return False, f"Count exceeds maximum allowed value ({max_value})"

    return True, ""


def detect_spike(new_count: int, previous_count: int) -> tuple[bool, float]:
    """
    Detect if a new count is a significant spike from the previous count.
    Returns (is_spike, percent_change).
    """
    if previous_count is None or previous_count == 0:
        return False, 0.0

    threshold = int(get_setting('spike_threshold_percent', '50'))
    percent_change = ((new_count - previous_count) / previous_count) * 100

    is_spike = percent_change > threshold
    return is_spike, percent_change


def format_percent_change(change: float) -> str:
    """Format a percent change for display."""
    if change > 0:
        return f"+{change:.1f}%"
    else:
        return f"{change:.1f}%"


def validate_username(username: str) -> tuple[bool, str]:
    """Validate a username."""
    if not username:
        return False, "Username cannot be empty"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must be 50 characters or less"

    if not username.isalnum() and not all(c.isalnum() or c in '_-' for c in username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate a password."""
    if not password:
        return False, "Password cannot be empty"

    if len(password) < 4:
        return False, "Password must be at least 4 characters"

    return True, ""


def validate_floor_name(name: str) -> tuple[bool, str]:
    """Validate a floor name."""
    if not name:
        return False, "Floor name cannot be empty"

    if len(name) > 100:
        return False, "Floor name must be 100 characters or less"

    return True, ""
