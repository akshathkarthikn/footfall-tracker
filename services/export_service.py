"""
Service for exporting data to CSV and Excel.
"""

import io
from datetime import date
import pandas as pd
from services.entry_service import get_entries_for_date_range, get_floors
from utils.datetime_utils import format_hour_slot


def export_to_csv(start_date: date, end_date: date, floor_ids: list = None) -> bytes:
    """
    Export footfall data to CSV.
    Returns CSV content as bytes.
    """
    df = _get_export_dataframe(start_date, end_date, floor_ids)

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    return buffer.getvalue()


def export_to_excel(start_date: date, end_date: date, floor_ids: list = None) -> bytes:
    """
    Export footfall data to Excel.
    Returns Excel content as bytes.
    """
    df = _get_export_dataframe(start_date, end_date, floor_ids)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Footfall Data')

        # Add summary sheet
        summary = _get_summary_dataframe(start_date, end_date, floor_ids)
        summary.to_excel(writer, index=False, sheet_name='Summary')

    buffer.seek(0)
    return buffer.getvalue()


def _get_export_dataframe(start_date: date, end_date: date, floor_ids: list = None) -> pd.DataFrame:
    """Create DataFrame for export."""
    entries = get_entries_for_date_range(start_date, end_date)
    floors = get_floors(active_only=False)
    floor_names = {f['floor_id']: f['floor_name'] for f in floors}

    if floor_ids:
        entries = [e for e in entries if e['floor_id'] in floor_ids]

    records = []
    for entry in entries:
        records.append({
            'Date': entry['date'].strftime('%Y-%m-%d'),
            'Weekday': entry['date'].strftime('%A'),
            'Hour': format_hour_slot(entry['hour_slot']),
            'Hour (24h)': entry['hour_slot'],
            'Floor': floor_names.get(entry['floor_id'], f"Floor {entry['floor_id']}"),
            'Count': entry['count'],
            'Source': entry['source'],
            'Notes': entry['notes'] or ''
        })

    return pd.DataFrame(records)


def _get_summary_dataframe(start_date: date, end_date: date, floor_ids: list = None) -> pd.DataFrame:
    """Create summary DataFrame for export."""
    entries = get_entries_for_date_range(start_date, end_date)
    floors = get_floors(active_only=False)
    floor_names = {f['floor_id']: f['floor_name'] for f in floors}

    if floor_ids:
        entries = [e for e in entries if e['floor_id'] in floor_ids]

    # Aggregate by date
    from collections import defaultdict
    daily_totals = defaultdict(int)
    floor_totals = defaultdict(int)

    for entry in entries:
        daily_totals[entry['date']] += entry['count']
        floor_name = floor_names.get(entry['floor_id'], f"Floor {entry['floor_id']}")
        floor_totals[floor_name] += entry['count']

    # Create summary records
    total = sum(daily_totals.values())
    days = len(daily_totals) if daily_totals else 1
    avg_daily = total / days if days > 0 else 0

    records = [
        {'Metric': 'Date Range', 'Value': f"{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"},
        {'Metric': 'Total Footfall', 'Value': total},
        {'Metric': 'Days with Data', 'Value': len(daily_totals)},
        {'Metric': 'Average Daily', 'Value': round(avg_daily, 0)},
        {'Metric': '', 'Value': ''},
        {'Metric': 'By Floor', 'Value': ''},
    ]

    for floor_name, floor_total in sorted(floor_totals.items()):
        pct = (floor_total / total * 100) if total > 0 else 0
        records.append({
            'Metric': f'  {floor_name}',
            'Value': f"{floor_total} ({pct:.1f}%)"
        })

    return pd.DataFrame(records)


def generate_missing_entries_report(start_date: date, end_date: date) -> pd.DataFrame:
    """Generate a report of missing entries."""
    from datetime import timedelta
    from services.entry_service import get_missing_slots
    from utils.datetime_utils import format_date

    all_missing = []
    current = start_date
    while current <= end_date:
        missing = get_missing_slots(current)
        for m in missing:
            all_missing.append({
                'Date': format_date(current),
                'Floor': m['floor_name'],
                'Hour': format_hour_slot(m['hour_slot'])
            })
        current += timedelta(days=1)

    return pd.DataFrame(all_missing)
