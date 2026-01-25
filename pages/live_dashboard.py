"""
Live Dashboard page - Today's metrics and real-time monitoring.
"""

import streamlit as st
from datetime import date
from services.metrics_service import (
    get_daily_total, get_floor_breakdown, get_hourly_trend,
    get_peak_hour, get_floor_share_percent, get_delta_vs_yesterday
)
from components.charts import (
    create_hourly_trend_chart, create_floor_pie_chart, create_floor_bar_chart
)
from components.metric_tiles import dashboard_kpi_tiles
from utils.datetime_utils import format_hour_slot


def render_live_dashboard_page():
    """Render the Live Dashboard page."""
    st.title("Today's Dashboard")

    today = date.today()

    # Get data
    delta_data = get_delta_vs_yesterday(today)
    hourly = get_hourly_trend(today)
    breakdown = get_floor_breakdown(today)
    share_pct = get_floor_share_percent(today)

    # KPI tiles row
    st.markdown("### Key Metrics")
    dashboard_kpi_tiles(delta_data)

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Hourly Trend")
        fig = create_hourly_trend_chart(hourly, title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Floor Distribution")
        fig = create_floor_pie_chart(breakdown, title="")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Floor breakdown table
    st.markdown("### Floor Breakdown")

    if breakdown:
        col1, col2 = st.columns(2)

        with col1:
            # Table view
            for floor, count in sorted(breakdown.items()):
                pct = share_pct.get(floor, 0)
                st.markdown(f"**{floor}**: {count:,} ({pct:.1f}%)")

        with col2:
            # Bar chart
            fig = create_floor_bar_chart(breakdown, title="")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for today yet. Start entering footfall counts!")

    st.markdown("---")

    # Comparison with yesterday
    st.markdown("### vs Yesterday")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Today Total",
            value=f"{delta_data['today_total']:,}"
        )

    with col2:
        st.metric(
            label="Yesterday Total",
            value=f"{delta_data['yesterday_total']:,}"
        )

    with col3:
        change_color = "green" if delta_data['total_change'] >= 0 else "red"
        st.metric(
            label="Change",
            value=f"{delta_data['total_change']:+,}",
            delta=f"{delta_data['total_percent_change']:+.1f}%"
        )

    # Auto-refresh option
    st.markdown("---")
    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("Refresh", use_container_width=True):
            st.rerun()


def render_dashboard_sidebar():
    """Render sidebar content for dashboard page."""
    st.sidebar.markdown("### Dashboard Info")
    st.sidebar.markdown(f"**Date:** {date.today().strftime('%d %b %Y')}")

    # Quick stats
    today = date.today()
    total = get_daily_total(today)
    peak_hour, peak_count = get_peak_hour(today)

    st.sidebar.markdown(f"**Total:** {total:,}")
    if peak_hour is not None:
        st.sidebar.markdown(f"**Peak:** {format_hour_slot(peak_hour)} ({peak_count:,})")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Links")

    if st.sidebar.button("Go to Entry", use_container_width=True):
        st.session_state['page'] = 'Quick Entry'
        st.rerun()

    if st.sidebar.button("View Trends", use_container_width=True):
        st.session_state['page'] = 'Trends'
        st.rerun()
