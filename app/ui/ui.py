from __future__ import annotations

import ctypes
import sys
from typing import TYPE_CHECKING

import customtkinter as ctk

from ui.main_window.main_window import MainWindowComponents, DropdownMenu
from ui.theme import configure_native_widget_theme, configure_theme

if TYPE_CHECKING:
    from backend.backend import BackEnd


class AppWindow:
    def __init__(self, backend: BackEnd):
        self.backend = backend
        self._closing = False
        self._message_pump_id = None

    def run(self):
        self._initialize_sta()
        try:
            self._validate_runtime()
            self._run_ui()
        finally:
            ctypes.windll.ole32.CoUninitialize()

    def _initialize_sta(self):
        if sys.platform != "win32":
            raise RuntimeError("Interactive charts currently require Windows WebView2.")
        result = ctypes.windll.ole32.CoInitializeEx(None, 0x2)
        if result not in (0, 1):
            raise OSError(result, "Could not initialize the UI thread as a COM STA.")

    def _validate_runtime(self):
        from tkwebview2.tkwebview2 import have_runtime

        if not have_runtime():
            raise RuntimeError("Install the Microsoft Edge WebView2 Runtime before starting Midas.")

    def _run_ui(self):
        configure_theme()
        self.window = ctk.CTk()
        configure_native_widget_theme()
        self.window.title("Midas v0.0.1")
        self.main_window = MainWindowComponents(self.window, self.backend)
        self.dropdown_menu = DropdownMenu(self.window, self.backend, self.main_window)
        self._message_pump_id = self.window.after(10, self._pump_webview_messages)
        self.window.bind("<Destroy>", self._stop_webview_message_pump, add="+")
        self.window.mainloop()

    def _pump_webview_messages(self):
        self._message_pump_id = None
        if self._closing:
            return
        from System.Windows.Forms import Application

        Application.DoEvents()
        if not self._closing:
            self._message_pump_id = self.window.after(10, self._pump_webview_messages)

    def _stop_webview_message_pump(self, event):
        if event.widget is self.window:
            self._closing = True
            if self._message_pump_id is not None:
                self.window.after_cancel(self._message_pump_id)
            self._message_pump_id = None
