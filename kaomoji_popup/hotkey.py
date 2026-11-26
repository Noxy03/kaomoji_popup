"""
Hotkey: persistence, parsing, live re-registration.
"""
from pynput import keyboard

from . import settings

HOTKEY = "<ctrl>+<shift>+<space>"
KEY_CHOICES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + [f"f{i}" for i in range(1, 13)] + ["space"]


def load_hotkey():
    hk = settings.load_settings().get("hotkey")
    return hk if isinstance(hk, str) and hk else HOTKEY


def save_hotkey(hotkey_str: str):
    settings.update_settings(hotkey=hotkey_str)


def parse_hotkey(hotkey_str: str):
    ctrl = alt = shift = False
    key = ""
    for part in hotkey_str.split("+"):
        token = part.strip().strip("<>").lower()
        if token == "ctrl":
            ctrl = True
        elif token == "alt":
            alt = True
        elif token == "shift":
            shift = True
        elif token:
            key = token
    return ctrl, alt, shift, key


def build_hotkey(ctrl: bool, alt: bool, shift: bool, key: str) -> str:
    parts = []
    if ctrl:
        parts.append("<ctrl>")
    if alt:
        parts.append("<alt>")
    if shift:
        parts.append("<shift>")
    if key:
        key = key.lower()  # pynput treats "K" and "k" as different key codes;
        # always normalize plain letters to lowercase.
        # F-keys and "space" must be enclosed in <...>
        if (key.startswith("f") and key[1:].isdigit()) or key == "space":
            parts.append(f"<{key}>")
        else:
            parts.append(key)
    return "+".join(parts)


def format_hotkey_display(hotkey_str: str) -> str:
    ctrl, alt, shift, key = parse_hotkey(hotkey_str)
    labels = []
    if ctrl:
        labels.append("Ctrl")
    if alt:
        labels.append("Alt")
    if shift:
        labels.append("Shift")
    if key:
        labels.append("Space" if key == "space" else key.upper())
    return " + ".join(labels) if labels else "(none)"


class HotkeyManager:
    """Starts/stops the global hotkey listener and allows changing it
    at runtime without restarting the application."""

    def __init__(self, on_trigger):
        self.on_trigger = on_trigger
        self.listener = None
        self.current = None

    def start(self, hotkey_str: str):
        self.stop()
        new_listener = keyboard.GlobalHotKeys({hotkey_str: self.on_trigger})
        new_listener.daemon = True
        new_listener.start()
        self.listener = new_listener
        self.current = hotkey_str

    def stop(self):
        if self.listener is not None:
            self.listener.stop()
            self.listener = None