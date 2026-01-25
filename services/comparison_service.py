"""
Service for comparing footfall data across different time periods.
"""

from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
from services.entry_service import get_entries_for_date, get_entries_for_date_range, get_floors
from services.metrics_service import get_daily_total, get_hourly_trend, get_floor_breakdown
from utils.datetime_utils import get_hour_slots, format_hour_slot, get_weekday_name


def compare_days(date1: date, date2: date, floor_ids: list = None) -> pd.DataFrame:
    """
    Compare two days side by side.
    Returns a DataFrame with hourly comparison.
    """
    hours = get_hour_slots()
    floors = get_floors()
    floor_names = {f['floor_id']: f['floor_name'] for f in floors}

    if floor_ids:
        floors = [f for f in floors if f['floor_id'] in floor_ids]

    entries1 = get_entries_for_date(date1)
    entries2 = get_entries_for_date(date2)

    # Create lookup dictionaries
    lookup1 = {(e['hour_slot'], e['floor_id']): e['count'] for e in entries1}
    lookup2 = {(e['hour_slot'], e['floor_id']): e['count'] for e in entries2}

    rows = []
    for hour in hours:
        row = {
            'Hour': format_hour_slot(hour),
            f'{date1.strftime("%d %b")}': sum(lookup1.get((hour, f['floor_id']), 0) for f in floors),
            f'{date2.strftime("%d %b")}': sum(lookup2.get((hour, f['floor_id']), 0) for f in floors),
        }

        # Calculate change
        if row[f'{date2.strftime("%d %b")}'] > 0:
            change = ((row[f'{date1.strftime("%d %b")}'] - row[f'{date2.strftime("%d %b")}']) /
                      row[f'{date2.strftime("%d %b")}']) * 100
            row['Change %'] = f"{change:+.1f}%"
        else:
            row['Change %'] = "N/A"

        rows.append(row)

    # Add totals row
    total1 = sum(r[f'{date1.strftime("%d %b")}'] for r in rows)
    total2 = sum(r[f'{date2.strftime("%d %b")}'] for r in rows)
    if total2 > 0:
        total_change = ((total1 - total2) / total2) * 100
        change_str = f"{total_change:+.1f}%"
    else:
        change_str = "N/A"

    rows.append({
        'Hour': 'TOTAL',
        f'{date1.strftime("%d %b")}': total1,
        f'{date2.strftime("%d %b")}': total2,
        'Change %': change_str
    })

    return pd.DataFrame(rows)


def compare_weeks(week1_start: date, week2_start: date, floor_ids: list = None) -> pd.DataFrame:
    """
    Compare two weeks side by side.
    Returns a DataFrame with daily comparison.
    """
    week1_end = week1_start + timedelta(days=6)
    week2_end = week2_start + timedelta(days=6)

    floors = get_floors()
    if floor_ids:
        floors = [f for f in floors if f['floor_id'] in floor_ids]
    floor_id_set = {f['floor_id'] for f in floors}

    entries1 = get_entries_for_date_range(week1_start, week1_end)
    entries2 = get_entries_for_date_range(week2_start, week2_end)

    # Filter by floors
    entries1 = [e for e in entries1 if e['floor_id'] in floor_id_set]
    entries2 = [e for e in entries2 if e['floor_id'] in floor_id_set]

    # Aggregate by day
    daily1 = defaultdict(int)
    daily2 = defaultdict(int)

    for e in entries1:
        days_from_start = (e['date'] - week1_start).days
        daily1[days_from_start] += e['count']

    for e in entries2:
        days_from_start = (e['date'] - week2_start).days
        daily2[days_from_start] += e['count']

    rows = []
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for i, weekday in enumerate(weekdays):
        row = {
            'Day': weekday,
            f'Week of {week1_start.strftime("%d %b")}': daily1.get(i, 0),
            f'Week of {week2_start.strftime("%d %b")}': daily2.get(i, 0),
        }

        if daily2.get(i, 0) > 0:
            change = ((daily1.get(i, 0) - daily2.get(i, 0)) / daily2.get(i, 0)) * 100
            row['Change %'] = f"{change:+.1f}%"
        else:
            row['Change %'] = "N/A"

        rows.append(row)

    # Add totals row
    total1 = sum(daily1.values())
    total2 = sum(daily2.values())
    if total2 > 0:
        total_change = ((total1 - total2) / total2) * 100
        change_str = f"{total_change:+.1f}%"
    else:
        change_str = "N/A"

    rows.append({
        'Day': 'TOTAL',
        f'Week of {week1_start.strftime("%d %b")}': total1,
        f'Week of {week2_start.strftime("%d %b")}': total2,
        'Change %': change_str
    })

    return pd.DataFrame(rows)


def compare_same_weekday(start_date: date, end_date: date, weekday: int,
                          floor_ids: list = None) -> pd.DataFrame:
    """
    Compare the same weekday across a date range.
    weekday: 0=Monday, 6=Sunday
    """
    from utils.datetime_utils import get_same_weekday_dates

    dates = get_same_weekday_dates(start_date, end_date, weekday)

    floors = get_floors()
    if floor_ids:
        floors = [f for f in floors if f['floor_id'] in floor_ids]
    floor_id_set = {f['floor_id'] for f in floors}

    rows = []
    for d in dates:
        entries = get_entries_for_date(d)
        entries = [e for e in entries if e['floor_id'] in floor_id_set]
        total = sum(e['count'] for e in entries)

        rows.append({
            'Date': d.strftime("%d %b %Y"),
            'Total': total
        })

    # Calculate averages and trends
    if len(rows) >= 2:
        totals = [r['Total'] for r in rows]
        avg = sum(totals) / len(totals)

        for row in rows:
            if avg > 0:
                diff = ((row['Total'] - avg) / avg) * 100
                row['vs Avg'] = f"{diff:+.1f}%"
            else:
                row['vs Avg'] = "N/A"

    return pd.DataFrame(rows)


def get_comparison_summary(date1: date, date2: date) -> dict:
    """Get a summary comparison between two dates."""
    total1 = get_daily_total(date1)
    total2 = get_daily_total(date2)

    breakdown1 = get_floor_breakdown(date1)
    breakdown2 = get_floor_breakdown(date2)

    hourly1 = get_hourly_trend(date1)
    hourly2 = get_hourly_trend(date2)

    # Find peak hours
    peak1 = max(hourly1, key=hourly1.get) if hourly1 else None
    peak2 = max(hourly2, key=hourly2.get) if hourly2 else None

    # Calculate percent change
    if total2 > 0:
        percent_change = ((total1 - total2) / total2) * 100
    else:
        percent_change = 0.0

    return {
        'date1': date1,
        'date2': date2,
        'total1': total1,
        'total2': total2,
        'change': total1 - total2,
        'percent_change': round(percent_change, 1),
        'peak_hour1': peak1,
        'peak_hour2': peak2,
        'floor_breakdown1': breakdown1,
        'floor_breakdown2': breakdown2
    }
