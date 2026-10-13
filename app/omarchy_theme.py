import os
import tomllib
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QFileSystemWatcher, QObject, QTimer, QTranslator, pyqtSignal, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QProxyStyle, QStyle

_STATE_DIR = Path.home() / ".local" / "state" / "omarchy" / "current"
_COLORS_FILE = _STATE_DIR / "theme" / "colors.toml"

_DEFAULTS = {
    "background": "#2c2525",
    "foreground": "#e6d9db",
    "dark_background": "#211b1b",
    "darker_background": "#181414",
    "lighter_background": "#3d2f2a",
    "muted": "#72696a",
    "light_foreground": "#c3b7b8",
    "accent": "#f38d70",
}

_RELOAD_DEBOUNCE_MS = 400


def is_omarchy() -> bool:
    return bool(os.environ.get("OMARCHY_PATH"))


def prefer_portal_dialogs() -> None:
    """Route file dialogs through the desktop portal on Omarchy.

    Omarchy exports QT_QPA_PLATFORMTHEME=gtk3, under which Qt draws GTK's own
    file dialog in-process and never asks the portal, so the user's chosen
    file picker (set in xdg-desktop-portal's FileChooser preference) is
    ignored. The portal theme opens that picker instead. On Omarchy the
    palette comes from apply() below, not from the GTK theme, so nothing else
    is lost. Must run before the QApplication is created; a theme the user
    set explicitly is left alone.
    """
    if is_omarchy() and os.environ.get("QT_QPA_PLATFORMTHEME", "gtk3") == "gtk3":
        os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"


def _load_colors() -> dict | None:
    try:
        with open(_COLORS_FILE, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _contrast_text(color: QColor) -> QColor:
    """Black or white, whichever reads better on top of `color`."""
    luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
    return QColor("black") if luminance > 0.5 else QColor("white")


def _build_palette(colors: dict) -> QPalette:
    def c(key: str) -> QColor:
        return QColor(colors.get(key, _DEFAULTS.get(key)))

    background = c("background")
    foreground = c("foreground")
    base = c("dark_background")
    alt_base = c("lighter_background")
    tooltip_base = c("darker_background")
    muted = c("muted")
    light_foreground = c("light_foreground")
    accent = c("accent")
    highlighted_text = _contrast_text(accent)

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, background)
    pal.setColor(QPalette.ColorRole.Button, background)
    pal.setColor(QPalette.ColorRole.WindowText, foreground)
    pal.setColor(QPalette.ColorRole.Text, foreground)
    pal.setColor(QPalette.ColorRole.ButtonText, foreground)
    pal.setColor(QPalette.ColorRole.Base, base)
    pal.setColor(QPalette.ColorRole.AlternateBase, alt_base)
    pal.setColor(QPalette.ColorRole.ToolTipBase, tooltip_base)
    pal.setColor(QPalette.ColorRole.ToolTipText, foreground)
    # `muted` reads fine as a subtle border/divider tone, but as text it's
    # often near-invisible against `background` in stock themes (well under
    # WCAG's 4.5:1 minimum), so placeholder/secondary text uses the lighter
    # tone instead.
    pal.setColor(QPalette.ColorRole.PlaceholderText, light_foreground)
    pal.setColor(QPalette.ColorRole.Mid, muted)
    pal.setColor(QPalette.ColorRole.Highlight, accent)
    pal.setColor(QPalette.ColorRole.HighlightedText, highlighted_text)
    pal.setColor(QPalette.ColorRole.Link, accent)

    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        pal.setColor(QPalette.ColorGroup.Disabled, role, muted)

    return pal


class OmarchyThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._watcher = QFileSystemWatcher([str(_STATE_DIR)])
        self._watcher.directoryChanged.connect(self._on_changed)
        self._reload_timer = QTimer()
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self._reload)
        self._reload()

    def _on_changed(self, _path: str):
        self._reload_timer.start(_RELOAD_DEBOUNCE_MS)
        # The watch can be dropped by some filesystems/tools when the watched
        # directory's contents are replaced; re-arm defensively.
        if str(_STATE_DIR) not in self._watcher.directories():
            self._watcher.addPath(str(_STATE_DIR))

    def _reload(self):
        colors = _load_colors()
        if colors is None:
            return
        self._app.setPalette(_build_palette(colors))
        self._refresh_stylesheets()
        self.theme_changed.emit()

    def _refresh_stylesheets(self):
        # Qt resolves `palette(...)` refs inside a widget's own setStyleSheet()
        # string once and caches the result; QApplication.setPalette() alone
        # doesn't invalidate that cache. Re-assigning the same string forces
        # Qt to recompute it against the new palette. Widgets painted directly
        # from QPalette (the vast majority) don't need this and already just
        # repaint on their own.
        for widget in self._app.allWidgets():
            sheet = widget.styleSheet()
            if sheet:
                widget.setStyleSheet(sheet)


