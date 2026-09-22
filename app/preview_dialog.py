from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from app.pdf_renderer import PdfRenderer
from app.settings import restore_geometry, save_geometry

ZOOM_LEVELS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
BASE_WIDTH = 900

# A touchpad pinch reports many small fractional deltas over the course of
# one gesture; stepping ZOOM_LEVELS on every event would be too twitchy, so
# deltas accumulate until they cross this fraction.
PINCH_STEP_THRESHOLD = 0.08


class PreviewDialog(QDialog):
    """Shows a zoomable preview of a single PDF page with navigation and selection."""

    selection_toggled = pyqtSignal(int, bool)  # (page_index, selected)
    rotation_changed = pyqtSignal(int)  # page_index

    def __init__(self, renderer: PdfRenderer, page_index: int,
                 selected_indices: set[int] | None = None, parent=None):
        super().__init__(parent)
        self._renderer = renderer
        self._page_index = page_index
        self._page_count = renderer.page_count
        self._zoom_idx = ZOOM_LEVELS.index(1.0)
        self._pinch_accum = 0.0
        self._selected_indices: set[int] = selected_indices.copy() if selected_indices else set()

        self.setWindowTitle(self._make_title())
        self.resize(960, 720)
        restore_geometry("preview_geometry", self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QHBoxLayout()
        tb.setContentsMargins(6, 4, 6, 4)

        # Navigation buttons
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setToolTip(self.tr("Previous page"))
        self._prev_btn.setFixedWidth(32)
        self._prev_btn.clicked.connect(self._go_prev)
        tb.addWidget(self._prev_btn)

        self._page_input = QLineEdit()
        self._page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_input.setFixedWidth(40)
        self._page_input.setToolTip(self.tr("Go to page"))
        self._page_input.setValidator(QIntValidator(1, self._page_count, self))
        self._page_input.returnPressed.connect(self._jump_to_page_input)
        tb.addWidget(self._page_input)

        self._page_total_label = QLabel()
        tb.addWidget(self._page_total_label)

        self._next_btn = QPushButton("▶")
        self._next_btn.setToolTip(self.tr("Next page"))
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

        reset_btn = QPushButton(self.tr("Reset"))
        reset_btn.clicked.connect(self._zoom_reset)
        tb.addWidget(reset_btn)

        tb.addSpacing(16)

        # Rotation controls
        rotate_left_btn = QPushButton("\u21ba")
        rotate_left_btn.setToolTip(self.tr("Rotate left  ([)"))
        rotate_left_btn.setFixedWidth(32)
        rotate_left_btn.clicked.connect(self._rotate_left)
        tb.addWidget(rotate_left_btn)

        rotate_right_btn = QPushButton("\u21bb")
        rotate_right_btn.setToolTip(self.tr("Rotate right  (])"))
        rotate_right_btn.setFixedWidth(32)
        rotate_right_btn.clicked.connect(self._rotate_right)
        tb.addWidget(rotate_right_btn)

        tb.addStretch()

        # Selection checkbox (top-right)
        self._select_cb = QCheckBox(self.tr("Select for export"))
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

        # Two-finger pinch on a touchpad arrives as a native gesture targeted
        # at the viewport under the cursor, not at this dialog, so it's
        # caught with an event filter rather than an event()/wheelEvent()
        # override here.
        self._scroll.viewport().installEventFilter(self)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._go_prev)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._go_next)
        QShortcut(QKeySequence(Qt.Key.Key_Home), self, self._go_first)
        QShortcut(QKeySequence(Qt.Key.Key_End), self, self._go_last)
        QShortcut(QKeySequence("["), self, self._rotate_left)
        QShortcut(QKeySequence("]"), self, self._rotate_right)

        self._render()
        self._update_nav()

    def _make_title(self) -> str:
        return self.tr("Page {0} / {1} Preview").format(
            self._page_index + 1, self._page_count
        )

    def _update_nav(self):
        self._prev_btn.setEnabled(self._page_index > 0)
        self._next_btn.setEnabled(self._page_index < self._page_count - 1)
        self._page_input.setText(str(self._page_index + 1))
        self._page_total_label.setText(f"/ {self._page_count}")
        self.setWindowTitle(self._make_title())

        # Update checkbox without triggering signal
        self._select_cb.blockSignals(True)
        self._select_cb.setChecked(self._page_index in self._selected_indices)
        self._select_cb.blockSignals(False)

    def _go_to_page(self, target: int):
        target = max(0, min(target, self._page_count - 1))
        if target != self._page_index:
            self._page_index = target
            self._render()
        self._update_nav()

    def _go_prev(self):
        self._go_to_page(self._page_index - 1)

    def _go_next(self):
        self._go_to_page(self._page_index + 1)

    def _go_first(self):
        self._go_to_page(0)

    def _go_last(self):
        self._go_to_page(self._page_count - 1)

    def _jump_to_page_input(self):
        try:
            page_num = int(self._page_input.text())
        except ValueError:
            self._update_nav()  # revert to the current page
            return
        self._go_to_page(page_num - 1)
        self._page_input.clearFocus()

    def _rotate_left(self):
        self._rotate(-90)

    def _rotate_right(self):
        self._rotate(90)

    def _rotate(self, delta: int):
        self._renderer.rotate(self._page_index, delta)
        self._render()
        self.rotation_changed.emit(self._page_index)

    def done(self, result: int):
        save_geometry("preview_geometry", self)
        super().done(result)

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

    def eventFilter(self, obj, event):
        if obj is self._scroll.viewport() and event.type() == QEvent.Type.NativeGesture:
            if event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                self._handle_pinch(event.value())
                return True
        return super().eventFilter(obj, event)

    def _handle_pinch(self, delta: float):
        self._pinch_accum += delta
        while self._pinch_accum >= PINCH_STEP_THRESHOLD:
            self._zoom_in()
            self._pinch_accum -= PINCH_STEP_THRESHOLD
        while self._pinch_accum <= -PINCH_STEP_THRESHOLD:
            self._zoom_out()
            self._pinch_accum += PINCH_STEP_THRESHOLD
