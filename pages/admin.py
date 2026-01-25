"""
Admin page - Floor/User management, export, settings, and data QA tools.
"""

import streamlit as st
from datetime import date, datetime, timedelta
from database.db import get_db_session, get_setting, set_setting
from database.models import Floor, User, HolidayLabel, AuditLog
from auth.auth import (
    get_current_user_id, is_admin, create_user, update_user_password,
    get_all_users, hash_password
)
from auth.permissions import can_manage_floors, can_manage_users, can_export_data
from services.entry_service import get_floors
from services.export_service import export_to_csv, export_to_excel, generate_missing_entries_report
from services.audit_service import get_audit_logs
from utils.validators import validate_username, validate_password, validate_floor_name


def render_admin_page():
    """Render the Admin page."""
    st.title("Admin Panel")

    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        return

    # Admin tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Floors", "Users", "Settings", "Export", "Data QA", "Audit Log"
    ])

    with tab1:
        render_floors_management()

    with tab2:
        render_users_management()

    with tab3:
        render_settings_management()

    with tab4:
        render_export_tools()

    with tab5:
        render_data_qa_tools()

    with tab6:
        render_audit_log()


def render_floors_management():
    """Render floor management section."""
    st.markdown("### Manage Floors")

    # Add new floor
    with st.expander("Add New Floor", expanded=False):
        col1, col2 = st.columns([3, 1])

        with col1:
            new_floor_name = st.text_input("Floor Name", key="new_floor_name")
        with col2:
            new_floor_order = st.number_input("Order", min_value=1, value=1, key="new_floor_order")

        if st.button("Add Floor", key="add_floor"):
            is_valid, error = validate_floor_name(new_floor_name)
            if not is_valid:
                st.error(error)
            else:
                with get_db_session() as db:
                    existing = db.query(Floor).filter(Floor.floor_name == new_floor_name).first()
                    if existing:
                        st.error("A floor with this name already exists.")
                    else:
                        new_floor = Floor(
                            floor_name=new_floor_name,
                            display_order=new_floor_order,
                            active=True
                        )
                        db.add(new_floor)
                        db.commit()
                        st.success(f"Floor '{new_floor_name}' added successfully!")
                        st.rerun()

    st.markdown("---")

    # List existing floors
    floors = get_floors(active_only=False)

    for floor in floors:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"**{floor['floor_name']}**")
                status = "Active" if floor['active'] else "Inactive"
                st.caption(f"Order: {floor['display_order']} | Status: {status}")

            with col2:
                new_order = st.number_input(
                    "Order",
                    min_value=1,
                    value=floor['display_order'],
                    key=f"order_{floor['floor_id']}",
                    label_visibility="collapsed"
                )
                if new_order != floor['display_order']:
                    with get_db_session() as db:
                        f = db.query(Floor).filter(Floor.floor_id == floor['floor_id']).first()
                        if f:
                            f.display_order = new_order
                            db.commit()
                            st.rerun()

            with col3:
                if floor['active']:
                    if st.button("Deactivate", key=f"deact_{floor['floor_id']}"):
                        with get_db_session() as db:
                            f = db.query(Floor).filter(Floor.floor_id == floor['floor_id']).first()
                            if f:
                                f.active = False
                                db.commit()
                                st.rerun()
                else:
                    if st.button("Activate", key=f"act_{floor['floor_id']}"):
                        with get_db_session() as db:
                            f = db.query(Floor).filter(Floor.floor_id == floor['floor_id']).first()
                            if f:
                                f.active = True
                                db.commit()
                                st.rerun()

            st.markdown("---")