class _OmarchyStyle(QProxyStyle):
    """Fusion without stock icons on dialog buttons (OK, Cancel, Close...).
    Omarchy's own UI uses plain text buttons; Breeze on KDE keeps its icons."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_DialogButtonBox_ButtonsHaveIcons:
            return 0
        # GTK's order (Cancel before OK), as under the gtk3 platform theme;
        # the portal theme would otherwise switch to Qt's generic layout (see
        # prefer_portal_dialogs).
        if hint == QStyle.StyleHint.SH_DialogButtonLayout:
            return QDialogButtonBox.ButtonLayout.GnomeLayout.value
        return super().styleHint(hint, option, widget, returnData)


_PORTAL = ("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop",
           "org.freedesktop.portal.Settings")
_INTERFACE_NS = "org.gnome.desktop.interface"


def parse_font_name(value: str) -> QFont | None:
    """A GTK font description ("Noto Sans 10") as a QFont, or None.

    Only family and size are taken; style words ("Bold") stay in the family
    name, which fontconfig resolves the same way GTK does.
    """
    family, _, size = value.strip().rpartition(" ")
    try:
        points = float(size)
    except ValueError:
        return None
    if not family or points <= 0:
        return None
    font = QFont(family)
    font.setPointSizeF(points)
    return font


class _DesktopInterface(QObject):
    """Font and icon theme from the desktop's GTK settings, via the portal.

    Under QT_QPA_PLATFORMTHEME=gtk3 Qt took these from GTK; the portal theme
    (see prefer_portal_dialogs) doesn't, and would fall back to Qt's generic
    "Sans Serif 9" and the hicolor icons. Reading the same keys from the
    Settings portal keeps the app looking as before, live changes included
    (`omarchy font set`, theme switches).
    """

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        bus = QDBusConnection.sessionBus()
        portal = QDBusInterface(*_PORTAL, bus)
        for key in ("font-name", "icon-theme"):
            reply = portal.call("ReadOne", _INTERFACE_NS, key)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                self._apply(key, reply.arguments()[0])
        bus.connect(_PORTAL[0], _PORTAL[1], _PORTAL[2], "SettingChanged", self._on_changed)

    @pyqtSlot(QDBusMessage)
    def _on_changed(self, message: QDBusMessage):
        namespace, key, value = (message.arguments() + [None, None, None])[:3]
        if namespace == _INTERFACE_NS:
            self._apply(key, value)

    def _apply(self, key: str, value):
        value = getattr(value, "variant", lambda: value)()  # unwrap a QDBusVariant
        if not isinstance(value, str) or not value:
            return
        if key == "font-name":
            font = parse_font_name(value)
            if font is not None:
                self._app.setFont(font)
        elif key == "icon-theme":
            QIcon.setThemeName(value)


class _ButtonLabels(QTranslator):
    """OK and Cancel labelled from Monokular's own catalogues.

    Under the gtk3 platform theme GTK supplied these, translated and with
    mnemonics ("_Cancel"). The portal theme falls back to Qt's qtbase
    catalogue, which ships only some of Monokular's languages and has no
    mnemonics. Qt asks for them as ("QPlatformTheme", "OK"), so answering
    that request covers dialog button boxes and message boxes alike.
    """

    def translate(self, context, source, disambiguation=None, n=-1):
        if context == "QPlatformTheme":
            if source == "OK":
                return QCoreApplication.translate("StandardButtons", "&OK")
            if source == "Cancel":
                return QCoreApplication.translate("StandardButtons", "&Cancel")
        # None, not "": an empty string would count as a translation and
        # blank out every other text in the app.
        return None


_manager: OmarchyThemeManager | None = None
_desktop: _DesktopInterface | None = None
_button_labels: _ButtonLabels | None = None


def apply(app: QApplication) -> OmarchyThemeManager | None:
    global _manager
    if not is_omarchy():
        return None
    global _desktop, _button_labels
    app.setStyle(_OmarchyStyle("Fusion"))
    if os.environ.get("QT_QPA_PLATFORMTHEME") == "xdgdesktopportal":
        _desktop = _DesktopInterface(app)
        _button_labels = _ButtonLabels(app)
        app.installTranslator(_button_labels)
    _manager = OmarchyThemeManager(app)
    return _manager
