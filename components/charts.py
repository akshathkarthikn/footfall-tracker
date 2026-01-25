"""
Plotly chart builders for the Footfall Tracker.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import CHART_COLORS, get_floor_color
from utils.datetime_utils import format_hour_slot


def create_hourly_trend_chart(hourly_data: dict, title: str = "Hourly Footfall") -> go.Figure:
    """Create a line chart showing hourly trend."""
    if not hourly_data:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    hours = sorted(hourly_data.keys())
    values = [hourly_data[h] for h in hours]
    labels = [format_hour_slot(h) for h in hours]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=values,
        mode='lines+markers',
        name='Footfall',
        line=dict(color=CHART_COLORS[0], width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Hour",
        yaxis_title="Footfall",
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_floor_pie_chart(breakdown: dict, title: str = "Floor Distribution") -> go.Figure:
    """Create a donut chart showing floor breakdown."""
    if not breakdown or sum(breakdown.values()) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    floors = list(breakdown.keys())
    values = list(breakdown.values())
    colors = [get_floor_color(i) for i in range(len(floors))]

    fig = go.Figure(data=[go.Pie(
        labels=floors,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside'
    )])

    fig.update_layout(
        title=title,
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_floor_bar_chart(breakdown: dict, title: str = "Footfall by Floor") -> go.Figure:
    """Create a horizontal bar chart showing floor breakdown."""
    if not breakdown:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    floors = list(breakdown.keys())
    values = list(breakdown.values())
    colors = [get_floor_color(i) for i in range(len(floors))]

    fig = go.Figure(data=[go.Bar(
        y=floors,
        x=values,
        orientation='h',
        marker_color=colors,
        text=values,
        textposition='outside'
    )])

    fig.update_layout(
        title=title,
        xaxis_title="Footfall",
        yaxis_title="Floor",
        margin=dict(l=40, r=80, t=60, b=40)
    )

    return fig


def create_comparison_bar_chart(df: pd.DataFrame, title: str = "Comparison") -> go.Figure:
    """Create a grouped bar chart for comparison data."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    fig = go.Figure()

    # Get the columns (excluding 'Hour', 'Day', 'Date' and 'Change %')
    x_col = 'Hour' if 'Hour' in df.columns else ('Day' if 'Day' in df.columns else 'Date')
    value_cols = [c for c in df.columns if c not in [x_col, 'Change %', 'vs Avg']]

    for i, col in enumerate(value_cols):
        fig.add_trace(go.Bar(
            name=col,
            x=df[x_col],
            y=df[col],
            marker_color=CHART_COLORS[i % len(CHART_COLORS)]
        ))

    fig.update_layout(
        title=title,
        barmode='group',
        xaxis_title=x_col,
        yaxis_title="Footfall",
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_rolling_average_chart(data: dict, title: str = "7-Day Rolling Average") -> go.Figure:
    """Create a line chart showing rolling average."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    dates = sorted(data.keys())
    values = [data[d] for d in dates]
    labels = [d.strftime('%d %b') for d in dates]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=values,
        mode='lines',
        name='Rolling Avg',
        line=dict(color=CHART_COLORS[1], width=2),
        fill='tozeroy',
        fillcolor='rgba(37, 99, 235, 0.1)'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Average Footfall",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_heatmap(df: pd.DataFrame, title: str = "Weekday x Hour Heatmap") -> go.Figure:
    """Create a heatmap from a DataFrame with weekdays as rows and hours as columns."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    weekdays = df['Weekday'].tolist()
    hours = [c for c in df.columns if c != 'Weekday']
    values = df[[c for c in df.columns if c != 'Weekday']].values

    # Create hour labels
    hour_labels = [format_hour_slot(int(h)) for h in hours]

    fig = go.Figure(data=go.Heatmap(
        z=values,
        x=hour_labels,
        y=weekdays,
        colorscale='YlOrRd',
        text=values,
        texttemplate='%{text:.0f}',
        textfont={"size": 10},
        hovertemplate='%{y} %{x}: %{z:.0f}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Hour",
        yaxis_title="Day",
        margin=dict(l=80, r=40, t=60, b=60)
    )

    return fig


def create_floor_trend_chart(df: pd.DataFrame, title: str = "Floor Trend Over Time") -> go.Figure:
    """Create a stacked area chart showing floor trends over time."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    fig = go.Figure()

    floor_cols = [c for c in df.columns if c != 'Date']

    for i, floor in enumerate(floor_cols):
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df[floor],
            mode='lines',
            name=floor,
            stackgroup='one',
            fillcolor=get_floor_color(i),
            line=dict(color=get_floor_color(i))
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Footfall",
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig


def create_monthly_bar_chart(data: dict, title: str = "Monthly Totals") -> go.Figure:
    """Create a bar chart showing monthly totals."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    months = sorted(data.keys())
    values = [data[m] for m in months]

    # Format month labels
    from datetime import datetime
    labels = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in months]

    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=CHART_COLORS[0],
        text=values,
        textposition='outside'
    )])

    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Total Footfall",
        margin=dict(l=40, r=40, t=60, b=60)
    )

    return fig
