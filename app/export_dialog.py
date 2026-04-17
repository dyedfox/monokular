import os

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

from app.pdf_renderer import PdfRenderer


class ExportDialog(QDialog):
    def __init__(self, renderer: PdfRenderer, selected: list[int], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Pages")
        self.setMinimumWidth(400)
        self._renderer = renderer
        self._selected = selected

        form = QFormLayout(self)

        # Pages info
        form.addRow("Pages:", QLabel(f"{len(selected)} selected"))

        # Format
        self._format = QComboBox()
        self._format.addItems(["PNG", "JPEG"])
        self._format.setCurrentText("JPEG")
        self._format.currentTextChanged.connect(self._on_format_changed)
        form.addRow("Format:", self._format)

        # Quality (JPEG only)
        self._quality = QSpinBox()
        self._quality.setRange(1, 100)
        self._quality.setValue(92)
        self._quality.setSuffix("%")
        form.addRow("Quality:", self._quality)

        # PPI
        self._ppi = QSpinBox()
        self._ppi.setRange(72, 1200)
        self._ppi.setValue(300)
        self._ppi.setSuffix(" PPI")
        form.addRow("Resolution:", self._ppi)

        # Output directory
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setText(os.path.dirname(renderer.path))
        self._dir_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        dir_row.addWidget(self._dir_edit)
        dir_row.addWidget(browse_btn)
        form.addRow("Output:", dir_row)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_format_changed(self, fmt: str):
        self._quality.setEnabled(fmt == "JPEG")

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self._dir_edit.setText(d)

    def _export(self):
        out_dir = self._dir_edit.text()
        if not out_dir:
            QMessageBox.warning(self, "Export", "Please select an output folder.")
            return

        fmt = self._format.currentText().lower()
        ext = "png" if fmt == "png" else "jpg"
        quality = -1 if fmt == "png" else self._quality.value()
        ppi = self._ppi.value()

        base = os.path.splitext(os.path.basename(self._renderer.path))[0]

        for idx in self._selected:
            img = self._renderer.render_page_at_ppi(idx, ppi)
            filename = f"{base}_page{idx + 1}.{ext}"
            filepath = os.path.join(out_dir, filename)
            img.save(filepath, fmt.upper(), quality)

        QMessageBox.information(
            self, "Export", f"Exported {len(self._selected)} page(s) to:\n{out_dir}"
        )
        self.accept()
