import pytest
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusVariant
from PyQt6.QtGui import QIcon

from app import omarchy_theme


@pytest.fixture
def on_omarchy(monkeypatch):
    monkeypatch.setenv("OMARCHY_PATH", "/usr/share/omarchy")


def test_omarchys_gtk3_theme_is_swapped_for_the_portal(on_omarchy, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORMTHEME", "gtk3")
    omarchy_theme.prefer_portal_dialogs()
    assert omarchy_theme.os.environ["QT_QPA_PLATFORMTHEME"] == "xdgdesktopportal"


def test_an_unset_theme_on_omarchy_also_gets_the_portal(on_omarchy, monkeypatch):
    monkeypatch.delenv("QT_QPA_PLATFORMTHEME", raising=False)
    omarchy_theme.prefer_portal_dialogs()
    assert omarchy_theme.os.environ["QT_QPA_PLATFORMTHEME"] == "xdgdesktopportal"


def test_a_theme_the_user_chose_is_left_alone(on_omarchy, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORMTHEME", "qt6ct")
    omarchy_theme.prefer_portal_dialogs()
    assert omarchy_theme.os.environ["QT_QPA_PLATFORMTHEME"] == "qt6ct"


def test_outside_omarchy_the_theme_is_never_touched(monkeypatch):
    monkeypatch.delenv("OMARCHY_PATH", raising=False)
    monkeypatch.setenv("QT_QPA_PLATFORMTHEME", "gtk3")
    omarchy_theme.prefer_portal_dialogs()
    assert omarchy_theme.os.environ["QT_QPA_PLATFORMTHEME"] == "gtk3"


@pytest.mark.parametrize("value, family, size", [
    ("Noto Sans 10", "Noto Sans", 10.0),
    ("Adwaita Sans 11.5", "Adwaita Sans", 11.5),
    ("Liberation Sans Bold 12", "Liberation Sans Bold", 12.0),
])
def test_gtk_font_names_are_read(qapp, value, family, size):
    font = omarchy_theme.parse_font_name(value)
    assert (font.family(), font.pointSizeF()) == (family, size)


@pytest.mark.parametrize("value", ["", "Noto Sans", "10", "Noto Sans 0"])
def test_unreadable_font_names_are_ignored(qapp, value):
    assert omarchy_theme.parse_font_name(value) is None


class _FakeDesktop:
    def __init__(self, app):
        self._app = app

    _apply = omarchy_theme._DesktopInterface._apply


def test_the_desktop_font_becomes_the_app_font(qapp):
    original = qapp.font()
    try:
        _FakeDesktop(qapp)._apply("font-name", QDBusVariant("Noto Sans 13"))
        assert qapp.font().pointSizeF() == 13.0
    finally:
        qapp.setFont(original)


def test_the_desktop_icon_theme_becomes_the_app_icon_theme(qapp):
    original = QIcon.themeName()
    try:
        _FakeDesktop(qapp)._apply("icon-theme", "Yaru-blue")
        assert QIcon.themeName() == "Yaru-blue"
    finally:
        QIcon.setThemeName(original)


@pytest.fixture
def button_labels(qapp):
    labels = omarchy_theme._ButtonLabels(qapp)
    qapp.installTranslator(labels)
    yield
    qapp.removeTranslator(labels)


def test_ok_and_cancel_get_gtk_style_mnemonics(button_labels):
    assert QCoreApplication.translate("QPlatformTheme", "OK") == "&OK"
    assert QCoreApplication.translate("QPlatformTheme", "Cancel") == "&Cancel"


def test_every_other_text_is_left_to_the_normal_catalogues(button_labels):
    # An empty answer here would count as a translation and blank the UI.
    assert QCoreApplication.translate("MainWindow", "Open PDF") == "Open PDF"
    assert QCoreApplication.translate("QPlatformTheme", "Close") == "Close"
