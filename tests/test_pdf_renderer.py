import fitz
import pytest

from app.pdf_renderer import PdfRenderer
from tests.conftest import PAGE_COUNT


@pytest.fixture
def renderer(qapp, pdf_path):
    r = PdfRenderer(pdf_path)
    yield r
    r.close()


def test_new_renderer_reports_no_rotation(renderer):
    assert [renderer.rotation(i) for i in range(PAGE_COUNT)] == [0] * PAGE_COUNT


def test_rotate_accumulates_clockwise(renderer):
    renderer.rotate(0, 90)
    renderer.rotate(0, 90)
    assert renderer.rotation(0) == 180


def test_rotate_wraps_past_full_turn(renderer):
    renderer.rotate(1, 270)
    renderer.rotate(1, 180)
    assert renderer.rotation(1) == 90


def test_rotate_counter_clockwise_wraps_below_zero(renderer):
    renderer.rotate(2, -90)
    assert renderer.rotation(2) == 270


def test_rotate_affects_only_the_named_page(renderer):
    renderer.rotate(1, 90)
    assert renderer.rotation(0) == 0
    assert renderer.rotation(2) == 0


def test_render_page_honours_requested_width(renderer):
    assert renderer.render_page(0, 300).width() == 300


def test_rotating_a_page_swaps_its_rendered_aspect(renderer):
    upright = renderer.render_page(0, 300)
    assert upright.height() > upright.width()

    renderer.rotate(0, 90)
    turned = renderer.render_page(0, 300)
    assert turned.width() > turned.height()


def test_render_at_ppi_swaps_dimensions_when_rotated(renderer):
    upright = renderer.render_page_at_ppi(0, 72)
    assert (upright.width(), upright.height()) == (200, 400)

    renderer.rotate(0, 90)
    turned = renderer.render_page_at_ppi(0, 72)
    assert (turned.width(), turned.height()) == (400, 200)


def test_page_size_reflects_rotation(renderer):
    assert (renderer.page_size(0).width(), renderer.page_size(0).height()) == (200, 400)
    renderer.rotate(0, 90)
    assert (renderer.page_size(0).width(), renderer.page_size(0).height()) == (400, 200)


def test_write_pdf_keeps_only_the_selected_pages_in_order(renderer, tmp_path):
    out = tmp_path / "out.pdf"
    renderer.write_pdf([2, 0], str(out))

    doc = fitz.open(str(out))
    assert doc.page_count == 2
    assert "Page 3" in doc[0].get_text()
    assert "Page 1" in doc[1].get_text()
    doc.close()


def test_write_pdf_carries_page_rotation(renderer, tmp_path):
    out = tmp_path / "out.pdf"
    renderer.rotate(1, 90)
    renderer.write_pdf([1], str(out))

    doc = fitz.open(str(out))
    assert doc[0].rotation == 90
    doc.close()


def test_write_pdf_returns_the_path_it_wrote(renderer, tmp_path):
    out = tmp_path / "out.pdf"
    assert renderer.write_pdf([0], str(out)) == str(out)
