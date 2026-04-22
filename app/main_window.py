from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.export_dialog import ExportDialog
from app.pdf_renderer import PdfRenderer
from app.preview_dialog import PreviewDialog
from app.settings import Settings
from app.settings_dialog import SettingsDialog
from app.thumbnail_grid import ThumbnailGrid
from app.version import __version__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monokular")
        self.setMinimumSize(1000, 700)
        self.setAcceptDrops(True)

        self._renderer: PdfRenderer | None = None
        self._settings = Settings()

        # Toolbar
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = toolbar.addAction("Open PDF")
        open_action.triggered.connect(self._open_file)

        toolbar.addSeparator()

        self._select_all_action = toolbar.addAction("Select All")
        self._select_all_action.triggered.connect(self._select_all)
        self._select_all_action.setEnabled(False)

        self._deselect_action = toolbar.addAction("Deselect All")
        self._deselect_action.triggered.connect(self._deselect_all)
        self._deselect_action.setEnabled(False)

        toolbar.addSeparator()

        self._export_action = toolbar.addAction("Export Selected")
        self._export_action.triggered.connect(self._export)
        self._export_action.setEnabled(False)

        toolbar.addSeparator()

        self._zoom_out_action = toolbar.addAction("🔍−")
        self._zoom_out_action.setToolTip("Smaller thumbnails")
        self._zoom_out_action.triggered.connect(self._thumb_zoom_out)

        self._zoom_label = QLabel(f" {ThumbnailGrid.THUMB_SIZES.index(180) + 1}/{len(ThumbnailGrid.THUMB_SIZES)} ")
        toolbar.addWidget(self._zoom_label)

        self._zoom_in_action = toolbar.addAction("🔍+")
        self._zoom_in_action.setToolTip("Larger thumbnails")
        self._zoom_in_action.triggered.connect(self._thumb_zoom_in)

        # Apply saved thumbnail size
        saved_size = self._settings.get("thumbnails/default_size")
        if saved_size in ThumbnailGrid.THUMB_SIZES:
            self._thumb_size_idx = ThumbnailGrid.THUMB_SIZES.index(saved_size)
        else:
            self._thumb_size_idx = ThumbnailGrid.THUMB_SIZES.index(180)
        self._grid = ThumbnailGrid()
        self._grid.thumb_width = ThumbnailGrid.THUMB_SIZES[self._thumb_size_idx]
        self._grid.min_columns = self._settings.get("thumbnails/min_columns")
        self._update_zoom_label()

        toolbar.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        settings_action = toolbar.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)

        about_action = toolbar.addAction("About")
        about_action.triggered.connect(self._show_about)

        # Central: stack with placeholder and grid
        self._stack = QStackedWidget()

        self._placeholder = QLabel("Open a PDF or drag & drop one here")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("font-size: 18px; color: #888;")

        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._grid)
        self._stack.setCurrentWidget(self._placeholder)

        self.setCentralWidget(self._stack)

        # Status bar for selection info
        self._status_label = QLabel("No pages selected")
        self.statusBar().addWidget(self._status_label)
        self.statusBar().addPermanentWidget(QLabel("Ctrl+Click to preview"))
        self._grid.selection_changed.connect(self._update_selection_status)
        self._grid.preview_requested.connect(self._preview_page)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

        # Restore saved geometry
        settings = QSettings("Monokular", "Monokular")
        geometry = settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        settings = QSettings("Monokular", "Monokular")
        settings.setValue("window/geometry", self.saveGeometry())
        super().closeEvent(event)

    def _open_file(self):
        start_dir = ""
        if self._settings.get("general/remember_last_dir"):
            start_dir = self._settings.get("general/last_open_dir")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", start_dir, "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._load_pdf(path)

    def _load_pdf(self, path: str):
        import os
        if self._renderer:
            self._renderer.close()

        self._renderer = PdfRenderer(path)
        self.setWindowTitle(f"Monokular — {path.split('/')[-1]}")

        if self._settings.get("general/remember_last_dir"):
            self._settings.set("general/last_open_dir", os.path.dirname(path))

        self._grid.load(self._renderer)
        self._stack.setCurrentWidget(self._grid)

        self._select_all_action.setEnabled(True)
        self._deselect_action.setEnabled(True)
        self._export_action.setEnabled(True)
        self._update_selection_status()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._load_pdf(path)
                return

    def _select_all(self):
        self._grid.select_all()

    def _deselect_all(self):
        self._grid.deselect_all()

    def _update_selection_status(self):
        selected = self._grid.selected_indices()
        if not selected:
            self._status_label.setText("No pages selected")
        else:
            pages = ", ".join(str(i + 1) for i in selected)
            self._status_label.setText(f"Selected ({len(selected)}): pages {pages}")

    def _export(self):
        selected = self._grid.selected_indices()
        if not selected:
            QMessageBox.information(self, "Export", "No pages selected.")
            return
        dialog = ExportDialog(self._renderer, selected, self._settings, self)
        dialog.exec()

    def _preview_page(self, index: int):
        if self._renderer:
            dialog = PreviewDialog(self._renderer, index, self)
            dialog.exec()

    def _thumb_zoom_in(self):
        sizes = ThumbnailGrid.THUMB_SIZES
        if self._thumb_size_idx < len(sizes) - 1:
            self._thumb_size_idx += 1
            self._grid.thumb_width = sizes[self._thumb_size_idx]
            self._update_zoom_label()

    def _thumb_zoom_out(self):
        sizes = ThumbnailGrid.THUMB_SIZES
        if self._thumb_size_idx > 0:
            self._thumb_size_idx -= 1
            self._grid.thumb_width = sizes[self._thumb_size_idx]
            self._update_zoom_label()

    def _update_zoom_label(self):
        sizes = ThumbnailGrid.THUMB_SIZES
        self._zoom_label.setText(f" {self._thumb_size_idx + 1}/{len(sizes)} ")

    def _open_settings(self):
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec():
            # Apply changed settings
            new_size = self._settings.get("thumbnails/default_size")
            if new_size in ThumbnailGrid.THUMB_SIZES:
                self._thumb_size_idx = ThumbnailGrid.THUMB_SIZES.index(new_size)
                self._grid.thumb_width = new_size
                self._update_zoom_label()
            self._grid.min_columns = self._settings.get("thumbnails/min_columns")

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Monokular",
            f"<h3>Monokular v{__version__}</h3>"
            "<p>Export PDF pages as images — one thing, done well.</p>"
            "<p>License: GPL-3.0-or-later</p>",
        )
