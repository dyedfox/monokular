import os

import main


def test_the_icon_path_is_absolute_or_absent():
    assert main.ICON_PATH == "" or os.path.isabs(main.ICON_PATH)


def test_a_stray_assets_folder_in_the_working_directory_is_ignored(tmp_path, monkeypatch):
    decoy = tmp_path / "assets"
    decoy.mkdir()
    (decoy / "icon.svg").write_text("<svg/>")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr("sys._MEIPASS", raising=False)

    assert os.path.abspath(main._find_icon()) != str(decoy / "icon.svg")
