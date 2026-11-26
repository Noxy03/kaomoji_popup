"""
Tests for KaomojiStore - the default-list sync/tombstone system, legacy
migration, CRUD, and the recent-first ordering logic described in DEV.md.
"""
import json

import pytest

from conftest import default_entry


# ---------------------------------------------------------------------------
# Fresh install / legacy migration
# ---------------------------------------------------------------------------

def test_fresh_install_seeds_from_defaults(store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy", ["joy"])]
    store = store_factory(defaults=defaults)

    assert [i["kaomoji"] for i in store.items] == ["(^_^)"]
    assert store.items[0]["id"] == "d_a"
    assert store.items[0]["origin"] == "default"
    assert store.deleted_default_ids == []


def test_legacy_flat_list_is_migrated_and_matched_by_text(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy", ["joy"])]
    user_file = tmp_path / "kaomojis.json"
    # Old pre-id format: a bare list, one entry matching a default by text,
    # one entry that is genuinely user-created.
    user_file.write_text(
        json.dumps([
            {"kaomoji": "(^_^)", "desc": "happy"},
            {"kaomoji": "(??_??)", "desc": "my own face"},
        ]),
        encoding="utf-8",
    )

    store = store_factory(defaults=defaults, user_data_path=user_file)
    by_text = {i["kaomoji"]: i for i in store.items}

    assert by_text["(^_^)"]["id"] == "d_a"
    assert by_text["(^_^)"]["origin"] == "default"
    assert by_text["(??_??)"]["origin"] == "user"
    assert by_text["(??_??)"]["id"].startswith("u_")


def test_current_format_items_missing_id_are_migrated(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy", ["joy"])]
    user_file = tmp_path / "kaomojis.json"
    user_file.write_text(
        json.dumps({
            "items": [{"kaomoji": "(^_^)", "desc": "happy"}],
            "deleted_default_ids": [],
        }),
        encoding="utf-8",
    )

    store = store_factory(defaults=defaults, user_data_path=user_file)

    assert store.items[0]["id"] == "d_a"
    assert store.items[0]["origin"] == "default"


def test_corrupted_json_falls_back_to_defaults_without_crashing(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy")]
    user_file = tmp_path / "kaomojis.json"
    user_file.write_text("{not valid json", encoding="utf-8")

    store = store_factory(defaults=defaults, user_data_path=user_file)

    assert [i["kaomoji"] for i in store.items] == ["(^_^)"]


# ---------------------------------------------------------------------------
# sync_with_defaults - the tombstone algorithm (see DEV.md "Sync algorithm")
# ---------------------------------------------------------------------------

def test_sync_skips_tombstoned_id(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy")]
    user_file = tmp_path / "kaomojis.json"
    user_file.write_text(
        json.dumps({"items": [], "deleted_default_ids": ["d_a"]}),
        encoding="utf-8",
    )

    store = store_factory(defaults=defaults, user_data_path=user_file)

    assert store.items == []
    assert store.deleted_default_ids == ["d_a"]


def test_sync_skips_id_already_present_preserving_user_edits(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy", ["joy"])]
    user_file = tmp_path / "kaomojis.json"
    # User already has this id, but has edited the description/tags and
    # used it - sync must not touch it.
    user_file.write_text(
        json.dumps({
            "items": [{
                "id": "d_a", "origin": "default", "kaomoji": "(^_^)",
                "desc": "my custom desc", "tags": ["custom"],
                "last_used": "2026-01-01T00:00:00", "use_count": 5,
            }],
            "deleted_default_ids": [],
        }),
        encoding="utf-8",
    )

    store = store_factory(defaults=defaults, user_data_path=user_file)

    assert len(store.items) == 1
    assert store.items[0]["desc"] == "my custom desc"
    assert store.items[0]["use_count"] == 5


def test_sync_skips_matching_text_under_different_id(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy")]
    user_file = tmp_path / "kaomojis.json"
    user_file.write_text(
        json.dumps({
            "items": [{
                "id": "u_existing", "origin": "user", "kaomoji": "(^_^)",
                "desc": "same face, different id", "tags": [],
                "last_used": None, "use_count": 0,
            }],
            "deleted_default_ids": [],
        }),
        encoding="utf-8",
    )

    store = store_factory(defaults=defaults, user_data_path=user_file)

    # No visual duplicate: the default is not appended.
    assert len(store.items) == 1
    assert store.items[0]["id"] == "u_existing"


def test_sync_appends_genuinely_new_default(kp, tmp_path, store_factory):
    defaults = [
        default_entry("d_a", "(^_^)", "happy"),
        default_entry("d_b", "(T_T)", "sad"),
    ]
    user_file = tmp_path / "kaomojis.json"
    user_file.write_text(
        json.dumps({
            "items": [{
                "id": "d_a", "origin": "default", "kaomoji": "(^_^)",
                "desc": "happy", "tags": [], "last_used": None, "use_count": 0,
            }],
            "deleted_default_ids": [],
        }),
        encoding="utf-8",
    )

    store = store_factory(defaults=defaults, user_data_path=user_file)

    new_item = next(i for i in store.items if i["id"] == "d_b")
    assert new_item["last_used"] is None
    assert new_item["use_count"] == 0
    assert new_item["origin"] == "default"


def test_sync_persists_newly_added_defaults_to_disk(kp, tmp_path, store_factory):
    # Note: a *fresh* install (no kaomojis.json yet) loads straight from
    # defaults and writes nothing to disk until sync finds something
    # genuinely new to add, or a mutation (add/delete/mark_used) happens -
    # so this test exercises an *existing* user file that predates a new
    # default release, which is the case that actually calls save().
    defaults = [
        default_entry("d_a", "(^_^)", "happy"),
        default_entry("d_b", "(T_T)", "sad"),
    ]
    user_file = tmp_path / "kaomojis.json"
    user_file.write_text(
        json.dumps({
            "items": [{
                "id": "d_a", "origin": "default", "kaomoji": "(^_^)",
                "desc": "happy", "tags": [], "last_used": None, "use_count": 0,
            }],
            "deleted_default_ids": [],
        }),
        encoding="utf-8",
    )

    store_factory(defaults=defaults, user_data_path=user_file)

    on_disk = json.loads(user_file.read_text(encoding="utf-8"))
    assert {i["id"] for i in on_disk["items"]} == {"d_a", "d_b"}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def test_add_creates_user_item_and_persists(kp, tmp_path, store_factory):
    user_file = tmp_path / "kaomojis.json"
    store = store_factory(defaults=[], user_data_path=user_file)

    store.add("(o_O)", "confused", ["shrug"])

    assert any(i["kaomoji"] == "(o_O)" and i["origin"] == "user" for i in store.items)
    reloaded = kp.KaomojiStore(user_file)
    assert any(i["kaomoji"] == "(o_O)" for i in reloaded.items)


def test_add_duplicate_kaomoji_text_raises(store_factory):
    store = store_factory(defaults=[])
    store.add("(o_O)", "confused", [])

    with pytest.raises(ValueError):
        store.add("(o_O)", "duplicate", [])


def test_exists_is_case_sensitive(store_factory):
    store = store_factory(defaults=[])
    store.add("ABC", "shout", [])

    assert store.exists("ABC") is True
    assert store.exists("abc") is False


def test_exists_excludes_given_id_for_self_edit(store_factory):
    store = store_factory(defaults=[])
    store.add("ABC", "shout", [])
    item_id = store.items[0]["id"]

    # Editing the item to keep its own text shouldn't look like a collision.
    assert store.exists("ABC", exclude_id=item_id) is False
    assert store.exists("ABC", exclude_id="some_other_id") is True


def test_delete_default_item_adds_tombstone(kp, tmp_path, store_factory):
    defaults = [default_entry("d_a", "(^_^)", "happy")]
    user_file = tmp_path / "kaomojis.json"
    store = store_factory(defaults=defaults, user_data_path=user_file)

    store.delete("d_a")

    assert store.items == []
    assert "d_a" in store.deleted_default_ids

    # A fresh sync (e.g. on next app start) must not resurrect it.
    reloaded = kp.KaomojiStore(user_file)
    assert reloaded.items == []
    assert "d_a" in reloaded.deleted_default_ids


def test_delete_user_item_does_not_tombstone(store_factory):
    store = store_factory(defaults=[])
    store.add("(o_O)", "confused", [])
    item_id = store.items[0]["id"]

    store.delete(item_id)

    assert store.items == []
    assert store.deleted_default_ids == []


def test_delete_unknown_id_is_a_no_op(store_factory):
    store = store_factory(defaults=[])
    store.add("(o_O)", "confused", [])

    store.delete("does_not_exist")

    assert len(store.items) == 1


def test_mark_used_sets_timestamp_and_increments_use_count(store_factory):
    store = store_factory(defaults=[])
    store.add("(o_O)", "confused", [])
    item_id = store.items[0]["id"]

    store.mark_used(item_id)
    assert store.items[0]["last_used"] is not None
    assert store.items[0]["use_count"] == 1

    store.mark_used(item_id)
    assert store.items[0]["use_count"] == 2


def test_all_tags_returns_sorted_unique_tags(store_factory):
    store = store_factory(defaults=[])
    store.add("a", "d1", ["joy", "cat"])
    store.add("b", "d2", ["anger", "cat"])

    assert store.all_tags() == ["anger", "cat", "joy"]


# ---------------------------------------------------------------------------
# Ordering: recent-first, non-mutating (see DEV.md "Stale Recently Used")
# ---------------------------------------------------------------------------

def test_ordered_items_puts_recently_used_first_without_mutating_storage_order(store_factory):
    store = store_factory(defaults=[])
    store.add("a", "first added", [])
    store.add("b", "second added", [])
    b_id = store.items[1]["id"]

    storage_order_before = [i["kaomoji"] for i in store.items]
    ordered = store.ordered_items()

    assert ordered[0]["kaomoji"] == "a"  # nothing used yet -> alpha by desc
    store.mark_used(b_id)

    ordered_after_use = store.ordered_items()
    assert ordered_after_use[0]["kaomoji"] == "b"
    # Crucially: self.items (storage order) must be untouched by
    # ordered_items() - this is the fix for the "stale order until
    # restart" bug.
    assert [i["kaomoji"] for i in store.items] == storage_order_before


def test_ordered_items_respects_recent_limit(store_factory):
    store = store_factory(defaults=[])
    for i in range(5):
        store.add(f"k{i}", f"desc{i}", [])
        store.mark_used(store.items[-1]["id"])

    ordered = store.ordered_items(recent_limit=2)
    recent_slice_ids = {i["id"] for i in ordered[:2]}

    # Only the 2 most recently used should occupy the "recent" head slots.
    most_recently_used_ids = {i["id"] for i in store.items[-2:]}
    assert recent_slice_ids == most_recently_used_ids


def test_recent_items_sorted_descending_and_limited(store_factory):
    store = store_factory(defaults=[])
    store.add("a", "d", [])
    store.add("b", "d", [])
    store.mark_used(store.items[0]["id"])
    store.mark_used(store.items[1]["id"])  # used after "a" -> most recent

    recent = store.recent_items(limit=1)

    assert len(recent) == 1
    assert recent[0]["kaomoji"] == "b"


def test_recent_items_excludes_never_used(store_factory):
    store = store_factory(defaults=[])
    store.add("a", "d", [])
    store.add("b", "d", [])
    store.mark_used(store.items[0]["id"])

    recent = store.recent_items()

    assert [i["kaomoji"] for i in recent] == ["a"]