"""
Quick Entry page - Primary data entry interface.
"""

import streamlit as st
from datetime import date, datetime
from auth.auth import get_current_user_id, is_admin
from services.entry_service import (
    get_floors, get_entries_for_date, save_entries_bulk, get_missing_slots
)
from components.floor_grid import render_entry_grid, render_compact_entry_form
from components.alerts import (
    show_missing_slots_warning, show_overwrite_warning,
    show_success_message, show_validation_errors
)
from utils.datetime_utils import format_date, is_within_edit_window


def render_quick_entry_page():
    """Render the Quick Entry page."""
    st.title("Quick Entry")

    # Date selector
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        entry_date = st.date_input(
            "Date",
            value=date.today(),
            max_value=date.today()
        )

    with col2:
        floors = get_floors(active_only=True)
        floor_options = {f['floor_id']: f['floor_name'] for f in floors}
        selected_floors = st.multiselect(
            "Filter Floors",
            options=list(floor_options.keys()),
            format_func=lambda x: floor_options[x],
            default=list(floor_options.keys())
        )

    with col3:
        st.markdown("")  # Spacer
        st.markdown("")
        if st.button("Today", use_container_width=True):
            st.session_state['entry_date'] = date.today()
            st.rerun()

    # Check for missing slots
    missing = get_missing_slots(entry_date)
    if missing:
        filtered_missing = [m for m in missing if m['floor_id'] in selected_floors]
        if filtered_missing:
            show_missing_slots_warning(filtered_missing)

    st.markdown("---")

    # Entry mode toggle
    entry_mode = st.radio(
        "Entry Mode",
        options=["Full Grid", "Single Hour"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Notes field
    notes = st.text_input("Notes (optional)", placeholder="e.g., Rain, Sale event, Power cut...")

    st.markdown("---")

    if entry_mode == "Full Grid":
        entered_values = render_entry_grid(entry_date, selected_floors)
    else:
        compact_data = render_compact_entry_form(entry_date)
        entered_values = {
            (floor_id, compact_data['hour']): count
            for floor_id, count in compact_data['values'].items()
        }

    # Validation issues display
    if 'validation_issues' in st.session_state and st.session_state['validation_issues']:
        show_validation_errors(st.session_state['validation_issues'])

    st.markdown("---")

    # Existing entries check
    existing_entries = get_entries_for_date(entry_date)
    existing_keys = {(e['floor_id'], e['hour_slot']) for e in existing_entries}
    will_overwrite = [k for k in entered_values.keys() if k in existing_keys]

    # Overwrite warning
    overwrite_confirmed = True
    if will_overwrite:
        overwrite_confirmed = show_overwrite_warning(will_overwrite)

    # Save button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        save_disabled = not entered_values or (will_overwrite and not overwrite_confirmed)

        if st.button("Save All", type="primary", use_container_width=True, disabled=save_disabled):
            user_id = get_current_user_id()

            # Prepare entries for saving
            entries_to_save = []
            for (floor_id, hour_slot), count in entered_values.items():
                entries_to_save.append({
                    'date': entry_date,
                    'hour_slot': hour_slot,
                    'floor_id': floor_id,
                    'count': count,
                    'notes': notes if notes else None
                })

            # Save entries
            saved, updated, errors = save_entries_bulk(entries_to_save, user_id)

            if errors:
                show_validation_errors(errors)
            else:
                show_success_message(saved, updated)
                st.balloons()

                # Clear session state
                if 'validation_issues' in st.session_state:
                    del st.session_state['validation_issues']
                if 'spike_warnings' in st.session_state:
                    del st.session_state['spike_warnings']

    # Summary of what will be saved
    if entered_values:
        st.caption(f"{len(entered_values)} entries ready to save")
        if will_overwrite:
            st.caption(f"({len(will_overwrite)} existing entries will be updated)")


def render_quick_entry_sidebar():
    """Render sidebar content for Quick Entry page."""
    st.sidebar.markdown("### Quick Tips")
    st.sidebar.markdown("""
    - Tab through fields for fast entry
    - Values default to empty (0)
    - Existing entries shown in filled fields
    - Green confirmation appears after save
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Legend")
    st.sidebar.markdown("""
    - **Bold hour**: Current hour
    - Empty field: No data yet
    - Filled field: Has existing data
    """)
