"""Loading Qt translation catalogues at startup."""

import os
import sys

from PyQt6.QtCore import QLocale, QTranslator

#: Languages Monokular ships, matching Dyedfox Radio's set.
LANGUAGES = [
    "bg", "ca", "cs", "da", "de", "el", "es", "et", "fi", "fr", "hr", "hu",
    "it", "lt", "lv", "nb", "nl", "pl", "pt", "ro", "sk", "sl", "sr", "sv", "uk",
]

CATALOGUE_PREFIX = "monokular_"


def translations_dir() -> str:
    """Locate the catalogue folder in a PyInstaller bundle, a checkout, or an install."""
    candidates = []
    # Only inside a PyInstaller bundle; otherwise _MEIPASS is absent and
    # joining "" would yield a relative path resolved against the cwd.
    bundle = getattr(sys, "_MEIPASS", "")
    if bundle:
        candidates.append(os.path.join(bundle, "translations"))
    candidates.append(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations")
    )
    candidates.append("/usr/lib/monokular/translations")
    for path in candidates:
        if os.path.isdir(path):
            return path
    return ""


def install_translator(app, locale_name: str | None = None) -> str | None:
    """Install the catalogue for a locale. Returns the language used, or None.

    QTranslator.load() narrows on its own, so "uk_UA" finds monokular_uk.qm.
    """
    if locale_name is None:
        locale_name = QLocale.system().name()

    directory = translations_dir()
    if not directory:
        return None

    translator = QTranslator(app)
    if not translator.load(f"{CATALOGUE_PREFIX}{locale_name}", directory):
        return None

    app.installTranslator(translator)
    # Keep a reference; a garbage-collected translator stops translating.
    app._monokular_translator = translator
    return os.path.basename(translator.filePath())[len(CATALOGUE_PREFIX):].removesuffix(".qm")
