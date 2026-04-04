import pandas as pd
import plotly.graph_objects as go

from components.charts import (
    create_funnel_chart,
    create_pie_chart,
    create_retention_heatmap,
    create_stacked_area,
    create_timeseries,
)


class TestFunnelChart:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame({"stage": ["A", "B", "C"], "count": [100, 50, 20]})
        fig = create_funnel_chart(data, "stage", "count")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame({"stage": [], "count": []})
        fig = create_funnel_chart(data, "stage", "count")
        assert isinstance(fig, go.Figure)

    def test_handles_single_stage(self):
        data = pd.DataFrame({"stage": ["A"], "count": [100]})
        fig = create_funnel_chart(data, "stage", "count")
        assert isinstance(fig, go.Figure)


class TestRetentionHeatmap:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame(
            {
                "cohort_week": pd.to_datetime(
                    ["2026-01-01", "2026-01-01", "2026-01-08"]
                ),
                "week_number": [0, 1, 0],
                "retention_pct": [100.0, 80.0, 100.0],
            }
        )
        fig = create_retention_heatmap(data)
        assert isinstance(fig, go.Figure)

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame(
            {"cohort_week": [], "week_number": [], "retention_pct": []}
        )
        fig = create_retention_heatmap(data)
        assert isinstance(fig, go.Figure)


class TestTimeseries:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=10),
                "value": range(10),
            }
        )
        fig = create_timeseries(data, "date", "value", title="Test")
        assert isinstance(fig, go.Figure)

    def test_multi_column(self):
        data = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=5),
                "a": range(5),
                "b": range(5, 10),
            }
        )
        fig = create_timeseries(data, "date", ["a", "b"])
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame({"date": [], "value": []})
        fig = create_timeseries(data, "date", "value")
        assert isinstance(fig, go.Figure)


class TestPieChart:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame({"label": ["A", "B"], "value": [60, 40]})
        fig = create_pie_chart(data, "label", "value")
        assert isinstance(fig, go.Figure)

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame({"label": [], "value": []})
        fig = create_pie_chart(data, "label", "value")
        assert isinstance(fig, go.Figure)


class TestStackedArea:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame(
            {
                "week": pd.date_range("2026-01-01", periods=5, freq="W"),
                "high": [10, 12, 15, 13, 14],
                "low": [5, 3, 4, 6, 5],
            }
        )
        fig = create_stacked_area(data, "week", ["high", "low"])
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame({"week": [], "a": [], "b": []})
        fig = create_stacked_area(data, "week", ["a", "b"])
        assert isinstance(fig, go.Figure)
