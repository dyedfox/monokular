import fitz
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QImage, QPixmap


class PdfRenderer:
    """Wraps PyMuPDF to render PDF pages as QPixmaps."""

    def __init__(self, path: str):
        self._doc = fitz.open(path)
        self.path = path

    @property
    def page_count(self) -> int:
        return len(self._doc)

    def rotation(self, index: int) -> int:
        """Rotation in degrees as the page is currently rendered."""
        return self._doc[index].rotation

    def rotate(self, index: int, delta: int):
        """Turn a page by delta degrees, wrapping into 0-359."""
        page = self._doc[index]
        page.set_rotation((page.rotation + delta) % 360)

    def render_page(self, index: int, width: int) -> QPixmap:
        page = self._doc[index]
        scale = width / page.rect.width
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(img)

    def render_page_at_ppi(self, index: int, ppi: int) -> QImage:
        """Render a page at a specific PPI (pixels per inch)."""
        page = self._doc[index]
        scale = ppi / 72.0  # PDF default is 72 PPI
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        # Store PPI in the image metadata
        dpm = int(ppi / 0.0254)  # dots per meter
        img.setDotsPerMeterX(dpm)
        img.setDotsPerMeterY(dpm)
        return img

    def write_pdf(self, indices: list[int], out_path: str) -> str:
        """Copy the given pages, in the given order, into a new PDF."""
        out = fitz.open()
        for idx in indices:
            out.insert_pdf(self._doc, from_page=idx, to_page=idx)
        out.save(out_path)
        out.close()
        return out_path

    def page_size(self, index: int) -> QSize:
        rect = self._doc[index].rect
        return QSize(int(rect.width), int(rect.height))

    def close(self):
        self._doc.close()