def render_users_management():
    """Render user management section."""
    st.markdown("### Manage Users")

    # Add new user
    with st.expander("Add New User", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", type="password", key="new_password")

        with col2:
            new_full_name = st.text_input("Full Name", key="new_full_name")
            new_role = st.selectbox("Role", options=["entry", "admin"], key="new_role")

        if st.button("Create User", key="create_user"):
            valid_user, user_error = validate_username(new_username)
            valid_pass, pass_error = validate_password(new_password)

            if not valid_user:
                st.error(user_error)
            elif not valid_pass:
                st.error(pass_error)
            else:
                success = create_user(new_username, new_password, new_role, new_full_name)
                if success:
                    st.success(f"User '{new_username}' created successfully!")
                    st.rerun()
                else:
                    st.error("Username already exists.")

    st.markdown("---")

    # List existing users
    users = get_all_users()

    for user in users:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                status_emoji = "" if user['active'] else " (Inactive)"
                st.markdown(f"**{user['username']}**{status_emoji}")
                st.caption(f"{user['full_name'] or 'No name'} | Role: {user['role'].title()}")
                if user['last_login']:
                    st.caption(f"Last login: {user['last_login'].strftime('%d %b %Y %H:%M')}")

            with col2:
                # Reset password
                new_pass = st.text_input(
                    "New Password",
                    type="password",
                    key=f"reset_pass_{user['user_id']}",
                    label_visibility="collapsed",
                    placeholder="New password"
                )
                if new_pass and st.button("Reset", key=f"reset_btn_{user['user_id']}"):
                    if len(new_pass) >= 4:
                        update_user_password(user['user_id'], new_pass)
                        st.success("Password updated!")
                    else:
                        st.error("Password too short")

            with col3:
                if user['active']:
                    if st.button("Deactivate", key=f"deact_user_{user['user_id']}"):
                        with get_db_session() as db:
                            u = db.query(User).filter(User.user_id == user['user_id']).first()
                            if u:
                                u.active = False
                                db.commit()
                                st.rerun()
                else:
                    if st.button("Activate", key=f"act_user_{user['user_id']}"):
                        with get_db_session() as db:
                            u = db.query(User).filter(User.user_id == user['user_id']).first()
                            if u:
                                u.active = True
                                db.commit()
                                st.rerun()

            st.markdown("---")


def render_settings_management():
    """Render settings section."""
    st.markdown("### Application Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Operating Hours")

        opening_hour = st.number_input(
            "Opening Hour",
            min_value=0,
            max_value=23,
            value=int(get_setting('opening_hour', '9')),
            key="opening_hour"
        )

        closing_hour = st.number_input(
            "Closing Hour",
            min_value=0,
            max_value=23,
            value=int(get_setting('closing_hour', '21')),
            key="closing_hour"
        )

    with col2:
        st.markdown("#### Validation Settings")

        spike_threshold = st.number_input(
            "Spike Threshold (%)",
            min_value=10,
            max_value=200,
            value=int(get_setting('spike_threshold_percent', '50')),
            key="spike_threshold",
            help="Warn if count exceeds previous hour by this percentage"
        )

        max_value = st.number_input(
            "Max Footfall Value",
            min_value=100,
            max_value=100000,
            value=int(get_setting('max_footfall_value', '10000')),
            key="max_value"
        )

        edit_window = st.number_input(
            "Edit Window (hours)",
            min_value=1,
            max_value=24,
            value=int(get_setting('edit_window_hours', '2')),
            key="edit_window",
            help="Entry users can only edit entries within this window"
        )

    if st.button("Save Settings", type="primary"):
        user_id = get_current_user_id()
        set_setting('opening_hour', str(opening_hour), user_id)
        set_setting('closing_hour', str(closing_hour), user_id)
        set_setting('spike_threshold_percent', str(spike_threshold), user_id)
        set_setting('max_footfall_value', str(max_value), user_id)
        set_setting('edit_window_hours', str(edit_window), user_id)
        st.success("Settings saved!")

    st.markdown("---")

    # Holiday labels
    st.markdown("### Holiday Labels")

    with st.expander("Add Holiday Label", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            holiday_date = st.date_input("Date", key="holiday_date")
            holiday_label = st.text_input("Label (e.g., Diwali)", key="holiday_label")
        with col2:
            holiday_desc = st.text_area("Description (optional)", key="holiday_desc")

        if st.button("Add Holiday"):
            if holiday_label:
                with get_db_session() as db:
                    existing = db.query(HolidayLabel).filter(HolidayLabel.date == holiday_date).first()
                    if existing:
                        existing.label = holiday_label
                        existing.description = holiday_desc
                    else:
                        db.add(HolidayLabel(
                            date=holiday_date,
                            label=holiday_label,
                            description=holiday_desc
                        ))
                    db.commit()
                st.success("Holiday label saved!")
                st.rerun()

    # List existing holidays
    with get_db_session() as db:
        holidays = db.query(HolidayLabel).order_by(HolidayLabel.date.desc()).limit(20).all()

        if holidays:
            for h in holidays:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{h.date.strftime('%d %b %Y')}**: {h.label}")
                with col2:
                    if st.button("Delete", key=f"del_holiday_{h.id}"):
                        db.delete(h)
                        db.commit()
                        st.rerun()


def render_export_tools():
    """Render export section."""
    st.markdown("### Export Data")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "From Date",
            value=date.today() - timedelta(days=30),
            key="export_start"
        )

    with col2:
        end_date = st.date_input(
            "To Date",
            value=date.today(),
            max_value=date.today(),
            key="export_end"
        )

    # Floor filter
    floors = get_floors(active_only=False)
    floor_options = {f['floor_id']: f['floor_name'] for f in floors}

    selected_floors = st.multiselect(
        "Floors (leave empty for all)",
        options=list(floor_options.keys()),
        format_func=lambda x: floor_options[x],
        key="export_floors"
    )

    floor_ids = selected_floors if selected_floors else None

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export CSV", use_container_width=True):
            csv_data = export_to_csv(start_date, end_date, floor_ids)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"footfall_{start_date}_{end_date}.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("Export Excel", use_container_width=True):
            excel_data = export_to_excel(start_date, end_date, floor_ids)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name=f"footfall_{start_date}_{end_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


def render_data_qa_tools():
    """Render data quality tools."""
    st.markdown("### Data Quality Tools")

    # Missing entries report
    st.markdown("#### Missing Entries Report")

    col1, col2 = st.columns(2)

    with col1:
        qa_start = st.date_input(
            "From",
            value=date.today() - timedelta(days=7),
            key="qa_start"
        )

    with col2:
        qa_end = st.date_input(
            "To",
            value=date.today(),
            key="qa_end"
        )

    if st.button("Generate Report"):
        missing_df = generate_missing_entries_report(qa_start, qa_end)

        if missing_df.empty:
            st.success("No missing entries found!")
        else:
            st.warning(f"Found {len(missing_df)} missing entries")
            st.dataframe(missing_df, use_container_width=True)

            csv = missing_df.to_csv(index=False)
            st.download_button(
                "Download Report",
                data=csv,
                file_name=f"missing_entries_{qa_start}_{qa_end}.csv",
                mime="text/csv"
            )


def render_audit_log():
    """Render audit log viewer."""
    st.markdown("### Audit Log")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        audit_start = st.date_input(
            "From Date",
            value=date.today() - timedelta(days=7),
            key="audit_start"
        )

    with col2:
        audit_end = st.date_input(
            "To Date",
            value=date.today(),
            key="audit_end"
        )

    with col3:
        table_filter = st.selectbox(
            "Table",
            options=["All", "footfall_entries", "floors", "users", "settings"],
            key="audit_table"
        )

    # Get logs
    logs = get_audit_logs(
        table_name=None if table_filter == "All" else table_filter,
        start_date=datetime.combine(audit_start, datetime.min.time()),
        end_date=datetime.combine(audit_end, datetime.max.time()),
        limit=100
    )

    if logs:
        for log in logs:
            with st.expander(
                f"{log['changed_at'].strftime('%d %b %H:%M')} - {log['action']} on {log['table_name']}"
            ):
                st.json({
                    'action': log['action'],
                    'table': log['table_name'],
                    'record_id': log['record_id'],
                    'old_value': log['old_value'],
                    'new_value': log['new_value'],
                    'user_id': log['changed_by']
                })
    else:
        st.info("No audit log entries found for the selected filters.")


def render_admin_sidebar():
    """Render admin sidebar."""
    st.sidebar.markdown("### Admin Quick Actions")

    if st.sidebar.button("Refresh Data"):
        st.rerun()

    st.sidebar.markdown("---")

    # Database info
    st.sidebar.markdown("### Database Info")
    import os
    from config import DATA_DIR

    db_path = os.path.join(DATA_DIR, 'footfall.db')
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        size_mb = size / (1024 * 1024)
        st.sidebar.caption(f"Database size: {size_mb:.2f} MB")
