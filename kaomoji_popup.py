#!/usr/bin/env python3
"""
Kaomoji/ASCII-Art Popup Picker
--------------------------------
Global Hotkey (Default: Ctrl+Alt+Space) opens a small search window.
Typing filters live; pressing Enter or double-clicking automatically
inserts the selection at the cursor position in the previously active window.

Dependencies:
    pip install pynput pyperclip

Run:
    python kaomoji_popup.py

Create executable:
    pyinstaller --onefile --noconsole kaomoji_popup.py
"""

import json
import queue
import threading
import tkinter as tk
from datetime import datetime
import os
from pathlib import Path
from tkinter import messagebox, ttk
import urllib.request
import json
import webbrowser
import pyperclip
from pynput import keyboard

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOTKEY = "<ctrl>+<alt>+<space>"
WINDOW_WIDTH = 560
WINDOW_HEIGHT = 480

INSERT_MODE = "paste"
INSERT_DELAY_MS = 150
CLIPBOARD_RESTORE_DELAY_MS = 400

RECENT_TAG_LABEL = "\u2b50 Recently Used"
RECENT_LIMIT = 20
RECENT_STAR_COUNT = 6

# Determine the path to the user's AppData folder
APPDATA_DIR = Path(os.getenv("APPDATA", Path.home())) / "KaomojiPopup"
APPDATA_DIR.mkdir(parents=True, exist_ok=True) # Creates the folder if it does not exist
USER_SETTINGS_FILE = APPDATA_DIR / "kaomoji_settings.json"
USER_DATA_FILE = APPDATA_DIR / "kaomojis.json"

DEFAULT_DATA_FILE = Path(__file__).resolve().parent / "default_kaomojis.json"

KEY_CHOICES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + [f"f{i}" for i in range(1, 13)] + ["space"]

COLORS = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
    "text": "#cdd6f4",
    "subtext0": "#a6adc8",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "red": "#f38ba8",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "mauve": "#cba6f7",
    "lavender": "#b4befe",
}

FONT_UI = ("Consolas", 11)
FONT_KAOMOJI = ("Consolas", 11)

CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "Noxy03/kaomoji_popup"


def check_for_updates():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KaomojiApp"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").lstrip("v")

            # Simple version comparison
            if latest_version and latest_version > CURRENT_VERSION:
                html_url = data.get("html_url")
                # Optional: Ask tkinter.messagebox if to update
                webbrowser.open(html_url)
    except Exception:
        pass # Offline or API limit exceeded

