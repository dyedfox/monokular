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

from app.settings import DEFAULTS, Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self._settings = settings

        form = QFormLayout(self)

        # --- Export defaults ---
        self._format = QComboBox()
        self._format.addItems(["PNG", "JPEG"])
        self._format.setCurrentText(settings.get("export/format"))
        form.addRow("Default format:", self._format)

        self._quality = QSpinBox()
        self._quality.setRange(1, 100)
        self._quality.setValue(settings.get("export/quality"))
        self._quality.setSuffix("%")
        form.addRow("Default JPEG quality:", self._quality)

        self._ppi = QSpinBox()
        self._ppi.setRange(72, 1200)
        self._ppi.setValue(settings.get("export/ppi"))
        self._ppi.setSuffix(" PPI")
        form.addRow("Default resolution:", self._ppi)

        self._output_mode = QComboBox()
        self._output_mode.addItems(["same_as_pdf", "last_used", "fixed"])
        self._output_mode.setCurrentText(settings.get("export/output_mode"))
        self._output_mode.currentTextChanged.connect(self._on_output_mode)
        form.addRow("Output folder:", self._output_mode)

        fixed_row = QHBoxLayout()
        self._fixed_path = QLineEdit()
        self._fixed_path.setText(settings.get("export/fixed_path"))
        self._fixed_path.setReadOnly(True)
        self._fixed_browse = QPushButton("Browse...")
        self._fixed_browse.clicked.connect(self._browse_fixed)
        fixed_row.addWidget(self._fixed_path)
        fixed_row.addWidget(self._fixed_browse)
        form.addRow("Fixed path:", fixed_row)
        self._on_output_mode(self._output_mode.currentText())

        # --- Naming ---
        self._include_doc_name = QCheckBox("Include document name")
        self._include_doc_name.setChecked(settings.get("naming/include_doc_name"))
        form.addRow(self._include_doc_name)

        self._suffix = QLineEdit()
        self._suffix.setText(settings.get("naming/suffix"))
        self._suffix.setPlaceholderText("e.g. page_")
        form.addRow("Page suffix:", self._suffix)

        self._zero_padding = QSpinBox()
        self._zero_padding.setRange(0, 6)
        self._zero_padding.setValue(settings.get("naming/zero_padding"))
        form.addRow("Zero padding:", self._zero_padding)

        # Preview
        self._name_preview = QLabel()
        self._name_preview.setStyleSheet("color: #666; font-style: italic;")
        form.addRow("Preview:", self._name_preview)
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
        form.addRow("Default thumbnail size:", self._thumb_size)

        self._min_cols = QSpinBox()
        self._min_cols.setRange(2, 10)
        self._min_cols.setValue(settings.get("thumbnails/min_columns"))
        form.addRow("Minimum grid columns:", self._min_cols)

        # --- General ---
        self._remember_dir = QCheckBox("Remember last opened directory")
        self._remember_dir.setChecked(settings.get("general/remember_last_dir"))
        form.addRow(self._remember_dir)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset to Defaults")
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

    def _on_output_mode(self, mode: str):
        is_fixed = mode == "fixed"
        self._fixed_path.setEnabled(is_fixed)
        self._fixed_browse.setEnabled(is_fixed)

    def _browse_fixed(self):
        d = QFileDialog.getExistingDirectory(self, "Select Fixed Output Folder")
        if d:
            self._fixed_path.setText(d)

    def _reset(self):
        self._format.setCurrentText(DEFAULTS["export/format"])
        self._quality.setValue(DEFAULTS["export/quality"])
        self._ppi.setValue(DEFAULTS["export/ppi"])
        self._output_mode.setCurrentText(DEFAULTS["export/output_mode"])
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
        self._settings.set("export/output_mode", self._output_mode.currentText())
        self._settings.set("export/fixed_path", self._fixed_path.text())
        self._settings.set("naming/include_doc_name", self._include_doc_name.isChecked())
        self._settings.set("naming/suffix", self._suffix.text())
        self._settings.set("naming/zero_padding", self._zero_padding.value())
        self._settings.set("thumbnails/default_size", self._thumb_size.currentData())
        self._settings.set("thumbnails/min_columns", self._min_cols.value())
        self._settings.set("general/remember_last_dir", self._remember_dir.isChecked())
        self.accept()

    def _update_name_preview(self):
        parts = []
        if self._include_doc_name.isChecked():
            parts.append("document")
            parts.append("_")
        parts.append(self._suffix.text())
        pad = self._zero_padding.value()
        parts.append(str(1).zfill(pad) if pad > 0 else "1")
        self._name_preview.setText("".join(parts) + ".jpg")
