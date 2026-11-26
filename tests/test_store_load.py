"""Loading a broken data file must degrade gracefully, with or without a
display for the warning dialog."""
import json

from kaomoji_popup import store as store_module


def _corrupt_file(tmp_path):
    path = tmp_path / "kaomojis.json"
    path.write_text("{not valid json", encoding="utf-8")
    return path


def test_corrupt_file_shows_warning_and_starts_empty(tmp_path, store_factory, monkeypatch):
    shown = []
    monkeypatch.setattr(store_module.messagebox, "showwarning", lambda *a, **k: shown.append(a))
    store = store_factory(defaults=[], user_data_path=_corrupt_file(tmp_path))
    assert store.items == []
    assert len(shown) == 1 and "kaomojis.json" in shown[0][1]


def test_corrupt_file_survives_missing_display(tmp_path, store_factory, monkeypatch):
    def no_display(*args, **kwargs):
        raise RuntimeError("no display name and no $DISPLAY environment variable")

    monkeypatch.setattr(store_module.messagebox, "showwarning", no_display)
    store = store_factory(defaults=[], user_data_path=_corrupt_file(tmp_path))
    assert store.items == []


def test_valid_file_does_not_warn(tmp_path, store_factory, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("warning shown for a valid file")

    monkeypatch.setattr(store_module.messagebox, "showwarning", fail)
    path = tmp_path / "kaomojis.json"
    path.write_text(json.dumps({"items": [], "deleted_default_ids": []}), encoding="utf-8")
    store_factory(defaults=[], user_data_path=path)
