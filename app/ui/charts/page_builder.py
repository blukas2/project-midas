from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence


@dataclass(frozen=True)
class ChartCardSpec:
    chart_id: str
    title: str
    wide: bool = False


class DashboardPageBuilder:
    def build(
        self,
        title: str,
        chart_cards: Sequence[ChartCardSpec],
        include_metrics: bool = False,
        include_holdings: bool = False,
    ) -> str:
        return self._document(title, chart_cards, include_metrics, include_holdings)

    def metrics_markup(self, metrics: Sequence[tuple[str, str]]) -> str:
        items = [self._metric_markup(label, value) for label, value in metrics]
        return "".join(items)

    def table_markup(self, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
        heading = "".join(f"<th>{escape(str(value))}</th>" for value in headers)
        body = self._table_rows(rows, len(headers))
        return f"<table><thead><tr>{heading}</tr></thead><tbody>{body}</tbody></table>"

    def _document(self, title, chart_cards, include_metrics, include_holdings):
        cards = self._dashboard_cards(chart_cards, include_holdings)
        metrics = '<div id="metrics" class="metrics"></div>' if include_metrics else ""
        script = self._render_script([card.chart_id for card in chart_cards], include_holdings)
        layout_class = "portfolio-layout" if include_holdings else ""
        return self._html_document(title, cards, metrics, layout_class, script)

    def _dashboard_cards(self, chart_cards, include_holdings):
        if not include_holdings:
            return self._chart_cards(chart_cards)
        initial_cards = self._chart_cards(chart_cards[:2])
        remaining_cards = self._chart_cards(chart_cards[2:])
        return initial_cards + self._holdings_card() + remaining_cards

    def _chart_cards(self, chart_cards):
        cards = [self._chart_card(card) for card in chart_cards]
        return "".join(cards)

    def _chart_card(self, card: ChartCardSpec):
        wide_class = " wide" if card.wide else ""
        return (
            f'<section id="{escape(card.chart_id)}" class="card{wide_class}">'
            f'<h2>{escape(card.title)}</h2>'
            f'<div id="{escape(card.chart_id)}-plot" class="plot"></div></section>'
        )

    def _holdings_card(self):
        return (
            '<section id="holdings-card" class="card">'
            '<h2>Holdings</h2><div id="holdings"></div></section>'
        )

    def _metric_markup(self, label, value):
        return (
            f'<div class="metric"><span>{escape(str(label))}</span>'
            f'<strong>{escape(str(value))}</strong></div>'
        )

    def _table_rows(self, rows, column_count):
        if not rows:
            return f'<tr><td colspan="{column_count}">No holdings yet</td></tr>'
        return "".join(self._table_row(row) for row in rows)

    def _table_row(self, row):
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        return f"<tr>{cells}</tr>"

    def _render_script(self, chart_ids, include_holdings):
        ids = repr(list(chart_ids))
        update_holdings = "document.getElementById('holdings').innerHTML = payload.holdings;" if include_holdings else ""
        return f"""
        <script>
        const chartIds = {ids};
        let dashboardRenderId = 0;
        window.applyTheme = function(theme) {{
            document.documentElement.dataset.theme = theme;
            const dark = theme === 'Dark';
            const text = dark ? '#e7edf7' : '#1f2937';
            const grid = dark ? '#344156' : '#e4eaf2';
            chartIds.forEach(function(id) {{
                const chart = document.getElementById(id + '-plot');
                if (chart && chart.data) {{
                    Plotly.relayout(chart, {{
                        'font.color': text,
                        'xaxis.tickfont.color': dark ? '#a5b2c5' : '#64748b',
                        'yaxis.tickfont.color': dark ? '#a5b2c5' : '#64748b',
                        'xaxis.gridcolor': grid,
                        'yaxis.gridcolor': grid
                    }});
                }}
            }});
        }};
        window.renderDashboard = function(payload) {{
            document.documentElement.dataset.theme = payload.theme;
            const metrics = document.getElementById('metrics');
            if (metrics) metrics.innerHTML = payload.metrics;
            document.getElementById('subtitle').textContent = payload.subtitle;
            {update_holdings}
            const renderId = ++dashboardRenderId;
            const errors = [];
            window.dashboardRenderStatus = {{complete: false, errors: errors}};
            const renders = [];
            chartIds.forEach(function(id) {{
                const chart = document.getElementById(id + '-plot');
                const figure = payload.figures[id];
                if (!figure) return;
                try {{
                    renders.push(Plotly.react(chart, figure.data, figure.layout, {{
                        responsive: true, displaylogo: false, scrollZoom: true,
                        modeBarButtonsToRemove: ['lasso2d', 'select2d']
                    }}).catch(function(error) {{
                        window.reportChartError(id, chart, error, errors);
                    }}));
                }} catch (error) {{
                    window.reportChartError(id, chart, error, errors);
                }}
            }});
            Promise.all(renders).then(function() {{
                if (renderId !== dashboardRenderId) return;
                window.applyTheme(payload.theme);
                window.dashboardRenderStatus = {{complete: true, errors: errors}};
            }});
        }};
        window.reportChartError = function(id, chart, error, errors) {{
            const message = error && error.message ? error.message : String(error);
            errors.push({{chart: id, message: message}});
            chart.textContent = 'Chart could not be rendered: ' + message;
        }};
        </script>
        """

    def _html_document(self, title, cards, metrics, layout_class, script):
        return f"""<!doctype html>
        <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>{self._stylesheet()}</style>
        <script src="https://midas-plotly.example/plotly.min.js"></script></head>
        <body><main><header><h1>{escape(title)}</h1><p id="subtitle"></p></header>
        {metrics}<div class="dashboard-grid {layout_class}">{cards}</div></main>{script}</body></html>"""

    def _stylesheet(self):
        return """
        :root { color-scheme: light; --background: #f3f6fb; --card: #fff; --text: #1f2937;
                --muted: #64748b; --border: #e4eaf2; }
        :root[data-theme="Dark"] { color-scheme: dark; --background: #171c27; --card: #222a38;
                --text: #e7edf7; --muted: #a5b2c5; --border: #344156; }
        * { box-sizing: border-box; }
        body { margin: 0; background: var(--background); color: var(--text);
               font: 14px "Segoe UI", sans-serif; overflow-y: auto; }
        main { width: 100%; margin: 0 auto; padding: 14px; }
        header { display: flex; align-items: baseline; justify-content: space-between; margin: 0 2px 14px; }
        h1 { font-size: 21px; margin: 0; } h2 { font-size: 14px; margin: 0 0 8px; }
        #subtitle { color: var(--muted); margin: 0; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                   gap: 12px; margin-bottom: 14px; }
        .metric, .card { background: var(--card); border: 1px solid var(--border);
                         border-radius: 14px; box-shadow: 0 2px 8px rgba(25, 42, 70, .06); }
        .metric { display: flex; flex-direction: column; gap: 6px; padding: 13px 16px; }
        .metric span { color: var(--muted); font-size: 12px; }
        .metric strong { font-size: 19px; font-weight: 650; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr));
                          gap: 12px; align-items: stretch; }
        .card { grid-column: span 6; min-width: 0; min-height: 300px; padding: 12px; }
        .card.wide { grid-column: span 12; }
        .card .plot { width: 100%; height: 250px; }
        .card.wide .plot { height: 300px; }
        .portfolio-layout #portfolio-history { grid-column: span 8; }
        .portfolio-layout #allocation { grid-column: span 4; }
        .portfolio-layout #holdings-card { grid-column: span 6; }
        .portfolio-layout #portfolio-returns,
        .portfolio-layout #annualized-returns { grid-column: span 3; }
        .portfolio-layout #portfolio-volatility { grid-column: span 4; }
        .portfolio-layout #correlation { grid-column: span 8; }
        #asset-history { grid-column: span 8; }
        #asset-returns { grid-column: span 4; }
        .portfolio-layout #portfolio-history .plot,
        .portfolio-layout #correlation .plot { height: 280px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }
        th { color: var(--muted); font-size: 11px; text-transform: uppercase; }
        @media (max-width: 1050px) {
            .portfolio-layout #portfolio-history,
            .portfolio-layout #allocation,
            .portfolio-layout #holdings-card,
            .portfolio-layout #portfolio-returns,
            .portfolio-layout #annualized-returns,
            .portfolio-layout #portfolio-volatility,
            .portfolio-layout #correlation { grid-column: span 6; }
            .portfolio-layout #correlation { grid-column: span 12; }
            #asset-history, #asset-returns { grid-column: span 6; }
        }
        @media (max-width: 760px) {
            main { padding: 9px; }
            .dashboard-grid { grid-template-columns: minmax(0, 1fr); }
            .card, .card.wide,
            .portfolio-layout #portfolio-history,
            .portfolio-layout #allocation,
            .portfolio-layout #holdings-card,
            .portfolio-layout #portfolio-returns,
            .portfolio-layout #annualized-returns,
            .portfolio-layout #portfolio-volatility,
            .portfolio-layout #correlation,
            #asset-history, #asset-returns { grid-column: span 1; }
            header { align-items: flex-start; flex-direction: column; gap: 4px; }
        }
        """
