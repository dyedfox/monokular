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

    def page_size(self, index: int) -> QSize:
        rect = self._doc[index].rect
        return QSize(int(rect.width), int(rect.height))

    def close(self):
        self._doc.close()
