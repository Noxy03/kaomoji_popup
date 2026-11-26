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
- **Window Position:** Under `⚙ Settings → Window` choose whether the popup opens **near the cursor** (default) or in the **center of the screen**. "Screen" means the monitor the mouse cursor is on, so it works on multi-monitor setups; the popup never leaves that monitor. On Linux the monitor layout is read via `xrandr` (package `x11-xserver-utils` on Debian/Ubuntu, usually preinstalled); without it the popup falls back to the whole desktop.
- **Themes:** Switch under `⚙ Settings → Theme` between **Catppuccin Mocha** (default), **Dark**, **Light** and **System**. "System" follows your desktop: on KDE Plasma it uses the colors of your active color scheme (`~/.config/kdeglobals`), on GNOME and other desktops it follows the dark/light preference, on Windows the app theme setting. It is re-checked every time the popup opens, so a change of your desktop theme is picked up without restarting.

---

## 🛠️ Usage & Shortcuts

| Action                       | Shortcut / Interaction                                          |
|:---------------------------- |:--------------------------------------------------------------- |
| **Open / Close Popup**       | Global hotkey (Default: `Ctrl+Shift+Space`)                     |
| **Search & Filter**          | Type text into the search box or select a tag from the dropdown |
| **Navigate List**            | `Up / Down Arrow` (`↑ / ↓`) from the search box                 |
| **Insert Entry**             | `Enter` or `Click` on an entry                                  |
| **Edit Entry**               | Select entry → `Edit` button                                    |
| **Delete Entry**             | Select entry → `Delete` key or `Delete` button                  |
| **Add New Entry**            | `+ Add` button                                                  |
| **Hotkey, Theme & Position** | `⚙ Settings` button                                             |
| **Close Window**             | `Escape`, the `×` button top-right, or press the hotkey again   |

---

## 💻 Installation

### Option 1: Standalone Executable (Windows & Linux - Recommended)

Every release on the [Releases](https://github.com/Noxy03/kaomoji_popup/releases) page is built automatically by GitHub Actions and contains one file per platform. No Python installation required.

**Windows**

1. Download `kaomoji_popup.exe`.
2. Run it.

**Linux (x86_64)**

1. Download `kaomoji_popup-linux-x86_64.tar.gz`.
2. Extract and start it:

   ```bash
   tar -xzf kaomoji_popup-linux-x86_64.tar.gz
   ./kaomoji_popup
   ```
3. If the execute bit is missing, run `chmod +x kaomoji_popup` first.

The Linux binary is built on Ubuntu 22.04 so it runs on most current distributions. It needs an X11 session (see *Known Limitations & Notes* below). ARM devices such as the Raspberry Pi are not supported by the prebuilt binary - run from source instead.

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
python -m kaomoji_popup
```

### Building the Executable Locally

Releases are built by GitHub Actions (see *For Maintainers* below), so you normally don't need this. To build a standalone binary on your own machine:

```bash
pip install -r requirements-dev.txt pyinstaller
pyinstaller --onefile --noconsole --name kaomoji_popup --paths . \
  --add-data "kaomoji_popup/resources/default_kaomojis.json:kaomoji_popup/resources" \
  run_kaomoji_popup.py
```

On Windows, use `;` instead of `:` in the `--add-data` argument. The result is in `dist/`.

---

## 🔄 Setting Up Autostart

### Windows

1. Press `Win + R`, type `shell:startup`, and press `Enter`.
2. Create a shortcut to `kaomoji_popup.exe` inside this folder.

### Linux (most desktop environments)

Create `~/.config/autostart/kaomoji_popup.desktop` with the path to your binary:

```ini
[Desktop Entry]
Type=Application
Name=Kaomoji Popup
Exec=/path/to/kaomoji_popup
```

On KDE Plasma you can alternatively use *System Settings → Autostart*.

---

## 🗃️ Data & Storage

Your personal kaomoji list lives in `kaomojis.json` inside the app's config folder (the path is printed to the console on startup):

| OS          | Location                                                                |
|:----------- |:----------------------------------------------------------------------- |
| **Windows** | `%APPDATA%\kaomoji_popup\`                                              |
| **Linux**   | `$XDG_CONFIG_HOME/kaomoji_popup/` (default: `~/.config/kaomoji_popup/`) |

The same folder also holds `settings.json` (hotkey and theme) and the log file `kaomoji_popup.log`. Each entry has a stable internal `id` — entries you create yourself are marked `"origin": "user"`, entries that came from the built-in list are marked `"origin": "default"`.

You never need to touch this file by hand; it's shown here just so you know your customizations, deletions, and usage history are preserved safely across updates.

---

## 🔧 For Maintainers: Updating `default_kaomojis.json`

When adding new entries to the bundled default kaomoji list, new entries are merged into every user's personal list on their next app start — **without** duplicating entries they already have and **without** un-deleting ones they removed on purpose. This works because every default entry carries a stable `id` that, once assigned, must never change or be reused.

Workflow when extending the list:

1. Add your new kaomojis to `kaomoji_popup/resources/default_kaomojis.json` as usual (no need to set an `id` by hand).
2. Run the helper script to assign ids to the new entries only — existing ids are never touched:

   ```bash
   python assign_default_ids.py kaomoji_popup/resources/default_kaomojis.json
   ```
3. Review the diff and commit.

### Publishing a release

Releases are created automatically when a version tag is pushed. Order matters:

```bash
# 1. Bump CURRENT_VERSION in kaomoji_popup/config.py (e.g. "1.1.0"), then:
git add kaomoji_popup/config.py
git commit -m "Bump version to 1.1.0"

# 2. Tag the commit (tag = "v" + CURRENT_VERSION) and push branch and tag
git tag v1.1.0
git push origin main
git push origin v1.1.0
```

The workflow in `.github/workflows/release.yml` then runs the tests, checks that the tag matches `CURRENT_VERSION`, builds the Windows `.exe` and the Linux `.tar.gz` in parallel, and attaches both to a new GitHub Release. Progress is visible in the repository's **Actions** tab. See `DEV.md` for details and pitfalls.

---

## ⚠️ Known Limitations & Notes

- **Wayland (Linux):** `pynput` relies on X11 APIs for global hotkeys and simulated key combinations (`Ctrl+V` / typing). Under a pure Wayland session (e.g., GNOME/KDE without XWayland fallback), functionality may be restricted for security reasons. A workaround can be implemented using compositor tools like `ydotool`.
- **Password & Security Fields:** Some secure input fields or terminal emulators block clipboard pasting. In these cases, switching to `"type"` mode (`INSERT_MODE = "type"`) or pasting manually with `Ctrl+V` is recommended.
- **Linux binary:** Built for x86_64 on Ubuntu 22.04 (glibc 2.35 or newer). Older distributions or ARM devices should run from source.
- **Windows SmartScreen:** The `.exe` is not code-signed yet, so Windows Defender / SmartScreen may show a warning on first start.
- **Multi-Monitor Setups:** The popup opens on the monitor the cursor is on (near the cursor or centered, see *Window Position*). Monitor detection on Windows is untested on setups with mixed DPI scaling.

---

## 🔜 Coming Soon

- Option to close on background-click
- Code signing for the Windows `.exe` via GitHub Actions
