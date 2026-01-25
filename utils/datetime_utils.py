"""
Date and time utilities for the Footfall Tracker.
"""

from datetime import datetime, date, timedelta
from database.db import get_setting


def get_operating_hours() -> tuple[int, int]:
    """Get the opening and closing hours from settings."""
    opening = int(get_setting('opening_hour', '9'))
    closing = int(get_setting('closing_hour', '21'))
    return opening, closing


def get_hour_slots() -> list[int]:
    """Get list of hour slots based on operating hours."""
    opening, closing = get_operating_hours()
    return list(range(opening, closing + 1))


def format_hour_slot(hour: int) -> str:
    """Format an hour slot for display (e.g., '9 AM', '2 PM')."""
    if hour == 0:
        return "12 AM"
    elif hour < 12:
        return f"{hour} AM"
    elif hour == 12:
        return "12 PM"
    else:
        return f"{hour - 12} PM"


def get_hour_slot_options() -> list[tuple[int, str]]:
    """Get hour slot options as (value, label) tuples."""
    return [(h, format_hour_slot(h)) for h in get_hour_slots()]


def get_current_hour_slot() -> int:
    """Get the current hour slot."""
    return datetime.now().hour


def get_week_start(d: date) -> date:
    """Get the start of the week for a given date."""
    week_start_day = int(get_setting('week_start_day', '0'))  # 0=Monday
    days_since_start = (d.weekday() - week_start_day) % 7
    return d - timedelta(days=days_since_start)


def get_week_end(d: date) -> date:
    """Get the end of the week for a given date."""
    return get_week_start(d) + timedelta(days=6)


def get_week_range(d: date) -> tuple[date, date]:
    """Get the start and end of the week for a given date."""
    return get_week_start(d), get_week_end(d)


def format_date(d: date) -> str:
    """Format a date for display."""
    return d.strftime("%d %b %Y")


def format_date_short(d: date) -> str:
    """Format a date in short form."""
    return d.strftime("%d/%m")


def format_datetime(dt: datetime) -> str:
    """Format a datetime for display."""
    return dt.strftime("%d %b %Y %H:%M")


def get_weekday_name(d: date) -> str:
    """Get the weekday name for a date."""
    return d.strftime("%A")


def get_weekday_short(d: date) -> str:
    """Get the short weekday name for a date."""
    return d.strftime("%a")


def days_between(d1: date, d2: date) -> int:
    """Get the number of days between two dates."""
    return abs((d2 - d1).days)


def get_date_range(start: date, end: date) -> list[date]:
    """Get all dates in a range (inclusive)."""
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


def get_same_weekday_dates(start: date, end: date, weekday: int) -> list[date]:
    """Get all dates of a specific weekday within a range."""
    dates = []
    current = start
    while current <= end:
        if current.weekday() == weekday:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def is_within_edit_window(entered_at: datetime) -> bool:
    """Check if an entry is within the edit window."""
    edit_window = int(get_setting('edit_window_hours', '2'))
    cutoff = datetime.utcnow() - timedelta(hours=edit_window)
    return entered_at >= cutoff
