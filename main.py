import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import i18n
from app.main_window import MainWindow

def _find_icon():
    """Resolve icon path for PyInstaller, system install, or local dev."""
    candidates = []
    # Only inside a PyInstaller bundle; otherwise _MEIPASS is absent and
    # joining "" would yield a relative path resolved against the cwd.
    bundle = getattr(sys, '_MEIPASS', '')
    if bundle:
        candidates.append(os.path.join(bundle, "assets", "icon.svg"))
    candidates.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.svg")
    )
    candidates.append("/usr/share/icons/hicolor/scalable/apps/monokular.svg")
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
    i18n.install_translator(app)

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
