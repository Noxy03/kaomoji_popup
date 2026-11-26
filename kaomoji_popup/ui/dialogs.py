"""
Modal dialogs: add/edit an entry, themed confirmation/message prompts, and
the settings dialog (hotkey, theme, window position).

All dialogs are borderless windows in the popup's style (see
theme.prepare_dialog for why) - that is also why native tkinter
messageboxes are not used here: they are normal managed windows and would
open behind the popup.
"""
import tkinter as tk
from tkinter import ttk

from .. import hotkey as hotkey_mod
from .. import settings, themes
from ..store import KaomojiStore
from .theme import (COLORS, FONT_KAOMOJI, center_window, close_dialog, finish_dialog,
                    get_theme_mode, prepare_dialog)


class EntryDialog:
    def __init__(self, parent: tk.Toplevel, store: KaomojiStore, on_done, existing_item=None):
        self.parent = parent
        self.store = store
        self.on_done = on_done
        self.existing_item = existing_item

        self.win = tk.Toplevel(parent)
        prepare_dialog(self.win, "Edit Kaomoji" if existing_item else "Add Kaomoji", self._close)

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
        ttk.Button(btn_frame, text="Cancel", command=self._close).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Save", style="Accent.TButton", command=self._save).pack(side="right")

        self.win.bind("<Return>", lambda e: self._save())
        self.win.bind("<Escape>", lambda e: self._close())

        center_window(self.win, parent)
        finish_dialog(self.win)

    def _close(self):
        close_dialog(self.win, self.parent)

    def _save(self):
        kao = self.kao_var.get().strip()
        if not kao:
            MessageDialog(self.win, "Kaomoji Popup", "Please enter a Kaomoji.")
            return
        desc = self.desc_var.get().strip()
        tags = [t.strip().lower() for t in self.tags_var.get().split(",") if t.strip()]

        exclude_id = self.existing_item["id"] if self.existing_item is not None else None
        if self.store.exists(kao, exclude_id=exclude_id):
            MessageDialog(self.win, "Kaomoji Popup", f'"{kao}" already exists in the list.')
            return

        if self.existing_item is not None:
            self.existing_item["kaomoji"] = kao
            self.existing_item["desc"] = desc
            self.existing_item["tags"] = tags
            self.store.save()
        else:
            self.store.add(kao, desc, tags)

        self._close()
        self.on_done()


class ConfirmDialog:
    """Uniformly styled confirmation dialog (replaces native
    messagebox.askyesno, which cannot be themed and opens behind the popup)."""

    def __init__(self, parent: tk.Misc, title: str, message: str, on_confirm,
                 confirm_text: str = "Delete", danger: bool = True, show_cancel: bool = True):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        prepare_dialog(self.win, title, self._close)

        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=message, wraplength=320, justify="left").pack(pady=(0, 14))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        def confirm():
            self._close()
            on_confirm()

        if show_cancel:
            ttk.Button(btn_frame, text="Cancel", command=self._close).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text=confirm_text, style="Danger.TButton" if danger else "Accent.TButton",
                   command=confirm).pack(side="right")

        self.win.bind("<Escape>", lambda e: self._close())
        self.win.bind("<Return>", lambda e: confirm())

        center_window(self.win, parent)
        finish_dialog(self.win)

    def _close(self):
        close_dialog(self.win, self.parent)


class MessageDialog(ConfirmDialog):
    """Themed replacement for messagebox.showerror/showinfo: message + OK."""

    def __init__(self, parent: tk.Misc, title: str, message: str):
        super().__init__(parent, title, message, on_confirm=lambda: None,
                         confirm_text="OK", danger=False, show_cancel=False)


