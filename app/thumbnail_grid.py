from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.pdf_renderer import PdfRenderer

DEFAULT_THUMB_WIDTH = 180
MIN_COLUMNS = 4
SPACING = 10
CARD_PADDING = 16


class ThumbCard(QFrame):
    """A single selectable thumbnail card."""

    def __init__(self, index: int, pixmap: QPixmap, thumb_width: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        card_width = thumb_width + CARD_PADDING
        card_height = int(pixmap.height() * (thumb_width / pixmap.width())) + 30
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
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            grid = self.parent()
            while grid and not isinstance(grid, ThumbnailGrid):
                grid = grid.parent()
            if grid:
                grid.preview_requested.emit(self.index)
            return

        self.set_selected(not self.selected)
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
    """Scrollable grid of selectable page thumbnails. Adjusts columns to window width."""

    selection_changed = pyqtSignal()
    preview_requested = pyqtSignal(int)

    THUMB_SIZES = [100, 140, 180, 240, 320]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(SPACING)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        self._cards: list[ThumbCard] = []
        self._renderer: PdfRenderer | None = None
        self._thumb_width = DEFAULT_THUMB_WIDTH
        self._selected_set: set[int] = set()

    @property
    def thumb_width(self) -> int:
        return self._thumb_width

    @thumb_width.setter
    def thumb_width(self, value: int):
        if value != self._thumb_width:
            self._thumb_width = value
            if self._renderer:
                self._rebuild()

    def load(self, renderer: PdfRenderer):
        self._renderer = renderer
        self._selected_set.clear()
        self._rebuild()

    def _rebuild(self):
        """Re-render all cards at the current thumb width and re-lay them out."""
        old_selected = self._selected_set.copy()

        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        cols = self._calc_columns()

        for i in range(self._renderer.page_count):
            pixmap = self._renderer.render_page(i, self._thumb_width)
            card = ThumbCard(i, pixmap, self._thumb_width)
            if i in old_selected:
                card.set_selected(True)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col)
            self._cards.append(card)

        self._selected_set = old_selected

    def _calc_columns(self) -> int:
        available = self.viewport().width() - SPACING
        card_w = self._thumb_width + CARD_PADDING + SPACING
        cols = max(MIN_COLUMNS, available // card_w) if card_w > 0 else MIN_COLUMNS
        return cols

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._cards and self._renderer:
            new_cols = self._calc_columns()
            # Only re-layout if column count changed
            current_cols = 1
            if len(self._cards) > 1:
                pos0 = self._grid.indexOf(self._cards[0])
                pos1 = self._grid.indexOf(self._cards[1])
                if pos0 >= 0 and pos1 >= 0:
                    r0, c0, _, _ = self._grid.getItemPosition(pos0)
                    r1, c1, _, _ = self._grid.getItemPosition(pos1)
                    if r0 == r1:
                        current_cols = c1 - c0 + 1 if c1 > c0 else MIN_COLUMNS
            if new_cols != current_cols:
                self._relayout(new_cols)

    def _relayout(self, cols: int):
        """Move existing cards into new grid positions without re-rendering."""
        for card in self._cards:
            self._grid.removeWidget(card)
        for i, card in enumerate(self._cards):
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col)

    def selected_indices(self) -> list[int]:
        self._selected_set = {c.index for c in self._cards if c.selected}
        return sorted(self._selected_set)

    def select_all(self):
        for card in self._cards:
            card.set_selected(True)
        self._selected_set = {c.index for c in self._cards}
        self.selection_changed.emit()

    def deselect_all(self):
        for card in self._cards:
            card.set_selected(False)
        self._selected_set.clear()
        self.selection_changed.emit()
