"""
Service for managing footfall entries (CRUD operations).
"""

from datetime import date, datetime
from typing import Optional
from database.db import get_db_session
from database.models import FootfallEntry, Floor
from services.audit_service import log_change


def get_floors(active_only: bool = True) -> list[dict]:
    """Get all floors."""
    with get_db_session() as db:
        query = db.query(Floor)
        if active_only:
            query = query.filter(Floor.active == True)
        floors = query.order_by(Floor.display_order).all()
        return [
            {
                'floor_id': f.floor_id,
                'floor_name': f.floor_name,
                'display_order': f.display_order,
                'active': f.active
            }
            for f in floors
        ]


def get_entry(entry_date: date, hour_slot: int, floor_id: int) -> Optional[dict]:
    """Get a specific entry by date, hour, and floor."""
    with get_db_session() as db:
        entry = db.query(FootfallEntry).filter(
            FootfallEntry.date == entry_date,
            FootfallEntry.hour_slot == hour_slot,
            FootfallEntry.floor_id == floor_id
        ).first()

        if entry:
            return {
                'entry_id': entry.entry_id,
                'date': entry.date,
                'hour_slot': entry.hour_slot,
                'floor_id': entry.floor_id,
                'count': entry.count,
                'entered_by': entry.entered_by,
                'entered_at': entry.entered_at,
                'source': entry.source,
                'notes': entry.notes
            }
        return None


def get_entries_for_date(entry_date: date, floor_id: int = None) -> list[dict]:
    """Get all entries for a specific date, optionally filtered by floor."""
    with get_db_session() as db:
        query = db.query(FootfallEntry).filter(FootfallEntry.date == entry_date)
        if floor_id:
            query = query.filter(FootfallEntry.floor_id == floor_id)
        entries = query.order_by(FootfallEntry.hour_slot, FootfallEntry.floor_id).all()

        return [
            {
                'entry_id': e.entry_id,
                'date': e.date,
                'hour_slot': e.hour_slot,
                'floor_id': e.floor_id,
                'count': e.count,
                'entered_by': e.entered_by,
                'entered_at': e.entered_at,
                'source': e.source,
                'notes': e.notes
            }
            for e in entries
        ]


def get_entries_for_date_range(start_date: date, end_date: date,
                                floor_id: int = None) -> list[dict]:
    """Get all entries within a date range."""
    with get_db_session() as db:
        query = db.query(FootfallEntry).filter(
            FootfallEntry.date >= start_date,
            FootfallEntry.date <= end_date
        )
        if floor_id:
            query = query.filter(FootfallEntry.floor_id == floor_id)
        entries = query.order_by(FootfallEntry.date, FootfallEntry.hour_slot).all()

        return [
            {
                'entry_id': e.entry_id,
                'date': e.date,
                'hour_slot': e.hour_slot,
                'floor_id': e.floor_id,
                'count': e.count,
                'entered_by': e.entered_by,
                'entered_at': e.entered_at,
                'source': e.source,
                'notes': e.notes
            }
            for e in entries
        ]


def save_entry(entry_date: date, hour_slot: int, floor_id: int, count: int,
               user_id: int, notes: str = None, source: str = 'manual') -> tuple[bool, str, bool]:
    """
    Save or update an entry.
    Returns (success, message, was_update).
    """
    with get_db_session() as db:
        existing = db.query(FootfallEntry).filter(
            FootfallEntry.date == entry_date,
            FootfallEntry.hour_slot == hour_slot,
            FootfallEntry.floor_id == floor_id
        ).first()

        if existing:
            # Update existing entry
            old_value = {
                'count': existing.count,
                'notes': existing.notes,
                'entered_by': existing.entered_by,
                'entered_at': existing.entered_at.isoformat() if existing.entered_at else None
            }

            existing.count = count
            existing.notes = notes
            existing.entered_by = user_id
            existing.entered_at = datetime.utcnow()

            new_value = {
                'count': count,
                'notes': notes,
                'entered_by': user_id,
                'entered_at': existing.entered_at.isoformat()
            }

            db.commit()

            log_change(
                table_name='footfall_entries',
                record_id=existing.entry_id,
                action='UPDATE',
                old_value=old_value,
                new_value=new_value,
                user_id=user_id
            )

            return True, "Entry updated", True
        else:
            # Create new entry
            new_entry = FootfallEntry(
                date=entry_date,
                hour_slot=hour_slot,
                floor_id=floor_id,
                count=count,
                entered_by=user_id,
                source=source,
                notes=notes
            )
            db.add(new_entry)
            db.commit()

            log_change(
                table_name='footfall_entries',
                record_id=new_entry.entry_id,
                action='INSERT',
                old_value=None,
                new_value={
                    'date': entry_date.isoformat(),
                    'hour_slot': hour_slot,
                    'floor_id': floor_id,
                    'count': count,
                    'entered_by': user_id,
                    'notes': notes
                },
                user_id=user_id
            )

            return True, "Entry saved", False


def save_entries_bulk(entries: list[dict], user_id: int) -> tuple[int, int, list[str]]:
    """
    Save multiple entries at once.
    Returns (saved_count, updated_count, errors).
    """
    saved = 0
    updated = 0
    errors = []

    for entry in entries:
        try:
            success, msg, was_update = save_entry(
                entry_date=entry['date'],
                hour_slot=entry['hour_slot'],
                floor_id=entry['floor_id'],
                count=entry['count'],
                user_id=user_id,
                notes=entry.get('notes'),
                source=entry.get('source', 'manual')
            )
            if success:
                if was_update:
                    updated += 1
                else:
                    saved += 1
        except Exception as e:
            errors.append(f"Error saving entry for floor {entry['floor_id']}, hour {entry['hour_slot']}: {str(e)}")

    return saved, updated, errors


def delete_entry(entry_id: int, user_id: int) -> bool:
    """Delete an entry by ID."""
    with get_db_session() as db:
        entry = db.query(FootfallEntry).filter(FootfallEntry.entry_id == entry_id).first()
        if entry:
            old_value = {
                'date': entry.date.isoformat(),
                'hour_slot': entry.hour_slot,
                'floor_id': entry.floor_id,
                'count': entry.count
            }

            db.delete(entry)
            db.commit()

            log_change(
                table_name='footfall_entries',
                record_id=entry_id,
                action='DELETE',
                old_value=old_value,
                new_value=None,
                user_id=user_id
            )
            return True
        return False


def get_previous_hour_count(entry_date: date, hour_slot: int, floor_id: int) -> Optional[int]:
    """Get the count from the previous hour for spike detection."""
    if hour_slot == 0:
        return None

    entry = get_entry(entry_date, hour_slot - 1, floor_id)
    return entry['count'] if entry else None


def get_missing_slots(entry_date: date) -> list[dict]:
    """Get list of missing hour slots for a date."""
    from utils.datetime_utils import get_hour_slots

    floors = get_floors(active_only=True)
    hour_slots = get_hour_slots()
    entries = get_entries_for_date(entry_date)

    # Create set of existing (hour, floor_id) tuples
    existing = {(e['hour_slot'], e['floor_id']) for e in entries}

    missing = []
    for floor in floors:
        for hour in hour_slots:
            if (hour, floor['floor_id']) not in existing:
                missing.append({
                    'floor_id': floor['floor_id'],
                    'floor_name': floor['floor_name'],
                    'hour_slot': hour
                })

    return missing
