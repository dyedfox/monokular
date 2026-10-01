import fitz
import pytest
from PyQt6.QtCore import QDate, QTime

from app import pdf_info
from app.pdf_renderer import PdfRenderer

A4 = (595.28, 841.89)  # points


def make_pdf(tmp_path, pages, metadata=None):
    """pages: list of (size, kind) where kind is "text", "image" or "blank"."""
    doc = fitz.open()
    for size, kind in pages:
        page = doc.new_page(width=size[0], height=size[1])
        if kind == "text":
            page.insert_text((50, 50), "Hello")
        elif kind == "image":
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
            pix.clear_with(200)
            page.insert_image(page.rect, pixmap=pix)
    if metadata:
        doc.set_metadata(metadata)
    path = tmp_path / "doc.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def collect(qapp):
    opened = []

    def run(path):
        r = PdfRenderer(path)
        opened.append(r)
        return pdf_info.collect(r)

    yield run
    for r in opened:
        r.close()


def test_an_a4_page_is_named_a4(tmp_path, collect):
    info = collect(make_pdf(tmp_path, [(A4, "text")]))
    assert info.paper == "A4"
    assert (round(info.page_width_mm), round(info.page_height_mm)) == (210, 297)


def test_a_landscape_a4_page_is_still_a4():
    assert pdf_info.paper_name(297, 210) == "A4"


def test_an_unusual_size_has_no_paper_name():
    assert pdf_info.paper_name(100, 100) is None


def test_portrait_and_landscape_pages_of_one_paper_are_not_mixed(tmp_path, collect):
    info = collect(make_pdf(tmp_path, [(A4, "text"), ((A4[1], A4[0]), "text")]))
    assert info.mixed_sizes is False


def test_pages_of_different_papers_are_mixed(tmp_path, collect):
    info = collect(make_pdf(tmp_path, [(A4, "text"), ((612, 792), "text")]))
    assert info.mixed_sizes is True


@pytest.mark.parametrize("kinds, expected", [
    (["text", "text"], pdf_info.TEXT),
    (["image", "image"], pdf_info.SCANNED),
    (["text", "image"], pdf_info.MIXED),
    (["blank"], pdf_info.EMPTY),
])
def test_content_tells_text_from_scans(tmp_path, collect, kinds, expected):
    info = collect(make_pdf(tmp_path, [(A4, k) for k in kinds]))
    assert info.content == expected


def test_only_filled_metadata_is_kept(tmp_path, collect):
    info = collect(make_pdf(tmp_path, [(A4, "text")], {"title": "Report", "author": "  "}))
    assert info.metadata["title"] == "Report"
    assert "author" not in info.metadata


def test_file_facts(tmp_path, collect):
    path = make_pdf(tmp_path, [(A4, "text")] * 3)
    info = collect(path)
    assert info.name == "doc.pdf"
    assert info.folder == str(tmp_path)
    assert info.page_count == 3
    assert info.file_size > 0
    assert info.pdf_version.startswith("PDF ")
    assert info.encrypted is False


def test_a_full_pdf_date_keeps_its_time_zone():
    when = pdf_info.parse_pdf_date("D:20240131154500+02'00'")
    assert when.date() == QDate(2024, 1, 31)
    assert when.time() == QTime(15, 45, 0)
    assert when.offsetFromUtc() == 2 * 3600


def test_a_utc_pdf_date():
    assert pdf_info.parse_pdf_date("D:20240131154500Z").offsetFromUtc() == 0


def test_a_year_alone_is_a_valid_pdf_date():
    assert pdf_info.parse_pdf_date("D:2024").date() == QDate(2024, 1, 1)


@pytest.mark.parametrize("value", ["", "garbage", "D:20241399"])
def test_unreadable_pdf_dates_are_dropped(value):
    assert pdf_info.parse_pdf_date(value) is None
