from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChartPalette:
    background: str
    card: str
    text: str
    muted: str
    grid: str
    accent: str
    secondary: str
    positive: str
    negative: str
    fill: str


class ChartTheme:
    def palette(self, mode: str) -> ChartPalette:
        if mode == "Dark":
            return self._dark_palette()
        return self._light_palette()

    def _light_palette(self) -> ChartPalette:
        return ChartPalette(
            background="#f3f6fb",
            card="#ffffff",
            text="#1f2937",
            muted="#64748b",
            grid="#e4eaf2",
            accent="#2377d2",
            secondary="#8b5cf6",
            positive="#169b70",
            negative="#d84f62",
            fill="rgba(35, 119, 210, 0.14)",
        )

    def _dark_palette(self) -> ChartPalette:
        return ChartPalette(
            background="#171c27",
            card="#222a38",
            text="#e7edf7",
            muted="#a5b2c5",
            grid="#344156",
            accent="#67a9ff",
            secondary="#b596ff",
            positive="#47ce93",
            negative="#ff7888",
            fill="rgba(103, 169, 255, 0.16)",
        )

    def layout(self, mode: str) -> dict:
        palette = self.palette(mode)
        return {
            "template": "none",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "font": {"family": "Segoe UI, sans-serif", "color": palette.text},
            "margin": {"l": 52, "r": 20, "t": 20, "b": 45},
            "hoverlabel": {"bgcolor": palette.card, "font": {"color": palette.text}},
            "xaxis": self._axis_options(palette),
            "yaxis": self._axis_options(palette),
        }

    def _axis_options(self, palette: ChartPalette) -> dict:
        return {
            "showline": False,
            "zerolinecolor": palette.grid,
            "gridcolor": palette.grid,
            "tickfont": {"color": palette.muted},
            "title": {"font": {"color": palette.muted}},
        }
