"""
Shared fixtures for the KaomojiStore test suite.

Per DEV.md's testing notes: KaomojiStore has no GUI dependency, so we can
test its logic (sync, migration, dedup, sorting) in a headless environment
by stubbing out tkinter/pynput/pyperclip before kaomoji_popup is imported,
and pointing its config dir at a throwaway temp directory.

These tests intentionally do NOT touch KaomojiPopup, EntryDialog, or any
other Tk widget class - only KaomojiStore and the small pure-function
utilities (_version_tuple, hotkey parsing) that don't need a display.
"""
import json
import os
import sys
import types
from pathlib import Path

import pytest


class _AutoAttrModule(types.ModuleType):
    """A stub module where any attribute access returns a generic,
    instantiable placeholder class instead of raising AttributeError.

    kaomoji_popup.py uses tkinter/ttk/pynput types as function annotations
    (e.g. ``def start(self, parent: tk.Toplevel, ...)``), which Python
    evaluates at *class-body execution time* since the file has no
    ``from __future__ import annotations``. A bare empty module would raise
    AttributeError the moment the module is imported. This stub makes any
    such attribute access - used as a type hint or called as a function -
    succeed harmlessly, without needing to enumerate every tkinter/pynput
    name kaomoji_popup happens to reference.
    """

    def __getattr__(self, name):
        class _Placeholder:
            def __init__(self, *args, **kwargs):
                pass

        _Placeholder.__name__ = name
        setattr(self, name, _Placeholder)  # cache so repeated access is stable
        return _Placeholder


def _stub_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    mod = _AutoAttrModule(name)
    sys.modules[name] = mod
    return mod


@pytest.fixture(scope="session", autouse=True)
def _isolated_appdata(tmp_path_factory):
    """Points the app's config dir at a throwaway temp dir for the whole
    test session, BEFORE kaomoji_popup is ever imported, so tests never
    create or touch a real user's KaomojiPopup folder or log file.

    Uses XDG_CONFIG_HOME since that's what get_appdata_dir() reads on
    Linux/CI. (On Windows this fixture would need to set APPDATA instead -
    not needed for this project's CI, which runs on Linux.)
    """
    config_dir = tmp_path_factory.mktemp("xdg_config")
    os.environ["XDG_CONFIG_HOME"] = str(config_dir)
    yield config_dir


@pytest.fixture(scope="session")
def kp(_isolated_appdata):
    tk = _stub_module("tkinter")
    _stub_module("tkinter.ttk")
    messagebox = _stub_module("tkinter.messagebox")
    tk.messagebox = messagebox
    tk.ttk = sys.modules["tkinter.ttk"]

    _stub_module("pynput")
    keyboard = _stub_module("pynput.keyboard")
    sys.modules["pynput"].keyboard = keyboard

    _stub_module("pyperclip")

    import kaomoji_popup.config as config
    from kaomoji_popup.store import KaomojiStore
    from kaomoji_popup.hotkey import (
        build_hotkey,
        parse_hotkey,
        format_hotkey_display,
    )
    from kaomoji_popup.updater import _version_tuple

    return types.SimpleNamespace(
        config=config,
        KaomojiStore=KaomojiStore,
        build_hotkey=build_hotkey,
        parse_hotkey=parse_hotkey,
        format_hotkey_display=format_hotkey_display,
        _version_tuple=_version_tuple,
    )


@pytest.fixture()
def make_default_file(tmp_path):
    """Writes a small, controlled default_kaomojis.json fixture - deliberately
    independent of the real bundled list, so tests aren't coupled to its
    exact contents - and returns its path."""

    def _make(entries):
        path = tmp_path / "default_kaomojis.json"
        path.write_text(json.dumps(entries), encoding="utf-8")
        return path

    return _make


@pytest.fixture()
def store_factory(kp, tmp_path, make_default_file, monkeypatch):

    def _factory(defaults=None, user_data_path=None):
        monkeypatch.setattr(
            kp.config,
            "DEFAULT_DATA_FILE",
            make_default_file(defaults or [])
        )

        path = user_data_path or (tmp_path / "kaomojis.json")
        return kp.KaomojiStore(path)

    return _factory


def default_entry(id_, kaomoji, desc="desc", tags=None):
    """Helper to build a well-formed default_kaomojis.json entry."""
    return {"id": id_, "kaomoji": kaomoji, "desc": desc, "tags": tags or []}