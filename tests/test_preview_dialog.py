import pytest

from app import settings
from app.pdf_renderer import PdfRenderer
from app.preview_dialog import ZOOM_LEVELS, PreviewDialog


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


def test_preview_size_is_remembered_on_wayland(renderer, clean_qsettings, monkeypatch):
    monkeypatch.setattr(settings, "_is_wayland", lambda: True)
    first = PreviewDialog(renderer, 0)
    first.show()
    first.resize(720, 540)
    first.close()

    second = PreviewDialog(renderer, 0)
    second.show()
    assert (second.width(), second.height()) == (720, 540)


def test_compositor_maximized_flag_does_not_shrink_the_preview_on_wayland(
        renderer, clean_qsettings, monkeypatch):
    # Hyprland reports even floating dialogs as maximized; the size the user
    # actually sees must still be what comes back next time.
    monkeypatch.setattr(settings, "_is_wayland", lambda: True)
    first = PreviewDialog(renderer, 0)
    first.show()
    first.resize(720, 540)
    monkeypatch.setattr(first, "saveGeometry", lambda: pytest.fail("blob used on Wayland"))
    first.close()

    second = PreviewDialog(renderer, 0)
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


def wheel(dialog, delta, ctrl=False):
    """Deliver a wheel turn to the page area, as a mouse over the page would."""
    from PyQt6.QtCore import QPoint, QPointF, Qt
    from PyQt6.QtGui import QWheelEvent
    from PyQt6.QtWidgets import QApplication

    modifiers = Qt.KeyboardModifier.ControlModifier if ctrl else Qt.KeyboardModifier.NoModifier
    event = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10), QPoint(0, 0), QPoint(0, delta),
        Qt.MouseButton.NoButton, modifiers, Qt.ScrollPhase.NoScrollPhase, False,
    )
    QApplication.sendEvent(dialog._scroll.viewport(), event)


@pytest.fixture
def make_preview(renderer, clean_qsettings):
    made = []

    def make(action, page=1):
        d = PreviewDialog(renderer, page, wheel_action=action)
        made.append(d)
        return d

    yield make
    for d in made:
        d.close()  # shown ones would otherwise keep the focus from later tests
        d.deleteLater()


def test_by_default_the_wheel_neither_zooms_nor_turns_pages(make_preview):
    d = make_preview("scroll")
    wheel(d, -120)
    assert d._page_index == 1
    assert d._zoom_idx == ZOOM_LEVELS.index(1.0)


def test_in_navigate_mode_wheeling_down_goes_to_the_next_page(make_preview):
    d = make_preview("navigate")
    wheel(d, -120)
    assert d._page_index == 2


def test_in_navigate_mode_wheeling_up_goes_to_the_previous_page(make_preview):
    d = make_preview("navigate")
    wheel(d, 120)
    assert d._page_index == 0


def test_in_zoom_mode_wheeling_up_zooms_in(make_preview):
    d = make_preview("zoom")
    wheel(d, 120)
    assert d._zoom_idx == ZOOM_LEVELS.index(1.0) + 1
    assert d._page_index == 1


def test_ctrl_wheel_zooms_even_in_navigate_mode(make_preview):
    d = make_preview("navigate")
    wheel(d, -120, ctrl=True)
    assert d._zoom_idx == ZOOM_LEVELS.index(1.0) - 1
    assert d._page_index == 1


def test_touchpad_fractions_add_up_to_a_single_page_turn(make_preview):
    d = make_preview("navigate", page=0)
    for _ in range(3):
        wheel(d, -40)
    assert d._page_index == 1


def test_reversing_direction_drops_a_half_finished_step(make_preview):
    d = make_preview("navigate")
    wheel(d, -100)
    wheel(d, 100)
    assert d._page_index == 1


def mouse(dialog, kind, x, y, button=None):
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtWidgets import QApplication

    left = Qt.MouseButton.LeftButton
    types = {"press": QEvent.Type.MouseButtonPress, "move": QEvent.Type.MouseMove,
             "release": QEvent.Type.MouseButtonRelease}
    pressed = Qt.MouseButton.NoButton if kind == "release" else left
    viewport = dialog._scroll.viewport()
    local = QPointF(x, y)
    event = QMouseEvent(
        types[kind], local, viewport.mapToGlobal(local),
        Qt.MouseButton.NoButton if kind == "move" else (button or left),
        pressed, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewport, event)


def shown(d, width=600, height=400):
    from PyQt6.QtWidgets import QApplication
    d.resize(width, height)
    d.show()
    QApplication.processEvents()
    return d


def bars(d):
    return d._scroll.horizontalScrollBar(), d._scroll.verticalScrollBar()


def test_dragging_a_zoomed_page_moves_it_with_the_mouse(make_preview):
    from PyQt6.QtWidgets import QApplication
    d = shown(make_preview("scroll"))
    d._zoom_idx = len(ZOOM_LEVELS) - 1
    d._render()
    QApplication.processEvents()
    h, v = bars(d)
    h.setValue(h.maximum() // 2)
    v.setValue(v.maximum() // 2)
    start_h, start_v = h.value(), v.value()

    mouse(d, "press", 200, 200)
    mouse(d, "move", 150, 120)  # drag left and up: the view moves right and down
    mouse(d, "release", 150, 120)

    assert (h.value(), v.value()) == (start_h + 50, start_v + 80)


def test_dragging_works_whatever_the_wheel_does(make_preview):
    from PyQt6.QtWidgets import QApplication
    d = shown(make_preview("navigate"))
    d._zoom_idx = len(ZOOM_LEVELS) - 1
    d._render()
    QApplication.processEvents()
    _, v = bars(d)

    mouse(d, "press", 200, 200)
    mouse(d, "move", 200, 100)
    mouse(d, "release", 200, 100)

    assert v.value() == 100
    assert d._page_index == 1


def test_the_hand_cursor_shows_only_when_there_is_room_to_drag(make_preview):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    d = shown(make_preview("scroll"), width=1600, height=1200)
    d._zoom_idx = 0  # 25%: the page fits
    d._render()
    QApplication.processEvents()
    viewport = d._scroll.viewport()
    assert viewport.cursor().shape() == Qt.CursorShape.ArrowCursor

    d._zoom_idx = len(ZOOM_LEVELS) - 1
    d._render()
    QApplication.processEvents()
    assert viewport.cursor().shape() == Qt.CursorShape.OpenHandCursor

    mouse(d, "press", 100, 100)
    assert viewport.cursor().shape() == Qt.CursorShape.ClosedHandCursor
    mouse(d, "release", 100, 100)
    assert viewport.cursor().shape() == Qt.CursorShape.OpenHandCursor


def test_a_press_on_a_page_that_fits_is_left_alone(make_preview):
    from PyQt6.QtWidgets import QApplication
    d = shown(make_preview("scroll"), width=1600, height=1200)
    d._zoom_idx = 0
    d._render()
    QApplication.processEvents()

    mouse(d, "press", 100, 100)
    assert d._pan_origin is None
