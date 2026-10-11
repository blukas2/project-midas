from unittest.mock import Mock

from ui.ui import AppWindow


class TestAppWindow:
    def test_initializes_main_window_and_runs_event_loop(self, monkeypatch):
        root = Mock()
        monkeypatch.setattr("ui.ui.tk.Tk", lambda: root)
        monkeypatch.setattr("ui.ui.MainWindowComponents", lambda window, backend: "main")
        monkeypatch.setattr("ui.ui.DropdownMenu", lambda window, backend, main: "menu")
        backend = object()

        application = AppWindow(backend)
        application.run()

        assert application.main_window == "main"
        assert application.dropdown_menu == "menu"
        root.mainloop.assert_called_once_with()


class TestApplicationEntrypoint:
    def test_main_initializes_logging_backend_and_gui(self, monkeypatch):
        import importlib.util
        from pathlib import Path

        source = Path(__file__).resolve().parents[2] / "app" / "app.py"
        spec = importlib.util.spec_from_file_location("midas_app_entrypoint", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app_instance = Mock()
        monkeypatch.setattr(module, "setup_logging", Mock())
        monkeypatch.setattr(module, "BackEnd", Mock(return_value="backend"))
        monkeypatch.setattr(module, "AppWindow", Mock(return_value=app_instance))

        module.main()

        module.setup_logging.assert_called_once_with()
        module.BackEnd.assert_called_once_with()
        module.AppWindow.assert_called_once_with("backend")
        app_instance.run.assert_called_once_with()
