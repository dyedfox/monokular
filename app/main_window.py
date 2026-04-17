from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.export_dialog import ExportDialog
from app.pdf_renderer import PdfRenderer
from app.preview_dialog import PreviewDialog
from app.thumbnail_grid import ThumbnailGrid


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monokular")
        self.setMinimumSize(1000, 700)
        self.setAcceptDrops(True)

        self._renderer: PdfRenderer | None = None

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

        # Central: stack with placeholder and grid
        self._stack = QStackedWidget()

        self._placeholder = QLabel("Open a PDF or drag && drop one here")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("font-size: 18px; color: #888;")

        self._grid = ThumbnailGrid()

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

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._load_pdf(path)

    def _load_pdf(self, path: str):
        if self._renderer:
            self._renderer.close()

        self._renderer = PdfRenderer(path)
        self.setWindowTitle(f"Monokular — {path.split('/')[-1]}")

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
        dialog = ExportDialog(self._renderer, selected, self)
        dialog.exec()

    def _preview_page(self, index: int):
        if self._renderer:
            dialog = PreviewDialog(self._renderer, index, self)
            dialog.exec()
