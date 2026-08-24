"""
Regression tests for small pure functions whose past bugs are documented in
DEV.md's "Fixed Bugs Worth Remembering" section - these exist specifically
so a future refactor can't silently reintroduce them.
"""


def test_version_tuple_orders_numerically_not_lexicographically(kp):
    # "1.10.0" > "1.9.0" is False as a plain string comparison - this is
    # the exact bug DEV.md calls out.
    assert kp._version_tuple("1.10.0") > kp._version_tuple("1.9.0")
    assert "1.10.0" < "1.9.0"  # documents *why* the tuple form is needed


def test_version_tuple_strips_non_numeric_characters_per_segment(kp):
    # _version_tuple only keeps digits within each dot-separated segment
    # (e.g. a stray "rc1" suffix), rather than failing on it.
    assert kp._version_tuple("1.2.3rc1") == (1, 2, 31)


def test_version_tuple_handles_plain_versions(kp):
    assert kp._version_tuple("1.2.3") == (1, 2, 3)
    assert kp._version_tuple("2.0.0") > kp._version_tuple("1.99.99")


def test_build_hotkey_normalizes_letters_to_lowercase(kp):
    # KEY_CHOICES holds uppercase letters for combobox display, but pynput
    # matching requires lowercase - see DEV.md "Hotkey letter case".
    hotkey = kp.build_hotkey(ctrl=True, alt=False, shift=True, key="K")
    assert hotkey == "<ctrl>+<shift>+k"


def test_build_hotkey_wraps_special_keys_in_angle_brackets(kp):
    assert kp.build_hotkey(True, False, True, "space") == "<ctrl>+<shift>+<space>"
    assert kp.build_hotkey(True, False, False, "f5") == "<ctrl>+<f5>"


def test_parse_hotkey_round_trips_with_build_hotkey(kp):
    original = kp.build_hotkey(True, True, True, "space")
    ctrl, alt, shift, key = kp.parse_hotkey(original)
    assert (ctrl, alt, shift, key) == (True, True, True, "space")


def test_format_hotkey_display_uppercases_plain_letters_only(kp):
    hotkey = kp.build_hotkey(True, False, True, "k")
    assert kp.format_hotkey_display(hotkey) == "Ctrl + Shift + K"

    space_hotkey = kp.build_hotkey(True, False, False, "space")
    assert kp.format_hotkey_display(space_hotkey) == "Ctrl + Space"