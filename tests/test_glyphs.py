import pytest
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QPushButton, QStyle, QStyleFactory

from app import glyphs, omarchy_theme


@pytest.fixture
def on_omarchy(qapp, monkeypatch):
    monkeypatch.setenv("OMARCHY_PATH", "/usr/share/omarchy")
    if not glyphs._has_glyph(glyphs.GLYPHS["rotate-left"]):
        pytest.skip("the monospace font has no Nerd Font glyphs")


def test_outside_omarchy_a_button_keeps_its_symbol(qapp, monkeypatch):
    monkeypatch.delenv("OMARCHY_PATH", raising=False)
    button = QPushButton("↺")

    assert glyphs.apply(button, "rotate-left") is False
    assert button.text() == "↺"
    assert button.icon().isNull()


def test_on_omarchy_a_button_shows_only_the_glyph(on_omarchy):
    button = QPushButton("↺")

    assert glyphs.apply(button, "rotate-left") is True
    assert button.text() == ""
    assert not button.icon().isNull()


def test_on_omarchy_a_toolbar_action_keeps_its_name(on_omarchy):
    action = QAction("↺")

    assert glyphs.apply(action, "rotate-left") is True
    assert action.text() == "↺"
    assert not action.icon().isNull()


def test_an_unmapped_name_leaves_the_button_alone(on_omarchy):
    button = QPushButton("?")

    assert glyphs.apply(button, "no-such-icon") is False
    assert button.text() == "?"


def test_omarchy_style_drops_icons_from_dialog_buttons(qapp):
    style = omarchy_theme._OmarchyStyle("Fusion")
    assert style.styleHint(QStyle.StyleHint.SH_DialogButtonBox_ButtonsHaveIcons) == 0


def test_omarchy_style_otherwise_behaves_like_fusion(qapp):
    style = omarchy_theme._OmarchyStyle("Fusion")
    fusion = QStyleFactory.create("Fusion")
    hint = QStyle.StyleHint.SH_ScrollBar_MiddleClickAbsolutePosition
    assert style.styleHint(hint) == fusion.styleHint(hint)
