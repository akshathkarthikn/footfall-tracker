"""
Service for calculating footfall metrics and aggregations.
"""

from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
from database.db import get_db_session
from database.models import FootfallEntry, Floor
from services.entry_service import get_entries_for_date, get_entries_for_date_range, get_floors


def get_daily_total(entry_date: date, floor_id: int = None) -> int:
    """Get the total footfall for a date, optionally by floor."""
    entries = get_entries_for_date(entry_date, floor_id)
    return sum(e['count'] for e in entries)


def get_floor_breakdown(entry_date: date) -> dict:
    """Get footfall totals per floor for a date."""
    entries = get_entries_for_date(entry_date)
    floors = get_floors()

    # Create floor name lookup
    floor_names = {f['floor_id']: f['floor_name'] for f in floors}

    # Sum by floor
    breakdown = defaultdict(int)
    for entry in entries:
        floor_name = floor_names.get(entry['floor_id'], f"Floor {entry['floor_id']}")
        breakdown[floor_name] += entry['count']

    return dict(breakdown)


def get_hourly_trend(entry_date: date, floor_id: int = None) -> dict:
    """Get hour-by-hour footfall for a date."""
    entries = get_entries_for_date(entry_date, floor_id)

    # Sum by hour
    hourly = defaultdict(int)
    for entry in entries:
        hourly[entry['hour_slot']] += entry['count']

    return dict(hourly)


def get_peak_hour(entry_date: date) -> tuple:
    """Get the peak hour and count for a date."""
    hourly = get_hourly_trend(entry_date)
    if not hourly:
        return None, 0

    peak_hour = max(hourly, key=hourly.get)
    return peak_hour, hourly[peak_hour]


def get_floor_share_percent(entry_date: date) -> dict:
    """Get floor contribution as percentages for a date."""
    breakdown = get_floor_breakdown(entry_date)
    total = sum(breakdown.values())

    if total == 0:
        return {floor: 0.0 for floor in breakdown}

    return {
        floor: round((count / total) * 100, 1)
        for floor, count in breakdown.items()
    }


def get_delta_vs_yesterday(entry_date: date) -> dict:
    """
    Compare today's footfall to yesterday's.
    Returns metrics with delta calculations.
    """
    yesterday = entry_date - timedelta(days=1)

    today_total = get_daily_total(entry_date)
    yesterday_total = get_daily_total(yesterday)

    if yesterday_total == 0:
        percent_change = 0.0
    else:
        percent_change = ((today_total - yesterday_total) / yesterday_total) * 100

    today_hourly = get_hourly_trend(entry_date)
    yesterday_hourly = get_hourly_trend(yesterday)

    # Compare current hour
    from datetime import datetime
    current_hour = datetime.now().hour

    today_at_hour = sum(v for k, v in today_hourly.items() if k <= current_hour)
    yesterday_at_hour = sum(v for k, v in yesterday_hourly.items() if k <= current_hour)

    if yesterday_at_hour == 0:
        hour_percent_change = 0.0
    else:
        hour_percent_change = ((today_at_hour - yesterday_at_hour) / yesterday_at_hour) * 100

    return {
        'today_total': today_total,
        'yesterday_total': yesterday_total,
        'total_change': today_total - yesterday_total,
        'total_percent_change': round(percent_change, 1),
        'today_at_hour': today_at_hour,
        'yesterday_at_hour': yesterday_at_hour,
        'hour_change': today_at_hour - yesterday_at_hour,
        'hour_percent_change': round(hour_percent_change, 1)
    }


def get_rolling_average(end_date: date, days: int = 7) -> dict:
    """Get rolling average footfall over a period."""
    start_date = end_date - timedelta(days=days - 1)
    entries = get_entries_for_date_range(start_date, end_date)

    # Sum by date
    daily_totals = defaultdict(int)
    for entry in entries:
        daily_totals[entry['date']] += entry['count']

    # Calculate rolling average for each date
    result = {}
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        window_start = current_date - timedelta(days=days - 1)

        # Get average of available days in window
        window_values = [
            daily_totals.get(window_start + timedelta(days=j), 0)
            for j in range(days)
            if window_start + timedelta(days=j) <= current_date
        ]

        if window_values:
            result[current_date] = sum(window_values) / len(window_values)
        else:
            result[current_date] = 0

    return result


def get_monthly_totals(year: int) -> dict:
    """Get monthly footfall totals for a year."""
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    entries = get_entries_for_date_range(start_date, end_date)

    monthly = defaultdict(int)
    for entry in entries:
        month_key = entry['date'].strftime('%Y-%m')
        monthly[month_key] += entry['count']

    return dict(monthly)


def get_weekday_hour_heatmap(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Get a heatmap of average footfall by weekday and hour.
    Returns a DataFrame with weekdays as rows and hours as columns.
    """
    entries = get_entries_for_date_range(start_date, end_date)

    # Aggregate by weekday and hour
    data = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        weekday = entry['date'].weekday()  # 0=Monday
        hour = entry['hour_slot']
        data[weekday][hour].append(entry['count'])

    # Calculate averages
    weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    from utils.datetime_utils import get_hour_slots
    hours = get_hour_slots()

    heatmap_data = []
    for weekday in range(7):
        row = {'Weekday': weekday_names[weekday]}
        for hour in hours:
            values = data[weekday][hour]
            row[hour] = round(sum(values) / len(values), 0) if values else 0
        heatmap_data.append(row)

    return pd.DataFrame(heatmap_data)


def get_floor_trend_over_time(start_date: date, end_date: date) -> pd.DataFrame:
    """Get floor-wise totals over a date range."""
    entries = get_entries_for_date_range(start_date, end_date)
    floors = get_floors()
    floor_names = {f['floor_id']: f['floor_name'] for f in floors}

    # Aggregate by date and floor
    data = defaultdict(lambda: defaultdict(int))
    for entry in entries:
        floor_name = floor_names.get(entry['floor_id'], f"Floor {entry['floor_id']}")
        data[entry['date']][floor_name] += entry['count']

    # Convert to DataFrame
    records = []
    current = start_date
    while current <= end_date:
        row = {'Date': current}
        for floor in floors:
            row[floor['floor_name']] = data[current].get(floor['floor_name'], 0)
        records.append(row)
        current += timedelta(days=1)

    return pd.DataFrame(records)
