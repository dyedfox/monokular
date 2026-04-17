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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
