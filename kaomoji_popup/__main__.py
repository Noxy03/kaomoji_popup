"""
Application entry point. Run with `python -m kaomoji_popup`.

Threading rule (see DEV.md): only this poll_queue() loop, running on the
Tk main thread via root.after(), may call tkinter widgets, messagebox, or
webbrowser. Background threads (check_for_updates, the pynput listener)
must only push plain data onto a queue.Queue and return.
"""
import queue
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox

from . import config
from .hotkey import HotkeyManager, format_hotkey_display, load_hotkey
from .store import KaomojiStore
from .ui.popup import KaomojiPopup
from .ui.theme import apply_theme
from .updater import check_for_updates


def main():
    root = tk.Tk()
    root.withdraw()
    apply_theme(root)

    update_queue: "queue.Queue[dict]" = queue.Queue()
    threading.Thread(target=check_for_updates, args=(update_queue,), daemon=True).start()

    store = KaomojiStore(config.USER_DATA_FILE)
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

        try:
            info = update_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            # Safe here: we're on the main thread (called via root.after),
            # unlike inside check_for_updates() which runs in a background thread.
            if messagebox.askyesno(
                "Kaomoji Popup",
                f"A new version ({info['version']}) is available "
                f"(you have {config.CURRENT_VERSION}). Open the release page?",
            ):
                webbrowser.open(info["url"])

        root.after(50, poll_queue)

    poll_queue()
    print(f"Kaomoji Popup is running in the background. Hotkey: {format_hotkey_display(hotkey_mgr.current)}")
    print(f"Data file: {config.USER_DATA_FILE}")
    print("To exit, close this terminal window or press Ctrl+C.")
    root.mainloop()


if __name__ == "__main__":
    main()