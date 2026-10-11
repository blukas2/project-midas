from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ui.charts.chart_theme import ChartTheme


class FigureFactory:
    def __init__(self, theme: ChartTheme | None = None):
        self.theme = theme or ChartTheme()

    def line_chart(
        self,
        series: Sequence[tuple[str, Sequence[Any], Sequence[float]]],
        mode: str,
        yaxis_title: str = "",
        date_axis: bool = True,
    ) -> go.Figure:
        figure = go.Figure()
        self._add_line_traces(figure, series, mode)
        figure.update_layout(**self.theme.layout(mode), hovermode="x unified")
        self._configure_line_axes(figure, yaxis_title, date_axis)
        return self._show_empty_state(figure, mode)

    def bar_chart(
        self, values: Mapping[str, float], mode: str, yaxis_title: str = "Return"
    ) -> go.Figure:
        figure = go.Figure()
        periods, returns = self._valid_values(values)
        if periods:
            self._add_bar_trace(
                figure, periods, returns, mode, "Portfolio", yaxis_title != "Volatility"
            )
        figure.update_layout(**self.theme.layout(mode), showlegend=False)
        self._configure_bar_axes(figure, yaxis_title)
        return self._show_empty_state(figure, mode)

    def grouped_bar_chart(
        self,
        series: Sequence[tuple[str, Mapping[str, float]]],
        mode: str,
        yaxis_title: str = "Return",
    ) -> go.Figure:
        figure = go.Figure()
        periods = self._periods(series)
        self._add_grouped_bar_traces(figure, series, periods, mode)
        figure.update_layout(**self.theme.layout(mode), barmode="group")
        self._configure_bar_axes(figure, yaxis_title)
        return self._show_empty_state(figure, mode)

    def heatmap(self, matrix: pd.DataFrame, mode: str) -> go.Figure:
        figure = go.Figure()
        if not matrix.empty:
            self._add_heatmap_trace(figure, matrix)
        layout = self.theme.layout(mode)
        layout["margin"] = {"l": 70, "r": 30, "t": 10, "b": 65}
        figure.update_layout(**layout)
        return self._show_empty_state(figure, mode)

    def donut_chart(self, values: Mapping[str, float], mode: str) -> go.Figure:
        figure = go.Figure()
        labels, amounts = self._valid_values(values)
        if labels:
            self._add_donut_trace(figure, labels, amounts, mode)
        layout = self.theme.layout(mode)
        layout.update({"showlegend": False, "margin": {"l": 10, "r": 10, "t": 10, "b": 10}})
        figure.update_layout(**layout)
        return self._show_empty_state(figure, mode)

    def _add_line_traces(self, figure, series, mode):
        palette = self.theme.palette(mode)
        colors = (palette.accent, palette.secondary)
        for index, (name, dates, values) in enumerate(series):
            if len(dates) != len(values) or len(dates) == 0:
                continue
            self._add_line_trace(figure, name, dates, values, colors[index % len(colors)], palette, len(series) == 1)

    def _add_line_trace(self, figure, name, dates, values, color, palette, fill):
        figure.add_trace(go.Scatter(
            x=list(dates), y=list(values), name=name, mode="lines",
            line={"color": color, "width": 2.5},
            fill="tozeroy" if fill else None,
            fillcolor=palette.fill if fill else None,
            hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.2f}<extra>%{fullData.name}</extra>",
        ))

    def _configure_line_axes(self, figure, title, date_axis):
        figure.update_yaxes(title_text=title)
        if date_axis:
            figure.update_xaxes(
                rangeselector={"buttons": self._range_buttons()},
                rangeslider={"visible": True, "thickness": 0.08},
                type="date",
            )
        if len(figure.data) > 1:
            figure.update_layout(legend={"orientation": "h", "y": 1.12, "x": 0})

    def _range_buttons(self) -> list[dict]:
        return [
            {"count": 1, "label": "1m", "step": "month", "stepmode": "backward"},
            {"count": 6, "label": "6m", "step": "month", "stepmode": "backward"},
            {"count": 1, "label": "1y", "step": "year", "stepmode": "backward"},
            {"count": 5, "label": "5y", "step": "year", "stepmode": "backward"},
            {"label": "Max", "step": "all"},
        ]

    def _add_bar_trace(self, figure, periods, values, mode, name, color_by_sign):
        palette = self.theme.palette(mode)
        colors = self._bar_colors(values, palette, color_by_sign)
        figure.add_trace(go.Bar(
            x=periods, y=values, name=name, marker_color=colors,
            text=[f"{value:.1f}%" for value in values], textposition="outside",
            hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
            cliponaxis=False,
        ))

    def _bar_colors(self, values, palette, color_by_sign):
        if not color_by_sign:
            return [palette.accent] * len(values)
        return [palette.positive if value >= 0 else palette.negative for value in values]

    def _add_grouped_bar_traces(self, figure, series, periods, mode):
        palette = self.theme.palette(mode)
        colors = (palette.accent, palette.secondary)
        for index, (name, values) in enumerate(series):
            aligned = [self._finite_value(values.get(period)) for period in periods]
            self._add_grouped_bar_trace(figure, name, periods, aligned, colors[index % len(colors)])

    def _add_grouped_bar_trace(self, figure, name, periods, values, color):
        labels = [None if value is None else f"{value:.1f}%" for value in values]
        figure.add_trace(go.Bar(
            x=periods, y=values, name=name, marker_color=color, text=labels,
            textposition="outside", hovertemplate="%{x}: %{y:.2f}%<extra>%{fullData.name}</extra>",
            cliponaxis=False,
        ))

    def _configure_bar_axes(self, figure, title):
        figure.update_yaxes(title_text=title, ticksuffix="%", rangemode="tozero")
        figure.update_xaxes(showgrid=False)

    def _add_heatmap_trace(self, figure, matrix):
        figure.add_trace(go.Heatmap(
            z=matrix.values.tolist(), x=[str(value) for value in matrix.columns],
            y=[str(value) for value in matrix.index], zmin=-1, zmax=1,
            colorscale="RdYlGn", colorbar={"title": "Correlation"},
            hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>",
        ))

    def _add_donut_trace(self, figure, labels, values, mode):
        palette = self.theme.palette(mode)
        figure.add_trace(go.Pie(
            labels=labels, values=values, hole=0.68, sort=False,
            marker={"colors": self._donut_colors(len(labels), palette)},
            textinfo="label+percent", hovertemplate="%{label}: %{percent}<extra></extra>",
        ))

    def _donut_colors(self, count: int, palette) -> list[str]:
        colors = [palette.accent, palette.secondary, palette.positive, palette.negative]
        return [colors[index % len(colors)] for index in range(count)]

    def _valid_values(self, values: Mapping[str, float]) -> tuple[list[str], list[float]]:
        entries = [
            (str(label), numeric)
            for label, value in values.items()
            if (numeric := self._finite_value(value)) is not None
        ]
        return [label for label, _ in entries], [value for _, value in entries]

    def _finite_value(self, value):
        if value is None or pd.isna(value):
            return None
        numeric = float(value)
        return numeric if isfinite(numeric) else None

    def _periods(self, series) -> list[str]:
        return list(dict.fromkeys(period for _, values in series for period in values))

    def _show_empty_state(self, figure, mode):
        if not figure.data:
            palette = self.theme.palette(mode)
            figure.add_annotation(
                text="No data available", showarrow=False,
                font={"color": palette.muted, "size": 14},
            )
        return figure
