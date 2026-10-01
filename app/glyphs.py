"""Omarchy-style icons: Nerd Font glyphs drawn in the palette's text color.

Omarchy's own shell draws its icons as Nerd Font glyphs (Material Design Icons)
rather than icon-theme images. On Omarchy, the icon-only buttons do the same, so
the app matches the shell and follows live theme switches; everywhere else they
keep their Unicode symbols exactly as before.
"""
from functools import lru_cache

from PyQt6.QtCore import QPointF, QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QIcon, QIconEngine, QPainter, QPainterPath, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication

from app.omarchy_theme import is_omarchy

# Code points are the same in every Nerd Font (nf-md-* names in comments).
GLYPHS: dict[str, int] = {
    "rotate-left":  0xF0465,  # rotate_left
    "rotate-right": 0xF0467,  # rotate_right
    "zoom-out":     0xF06EC,  # magnify_minus_outline
    "zoom-in":      0xF06ED,  # magnify_plus_outline
    "go-previous":  0xF0141,  # chevron_left
    "go-next":      0xF0142,  # chevron_right
    "go-top":       0xF005D,  # arrow_up
    "document-properties": 0xF02FD,  # information_outline
}


def _font(pixel_size: int) -> QFont:
    # The fontconfig alias, not a concrete family: `omarchy font set` rewrites
    # it, and the Omarchy shell (Commons/Style.qml) binds to it the same way.
    font = QFont("monospace")
    font.setPixelSize(max(1, pixel_size))
    return font


@lru_cache(maxsize=None)
def _has_glyph(code_point: int) -> bool:
    return QFontMetricsF(_font(16)).inFontUcs4(code_point)


class _GlyphEngine(QIconEngine):
    """Paints the glyph at draw time, so the color tracks the current palette
    (live Omarchy theme switches, disabled state) and it's sharp at any scale."""

    def __init__(self, char: str, color: QColor | None, role: QPalette.ColorRole):
        super().__init__()
        self._char = char
        self._fixed_color = color
        self._role = role

    def _color(self, mode: QIcon.Mode) -> QColor:
        if mode == QIcon.Mode.Disabled:
            return QApplication.palette().color(QPalette.ColorGroup.Disabled, self._role)
        if self._fixed_color is not None:
            return self._fixed_color
        return QApplication.palette().color(QPalette.ColorGroup.Normal, self._role)

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State):
        font = _font(min(rect.width(), rect.height()))
        center = QRectF(rect).center()
        path = QPainterPath()
        path.addText(0, 0, font, self._char)
        bounds = path.boundingRect()
        # Like Omarchy's OpticalGlyph: center the painted bounds horizontally
        # (icon glyphs often sit off-center in their cell) but keep the font's
        # line box vertically, so glyphs don't drift relative to the text
        # baseline. Whole pixels keep edges crisp.
        metrics = QFontMetricsF(font)
        baseline = center.y() + (metrics.ascent() - metrics.descent()) / 2
        origin = QPointF(round(center.x() - bounds.center().x()), round(baseline))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(font)
        painter.setPen(self._color(mode))
        painter.drawText(origin, self._char)
        painter.restore()

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        return self.scaledPixmap(size, mode, state, 1.0)

    def scaledPixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State, scale: float) -> QPixmap:
        pixmap = QPixmap(size * scale)
        pixmap.setDevicePixelRatio(scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.paint(painter, QRect(0, 0, size.width(), size.height()), mode, state)
        painter.end()
        return pixmap

    def clone(self) -> "QIconEngine":
        return _GlyphEngine(self._char, self._fixed_color, self._role)


def glyph_icon(
    name: str,
    color: QColor | None = None,
    role: QPalette.ColorRole = QPalette.ColorRole.ButtonText,
) -> QIcon | None:
    """The glyph for `name` on Omarchy, or None when not on Omarchy, the name
    isn't mapped, or the monospace font lacks Nerd Font glyphs.

    color fixes the color instead of following `role`, for a button whose
    stylesheet sets its own text color."""
    if not is_omarchy():
        return None
    code_point = GLYPHS.get(name)
    if code_point is None or not _has_glyph(code_point):
        return None
    return QIcon(_GlyphEngine(chr(code_point), color, role))


def apply(target, name: str, icon_size: int = 18, color: QColor | None = None) -> bool:
    """Swap a button's or toolbar action's Unicode symbol for the glyph.

    A button loses its text so only the glyph shows; an action keeps it, since
    a toolbar shows icon-only and screen readers still need the name. Returns
    False, leaving the symbol in place, when there's no glyph to use.
    """
    icon = glyph_icon(name, color)
    if icon is None:
        return False
    target.setIcon(icon)
    if hasattr(target, "setIconSize"):
        target.setText("")
        target.setIconSize(QSize(icon_size, icon_size))
    return True
