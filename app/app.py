import tkinter as tk

from ui.ui import AppWindow
from components.components import BackEnd

def main():
    backend = BackEnd()
    app = AppWindow(backend)
    app.run()


if __name__ == "__main__":
    main()