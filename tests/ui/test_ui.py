from unittest.mock import Mock
from types import SimpleNamespace

from ui.ui import AppWindow


class TestAppWindow:
    def test_builds_main_window_on_sta_ui_thread(self, monkeypatch):
        root = Mock()
        monkeypatch.setattr("ui.ui.ctk.CTk", lambda: root)
        monkeypatch.setattr("ui.ui.configure_theme", Mock())
        monkeypatch.setattr("ui.ui.configure_native_widget_theme", Mock())
        monkeypatch.setattr("ui.ui.MainWindowComponents", lambda window, backend: "main")
        monkeypatch.setattr("ui.ui.DropdownMenu", lambda window, backend, main: "menu")
        monkeypatch.setattr(AppWindow, "_initialize_sta", Mock())
        monkeypatch.setattr(AppWindow, "_validate_runtime", Mock())
        monkeypatch.setattr("ui.ui.ctypes.windll.ole32.CoUninitialize", Mock())
        backend = object()

        application = AppWindow(backend)
        application.run()

        assert application.backend is backend
        assert application.window is root
        assert application.main_window == "main"
        assert application.dropdown_menu == "menu"
        root.title.assert_called_once_with("Midas v0.0.1")
        root.after.assert_called_once_with(10, application._pump_webview_messages)
        root.bind.assert_called_once_with(
            "<Destroy>", application._stop_webview_message_pump, add="+"
        )
        root.mainloop.assert_called_once_with()

    def test_stops_message_pump_when_root_is_destroyed(self):
        application = AppWindow(object())
        application.window = Mock()
        application._message_pump_id = "after-id"

        application._stop_webview_message_pump(
            SimpleNamespace(widget=application.window)
        )

        application.window.after_cancel.assert_called_once_with("after-id")
        assert application._message_pump_id is None

    def test_run_reraises_ui_initialization_errors(self, monkeypatch):
        error = RuntimeError("UI startup failed")
        application = AppWindow(object())
        monkeypatch.setattr(AppWindow, "_initialize_sta", Mock())
        monkeypatch.setattr(AppWindow, "_validate_runtime", Mock())
        monkeypatch.setattr("ui.ui.ctypes.windll.ole32.CoUninitialize", Mock())

        def fail_to_run_ui(_application):
            raise error

        monkeypatch.setattr(AppWindow, "_run_ui", fail_to_run_ui)

        try:
            application.run()
        except RuntimeError as raised:
            assert raised is error
        else:
            raise AssertionError("UI startup errors must propagate")


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
