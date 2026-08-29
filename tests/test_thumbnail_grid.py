import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from app.pdf_renderer import PdfRenderer
from app.thumbnail_grid import ThumbnailGrid


@pytest.fixture
def renderer(qapp, pdf_path):
    r = PdfRenderer(pdf_path)
    yield r
    r.close()


@pytest.fixture
def grid(renderer):
    g = ThumbnailGrid()
    g.load(renderer)
    g.resize(500, 80)  # short enough that the single row of cards overflows
    g.show()
    yield g
    g.deleteLater()


def scroll_to_bottom(grid):
    bar = grid.verticalScrollBar()
    bar.setValue(bar.maximum())
    return bar


def test_the_grid_can_actually_scroll(grid):
    assert grid.verticalScrollBar().maximum() > 0


def test_scroll_to_top_button_stays_hidden_at_the_top(grid):
    assert grid._top_btn.isVisible() is False


def test_scroll_to_top_button_appears_once_scrolled_down(grid):
    scroll_to_bottom(grid)
    assert grid._top_btn.isVisible() is True


def test_scroll_to_top_button_returns_the_view_to_the_top(grid):
    bar = scroll_to_bottom(grid)
    grid._top_btn.click()
    assert bar.value() == 0


def test_scroll_to_top_button_hides_itself_again_at_the_top(grid):
    scroll_to_bottom(grid)
    grid._top_btn.click()
    assert grid._top_btn.isVisible() is False


def test_home_key_jumps_to_the_top(grid):
    bar = scroll_to_bottom(grid)
    QTest.keyClick(grid, Qt.Key.Key_Home)
    assert bar.value() == 0


def test_end_key_jumps_to_the_bottom(grid):
    bar = grid.verticalScrollBar()
    QTest.keyClick(grid, Qt.Key.Key_End)
    assert bar.value() == bar.maximum()


def test_refreshing_a_card_picks_up_the_page_rotation(grid, renderer):
    tall = grid._cards[0].height()
    renderer.rotate(0, 90)
    grid.refresh_card(0)

    thumbnail = grid._cards[0]._image.pixmap()
    assert thumbnail.width() > thumbnail.height()
    assert grid._cards[0].height() < tall


def test_refreshing_a_card_leaves_its_neighbours_alone(grid, renderer):
    untouched = grid._cards[1].height()
    renderer.rotate(0, 90)
    grid.refresh_card(0)
    assert grid._cards[1].height() == untouched


def test_refreshing_a_card_keeps_it_selected(grid, renderer):
    grid._cards[0].set_selected(True)
    renderer.rotate(0, 90)
    grid.refresh_card(0)
    assert grid._cards[0].selected is True


@pytest.fixture
def barely_scrolling_grid(renderer):
    """A grid whose content overflows by much less than one viewport height."""
    g = ThumbnailGrid()
    g.load(renderer)
    g.resize(500, 360)
    g.show()
    yield g
    g.deleteLater()


def test_a_short_overflow_still_scrolls(barely_scrolling_grid):
    bar = barely_scrolling_grid.verticalScrollBar()
    assert 0 < bar.maximum() < barely_scrolling_grid.viewport().height() // 2


def test_top_button_appears_even_when_the_document_barely_overflows(barely_scrolling_grid):
    scroll_to_bottom(barely_scrolling_grid)
    assert barely_scrolling_grid._top_btn.isVisible() is True


def test_top_button_stays_hidden_when_nothing_can_scroll(renderer):
    grid = ThumbnailGrid()
    grid.load(renderer)
    grid.resize(500, 900)
    grid.show()
    assert grid.verticalScrollBar().maximum() == 0
    assert grid._top_btn.isVisible() is False
