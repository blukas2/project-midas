from __future__ import annotations

import json
import logging
from queue import Empty, Queue
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

import customtkinter as ctk
import plotly
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from ui.charts.page_builder import ChartCardSpec, DashboardPageBuilder
from ui.theme import chart_styler


logger = logging.getLogger(__name__)


class PlotlyDashboard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        chart_cards: Sequence[ChartCardSpec],
        include_metrics: bool = False,
        include_holdings: bool = False,
        height: int = 680,
    ):
        super().__init__(master, corner_radius=14)
        self.page_builder = DashboardPageBuilder()
        self.chart_cards = tuple(chart_cards)
        self.include_holdings = include_holdings
        self._ready = False
        self._failed = False
        self._closed = False
        self._page_check_pending = False
        self._render_status_pending = False
        self._last_render_complete = False
        self._page_timeout_id = None
        self._render_check_id = None
        self._browser_events = Queue()
        self._last_render_errors = []
        self._pending_content = None
        self._theme = ctk.get_appearance_mode()
        self._load_browser(title, include_metrics, include_holdings, height)
        self.bind("<Destroy>", self._cleanup_page_directory, add="+")
        self._event_poll_id = self.after(25, self._process_browser_events)
        chart_styler.register(self)

    def _load_browser(self, title, include_metrics, include_holdings, height):
        self._page_html = self.page_builder.build(
            title, self.chart_cards, include_metrics, include_holdings
        )
        self._page_directory = tempfile.TemporaryDirectory(prefix="midas-charts-")
        page_path = Path(self._page_directory.name) / "index.html"
        page_path.write_text(self._page_html, encoding="utf-8")
        self.browser = self._create_browser(height)
        self.browser.pack(fill="both", expand=True)
        self.browser.event_core_completed(self._queue_browser_initialized)

    def render(
        self,
        figures: dict[str, go.Figure],
        metrics: Sequence[tuple[str, str]] = (),
        table_headers: Sequence[str] = (),
        table_rows: Sequence[Sequence[str]] = (),
        subtitle: str = "",
    ):
        self._pending_content = self._make_payload(figures, metrics, table_headers, table_rows, subtitle)
        if self._ready:
            self._dispatch_render()

    def set_theme(self, mode: str):
        self._theme = mode
        if self._ready and self._pending_content is not None:
            self._dispatch_render()

    def _create_browser(self, height):
        if sys.platform != "win32":
            raise RuntimeError("Interactive charts currently require Windows WebView2.")
        from tkwebview2.tkwebview2 import WebView2, have_runtime

        if not have_runtime():
            raise RuntimeError("Install the Microsoft Edge WebView2 Runtime to display charts.")
        return WebView2(self, width=1000, height=height)

    def _queue_browser_initialized(self, _sender, args):
        error = args.InitializationException
        message = str(error) if error is not None else ""
        self._browser_events.put(("browser", bool(args.IsSuccess), message))

    def _load_page(self):
        self._page_load_deadline = time.monotonic() + 30
        self._map_browser_assets()
        self.browser.core.Navigate("https://midas-dashboard.example/index.html")
        self.after(50, self._check_page_ready)
        self._page_timeout_id = self.after(30000, self._on_page_timeout)

    def _map_browser_assets(self):
        from Microsoft.Web.WebView2.Core import CoreWebView2HostResourceAccessKind

        plotly_location = plotly.__file__
        if plotly_location is None:
            raise RuntimeError("Could not locate the installed Plotly package.")
        plotly_directory = Path(plotly_location).parent / "package_data"
        if not (plotly_directory / "plotly.min.js").is_file():
            raise RuntimeError("The installed Plotly package is missing plotly.min.js.")
        access = CoreWebView2HostResourceAccessKind.Allow
        self.browser.core.SetVirtualHostNameToFolderMapping(
            "midas-dashboard.example", self._page_directory.name, access
        )
        self.browser.core.SetVirtualHostNameToFolderMapping(
            "midas-plotly.example", str(plotly_directory), access
        )

    def _check_page_ready(self):
        if self._closed or self._failed or self._ready or self._page_check_pending:
            return
        self._page_check_pending = True
        self.browser.evaluate_js(
            "typeof Plotly !== 'undefined' && typeof window.renderDashboard === 'function'",
            self._queue_page_ready,
        )

    def _queue_page_ready(self, page_ready):
        self._browser_events.put(("page", bool(page_ready)))

    def _on_page_ready(self, page_ready):
        self._page_check_pending = False
        if self._failed or self._ready:
            return
        if page_ready:
            self._ready = True
            if self._page_timeout_id is not None:
                self.after_cancel(self._page_timeout_id)
                self._page_timeout_id = None
            if self._pending_content is not None:
                self._dispatch_render()
            return
        if time.monotonic() < self._page_load_deadline:
            self.after(50, self._check_page_ready)

    def _on_page_timeout(self):
        self._page_timeout_id = None
        if not self._ready and not self._failed:
            self._show_browser_error("The chart page did not become ready within 30 seconds.")

    def _show_browser_error(self, message):
        self._failed = True
        logger.error("Interactive chart dashboard failed: %s", message)
        self.browser.destroy()
        error = ctk.CTkLabel(
            self,
            text=f"Interactive charts are unavailable: {message}",
            wraplength=720,
            justify="left",
        )
        error.pack(fill="both", expand=True, padx=20, pady=20)

    def _process_browser_events(self):
        self._event_poll_id = None
        if self._closed:
            return
        while True:
            try:
                event = self._browser_events.get_nowait()
            except Empty:
                break
            self._handle_browser_event(event)
        self._event_poll_id = self.after(25, self._process_browser_events)

    def _handle_browser_event(self, event):
        kind, *values = event
        if kind == "browser":
            self._handle_browser_initialization(*values)
        elif kind == "page":
            self._on_page_ready(*values)
        elif kind == "render":
            self._on_render_status(*values)

    def _handle_browser_initialization(self, succeeded, message):
        if succeeded:
            self.after(100, self._load_page)
            return
        error = message or "Unknown WebView2 initialization error."
        self._show_browser_error(error)

    def _check_render_status(self):
        self._render_check_id = None
        if not self._render_status_pending or self._closed:
            return
        if time.monotonic() >= self._render_deadline:
            self._render_status_pending = False
            logger.error("Plotly charts did not finish rendering within 30 seconds.")
            return
        self.browser.evaluate_js(
            "JSON.stringify(window.dashboardRenderStatus)",
            self._queue_render_status,
        )

    def _queue_render_status(self, status):
        self._browser_events.put(("render", status))

    def _on_render_status(self, raw_status):
        if not raw_status:
            self._schedule_render_status_check()
            return
        status = self._parse_render_status(raw_status)
        if status is None:
            return
        if not status.get("complete"):
            self._schedule_render_status_check()
            return
        self._render_status_pending = False
        self._last_render_complete = True
        self._last_render_errors = status.get("errors", [])
        self._log_render_errors()

    def _parse_render_status(self, raw_status):
        try:
            status = json.loads(raw_status) if isinstance(raw_status, str) else raw_status
        except json.JSONDecodeError as error:
            logger.error("Could not read the Plotly render status: %s", error)
            self._render_status_pending = False
            return None
        if not isinstance(status, dict):
            logger.error("Plotly returned an invalid render status: %r", status)
            self._render_status_pending = False
            return None
        return status

    def _schedule_render_status_check(self):
        self._render_check_id = self.after(100, self._check_render_status)

    def _log_render_errors(self):
        for error in self._last_render_errors:
            logger.error("Plotly chart '%s' failed: %s", error["chart"], error["message"])

    def _cleanup_page_directory(self, event):
        if event.widget is self:
            self._closed = True
            if self._event_poll_id is not None:
                self.after_cancel(self._event_poll_id)
                self._event_poll_id = None
            if self._render_check_id is not None:
                self.after_cancel(self._render_check_id)
            if self._page_timeout_id is not None:
                self.after_cancel(self._page_timeout_id)
            self._page_directory.cleanup()

    def _make_payload(self, figures, metrics, headers, rows, subtitle):
        figure_json = {chart_id: json.loads(figure.to_json()) for chart_id, figure in figures.items()}
        return {
            "figures": figure_json,
            "metrics": self.page_builder.metrics_markup(metrics),
            "holdings": self.page_builder.table_markup(headers, rows) if self.include_holdings else "",
            "subtitle": subtitle,
            "theme": self._theme,
        }

    def _dispatch_render(self):
        payload = json.dumps(self._pending_content, cls=PlotlyJSONEncoder, separators=(",", ":"))
        self._last_render_complete = False
        self.browser.evaluate_js(f"window.renderDashboard({payload})")
        self._render_status_pending = True
        self._render_deadline = time.monotonic() + 30
        self._render_check_id = self.after(100, self._check_render_status)
