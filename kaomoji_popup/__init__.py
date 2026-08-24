"""
Kaomoji/ASCII-Art Popup Picker.

Global Hotkey (default: Ctrl+Shift+Space) opens a small search window.
Typing filters live; pressing Enter or double-clicking automatically
inserts the selection at the cursor position in the previously active
window.

Entry point: `python -m kaomoji_popup` (see __main__.py).
Module layout is documented in DEV.md.

This file is intentionally kept free of imports from the rest of the
package: importing `kaomoji_popup` on its own should have no side
effects. Config/logging setup only runs once something actually
imports `kaomoji_popup.config` (directly, or transitively through
`store`, `hotkey`, `updater`, or `ui.*`).
"""
