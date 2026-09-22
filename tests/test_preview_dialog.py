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


def test_go_first_jumps_to_the_first_page(renderer, clean_qsettings):
    preview = PreviewDialog(renderer, 2)
    preview._go_first()
    assert preview._page_index == 0
    assert preview._page_input.text() == "1"


def test_go_last_jumps_to_the_last_page(preview):
    preview._go_last()
    assert preview._page_index == preview._page_count - 1
    assert preview._page_input.text() == str(preview._page_count)


def test_page_input_reflects_navigation(preview):
    preview._go_next()
    assert preview._page_input.text() == "2"


def test_typing_a_page_number_and_pressing_enter_jumps_there(preview):
    preview._page_input.setText("3")
    preview._jump_to_page_input()
    assert preview._page_index == 2


def test_jumping_to_the_current_page_does_not_re_render(preview, monkeypatch):
    calls = []
    monkeypatch.setattr(preview, "_render", lambda: calls.append(1))
    preview._page_input.setText("1")
    preview._jump_to_page_input()
    assert calls == []


def test_invalid_page_input_reverts_to_the_current_page(preview):
    preview._go_next()
    preview._page_input.setText("")
    preview._jump_to_page_input()
    assert preview._page_index == 1
    assert preview._page_input.text() == "2"
