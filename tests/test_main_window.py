import pytest

from app.main_window import MainWindow


@pytest.fixture
def window(qapp, clean_qsettings, pdf_path):
    w = MainWindow()
    w._load_pdf(pdf_path)
    yield w
    w.deleteLater()


def select(window, *indices):
    for i in indices:
        window._grid._cards[i].set_selected(True)
    window._grid.selection_changed.emit()


def test_rotate_actions_start_disabled(window):
    assert window._rotate_left_action.isEnabled() is False
    assert window._rotate_right_action.isEnabled() is False


def test_rotate_actions_enable_once_pages_are_selected(window):
    select(window, 0)
    assert window._rotate_left_action.isEnabled() is True
    assert window._rotate_right_action.isEnabled() is True


def test_rotate_actions_disable_again_when_the_selection_is_cleared(window):
    select(window, 0)
    window._deselect_all()
    assert window._rotate_right_action.isEnabled() is False


def test_rotating_turns_every_selected_page(window):
    select(window, 0, 2)
    window._rotate_selected(90)

    assert window._renderer.rotation(0) == 90
    assert window._renderer.rotation(2) == 90


def test_rotating_leaves_unselected_pages_upright(window):
    select(window, 0)
    window._rotate_selected(90)
    assert window._renderer.rotation(1) == 0


def test_rotating_updates_the_thumbnail(window):
    select(window, 0)
    tall = window._grid._cards[0].height()
    window._rotate_selected(90)
    assert window._grid._cards[0].height() < tall


def test_rotation_in_the_preview_reaches_the_grid(window):
    tall = window._grid._cards[1].height()
    window._renderer.rotate(1, 90)
    window._on_preview_rotation_changed(1)
    assert window._grid._cards[1].height() < tall


def test_opening_another_pdf_starts_from_unrotated_pages(window, pdf_path):
    select(window, 0)
    window._rotate_selected(180)
    window._load_pdf(pdf_path)
    assert window._renderer.rotation(0) == 0
