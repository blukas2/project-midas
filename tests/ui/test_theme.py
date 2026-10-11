from unittest.mock import Mock

from ui import theme


class TestTheme:
    def test_configure_theme_uses_system_appearance_and_blue_palette(self, monkeypatch):
        set_appearance = Mock()
        set_color_theme = Mock()
        monkeypatch.setattr(theme.ctk, "set_appearance_mode", set_appearance)
        monkeypatch.setattr(theme.ctk, "set_default_color_theme", set_color_theme)

        theme.configure_theme()

        set_appearance.assert_called_once_with("system")
        set_color_theme.assert_called_once_with("blue")

    def test_toggle_appearance_changes_dark_to_light(self, monkeypatch):
        set_appearance = Mock()
        configure_native_theme = Mock()
        refresh_charts = Mock()
        monkeypatch.setattr(theme.ctk, "get_appearance_mode", lambda: "Dark")
        monkeypatch.setattr(theme.ctk, "set_appearance_mode", set_appearance)
        monkeypatch.setattr(theme, "configure_native_widget_theme", configure_native_theme)
        monkeypatch.setattr(theme.chart_styler, "refresh", refresh_charts)

        mode = theme.toggle_appearance_mode()

        assert mode == "Light"
        set_appearance.assert_called_once_with("Light")
        configure_native_theme.assert_called_once_with()
        refresh_charts.assert_called_once_with()

    def test_chart_styler_refreshes_registered_dashboards(self, monkeypatch):
        dashboard = Mock()
        monkeypatch.setattr(theme.ctk, "get_appearance_mode", lambda: "Dark")
        styler = theme.ChartStyler()

        styler.register(dashboard)
        styler.refresh()

        dashboard.set_theme.assert_called_once_with("Dark")
