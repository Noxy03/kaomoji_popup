"""
Catppuccin Mocha color palette, fonts, window-size constants, and the
small tkinter helper functions shared across dialogs and the main popup.
"""
import tkinter as tk
from tkinter import ttk

WINDOW_WIDTH = 560
WINDOW_HEIGHT = 480

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