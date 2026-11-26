"""
Theme application (palette -> ttk styles), window-size constants, and the
small tkinter helper functions shared across dialogs and the main popup.

The palettes themselves live in kaomoji_popup/themes.py (tkinter-free).
"""
import tkinter as tk
from tkinter import ttk

from .. import themes

WINDOW_WIDTH = 560
WINDOW_HEIGHT = 480

# The live palette. Other modules do `from .theme import COLORS`, so this
# dict must never be rebound - _apply_palette() mutates it in place.
COLORS = dict(themes.PALETTES[themes.DEFAULT_THEME])

FONT_UI = ("Consolas", 11)
FONT_KAOMOJI = ("Consolas", 11)

_current_mode = themes.DEFAULT_THEME


def get_theme_mode() -> str:
    """The currently selected mode ("system", "mocha", "dark", "light")."""
    return _current_mode


def apply_theme(root: tk.Tk, mode: str = None):
    """Applies a theme. `mode=None` re-applies the current mode (useful for
    "system" to re-read the desktop colours)."""
    global _current_mode
    if mode is not None:
        _current_mode = themes.normalize_mode(mode)
    _apply_palette(root, themes.resolve_palette(_current_mode))


def refresh_system_theme(root: tk.Tk) -> bool:
    """In "system" mode: re-detects the desktop colours and re-applies the
    theme if they changed. Returns True if anything changed."""
    if _current_mode != themes.THEME_SYSTEM:
        return False
    palette = themes.resolve_palette(themes.THEME_SYSTEM)
    if palette == COLORS:
        return False
    _apply_palette(root, palette)
    return True


def _apply_palette(root: tk.Tk, palette: dict):
    COLORS.clear()
    COLORS.update(palette)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=COLORS["base"], foreground=COLORS["text"],
                    fieldbackground=COLORS["surface0"], font=FONT_UI)
    style.configure("TFrame", background=COLORS["base"])
    style.configure("TLabel", background=COLORS["base"], foreground=COLORS["text"])
    style.configure("TSeparator", background=COLORS["surface1"])
    style.configure("TButton", background=COLORS["surface0"], foreground=COLORS["text"],
                    borderwidth=0, padding=6)
    style.map("TButton",
              background=[("active", COLORS["surface1"]), ("pressed", COLORS["surface2"])])
    style.configure("Accent.TButton", background=COLORS["mauve"], foreground=COLORS["on_accent"])
    style.map("Accent.TButton",
              background=[("active", COLORS["lavender"]), ("pressed", COLORS["lavender"])])
    style.configure("TEntry", fieldbackground=COLORS["surface0"], foreground=COLORS["text"],
                    insertcolor=COLORS["text"], borderwidth=0)
    style.configure("TCombobox", fieldbackground=COLORS["surface0"], background=COLORS["surface0"],
                    foreground=COLORS["text"], arrowcolor=COLORS["text"])
    # The selection* entries stop clam from painting a default-blue highlight
    # over the text of a read-only combobox.
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["surface0"])],
              selectbackground=[("readonly", COLORS["surface0"])],
              selectforeground=[("readonly", COLORS["text"])])

    # clam draws a light 3D-style border around entries/lists; recolour it so
    # it blends into the theme instead of showing up as a white outline.
    for widget in ("TEntry", "TCombobox", "Treeview"):
        style.configure(widget, bordercolor=COLORS["surface1"],
                        lightcolor=COLORS["surface0"], darkcolor=COLORS["surface0"])

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
              foreground=[("selected", COLORS["on_accent"])])

    # Later option_add() calls win over earlier ones at the same priority,
    # so this also works when the theme is switched at runtime.
    root.option_add("*TCombobox*Listbox.background", COLORS["surface0"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["mauve"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["on_accent"])

    style.configure("Danger.TButton", background=COLORS["red"], foreground=COLORS["on_accent"])
    style.map("Danger.TButton",
              background=[("active", COLORS["red_hover"]), ("pressed", COLORS["red_hover"])])


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


def build_header(win: tk.Toplevel, title: str, on_close) -> tk.Frame:
    """Custom title bar for borderless windows: title, drag-to-move, and a
    close button. Must be created before the window's content is packed."""
    header = tk.Frame(win, bg=COLORS["mantle"], cursor="fleur", height=28)
    header.pack(fill="x", side="top")
    header.pack_propagate(False)

    title_lbl = tk.Label(header, text=title, bg=COLORS["mantle"], fg=COLORS["subtext0"],
                         font=("Consolas", 9))
    title_lbl.pack(side="left", padx=6, pady=4)

    close_btn = tk.Label(header, text="×", bg=COLORS["mantle"], fg=COLORS["subtext0"],
                         font=("Consolas", 12), cursor="arrow")
    close_btn.pack(side="right", padx=(0, 8), pady=2)
    close_btn.bind("<Button-1>", lambda e: on_close())
    close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=COLORS["red"]))
    close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=COLORS["subtext0"]))

    drag = {"x": 0, "y": 0}

    def start_drag(event):
        drag["x"], drag["y"] = event.x, event.y

    def do_drag(event):
        x = win.winfo_x() + (event.x - drag["x"])
        y = win.winfo_y() + (event.y - drag["y"])
        win.geometry(f"+{x}+{y}")

    for widget in (header, title_lbl):
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", do_drag)
    return header


def prepare_dialog(win: tk.Toplevel, title: str, on_close=None):
    """Makes a fresh Toplevel a borderless dialog in the popup's style.

    Why borderless (overrideredirect): the main popup is override-redirect,
    and on X11 such windows always stack above window-manager-managed ones.
    A normal dialog opened from the popup would therefore appear *behind*
    it. Making the dialog override-redirect too and raising it afterwards
    (finish_dialog) keeps it on top.
    """
    style_toplevel(win)
    win.title(title)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(highlightthickness=1, highlightbackground=COLORS["surface2"],
                  highlightcolor=COLORS["surface2"])
    build_header(win, f" {title}", on_close or win.destroy)


def finish_dialog(win: tk.Toplevel, retries: int = 20):
    """Call once the dialog's content is built and positioned: raises it,
    focuses it and makes it modal. The grab is retried because it fails
    until the window is actually mapped."""
    try:
        if not win.winfo_exists():
            return
        win.lift()
        win.focus_force()
        win.grab_set()
    except tk.TclError:
        if retries > 0:
            try:
                win.after(30, finish_dialog, win, retries - 1)
            except tk.TclError:
                pass


def close_dialog(win: tk.Toplevel, parent: tk.Misc = None):
    """Destroys a dialog and hands grab and focus back to its parent window."""
    try:
        win.grab_release()
    except tk.TclError:
        pass
    win.destroy()
    if parent is not None:
        try:
            parent.grab_set()
            parent.focus_force()
        except tk.TclError:
            pass


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