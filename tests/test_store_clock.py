"""'Recently used' ordering must not depend on the clock's resolution or
direction (Windows ticks every ~15 ms; local time can jump backwards)."""
from datetime import datetime

from kaomoji_popup import store as store_module


def _freeze(monkeypatch, *moments):
    """Makes datetime.now() inside store.py return the given moments in
    order (the last one repeats)."""
    queue = list(moments)

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return queue.pop(0) if len(queue) > 1 else queue[0]

    monkeypatch.setattr(store_module, "datetime", FakeDatetime)


def test_frozen_clock_still_orders_by_use(store_factory, monkeypatch):
    _freeze(monkeypatch, datetime(2026, 11, 26, 12, 0, 0))
    store = store_factory(defaults=[])
    store.add("a", "d", [])
    store.add("b", "d", [])
    store.mark_used(store.items[0]["id"])
    store.mark_used(store.items[1]["id"])
    assert store.recent_items(limit=1)[0]["kaomoji"] == "b"
    assert [i["kaomoji"] for i in store.recent_items()] == ["b", "a"]


def test_clock_going_backwards_still_orders_by_use(store_factory, monkeypatch):
    # e.g. DST fall-back: the second use happens at an earlier wall-clock time
    _freeze(monkeypatch, datetime(2026, 10, 25, 2, 30, 0), datetime(2026, 10, 25, 2, 10, 0))
    store = store_factory(defaults=[])
    store.add("a", "d", [])
    store.add("b", "d", [])
    store.mark_used(store.items[0]["id"])
    store.mark_used(store.items[1]["id"])
    assert store.recent_items(limit=1)[0]["kaomoji"] == "b"


def test_normal_clock_stamps_are_untouched(store_factory, monkeypatch):
    _freeze(monkeypatch, datetime(2026, 11, 26, 12, 0, 0), datetime(2026, 11, 26, 12, 5, 0))
    store = store_factory(defaults=[])
    store.add("a", "d", [])
    store.add("b", "d", [])
    store.mark_used(store.items[0]["id"])
    store.mark_used(store.items[1]["id"])
    assert store.items[1]["last_used"] == "2026-11-26T12:05:00"


def test_garbage_last_used_does_not_break_marking(store_factory):
    store = store_factory(defaults=[])
    store.add("a", "d", [])
    store.items[0]["last_used"] = "not-a-date"
    store.mark_used(store.items[0]["id"])
    assert store.items[0]["last_used"] != "not-a-date"
