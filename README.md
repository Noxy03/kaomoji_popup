# Kaomoji Popup

A lightweight, fast desktop tool in Python for searching and inserting kaomojis and ASCII art via a global hotkey.

---

## 🚀 Features

- **Global Hotkey:** Default `Ctrl+Shift+Space` (or customizable via the menu / settings) to bring up the picker window system-wide.
- **Real-Time Filtering:** Live search across kaomoji characters, descriptions, and tags as you type.
- **Automatic Insertion:** Sends the selected kaomoji directly into the previously active text field.
- **Flexible Insertion Modes (`INSERT_MODE`):**
  - `"paste"` *(Default, recommended)*: Inserts the kaomoji via the clipboard (`Ctrl+V`) and restores the previous clipboard contents shortly after.
  - `"type"`: Simulates character-by-character typing (ideal for secured password fields or inputs that block copy-paste).
  - `"clipboard"`: Copies the kaomoji to the clipboard for manual insertion.
- **Built-in Management (UI & JSON):**
  - Add, edit, and delete kaomojis directly within the application.
  - Duplicate protection: adding or renaming an entry to match an existing kaomoji is blocked.
  - Tag system for categorization (e.g., `joy`, `cat`, `anger`).
  - Stored in `kaomojis.json` inside the AppData/configuration directory (persists across restarts).
- **Favorites & Recent Entries:**
  - Dropdown filter for `⭐ Recently Used` (sorted by most recent use).
  - The most frequently/recently used kaomojis are highlighted with a `⭐` in the main view and automatically float to the top of the full list — reordering is computed fresh every time the popup opens, so it's always up to date.
- **Automatic Update Check:** On startup, the app checks GitHub Releases for a newer version and asks (via a dialog) whether to open the release page — it never opens anything without confirmation.
- **New Default Kaomojis via Update:** When the developer adds new entries to the built-in kaomoji list, they're merged in automatically the next time you start the app — without duplicating kaomojis you already have and without bringing back ones you deliberately deleted.
- **Modern Design:** Dark theme with an elegant **Catppuccin Mocha** color scheme.

---

## 🛠️ Usage & Shortcuts

| Action | Shortcut / Interaction                                          |
| :--- |:----------------------------------------------------------------|
| **Open / Close Popup** | Global hotkey (Default: `Ctrl+Shift+Space`)                     |
| **Search & Filter** | Type text into the search box or select a tag from the dropdown |
| **Navigate List** | `Up / Down Arrow` (`↑ / ↓`) from the search box                 |
| **Insert Entry** | `Enter` or `Click` on an entry                                  |
| **Edit Entry** | Select entry → `Edit` button                                    |
| **Delete Entry** | Select entry → `Delete` key or `Delete` button                  |
| **Add New Entry** | `+ Add` button                                                  |
| **Customize Hotkey** | `⚙ Hotkey` button                                               |
| **Close Window** | `Escape`, the `×` button top-right, or press the hotkey again   |

---

## 💻 Installation

### Option 1: Standalone Executable (Windows - Recommended)

1. Download the latest `kaomoji_popup.exe` from the [Releases](https://github.com/Noxy03/kaomoji_popup/releases) page.
2. Run the `.exe` file. No Python installation required!

---

### Option 2: Running from Source

#### Requirements
- Python 3.8 or newer

#### Install Dependencies
```bash
pip install pynput pyperclip
```

#### OS-Specific Notes:

- **Windows:** Install Python from [python.org](https://www.python.org/) (make sure to check *Add Python to PATH*). Then run the above `pip` command in Command Prompt (`cmd`) or PowerShell.
- **Linux:** Requires `tkinter`. Included by default in many distributions; otherwise, install it via:
  - **Debian / Ubuntu / Mint:** `sudo apt install python3-tk`
  - **Arch Linux / Manjaro:** `sudo pacman -S tk`
  - **Fedora:** `sudo dnf install python3-tkinter`

### Start the Application

```bash
python kaomoji_popup.py
```

### Building the Executable
To build a single standalone .exe bundle with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "default_kaomojis.json;." kaomoji_popup.py
```

---

## 🔄 Setting Up Autostart

### Windows

1. Press `Win + R`, type `shell:startup`, and press `Enter`.
2. Create a shortcut to `kaomoji_popup.exe` inside this folder.

---

## 🗃️ Data & Storage

Your personal kaomoji list lives in `kaomojis.json` inside the app's AppData/config folder (path is printed to the console on startup). Each entry has a stable internal `id` — entries you create yourself are marked `"origin": "user"`, entries that came from the built-in list are marked `"origin": "default"`.

You never need to touch this file by hand; it's shown here just so you know your customizations, deletions, and usage history are preserved safely across updates.

---

## 🔧 For Maintainers: Updating `default_kaomojis.json`

When adding new entries to the bundled default kaomoji list, new entries are merged into every user's personal list on their next app start — **without** duplicating entries they already have and **without** un-deleting ones they removed on purpose. This works because every default entry carries a stable `id` that, once assigned, must never change or be reused.

Workflow when extending the list:

1. Add your new kaomojis to `default_kaomojis.json` as usual (no need to set an `id` by hand).
2. Run the helper script to assign ids to the new entries only — existing ids are never touched:
   ```bash
   python assign_default_ids.py default_kaomojis.json
   ```
3. Review the diff, commit, and publish the release as usual.

---

## ⚠️ Known Limitations & Notes

- **Wayland (Linux):** `pynput` relies on X11 APIs for global hotkeys and simulated key combinations (`Ctrl+V` / typing). Under a pure Wayland session (e.g., GNOME/KDE without XWayland fallback), functionality may be restricted for security reasons. A workaround can be implemented using compositor tools like `ydotool`.
- **Password & Security Fields:** Some secure input fields or terminal emulators block clipboard pasting. In these cases, switching to `"type"` mode (`INSERT_MODE = "type"`) or pasting manually with `Ctrl+V` is recommended.
- **Multi-Monitor Setups:** The popup opens at the current cursor/mouse position.

---

## 🔜 Coming Soon

- Change Pop-Up opening mode: open in the middle of the screen
- Open on correct monitor
- Option to close on background-click