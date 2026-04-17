from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.pdf_renderer import PdfRenderer

THUMB_WIDTH = 180


class ThumbCard(QFrame):
    """A single selectable thumbnail card."""

    def __init__(self, index: int, pixmap, parent=None):
        super().__init__(parent)
        self.index = index
        self.selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Size card to match the pixmap aspect ratio
        card_width = THUMB_WIDTH + 16
        card_height = int(pixmap.height() * (THUMB_WIDTH / pixmap.width())) + 30
        self.setFixedSize(card_width, card_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._image = QLabel()
        self._image.setPixmap(pixmap)
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._image)

        self._label = QLabel(f"Page {index + 1}")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(self._label)

        self._update_style()

    def mousePressEvent(self, event):
        # Ctrl+click → preview, normal click → toggle selection
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            grid = self.parent()
            while grid and not isinstance(grid, ThumbnailGrid):
                grid = grid.parent()
            if grid:
                grid.preview_requested.emit(self.index)
            return

        self.set_selected(not self.selected)
        # Notify parent grid
        grid = self.parent()
        while grid and not isinstance(grid, ThumbnailGrid):
            grid = grid.parent()
        if grid:
            grid.selection_changed.emit()

    def set_selected(self, selected: bool):
        self.selected = selected
        self._update_style()

    def _update_style(self):
        if self.selected:
            self.setStyleSheet(
                "ThumbCard { border: 3px solid #2979ff; border-radius: 6px; background: #e3f2fd; }"
            )
        else:
            self.setStyleSheet(
                "ThumbCard { border: 1px solid #ccc; border-radius: 6px; background: white; }"
            )


class ThumbnailGrid(QScrollArea):
    """Scrollable grid of selectable page thumbnails."""

    COLUMNS = 4
    selection_changed = pyqtSignal()
    preview_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(10)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        self._cards: list[ThumbCard] = []

    def load(self, renderer: PdfRenderer):
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        for i in range(renderer.page_count):
            pixmap = renderer.render_page(i, THUMB_WIDTH)
            card = ThumbCard(i, pixmap)
            row, col = divmod(i, self.COLUMNS)
            self._grid.addWidget(card, row, col)
            self._cards.append(card)

    def selected_indices(self) -> list[int]:
        return [c.index for c in self._cards if c.selected]

    def select_all(self):
        for card in self._cards:
            card.set_selected(True)
        self.selection_changed.emit()

    def deselect_all(self):
        for card in self._cards:
            card.set_selected(False)
        self.selection_changed.emit()
