import os

import pytest
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QApplication, QFormLayout, QLabel

from app import pdf_info
from app.info_dialog import InfoDialog


def make_info(**overrides):
    values = dict(
        path="/data/scans/magazine.pdf", file_size=2_500_000, page_count=72,
        page_width_mm=210.0, page_height_mm=297.0, paper="A4", mixed_sizes=False,
        content=pdf_info.SCANNED, pdf_version="PDF 1.5", encrypted=False,
        metadata={}, created=None, modified=None,
    )
    values.update(overrides)
    return pdf_info.PdfInfo(**values)


def rows(dialog):
    """{label: value} for every labelled row."""
    form = dialog._form
    out = {}
    for i in range(form.rowCount()):
        label = form.itemAt(i, QFormLayout.ItemRole.LabelRole)
        field = form.itemAt(i, QFormLayout.ItemRole.FieldRole)
        if label and field:
            out[label.widget().text()] = field.widget().text()
    return out


@pytest.fixture
def show(qapp):
    made = []

    def make(**overrides):
        d = InfoDialog(make_info(**overrides))
        made.append(d)
        return d

    yield make
    for d in made:
        d.deleteLater()


def test_file_and_document_facts_are_shown(show):
    r = rows(show())
    assert r["Name:"] == "magazine.pdf"
    assert r["Pages:"] == "72"
    assert r["Page size:"] == "A4 (210 × 297 mm)"
    assert r["Content:"] == "Scanned (images only)"
    assert r["PDF version:"] == "1.5"


def test_a_size_without_a_paper_name_shows_just_millimetres(show):
    assert rows(show(paper=None, page_width_mm=100.4, page_height_mm=150.6))["Page size:"] == "100 × 151 mm"


def test_mixed_page_sizes_say_so(show):
    assert rows(show(mixed_sizes=True))["Page size:"] == "Mixed"


def test_a_folder_under_home_is_shown_with_a_tilde(show):
    home = os.path.expanduser("~")
    folder = rows(show(path=os.path.join(home, "Docs", "a.pdf")))["Folder:"]
    assert folder.replace("​", "") == "~/Docs"


def test_without_metadata_there_is_no_metadata_section(show):
    d = show()
    headings = [w.text() for w in d.findChildren(QLabel) if w.font().bold()]
    assert "Metadata" not in headings
    assert "Title:" not in rows(d)


def test_filled_metadata_and_dates_are_shown(show):
    created = QDateTime.fromString("2024-01-31T15:45:00", "yyyy-MM-ddTHH:mm:ss")
    r = rows(show(metadata={"title": "Issue 12", "producer": "Scanner"}, created=created))
    assert r["Title:"] == "Issue 12"
    assert r["Producer:"] == "Scanner"
    assert "Created:" in r
    assert "Author:" not in r and "Modified:" not in r


def test_encryption_is_shown_only_when_present(show):
    assert "Encrypted:" not in rows(show())
    assert rows(show(encrypted=True))["Encrypted:"] == "Yes"


def test_copy_path_puts_the_real_path_on_the_clipboard(show):
    show()._copy_path_btn.click()
    assert QApplication.clipboard().text() == "/data/scans/magazine.pdf"


def test_open_folder_opens_the_containing_folder(show, monkeypatch):
    from PyQt6.QtGui import QDesktopServices

    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()))
    show()._open_folder_btn.click()
    assert opened == ["/data/scans"]
