"""
Compare page - Day vs Day, Week vs Week comparisons.
"""

import streamlit as st
from datetime import date, timedelta
from services.entry_service import get_floors
from services.comparison_service import (
    compare_days, compare_weeks, compare_same_weekday, get_comparison_summary
)
from services.export_service import export_to_csv
from components.charts import create_comparison_bar_chart
from utils.datetime_utils import get_week_start, format_date


def render_compare_page():
    """Render the Compare page."""
    st.title("Compare")

    # Comparison mode selector
    mode = st.radio(
        "Comparison Mode",
        options=["Day vs Day", "Week vs Week", "Same Weekday"],
        horizontal=True
    )

    st.markdown("---")

    # Floor filter
    floors = get_floors(active_only=True)
    floor_options = {f['floor_id']: f['floor_name'] for f in floors}

    selected_floors = st.multiselect(
        "Filter Floors",
        options=list(floor_options.keys()),
        format_func=lambda x: floor_options[x],
        default=list(floor_options.keys())
    )

    st.markdown("---")

    if mode == "Day vs Day":
        render_day_comparison(selected_floors)
    elif mode == "Week vs Week":
        render_week_comparison(selected_floors)
    else:
        render_weekday_comparison(selected_floors)


def render_day_comparison(floor_ids: list):
    """Render day vs day comparison."""
    col1, col2 = st.columns(2)

    with col1:
        date1 = st.date_input(
            "Date 1",
            value=date.today(),
            max_value=date.today(),
            key="date1"
        )

    with col2:
        # Default to same day last week
        default_date2 = date.today() - timedelta(days=7)
        date2 = st.date_input(
            "Date 2 (Compare to)",
            value=default_date2,
            max_value=date.today(),
            key="date2"
        )

    if st.button("Compare", type="primary"):
        # Get comparison data
        df = compare_days(date1, date2, floor_ids)
        summary = get_comparison_summary(date1, date2)

        # Show summary
        st.markdown("### Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label=format_date(date1),
                value=f"{summary['total1']:,}"
            )

        with col2:
            st.metric(
                label=format_date(date2),
                value=f"{summary['total2']:,}"
            )

        with col3:
            st.metric(
                label="Change",
                value=f"{summary['change']:+,}",
                delta=f"{summary['percent_change']:+.1f}%"
            )

        st.markdown("---")

        # Show chart
        st.markdown("### Hourly Comparison")
        fig = create_comparison_bar_chart(df[:-1], title="")  # Exclude total row
        st.plotly_chart(fig, use_container_width=True)

        # Show table
        st.markdown("### Detailed Breakdown")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export button
        csv_data = export_to_csv(min(date1, date2), max(date1, date2), floor_ids)
        st.download_button(
            label="Export CSV",
            data=csv_data,
            file_name=f"comparison_{date1}_{date2}.csv",
            mime="text/csv"
        )


def render_week_comparison(floor_ids: list):
    """Render week vs week comparison."""
    col1, col2 = st.columns(2)

    with col1:
        # Default to current week start
        current_week_start = get_week_start(date.today())
        week1_start = st.date_input(
            "Week 1 Start (Monday)",
            value=current_week_start,
            key="week1"
        )

    with col2:
        # Default to previous week
        prev_week_start = current_week_start - timedelta(days=7)
        week2_start = st.date_input(
            "Week 2 Start (Compare to)",
            value=prev_week_start,
            key="week2"
        )

    if st.button("Compare Weeks", type="primary"):
        df = compare_weeks(week1_start, week2_start, floor_ids)

        # Show chart
        st.markdown("### Weekly Comparison")
        fig = create_comparison_bar_chart(df[:-1], title="")  # Exclude total row
        st.plotly_chart(fig, use_container_width=True)

        # Show table
        st.markdown("### Daily Breakdown")
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_weekday_comparison(floor_ids: list):
    """Render same weekday comparison across weeks."""
    col1, col2, col3 = st.columns(3)

    with col1:
        weekday = st.selectbox(
            "Weekday",
            options=[0, 1, 2, 3, 4, 5, 6],
            format_func=lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x],
            index=date.today().weekday()
        )

    with col2:
        start_date = st.date_input(
            "From Date",
            value=date.today() - timedelta(days=56),  # 8 weeks ago
            key="weekday_start"
        )

    with col3:
        end_date = st.date_input(
            "To Date",
            value=date.today(),
            max_value=date.today(),
            key="weekday_end"
        )

    if st.button("Compare Weekdays", type="primary"):
        df = compare_same_weekday(start_date, end_date, weekday, floor_ids)

        if df.empty:
            st.warning("No data found for the selected weekday in this range.")
        else:
            weekday_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday]

            # Show chart
            st.markdown(f"### All {weekday_name}s")
            fig = create_comparison_bar_chart(df, title="")
            st.plotly_chart(fig, use_container_width=True)

            # Show table
            st.markdown("### Detailed Data")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Statistics
            if 'Total' in df.columns:
                totals = df['Total'].tolist()
                if totals:
                    avg = sum(totals) / len(totals)
                    max_val = max(totals)
                    min_val = min(totals)

                    st.markdown("### Statistics")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Average", f"{avg:,.0f}")
                    with col2:
                        st.metric("Maximum", f"{max_val:,}")
                    with col3:
                        st.metric("Minimum", f"{min_val:,}")


def render_compare_sidebar():
    """Render sidebar for compare page."""
    st.sidebar.markdown("### Comparison Tips")
    st.sidebar.markdown("""
    - **Day vs Day**: Compare hourly patterns
    - **Week vs Week**: Compare daily totals
    - **Same Weekday**: Track trends over time
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Comparisons")

    if st.sidebar.button("Today vs Yesterday"):
        st.session_state['compare_mode'] = 'day'
        st.session_state['date1'] = date.today()
        st.session_state['date2'] = date.today() - timedelta(days=1)
        st.rerun()

    if st.sidebar.button("This Week vs Last Week"):
        st.session_state['compare_mode'] = 'week'
        st.rerun()
