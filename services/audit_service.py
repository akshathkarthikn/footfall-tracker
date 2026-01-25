"""
Audit logging service for tracking changes.
"""

from datetime import datetime
from database.db import get_db_session
from database.models import AuditLog


def log_change(table_name: str, record_id: int, action: str,
               old_value: dict, new_value: dict, user_id: int,
               ip_address: str = None):
    """
    Log a change to the audit log.

    Args:
        table_name: Name of the table being changed
        record_id: ID of the record being changed
        action: 'INSERT', 'UPDATE', or 'DELETE'
        old_value: Dictionary of old values (None for INSERT)
        new_value: Dictionary of new values (None for DELETE)
        user_id: ID of the user making the change
        ip_address: Optional IP address of the user
    """
    with get_db_session() as db:
        log_entry = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_by=user_id,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()


def get_audit_logs(table_name: str = None, record_id: int = None,
                   start_date: datetime = None, end_date: datetime = None,
                   user_id: int = None, limit: int = 100) -> list[dict]:
    """
    Get audit logs with optional filters.
    """
    with get_db_session() as db:
        query = db.query(AuditLog)

        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if record_id:
            query = query.filter(AuditLog.record_id == record_id)
        if start_date:
            query = query.filter(AuditLog.changed_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.changed_at <= end_date)
        if user_id:
            query = query.filter(AuditLog.changed_by == user_id)

        logs = query.order_by(AuditLog.changed_at.desc()).limit(limit).all()

        return [
            {
                'log_id': log.log_id,
                'table_name': log.table_name,
                'record_id': log.record_id,
                'action': log.action,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'changed_by': log.changed_by,
                'changed_at': log.changed_at,
                'ip_address': log.ip_address
            }
            for log in logs
        ]


def get_entry_history(entry_id: int) -> list[dict]:
    """Get all audit log entries for a specific footfall entry."""
    return get_audit_logs(table_name='footfall_entries', record_id=entry_id, limit=1000)
