import pandas as pd
import plotly.graph_objects as go


def create_funnel_chart(
    data: pd.DataFrame,
    stage_col: str,
    value_col: str,
    title: str = "",
) -> go.Figure:
    if data.empty:
        return go.Figure().update_layout(title=title)
    fig = go.Figure(
        go.Funnel(
            y=data[stage_col],
            x=data[value_col],
            textinfo="value+percent initial",
        )
    )
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def create_retention_heatmap(
    data: pd.DataFrame,
    title: str = "Retention Cohorts",
) -> go.Figure:
    if data.empty:
        return go.Figure().update_layout(title=title)
    pivot = data.pivot_table(
        index="cohort_week",
        columns="week_number",
        values="retention_pct",
        aggfunc="first",
    )
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"W{int(c)}" for c in pivot.columns],
            y=[str(d.date()) if hasattr(d, "date") else str(d) for d in pivot.index],
            colorscale="Greens",
            text=pivot.values,
            texttemplate="%{text:.0f}%",
            hovertemplate="Cohort: %{y}<br>Week: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Weeks Since Signup",
        yaxis_title="Cohort",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def create_timeseries(
    data: pd.DataFrame,
    x_col: str,
    y_col: str | list[str],
    title: str = "",
) -> go.Figure:
    fig = go.Figure()
    if data.empty:
        fig.update_layout(title=title)
        return fig

    y_cols = [y_col] if isinstance(y_col, str) else y_col
    for col in y_cols:
        if col in data.columns:
            fig.add_trace(
                go.Scatter(x=data[x_col], y=data[col], mode="lines+markers", name=col)
            )
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def create_pie_chart(
    data: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str = "",
) -> go.Figure:
    if data.empty:
        return go.Figure().update_layout(title=title)
    fig = go.Figure(
        go.Pie(
            labels=data[label_col],
            values=data[value_col],
            hole=0.4,
            textinfo="label+percent",
        )
    )
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def create_stacked_area(
    data: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    title: str = "",
) -> go.Figure:
    fig = go.Figure()
    if data.empty:
        fig.update_layout(title=title)
        return fig
    for col in y_cols:
        if col in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data[x_col],
                    y=data[col],
                    mode="lines",
                    name=col,
                    stackgroup="one",
                )
            )
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20))
    return fig
