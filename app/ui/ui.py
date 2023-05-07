from __future__ import annotations

import tkinter as tk

from ui.main_window.main_window import MainWindowComponents, DropdownMenu

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.backend import BackEnd


class AppWindow:
    def __init__(self, backend: BackEnd):
        self.window = tk.Tk()
        self.window.title("Midas v0.0.1")
        self.main_window = MainWindowComponents(self.window, backend)
        self.dropdown_menu = DropdownMenu(self.window, backend, self.main_window)
    
    def run(self):
        self.window.mainloop()
