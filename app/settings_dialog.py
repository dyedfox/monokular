from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from app.export import available_formats, find_format, page_filename, pdf_filename
from app.settings import DEFAULTS, Settings

#: Stored values for export/output_mode, in the order they are offered.
OUTPUT_MODE_KEYS = ["same_as_pdf", "last_used", "fixed"]


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Settings"))
        self.setMinimumWidth(450)
        self._settings = settings

        form = QFormLayout(self)

        # --- Export defaults ---
        self._format = QComboBox()
        self._format.addItems([f.label for f in available_formats()])
        saved = settings.get("export/format")
        if self._format.findText(saved) >= 0:
            self._format.setCurrentText(saved)
        form.addRow(self.tr("Default format:"), self._format)

        self._quality = QSpinBox()
        self._quality.setRange(1, 100)
        self._quality.setValue(settings.get("export/quality"))
        self._quality.setSuffix("%")
        form.addRow(self.tr("Default quality (JPEG/WEBP):"), self._quality)

        self._ppi = QSpinBox()
        self._ppi.setRange(72, 1200)
        self._ppi.setValue(settings.get("export/ppi"))
        self._ppi.setSuffix(" PPI")
        form.addRow(self.tr("Default resolution:"), self._ppi)

        self._output_mode = QComboBox()
        labels = [
            self.tr("Same folder as the PDF"),
            self.tr("Last used folder"),
            self.tr("Always this folder"),
        ]
        for key, label in zip(OUTPUT_MODE_KEYS, labels):
            self._output_mode.addItem(label, key)
        self._select_output_mode(settings.get("export/output_mode"))
        self._output_mode.currentIndexChanged.connect(self._on_output_mode)
        form.addRow(self.tr("Output folder:"), self._output_mode)

        fixed_row = QHBoxLayout()
        self._fixed_path = QLineEdit()
        self._fixed_path.setText(settings.get("export/fixed_path"))
        self._fixed_path.setPlaceholderText(self.tr("Type or browse for a folder..."))
        self._fixed_browse = QPushButton(self.tr("Browse..."))
        self._fixed_browse.clicked.connect(self._browse_fixed)
        fixed_row.addWidget(self._fixed_path)
        fixed_row.addWidget(self._fixed_browse)
        form.addRow(self.tr("Fixed path:"), fixed_row)
        self._on_output_mode()

        # --- Naming ---
        self._include_doc_name = QCheckBox(self.tr("Include document name"))
        self._include_doc_name.setChecked(settings.get("naming/include_doc_name"))
        form.addRow(self._include_doc_name)

        self._suffix = QLineEdit()
        self._suffix.setText(settings.get("naming/suffix"))
        self._suffix.setPlaceholderText(self.tr("e.g. page_"))
        form.addRow(self.tr("Page suffix:"), self._suffix)

        self._zero_padding = QSpinBox()
        self._zero_padding.setRange(0, 6)
        self._zero_padding.setValue(settings.get("naming/zero_padding"))
        form.addRow(self.tr("Leading zeros:"), self._zero_padding)

        # Preview
        self._name_preview = QLabel()
        self._name_preview.setStyleSheet("color: #666; font-style: italic;")
        form.addRow(self.tr("Preview:"), self._name_preview)
        self._format.currentTextChanged.connect(lambda: self._update_name_preview())
        self._include_doc_name.toggled.connect(lambda: self._update_name_preview())
        self._suffix.textChanged.connect(lambda: self._update_name_preview())
        self._zero_padding.valueChanged.connect(lambda: self._update_name_preview())
        self._update_name_preview()

        # --- Thumbnails ---
        self._thumb_size = QComboBox()
        for s in [100, 140, 180, 240, 320]:
            self._thumb_size.addItem(f"{s}px", s)
        current = settings.get("thumbnails/default_size")
        idx = self._thumb_size.findData(current)
        if idx >= 0:
            self._thumb_size.setCurrentIndex(idx)
        form.addRow(self.tr("Default thumbnail size:"), self._thumb_size)

        self._min_cols = QSpinBox()
        self._min_cols.setRange(2, 10)
        self._min_cols.setValue(settings.get("thumbnails/min_columns"))
        form.addRow(self.tr("Minimum grid columns:"), self._min_cols)

        # --- General ---
        self._remember_dir = QCheckBox(self.tr("Remember last opened directory"))
        self._remember_dir.setChecked(settings.get("general/remember_last_dir"))
        form.addRow(self._remember_dir)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton(self.tr("Reset to Defaults"))
        reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        form.addRow(btn_layout)

    def _select_output_mode(self, key: str):
        index = self._output_mode.findData(key)
        if index >= 0:
            self._output_mode.setCurrentIndex(index)

    def _on_output_mode(self):
        is_fixed = self._output_mode.currentData() == "fixed"
        self._fixed_path.setEnabled(is_fixed)
        self._fixed_browse.setEnabled(is_fixed)

    def _browse_fixed(self):
        d = QFileDialog.getExistingDirectory(self, self.tr("Select Fixed Output Folder"))
        if d:
            self._fixed_path.setText(d)

    def _reset(self):
        self._format.setCurrentText(DEFAULTS["export/format"])
        self._quality.setValue(DEFAULTS["export/quality"])
        self._ppi.setValue(DEFAULTS["export/ppi"])
        self._select_output_mode(DEFAULTS["export/output_mode"])
        self._fixed_path.setText(DEFAULTS["export/fixed_path"])
        self._include_doc_name.setChecked(DEFAULTS["naming/include_doc_name"])
        self._suffix.setText(DEFAULTS["naming/suffix"])
        self._zero_padding.setValue(DEFAULTS["naming/zero_padding"])
        self._thumb_size.setCurrentIndex(self._thumb_size.findData(DEFAULTS["thumbnails/default_size"]))
        self._min_cols.setValue(DEFAULTS["thumbnails/min_columns"])
        self._remember_dir.setChecked(DEFAULTS["general/remember_last_dir"])

    def _save(self):
        self._settings.set("export/format", self._format.currentText())
        self._settings.set("export/quality", self._quality.value())
        self._settings.set("export/ppi", self._ppi.value())
        self._settings.set("export/output_mode", self._output_mode.currentData())
        self._settings.set("export/fixed_path", self._fixed_path.text())
        self._settings.set("naming/include_doc_name", self._include_doc_name.isChecked())
        self._settings.set("naming/suffix", self._suffix.text())
        self._settings.set("naming/zero_padding", self._zero_padding.value())
        self._settings.set("thumbnails/default_size", self._thumb_size.currentData())
        self._settings.set("thumbnails/min_columns", self._min_cols.value())
        self._settings.set("general/remember_last_dir", self._remember_dir.isChecked())
        self.accept()

    def _update_name_preview(self):
        fmt = find_format(self._format.currentText())
        include_doc_name = self._include_doc_name.isChecked()
        if fmt.is_pdf:
            self._name_preview.setText(pdf_filename("document", include_doc_name))
            return
        self._name_preview.setText(
            page_filename(
                "document",
                1,
                include_doc_name=include_doc_name,
                suffix=self._suffix.text(),
                padding=self._zero_padding.value(),
                extension=fmt.extension,
            )
        )
