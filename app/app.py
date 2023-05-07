from ui.ui import AppWindow
from backend.backend import BackEnd

def main():
    backend = BackEnd()
    app = AppWindow(backend)
    app.run()


if __name__ == "__main__":
    main()