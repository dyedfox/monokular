from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from app.pdf_renderer import PdfRenderer

ZOOM_LEVELS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
BASE_WIDTH = 900


class PreviewDialog(QDialog):
    """Shows a zoomable preview of a single PDF page with navigation and selection."""

    selection_toggled = pyqtSignal(int, bool)  # (page_index, selected)

    def __init__(self, renderer: PdfRenderer, page_index: int,
                 selected_indices: set[int] | None = None, parent=None):
        super().__init__(parent)
        self._renderer = renderer
        self._page_index = page_index
        self._page_count = renderer.page_count
        self._zoom_idx = ZOOM_LEVELS.index(1.0)
        self._selected_indices: set[int] = selected_indices.copy() if selected_indices else set()

        self.setWindowTitle(self._make_title())
        self.resize(960, 720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QHBoxLayout()
        tb.setContentsMargins(6, 4, 6, 4)

        # Navigation buttons
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setToolTip("Previous page")
        self._prev_btn.setFixedWidth(32)
        self._prev_btn.clicked.connect(self._go_prev)
        tb.addWidget(self._prev_btn)

        self._page_label = QLabel()
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setFixedWidth(80)
        tb.addWidget(self._page_label)

        self._next_btn = QPushButton("▶")
        self._next_btn.setToolTip("Next page")
        self._next_btn.setFixedWidth(32)
        self._next_btn.clicked.connect(self._go_next)
        tb.addWidget(self._next_btn)

        tb.addSpacing(16)

        # Zoom controls
        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setFixedWidth(32)
        self._zoom_out_btn.clicked.connect(self._zoom_out)
        tb.addWidget(self._zoom_out_btn)

        self._zoom_label = QLabel()
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(60)
        tb.addWidget(self._zoom_label)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedWidth(32)
        self._zoom_in_btn.clicked.connect(self._zoom_in)
        tb.addWidget(self._zoom_in_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._zoom_reset)
        tb.addWidget(reset_btn)

        tb.addStretch()

        # Selection checkbox (top-right)
        self._select_cb = QCheckBox("Select for export")
        self._select_cb.setChecked(self._page_index in self._selected_indices)
        self._select_cb.toggled.connect(self._on_selection_toggled)
        tb.addWidget(self._select_cb)

        layout.addLayout(tb)

        # Scroll area with image
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._scroll)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setWidget(self._image_label)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._go_prev)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._go_next)

        self._render()
        self._update_nav()

    def _make_title(self) -> str:
        return f"Page {self._page_index + 1} / {self._page_count} Preview"

    def _update_nav(self):
        self._prev_btn.setEnabled(self._page_index > 0)
        self._next_btn.setEnabled(self._page_index < self._page_count - 1)
        self._page_label.setText(f"{self._page_index + 1} / {self._page_count}")
        self.setWindowTitle(self._make_title())

        # Update checkbox without triggering signal
        self._select_cb.blockSignals(True)
        self._select_cb.setChecked(self._page_index in self._selected_indices)
        self._select_cb.blockSignals(False)

    def _go_prev(self):
        if self._page_index > 0:
            self._page_index -= 1
            self._render()
            self._update_nav()

    def _go_next(self):
        if self._page_index < self._page_count - 1:
            self._page_index += 1
            self._render()
            self._update_nav()

    def _on_selection_toggled(self, checked: bool):
        if checked:
            self._selected_indices.add(self._page_index)
        else:
            self._selected_indices.discard(self._page_index)
        self.selection_toggled.emit(self._page_index, checked)

    def _render(self):
        zoom = ZOOM_LEVELS[self._zoom_idx]
        width = int(BASE_WIDTH * zoom)
        pixmap = self._renderer.render_page(self._page_index, width)
        self._image_label.setPixmap(pixmap)
        self._zoom_label.setText(f"{int(zoom * 100)}%")
        self._zoom_out_btn.setEnabled(self._zoom_idx > 0)
        self._zoom_in_btn.setEnabled(self._zoom_idx < len(ZOOM_LEVELS) - 1)

    def _zoom_in(self):
        if self._zoom_idx < len(ZOOM_LEVELS) - 1:
            self._zoom_idx += 1
            self._render()

    def _zoom_out(self):
        if self._zoom_idx > 0:
            self._zoom_idx -= 1
            self._render()

    def _zoom_reset(self):
        self._zoom_idx = ZOOM_LEVELS.index(1.0)
        self._render()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.BackButton:
            self._go_prev()
            event.accept()
        elif event.button() == Qt.MouseButton.ForwardButton:
            self._go_next()
            event.accept()
        else:
            super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
