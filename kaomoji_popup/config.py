
"""
Central application configuration.
"""

import os
import sys
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

CURRENT_VERSION = "1.0.2"
GITHUB_REPO = "Noxy03/kaomoji_popup"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

APP_NAME = "kaomoji_popup"

def _get_config_dir() -> Path:
    if os.name == "nt" or sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / APP_NAME

def _get_default_data_file() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        for candidate in (
                meipass / "default_kaomojis.json",
                meipass / "kaomoji_popup" / "resources" / "default_kaomojis.json",
        ):
            if candidate.exists():
                return candidate
    return Path(__file__).parent / "resources" / "default_kaomojis.json"

# Linux configuration directory: ~/.config/kaomoji_popup/
CONFIG_DIR = _get_config_dir()

USER_DATA_FILE = CONFIG_DIR / "kaomojis.json"
USER_SETTINGS_FILE = CONFIG_DIR / "settings.json"

# Bundled default data
DEFAULT_DATA_FILE = _get_default_data_file()

# ---------------------------------------------------------------------------
# Recent entries
# ---------------------------------------------------------------------------

RECENT_LIMIT = 20
RECENT_STAR_COUNT = 5
RECENT_TAG_LABEL = "⭐ Recently Used"

# ---------------------------------------------------------------------------
# Insertion
# ---------------------------------------------------------------------------

# Supported: "paste", "type", "clipboard"
INSERT_MODE = "paste"

# Delay before inserting after the popup closes (milliseconds)
INSERT_DELAY_MS = 100

# Delay before restoring the previous clipboard contents (milliseconds)
CLIPBOARD_RESTORE_DELAY_MS = 500

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FILE = CONFIG_DIR / "kaomoji_popup.log"

logger = logging.getLogger(APP_NAME)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Falls das Config-Verzeichnis gerade nicht beschreibbar ist,
        # zumindest einen StreamHandler verwenden.
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARNING)
        logger.addHandler(stream_handler)
