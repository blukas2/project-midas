from datetime import date
import json
from unittest.mock import Mock

import pandas as pd

from ui.charts.chart_theme import ChartTheme
from ui.charts.figure_factory import FigureFactory
from ui.charts.page_builder import ChartCardSpec, DashboardPageBuilder
from ui.charts.plotly_dashboard import PlotlyDashboard


class TestChartTheme:
    def test_dark_and_light_palettes_have_distinct_surfaces(self):
        theme = ChartTheme()

        assert theme.palette("Dark").background == "#171c27"
        assert theme.palette("Dark").text != theme.palette("Light").text
        assert theme.layout("Light")["template"] == "none"


class TestFigureFactory:
    def test_line_chart_has_range_controls_and_multiple_series(self):
        factory = FigureFactory()
        dates = [date(2024, 1, 1), date(2024, 1, 2)]

        figure = factory.line_chart(
            [("Asset", dates, [100, 105]), ("Portfolio", dates, [100, 103])],
            "Light",
            "Index",
        )

        assert len(figure.data) == 2
        assert figure.layout.xaxis.rangeselector.buttons[0].label == "1m"
        assert figure.layout.xaxis.rangeslider.visible is True

    def test_bar_chart_uses_sign_colors_and_consistent_labels(self):
        figure = FigureFactory().bar_chart({"1y": 12.345, "3y": -2.0}, "Light")

        assert list(figure.data[0].text) == ["12.3%", "-2.0%"]
        assert list(figure.data[0].marker.color) == [
            ChartTheme().palette("Light").positive,
            ChartTheme().palette("Light").negative,
        ]
        assert figure.layout.yaxis.ticksuffix == "%"

    def test_grouped_bar_chart_aligns_periods_without_fabricating_values(self):
        figure = FigureFactory().grouped_bar_chart(
            [("Asset", {"1y": 3}), ("Portfolio", {"3y": 5})], "Dark"
        )

        assert list(figure.data[0].x) == ["1y", "3y"]
        assert list(figure.data[0].y) == [3.0, None]
        assert list(figure.data[1].y) == [None, 5.0]

    def test_empty_and_heatmap_data_produce_readable_figures(self):
        factory = FigureFactory()
        empty = factory.bar_chart({}, "Light")
        heatmap = factory.heatmap(pd.DataFrame({"ABC": [1.0]}, index=["ABC"]), "Dark")

        assert empty.layout.annotations[0].text == "No data available"
        assert heatmap.data[0].z == ([1.0],)
        assert heatmap.data[0].zmin == -1
        assert heatmap.data[0].zmax == 1


class TestDashboardPageBuilder:
    def test_builds_offline_responsive_dashboard_and_escapes_content(self):
        builder = DashboardPageBuilder()

        page = builder.build(
            "<Portfolio>",
            [ChartCardSpec("history", "Value history", wide=True)],
            include_metrics=True,
            include_holdings=True,
        )
        table = builder.table_markup(("Ticker",), (("<ABC>",),))

        assert "<Portfolio>" not in page
        assert 'id="history"' in page
        assert "responsive: true" in page
        assert '<script src="https://midas-plotly.example/plotly.min.js"></script>' in page
        assert "grid-template-columns: repeat(12, minmax(0, 1fr))" in page
        assert "portfolio-layout #portfolio-history { grid-column: span 8; }" in page
        assert "overflow-y: auto" in page
        assert "#holdings { max-height" not in page
        assert "chart.innerHTML = ''" not in page
        assert "dashboardRenderStatus" in page
        assert "&lt;ABC&gt;" in table

    def test_portfolio_cards_have_explicit_non_overlapping_grid_spans(self):
        page = DashboardPageBuilder().build(
            "Portfolio",
            [
                ChartCardSpec("portfolio-history", "History", wide=True),
                ChartCardSpec("allocation", "Allocation"),
                ChartCardSpec("portfolio-returns", "Returns"),
                ChartCardSpec("annualized-returns", "Annualized"),
                ChartCardSpec("portfolio-volatility", "Volatility"),
                ChartCardSpec("correlation", "Correlation", wide=True),
            ],
            include_holdings=True,
        )

        assert 'class="dashboard-grid portfolio-layout"' in page
        assert 'id="holdings-card"' in page
        assert ".portfolio-layout #holdings-card { grid-column: span 6; }" in page
        assert ".portfolio-layout #portfolio-volatility { grid-column: span 4; }" in page
        assert ".portfolio-layout #correlation { grid-column: span 8; }" in page

    def test_asset_history_and_returns_share_the_wide_dashboard_row(self):
        page = DashboardPageBuilder().build(
            "Asset details",
            [
                ChartCardSpec("asset-history", "Price history", wide=True),
                ChartCardSpec("asset-returns", "Annualized returns"),
            ],
        )

        assert "#asset-history { grid-column: span 8; }" in page
        assert "#asset-returns { grid-column: span 4; }" in page


class TestPlotlyDashboard:
    def test_dispatches_pending_charts_after_page_becomes_ready(self):
        dashboard = Mock()
        dashboard._failed = False
        dashboard._ready = False
        dashboard._page_timeout_id = None
        dashboard._pending_content = {"figures": {}}

        PlotlyDashboard._on_page_ready(dashboard, True)

        assert dashboard._ready is True
        dashboard._dispatch_render.assert_called_once_with()

    def test_retries_until_page_is_ready(self):
        dashboard = Mock()
        dashboard._failed = False
        dashboard._ready = False
        dashboard._pending_content = None
        dashboard._page_load_deadline = float("inf")

        PlotlyDashboard._on_page_ready(dashboard, False)

        dashboard.after.assert_called_once_with(50, dashboard._check_page_ready)

    def test_webview_callback_queues_page_state_without_touching_tk(self):
        from queue import Queue

        dashboard = Mock()
        dashboard._browser_events = Queue()

        PlotlyDashboard._queue_page_ready(dashboard, True)

        assert dashboard._browser_events.get_nowait() == ("page", True)

    def test_plotly_render_errors_are_logged_and_retained(self, caplog):
        dashboard = Mock()
        dashboard._render_status_pending = True
        dashboard._last_render_complete = False
        dashboard._last_render_errors = []
        dashboard._parse_render_status = json.loads
        dashboard._log_render_errors = lambda: PlotlyDashboard._log_render_errors(dashboard)
        raw_status = '{"complete":true,"errors":[{"chart":"history","message":"bad figure"}]}'

        PlotlyDashboard._on_render_status(dashboard, raw_status)

        assert dashboard._render_status_pending is False
        assert dashboard._last_render_complete is True
        assert dashboard._last_render_errors == [
            {"chart": "history", "message": "bad figure"}
        ]
        assert "Plotly chart 'history' failed: bad figure" in caplog.text
