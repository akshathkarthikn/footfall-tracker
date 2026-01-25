"""
KPI metric tiles for dashboards.
"""

import streamlit as st


def metric_tile(label: str, value, delta=None, delta_color: str = "normal"):
    """
    Display a metric tile with optional delta.

    Args:
        label: Metric label
        value: Main value to display
        delta: Optional delta/change value
        delta_color: 'normal' (green for positive), 'inverse' (red for positive), or 'off'
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def render_metric_row(metrics: list[dict]):
    """
    Render a row of metric tiles.

    Args:
        metrics: List of dicts with 'label', 'value', 'delta' (optional), 'delta_color' (optional)
    """
    cols = st.columns(len(metrics))

    for i, metric in enumerate(metrics):
        with cols[i]:
            metric_tile(
                label=metric.get('label', ''),
                value=metric.get('value', 0),
                delta=metric.get('delta'),
                delta_color=metric.get('delta_color', 'normal')
            )


def dashboard_kpi_tiles(delta_data: dict):
    """
    Render dashboard KPI tiles from delta data.
    """
    from utils.datetime_utils import format_hour_slot

    # Format delta values
    total_delta = f"{delta_data['total_percent_change']:+.1f}%" if delta_data['yesterday_total'] > 0 else "N/A"
    hour_delta = f"{delta_data['hour_percent_change']:+.1f}%" if delta_data['yesterday_at_hour'] > 0 else "N/A"

    # Determine peak hour
    from services.metrics_service import get_peak_hour
    from datetime import date
    peak_hour, peak_count = get_peak_hour(date.today())
    peak_str = f"{format_hour_slot(peak_hour)} ({peak_count:,})" if peak_hour is not None else "N/A"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Today's Total",
            value=f"{delta_data['today_total']:,}",
            delta=total_delta
        )

    with col2:
        st.metric(
            label="vs Yesterday",
            value=f"{delta_data['total_change']:+,}",
            delta=total_delta
        )

    with col3:
        st.metric(
            label="So Far Today",
            value=f"{delta_data['today_at_hour']:,}",
            delta=hour_delta
        )

    with col4:
        st.metric(
            label="Peak Hour",
            value=peak_str
        )
