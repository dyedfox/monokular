import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow

def _find_icon():
    """Resolve icon path for PyInstaller, system install, or local dev."""
    candidates = [
        os.path.join(getattr(sys, '_MEIPASS', ''), "assets", "icon.svg"),
        os.path.join(os.path.dirname(__file__), "assets", "icon.svg"),
        "/usr/share/icons/hicolor/scalable/apps/monokular.svg",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return ""


ICON_PATH = _find_icon()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Monokular")
    app.setDesktopFileName("monokular")
    app.setWindowIcon(QIcon(ICON_PATH))
    window = MainWindow()
    window.show()

    # Open PDF passed as command-line argument (e.g. "Open With" from file manager)
    args = app.arguments()[1:]
    for arg in args:
        if arg.lower().endswith(".pdf") and os.path.isfile(arg):
            window._load_pdf(arg)
            break

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
