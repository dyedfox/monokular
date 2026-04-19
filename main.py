import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow

ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icon.svg")


def main():
    app = QApplication(sys.argv)
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