def apply_theme(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=COLORS["base"], foreground=COLORS["text"],
                    fieldbackground=COLORS["surface0"], font=FONT_UI)
    style.configure("TFrame", background=COLORS["base"])
    style.configure("TLabel", background=COLORS["base"], foreground=COLORS["text"])
    style.configure("TButton", background=COLORS["surface0"], foreground=COLORS["text"],
                    borderwidth=0, padding=6)
    style.map("TButton",
              background=[("active", COLORS["surface1"]), ("pressed", COLORS["surface2"])])
    style.configure("Accent.TButton", background=COLORS["mauve"], foreground=COLORS["crust"])
    style.map("Accent.TButton",
              background=[("active", COLORS["lavender"]), ("pressed", COLORS["lavender"])])
    style.configure("TEntry", fieldbackground=COLORS["surface0"], foreground=COLORS["text"],
                    insertcolor=COLORS["text"], borderwidth=0)
    style.configure("TCombobox", fieldbackground=COLORS["surface0"], background=COLORS["surface0"],
                    foreground=COLORS["text"], arrowcolor=COLORS["text"])
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface0"])])

    # Treeview styling for real columns
    style.configure("Treeview",
                    background=COLORS["surface0"],
                    foreground=COLORS["text"],
                    fieldbackground=COLORS["surface0"],
                    font=FONT_KAOMOJI,
                    borderwidth=0,
                    rowheight=26)
    style.map("Treeview",
              background=[("selected", COLORS["mauve"])],
              foreground=[("selected", COLORS["crust"])])

    root.option_add("*TCombobox*Listbox.background", COLORS["surface0"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["mauve"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["crust"])

    style.configure("Danger.TButton", background=COLORS["red"], foreground=COLORS["crust"])
    style.map("Danger.TButton",
              background=[("active", "#f5a3bb"), ("pressed", "#f5a3bb")])


def style_toplevel(win: tk.Toplevel):
    win.configure(bg=COLORS["base"])


def center_window(win: tk.Toplevel, parent: tk.Misc = None):
    """Centers a Toplevel window relative to a parent window,
    or relative to the screen if no parent is provided."""
    win.update_idletasks()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()
    if parent is not None:
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
    else:
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")


# ---------------------------------------------------------------------------
# Hotkey: Persistence, Parsing, Live Re-registration
# ---------------------------------------------------------------------------

def load_hotkey():
    if USER_SETTINGS_FILE.exists():
        try:
            with open(USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                hk = data.get("hotkey")
                if hk:
                    return hk
        except (json.JSONDecodeError, OSError):
            pass
    return HOTKEY


def save_hotkey(hotkey_str: str):
    with open(USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"hotkey": hotkey_str}, f, ensure_ascii=False, indent=2)


def parse_hotkey(hotkey_str: str):
    ctrl = alt = shift = False
    key = ""
    for part in hotkey_str.split("+"):
        token = part.strip().strip("<>").lower()
        if token == "ctrl":
            ctrl = True
        elif token == "alt":
            alt = True
        elif token == "shift":
            shift = True
        elif token:
            key = token
    return ctrl, alt, shift, key


def build_hotkey(ctrl: bool, alt: bool, shift: bool, key: str) -> str:
    parts = []
    if ctrl:
        parts.append("<ctrl>")
    if alt:
        parts.append("<alt>")
    if shift:
        parts.append("<shift>")
    if key:
        # F-keys and "space" must be enclosed in <...>
        if (key.startswith("f") and key[1:].isdigit()) or key == "space":
            parts.append(f"<{key}>")
        else:
            parts.append(key)
    return "+".join(parts)


def format_hotkey_display(hotkey_str: str) -> str:
    ctrl, alt, shift, key = parse_hotkey(hotkey_str)
    labels = []
    if ctrl:
        labels.append("Ctrl")
    if alt:
        labels.append("Alt")
    if shift:
        labels.append("Shift")
    if key:
        labels.append("Space" if key == "space" else key.upper())
    return " + ".join(labels) if labels else "(none)"


class HotkeyManager:
    """Starts/stops the global hotkey listener and allows changing it
    at runtime without restarting the application."""

    def __init__(self, on_trigger):
        self.on_trigger = on_trigger
        self.listener = None
        self.current = None

    def start(self, hotkey_str: str):
        new_listener = keyboard.GlobalHotKeys({hotkey_str: self.on_trigger})
        new_listener.daemon = True
        new_listener.start()
        self.stop()
        self.listener = new_listener
        self.current = hotkey_str

    def stop(self):
        if self.listener is not None:
            self.listener.stop()
            self.listener = None


def make_treeview(parent) -> ttk.Treeview:
    tree = ttk.Treeview(
        parent,
        columns=("kaomoji", "desc", "tags"),
        show="",
        selectmode="browse",
        height=12
    )
    # Set exact pixel widths for each real column
    tree.column("kaomoji", width=220, anchor="w")
    tree.column("desc", width=160, anchor="w")
    tree.column("tags", width=140, anchor="w")
    return tree


class KaomojiStore:
    def __init__(self, path: Path):
        self.path = path
        self.items = self._load()
        self.sort_items()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                messagebox.showwarning(
                    "Kaomoji Popup",
                    f"Could not read {self.path.name}. Starting with default list.",
                )
        data = [dict(d) for d in DEFAULT_DATA_FILE]
        self.items = data
        self.save()
        return data

    def sort_items(self, recent_limit=10):
        """Places the X last used Kaomojis at the top and sorts the rest by day."""
        # 1. Sort only Kaomojis with usage date in descending order
        used_items = [i for i in self.items if i.get("last_used")]
        used_items.sort(key=lambda i: i["last_used"], reverse=True)

        top_recent = used_items[:recent_limit]
        recent_set = {i["kaomoji"] for i in top_recent}

        # 2. Filter remaining Kaomojis and sort by day + description
        remaining = [i for i in self.items if i["kaomoji"] not in recent_set]
        remaining.sort(
            key=lambda i: (
                i.get("tags", [""])[0].lower() if i.get("tags") else "zzz",
                i.get("desc", "").lower()
            )
        )

        # 3. Merge both lists
        self.items = top_recent + remaining

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

    def add(self, kaomoji: str, desc: str, tags: list):
        self.items.append({
            "kaomoji": kaomoji, "desc": desc, "tags": tags,
            "last_used": None, "use_count": 0,
        })
        self.save()

    def delete(self, kaomoji: str):
        self.items = [i for i in self.items if i["kaomoji"] != kaomoji]
        self.save()

    def mark_used(self, kaomoji: str):
        for item in self.items:
            if item["kaomoji"] == kaomoji:
                item["last_used"] = datetime.now().isoformat()
                item["use_count"] = item.get("use_count", 0) + 1
                self.save()
                return

    def all_tags(self):
        tags = set()
        for i in self.items:
            tags.update(i.get("tags", []))
        return sorted(tags)

    def recent_items(self, limit=RECENT_LIMIT):
        used = [i for i in self.items if i.get("last_used")]
        used.sort(key=lambda i: i["last_used"], reverse=True)
        return used[:limit]


class EntryDialog:
    def __init__(self, parent: tk.Toplevel, store: KaomojiStore, on_done, existing_item=None):
        self.store = store
        self.on_done = on_done
        self.existing_item = existing_item

        self.win = tk.Toplevel(parent)
        style_toplevel(self.win)
        self.win.title("Edit Kaomoji" if existing_item else "Add Kaomoji")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Kaomoji:").grid(row=0, column=0, sticky="w", pady=4)
        self.kao_var = tk.StringVar(value=existing_item["kaomoji"] if existing_item else "")
        kao_entry = ttk.Entry(frame, textvariable=self.kao_var, font=FONT_KAOMOJI, width=32)
        kao_entry.grid(row=0, column=1, pady=4)
        kao_entry.focus_set()

        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar(value=existing_item["desc"] if existing_item else "")
        ttk.Entry(frame, textvariable=self.desc_var, width=32).grid(row=1, column=1, pady=4)

        ttk.Label(frame, text="Tags (comma-separated):").grid(row=2, column=0, sticky="w", pady=4)
        tags_default = ", ".join(existing_item.get("tags", [])) if existing_item else ""
        self.tags_var = tk.StringVar(value=tags_default)
        ttk.Entry(frame, textvariable=self.tags_var, width=32).grid(row=2, column=1, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Save", style="Accent.TButton", command=self._save).pack(side="right")

        self.win.bind("<Return>", lambda e: self._save())
        self.win.bind("<Escape>", lambda e: self.win.destroy())

        center_window(self.win, parent)

    def _save(self):
        kao = self.kao_var.get().strip()
        if not kao:
            messagebox.showerror("Kaomoji Popup", "Please enter a Kaomoji.", parent=self.win)
            return
        desc = self.desc_var.get().strip()
        tags = [t.strip().lower() for t in self.tags_var.get().split(",") if t.strip()]

        if self.existing_item is not None:
            self.existing_item["kaomoji"] = kao
            self.existing_item["desc"] = desc
            self.existing_item["tags"] = tags
            self.store.save()
        else:
            self.store.add(kao, desc, tags)

        self.win.destroy()
        self.on_done()


class ConfirmDialog:
    """Uniformly styled confirmation dialog (replaces native
    messagebox.askyesno, which cannot be themed)."""

    def __init__(self, parent: tk.Misc, title: str, message: str, on_confirm,
                 confirm_text: str = "Delete", danger: bool = True):
        self.win = tk.Toplevel(parent)
        style_toplevel(self.win)
        self.win.title(title)
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=message, wraplength=320, justify="left").pack(pady=(0, 14))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        def confirm():
            self.win.destroy()
            on_confirm()

        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text=confirm_text, style="Danger.TButton" if danger else "Accent.TButton",
                   command=confirm).pack(side="right")

        self.win.bind("<Escape>", lambda e: self.win.destroy())
        self.win.bind("<Return>", lambda e: confirm())

        center_window(self.win, parent)


class SettingsDialog:
    """Dialog for changing the global hotkey, registered live immediately."""

    def __init__(self, parent: tk.Misc, hotkey_mgr: HotkeyManager, on_done):
        self.hotkey_mgr = hotkey_mgr
        self.on_done = on_done

        self.win = tk.Toplevel(parent)
        style_toplevel(self.win)
        self.win.title("Settings")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Hotkey", font=("Consolas", 12, "bold")).pack(anchor="w")

        ctrl0, alt0, shift0, key0 = parse_hotkey(hotkey_mgr.current)

        mod_frame = ttk.Frame(frame)
        mod_frame.pack(fill="x", pady=(10, 4))
        self.ctrl_var = tk.BooleanVar(value=ctrl0)
        self.alt_var = tk.BooleanVar(value=alt0)
        self.shift_var = tk.BooleanVar(value=shift0)
        ttk.Checkbutton(mod_frame, text="Ctrl", variable=self.ctrl_var,
                         command=self._update_preview).pack(side="left")
        ttk.Checkbutton(mod_frame, text="Alt", variable=self.alt_var,
                         command=self._update_preview).pack(side="left", padx=(10, 0))
        ttk.Checkbutton(mod_frame, text="Shift", variable=self.shift_var,
                         command=self._update_preview).pack(side="left", padx=(10, 0))

        key_frame = ttk.Frame(frame)
        key_frame.pack(fill="x", pady=(4, 10))
        ttk.Label(key_frame, text="Key:").pack(side="left")
        self.key_var = tk.StringVar(value=key0 if key0 in KEY_CHOICES else "k")
        key_combo = ttk.Combobox(key_frame, textvariable=self.key_var, values=KEY_CHOICES,
                                  state="readonly", width=6)
        key_combo.pack(side="left", padx=(8, 0))
        key_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        self.preview_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.preview_var, foreground=COLORS["lavender"]).pack(
            anchor="w", pady=(0, 14)
        )
        self._update_preview()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Save", style="Accent.TButton", command=self._save).pack(side="right")

        self.win.bind("<Escape>", lambda e: self.win.destroy())

        center_window(self.win, parent)

    def _update_preview(self):
        hk = build_hotkey(self.ctrl_var.get(), self.alt_var.get(), self.shift_var.get(), self.key_var.get())
        self.preview_var.set(format_hotkey_display(hk))

    def _save(self):
        if not self.key_var.get():
            messagebox.showerror("Kaomoji Popup", "Please choose a key.", parent=self.win)
            return
        if not (self.ctrl_var.get() or self.alt_var.get() or self.shift_var.get()):
            if not messagebox.askyesno(
                "Kaomoji Popup",
                "No modifier selected — this hotkey may interfere with normal typing. "
                "Continue anyway?",
                parent=self.win,
            ):
                return

        new_hotkey = build_hotkey(
            self.ctrl_var.get(), self.alt_var.get(), self.shift_var.get(), self.key_var.get()
        )
        try:
            self.hotkey_mgr.start(new_hotkey)
        except Exception as e:
            messagebox.showerror("Kaomoji Popup", f"Could not register hotkey: {e}", parent=self.win)
            return

        save_hotkey(new_hotkey)
        self.win.destroy()
        self.on_done(new_hotkey)


