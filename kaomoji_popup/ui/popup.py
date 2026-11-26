"""
KaomojiPopup: the borderless search/insert window opened by the global
hotkey.
"""
import os
import tkinter as tk
from tkinter import ttk

import pyperclip
from pynput import keyboard

from .. import config
from ..hotkey import HotkeyManager
from ..store import KaomojiStore
from .dialogs import ConfirmDialog, EntryDialog, SettingsDialog
from .theme import (COLORS, FONT_KAOMOJI, WINDOW_HEIGHT, WINDOW_WIDTH, apply_theme,
                    make_treeview, refresh_system_theme, style_toplevel)


class KaomojiPopup:
    def __init__(self, root: tk.Tk, store: KaomojiStore, hotkey_mgr: HotkeyManager):
        self.root = root
        self.store = store
        self.hotkey_mgr = hotkey_mgr
        self.win = None
        self._visible_items = []
        self._has_grab = False

    def show(self):
        if self.win is not None:
            self._close()
            return

        # In "System" mode, pick up desktop theme changes made since last time.
        refresh_system_theme(self.root)

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        style_toplevel(self.win)
        self.win.title("Kaomoji Picker")
        self.win.resizable(False, False)
        self._center()

        # - Force window to foreground ---
        self.win.attributes("-topmost", True)
        self.win.lift()
        self.win.focus_force()

        # Optional for Windows: A short pulse ensures, that the system focus ban is circumvented
        self.win.after(10, lambda: self.win.attributes("-topmost", True))

        self.win.bind("<Escape>", lambda e: self._close())
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        header = tk.Frame(self.win, bg=COLORS["mantle"], cursor="fleur", height=28)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text=" Kaomoji Picker",
            bg=COLORS["mantle"],
            fg=COLORS["subtext0"],
            font=("Consolas", 9)
        )
        title_lbl.pack(side="left", padx=6, pady=4)

        close_btn = tk.Label(
            header,
            text="×",
            bg=COLORS["mantle"],
            fg=COLORS["subtext0"],
            font=("Consolas", 12),
            cursor="arrow",
        )
        close_btn.pack(side="right", padx=(0, 8), pady=2)
        close_btn.bind("<Button-1>", lambda e: self._close())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=COLORS["red"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=COLORS["subtext0"]))

        # Dragging-Logic
        self._drag_start_x = 0
        self._drag_start_y = 0

        def start_drag(event):
            self._drag_start_x = event.x
            self._drag_start_y = event.y

        def do_drag(event):
            x = self.win.winfo_x() + (event.x - self._drag_start_x)
            y = self.win.winfo_y() + (event.y - self._drag_start_y)
            self.win.geometry(f"+{x}+{y}")

        header.bind("<Button-1>", start_drag)
        header.bind("<B1-Motion>", do_drag)
        title_lbl.bind("<Button-1>", start_drag)
        title_lbl.bind("<B1-Motion>", do_drag)

        frame = ttk.Frame(self.win, padding=8)
        frame.pack(fill="both", expand=True)

        top_row = ttk.Frame(frame)
        top_row.pack(fill="x")

        self.query = tk.StringVar()
        entry = ttk.Entry(top_row, textvariable=self.query, font=FONT_KAOMOJI)
        entry.pack(side="left", fill="x", expand=True)
        entry.focus_set()
        self.query.trace_add("write", lambda *a: self._refresh())

        self.tag_var = tk.StringVar(value="All")
        self.tag_combo = ttk.Combobox(top_row, textvariable=self.tag_var, state="readonly", width=16)
        self.tag_combo.pack(side="left", padx=(6, 0))
        self.tag_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        self.tree = make_treeview(frame)
        self.tree.pack(fill="both", expand=True, pady=(6, 0))

        entry.bind("<Down>", lambda e: self._focus_list())
        entry.bind("<Return>", lambda e: self._select_first())
        self.tree.bind("<Return>", lambda e: self._select_current())
        self.tree.bind("<Double-Button-1>", lambda e: self._select_current())
        self.tree.bind("<Delete>", lambda e: self._delete_selected())

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_row, text="+ Add", style="Accent.TButton",
                   command=self._open_add_dialog).pack(side="left")
        ttk.Button(btn_row, text="Edit", command=self._open_edit_dialog).pack(side="left", padx=(6, 0))
        ttk.Button(btn_row, text="Delete", command=self._delete_selected).pack(side="left", padx=(6, 0))
        ttk.Button(btn_row, text="⚙ Settings", command=self._open_settings_dialog).pack(side="right")

        self._update_tag_choices()
        self._refresh()
        self._has_grab = False
        self._try_grab()

    def _center(self):
        px = self.root.winfo_pointerx()
        py = self.root.winfo_pointery()
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()

        x = max(0, min(px - WINDOW_WIDTH // 2, screen_w - WINDOW_WIDTH))
        y = max(0, min(py - WINDOW_HEIGHT // 2, screen_h - WINDOW_HEIGHT))
        self.win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _update_tag_choices(self):
        tags = ["All", config.RECENT_TAG_LABEL] + self.store.all_tags()
        self.tag_combo["values"] = tags
        if self.tag_var.get() not in tags:
            self.tag_var.set("All")

    def _refresh(self):
        q = self.query.get().lower().strip()
        tag_filter = self.tag_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._visible_items = []

        if tag_filter == config.RECENT_TAG_LABEL:
            candidates = self.store.recent_items()
        else:
            candidates = self.store.ordered_items()

        recent_star = {i["id"] for i in self.store.recent_items(config.RECENT_STAR_COUNT)}

        for item in candidates:
            if tag_filter not in ("All", config.RECENT_TAG_LABEL) and tag_filter not in item.get("tags", []):
                continue
            hay = f'{item["kaomoji"]} {item["desc"]} {" ".join(item.get("tags", []))}'.lower()
            if q and q not in hay:
                continue

            # iid must match the index this item will have in _visible_items,
            # NOT its position in the unfiltered "candidates" list - otherwise
            # selecting a row after filtering picks the wrong item.
            vis_idx = len(self._visible_items)
            self._visible_items.append(item)

            is_starred = item["id"] in recent_star and tag_filter != config.RECENT_TAG_LABEL
            star_prefix = "⭐ " if is_starred else ""

            kaomoji_val = f"{star_prefix}{item['kaomoji']}"
            desc_val = item["desc"]
            tag_val = f"[{', '.join(item.get('tags', []))}]" if item.get("tags") else ""

            # The Treeview inserts values directly as separate column entries
            self.tree.insert("", "end", iid=str(vis_idx), values=(kaomoji_val, desc_val, tag_val))

        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])

    def _focus_list(self):
        self.tree.focus_set()
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])

    def _select_first(self):
        if self._visible_items:
            self._insert(self._visible_items[0])

    def _select_current(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            self._insert(self._visible_items[idx])

    def _open_add_dialog(self):
        EntryDialog(self.win, self.store, on_done=self._after_data_change)

    def _open_edit_dialog(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = self._visible_items[idx]
        EntryDialog(self.win, self.store, on_done=self._after_data_change, existing_item=item)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = self._visible_items[idx]

        def do_delete():
            self.store.delete(item["id"])
            self._after_data_change()

        ConfirmDialog(
            self.win,
            "Delete Kaomoji",
            f'Are you sure you want to delete "{item["kaomoji"]}" ({item["desc"]})?',
            on_confirm=do_delete,
        )

    def _open_settings_dialog(self):
        SettingsDialog(self.win, self.hotkey_mgr, on_done=self._on_settings_changed)

    def _on_settings_changed(self, new_hotkey: str, theme_mode: str, theme_changed: bool):
        # Hotkey: nothing to do, the listener is already running with the new one.
        if theme_changed:
            # Widgets pick their colours up at creation time, so the simplest
            # correct way to re-theme is to rebuild the popup window.
            apply_theme(self.root, theme_mode)
            self._close()
            self.root.after(50, self.show)

    def _after_data_change(self):
        self._update_tag_choices()
        self._refresh()

    def _insert(self, item: dict):
        kaomoji = item["kaomoji"]
        self.store.mark_used(item["id"])
        self._close()

        if config.INSERT_MODE in ("paste", "clipboard"):
            try:
                pyperclip.copy(kaomoji)
            except Exception as exc:
                config.logger.warning("Clipboard copy failed: %s", exc)
            if config.INSERT_MODE == "clipboard":
                return

        def do_insert():
            try:
                kb = keyboard.Controller()
                if config.INSERT_MODE == "type":
                    kb.type(kaomoji)
                elif config.INSERT_MODE == "paste":
                    kb.press(keyboard.Key.ctrl)
                    kb.press("v")
                    kb.release("v")
                    kb.release(keyboard.Key.ctrl)
            except Exception as exc:
                config.logger.debug(
                    "Best-effort insertion failed (%s): %s",
                    config.INSERT_MODE,
                    exc,
                )

        self.root.after(config.INSERT_DELAY_MS, do_insert)

    def _close(self):
        if self.win is not None:
            if self._has_grab:
                try:
                    self.win.grab_release()
                except tk.TclError:
                    pass
                self._has_grab = False
            self.win.destroy()
            self.win = None

    def _try_grab(self, retries: int = 12, delay_ms: int = 35):
        if self.win is None or not self.win.winfo_exists():
            return
        try:
            self.win.grab_set()
            self._has_grab = True
        except tk.TclError:
            if retries > 0:
                self.win.after(delay_ms, lambda: self._try_grab(retries - 1, delay_ms))
