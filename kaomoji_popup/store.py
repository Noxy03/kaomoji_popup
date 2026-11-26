"""
KaomojiStore: owns all data - loading, migration, the default-list
sync/tombstone system, sorting, and persistence.
"""
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox

from . import config


class KaomojiStore:
    """
    Data model per item:
        {
            "id": "d_xxxxxxxx" | "u_xxxxxxxx",  # stable, never reused/reassigned
            "origin": "default" | "user",
            "kaomoji": "...", "desc": "...", "tags": [...],
            "last_used": iso-string | None, "use_count": int,
        }

    On-disk file (kaomojis.json):
        {
            "items": [ ...items... ],
            "deleted_default_ids": ["d_xxxx", ...]   # tombstones
        }

    Sync rule with default_kaomojis.json (run once at startup):
      - default id in deleted_default_ids       -> skip (user deleted it on purpose)
      - default id already present in items     -> skip (already synced, don't
                                                    touch it - preserves user
                                                    edits / last_used / use_count)
      - default kaomoji TEXT already present    -> skip (avoids visual dupes,
                                                    e.g. user already created
                                                    the exact same face)
      - otherwise                               -> append as a brand-new item
                                                    (last_used=None, so it
                                                    doesn't affect "Recently Used")
    """

    def __init__(self, path: Path):
        self.path = path
        self.items, self.deleted_default_ids = self._load()
        self.sync_with_defaults()
        self.sort_items()

    # -- loading / migration -------------------------------------------------

    def _load(self):
        raw = None
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, OSError):
                messagebox.showwarning(
                    "Kaomoji Popup",
                    f"Could not read {self.path.name}. Starting with default list.",
                )

        if raw is None:
            # Fresh install: seed straight from the bundled defaults.
            items = self._load_default_items()
            return items, []

        if isinstance(raw, list):
            # Legacy format (plain list, no ids/origin/tombstones yet) -> migrate.
            items = self._migrate_legacy_items(raw)
            return items, []

        # Current format: {"items": [...], "deleted_default_ids": [...]}
        items = raw.get("items", [])
        deleted_ids = raw.get("deleted_default_ids", [])
        # Defensive: fill in ids/origin for any item that somehow lacks them
        # (e.g. manually edited JSON).
        items = self._migrate_legacy_items(items)
        return items, deleted_ids

    def _migrate_legacy_items(self, items: list) -> list:
        """Assigns id/origin to items that don't have them yet, matching
        against the bundled defaults by kaomoji text where possible so
        existing installations plug into the tombstone system correctly."""
        default_by_text = {d["kaomoji"]: d for d in self._load_default_items()}
        for item in items:
            item.setdefault("last_used", None)
            item.setdefault("use_count", 0)
            if "id" in item and "origin" in item:
                continue
            match = default_by_text.get(item.get("kaomoji"))
            if match is not None:
                item["id"] = match["id"]
                item["origin"] = "default"
            else:
                item["id"] = f"u_{uuid.uuid4().hex[:10]}"
                item["origin"] = "user"
        return items

    def _load_default_items(self) -> list:
        if not config.DEFAULT_DATA_FILE.exists():
            return []
        try:
            with open(config.DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

        # Defensive fallback: if an entry in default_kaomojis.json is missing
        # an "id" (dev forgot to run the id-assignment step), derive a
        # deterministic one from its text so sync still works within this
        # release. Prefer running assign_default_ids.py instead - a
        # text-derived id changes if the text is later edited/typo-fixed,
        # which would make the tombstone system treat it as a "new" entry.
        for entry in data:
            entry.setdefault("tags", [])
            entry.setdefault("desc", "")
            if not entry.get("id"):
                entry["id"] = "d_" + uuid.uuid5(uuid.NAMESPACE_URL, entry["kaomoji"]).hex[:10]
            entry["origin"] = "default"
        return data

    # -- sync ------------------------------------------------------------

    def sync_with_defaults(self):
        """Adds newly-released default kaomojis the user doesn't have yet,
        without resurrecting ones they deleted or duplicating ones they
        already have. Safe to call every startup."""
        defaults = self._load_default_items()
        existing_ids = {i["id"] for i in self.items}
        existing_texts = {i["kaomoji"] for i in self.items}
        deleted_ids = set(self.deleted_default_ids)

        added = False
        for d in defaults:
            if d["id"] in deleted_ids:
                continue
            if d["id"] in existing_ids:
                continue
            if d["kaomoji"] in existing_texts:
                continue
            self.items.append({
                "id": d["id"],
                "origin": "default",
                "kaomoji": d["kaomoji"],
                "desc": d.get("desc", ""),
                "tags": d.get("tags", []),
                "last_used": None,
                "use_count": 0,
            })
            existing_ids.add(d["id"])
            existing_texts.add(d["kaomoji"])
            added = True

        if added:
            self.save()

    # -- sorting -----------------------------------------------------------

    def _split_recent(self, recent_limit=10):
        """Shared helper: returns (top_recent, remaining_sorted) without mutating self.items."""
        used_items = [i for i in self.items if i.get("last_used")]
        used_items.sort(key=lambda i: i["last_used"], reverse=True)

        top_recent = used_items[:recent_limit]
        recent_ids = {i["id"] for i in top_recent}

        remaining = [i for i in self.items if i["id"] not in recent_ids]
        remaining.sort(
            key=lambda i: (
                i.get("tags", [""])[0].lower() if i.get("tags") else "zzz",
                i.get("desc", "").lower()
            )
        )
        return top_recent, remaining

    def sort_items(self, recent_limit=10):
        """Places the X last used Kaomojis at the top and sorts the rest by day.
        Mutates self.items (used once at load time)."""
        top_recent, remaining = self._split_recent(recent_limit)
        self.items = top_recent + remaining

    def ordered_items(self, recent_limit=10):
        """Non-mutating version of sort_items(): computes a fresh recent-first
        ordering on demand (e.g. every time the popup is opened) without
        touching self.items or the on-disk order. This is what fixes the
        'stale order until restart' issue - call this instead of self.items
        whenever you display the full list."""
        top_recent, remaining = self._split_recent(recent_limit)
        return top_recent + remaining

    # -- persistence ---------------------------------------------------------

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "items": self.items,
            "deleted_default_ids": self.deleted_default_ids,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # -- CRUD ------------------------------------------------------------

    def exists(self, kaomoji: str, exclude_id: str = None) -> bool:
        """Case-sensitive exact-text duplicate check, used before add/edit."""
        return any(
            i["kaomoji"] == kaomoji and i["id"] != exclude_id
            for i in self.items
        )

    def add(self, kaomoji: str, desc: str, tags: list):
        if self.exists(kaomoji):
            raise ValueError(f'"{kaomoji}" already exists.')
        self.items.append({
            "id": f"u_{uuid.uuid4().hex[:10]}",
            "origin": "user",
            "kaomoji": kaomoji, "desc": desc, "tags": tags,
            "last_used": None, "use_count": 0,
        })
        self.save()

    def delete(self, item_id: str):
        item = next((i for i in self.items if i["id"] == item_id), None)
        if item is None:
            return
        self.items = [i for i in self.items if i["id"] != item_id]
        if item.get("origin") == "default":
            # Tombstone it so a future default_kaomojis.json sync won't
            # bring it back.
            self.deleted_default_ids.append(item_id)
        self.save()

    def _next_timestamp(self) -> str:
        """A 'last_used' stamp that is strictly newer than every existing one.

        datetime.now() alone is not enough: on Windows the clock only ticks
        every ~15 ms, so two quick uses can get the identical stamp, and a
        local-time clock can also jump backwards (DST change, manual
        adjustment). Either would make the newer use sort *below* an older
        one in the "recently used" list.
        """
        now = datetime.now()
        newest = None
        for item in self.items:
            stamp = item.get("last_used")
            if not stamp:
                continue
            try:
                parsed = datetime.fromisoformat(stamp)
            except (TypeError, ValueError):
                continue
            if newest is None or parsed > newest:
                newest = parsed
        if newest is not None and now <= newest:
            now = newest + timedelta(microseconds=1)
        return now.isoformat()

    def mark_used(self, item_id: str):
        for item in self.items:
            if item["id"] == item_id:
                item["last_used"] = self._next_timestamp()
                item["use_count"] = item.get("use_count", 0) + 1
                self.save()
                return

    def all_tags(self):
        tags = set()
        for i in self.items:
            tags.update(i.get("tags", []))
        return sorted(tags)

    def recent_items(self, limit=config.RECENT_LIMIT):
        used = [i for i in self.items if i.get("last_used")]
        used.sort(key=lambda i: i["last_used"], reverse=True)
        return used[:limit]