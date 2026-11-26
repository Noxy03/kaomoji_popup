"""
Colour palettes and system colour-scheme detection.

Deliberately free of tkinter so it can be imported and tested headlessly
(see DEV.md). The UI layer (ui/theme.py) turns a palette into ttk styles.

Modes:
    "system" - follow the desktop. On KDE the real colours are read from
               ~/.config/kdeglobals; on other desktops only dark/light is
               detected and the built-in "dark"/"light" palette is used.
    "mocha"  - Catppuccin Mocha (the original look, default)
    "dark"   - neutral dark grey
    "light"  - Catppuccin Latte
"""
import configparser
import os
import re
import subprocess
import sys
from pathlib import Path

THEME_SYSTEM = "system"
THEME_MOCHA = "mocha"
THEME_DARK = "dark"
THEME_LIGHT = "light"

DEFAULT_THEME = THEME_MOCHA

# Display order in the settings dialog.
THEME_LABELS = {
    THEME_SYSTEM: "System",
    THEME_MOCHA: "Catppuccin Mocha",
    THEME_DARK: "Dark",
    THEME_LIGHT: "Light",
}


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb) -> str:
    r, g, b = (max(0, min(255, int(round(c)))) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def mix(color_a: str, color_b: str, amount: float) -> str:
    """Blend two '#rrggbb' colours: amount=0 -> color_a, amount=1 -> color_b."""
    a, b = _hex_to_rgb(color_a), _hex_to_rgb(color_b)
    return _rgb_to_hex(x + (y - x) * amount for x, y in zip(a, b))


def luminance(color: str) -> float:
    """Perceived brightness, 0.0 (black) .. 1.0 (white)."""
    r, g, b = _hex_to_rgb(color)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def is_dark(color: str) -> bool:
    return luminance(color) < 0.5


def readable_on(background: str) -> str:
    """Black or white, whichever is easier to read on `background`."""
    return "#111111" if luminance(background) > 0.55 else "#ffffff"


def _with_derived(palette: dict) -> dict:
    """Fills in the keys that can be computed from the others."""
    palette = dict(palette)
    palette.setdefault("on_accent", readable_on(palette["mauve"]))
    palette.setdefault("red_hover", mix(palette["red"], "#ffffff", 0.25))
    return palette


# ---------------------------------------------------------------------------
# Built-in palettes
#
# Key roles: base/mantle/crust = backgrounds (window, header, darkest),
# text/subtext0 = foregrounds, surface0-2 = fields/buttons/hover,
# mauve = accent, lavender = accent hover, on_accent = text on accent/danger
# buttons, red_hover = danger button hover.
# ---------------------------------------------------------------------------

PALETTES = {
    THEME_MOCHA: _with_derived({
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "text": "#cdd6f4", "subtext0": "#a6adc8",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "overlay0": "#6c7086",
        "red": "#f38ba8", "green": "#a6e3a1", "yellow": "#f9e2af",
        "mauve": "#cba6f7", "lavender": "#b4befe",
        "on_accent": "#11111b", "red_hover": "#f5a3bb",
    }),
    THEME_DARK: _with_derived({
        "base": "#1f1f1f", "mantle": "#181818", "crust": "#111111",
        "text": "#e4e4e4", "subtext0": "#a0a0a0",
        "surface0": "#2d2d2d", "surface1": "#3a3a3a", "surface2": "#4a4a4a",
        "overlay0": "#6e6e6e",
        "red": "#f07178", "green": "#8bd49c", "yellow": "#e5c07b",
        "mauve": "#6ea8fe", "lavender": "#9ec5fe",
        "on_accent": "#111111", "red_hover": "#f58f94",
    }),
    # Catppuccin Latte
    THEME_LIGHT: _with_derived({
        "base": "#eff1f5", "mantle": "#e6e9ef", "crust": "#dce0e8",
        "text": "#4c4f69", "subtext0": "#6c6f85",
        "surface0": "#ccd0da", "surface1": "#bcc0cc", "surface2": "#acb0be",
        "overlay0": "#9ca0b0",
        "red": "#d20f39", "green": "#40a02b", "yellow": "#df8e1d",
        "mauve": "#8839ef", "lavender": "#7287fd",
        "on_accent": "#eff1f5", "red_hover": "#e64553",
    }),
}


def normalize_mode(mode) -> str:
    """Returns `mode` if it is a known theme key, else the default."""
    return mode if mode in THEME_LABELS else DEFAULT_THEME


# ---------------------------------------------------------------------------
# KDE: real colours from kdeglobals
# ---------------------------------------------------------------------------

def _kdeglobals_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "kdeglobals"


def _kde_session() -> bool:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    return sys.platform.startswith("linux") and "KDE" in desktop


def palette_from_kdeglobals(path=None):
    """Builds a palette from the active KDE colour scheme, or returns None
    if the file is missing/unreadable or lacks the basic window colours."""
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str  # KDE keys are case-sensitive
    try:
        cp.read(path or _kdeglobals_path(), encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return None

    def color(section, key):
        try:
            parts = [int(p) for p in cp.get(section, key).split(",")]
        except (configparser.Error, ValueError):
            return None
        return _rgb_to_hex(parts[:3]) if len(parts) >= 3 else None

    window_bg = color("Colors:Window", "BackgroundNormal")
    window_fg = color("Colors:Window", "ForegroundNormal")
    if not window_bg or not window_fg:
        return None

    view_bg = color("Colors:View", "BackgroundNormal") or mix(window_bg, window_fg, 0.08)
    accent = color("Colors:Selection", "BackgroundNormal") or "#3daee9"
    on_accent = color("Colors:Selection", "ForegroundNormal") or readable_on(accent)

    return _with_derived({
        "base": window_bg,
        "mantle": mix(window_bg, "#000000", 0.08),
        "crust": mix(window_bg, "#000000", 0.16),
        "text": window_fg,
        "subtext0": color("Colors:Window", "ForegroundInactive") or mix(window_fg, window_bg, 0.35),
        "surface0": view_bg,
        "surface1": mix(view_bg, window_fg, 0.10),
        "surface2": mix(view_bg, window_fg, 0.20),
        "overlay0": mix(window_bg, window_fg, 0.45),
        "red": color("Colors:Window", "ForegroundNegative") or "#da4453",
        "green": color("Colors:Window", "ForegroundPositive") or "#27ae60",
        "yellow": color("Colors:Window", "ForegroundNeutral") or "#f67400",
        "mauve": accent,
        "lavender": mix(accent, "#ffffff", 0.25),
        "on_accent": on_accent,
    })


# ---------------------------------------------------------------------------
# Dark/light detection for everything that is not KDE
# ---------------------------------------------------------------------------

def _run(cmd) -> str:
    """Runs a short helper command; '' on any failure (missing tool, timeout...)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


_PORTAL_RE = re.compile(r"uint32\s+(\d+)")


def parse_portal_color_scheme(output: str):
    """xdg-desktop-portal 'color-scheme': 1 = prefer dark, 2 = prefer light,
    0 = no preference (-> None)."""
    match = _PORTAL_RE.search(output or "")
    if not match:
        return None
    return {"1": "dark", "2": "light"}.get(match.group(1))


def parse_gsettings_color_scheme(output: str):
    value = (output or "").strip().strip("'\"").lower()
    if "dark" in value:
        return "dark"
    if value in ("default", "prefer-light"):
        return "light"
    return None


def _detect_windows():
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value else "dark"
    except (ImportError, OSError):
        return None


def _detect_macos():
    return "dark" if _run(["defaults", "read", "-g", "AppleInterfaceStyle"]).lower() == "dark" else "light"


def _detect_linux():
    if _kde_session():
        palette = palette_from_kdeglobals()
        if palette:
            return "dark" if is_dark(palette["base"]) else "light"

    scheme = parse_portal_color_scheme(_run([
        "gdbus", "call", "--session",
        "--dest", "org.freedesktop.portal.Desktop",
        "--object-path", "/org/freedesktop/portal/desktop",
        "--method", "org.freedesktop.portal.Settings.Read",
        "org.freedesktop.appearance", "color-scheme",
    ]))
    if scheme:
        return scheme

    scheme = parse_gsettings_color_scheme(
        _run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"]))
    if scheme:
        return scheme

    gtk_theme = _run(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]).lower()
    if gtk_theme:
        return "dark" if "dark" in gtk_theme else "light"
    return None


def detect_system_scheme() -> str:
    """'dark' or 'light'. Falls back to 'dark' if nothing can be detected."""
    if sys.platform.startswith("win"):
        scheme = _detect_windows()
    elif sys.platform == "darwin":
        scheme = _detect_macos()
    else:
        scheme = _detect_linux()
    return scheme or THEME_DARK


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def resolve_palette(mode) -> dict:
    """Returns a fresh palette dict for `mode` (including "system")."""
    mode = normalize_mode(mode)
    if mode == THEME_SYSTEM:
        if _kde_session():
            palette = palette_from_kdeglobals()
            if palette:
                return palette
        mode = detect_system_scheme()
    return dict(PALETTES[mode])
