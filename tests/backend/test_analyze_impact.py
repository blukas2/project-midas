from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ui.main_window.analyze_impact import (
    METRIC_CONFIGS,
    NEGATIVE_COLOR,
    POSITIVE_COLOR,
    AnalyzeImpactWindow,
)


class TestAnalyzeImpactWindow:
    @pytest.fixture
    def window(self):
        instance = AnalyzeImpactWindow.__new__(AnalyzeImpactWindow)
        instance.current = SimpleNamespace(annualized_return_10y=5.0, annualized_return_5y=3.0)
        instance.projected = SimpleNamespace(annualized_return_10y=0.0, annualized_return_5y=3.2)
        return instance

    def test_constructor_configures_popup(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr(
            "ui.main_window.analyze_impact.tk.Toplevel", Mock(return_value=popup)
        )
        window = AnalyzeImpactWindow.__new__(AnalyzeImpactWindow)
        window._build_ui = Mock()
        current, projected = object(), object()

        window.__init__(object(), current, projected, "ABC", -2)

        assert window.current is current
        assert window.projected is projected
        popup.title.assert_called_once_with("Impact Analysis")
        popup.geometry.assert_called_once_with("1100x700")
        window._build_ui.assert_called_once_with("ABC", -2)

    def test_header_describes_direction_and_absolute_quantity(self, window):
        assert window._build_header_text("ABC", 4) == "Impact of adding 4 share(s) of ABC"
        assert window._build_header_text("ABC", -2) == "Impact of removing 2 share(s) of ABC"

    def test_annualized_return_uses_ten_year_then_five_year_then_na(self, window):
        assert window._resolve_annualized_return_period() == ("5y", True)
        window.projected.annualized_return_10y = 1.5
        assert window._resolve_annualized_return_period() == ("10y", True)
        window.projected.annualized_return_10y = 0.0
        window.projected.annualized_return_5y = 0.0
        assert window._resolve_annualized_return_period() == ("10y", False)

    def test_formatting_includes_suffix_and_explicit_sign(self, window):
        assert window._format_value(1.5, "%") == "1.5%"
        assert window._format_change(-1.5, "%", "+.2f") == "-1.50%"

    @pytest.mark.parametrize(
        ("change", "higher_is_better", "expected"),
        [(1, True, POSITIVE_COLOR), (-1, True, NEGATIVE_COLOR),
         (-1, False, POSITIVE_COLOR), (1, False, NEGATIVE_COLOR),
         (0, True, "black"), (1, None, "black")],
    )
    def test_impact_color_reflects_metric_direction(self, window, change, higher_is_better, expected):
        assert window._get_impact_color(change, higher_is_better) == expected

    def test_add_metric_row_renders_signed_delta(self, monkeypatch, window):
        labels = []

        def create_label(*args, **kwargs):
            label = SimpleNamespace(grid=Mock())
            labels.append((args, kwargs, label))
            return label

        monkeypatch.setattr("ui.main_window.analyze_impact.tk.Label", create_label)

        window._add_metric_row(Mock(), 2, "Alpha", 1.0, 2.0, "description", "%", "+.2f", True)

        assert labels[0][1]["text"] == "Alpha:"
        assert labels[3][1]["text"] == "2.0% (+1.00%)"
        assert labels[3][1]["fg"] == POSITIVE_COLOR

    def test_add_annualized_return_uses_best_available_period(self, window):
        window.current.annualized_return_5y_text = "Five years"
        window.projected.annualized_return_5y_text = "Projected"
        window._add_metric_row = Mock()

        next_row = window._add_annualized_return_row(Mock(), 3)

        assert next_row == 4
        assert window._add_metric_row.call_args.args[2:5] == (
            "Annualized Return (5y)", 3.0, 3.2
        )

    def test_metric_rows_include_annualized_and_configured_metrics(self, window):
        for index, (_, attribute, text_attribute, *_rest) in enumerate(METRIC_CONFIGS):
            setattr(window.current, attribute, index + 1)
            setattr(window.projected, attribute, index + 2)
            setattr(window.current, text_attribute, "description")
        window.current.annualized_return_5y_text = "description"
        window._add_metric_row = Mock()

        window._add_metric_rows(Mock())

        assert window._add_metric_row.call_count == len(METRIC_CONFIGS) + 1

    def test_build_ui_places_header_subtitle_and_metrics(self, monkeypatch, window):
        canvas, scrollable = Mock(), Mock()
        window.window = Mock()
        window._create_scrollable_frame = Mock(return_value=(canvas, scrollable))
        window._add_header = Mock()
        window._add_metric_rows = Mock()
        monkeypatch.setattr("ui.main_window.analyze_impact.tk.Label", Mock())
        monkeypatch.setattr("ui.main_window.analyze_impact.tk.Frame", Mock())

        window._build_ui("ABC", 3)

        window._add_header.assert_called_once_with(
            scrollable, "Impact of adding 3 share(s) of ABC"
        )
        window._add_metric_rows.assert_called_once()
        canvas.configure.assert_called_once_with(scrollregion=canvas.bbox("all"))

    def test_create_scrollable_frame_wires_canvas_and_scrollbar(self, monkeypatch, window):
        canvas, scrollbar, frame = Mock(), Mock(), Mock()
        window.window = object()
        monkeypatch.setattr("ui.main_window.analyze_impact.tk.Canvas", Mock(return_value=canvas))
        monkeypatch.setattr("ui.main_window.analyze_impact.tk.Frame", Mock(return_value=frame))
        monkeypatch.setattr(
            "ui.main_window.analyze_impact.ttk.Scrollbar", Mock(return_value=scrollbar)
        )

        actual_canvas, actual_frame = window._create_scrollable_frame()

        assert actual_canvas is canvas
        assert actual_frame is frame
        canvas.create_window.assert_called_once()
        canvas.configure.assert_called_once_with(yscrollcommand=scrollbar.set)

    def test_header_and_missing_annualized_return_are_rendered(self, monkeypatch, window):
        label_factory, separator_factory = Mock(), Mock()
        monkeypatch.setattr("ui.main_window.analyze_impact.tk.Label", label_factory)
        monkeypatch.setattr("ui.main_window.analyze_impact.ttk.Separator", separator_factory)

        window._add_header(Mock(), "Impact")
        window.projected.annualized_return_5y = 0.0
        parent = Mock()
        next_row = window._add_annualized_return_na_row(parent, 2)

        assert next_row == 3
        assert label_factory.call_count == 6
        assert label_factory.call_args_list[-1].kwargs["text"] == (
            "New asset has less than 5 years of history — annualized return comparison is not available."
        )
