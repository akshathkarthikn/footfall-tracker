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

    /* Mobile-first base - ensure page is scrollable */
    .main .block-container {
        padding: 0.75rem 0.75rem 5rem 0.75rem !important;
        max-width: 100% !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* ============================================
       MOBILE SCROLL FIX
       Ensure page scrolls when keyboard is open
       ============================================ */

    /* Main container should always be scrollable */
    .main {
        overflow-y: auto !important;
        height: 100vh !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* Ensure the app view is scrollable */
    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* Fix for selectbox/dropdown popup - make it scrollable */
    [data-baseweb="popover"] {
        max-height: 50vh !important;
        overflow-y: auto !important;
    }

    [data-baseweb="menu"] {
        max-height: 40vh !important;
        overflow-y: auto !important;
    }

    /* Date input popup fix */
    [data-baseweb="calendar"] {
        max-height: 50vh !important;
        overflow-y: auto !important;
    }

    /* ============================================
       MOBILE RESPONSIVE COLUMNS
       Make all Streamlit column layouts work on mobile
       ============================================ */

    /* All horizontal blocks should handle small screens */
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }

    /* Column children should not have min-width that breaks mobile */
    [data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
    }

    /* Buttons in columns should fill available space */
    [data-testid="stHorizontalBlock"] .stButton > button {
        width: 100% !important;
        min-width: 0 !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* Large touch-friendly inputs */
    .stNumberInput input {
        font-size: 32px !important;
        height: 70px !important;
        line-height: 70px !important;
        text-align: center !important;
        border-radius: 12px !important;
        padding: 0 !important;
    }

    .stNumberInput [data-testid="stNumberInputContainer"] {
        width: 100% !important;
    }

    /* Number input stepper buttons larger for touch */
    .stNumberInput button {
        width: 50px !important;
        height: 70px !important;
    }

    .stTextInput input {
        font-size: 18px !important;
        height: 50px !important;
        line-height: 50px !important;
        border-radius: 12px !important;
        padding: 0 1rem !important;
    }

    /* Fix text vertical alignment in all inputs */
    input[type="text"], input[type="password"], input[type="number"] {
        display: flex !important;
        align-items: center !important;
    }

    /* Big buttons */
    .stButton > button {
        width: 100%;
        height: 48px;
        font-size: 15px !important;
        font-weight: 600;
        border-radius: 10px !important;
        margin: 0.15rem 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #EA580C 0%, #DC2626 100%);
        border: none;
        height: 56px;
        font-size: 18px !important;
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
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }

    /* Date badge */
    .date-badge {
        background: #f3f4f6;
        color: #374151;
        padding: 0.3rem 0.75rem;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        display: inline-block;
        cursor: pointer;
    }

    .date-badge.today {
        background: #dbeafe;
        color: #1d4ed8;
    }

    /* Stats cards - compact for mobile */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 0.6rem 0.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        margin: 0;
        min-height: 65px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .stat-value {
        font-size: 22px;
        font-weight: 700;
        color: #1a1a1a;
        line-height: 1.2;
    }

    .stat-label {
        font-size: 9px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-top: 0.2rem;
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

    /* Selectbox styling - scrollable dropdown */
    .stSelectbox > div > div {
        font-size: 18px !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        max-height: 50px !important;
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

    /* Divider spacing */
    hr {
        margin: 0.75rem 0 !important;
    }

    /* Section headers */
    h3 {
        font-size: 16px !important;
        margin-bottom: 0.5rem !important;
        margin-top: 0.25rem !important;
    }

    /* Radio buttons more touch-friendly */
    .stRadio > div {
        gap: 0.5rem !important;
    }

    .stRadio label {
        padding: 0.5rem 1rem !important;
    }

    /* Progress bars */
    .stProgress > div {
        height: 24px !important;
    }

    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
    }

    /* Reduce vertical spacing between elements */
    .element-container {
        margin-bottom: 0.25rem !important;
    }

    /* Reduce gap between vertical blocks */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }

    /* Make column gaps tighter on mobile */
    [data-testid="stHorizontalBlock"] {
        gap: 0.4rem !important;
    }

    /* Date input compact styling */
    .stDateInput > div > div {
        font-size: 14px !important;
    }

    .stDateInput input {
        height: 40px !important;
        font-size: 14px !important;
    }

    /* Dataframe/table styling for mobile */
    .stDataFrame {
        font-size: 12px !important;
    }

    [data-testid="stDataFrame"] > div {
        overflow-x: auto !important;
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
                # Auto-select current date and hour on login
                st.session_state['selected_date'] = date.today()
                st.session_state['selected_hour'] = get_current_hour_slot()
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
    from datetime import timedelta

    user = get_current_user()
    floor_id = user.get('floor_id')
    floor_name = user.get('floor_name')

    # Header with floor badge and logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="floor-badge">{floor_name}</div>', unsafe_allow_html=True)
    with col2:
        if st.button("↩️ Exit", help="Logout", use_container_width=True):
            logout()
            st.rerun()

    # Date selector - allow past dates for retroactive editing
    today = date.today()
    selected_date = st.date_input(
        "Date",
        value=st.session_state.get('selected_date', today),
        max_value=today,
        min_value=today - timedelta(days=30),  # Allow up to 30 days back
        key="entry_date"
    )
    st.session_state['selected_date'] = selected_date

    is_today = selected_date == today
    current_hour = get_current_hour_slot() if is_today else None
    hour_slots = get_hour_slots()

    # Get existing entries for selected date
    entries = get_entries_for_date(selected_date, floor_id)
    entries_by_hour = {e['hour_slot']: e['count'] for e in entries}

    # Stats for selected date
    total_count = sum(entries_by_hour.values())
    filled_hours = len(entries_by_hour)
    total_hours = len(hour_slots)

    # Stats row - 3 equal columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value">{total_count:,}</div>
                <div class="stat-label">Total</div>
            </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value">{filled_hours}/{total_hours}</div>
                <div class="stat-label">Hours</div>
            </div>
        ''', unsafe_allow_html=True)
    with col3:
        last_entry = max(entries_by_hour.keys()) if entries_by_hour else None
        last_str = format_hour_slot(last_entry, period=False) if last_entry else "-"
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value">{last_str}</div>
                <div class="stat-label">Last</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("---")

    # Hour selection with big buttons
    st.markdown("### Select Hour")

    # Default to current hour if today, else first slot
    default_hour = current_hour if is_today and current_hour in hour_slots else hour_slots[0]
    selected_hour = st.session_state.get('selected_hour', default_hour)
    if selected_hour not in hour_slots:
        selected_hour = hour_slots[0]

    # Show hours in a 2-column grid for mobile friendliness
    for row_start in range(0, len(hour_slots), 2):
        row_hours = hour_slots[row_start:row_start + 2]
        cols = st.columns(2)

        for i, hour in enumerate(row_hours):
            with cols[i]:
                existing_count = entries_by_hour.get(hour)
                is_current = is_today and hour == current_hour
                is_selected = hour == selected_hour

                # Period format for button label (compact)
                label = format_hour_slot(hour)
                if existing_count is not None:
                    label += f" ✓"
                if is_current:
                    label += " ⏰"

                btn_type = "primary" if is_selected else "secondary"

                if st.button(label, key=f"hour_{hour}_{selected_date}", type=btn_type, use_container_width=True):
                    st.session_state['selected_hour'] = hour
                    st.rerun()

    st.markdown("---")

    # Entry form for selected hour
    selected_hour = st.session_state.get('selected_hour', default_hour)
    if selected_hour not in hour_slots:
        selected_hour = hour_slots[0]
    existing_value = entries_by_hour.get(selected_hour)

    st.markdown(f"### {format_hour_slot(selected_hour)}")

    # Check if there's a quick add value to apply
    default_count = existing_value if existing_value else 0
    if 'quick_add' in st.session_state:
        default_count = st.session_state.pop('quick_add')

    # Big number input
    count = st.number_input(
        "Footfall count",
        min_value=0,
        max_value=10000,
        value=default_count,
        step=1,
        label_visibility="collapsed",
        key=f"count_input_{selected_hour}_{selected_date}"
    )

    # Quick add buttons - 3 columns
    st.markdown("**Quick add:**")
    quick_cols = st.columns(3)
    quick_values = [10, 50, 100]
    for i, val in enumerate(quick_values):
        with quick_cols[i]:
            if st.button(f"+{val}", key=f"quick_{val}_{selected_hour}", use_container_width=True):
                st.session_state['quick_add'] = count + val
                st.rerun()

    # Save button
    if st.button("💾 Save Entry", type="primary", use_container_width=True):
        if count > 0:
            success, msg, was_update = save_entry(
                entry_date=selected_date,
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
    """Today's overview for all floors with comparison stats."""
    from services.metrics_service import get_daily_total, get_floor_breakdown, get_hourly_trend
    from components.charts import create_hourly_trend_chart, create_floor_bar_chart
    from datetime import timedelta

    today = date.today()

    # Total stats
    total = get_daily_total(today)
    breakdown = get_floor_breakdown(today)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Today", f"{total:,}")
    with col2:
        st.metric("Floors Active", len([v for v in breakdown.values() if v > 0]))

    # Comparison stats
    st.markdown("### Comparisons")

    # Calculate comparison values
    def get_average(days_list):
        """Get average of daily totals for given dates, excluding zeros (N/A days)."""
        totals = [get_daily_total(d) for d in days_list]
        valid_totals = [t for t in totals if t > 0]
        return sum(valid_totals) / len(valid_totals) if valid_totals else None

    def format_comparison(current, comparison):
        """Format comparison as percentage change."""
        if comparison is None or comparison == 0:
            return "N/A", None
        diff = ((current - comparison) / comparison) * 100
        return f"{comparison:,.0f}", diff

    # Last 7 days average (excluding today)
    last_7_days = [today - timedelta(days=i) for i in range(1, 8)]
    avg_7_days = get_average(last_7_days)
    avg_7_str, avg_7_diff = format_comparison(total, avg_7_days)

    # This month average (excluding today)
    month_start = today.replace(day=1)
    month_days = [(month_start + timedelta(days=i)) for i in range((today - month_start).days)]
    avg_month = get_average(month_days) if month_days else None
    avg_month_str, avg_month_diff = format_comparison(total, avg_month)

    # Same weekday average (last 4 occurrences)
    same_weekdays = [today - timedelta(weeks=i) for i in range(1, 5)]
    avg_weekday = get_average(same_weekdays)
    weekday_name = today.strftime("%A")
    avg_weekday_str, avg_weekday_diff = format_comparison(total, avg_weekday)

    # Last year same date
    try:
        last_year_date = today.replace(year=today.year - 1)
        last_year_total = get_daily_total(last_year_date)
        last_year_str = f"{last_year_total:,}" if last_year_total > 0 else "N/A"
        _, last_year_diff = format_comparison(total, last_year_total if last_year_total > 0 else None)
    except ValueError:  # Feb 29 edge case
        last_year_str, last_year_diff = "N/A", None

    # Last year same month average
    try:
        last_year_month_start = today.replace(year=today.year - 1, day=1)
        last_year_month_end = (last_year_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        last_year_month_days = [last_year_month_start + timedelta(days=i)
                                for i in range((last_year_month_end - last_year_month_start).days + 1)]
        avg_last_year_month = get_average(last_year_month_days)
        avg_ly_month_str, avg_ly_month_diff = format_comparison(total, avg_last_year_month)
    except ValueError:
        avg_ly_month_str, avg_ly_month_diff = "N/A", None

    # Display comparisons in 2 columns
    col1, col2 = st.columns(2)
    with col1:
        delta_7 = f"{avg_7_diff:+.0f}%" if avg_7_diff is not None else None
        st.metric("vs 7-Day Avg", avg_7_str, delta=delta_7)

        delta_weekday = f"{avg_weekday_diff:+.0f}%" if avg_weekday_diff is not None else None
        st.metric(f"vs {weekday_name}s", avg_weekday_str, delta=delta_weekday)

        delta_ly = f"{last_year_diff:+.0f}%" if last_year_diff is not None else None
        st.metric("vs Last Year Date", last_year_str, delta=delta_ly)

    with col2:
        delta_month = f"{avg_month_diff:+.0f}%" if avg_month_diff is not None else None
        st.metric("vs Month Avg", avg_month_str, delta=delta_month)

        delta_ly_month = f"{avg_ly_month_diff:+.0f}%" if avg_ly_month_diff is not None else None
        st.metric("vs LY Month Avg", avg_ly_month_str, delta=delta_ly_month)

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
    """Reports with table view and optional CSV export."""
    from services.export_service import export_to_csv
    from services.entry_service import get_entries_for_date_range, get_floors
    from datetime import timedelta
    import pandas as pd

    st.markdown("### Reports")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date.today() - timedelta(days=7), key="report_start_date")
    with col2:
        end_date = st.date_input("To", value=date.today(), key="report_end_date")

    if st.button("Generate Report", type="primary"):
        st.session_state['show_report'] = True

    # Show report if generated
    if st.session_state.get('show_report'):
        entries = get_entries_for_date_range(start_date, end_date)
        floors = get_floors(active_only=False)
        floor_names = {f['floor_id']: f['floor_name'] for f in floors}

        if entries:
            # Create dataframe for display
            records = []
            for entry in entries:
                records.append({
                    'Date': entry['date'].strftime('%Y-%m-%d'),
                    'Day': entry['date'].strftime('%a'),
                    'Hour': format_hour_slot(entry['hour_slot']),
                    'Floor': floor_names.get(entry['floor_id'], f"Floor {entry['floor_id']}"),
                    'Count': entry['count'],
                })
            df = pd.DataFrame(records)

            # Summary stats
            total = df['Count'].sum()
            days_count = df['Date'].nunique()
            avg_daily = total / days_count if days_count > 0 else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", f"{total:,}")
            with col2:
                st.metric("Days", days_count)
            with col3:
                st.metric("Avg/Day", f"{avg_daily:,.0f}")

            # Floor breakdown
            st.markdown("**By Floor:**")
            floor_totals = df.groupby('Floor')['Count'].sum().sort_values(ascending=False)
            for floor, floor_total in floor_totals.items():
                pct = (floor_total / total * 100) if total > 0 else 0
                st.progress(pct / 100, text=f"{floor}: {floor_total:,} ({pct:.0f}%)")

            # Data table
            st.markdown("**Details:**")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # CSV download
            csv_data = export_to_csv(start_date, end_date)
            st.download_button(
                "📥 Download CSV",
                data=csv_data,
                file_name=f"footfall_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data found for the selected date range")


def show_admin_settings():
    """Basic settings."""
    from database.db import get_setting, set_setting, get_db_session
    from database.models import FootfallEntry, AuditLog
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

    # Reset floors to defaults
    st.markdown("### Reset Floors")
    st.info("Reset floors to: Basement, Ground, Upper Ground, First, Second, Third")
    if st.button("🔄 Reset Floors to Defaults"):
        from database.db import reset_floors_to_defaults
        count = reset_floors_to_defaults()
        st.success(f"Reset to {count} default floors.")
        st.rerun()

    st.markdown("---")

    # Danger zone - Reset data
    st.markdown("### Danger Zone")
    st.warning("This will permanently delete ALL footfall entries and audit logs.")

    confirm_text = st.text_input(
        "Type 'delete' to confirm data reset",
        key="reset_confirm",
        placeholder="Type 'delete' to confirm"
    )

    if st.button("🗑️ Reset All Data", type="secondary"):
        if confirm_text.lower() == "delete":
            with get_db_session() as db:
                # Delete all footfall entries
                entry_count = db.query(FootfallEntry).count()
                db.query(FootfallEntry).delete()

                # Delete all audit logs
                log_count = db.query(AuditLog).count()
                db.query(AuditLog).delete()

                db.commit()

            st.success(f"Deleted {entry_count} entries and {log_count} audit logs.")
            st.rerun()
        else:
            st.error("Please type 'delete' to confirm.")

    st.markdown("---")
    st.caption("For full admin features, access from desktop browser")


if __name__ == "__main__":
    main()
