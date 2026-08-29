"""Export formats, output naming, and the routines that write files."""

import os
from dataclasses import dataclass

from PyQt6.QtGui import QImageWriter


@dataclass(frozen=True)
class ExportFormat:
    label: str
    extension: str
    qt_format: str | None  # None for formats Qt does not write
    supports_quality: bool = False
    is_pdf: bool = False


FORMATS: tuple[ExportFormat, ...] = (
    ExportFormat("PNG", "png", "PNG"),
    ExportFormat("JPEG", "jpg", "JPEG", supports_quality=True),
    ExportFormat("WEBP", "webp", "WEBP", supports_quality=True),
    ExportFormat("TIFF", "tif", "TIFF"),
    ExportFormat("PDF", "pdf", None, is_pdf=True),
)


def find_format(label: str) -> ExportFormat:
    for fmt in FORMATS:
        if fmt.label == label:
            return fmt
    raise KeyError(label)


def supported_formats(writable: set[str]) -> tuple[ExportFormat, ...]:
    """Drop image formats the Qt runtime has no writer plugin for.

    WEBP and TIFF come from qt6-imageformats, which may not be installed;
    without this filter saving would fail silently. PDF is written by
    PyMuPDF, so it never depends on Qt.
    """
    return tuple(
        fmt for fmt in FORMATS
        if fmt.is_pdf or (fmt.qt_format or "").lower() in writable
    )


def available_formats() -> tuple[ExportFormat, ...]:
    writable = {bytes(f).decode().lower() for f in QImageWriter.supportedImageFormats()}
    return supported_formats(writable)


def page_filename(
    base: str,
    page_number: int,
    *,
    include_doc_name: bool,
    suffix: str,
    padding: int,
    extension: str,
) -> str:
    number = str(page_number).zfill(padding) if padding > 0 else str(page_number)
    prefix = f"{base}_" if include_doc_name else ""
    return f"{prefix}{suffix}{number}.{extension}"


def pdf_filename(base: str, include_doc_name: bool) -> str:
    return f"{base}_export.pdf" if include_doc_name else "export.pdf"


@dataclass(frozen=True)
class Naming:
    include_doc_name: bool
    suffix: str
    padding: int


def resolve_output_dir(mode: str, *, fixed_path: str, last_used_path: str, pdf_path: str) -> str:
    """Pick the export folder, falling back to the PDF's own folder."""
    if mode == "fixed" and fixed_path and os.path.isdir(fixed_path):
        return fixed_path
    if mode == "last_used" and last_used_path and os.path.isdir(last_used_path):
        return last_used_path
    return os.path.dirname(pdf_path)


def export_pages(
    renderer,
    indices: list[int],
    out_dir: str,
    fmt: ExportFormat,
    *,
    ppi: int,
    quality: int,
    naming: Naming,
) -> list[str]:
    """Render each selected page and write it as an image. Returns the paths written."""
    base = os.path.splitext(os.path.basename(renderer.path))[0]
    written = []
    for idx in indices:
        image = renderer.render_page_at_ppi(idx, ppi)
        filename = page_filename(
            base,
            idx + 1,
            include_doc_name=naming.include_doc_name,
            suffix=naming.suffix,
            padding=naming.padding,
            extension=fmt.extension,
        )
        path = os.path.join(out_dir, filename)
        image.save(path, fmt.qt_format, quality)
        written.append(path)
    return written
