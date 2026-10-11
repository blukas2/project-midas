from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ui.main_window.popups import (
    ChangePositionWindow,
    NewPortfolioWindow,
    OpenPortfolioWindow,
)


class TestChangePositionWindow:
    @pytest.fixture
    def window(self):
        instance = ChangePositionWindow.__new__(ChangePositionWindow)
        instance.window = object()
        instance.entry_ticker = Mock()
        instance.entry_quantity = Mock()
        return instance

    @pytest.mark.parametrize(
        ("ticker", "quantity", "expected"),
        [("", "2", (None, None)), ("ABC", "bad", (None, None)),
         ("ABC", "0", (None, None)), (" ABC ", "-2", ("ABC", -2))],
    )
    def test_validate_inputs(self, monkeypatch, window, ticker, quantity, expected):
        window.entry_ticker.get.return_value = ticker
        window.entry_quantity.get.return_value = quantity
        monkeypatch.setattr("ui.main_window.popups.msgbox.showerror", Mock())

        assert window._validate_inputs() == expected

    def test_constructor_defines_position_fields(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr("ui.main_window.popups.tk.Toplevel", Mock(return_value=popup))
        for name in ("Label", "Entry", "Button"):
            monkeypatch.setattr("ui.main_window.popups.tk." + name, Mock())

        window = ChangePositionWindow(object(), Mock(), Mock())

        assert window.window is popup
        popup.title.assert_called_once_with("Change Position")
        assert window.entry_ticker is not None
        assert window.entry_quantity is not None

    def test_change_position_calculates_refreshes_and_closes(self, window):
        portfolio = SimpleNamespace(change_position=Mock(), calculate=Mock(), content={"ABC": object()})
        window.backend = SimpleNamespace(portfolio=portfolio)
        window.subject = SimpleNamespace(refresh_table=Mock())
        window.window = Mock()
        window._validate_inputs = lambda: ("ABC", 2)

        window.change_position()

        portfolio.change_position.assert_called_once_with("ABC", 2)
        portfolio.calculate.assert_called_once_with()
        window.subject.refresh_table.assert_called_once_with()
        window.window.destroy.assert_called_once_with()

    def test_change_position_surfaces_validation_error(self, monkeypatch, window):
        window.backend = SimpleNamespace(
            portfolio=SimpleNamespace(change_position=Mock(side_effect=ValueError("invalid")))
        )
        window._validate_inputs = lambda: ("ABC", -3)
        error = Mock()
        monkeypatch.setattr("ui.main_window.popups.msgbox.showerror", error)

        window.change_position()

        error.assert_called_once()
        assert error.call_args.kwargs["message"] == "invalid"

    def test_analyze_impact_requires_nonempty_portfolio(self, monkeypatch, window):
        window.backend = SimpleNamespace(portfolio=SimpleNamespace(content={}))
        window._validate_inputs = lambda: ("ABC", 1)
        warning = Mock()
        monkeypatch.setattr("ui.main_window.popups.msgbox.showwarning", warning)

        window.analyze_impact()

        warning.assert_called_once()

    def test_analyze_impact_creates_comparison_popup(self, monkeypatch, window):
        current, projected = object(), object()
        window.backend = SimpleNamespace(
            portfolio=SimpleNamespace(content={"ABC": object()}),
            analyze_impact=Mock(return_value=(current, projected)),
        )
        window._validate_inputs = lambda: ("ABC", 2)
        popup = Mock()
        monkeypatch.setattr("ui.main_window.popups.AnalyzeImpactWindow", popup)

        window.analyze_impact()

        popup.assert_called_once_with(window.window, current, projected, "ABC", 2)

    def test_analyze_impact_reports_runtime_errors(self, monkeypatch, window):
        window.backend = SimpleNamespace(
            portfolio=SimpleNamespace(content={"ABC": object()}),
            analyze_impact=Mock(side_effect=RuntimeError("broken")),
        )
        window._validate_inputs = lambda: ("ABC", 1)
        error = Mock()
        monkeypatch.setattr("ui.main_window.popups.msgbox.showerror", error)

        window.analyze_impact()

        assert error.call_args.kwargs["message"] == "broken"

    def test_prefill_ticker_replaces_entry_contents(self, window):
        window.entry_ticker.delete = Mock()
        window.entry_ticker.insert = Mock()

        window._prefill_ticker("ABC")

        window.entry_ticker.delete.assert_called_once()
        window.entry_ticker.insert.assert_called_once_with(0, "ABC")

    def test_close_methods_destroy_their_windows(self):
        change = ChangePositionWindow.__new__(ChangePositionWindow)
        opening = OpenPortfolioWindow.__new__(OpenPortfolioWindow)
        creating = NewPortfolioWindow.__new__(NewPortfolioWindow)
        change.window = Mock()
        opening.window = Mock()
        creating.window = Mock()

        change.close()
        opening.close()
        creating.close()

        change.window.destroy.assert_called_once()
        opening.window.destroy.assert_called_once()
        creating.window.destroy.assert_called_once()


class TestPortfolioPopups:
    def test_open_portfolio_constructor_selects_first_name(self, monkeypatch):
        popup = Mock()
        dropdown = Mock()
        string_var = Mock()
        monkeypatch.setattr("ui.main_window.popups.tk.Toplevel", Mock(return_value=popup))
        monkeypatch.setattr("ui.main_window.popups.tk.Label", Mock())
        monkeypatch.setattr("ui.main_window.popups.tk.Button", Mock())
        monkeypatch.setattr("ui.main_window.popups.tk.StringVar", Mock(return_value=string_var))
        monkeypatch.setattr("ui.main_window.popups.tk.OptionMenu", Mock(return_value=dropdown))
        backend = SimpleNamespace(
            file_manager=SimpleNamespace(portfolio_names_list=["Fund", "Other"])
        )

        window = OpenPortfolioWindow(object(), backend, Mock())

        string_var.set.assert_called_once_with("Fund")
        assert window.dropd_selecter is dropdown
        popup.title.assert_called_once_with("Opening Portfolio...")

    def test_open_portfolio_loads_selected_and_refreshes(self):
        popup = OpenPortfolioWindow.__new__(OpenPortfolioWindow)
        popup.dropd_content = SimpleNamespace(get=lambda: "Fund")
        popup.backend = SimpleNamespace(load_portfolio=Mock())
        popup.main_window = SimpleNamespace(recalculate_portfolio=Mock())
        popup.window = Mock()

        popup.load_selected_portfolio()

        popup.backend.load_portfolio.assert_called_once_with("Fund")
        popup.main_window.recalculate_portfolio.assert_called_once_with()
        popup.window.destroy.assert_called_once_with()

    def test_new_portfolio_refuses_duplicate(self, monkeypatch):
        popup = NewPortfolioWindow.__new__(NewPortfolioWindow)
        popup.entry_portfolio_name = SimpleNamespace(get=lambda: "Fund")
        popup.backend = SimpleNamespace(
            file_manager=SimpleNamespace(
                list_portfolio_names=lambda: None,
                portfolio_names_list=["Fund"],
            ),
            new_portfolio=Mock(),
        )
        popup.main_window = SimpleNamespace(display_portfolio_name=Mock())
        popup.window = Mock()
        error = Mock()
        monkeypatch.setattr("ui.main_window.popups.msgbox.showerror", error)

        popup.new_portfolio()

        error.assert_called_once()
        popup.backend.new_portfolio.assert_not_called()
        popup.window.destroy.assert_not_called()

    def test_new_portfolio_creates_unique_name(self):
        popup = NewPortfolioWindow.__new__(NewPortfolioWindow)
        popup.entry_portfolio_name = SimpleNamespace(get=lambda: "New Fund")
        popup.backend = SimpleNamespace(
            file_manager=SimpleNamespace(
                list_portfolio_names=lambda: None,
                portfolio_names_list=["Existing"],
            ),
            new_portfolio=Mock(),
        )
        popup.main_window = SimpleNamespace(display_portfolio_name=Mock())
        popup.window = Mock()

        popup.new_portfolio()

        popup.backend.new_portfolio.assert_called_once_with("New Fund")
        popup.main_window.display_portfolio_name.assert_called_once_with()
        popup.window.destroy.assert_called_once_with()

    def test_new_portfolio_constructor_places_name_entry(self, monkeypatch):
        popup = Mock()
        monkeypatch.setattr("ui.main_window.popups.tk.Toplevel", Mock(return_value=popup))
        monkeypatch.setattr("ui.main_window.popups.tk.Label", Mock())
        monkeypatch.setattr("ui.main_window.popups.tk.Entry", Mock())
        monkeypatch.setattr("ui.main_window.popups.tk.Button", Mock())
        backend = SimpleNamespace(file_manager=SimpleNamespace())

        window = NewPortfolioWindow(object(), backend, Mock())

        assert window.entry_portfolio_name is not None
        popup.title.assert_called_once_with("Creating New Portfolio...")
