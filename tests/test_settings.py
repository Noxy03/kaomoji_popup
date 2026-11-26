import json

import pytest

from kaomoji_popup import config, hotkey, settings


@pytest.fixture(autouse=True)
def temp_settings_file(tmp_path, monkeypatch):
    path = tmp_path / "cfg" / "settings.json"
    monkeypatch.setattr(config, "USER_SETTINGS_FILE", path)
    return path


def test_defaults_when_file_missing():
    assert settings.load_settings() == {}
    assert settings.load_theme_mode() == "mocha"
    assert hotkey.load_hotkey() == hotkey.HOTKEY


def test_saving_theme_keeps_hotkey_and_vice_versa():
    hotkey.save_hotkey("<ctrl>+<alt>+k")
    settings.save_theme_mode("dark")
    assert hotkey.load_hotkey() == "<ctrl>+<alt>+k"
    assert settings.load_theme_mode() == "dark"

    hotkey.save_hotkey("<ctrl>+<shift>+<space>")
    assert settings.load_theme_mode() == "dark"


def test_legacy_settings_file_with_only_hotkey(temp_settings_file):
    temp_settings_file.parent.mkdir(parents=True)
    temp_settings_file.write_text(json.dumps({"hotkey": "<ctrl>+k"}), encoding="utf-8")
    assert hotkey.load_hotkey() == "<ctrl>+k"
    assert settings.load_theme_mode() == "mocha"


@pytest.mark.parametrize("content", ["{broken", "[1, 2]", '"text"'])
def test_corrupt_or_wrong_shape_file_is_ignored(temp_settings_file, content):
    temp_settings_file.parent.mkdir(parents=True)
    temp_settings_file.write_text(content, encoding="utf-8")
    assert settings.load_settings() == {}
    assert hotkey.load_hotkey() == hotkey.HOTKEY


def test_unknown_theme_value_falls_back(temp_settings_file):
    settings.update_settings(theme="neon-pink")
    assert settings.load_theme_mode() == "mocha"
    settings.save_theme_mode("also-bogus")
    assert settings.load_settings()["theme"] == "mocha"
