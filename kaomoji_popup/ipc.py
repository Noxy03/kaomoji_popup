"""
Optional Unix-domain socket trigger so external scripts (e.g. a launcher
or toolbox) can ask an already-running instance to show the popup.
"""
import os
import socket
import sys
import threading

SOCK_PATH = "/tmp/kaomoji_popup.sock"


def wants_show_on_start() -> bool:
    return "--show" in sys.argv[1:]


def start_trigger_listener(on_trigger) -> None:
    """Starts a daemon thread listening for b'show' on SOCK_PATH.

    `on_trigger` must be thread-safe (e.g. pushing onto a queue.Queue),
    never touching tkinter directly.
    """
    if os.path.exists(SOCK_PATH):
        try:
            os.unlink(SOCK_PATH)
        except OSError:
            pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCK_PATH)
    server.listen(4)
    server.settimeout(0.5)

    def _serve() -> None:
        try:
            while True:
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    data = conn.recv(64)
                    if data.strip() == b"show":
                        on_trigger()
        finally:
            try:
                server.close()
            except OSError:
                pass
            if os.path.exists(SOCK_PATH):
                try:
                    os.unlink(SOCK_PATH)
                except OSError:
                    pass

    threading.Thread(target=_serve, daemon=True).start()