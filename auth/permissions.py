"""
Role-based permission checks for the Footfall Tracker.
"""

from datetime import datetime, timedelta
from auth.auth import get_current_user, is_admin
from database.db import get_setting


def can_edit_entry(entry_entered_at: datetime) -> bool:
    """
    Check if the current user can edit an entry.
    - Admins can edit any entry.
    - Entry users can only edit entries within the edit window (default 2 hours).
    """
    if is_admin():
        return True

    # Get edit window from settings
    edit_window_hours = int(get_setting('edit_window_hours', '2'))
    cutoff_time = datetime.utcnow() - timedelta(hours=edit_window_hours)

    return entry_entered_at >= cutoff_time


def can_manage_floors() -> bool:
    """Check if the current user can manage floors."""
    return is_admin()


def can_manage_users() -> bool:
    """Check if the current user can manage users."""
    return is_admin()


def can_export_data() -> bool:
    """Check if the current user can export data."""
    return is_admin()


def can_view_audit_log() -> bool:
    """Check if the current user can view the audit log."""
    return is_admin()


def can_manage_settings() -> bool:
    """Check if the current user can manage settings."""
    return is_admin()


def can_manage_holidays() -> bool:
    """Check if the current user can manage holiday labels."""
    return is_admin()


def can_trigger_backup() -> bool:
    """Check if the current user can trigger a backup."""
    return is_admin()


def get_user_permissions() -> dict:
    """Get all permissions for the current user."""
    return {
        'edit_any_entry': is_admin(),
        'manage_floors': can_manage_floors(),
        'manage_users': can_manage_users(),
        'export_data': can_export_data(),
        'view_audit_log': can_view_audit_log(),
        'manage_settings': can_manage_settings(),
        'manage_holidays': can_manage_holidays(),
        'trigger_backup': can_trigger_backup(),
    }
