import os
import xml.etree.ElementTree as ET

import pytest
from PyQt6.QtCore import QTranslator

from app import i18n

# The set shipped by Dyedfox Radio, which Monokular deliberately matches.
EXPECTED = [
    "bg", "ca", "cs", "da", "de", "el", "es", "et", "fi", "fr", "hr", "hu",
    "it", "lt", "lv", "nb", "nl", "pl", "pt", "ro", "sk", "sl", "sr", "sv", "uk",
]


def ts_path(lang):
    return os.path.join(i18n.translations_dir(), f"monokular_{lang}.ts")


def qm_path(lang):
    return os.path.join(i18n.translations_dir(), f"monokular_{lang}.qm")


def messages(lang):
    for context in ET.parse(ts_path(lang)).getroot().iter("context"):
        name = context.findtext("name")
        for message in context.iter("message"):
            yield name, message


def test_the_language_list_matches_dyedfox_radio():
    assert i18n.LANGUAGES == EXPECTED


def test_translations_live_beside_the_source_in_a_checkout():
    assert os.path.isdir(i18n.translations_dir())


@pytest.mark.parametrize("lang", EXPECTED)
def test_every_language_has_a_source_catalogue(lang):
    assert os.path.isfile(ts_path(lang))


@pytest.mark.parametrize("lang", EXPECTED)
def test_every_language_has_a_compiled_catalogue(lang):
    assert os.path.getsize(qm_path(lang)) > 0


@pytest.mark.parametrize("lang", EXPECTED)
def test_no_catalogue_has_unfinished_entries(lang):
    unfinished = [
        m.findtext("source")
        for _, m in messages(lang)
        if (m.find("translation") is not None
            and m.find("translation").get("type") == "unfinished")
    ]
    assert unfinished == []


@pytest.mark.parametrize("lang", EXPECTED)
def test_every_message_is_actually_translated(lang):
    empty = []
    for _, message in messages(lang):
        translation = message.find("translation")
        forms = [n.text for n in translation.iter("numerusform")]
        if forms:
            if not all(f and f.strip() for f in forms):
                empty.append(message.findtext("source"))
        elif not (translation.text or "").strip():
            empty.append(message.findtext("source"))
    assert empty == []


@pytest.mark.parametrize("lang", ["uk", "pl", "cs", "sk", "sr", "hr", "lt", "ru"][:8])
def test_languages_with_extra_plural_forms_have_them(lang):
    if lang not in EXPECTED:
        pytest.skip(f"{lang} is not shipped")
    plural_counts = {
        len([n for n in m.find("translation").iter("numerusform")])
        for _, m in messages(lang)
        if m.get("numerus") == "yes"
    }
    assert plural_counts and min(plural_counts) >= 3


def test_a_regional_locale_falls_back_to_its_base_language(qapp):
    translator = QTranslator()
    assert translator.load("monokular_de_DE", i18n.translations_dir()) is True


def test_an_unsupported_locale_loads_nothing(qapp):
    translator = QTranslator()
    assert translator.load("monokular_zz_ZZ", i18n.translations_dir()) is False


def test_installing_a_translator_reports_the_language_it_used(qapp):
    assert i18n.install_translator(qapp, "uk_UA") == "uk"


def test_installing_a_translator_for_an_unknown_locale_reports_nothing(qapp):
    assert i18n.install_translator(qapp, "zz_ZZ") is None


def test_the_compiler_accepts_every_catalogue_without_warnings():
    """lrelease warns when a catalogue's plural-form count is wrong for its language."""
    import shutil
    import subprocess

    lrelease = shutil.which("lrelease6") or shutil.which("lrelease")
    if not lrelease:
        pytest.skip("lrelease is not installed (qt6-tools)")

    complaints = []
    for lang in EXPECTED:
        result = subprocess.run(
            [lrelease, ts_path(lang), "-qm", os.path.join("/tmp", f"check_{lang}.qm")],
            capture_output=True, text=True,
        )
        noise = (result.stderr or "").strip()
        if noise:
            complaints.append(f"{lang}: {noise.splitlines()[0]}")
    assert complaints == []


def test_the_catalogue_path_is_absolute():
    assert os.path.isabs(i18n.translations_dir())


def test_a_stray_translations_folder_in_the_working_directory_is_ignored(tmp_path, monkeypatch):
    """Outside a PyInstaller bundle nothing may resolve against the cwd."""
    decoy = tmp_path / "translations"
    decoy.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr("sys._MEIPASS", raising=False)

    assert i18n.translations_dir() != str(decoy)
    assert os.path.isfile(os.path.join(i18n.translations_dir(), "monokular_uk.qm"))


def test_the_package_build_compiles_catalogues_from_source():
    """The Arch package must regenerate .qm from .ts, not ship stale ones."""
    pkgbuild = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PKGBUILD"
    )
    with open(pkgbuild) as fh:
        text = fh.read()

    assert "qt6-tools" in text, "qt6-tools must be a makedepend for lrelease6"
    assert "lrelease6" in text, "build() must compile the catalogues"
    assert "translations/*.ts" in text, "build() must read the .ts sources"
    assert "/translations" in text, "package() must install the catalogues"
