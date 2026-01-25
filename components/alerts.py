"""
Alert and warning components.
"""

import streamlit as st
from utils.datetime_utils import format_hour_slot


def show_missing_slots_warning(missing_slots: list):
    """Display warning about missing entry slots."""
    if not missing_slots:
        return

    # Group by floor
    by_floor = {}
    for slot in missing_slots:
        floor_name = slot['floor_name']
        if floor_name not in by_floor:
            by_floor[floor_name] = []
        by_floor[floor_name].append(format_hour_slot(slot['hour_slot']))

    # Build warning message
    warnings = []
    for floor, hours in by_floor.items():
        hours_str = ', '.join(hours[:5])
        if len(hours) > 5:
            hours_str += f" (+{len(hours) - 5} more)"
        warnings.append(f"**{floor}**: {hours_str}")

    with st.expander(f"Missing {len(missing_slots)} entries", expanded=True):
        for w in warnings:
            st.markdown(f"- {w}")


def show_spike_warning(floor_name: str, hour: int, new_count: int,
                        previous_count: int, percent_change: float) -> bool:
    """
    Show a spike detection warning and get user confirmation.
    Returns True if user confirms, False otherwise.
    """
    st.warning(
        f"Unusual value detected for **{floor_name}** at **{format_hour_slot(hour)}**:\n\n"
        f"- New value: **{new_count}**\n"
        f"- Previous hour: **{previous_count}**\n"
        f"- Change: **{percent_change:+.1f}%**"
    )

    return st.checkbox(
        f"Confirm this value is correct for {floor_name} at {format_hour_slot(hour)}",
        key=f"spike_confirm_{floor_name}_{hour}"
    )


def show_overwrite_warning(existing_entries: list) -> bool:
    """
    Show warning about existing entries that will be overwritten.
    Returns True if user confirms.
    """
    if not existing_entries:
        return True

    st.warning(
        f"**{len(existing_entries)} existing entries will be updated.**\n\n"
        "Saving will overwrite the current values. All changes are logged."
    )

    return st.checkbox(
        "I understand and want to update these entries",
        key="overwrite_confirm"
    )


def show_success_message(saved: int, updated: int):
    """Show success message after saving entries."""
    if saved > 0 and updated > 0:
        st.success(f"Saved {saved} new entries and updated {updated} existing entries.")
    elif saved > 0:
        st.success(f"Saved {saved} new entries.")
    elif updated > 0:
        st.success(f"Updated {updated} entries.")


def show_edit_restriction_warning():
    """Show warning when user cannot edit due to time restriction."""
    st.warning(
        "You can only edit entries from the last 2 hours. "
        "Contact an administrator to edit older entries."
    )


def show_validation_errors(errors: list):
    """Display validation errors."""
    if not errors:
        return

    st.error("Validation errors:")
    for error in errors:
        st.markdown(f"- {error}")
