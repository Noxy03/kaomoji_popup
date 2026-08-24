"""
tkinter-dependent UI layer: theme (colors/fonts/window helpers), dialogs
(add/edit/confirm/settings), and the main popup window.

Nothing outside kaomoji_popup.ui should need a real display to import -
KaomojiStore (store.py) and the hotkey/updater logic stay in the parent
package specifically so they can be tested headlessly (see DEV.md).
"""
