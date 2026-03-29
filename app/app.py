from backend.globals.logging_config import setup_logging
from ui.ui import AppWindow
from backend.backend import BackEnd


def main():
    setup_logging()
    backend = BackEnd()
    app = AppWindow(backend)
    app.run()


if __name__ == "__main__":
    main()