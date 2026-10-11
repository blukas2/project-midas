from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd

from ui.charts.figure_factory import FigureFactory
from ui.main_window.main_window import DropdownMenu, MainWindowComponents


class TestMainWindowComponents:
    def test_button_setup(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = object()
        toolbar = Mock()
        monkeypatch.setattr(
            "ui.main_window.main_window.ctk.CTkFrame", Mock(return_value=toolbar)
        )
        button_factory = Mock()
        monkeypatch.setattr("ui.main_window.main_window.ctk.CTkButton", button_factory)

        component._define_buttons()

        assert component.toolbar_frame is toolbar
        assert button_factory.call_count == 3

    def test_display_portfolio_name_creates_and_updates_label(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.toolbar_frame = object()
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(name="Growth"))
        label = Mock()
        monkeypatch.setattr("ui.main_window.main_window.ctk.CTkLabel", Mock(return_value=label))

        component.display_portfolio_name()
        component.backend.portfolio.name = "Income"
        component.display_portfolio_name()

        assert label.configure.call_args.kwargs["text"] == "Portfolio: Income"
        assert label.pack.call_count == 2

    def test_place_components_creates_portfolio_label_before_placing_it(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = Mock()
        component.toolbar_frame = Mock()
        component.btn_change_position = Mock()
        component.btn_recalculate_portfolio = Mock()
        component.btn_analyze_portfolio = Mock()
        component.dashboard = Mock()
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(name="Growth"))
        label = Mock()
        monkeypatch.setattr("ui.main_window.main_window.ctk.CTkLabel", Mock(return_value=label))

        component._place_components()

        assert component.lbl_portfolio_name is label
        component.toolbar_frame.grid.assert_called_once_with(
            row=1, column=0, columnspan=8, sticky="ew", padx=8, pady=6
        )
        component.btn_change_position.pack.assert_called_once_with(side="left", padx=4)
        label.pack.assert_called_once_with(side="left", padx=(12, 8))
        component.dashboard.grid.assert_called_once_with(
            row=2, column=0, columnspan=8, sticky="nsew", padx=10, pady=(0, 10)
        )

    def test_build_figures_maps_portfolio_data_to_interactive_charts(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.chart_factory = FigureFactory()
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(
            history=pd.DataFrame({
                "Date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "Value": [100, 110],
            }),
            returns={"1y": 10},
            annualized_returns={"1y": 8},
            volatility={"1y": 5},
            correlation_matrix=pd.DataFrame({"ABC": [1.0]}, index=["ABC"]),
            content={},
        ))
        monkeypatch.setattr("ui.main_window.main_window.ctk.get_appearance_mode", lambda: "Light")

        figures = component._build_figures()

        assert set(figures) == {
            "portfolio-history", "allocation", "portfolio-returns",
            "annualized-returns", "portfolio-volatility", "correlation",
        }
        assert list(figures["portfolio-history"].data[0].y) == [100, 110]
        assert list(figures["portfolio-returns"].data[0].y) == [10.0]
        assert figures["correlation"].data[0].z == ([1.0],)

    def test_holdings_rows_use_latest_converted_price(self):
        component = MainWindowComponents.__new__(MainWindowComponents)
        asset = SimpleNamespace(
            ticker="ABC",
            quantity=2,
            price_history=pd.DataFrame({"Price": [12.5]}),
            get_longname=lambda: "Alpha",
        )
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(content={"ABC": asset}))

        assert component._holdings_rows() == [("ABC", "Alpha", "2", "12.50 EUR", "25.00 EUR")]

    def test_refresh_table_sends_dashboard_content(self):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(name="Fund"))
        component.dashboard = Mock()
        component._build_figures = Mock(return_value={"history": object()})
        component._build_metrics = Mock(return_value=[("Current value", "100 EUR")])
        component._holdings_rows = Mock(return_value=[("ABC",)])

        component.refresh_table()

        component.dashboard.render.assert_called_once_with(
            component._build_figures.return_value,
            component._build_metrics.return_value,
            ("Ticker", "Name", "Quantity", "Unit price", "Value"),
            [("ABC",)],
            "Fund",
        )

    def test_refresh_theme_applies_current_mode(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.dashboard = Mock()
        monkeypatch.setattr("ui.main_window.main_window.ctk.get_appearance_mode", lambda: "Dark")

        component.refresh_theme()

        component.dashboard.set_theme.assert_called_once_with("Dark")

    def test_recalculate_refreshes_dashboard(self):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(calculate=Mock()))
        component.display_portfolio_name = Mock()
        component.refresh_table = Mock()

        component.recalculate_portfolio()

        component.backend.portfolio.calculate.assert_called_once_with()
        component.display_portfolio_name.assert_called_once_with()
        component.refresh_table.assert_called_once_with()

    def test_window_action_callbacks_open_expected_popups(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = object()
        component.backend = object()
        analyze, change = Mock(), Mock()
        monkeypatch.setattr("ui.main_window.main_window.AnalyzePortfolioWindow", analyze)
        monkeypatch.setattr("ui.main_window.main_window.ChangePositionWindow", change)

        component.analyze_portfolio()
        component.change_position()

        analyze.assert_called_once_with(component.window, component.backend)
        change.assert_called_once_with(component.window, component, component.backend)


class TestDropdownMenu:
    def test_constructor_builds_all_menu_groups(self, monkeypatch):
        root, menu, frame = Mock(), Mock(), Mock()
        monkeypatch.setattr("ui.main_window.main_window.Menu", Mock(return_value=menu))
        monkeypatch.setattr("ui.main_window.main_window.ctk.CTkFrame", Mock(return_value=frame))
        monkeypatch.setattr("ui.main_window.main_window.ctk.CTkButton", Mock())

        dropdown = DropdownMenu(root, object(), object())

        assert dropdown.root is root
        assert menu.add_command.call_count == 6
        frame.grid.assert_called_once()

    def test_portfolio_commands_delegate_to_backend_and_windows(self, monkeypatch):
        menu = DropdownMenu.__new__(DropdownMenu)
        menu.root = Mock()
        menu.backend = SimpleNamespace(
            file_manager=SimpleNamespace(list_portfolio_names=Mock()),
            save_portfolio=Mock(),
        )
        menu.main_window = object()
        open_window, new_window = Mock(), Mock()
        monkeypatch.setattr("ui.main_window.main_window.OpenPortfolioWindow", open_window)
        monkeypatch.setattr("ui.main_window.main_window.NewPortfolioWindow", new_window)

        menu._open_portfolio()
        menu._save_portfolio()
        menu._new_portfolio()

        menu.backend.file_manager.list_portfolio_names.assert_called_once()
        open_window.assert_called_once_with(menu.root, menu.backend, menu.main_window)
        menu.backend.save_portfolio.assert_called_once()
        new_window.assert_called_once_with(menu.root, menu.backend, menu.main_window)

    def test_exit_destroys_root(self):
        menu = DropdownMenu.__new__(DropdownMenu)
        menu.root = Mock()

        menu._exit_command()

        menu.root.destroy.assert_called_once_with()