class SettingsDialog:
    """Settings: global hotkey (registered live), colour theme and where the
    popup opens.

    on_done(theme_mode, theme_changed, position_changed) is called after a
    successful save; Cancel just closes the dialog without calling it.
    """

    def __init__(self, parent: tk.Misc, hotkey_mgr: hotkey_mod.HotkeyManager, on_done):
        self.parent = parent
        self.hotkey_mgr = hotkey_mgr
        self.on_done = on_done

        self.win = tk.Toplevel(parent)
        prepare_dialog(self.win, "Settings", self._close)

        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill="both", expand=True)

        # -- Hotkey ----------------------------------------------------------
        ttk.Label(frame, text="Hotkey", font=("Consolas", 12, "bold")).pack(anchor="w")

        ctrl0, alt0, shift0, key0 = hotkey_mod.parse_hotkey(hotkey_mgr.current)

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
        # KEY_CHOICES holds letters uppercase ("K") but "space"/"f1"..."f12"
        # lowercase, while key0 from parse_hotkey() is always lowercase -
        # normalize per-kind so the current key is correctly preselected.
        if key0 in ("space",) or (key0.startswith("f") and key0[1:].isdigit()):
            key0_norm = key0
        else:
            key0_norm = key0.upper()
        self.key_var = tk.StringVar(value=key0_norm if key0_norm in hotkey_mod.KEY_CHOICES else "K")
        key_combo = ttk.Combobox(key_frame, textvariable=self.key_var, values=hotkey_mod.KEY_CHOICES,
                                  state="readonly", width=6)
        key_combo.pack(side="left", padx=(8, 0))
        key_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        self.preview_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.preview_var, foreground=COLORS["lavender"]).pack(
            anchor="w", pady=(0, 10)
        )
        self._update_preview()

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=(0, 10))

        # -- Theme -----------------------------------------------------------
        ttk.Label(frame, text="Theme", font=("Consolas", 12, "bold")).pack(anchor="w")

        theme_frame = ttk.Frame(frame)
        theme_frame.pack(fill="x", pady=(10, 10))
        ttk.Label(theme_frame, text="Appearance:").pack(side="left")
        self._mode_by_label = {label: mode for mode, label in themes.THEME_LABELS.items()}
        self.theme_var = tk.StringVar(value=themes.THEME_LABELS[get_theme_mode()])
        ttk.Combobox(theme_frame, textvariable=self.theme_var, values=list(self._mode_by_label),
                     state="readonly", width=20).pack(side="left", padx=(8, 0))

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=(0, 10))

        # -- Window position -------------------------------------------------
        ttk.Label(frame, text="Window", font=("Consolas", 12, "bold")).pack(anchor="w")

        pos_frame = ttk.Frame(frame)
        pos_frame.pack(fill="x", pady=(10, 14))
        ttk.Label(pos_frame, text="Opens:").pack(side="left")
        self._position_by_label = {label: pos for pos, label in settings.POSITION_LABELS.items()}
        self.position_var = tk.StringVar(
            value=settings.POSITION_LABELS[settings.load_popup_position()])
        ttk.Combobox(pos_frame, textvariable=self.position_var,
                     values=list(self._position_by_label),
                     state="readonly", width=20).pack(side="left", padx=(8, 0))

        # -- Buttons ---------------------------------------------------------
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Cancel", command=self._close).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Save", style="Accent.TButton", command=self._save).pack(side="right")

        self.win.bind("<Escape>", lambda e: self._close())

        center_window(self.win, parent)
        finish_dialog(self.win)

    def _close(self):
        close_dialog(self.win, self.parent)

    def _update_preview(self):
        hk = hotkey_mod.build_hotkey(
            self.ctrl_var.get(), self.alt_var.get(), self.shift_var.get(), self.key_var.get()
        )
        self.preview_var.set(hotkey_mod.format_hotkey_display(hk))

    def _save(self):
        if not self.key_var.get():
            MessageDialog(self.win, "Kaomoji Popup", "Please choose a key.")
            return

        new_hotkey = hotkey_mod.build_hotkey(
            self.ctrl_var.get(), self.alt_var.get(), self.shift_var.get(), self.key_var.get()
        )
        hotkey_changed = new_hotkey != self.hotkey_mgr.current

        # Only nag about missing modifiers if the hotkey is actually being
        # changed - otherwise a pure theme/position change would trigger it.
        if hotkey_changed and not (self.ctrl_var.get() or self.alt_var.get() or self.shift_var.get()):
            ConfirmDialog(
                self.win, "Kaomoji Popup",
                "No modifier selected — this hotkey may interfere with normal typing. "
                "Continue anyway?",
                on_confirm=lambda: self._commit(new_hotkey, hotkey_changed),
                confirm_text="Continue", danger=False,
            )
            return
        self._commit(new_hotkey, hotkey_changed)

    def _commit(self, new_hotkey: str, hotkey_changed: bool):
        if hotkey_changed:
            try:
                self.hotkey_mgr.start(new_hotkey)
            except Exception as e:
                MessageDialog(self.win, "Kaomoji Popup", f"Could not register hotkey: {e}")
                return
            hotkey_mod.save_hotkey(new_hotkey)

        new_mode = self._mode_by_label.get(self.theme_var.get(), themes.DEFAULT_THEME)
        theme_changed = new_mode != get_theme_mode()
        if theme_changed:
            settings.save_theme_mode(new_mode)

        new_position = self._position_by_label.get(self.position_var.get(), settings.DEFAULT_POSITION)
        position_changed = new_position != settings.load_popup_position()
        if position_changed:
            settings.save_popup_position(new_position)

        self._close()
        self.on_done(new_mode, theme_changed, position_changed)
