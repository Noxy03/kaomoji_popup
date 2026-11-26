"""
Monitor geometry lookup, so the popup can open on the screen the mouse
cursor is on (tkinter alone only reports the size of the whole virtual
desktop on multi-monitor setups).

tkinter-free and best-effort: every function degrades to "no information"
([] / None) and the caller falls back to the full Tk screen size.

    Linux    - `xrandr --listmonitors` (works under X11 and XWayland)
    Windows  - EnumDisplayMonitors via ctypes (work area, i.e. without taskbar)
    other    - no information
"""
import re
import subprocess
import sys

# "0: +*DP-1 1920/527x1080/296+0+0  DP-1"  ->  w=1920 h=1080 x=0 y=0
_XRANDR_RE = re.compile(r"(\d+)/\d+x(\d+)/\d+\+(-?\d+)\+(-?\d+)")


def parse_xrandr_listmonitors(text: str):
    """Returns a list of (x, y, width, height) from `xrandr --listmonitors`."""
    rects = []
    for line in (text or "").splitlines():
        match = _XRANDR_RE.search(line)
        if match:
            w, h, x, y = (int(g) for g in match.groups())
            rects.append((x, y, w, h))
    return rects


def pick_monitor(x: int, y: int, rects):
    """The rect containing the point, else the nearest one, else None."""
    best, best_key = None, None
    for rx, ry, rw, rh in rects:
        dx = max(rx - x, 0, x - (rx + rw - 1))
        dy = max(ry - y, 0, y - (ry + rh - 1))
        # Nearest first; among equals the smallest area, so a combined
        # "whole desktop" entry never beats the real monitor inside it.
        key = (dx * dx + dy * dy, rw * rh)
        if best_key is None or key < best_key:
            best, best_key = (rx, ry, rw, rh), key
    return best


def _linux_monitors():
    try:
        result = subprocess.run(["xrandr", "--listmonitors"], capture_output=True,
                                text=True, timeout=1.5, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    return parse_xrandr_listmonitors(result.stdout) if result.returncode == 0 else []


def _windows_monitors():
    try:
        import ctypes
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

        user32 = ctypes.windll.user32
        rects = []

        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.POINTER(wintypes.RECT), ctypes.c_void_p)
        def callback(hmonitor, hdc, lprect, lparam):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(ctypes.c_void_p(hmonitor), ctypes.byref(info)):
                r = info.rcWork
                rects.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
            return 1

        user32.EnumDisplayMonitors(None, None, callback, 0)
        return rects
    except Exception:
        return []


def list_monitors():
    if sys.platform.startswith("win"):
        return _windows_monitors()
    if sys.platform.startswith("linux"):
        return _linux_monitors()
    return []


def monitor_for_point(x: int, y: int, fallback):
    """(x, y, w, h) of the monitor under (x, y); `fallback` if unknown."""
    return pick_monitor(x, y, list_monitors()) or fallback
