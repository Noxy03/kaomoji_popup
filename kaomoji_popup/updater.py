"""
GitHub release update check. Runs in a background thread - see the
threading rule in DEV.md: this module must never touch tkinter or call
webbrowser directly. It only does network I/O and hands results back via
a queue.Queue, which the main thread polls.
"""
import json
import queue
import urllib.error
import urllib.request

from . import config


def _version_tuple(v: str):
    """Turns '1.10.2' into (1, 10, 2) so versions compare numerically,
    not lexicographically ('1.10.0' > '1.9.0' is False as plain strings!)."""
    parts = []
    for p in v.split("."):
        digits = "".join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_updates(result_queue: "queue.Queue[dict]"):
    """Runs in a background thread - must NOT touch tkinter (messagebox) or
    call webbrowser directly from here. It only does network I/O and hands
    the result back to the main thread via result_queue, which the main
    loop polls with root.after()."""
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KaomojiApp"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").lstrip("v")

            if latest_version and _version_tuple(latest_version) > _version_tuple(config.CURRENT_VERSION):
                result_queue.put({
                    "version": latest_version,
                    "url": data.get("html_url"),
                })
    except (urllib.error.URLError, TimeoutError) as e:
        # Expected when offline or the API is briefly unreachable - not worth
        # more than a debug note.
        config.logger.debug("Update check skipped (network issue): %s", e)
    except Exception:
        # Anything else (e.g. GitHub changed its JSON schema, unexpected
        # KeyError) is a real bug, not just "offline" - keep it out of the
        # user's face but still capture it for diagnosis.
        config.logger.warning("Update check failed unexpectedly", exc_info=True)