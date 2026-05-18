"""Generic recent-question history for exercise pickers.

Each exercise tracks the keys of recently asked questions so the picker can
avoid repeating them. A "key" is a string that uniquely identifies a single
question in that exercise (e.g. a chord id, or a ``"<string>:<fret>"`` pair).

The same primitives serve every exercise — only the key function changes.
"""

from collections.abc import Iterable

RECENT_WINDOW = 25


def parse_recent(cookie_value: str | None) -> list[str]:
    """Decode a comma-joined cookie into an ordered list of unique keys.

    Keys are returned most-recent first, capped at :data:`RECENT_WINDOW`.
    Empty or malformed entries are silently skipped — the cookie is
    user-controlled, so we accept best-effort.
    """
    if not cookie_value:
        return []
    parsed: list[str] = []
    for raw in cookie_value.split(","):
        key = raw.strip()
        if not key or key in parsed:
            continue
        parsed.append(key)
        if len(parsed) >= RECENT_WINDOW:
            break
    return parsed


def push_recent(recent: Iterable[str], key: str) -> list[str]:
    """Return ``recent`` with ``key`` prepended, deduplicated, window-trimmed."""
    return [key, *(k for k in recent if k != key)][:RECENT_WINDOW]


def serialize_recent(recent: Iterable[str]) -> str:
    return ",".join(recent)
