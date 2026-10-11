from unittest.mock import Mock

import pytest

from ui.main_window.analyze_portfolio import AnalyzePortfolioWindow
from backend.portfolio.portfolio_analyzer import AnalysisResult


class TestAnalyzePortfolioWindow:
    def test_constructor_configures_popup_and_runs_analysis(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr(
            "ui.main_window.analyze_portfolio.ctk.CTkToplevel", Mock(return_value=popup)
        )
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window._run_analysis = Mock()
        backend = object()

        window.__init__(object(), backend)

        assert window.backend is backend
        popup.title.assert_called_once_with("Portfolio Analysis")
        popup.geometry.assert_called_once_with("1100x700")
        window._run_analysis.assert_called_once_with()

    def test_empty_portfolio_warns_and_closes(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window.backend = Mock()
        window.backend.portfolio.content = {}
        window.window = Mock()
        warning = Mock()
        monkeypatch.setattr("ui.main_window.analyze_portfolio.msgbox.showwarning", warning)

        window._run_analysis()

        warning.assert_called_once()
        window.window.destroy.assert_called_once_with()

    def test_analysis_exception_is_reported_and_closes(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window.backend = Mock()
        window.backend.portfolio.content = {"ABC": object()}
        window.backend.analyze_portfolio.side_effect = RuntimeError("failure")
        window.window = Mock()
        error = Mock()
        monkeypatch.setattr("ui.main_window.analyze_portfolio.msgbox.showerror", error)

        window._run_analysis()

        assert error.call_args.args[1] == "failure"
        window.window.destroy.assert_called_once_with()

    def test_successful_analysis_builds_ui(self):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window.backend = Mock()
        window.backend.portfolio.content = {"ABC": object()}
        result = AnalysisResult()
        window.backend.analyze_portfolio.return_value = result
        window.window = Mock()
        window._build_ui = Mock()

        window._run_analysis()

        window._build_ui.assert_called_once_with(result)

    def test_sort_treeview_numeric_values_and_toggle(self):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window._sort_ascending = {}
        tree = Mock()
        tree.get_children.return_value = ["a", "b", "c"]
        values = {"a": "10.0%", "b": "2.0%", "c": "5.0%"}
        tree.set.side_effect = lambda item, column: values[item]

        window._sort_treeview(tree, "risk")

        assert [call.args for call in tree.move.call_args_list] == [
            ("b", "", 0), ("c", "", 1), ("a", "", 2)
        ]
        tree.move.reset_mock()
        window._sort_treeview(tree, "risk")
        assert [call.args[0] for call in tree.move.call_args_list] == ["a", "c", "b"]

    def test_sort_treeview_ticker_alphabetically(self):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window._sort_ascending = {}
        tree = Mock()
        tree.get_children.return_value = ["a", "b"]
        tree.set.side_effect = lambda item, column: {"a": "ZED", "b": "ABC"}[item]

        window._sort_treeview(tree, "ticker")

        assert [call.args[0] for call in tree.move.call_args_list] == ["b", "a"]

    def test_copy_metrics_to_clipboard(self):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window._metrics = [("Beta", "1.2"), ("Alpha", "2%")]
        window.window = Mock()

        window._copy_metrics_to_clipboard()

        window.window.clipboard_clear.assert_called_once_with()
        window.window.clipboard_append.assert_called_once_with("Beta: 1.2\nAlpha: 2%")

    def test_metric_section_records_clipboard_values(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window._metrics = []
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkFrame", Mock())
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkLabel", Mock())

        window._add_metric_section(Mock(), "Beta", 1.2, "Tracks market")

        assert window._metrics == [("Beta", "1.2")]

    def test_risk_table_formats_rows_and_builds_tree(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        result = AnalysisResult(
            risk_contributions={"A": 60, "B": 40},
            return_contributions={"A": 2.25, "B": -1.5},
            portfolio_weights={"A": 70, "B": 30},
        )
        tree = Mock()
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ttk.Treeview", Mock(return_value=tree))
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkLabel", Mock())
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkFrame", Mock())

        window._add_risk_contribution_table(Mock(), result)

        assert tree.insert.call_count == 2
        assert tree.insert.call_args_list[0].kwargs["values"] == (
            "A", "60.0%", "70.0%", "2.25%"
        )
        assert window._sort_ascending == {}

    def test_build_ui_connects_sections_and_scroll_region(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        scrollable = Mock()
        window.window = Mock()
        window._create_scrollable_frame = Mock(return_value=scrollable)
        window._add_header = Mock()
        window._add_metric_section = Mock()
        window._add_copy_button = Mock()
        window._add_risk_contribution_table = Mock()
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkFrame", Mock())
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkLabel", Mock())
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkButton", Mock())

        window._build_ui(AnalysisResult())

        assert window._add_metric_section.call_count == 11
        window._add_copy_button.assert_called_once()
        window._add_risk_contribution_table.assert_called_once()

    def test_scrollable_frame_uses_customtkinter_container(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        window.window = object()
        frame = Mock()
        monkeypatch.setattr(
            "ui.main_window.analyze_portfolio.ctk.CTkScrollableFrame", Mock(return_value=frame)
        )

        actual_frame = window._create_scrollable_frame()

        assert actual_frame is frame
        frame.pack.assert_called_once_with(fill="both", expand=True)

    def test_header_and_section_label(self, monkeypatch):
        window = AnalyzePortfolioWindow.__new__(AnalyzePortfolioWindow)
        label_factory = Mock()
        separator_factory = Mock()
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkLabel", label_factory)
        monkeypatch.setattr("ui.main_window.analyze_portfolio.ctk.CTkFrame", separator_factory)
        parent = Mock()

        window._add_header(parent, "Portfolio Analysis")
        window._add_section_label(parent, "Breakdown")

        assert label_factory.call_count == 2
        assert separator_factory.call_count == 2
