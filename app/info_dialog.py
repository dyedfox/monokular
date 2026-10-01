import os

from PyQt6.QtCore import QLocale, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
)

from app.pdf_info import EMPTY, MIXED, SCANNED, TEXT, PdfInfo

# Values wrap within this width; a wide minimum keeps typical ones on one line.
VALUE_MIN_WIDTH = 320
VALUE_MAX_WIDTH = 480


class InfoDialog(QDialog):
    """Read-only facts about the open PDF: file, document, and its metadata."""

    def __init__(self, info: PdfInfo, parent=None):
        super().__init__(parent)
        self._info = info
        self.setWindowTitle(self.tr("Document Info"))

        layout = QVBoxLayout(self)
        self._form = QFormLayout()
        self._form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.addLayout(self._form)

        locale = QLocale()

        self._add_heading(self.tr("File"))
        self._add_row(self.tr("Name:"), info.name)
        # A zero-width space after each slash lets a long path wrap between
        # folders; Copy Path hands out the real one.
        self._add_row(self.tr("Folder:"), _home_relative(info.folder).replace("/", "/\u200b"))
        self._add_row(self.tr("Size:"), locale.formattedDataSize(
            info.file_size, 1, QLocale.DataSizeFormat.DataSizeTraditionalFormat))

        self._add_heading(self.tr("Document"))
        self._add_row(self.tr("Pages:"), locale.toString(info.page_count))
        self._add_row(self.tr("Page size:"), self._page_size_text(locale))
        self._add_row(self.tr("Content:"), self._content_text())
        if info.pdf_version:
            self._add_row(self.tr("PDF version:"), info.pdf_version.removeprefix("PDF").strip())
        if info.encrypted:
            self._add_row(self.tr("Encrypted:"), self.tr("Yes"))

        labels = {
            "title": self.tr("Title:"),
            "author": self.tr("Author:"),
            "subject": self.tr("Subject:"),
            "keywords": self.tr("Keywords:"),
            "creator": self.tr("Creator:"),
            "producer": self.tr("Producer:"),
        }
        dates = [(self.tr("Created:"), info.created), (self.tr("Modified:"), info.modified)]
        if info.metadata or any(when for _, when in dates):
            self._add_heading(self.tr("Metadata"))
            for key in ("title", "author", "subject", "keywords"):
                if key in info.metadata:
                    self._add_row(labels[key], info.metadata[key])
            for label, when in dates:
                if when is not None:
                    self._add_row(label, locale.toString(when.toLocalTime(), QLocale.FormatType.ShortFormat))
            for key in ("creator", "producer"):
                if key in info.metadata:
                    self._add_row(labels[key], info.metadata[key])

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._open_folder_btn = QPushButton(self.tr("Open Folder"))
        self._open_folder_btn.clicked.connect(self._open_folder)
        buttons.addButton(self._open_folder_btn, QDialogButtonBox.ButtonRole.ActionRole)
        self._copy_path_btn = QPushButton(self.tr("Copy Path"))
        self._copy_path_btn.clicked.connect(self._copy_path)
        buttons.addButton(self._copy_path_btn, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        # Wrapped values need height for the width they end up with; a fixed
        # size constraint makes the dialog fit them instead of clipping.
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def _add_heading(self, text: str):
        label = QLabel(text)
        font = QFont(label.font())
        font.setBold(True)
        label.setFont(font)
        if self._form.rowCount():
            label.setContentsMargins(0, 8, 0, 0)
        self._form.addRow(label)

    def _add_row(self, label: str, value: str):
        field = QLabel(value)
        field.setTextFormat(Qt.TextFormat.PlainText)
        field.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        field.setWordWrap(True)
        field.setMinimumWidth(VALUE_MIN_WIDTH)
        field.setMaximumWidth(VALUE_MAX_WIDTH)
        self._form.addRow(label, field)

    def _page_size_text(self, locale: QLocale) -> str:
        info = self._info
        if info.mixed_sizes:
            return self.tr("Mixed")
        size = self.tr("{0} × {1} mm").format(
            locale.toString(round(info.page_width_mm)), locale.toString(round(info.page_height_mm))
        )
        return f"{info.paper} ({size})" if info.paper else size

    def _content_text(self) -> str:
        return {
            TEXT: self.tr("Text"),
            SCANNED: self.tr("Scanned (images only)"),
            MIXED: self.tr("Text and scanned pages"),
            EMPTY: self.tr("No text or images"),
        }[self._info.content]

    def _open_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self._info.folder))

    def _copy_path(self):
        QGuiApplication.clipboard().setText(self._info.path)


def _home_relative(path: str) -> str:
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path
