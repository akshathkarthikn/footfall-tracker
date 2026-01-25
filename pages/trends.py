"""
Trends page - Long-term analytics and patterns.
"""

import streamlit as st
from datetime import date, timedelta
from services.entry_service import get_floors
from services.metrics_service import (
    get_rolling_average, get_monthly_totals, get_weekday_hour_heatmap,
    get_floor_trend_over_time
)
from database.db import get_db_session
from database.models import HolidayLabel
from components.charts import (
    create_rolling_average_chart, create_heatmap, create_floor_trend_chart,
    create_monthly_bar_chart
)


def render_trends_page():
    """Render the Trends page."""
    st.title("Trends & Analytics")

    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        range_option = st.selectbox(
            "Time Range",
            options=["Last 7 days", "Last 30 days", "Last 90 days", "This Year", "Custom"]
        )

    # Calculate date range based on selection
    today = date.today()
    if range_option == "Last 7 days":
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_option == "Last 30 days":
        start_date = today - timedelta(days=30)
        end_date = today
    elif range_option == "Last 90 days":
        start_date = today - timedelta(days=90)
        end_date = today
    elif range_option == "This Year":
        start_date = date(today.year, 1, 1)
        end_date = today
    else:
        with col2:
            start_date = st.date_input("From", value=today - timedelta(days=30))
        with col3:
            end_date = st.date_input("To", value=today, max_value=today)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Rolling Average", "Heatmap", "Floor Trends", "Monthly"])

    with tab1:
        render_rolling_average(end_date)

    with tab2:
        render_heatmap(start_date, end_date)

    with tab3:
        render_floor_trends(start_date, end_date)

    with tab4:
        render_monthly_totals(today.year)


def render_rolling_average(end_date: date):
    """Render rolling average chart."""
    st.markdown("### 7-Day Rolling Average")
    st.caption("Smoothed trend showing average daily footfall over a rolling 7-day window")

    # Get 30 days of rolling average data
    rolling_data = get_rolling_average(end_date, days=30)

    if rolling_data:
        fig = create_rolling_average_chart(rolling_data, title="")
        st.plotly_chart(fig, use_container_width=True)

        # Show statistics
        values = list(rolling_data.values())
        if values:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Avg", f"{values[-1]:,.0f}")
            with col2:
                st.metric("Peak Avg", f"{max(values):,.0f}")
            with col3:
                trend = values[-1] - values[0] if len(values) > 1 else 0
                st.metric("Trend", f"{trend:+,.0f}")
    else:
        st.info("No data available for rolling average calculation.")


def render_heatmap(start_date: date, end_date: date):
    """Render weekday x hour heatmap."""
    st.markdown("### Traffic Heatmap")
    st.caption("Average footfall by day of week and hour. Darker = Higher traffic")

    heatmap_df = get_weekday_hour_heatmap(start_date, end_date)

    if not heatmap_df.empty:
        fig = create_heatmap(heatmap_df, title="")
        st.plotly_chart(fig, use_container_width=True)

        # Find peak time
        max_val = 0
        peak_day = ""
        peak_hour = 0

        for _, row in heatmap_df.iterrows():
            for col in heatmap_df.columns:
                if col != 'Weekday' and row[col] > max_val:
                    max_val = row[col]
                    peak_day = row['Weekday']
                    peak_hour = col

        if max_val > 0:
            from utils.datetime_utils import format_hour_slot
            st.info(f"**Peak time:** {peak_day} at {format_hour_slot(int(peak_hour))} (avg: {max_val:,.0f})")
    else:
        st.info("No data available for heatmap.")


def render_floor_trends(start_date: date, end_date: date):
    """Render floor-wise trends over time."""
    st.markdown("### Floor Trends")
    st.caption("Daily footfall by floor over time")

    # Floor filter
    floors = get_floors(active_only=True)
    floor_options = {f['floor_id']: f['floor_name'] for f in floors}

    selected_floors = st.multiselect(
        "Select Floors",
        options=list(floor_options.keys()),
        format_func=lambda x: floor_options[x],
        default=list(floor_options.keys())[:3]  # Default to first 3 floors
    )

    if selected_floors:
        trend_df = get_floor_trend_over_time(start_date, end_date)

        if not trend_df.empty:
            # Filter to selected floors
            cols_to_keep = ['Date'] + [floor_options[fid] for fid in selected_floors if floor_options[fid] in trend_df.columns]
            filtered_df = trend_df[cols_to_keep]

            fig = create_floor_trend_chart(filtered_df, title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for floor trends.")
    else:
        st.warning("Please select at least one floor.")


def render_monthly_totals(year: int):
    """Render monthly totals bar chart."""
    st.markdown(f"### Monthly Totals ({year})")

    # Year selector
    col1, col2 = st.columns([3, 1])
    with col2:
        selected_year = st.number_input(
            "Year",
            min_value=2020,
            max_value=date.today().year,
            value=year,
            step=1,
            key="monthly_year"
        )

    monthly_data = get_monthly_totals(selected_year)

    if monthly_data:
        fig = create_monthly_bar_chart(monthly_data, title="")
        st.plotly_chart(fig, use_container_width=True)

        # Summary stats
        total = sum(monthly_data.values())
        months_with_data = len([v for v in monthly_data.values() if v > 0])
        avg_monthly = total / months_with_data if months_with_data > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Year Total", f"{total:,}")
        with col2:
            st.metric("Monthly Avg", f"{avg_monthly:,.0f}")
        with col3:
            st.metric("Months with Data", f"{months_with_data}")
    else:
        st.info(f"No data available for {selected_year}.")


def render_trends_sidebar():
    """Render sidebar for trends page."""
    st.sidebar.markdown("### Trend Insights")
    st.sidebar.markdown("""
    - **Rolling Avg**: Smooths out daily noise
    - **Heatmap**: Find peak hours/days
    - **Floor Trends**: Compare floor performance
    - **Monthly**: Long-term patterns
    """)

    st.sidebar.markdown("---")

    # Holiday labels section
    st.sidebar.markdown("### Holiday Labels")
    st.sidebar.caption("Tag special dates for analysis")

    with get_db_session() as db:
        holidays = db.query(HolidayLabel).order_by(HolidayLabel.date.desc()).limit(5).all()

        if holidays:
            for h in holidays:
                st.sidebar.markdown(f"- **{h.date.strftime('%d %b')}**: {h.label}")
        else:
            st.sidebar.caption("No holidays labeled yet")
