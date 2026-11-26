from kaomoji_popup import monitors

XRANDR_TWO = """\
Monitors: 2
 0: +*DP-1 2560/597x1440/336+0+0  DP-1
 1: +HDMI-1 1920/527x1080/296+2560+180  HDMI-1
"""

LEFT = (0, 0, 2560, 1440)
RIGHT = (2560, 180, 1920, 1080)


def test_parse_xrandr_listmonitors():
    assert monitors.parse_xrandr_listmonitors(XRANDR_TWO) == [LEFT, RIGHT]


def test_parse_handles_negative_offsets_and_garbage():
    text = "Monitors: 1\n 0: +*eDP-1 1920/344x1080/194+-1920+-100  eDP-1\nnot a monitor line\n"
    assert monitors.parse_xrandr_listmonitors(text) == [(-1920, -100, 1920, 1080)]
    assert monitors.parse_xrandr_listmonitors("") == []
    assert monitors.parse_xrandr_listmonitors(None) == []


def test_pick_monitor_containing_point():
    rects = [LEFT, RIGHT]
    assert monitors.pick_monitor(100, 100, rects) == LEFT
    assert monitors.pick_monitor(2560, 180, rects) == RIGHT      # first pixel of RIGHT
    assert monitors.pick_monitor(2559, 500, rects) == LEFT       # last pixel of LEFT


def test_pick_monitor_nearest_when_in_a_gap():
    # y=50 is above RIGHT (starts at y=180) but x is inside it -> RIGHT is nearest
    assert monitors.pick_monitor(3000, 50, [LEFT, RIGHT]) == RIGHT


def test_pick_monitor_without_monitors():
    assert monitors.pick_monitor(10, 10, []) is None


def test_monitor_for_point_falls_back(monkeypatch):
    monkeypatch.setattr(monitors, "list_monitors", lambda: [])
    assert monitors.monitor_for_point(5, 5, fallback=(0, 0, 800, 600)) == (0, 0, 800, 600)
    monkeypatch.setattr(monitors, "list_monitors", lambda: [LEFT, RIGHT])
    assert monitors.monitor_for_point(3000, 500, fallback=(0, 0, 1, 1)) == RIGHT


def test_pick_monitor_prefers_smallest_overlapping_rect():
    combined = (0, 0, 4480, 1440)
    assert monitors.pick_monitor(100, 100, [combined, LEFT, RIGHT]) == LEFT
    assert monitors.pick_monitor(100, 100, [LEFT, RIGHT, combined]) == LEFT
