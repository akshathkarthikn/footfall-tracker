"""
Footfall Tracker - Mobile-First Application

Staff log in with their floor assignment and only see what they need.
Clean, fast, phone-friendly interface.
"""

import streamlit as st
from datetime import date, datetime
from config import APP_NAME
from database.db import init_database, get_db_session
from database.models import User, Floor
from auth.auth import (
    is_authenticated, get_current_user, logout, verify_password
)
from services.entry_service import get_entry, save_entry, get_entries_for_date
from utils.datetime_utils import get_hour_slots, format_hour_slot, get_current_hour_slot

# Page config - mobile optimized
st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_database()

# Mobile-first CSS
st.markdown("""
<style>
    /* Hide Streamlit extras */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Mobile-first base */
    .main .block-container {
        padding: 1rem 1rem 4rem 1rem;
        max-width: 100%;
    }

    /* Large touch-friendly inputs */
    .stNumberInput input {
        font-size: 24px !important;
        height: 60px !important;
        text-align: center !important;
        border-radius: 12px !important;
    }

    .stTextInput input {
        font-size: 18px !important;
        height: 50px !important;
        border-radius: 12px !important;
    }

    /* Big buttons */
    .stButton > button {
        width: 100%;
        height: 56px;
        font-size: 18px !important;
        font-weight: 600;
        border-radius: 12px !important;
        margin: 0.25rem 0;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #EA580C 0%, #DC2626 100%);
        border: none;
    }

    /* Hour selector cards */
    .hour-card {
        background: #f8f8f8;
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 2px solid transparent;
    }

    .hour-card.current {
        border-color: #EA580C;
        background: #fff7ed;
    }

    .hour-card.filled {
        background: #f0fdf4;
        border-color: #22c55e;
    }

    /* Floor badge */
    .floor-badge {
        background: linear-gradient(135deg, #EA580C 0%, #DC2626 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 24px;
        font-size: 14px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
    }

    /* Stats cards */
    .stat-card {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        margin: 0.5rem 0;
    }

    .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #1a1a1a;
    }

    .stat-label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Success animation */
    .success-msg {
        background: #22c55e;
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 600;
        animation: pulse 0.5s ease;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    /* Login screen */
    .login-container {
        max-width: 320px;
        margin: 2rem auto;
        padding: 2rem;
    }

    .app-logo {
        font-size: 48px;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .app-title {
        font-size: 24px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        color: #1a1a1a;
    }

    /* Hide sidebar on mobile */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        font-size: 18px !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
    }

    .stTabs [data-baseweb="tab"] {
        flex: 1;
        justify-content: center;
        font-size: 14px;
        padding: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    if not is_authenticated():
        show_login()
    else:
        user = get_current_user()
        if user['role'] == 'admin':
            show_admin_view()
        else:
            show_floor_entry_view()


def show_login():
    """Clean mobile login screen."""
    st.markdown('<div class="app-logo">📊</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">Footfall Tracker</div>', unsafe_allow_html=True)

    # Get floors for selection
    with get_db_session() as db:
        floors = db.query(Floor).filter(Floor.active == True).order_by(Floor.display_order).all()
        floor_options = {f.floor_id: f.floor_name for f in floors}

    # Login type selection
    login_type = st.radio(
        "I am",
        ["Floor Staff", "Admin"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if login_type == "Floor Staff":
        # Floor selection for staff
        selected_floor = st.selectbox(
            "Select your floor",
            options=list(floor_options.keys()),
            format_func=lambda x: floor_options[x]
        )

        pin = st.text_input("Enter PIN", type="password", max_chars=6)

        if st.button("Start Entry", type="primary"):
            # Simple PIN auth for floor staff
            if pin == "1234":  # Default PIN, should be configurable
                st.session_state['authenticated'] = True
                st.session_state['user'] = {
                    'user_id': 0,
                    'username': f'floor_{selected_floor}',
                    'role': 'entry',
                    'full_name': floor_options[selected_floor],
                    'floor_id': selected_floor,
                    'floor_name': floor_options[selected_floor]
                }
                st.rerun()
            else:
                st.error("Invalid PIN")
    else:
        # Admin login
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary"):
            with get_db_session() as db:
                user = db.query(User).filter(
                    User.username == username,
                    User.active == True
                ).first()

                if user and verify_password(password, user.password_hash):
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = {
                        'user_id': user.user_id,
                        'username': user.username,
                        'role': user.role,
                        'full_name': user.full_name
                    }
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    st.markdown("---")
    st.caption("Default PIN: 1234 | Admin: admin / admin123")


def show_floor_entry_view():
    """Streamlined entry view for floor staff - one floor only."""
    user = get_current_user()
    floor_id = user.get('floor_id')
    floor_name = user.get('floor_name')

    # Header with floor badge and logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="floor-badge">{floor_name}</div>', unsafe_allow_html=True)
    with col2:
        if st.button("↩️", help="Logout"):
            logout()
            st.rerun()

    today = date.today()
    current_hour = get_current_hour_slot()
    hour_slots = get_hour_slots()

    # Get existing entries for today
    entries = get_entries_for_date(today, floor_id)
    entries_by_hour = {e['hour_slot']: e['count'] for e in entries}

    # Today's stats
    total_today = sum(entries_by_hour.values())
    filled_hours = len(entries_by_hour)
    total_hours = len(hour_slots)

    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value">{total_today:,}</div>
                <div class="stat-label">Today</div>
            </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value">{filled_hours}/{total_hours}</div>
                <div class="stat-label">Hours Logged</div>
            </div>
        ''', unsafe_allow_html=True)
    with col3:
        last_entry = max(entries_by_hour.keys()) if entries_by_hour else None
        last_str = format_hour_slot(last_entry) if last_entry else "-"
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value" style="font-size:20px">{last_str}</div>
                <div class="stat-label">Last Entry</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("---")

    # Hour selection with big buttons
    st.markdown("### Select Hour")

    # Show hours in a 3-column grid
    cols = st.columns(3)
    selected_hour = st.session_state.get('selected_hour', current_hour)

    for i, hour in enumerate(hour_slots):
        with cols[i % 3]:
            existing_count = entries_by_hour.get(hour)
            is_current = hour == current_hour
            is_selected = hour == selected_hour

            # Button label
            label = format_hour_slot(hour)
            if existing_count is not None:
                label += f" ✓ ({existing_count})"
            if is_current:
                label += " ⏰"

            # Button type
            btn_type = "primary" if is_selected else "secondary"

            if st.button(label, key=f"hour_{hour}", type=btn_type, use_container_width=True):
                st.session_state['selected_hour'] = hour
                st.rerun()

    st.markdown("---")

    # Entry form for selected hour
    selected_hour = st.session_state.get('selected_hour', current_hour)
    existing_value = entries_by_hour.get(selected_hour)

    st.markdown(f"### Enter count for {format_hour_slot(selected_hour)}")

    # Big number input
    count = st.number_input(
        "Footfall count",
        min_value=0,
        max_value=10000,
        value=existing_value if existing_value else 0,
        step=1,
        label_visibility="collapsed"
    )

    # Quick add buttons
    st.markdown("**Quick add:**")
    quick_cols = st.columns(5)
    quick_values = [10, 25, 50, 100, 500]
    for i, val in enumerate(quick_values):
        with quick_cols[i]:
            if st.button(f"+{val}", key=f"quick_{val}"):
                st.session_state['quick_add'] = count + val
                st.rerun()

    # Apply quick add
    if 'quick_add' in st.session_state:
        count = st.session_state.pop('quick_add')

    # Save button
    if st.button("💾 Save Entry", type="primary", use_container_width=True):
        if count > 0:
            success, msg, was_update = save_entry(
                entry_date=today,
                hour_slot=selected_hour,
                floor_id=floor_id,
                count=count,
                user_id=user.get('user_id', 0)
            )
            if success:
                action = "Updated" if was_update else "Saved"
                st.markdown(f'<div class="success-msg">✓ {action}: {count} at {format_hour_slot(selected_hour)}</div>', unsafe_allow_html=True)
                st.balloons()
                # Move to next hour if available
                next_hour_idx = hour_slots.index(selected_hour) + 1 if selected_hour in hour_slots else 0
                if next_hour_idx < len(hour_slots):
                    st.session_state['selected_hour'] = hour_slots[next_hour_idx]
                st.rerun()
        else:
            st.warning("Enter a count greater than 0")


def show_admin_view():
    """Admin dashboard with all floors overview."""
    user = get_current_user()

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## Admin Dashboard")
    with col2:
        if st.button("Logout"):
            logout()
            st.rerun()

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Today", "📝 Entry", "📈 Reports", "⚙️ Settings"])

    with tab1:
        show_admin_dashboard()

    with tab2:
        show_admin_entry()

    with tab3:
        show_admin_reports()

    with tab4:
        show_admin_settings()


def show_admin_dashboard():
    """Today's overview for all floors."""
    from services.metrics_service import get_daily_total, get_floor_breakdown, get_hourly_trend
    from components.charts import create_hourly_trend_chart, create_floor_bar_chart

    today = date.today()

    # Total stats
    total = get_daily_total(today)
    breakdown = get_floor_breakdown(today)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Today", f"{total:,}")
    with col2:
        st.metric("Floors Active", len([v for v in breakdown.values() if v > 0]))

    # Floor breakdown
    st.markdown("### By Floor")
    if breakdown:
        for floor, count in sorted(breakdown.items()):
            pct = (count / total * 100) if total > 0 else 0
            st.progress(pct / 100, text=f"{floor}: {count:,} ({pct:.0f}%)")
    else:
        st.info("No entries yet today")

    # Hourly trend
    st.markdown("### Hourly Trend")
    hourly = get_hourly_trend(today)
    if hourly:
        fig = create_hourly_trend_chart(hourly, "")
        st.plotly_chart(fig, use_container_width=True)


def show_admin_entry():
    """Admin can enter for any floor."""
    from services.entry_service import get_floors

    floors = get_floors()
    floor_options = {f['floor_id']: f['floor_name'] for f in floors}

    col1, col2 = st.columns(2)
    with col1:
        selected_floor = st.selectbox(
            "Floor",
            options=list(floor_options.keys()),
            format_func=lambda x: floor_options[x]
        )
    with col2:
        entry_date = st.date_input("Date", value=date.today(), max_value=date.today())

    hour_slots = get_hour_slots()
    selected_hour = st.selectbox(
        "Hour",
        options=hour_slots,
        format_func=format_hour_slot,
        index=hour_slots.index(get_current_hour_slot()) if get_current_hour_slot() in hour_slots else 0
    )

    # Check existing
    existing = get_entry(entry_date, selected_hour, selected_floor)

    count = st.number_input(
        "Count",
        min_value=0,
        max_value=10000,
        value=existing['count'] if existing else 0
    )

    if st.button("Save", type="primary"):
        user = get_current_user()
        success, msg, _ = save_entry(
            entry_date=entry_date,
            hour_slot=selected_hour,
            floor_id=selected_floor,
            count=count,
            user_id=user['user_id']
        )
        if success:
            st.success(f"Saved: {count} for {floor_options[selected_floor]} at {format_hour_slot(selected_hour)}")


def show_admin_reports():
    """Export and comparison tools."""
    from services.export_service import export_to_csv
    from datetime import timedelta

    st.markdown("### Export Data")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date.today() - timedelta(days=7))
    with col2:
        end_date = st.date_input("To", value=date.today())

    if st.button("Download CSV", type="primary"):
        csv_data = export_to_csv(start_date, end_date)
        st.download_button(
            "📥 Download",
            data=csv_data,
            file_name=f"footfall_{start_date}_{end_date}.csv",
            mime="text/csv"
        )


def show_admin_settings():
    """Basic settings."""
    from database.db import get_setting, set_setting
    from services.entry_service import get_floors
    from auth.auth import get_all_users

    st.markdown("### Floors")
    floors = get_floors(active_only=False)
    for f in floors:
        status = "✓" if f['active'] else "✗"
        st.text(f"{status} {f['floor_name']}")

    st.markdown("### Users")
    users = get_all_users()
    for u in users:
        status = "✓" if u['active'] else "✗"
        st.text(f"{status} {u['username']} ({u['role']})")

    st.markdown("### Settings")
    st.text(f"Opening hour: {get_setting('opening_hour', '9')}")
    st.text(f"Closing hour: {get_setting('closing_hour', '21')}")

    st.markdown("---")
    st.caption("For full admin features, access from desktop browser")


if __name__ == "__main__":
    main()
