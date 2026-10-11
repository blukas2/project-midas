import ctypes
import json
import sys
import time
from queue import Queue

import pandas as pd
import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="The embedded Plotly dashboard requires Windows WebView2.",
)


def test_dashboard_renders_charts_after_empty_initial_render():
    initialized_com = _initialize_com_sta()
    if not initialized_com:
        pytest.skip("The test process is not running in a COM STA.")
    try:
        _render_empty_then_populated_dashboard()
    finally:
        ctypes.windll.ole32.CoUninitialize()


def _initialize_com_sta():
    result = ctypes.windll.ole32.CoInitializeEx(None, 0x2)
    return result in (0, 1)


def _render_empty_then_populated_dashboard():
    ctk, application, factory_class, card_class, dashboard_class, have_runtime = (
        _load_test_dependencies()
    )
    if not have_runtime():
        pytest.skip("The WebView2 Runtime is not installed.")
    root = ctk.CTk()
    try:
        root.geometry("1440x900")
        dashboard = _create_portfolio_dashboard(root, dashboard_class, card_class)
        _render_and_assert_charts(root, dashboard, factory_class(), application, pd)
    finally:
        root.destroy()


def _load_test_dependencies():
    import customtkinter as ctk

    from tkwebview2.tkwebview2 import have_runtime
    from System.Windows.Forms import Application
    from ui.charts.figure_factory import FigureFactory
    from ui.charts.page_builder import ChartCardSpec
    from ui.charts.plotly_dashboard import PlotlyDashboard

    return ctk, Application, FigureFactory, ChartCardSpec, PlotlyDashboard, have_runtime


def _create_portfolio_dashboard(root, dashboard_class, card_class):
    cards = [
        card_class("portfolio-history", "History", wide=True),
        card_class("allocation", "Allocation"),
        card_class("portfolio-returns", "Returns"),
        card_class("annualized-returns", "Annualized"),
        card_class("portfolio-volatility", "Volatility"),
        card_class("correlation", "Correlation", wide=True),
    ]
    dashboard = dashboard_class(
        root,
        "Portfolio dashboard",
        cards,
        include_metrics=True,
        include_holdings=True,
    )
    dashboard.pack(fill="both", expand=True)
    return dashboard


def _render_and_assert_charts(root, dashboard, factory, application, pandas):
    dashboard.render(_portfolio_figures(factory, pandas, False))
    _pump_until(root, application, lambda: dashboard._last_render_complete)
    dashboard.render(_portfolio_figures(factory, pandas, True))
    _pump_until(root, application, lambda: dashboard._last_render_complete)
    _assert_rendered_portfolio(root, dashboard, application)


def _assert_rendered_portfolio(root, dashboard, application):
    result = _evaluate_chart_state(root, dashboard, application)
    assert len(result["charts"]) == 6
    assert all(chart["data"] == 1 and chart["svgs"] > 0 for chart in result["charts"])
    _assert_portfolio_grid(result["spans"])
    assert dashboard._last_render_errors == []


def _assert_portfolio_grid(spans):
    expected_spans = {
        "portfolio-history": "span 8",
        "allocation": "span 4",
        "holdings-card": "span 6",
        "portfolio-returns": "span 3",
        "annualized-returns": "span 3",
        "portfolio-volatility": "span 4",
        "correlation": "span 8",
    }
    assert spans == expected_spans


def _portfolio_figures(factory, pandas, populated):
    dates = ["2025-01-01", "2025-01-02"] if populated else []
    values = [100, 105] if populated else []
    allocations = {"AAA": 60, "BBB": 40} if populated else {}
    returns = {"1y": 12, "3y": 20} if populated else {}
    correlations = pandas.DataFrame([[1, 0.5], [0.5, 1]]) if populated else pandas.DataFrame()
    return {
        "portfolio-history": factory.line_chart([("Portfolio", dates, values)], "Light", "EUR"),
        "allocation": factory.donut_chart(allocations, "Light"),
        "portfolio-returns": factory.bar_chart(returns, "Light"),
        "annualized-returns": factory.bar_chart(returns, "Light"),
        "portfolio-volatility": factory.bar_chart(returns, "Light", "Volatility"),
        "correlation": factory.heatmap(correlations, "Light"),
    }


def _pump_until(root, application, predicate):
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        root.update()
        application.DoEvents()
        if predicate():
            return
        time.sleep(0.01)
    pytest.fail("The WebView2 dashboard did not finish rendering.")


def _evaluate_chart_state(root, dashboard, application):
    result = Queue()
    script = (
        "JSON.stringify({charts:[...document.querySelectorAll('.plot')].map(plot=>"
        "({data:plot.data.length,svgs:plot.querySelectorAll('svg').length})),"
        "spans:Object.fromEntries(['portfolio-history','allocation','holdings-card',"
        "'portfolio-returns','annualized-returns','portfolio-volatility','correlation']"
        ".map(id=>[id,getComputedStyle(document.getElementById(id)).gridColumnStart]))})"
    )
    dashboard.browser.evaluate_js(script, result.put)
    _pump_until(root, application, lambda: not result.empty())
    return json.loads(result.get_nowait())
