"""
Floor entry grid component for quick data entry.
"""

import streamlit as st
from datetime import date
from services.entry_service import get_floors, get_entries_for_date, get_previous_hour_count
from utils.datetime_utils import get_hour_slots, format_hour_slot, get_current_hour_slot
from utils.validators import validate_footfall_count, detect_spike


def render_entry_grid(entry_date: date, selected_floors: list = None) -> dict:
    """
    Render the entry grid and return entered values.

    Args:
        entry_date: Date for entries
        selected_floors: List of floor IDs to show (None for all)

    Returns:
        Dictionary of {(floor_id, hour_slot): count} for non-empty entries
    """
    floors = get_floors(active_only=True)
    if selected_floors:
        floors = [f for f in floors if f['floor_id'] in selected_floors]

    hour_slots = get_hour_slots()
    current_hour = get_current_hour_slot()

    # Get existing entries
    existing = get_entries_for_date(entry_date)
    existing_lookup = {(e['floor_id'], e['hour_slot']): e for e in existing}

    # Prepare the grid data
    entered_values = {}
    validation_issues = []
    spike_warnings = []

    # Create tabs for different time periods
    morning_hours = [h for h in hour_slots if h < 12]
    afternoon_hours = [h for h in hour_slots if 12 <= h < 17]
    evening_hours = [h for h in hour_slots if h >= 17]

    tab1, tab2, tab3 = st.tabs(["Morning", "Afternoon", "Evening"])

    def render_hour_section(hours: list, tab):
        with tab:
            if not hours:
                st.info("No hours in this period")
                return

            # Create column headers
            cols = st.columns([2] + [1] * len(hours))
            with cols[0]:
                st.markdown("**Floor**")
            for i, hour in enumerate(hours):
                with cols[i + 1]:
                    is_current = hour == current_hour and entry_date == date.today()
                    label = format_hour_slot(hour)
                    if is_current:
                        label = f"**{label}**"
                    st.markdown(label)

            # Render rows for each floor
            for floor in floors:
                cols = st.columns([2] + [1] * len(hours))

                with cols[0]:
                    st.markdown(f"**{floor['floor_name']}**")

                for i, hour in enumerate(hours):
                    with cols[i + 1]:
                        key = (floor['floor_id'], hour)
                        existing_entry = existing_lookup.get(key)
                        default_value = existing_entry['count'] if existing_entry else None

                        # Create input
                        value = st.number_input(
                            label=f"{floor['floor_name']} {format_hour_slot(hour)}",
                            min_value=0,
                            max_value=10000,
                            value=default_value,
                            step=1,
                            key=f"entry_{floor['floor_id']}_{hour}",
                            label_visibility="collapsed"
                        )

                        if value is not None and value > 0:
                            entered_values[key] = value

                            # Validate
                            is_valid, error = validate_footfall_count(value)
                            if not is_valid:
                                validation_issues.append(f"{floor['floor_name']} {format_hour_slot(hour)}: {error}")

                            # Check for spike
                            prev_count = get_previous_hour_count(entry_date, hour, floor['floor_id'])
                            if prev_count is not None and prev_count > 0:
                                is_spike, pct = detect_spike(value, prev_count)
                                if is_spike:
                                    spike_warnings.append({
                                        'floor_name': floor['floor_name'],
                                        'hour': hour,
                                        'new_count': value,
                                        'previous_count': prev_count,
                                        'percent_change': pct
                                    })

    render_hour_section(morning_hours, tab1)
    render_hour_section(afternoon_hours, tab2)
    render_hour_section(evening_hours, tab3)

    # Store validation issues and spike warnings in session state
    st.session_state['validation_issues'] = validation_issues
    st.session_state['spike_warnings'] = spike_warnings

    return entered_values


def render_compact_entry_form(entry_date: date) -> dict:
    """
    Render a compact form for single hour entry.
    Returns dictionary of {floor_id: count} for the selected hour.
    """
    floors = get_floors(active_only=True)
    hour_slots = get_hour_slots()
    current_hour = get_current_hour_slot()

    # Hour selector
    hour_options = {h: format_hour_slot(h) for h in hour_slots}
    default_hour = current_hour if current_hour in hour_slots else hour_slots[0]

    selected_hour = st.selectbox(
        "Hour",
        options=list(hour_options.keys()),
        format_func=lambda x: hour_options[x],
        index=hour_slots.index(default_hour) if default_hour in hour_slots else 0
    )

    # Get existing entries for this hour
    existing = get_entries_for_date(entry_date)
    existing_lookup = {e['floor_id']: e for e in existing if e['hour_slot'] == selected_hour}

    st.markdown("---")

    entered_values = {}

    # Two columns for floors
    cols = st.columns(2)
    for i, floor in enumerate(floors):
        with cols[i % 2]:
            existing_entry = existing_lookup.get(floor['floor_id'])
            default_value = existing_entry['count'] if existing_entry else None

            value = st.number_input(
                label=floor['floor_name'],
                min_value=0,
                max_value=10000,
                value=default_value,
                step=1,
                key=f"compact_{floor['floor_id']}_{selected_hour}"
            )

            if value is not None and value > 0:
                entered_values[floor['floor_id']] = value

    return {'hour': selected_hour, 'values': entered_values}
