import os

import pytest
from PyQt6.QtGui import QImage

from app.export import Naming, export_pages, find_format, resolve_output_dir
from app.pdf_renderer import PdfRenderer


@pytest.fixture
def renderer(qapp, pdf_path):
    r = PdfRenderer(pdf_path)
    yield r
    r.close()


NAMING = Naming(include_doc_name=True, suffix="page_", padding=2)


def test_export_writes_one_file_per_selected_page(renderer, tmp_path):
    written = export_pages(
        renderer, [0, 2], str(tmp_path), find_format("PNG"), ppi=72, quality=-1, naming=NAMING
    )

    assert [os.path.basename(p) for p in written] == ["sample_page_01.png", "sample_page_03.png"]
    assert all(os.path.isfile(p) for p in written)


def test_exported_file_is_readable_in_the_chosen_format(renderer, tmp_path):
    written = export_pages(
        renderer, [0], str(tmp_path), find_format("PNG"), ppi=72, quality=-1, naming=NAMING
    )
    assert QImage(written[0]).size().isValid()


def test_resolution_drives_the_exported_pixel_size(renderer, tmp_path):
    written = export_pages(
        renderer, [0], str(tmp_path), find_format("PNG"), ppi=144, quality=-1, naming=NAMING
    )
    # The fixture page is 200x400pt; 144 PPI is twice the PDF's native 72.
    assert (QImage(written[0]).width(), QImage(written[0]).height()) == (400, 800)


def test_rotation_reaches_the_exported_image(renderer, tmp_path):
    renderer.rotate(0, 90)
    written = export_pages(
        renderer, [0], str(tmp_path), find_format("PNG"), ppi=72, quality=-1, naming=NAMING
    )
    assert (QImage(written[0]).width(), QImage(written[0]).height()) == (400, 200)


def test_lower_jpeg_quality_produces_a_smaller_file(renderer, tmp_path):
    coarse = tmp_path / "coarse"
    fine = tmp_path / "fine"
    coarse.mkdir()
    fine.mkdir()
    jpeg = find_format("JPEG")

    small = export_pages(renderer, [0], str(coarse), jpeg, ppi=150, quality=10, naming=NAMING)
    large = export_pages(renderer, [0], str(fine), jpeg, ppi=150, quality=95, naming=NAMING)

    assert os.path.getsize(small[0]) < os.path.getsize(large[0])


def test_output_defaults_to_the_folder_holding_the_pdf(tmp_path):
    pdf = tmp_path / "docs" / "a.pdf"
    assert resolve_output_dir(
        "same_as_pdf", fixed_path="", last_used_path="", pdf_path=str(pdf)
    ) == str(tmp_path / "docs")


def test_fixed_output_mode_uses_the_configured_folder(tmp_path):
    assert resolve_output_dir(
        "fixed", fixed_path=str(tmp_path), last_used_path="", pdf_path="/docs/a.pdf"
    ) == str(tmp_path)


def test_fixed_output_mode_falls_back_when_the_folder_is_gone(tmp_path):
    assert resolve_output_dir(
        "fixed", fixed_path=str(tmp_path / "missing"), last_used_path="", pdf_path="/docs/a.pdf"
    ) == "/docs"


def test_last_used_output_mode_falls_back_when_never_set():
    assert resolve_output_dir(
        "last_used", fixed_path="", last_used_path="", pdf_path="/docs/a.pdf"
    ) == "/docs"


@pytest.mark.parametrize("label", ["WEBP", "TIFF"])
def test_plugin_backed_formats_round_trip(renderer, tmp_path, label):
    from app.export import available_formats

    if label not in {f.label for f in available_formats()}:
        pytest.skip(f"Qt has no {label} writer plugin installed")

    written = export_pages(
        renderer, [0], str(tmp_path), find_format(label), ppi=72, quality=80, naming=NAMING
    )
    assert QImage(written[0]).size().isValid()
