import os
import sys
import tempfile

import fitz
import pytest

# Qt needs a platform plugin even for offscreen pixmap work.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QSettings  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

# Redirect QSettings at import time, before any is constructed, so tests never
# read or write the real ~/.config/Monokular.
_SETTINGS_DIR = tempfile.mkdtemp(prefix="monokular-tests-")
QSettings.setPath(
    QSettings.Format.NativeFormat, QSettings.Scope.UserScope, _SETTINGS_DIR
)


@pytest.fixture
def clean_qsettings():
    """Give a test an empty persistent store."""
    qs = QSettings("Monokular", "Monokular")
    qs.clear()
    qs.sync()
    yield qs
    qs.clear()
    qs.sync()

PAGE_WIDTH = 200
PAGE_HEIGHT = 400
PAGE_COUNT = 3


@pytest.fixture(scope="session")
def qapp():
    """QPixmap requires a running QGuiApplication."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def pdf_path(tmp_path):
    """A 3-page portrait PDF, each page labelled with its number."""
    doc = fitz.open()
    for i in range(PAGE_COUNT):
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        page.insert_text((20, 40), f"Page {i + 1}", fontsize=24)
    path = tmp_path / "sample.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)


class FakeSettings:
    """In-memory stand-in for Settings, so tests never touch the user's QSettings."""

    def __init__(self, **overrides):
        from app.settings import DEFAULTS

        self._values = dict(DEFAULTS)
        self._values.update(overrides)

    def get(self, key):
        return self._values[key]

    def set(self, key, value):
        self._values[key] = value


@pytest.fixture
def settings():
    return FakeSettings()
