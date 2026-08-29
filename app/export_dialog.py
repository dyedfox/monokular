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

from app.export import (
    ExportFormat,
    Naming,
    available_formats,
    export_pages,
    find_format,
    pdf_filename,
    resolve_output_dir,
)
from app.pdf_renderer import PdfRenderer
from app.settings import Settings


class ExportDialog(QDialog):
    def __init__(self, renderer: PdfRenderer, selected: list[int], settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Export Pages"))
        self.setMinimumWidth(460)
        self._renderer = renderer
        self._selected = selected
        self._settings = settings
        self._out_dir = resolve_output_dir(
            settings.get("export/output_mode"),
            fixed_path=settings.get("export/fixed_path"),
            last_used_path=settings.get("export/last_used_path"),
            pdf_path=renderer.path,
        )

        form = QFormLayout(self)

        # Pages info
        form.addRow(
            self.tr("Pages:"), QLabel(self.tr("%n page(s) selected", "", len(selected)))
        )

        # Format — only those the Qt runtime can actually write
        self._format = QComboBox()
        self._format.addItems([f.label for f in available_formats()])
        saved = settings.get("export/format")
        if self._format.findText(saved) >= 0:
            self._format.setCurrentText(saved)
        self._format.currentTextChanged.connect(self._on_format_changed)
        form.addRow(self.tr("Format:"), self._format)

        # Quality (lossy formats only)
        self._quality = QSpinBox()
        self._quality.setRange(1, 100)
        self._quality.setValue(settings.get("export/quality"))
        self._quality.setSuffix("%")
        form.addRow(self.tr("Quality:"), self._quality)

        # PPI (raster formats only)
        self._ppi = QSpinBox()
        self._ppi.setRange(72, 1200)
        self._ppi.setValue(settings.get("export/ppi"))
        self._ppi.setSuffix(" PPI")
        form.addRow(self.tr("Resolution:"), self._ppi)

        # Output target — a folder for images, a single file for PDF
        out_row = QHBoxLayout()
        self._out_edit = QLineEdit()
        self._out_edit.setReadOnly(True)
        self._browse_btn = QPushButton(self.tr("Browse..."))
        self._browse_btn.clicked.connect(self._browse)
        out_row.addWidget(self._out_edit)
        out_row.addWidget(self._browse_btn)
        self._out_label = QLabel(self.tr("Output:"))
        form.addRow(self._out_label, out_row)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self._on_format_changed(self._format.currentText())

    def _current_format(self) -> ExportFormat:
        return find_format(self._format.currentText())

    def _on_format_changed(self, _label: str):
        fmt = self._current_format()
        self._quality.setEnabled(fmt.supports_quality)
        self._ppi.setEnabled(not fmt.is_pdf)
        self._out_label.setText(self.tr("Save as:") if fmt.is_pdf else self.tr("Output:"))
        self._out_edit.setText(self._default_target(fmt))

    def _default_target(self, fmt: ExportFormat) -> str:
        if not fmt.is_pdf:
            return self._out_dir
        base = os.path.splitext(os.path.basename(self._renderer.path))[0]
        name = pdf_filename(base, self._settings.get("naming/include_doc_name"))
        return os.path.join(self._out_dir, name)

    def _browse(self):
        if self._current_format().is_pdf:
            path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Save PDF As"),
                self._out_edit.text(),
                self.tr("PDF Files (*.pdf)"),
            )
            if path:
                self._out_dir = os.path.dirname(path)
                self._out_edit.setText(path)
            return

        d = QFileDialog.getExistingDirectory(self, self.tr("Select Output Folder"), self._out_dir)
        if d:
            self._out_dir = d
            self._out_edit.setText(d)

    def _export(self):
        target = self._out_edit.text()
        if not target:
            QMessageBox.warning(self, self.tr("Export"), self.tr("Please choose where to save."))
            return

        fmt = self._current_format()
        if fmt.is_pdf:
            self._renderer.write_pdf(self._selected, target)
            out_dir = os.path.dirname(target)
            summary = self.tr(
                "Exported %n page(s) to:", "", len(self._selected)
            ) + f"\n{target}"
        else:
            export_pages(
                self._renderer,
                self._selected,
                target,
                fmt,
                ppi=self._ppi.value(),
                quality=self._quality.value() if fmt.supports_quality else -1,
                naming=Naming(
                    include_doc_name=self._settings.get("naming/include_doc_name"),
                    suffix=self._settings.get("naming/suffix"),
                    padding=self._settings.get("naming/zero_padding"),
                ),
            )
            out_dir = target
            summary = self.tr(
                "Exported %n page(s) to:", "", len(self._selected)
            ) + f"\n{out_dir}"

        QMessageBox.information(self, self.tr("Export"), summary)
        self._settings.set("export/last_used_path", out_dir)
        self.accept()
