import tkinter as tk

from ui.ui import *
from components.components import BackEnd

def main():
    backend = BackEnd()
    app = AppWindow(backend)
    app.run()


class AppWindow:
    def __init__(self, backend: BackEnd):
        self.window = tk.Tk()
        self.window.title("Midas v0.0.1")
        self.dropdown_menu = DropdownMenu(self.window)
        self.main_window = MainWindowComponents(self.window, backend)
    
    def run(self):
        self.window.mainloop()


main()