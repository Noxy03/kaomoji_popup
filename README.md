# Kaomoji Popup

A lightweight, fast desktop tool in Python for searching and inserting kaomojis and ASCII art via a global hotkey.

---

## 🚀 Features

- **Global Hotkey:** Default `Ctrl+Alt+K` (or customizable via the menu / settings) to bring up the picker window system-wide.
- **Real-Time Filtering:** Live search across kaomoji characters, descriptions, and tags as you type.
- **Automatic Insertion:** Sends the selected kaomoji directly into the previously active text field.
- **Flexible Insertion Modes (`INSERT_MODE`):**
  - `"paste"` *(Default, recommended)*: Inserts the kaomoji via the clipboard (`Ctrl+V`) and restores the previous clipboard contents shortly after.
  - `"type"`: Simulates character-by-character typing (ideal for secured password fields or inputs that block copy-paste).
  - `"clipboard"`: Copies the kaomoji to the clipboard for manual insertion.
- **Built-in Management (UI & JSON):**
  - Add, edit, and delete kaomojis directly within the application.
  - Tag system for categorization (e.g., `joy`, `cat`, `anger`).
  - Stored in `kaomojis.json` inside the AppData/configuration directory (persists across restarts).
- **Favorites & Recent Entries:**
  - Dropdown filter for `⭐ Recently Used` (sorted by most recent use).
  - The most frequently/recently used kaomojis are highlighted with a `⭐` in the main view.
- **Modern Design:** Dark theme with an elegant **Catppuccin Mocha** color scheme.

---

## 🛠️ Usage & Shortcuts

| Action | Shortcut / Interaction |
| :--- | :--- |
| **Open / Close Popup** | Global hotkey (Default: `Ctrl+Alt+K` / `Ctrl+Alt+Space`) |
| **Search & Filter** | Type text into the search box or select a tag from the dropdown |
| **Navigate List** | `Down Arrow` (`↓`) from the search box |
| **Insert Entry** | `Enter` or `Double-click` on an entry |
| **Edit Entry** | Select entry → `Edit` button |
| **Delete Entry** | Select entry → `Delete` key or `Delete` button |
| **Add New Entry** | `+ Add` button |
| **Customize Hotkey** | `⚙ Hotkey` button |
| **Close Window** | `Escape` (without inserting) |

---

## 💻 Installation

### System Requirements

- Python 3.8 or newer

### Install Python Packages

```bash
pip install pynput pyperclip
```

#### OS-Specific Notes:

- **Windows:** Install Python from [python.org](https://www.python.org/) (make sure to check *Add Python to PATH*). Then run the above `pip` command in Command Prompt (`cmd`) or PowerShell.
- **Linux:** Requires `tkinter`. Included by default in many distributions; otherwise, install it via:
  - **Debian / Ubuntu / Mint:** `sudo apt install python3-tk`
  - **Arch Linux / Manjaro:** `sudo pacman -S tk`
  - **Fedora:** `sudo dnf install python3-tkinter`

---

## 🚀 Running & Configuration

### Start the Application

```bash
python kaomoji_popup.py
```

### Configuration & Customization

1. **Add Custom Kaomojis:**
   - Directly via the user interface using the `+ Add` button.
   - Or manually by editing `kaomojis.json` (created automatically in the AppData/config folder on first launch).
2. **Change Hotkey:**
   - Customize easily in the UI using the `⚙ Hotkey` button.
   - Alternatively, change the default value of the `HOTKEY` variable in the script (e.g., `"<ctrl>+<shift>+k"`).
3. **Change Insertion Behavior:**
   - Adjust the `INSERT_MODE` variable in the script (`"paste"`, `"type"`, or `"clipboard"`).
   - On slower systems, increase `INSERT_DELAY_MS` (e.g., to `250`) to ensure focus reliably returns to the previous window.

---

## 🔄 Setting Up Autostart

### Windows (Without Console Window)

1. Press `Win + R`, type `shell:startup`, and press `Enter`.
2. Create a new shortcut in this folder.
3. Set the target to:
   ```cmd
   pythonw.exe "C:\Path\to\kaomoji_popup.py"
   ```
   *(Use `pythonw.exe` instead of `python.exe` to prevent a console window from remaining open in the background).*

### Linux (systemd User Service)

1. Create the file `~/.config/systemd/user/kaomoji-popup.service`:

   ```ini
   [Unit]
   Description=Kaomoji Popup
   After=graphical-session.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/kaomoji_popup.py
   Restart=on-failure

   [Install]
   WantedBy=default.target
   ```

2. Enable and start the service immediately:

   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now kaomoji-popup.service
   ```

---

## ⚠️ Known Limitations & Notes

- **Wayland (Linux):** `pynput` relies on X11 APIs for global hotkeys and simulated key combinations (`Ctrl+V` / typing). Under a pure Wayland session (e.g., GNOME/KDE without XWayland fallback), functionality may be restricted for security reasons. A workaround can be implemented using compositor tools like `ydotool`.
- **Password & Security Fields:** Some secure input fields or terminal emulators block clipboard pasting. In these cases, switching to `"type"` mode (`INSERT_MODE = "type"`) or pasting manually with `Ctrl+V` is recommended.
- **Multi-Monitor Setups:** The popup opens at the current cursor/mouse position.
- **Focus Delay:** The short delay (`INSERT_DELAY_MS`) ensures the operating system restores focus to the previous application window before key inputs are simulated.

---

## 🔜 Coming Soon

- Close Button
- Change Pop-Up opening mode: open in the middle of the screen
- Open on correct monitor
- Option to close on background-click
