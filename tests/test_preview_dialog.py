import pytest

from app.pdf_renderer import PdfRenderer
from app.preview_dialog import PreviewDialog


@pytest.fixture
def renderer(qapp, pdf_path):
    r = PdfRenderer(pdf_path)
    yield r
    r.close()


@pytest.fixture
def preview(renderer, clean_qsettings):
    d = PreviewDialog(renderer, 0)
    yield d
    d.deleteLater()


def test_rotate_right_turns_the_page_clockwise(preview, renderer):
    preview._rotate_right()
    assert renderer.rotation(0) == 90


def test_rotate_left_turns_the_page_anticlockwise(preview, renderer):
    preview._rotate_left()
    assert renderer.rotation(0) == 270


def test_rotation_reaches_the_image_on_screen(preview):
    upright = preview._image_label.pixmap()
    assert upright.height() > upright.width()

    preview._rotate_right()
    assert preview._image_label.pixmap().width() > preview._image_label.pixmap().height()


def test_rotation_is_announced_for_the_page_it_changed(preview):
    seen = []
    preview.rotation_changed.connect(seen.append)

    preview._go_next()
    preview._rotate_right()

    assert seen == [1]


def test_rotating_one_page_leaves_its_neighbours_upright(preview, renderer):
    preview._rotate_right()
    assert renderer.rotation(1) == 0
    assert renderer.rotation(2) == 0


def test_preview_size_is_remembered_for_the_next_opening(renderer, clean_qsettings):
    first = PreviewDialog(renderer, 0)
    first.show()
    first.resize(720, 540)
    first.close()

    second = PreviewDialog(renderer, 0)
    second.show()
    assert (second.width(), second.height()) == (720, 540)


def test_first_ever_preview_uses_the_default_size(renderer, clean_qsettings):
    first = PreviewDialog(renderer, 0)
    first.show()
    assert (first.width(), first.height()) == (960, 720)
