import pytest

from app.export import available_formats
from app.settings_dialog import SettingsDialog


@pytest.fixture
def dialog(qapp, settings):
    d = SettingsDialog(settings)
    yield d
    d.deleteLater()


def combo_items(combo):
    return [combo.itemText(i) for i in range(combo.count())]


def test_default_format_offers_everything_the_export_dialog_offers(dialog):
    assert combo_items(dialog._format) == [f.label for f in available_formats()]


def test_a_newly_chosen_default_format_is_saved(dialog, settings):
    dialog._format.setCurrentText("WEBP")
    dialog._save()
    assert settings.get("export/format") == "WEBP"


def test_name_preview_follows_the_chosen_format(dialog):
    dialog._format.setCurrentText("PNG")
    assert dialog._name_preview.text() == "document_page_01.png"


def test_name_preview_shows_the_single_file_name_for_pdf(dialog):
    dialog._format.setCurrentText("PDF")
    assert dialog._name_preview.text() == "document_export.pdf"


def test_name_preview_drops_the_document_name_when_disabled(dialog):
    dialog._format.setCurrentText("TIFF")
    dialog._include_doc_name.setChecked(False)
    assert dialog._name_preview.text() == "page_01.tif"


OUTPUT_MODE_LABELS = ["Same folder as the PDF", "Last used folder", "Always this folder"]


def test_output_mode_offers_readable_labels_not_storage_keys(dialog):
    assert combo_items(dialog._output_mode) == OUTPUT_MODE_LABELS


def test_output_mode_saves_the_storage_key(dialog, settings):
    dialog._output_mode.setCurrentText("Always this folder")
    dialog._save()
    assert settings.get("export/output_mode") == "fixed"


def test_output_mode_starts_on_the_saved_key(qapp):
    from tests.conftest import FakeSettings

    d = SettingsDialog(FakeSettings(**{"export/output_mode": "last_used"}))
    assert d._output_mode.currentData() == "last_used"


def test_fixed_path_is_editable_only_in_fixed_mode(dialog):
    dialog._output_mode.setCurrentText("Always this folder")
    assert dialog._fixed_path.isEnabled() is True

    dialog._output_mode.setCurrentText("Last used folder")
    assert dialog._fixed_path.isEnabled() is False


def test_resetting_defaults_returns_to_the_default_output_mode(dialog):
    dialog._output_mode.setCurrentText("Always this folder")
    dialog._reset()
    assert dialog._output_mode.currentData() == "same_as_pdf"