class KaomojiPopup:
    def __init__(self, root: tk.Tk, store: KaomojiStore, hotkey_mgr: HotkeyManager):
        self.root = root
        self.store = store
        self.hotkey_mgr = hotkey_mgr
        self.win = None
        self._visible_items = []

    def show(self):
        if self.win is not None:
            self._close()
            return

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
        ttk.Button(btn_row, text="⚙ Hotkey", command=self._open_settings_dialog).pack(side="right")

        self._update_tag_choices()
        self._refresh()
        self.win.grab_set()

    def _center(self):
        x = self.root.winfo_pointerx() - WINDOW_WIDTH // 2
        y = self.root.winfo_pointery() - WINDOW_HEIGHT // 2
        self.win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{max(x, 0)}+{max(y, 0)}")


    def _update_tag_choices(self):
        tags = ["All", RECENT_TAG_LABEL] + self.store.all_tags()
        self.tag_combo["values"] = tags
        if self.tag_var.get() not in tags:
            self.tag_var.set("All")

    def _refresh(self):
        q = self.query.get().lower().strip()
        tag_filter = self.tag_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._visible_items = []

        if tag_filter == RECENT_TAG_LABEL:
            candidates = self.store.recent_items()
        else:
            candidates = self.store.items

        recent_star = {i["kaomoji"] for i in self.store.recent_items(RECENT_STAR_COUNT)}

        for idx, item in enumerate(candidates):
            if tag_filter not in ("All", RECENT_TAG_LABEL) and tag_filter not in item.get("tags", []):
                continue
            hay = f'{item["kaomoji"]} {item["desc"]} {" ".join(item.get("tags", []))}'.lower()
            if q and q not in hay:
                continue

            self._visible_items.append(item)

            is_starred = item["kaomoji"] in recent_star and tag_filter != RECENT_TAG_LABEL
            star_prefix = "⭐ " if is_starred else ""

            kaomoji_val = f"{star_prefix}{item['kaomoji']}"
            desc_val = item["desc"]
            tag_val = f"[{', '.join(item.get('tags', []))}]" if item.get("tags") else ""

            # The Treeview inserts values directly as separate column entries
            self.tree.insert("", "end", iid=str(idx), values=(kaomoji_val, desc_val, tag_val))

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
            self._insert(self._visible_items[0]["kaomoji"])

    def _select_current(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            self._insert(self._visible_items[idx]["kaomoji"])

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
            self.store.delete(item["kaomoji"])
            self._after_data_change()

        ConfirmDialog(
            self.win,
            "Delete Kaomoji",
            f'Are you sure you want to delete "{item["kaomoji"]}" ({item["desc"]})?',
            on_confirm=do_delete,
        )

    def _open_settings_dialog(self):
        SettingsDialog(self.win, self.hotkey_mgr, on_done=self._on_hotkey_changed)

    def _on_hotkey_changed(self, new_hotkey: str):
        # No popup restart needed; the listener is already running with the new hotkey.
        pass

    def _after_data_change(self):
        self._update_tag_choices()
        self._refresh()

    def _insert(self, kaomoji: str):
        self.store.mark_used(kaomoji)
        self._close()

        if INSERT_MODE == "clipboard":
            pyperclip.copy(kaomoji)
            return

        old_clip = None
        if INSERT_MODE == "paste":
            try:
                old_clip = pyperclip.paste()
            except Exception:
                old_clip = None
            pyperclip.copy(kaomoji)

        def do_insert():
            kb = keyboard.Controller()
            if INSERT_MODE == "type":
                kb.type(kaomoji)
            elif INSERT_MODE == "paste":
                kb.press(keyboard.Key.ctrl)
                kb.press("v")
                kb.release("v")
                kb.release(keyboard.Key.ctrl)
                if old_clip is not None:
                    self.root.after(
                        CLIPBOARD_RESTORE_DELAY_MS,
                        lambda: pyperclip.copy(old_clip),
                    )

        self.root.after(INSERT_DELAY_MS, do_insert)

    def _close(self):
        if self.win is not None:
            self.win.grab_release()
            self.win.destroy()
            self.win = None


def main():
    root = tk.Tk()
    root.withdraw()
    apply_theme(root)

    threading.Thread(target=check_for_updates, daemon=True).start()

    store = KaomojiStore(USER_DATA_FILE)
    trigger_queue: "queue.Queue[bool]" = queue.Queue()

    def on_hotkey():
        trigger_queue.put(True)

    hotkey_mgr = HotkeyManager(on_hotkey)
    hotkey_mgr.start(load_hotkey())

    popup = KaomojiPopup(root, store, hotkey_mgr)

    def poll_queue():
        try:
            while True:
                trigger_queue.get_nowait()
                popup.show()
        except queue.Empty:
            pass
        root.after(50, poll_queue)

    poll_queue()
    print(f"Kaomoji Popup is running in the background. Hotkey: {format_hotkey_display(hotkey_mgr.current)}")
    print(f"Data file: {USER_DATA_FILE}")
    print("To exit, close this terminal window or press Ctrl+C.")
    root.mainloop()


if __name__ == "__main__":
    main()
