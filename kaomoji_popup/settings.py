"""
settings.json: small key/value store for user settings (hotkey, theme).

All writers go through update_settings(), which merges into the existing
file - so saving one setting never wipes the others.
"""
import json

from . import config
from .themes import normalize_mode


def load_settings() -> dict:
    try:
        with open(config.USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def update_settings(**changes) -> None:
    data = load_settings()
    data.update(changes)
    config.USER_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_theme_mode() -> str:
    return normalize_mode(load_settings().get("theme"))


def save_theme_mode(mode: str) -> None:
    update_settings(theme=normalize_mode(mode))


# -- window position ---------------------------------------------------------

POSITION_CURSOR = "cursor"
POSITION_CENTER = "center"
DEFAULT_POSITION = POSITION_CURSOR

# Display order in the settings dialog.
POSITION_LABELS = {
    POSITION_CURSOR: "Near cursor",
    POSITION_CENTER: "Center of screen",
}


def normalize_position(value) -> str:
    return value if value in POSITION_LABELS else DEFAULT_POSITION


def load_popup_position() -> str:
    return normalize_position(load_settings().get("popup_position"))


def save_popup_position(value: str) -> None:
    update_settings(popup_position=normalize_position(value))
