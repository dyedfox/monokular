from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
    """Shows a zoomable preview of a single PDF page."""

    def __init__(self, renderer: PdfRenderer, page_index: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Page {page_index + 1} Preview")
        self.resize(960, 720)

        self._renderer = renderer
        self._page_index = page_index
        self._zoom_idx = ZOOM_LEVELS.index(1.0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Zoom toolbar
        tb = QHBoxLayout()
        tb.setContentsMargins(6, 4, 6, 4)

        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setFixedWidth(32)
        self._zoom_out_btn.clicked.connect(self._zoom_out)

        self._zoom_label = QLabel()
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setFixedWidth(60)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedWidth(32)
        self._zoom_in_btn.clicked.connect(self._zoom_in)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._zoom_reset)

        tb.addWidget(self._zoom_out_btn)
        tb.addWidget(self._zoom_label)
        tb.addWidget(self._zoom_in_btn)
        tb.addWidget(reset_btn)
        tb.addStretch()

        layout.addLayout(tb)

        # Scroll area with image
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._scroll)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setWidget(self._image_label)

        self._render()

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

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
