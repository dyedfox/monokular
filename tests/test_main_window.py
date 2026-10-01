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


def drop_event(path):
    from PyQt6.QtCore import QMimeData, QPointF, Qt, QUrl
    from PyQt6.QtGui import QDropEvent

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(path)])
    event = QDropEvent(
        QPointF(10, 10), Qt.DropAction.CopyAction, mime,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    return event, mime


def test_a_dropped_pdf_is_accepted_and_loaded_after_the_drop_returns(qapp, clean_qsettings, pdf_path):
    w = MainWindow()
    event, _mime = drop_event(pdf_path)
    w.dropEvent(event)

    # The drop handler itself must return quickly, before any rendering.
    assert event.isAccepted()
    assert w._renderer is None

    from PyQt6.QtTest import QTest
    QTest.qWait(50)
    assert w._renderer is not None and w._renderer.path == pdf_path
    w.deleteLater()


def test_about_links_to_the_project_repository(window, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    shown = []
    monkeypatch.setattr(QMessageBox, "about", lambda parent, title, text: shown.append(text))
    window._show_about()

    assert '<a href="https://github.com/dyedfox/monokular">' in shown[0]


def test_info_is_unavailable_until_a_pdf_is_open(qapp, clean_qsettings):
    w = MainWindow()
    assert w._info_action.isEnabled() is False
    w.deleteLater()


def test_info_tooltip_names_the_open_file(window, pdf_path):
    import os

    assert window._info_action.isEnabled() is True
    assert window._info_action.toolTip().startswith(os.path.basename(pdf_path))


def test_info_opens_with_the_open_documents_facts(window, monkeypatch):
    from app import info_dialog

    shown = []
    monkeypatch.setattr(info_dialog.InfoDialog, "exec", lambda self: shown.append(self._info))
    window._info_action.trigger()

    assert shown[0].path == window._renderer.path
    assert shown[0].page_count == window._renderer.page_count
