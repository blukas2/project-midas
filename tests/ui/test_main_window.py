from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pandas as pd
from matplotlib.figure import Figure

from ui.main_window.main_window import DropdownMenu, MainWindowComponents


class TestMainWindowComponents:
    def test_button_and_asset_table_setup(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = object()
        button_factory = Mock()
        tree = MagicMock()
        monkeypatch.setattr("ui.main_window.main_window.tk.Button", button_factory)
        monkeypatch.setattr("ui.main_window.main_window.ttk.Treeview", Mock(return_value=tree))

        component._define_buttons()
        component._define_asset_table()

        assert button_factory.call_count == 3
        assert tree.column.call_count == 6
        assert tree.heading.call_count == 6
        assert component.asset_table is tree

    def test_display_portfolio_name(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = object()
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(name="Growth"))
        label = Mock()
        monkeypatch.setattr("ui.main_window.main_window.tk.Label", Mock(return_value=label))

        component.display_portfolio_name()

        label.grid.assert_called_once_with(row=1, column=1, columnspan=2)

    def test_refresh_table_replaces_rows_from_portfolio(self):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.asset_table = Mock()
        component.asset_table.get_children.return_value = []
        asset = SimpleNamespace(
            ticker="ABC",
            quantity=2,
            fast_info={"previousClose": 12.5},
            get_longname=lambda: "Alpha",
        )
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(content={"ABC": asset}))

        component.refresh_table()

        component.asset_table.delete.assert_called_once_with()
        component.asset_table.insert.assert_called_once()
        assert component.asset_table.insert.call_args.kwargs["values"] == ("ABC", "Alpha", 2, 12.5, 25)

    def test_recalculate_refreshes_portfolio_views(self):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.backend = SimpleNamespace(portfolio=SimpleNamespace(calculate=Mock()))
        component.display_portfolio_name = Mock()
        component.refresh_table = Mock()
        for name in (
            "plot_history", "plot_returns", "plot_annualized_returns",
            "plot_volatility", "plot_correlation_matrix",
        ):
            setattr(component, name, Mock())

        component.recalculate_portfolio()

        component.backend.portfolio.calculate.assert_called_once_with()
        component.display_portfolio_name.assert_called_once_with()
        component.refresh_table.assert_called_once_with()
        component.plot_history.assert_called_once_with()

    def test_plot_methods_handle_uncomputed_portfolio_metrics(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = object()
        component.chart_dpi = 80
        component.backend = SimpleNamespace(portfolio=SimpleNamespace())
        figure, axes, canvas = Mock(), Mock(), Mock()
        figure.add_subplot.return_value = axes
        canvas.get_tk_widget.return_value = Mock()
        monkeypatch.setattr("ui.main_window.main_window.Figure", lambda **kwargs: figure)
        monkeypatch.setattr("ui.main_window.main_window.pyplot.Figure", lambda **kwargs: figure)
        monkeypatch.setattr("ui.main_window.main_window.FigureCanvasTkAgg", lambda *args: canvas)
        monkeypatch.setattr("ui.main_window.main_window.tk.Frame", Mock())
        monkeypatch.setattr("ui.main_window.main_window.Table", Mock())
        monkeypatch.setattr("ui.main_window.main_window.config.apply_options", Mock())

        component.plot_history()
        component.plot_returns()
        component.plot_annualized_returns()
        component.plot_volatility()
        component.plot_correlation_matrix()

        assert canvas.get_tk_widget.return_value.grid.call_count == 4

    def test_plot_methods_render_available_portfolio_data(self, monkeypatch):
        component = MainWindowComponents.__new__(MainWindowComponents)
        component.window = object()
        component.chart_dpi = 80
        portfolio = SimpleNamespace(
            history=pd.DataFrame(
                {"Date": pd.to_datetime(["2024-01-01", "2024-01-02"]), "Value": [10, 12]}
            ),
            returns={"1m": 2},
            annualized_returns={"1y": 3},
            volatility={"1y": 5},
            correlation_matrix=pd.DataFrame({"A": [1]}, index=["A"]),
        )
        component.backend = SimpleNamespace(portfolio=portfolio)
        canvas = Mock()
        canvas.get_tk_widget.return_value = Mock()
        monkeypatch.setattr("ui.main_window.main_window.Figure", lambda **kwargs: Figure(**kwargs))
        monkeypatch.setattr(
            "ui.main_window.main_window.pyplot.Figure", lambda **kwargs: Figure(**kwargs)
        )
        monkeypatch.setattr("ui.main_window.main_window.FigureCanvasTkAgg", lambda *args: canvas)
        monkeypatch.setattr("ui.main_window.main_window.tk.Frame", Mock())
        monkeypatch.setattr("ui.main_window.main_window.Table", Mock())
        monkeypatch.setattr("ui.main_window.main_window.config.apply_options", Mock())

        component.plot_history()
        component.plot_returns()
        component.plot_annualized_returns()
        component.plot_volatility()
        component.plot_correlation_matrix()

        assert canvas.get_tk_widget.return_value.grid.call_count == 4

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
        root = Mock()
        menu = Mock()
        monkeypatch.setattr("ui.main_window.main_window.tk.Menu", Mock(return_value=menu))
        backend, main_window = object(), object()

        dropdown = DropdownMenu(root, backend, main_window)

        assert dropdown.root is root
        assert dropdown.backend is backend
        assert dropdown.main_window is main_window
        assert menu.add_cascade.call_count == 3
        root.config.assert_called_once_with(menu=menu)

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
