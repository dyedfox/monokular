"""Facts about an open PDF for the Info dialog, gathered without any UI."""
import os
import re
from dataclasses import dataclass, field

from PyQt6.QtCore import QDate, QDateTime, QTime, QTimeZone

from app.pdf_renderer import PdfRenderer

MM_PER_POINT = 25.4 / 72

# Common paper sizes in millimetres, portrait.
PAPER_SIZES = [
    ("A3", 297, 420),
    ("A4", 210, 297),
    ("A5", 148, 210),
    ("Letter", 215.9, 279.4),
    ("Legal", 215.9, 355.6),
]

# How far a page may be from a paper size, or from another page, and still
# count as the same size: generators round, and scanners crop a little.
SIZE_TOLERANCE_MM = 2.0

# Content kinds, as stored in PdfInfo.content.
TEXT, SCANNED, MIXED, EMPTY = "text", "scanned", "mixed", "empty"

#: Metadata keys shown, in order, when the PDF fills them in.
METADATA_KEYS = ["title", "author", "subject", "keywords", "creator", "producer"]


@dataclass
class PdfInfo:
    path: str
    file_size: int
    page_count: int
    page_width_mm: float
    page_height_mm: float
    paper: str | None  # e.g. "A4"; None when it matches no common size
    mixed_sizes: bool
    content: str  # TEXT, SCANNED, MIXED or EMPTY
    pdf_version: str
    encrypted: bool
    metadata: dict[str, str] = field(default_factory=dict)  # only non-empty METADATA_KEYS
    created: QDateTime | None = None
    modified: QDateTime | None = None

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def folder(self) -> str:
        return os.path.dirname(self.path)


def _same_size(a: tuple[float, float], b: tuple[float, float]) -> bool:
    """Equal within tolerance, ignoring orientation: a landscape spread of an
    A4 document is still A4."""
    a, b = sorted(a), sorted(b)
    return all(abs(x - y) <= SIZE_TOLERANCE_MM for x, y in zip(a, b))


def paper_name(width_mm: float, height_mm: float) -> str | None:
    for name, w, h in PAPER_SIZES:
        if _same_size((width_mm, height_mm), (w, h)):
            return name
    return None


_PDF_DATE = re.compile(
    r"(?:D:)?(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?"
    r"(?:([Zz])|([+-])(\d{2})'?(\d{2})?'?)?"
)


def parse_pdf_date(value: str) -> QDateTime | None:
    """A PDF date ("D:20240131154500+02'00'") as a QDateTime, or None.

    Everything after the year is optional in the spec; missing parts default
    to the start of their range, and a missing zone means local time.
    """
    match = _PDF_DATE.match(value.strip())
    if not match:
        return None
    year, month, day, hour, minute, second, utc, sign, tz_hours, tz_minutes = match.groups()
    date = QDate(int(year), int(month or 1), int(day or 1))
    time = QTime(int(hour or 0), int(minute or 0), int(second or 0))
    if not date.isValid() or not time.isValid():
        return None
    if utc:
        return QDateTime(date, time, QTimeZone.utc())
    if sign:
        offset = int(tz_hours) * 3600 + int(tz_minutes or 0) * 60
        return QDateTime(date, time, QTimeZone(offset if sign == "+" else -offset))
    return QDateTime(date, time)


def _content_kind(doc) -> str:
    has_text = has_scans = False
    for page in doc:
        if page.get_text("text").strip():
            has_text = True
        elif page.get_images():
            has_scans = True
        if has_text and has_scans:
            return MIXED
    if has_scans:
        return SCANNED
    return TEXT if has_text else EMPTY


def collect(renderer: PdfRenderer) -> PdfInfo:
    doc = renderer.doc
    sizes = [
        (page.rect.width * MM_PER_POINT, page.rect.height * MM_PER_POINT)
        for page in doc
    ]
    width, height = sizes[0] if sizes else (0.0, 0.0)
    meta = doc.metadata or {}
    return PdfInfo(
        path=renderer.path,
        file_size=os.path.getsize(renderer.path),
        page_count=renderer.page_count,
        page_width_mm=width,
        page_height_mm=height,
        paper=paper_name(width, height),
        mixed_sizes=any(not _same_size(s, sizes[0]) for s in sizes[1:]),
        content=_content_kind(doc),
        pdf_version=meta.get("format") or "",
        encrypted=bool(meta.get("encryption")),
        metadata={k: meta[k].strip() for k in METADATA_KEYS if (meta.get(k) or "").strip()},
        created=parse_pdf_date(meta.get("creationDate") or ""),
        modified=parse_pdf_date(meta.get("modDate") or ""),
    )
