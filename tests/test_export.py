import pytest

from app.export import (
    FORMATS,
    find_format,
    page_filename,
    pdf_filename,
    supported_formats,
)


def labels(formats):
    return [f.label for f in formats]


def test_every_format_is_findable_by_its_label():
    assert labels(FORMATS) == ["PNG", "JPEG", "WEBP", "TIFF", "PDF"]


@pytest.mark.parametrize(
    "label,extension",
    [("PNG", "png"), ("JPEG", "jpg"), ("WEBP", "webp"), ("TIFF", "tif"), ("PDF", "pdf")],
)
def test_format_extensions(label, extension):
    assert find_format(label).extension == extension


@pytest.mark.parametrize("label", ["JPEG", "WEBP"])
def test_lossy_formats_take_a_quality_setting(label):
    assert find_format(label).supports_quality is True


@pytest.mark.parametrize("label", ["PNG", "TIFF", "PDF"])
def test_lossless_formats_ignore_quality(label):
    assert find_format(label).supports_quality is False


def test_pdf_is_the_only_single_file_format():
    assert [f.label for f in FORMATS if f.is_pdf] == ["PDF"]


def test_unknown_format_label_is_rejected():
    with pytest.raises(KeyError):
        find_format("GIF")


def test_formats_qt_cannot_write_are_dropped():
    assert labels(supported_formats({"png", "jpeg"})) == ["PNG", "JPEG", "PDF"]


def test_plugin_backed_formats_appear_when_qt_can_write_them():
    assert labels(supported_formats({"png", "jpeg", "webp", "tiff"})) == [
        "PNG", "JPEG", "WEBP", "TIFF", "PDF",
    ]


def test_pdf_survives_even_with_no_image_support():
    assert labels(supported_formats(set())) == ["PDF"]


def test_page_filename_pads_the_page_number():
    assert page_filename(
        "report", 7, include_doc_name=True, suffix="page_", padding=3, extension="jpg"
    ) == "report_page_007.jpg"


def test_page_filename_without_padding_uses_the_bare_number():
    assert page_filename(
        "report", 7, include_doc_name=True, suffix="page_", padding=0, extension="png"
    ) == "report_page_7.png"


def test_page_filename_can_omit_the_document_name():
    assert page_filename(
        "report", 1, include_doc_name=False, suffix="page_", padding=2, extension="webp"
    ) == "page_01.webp"


def test_pdf_filename_is_derived_from_the_document_name():
    assert pdf_filename("report", include_doc_name=True) == "report_export.pdf"


def test_pdf_filename_falls_back_when_the_document_name_is_omitted():
    assert pdf_filename("report", include_doc_name=False) == "export.pdf"
