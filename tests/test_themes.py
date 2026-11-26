import pytest

from kaomoji_popup import themes

KDE_DARK = """\
[General]
ColorScheme=BreezeDark

[Colors:Window]
BackgroundNormal=42,46,50
ForegroundNormal=252,252,252
ForegroundInactive=161,169,177
ForegroundNegative=218,68,83

[Colors:View]
BackgroundNormal=27,30,32

[Colors:Selection]
BackgroundNormal=61,174,233
ForegroundNormal=252,252,252
"""

KDE_LIGHT = """\
[Colors:Window]
BackgroundNormal=239,240,241
ForegroundNormal=35,38,39
"""


@pytest.fixture
def kde_file(tmp_path):
    def make(text):
        path = tmp_path / "kdeglobals"
        path.write_text(text, encoding="utf-8")
        return path
    return make


# -- colour helpers -----------------------------------------------------------

def test_mix_endpoints_and_midpoint():
    assert themes.mix("#000000", "#ffffff", 0) == "#000000"
    assert themes.mix("#000000", "#ffffff", 1) == "#ffffff"
    assert themes.mix("#000000", "#ffffff", 0.5) == "#808080"


def test_is_dark():
    assert themes.is_dark("#1e1e2e")
    assert not themes.is_dark("#eff1f5")


def test_readable_on():
    assert themes.readable_on("#ffffff") == "#111111"
    assert themes.readable_on("#000000") == "#ffffff"


# -- palettes -----------------------------------------------------------------

def test_all_palettes_have_identical_keys():
    key_sets = {name: frozenset(p) for name, p in themes.PALETTES.items()}
    assert len(set(key_sets.values())) == 1, key_sets


def test_palette_values_are_hex_colours():
    for name, palette in themes.PALETTES.items():
        for key, value in palette.items():
            assert len(value) == 7 and value.startswith("#"), (name, key, value)
            int(value[1:], 16)


def test_normalize_mode():
    assert themes.normalize_mode("dark") == "dark"
    assert themes.normalize_mode("system") == "system"
    assert themes.normalize_mode("nonsense") == themes.DEFAULT_THEME
    assert themes.normalize_mode(None) == themes.DEFAULT_THEME


def test_resolve_fixed_modes_returns_copies():
    palette = themes.resolve_palette("light")
    assert palette == themes.PALETTES["light"]
    palette["base"] = "#000000"
    assert themes.PALETTES["light"]["base"] != "#000000"


def test_resolve_unknown_mode_falls_back_to_default():
    assert themes.resolve_palette("bogus") == themes.PALETTES[themes.DEFAULT_THEME]


# -- KDE ------------------------------------------------------------------------

def test_kdeglobals_dark(kde_file):
    palette = themes.palette_from_kdeglobals(kde_file(KDE_DARK))
    assert palette["base"] == "#2a2e32"
    assert palette["text"] == "#fcfcfc"
    assert palette["surface0"] == "#1b1e20"
    assert palette["mauve"] == "#3daee9"
    assert set(palette) == set(themes.PALETTES["mocha"])
    assert themes.is_dark(palette["base"])


def test_kdeglobals_light_with_missing_optional_sections(kde_file):
    palette = themes.palette_from_kdeglobals(kde_file(KDE_LIGHT))
    assert palette is not None
    assert not themes.is_dark(palette["base"])
    assert set(palette) == set(themes.PALETTES["mocha"])


def test_kdeglobals_missing_or_broken_returns_none(tmp_path, kde_file):
    assert themes.palette_from_kdeglobals(tmp_path / "does-not-exist") is None
    assert themes.palette_from_kdeglobals(kde_file("garbage without section")) is None
    assert themes.palette_from_kdeglobals(kde_file("[Colors:Window]\nBackgroundNormal=oops\n")) is None
    assert themes.palette_from_kdeglobals(kde_file("[General]\nColorScheme=x\n")) is None


def test_resolve_system_on_kde_uses_real_colours(monkeypatch, kde_file):
    path = kde_file(KDE_DARK)
    monkeypatch.setattr(themes, "_kde_session", lambda: True)
    monkeypatch.setattr(themes, "_kdeglobals_path", lambda: path)
    assert themes.resolve_palette("system")["base"] == "#2a2e32"


def test_resolve_system_on_kde_without_file_falls_back(monkeypatch, tmp_path):
    monkeypatch.setattr(themes, "_kde_session", lambda: True)
    monkeypatch.setattr(themes, "_kdeglobals_path", lambda: tmp_path / "nope")
    monkeypatch.setattr(themes, "detect_system_scheme", lambda: "light")
    assert themes.resolve_palette("system") == themes.PALETTES["light"]


def test_resolve_system_non_kde_uses_detected_scheme(monkeypatch):
    monkeypatch.setattr(themes, "_kde_session", lambda: False)
    monkeypatch.setattr(themes, "detect_system_scheme", lambda: "dark")
    assert themes.resolve_palette("system") == themes.PALETTES["dark"]


# -- GNOME/portal output parsing ------------------------------------------------

@pytest.mark.parametrize("output, expected", [
    ("(<<uint32 1>>,)", "dark"),
    ("(<<uint32 2>>,)", "light"),
    ("(<<uint32 0>>,)", None),
    ("", None),
    ("garbage", None),
])
def test_parse_portal_color_scheme(output, expected):
    assert themes.parse_portal_color_scheme(output) == expected


@pytest.mark.parametrize("output, expected", [
    ("'prefer-dark'", "dark"),
    ("'default'", "light"),
    ("'prefer-light'", "light"),
    ("", None),
])
def test_parse_gsettings_color_scheme(output, expected):
    assert themes.parse_gsettings_color_scheme(output) == expected


def test_detect_system_scheme_defaults_to_dark(monkeypatch):
    monkeypatch.setattr(themes.sys, "platform", "linux")
    monkeypatch.setattr(themes, "_detect_linux", lambda: None)
    assert themes.detect_system_scheme() == "dark"
