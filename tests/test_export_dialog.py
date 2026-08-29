import os

import pytest
from PyQt6.QtWidgets import QMessageBox

from app.export_dialog import ExportDialog
from app.pdf_renderer import PdfRenderer


@pytest.fixture
def renderer(qapp, pdf_path):
    r = PdfRenderer(pdf_path)
    yield r
    r.close()


@pytest.fixture
def out_dir(tmp_path):
    d = tmp_path / "out"
    d.mkdir()
    return d


@pytest.fixture
def dialog(renderer, settings, out_dir):
    settings.set("export/output_mode", "fixed")
    settings.set("export/fixed_path", str(out_dir))
    d = ExportDialog(renderer, [0, 1], settings)
    yield d
    d.deleteLater()


@pytest.mark.parametrize("label,enabled", [("PNG", False), ("JPEG", True), ("WEBP", True), ("TIFF", False)])
def test_quality_follows_the_chosen_format(dialog, label, enabled):
    dialog._format.setCurrentText(label)
    assert dialog._quality.isEnabled() is enabled


def test_pdf_export_has_no_resolution_or_quality(dialog):
    dialog._format.setCurrentText("PDF")
    assert dialog._ppi.isEnabled() is False
    assert dialog._quality.isEnabled() is False


def test_pdf_export_targets_a_single_file(dialog, out_dir):
    dialog._format.setCurrentText("PDF")
    assert dialog._out_edit.text() == str(out_dir / "sample_export.pdf")


def test_switching_back_to_an_image_format_targets_a_folder(dialog, out_dir):
    dialog._format.setCurrentText("PDF")
    dialog._format.setCurrentText("PNG")
    assert dialog._out_edit.text() == str(out_dir)


def test_exporting_images_writes_one_file_per_page(dialog, out_dir, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    dialog._format.setCurrentText("PNG")
    dialog._export()

    assert sorted(os.listdir(out_dir)) == ["sample_page_01.png", "sample_page_02.png"]


def test_exporting_pdf_writes_one_document(dialog, out_dir, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    dialog._format.setCurrentText("PDF")
    dialog._export()

    assert os.listdir(out_dir) == ["sample_export.pdf"]


def test_export_records_the_folder_it_used(dialog, settings, out_dir, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    dialog._format.setCurrentText("PNG")
    dialog._export()

    assert settings.get("export/last_used_path") == str(out_dir)
