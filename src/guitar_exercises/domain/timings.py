"""Per-exercise answer-time history for the session-only stats widget.

Each exercise tracks the player's recent answer times in a cookie so the page
can show a small "evolution" widget (chip row, streak, average). State is
session-scoped — there is no database or auth.

Entries are stored most-recent-first as ``"<c>:<ms>"`` pairs joined by ``|``,
where ``c`` is ``1`` for a correct answer and ``0`` for a wrong one and ``ms``
is the elapsed milliseconds. The pipe separator is in ``http.cookies``'
LegalChars set, so the value round-trips through Set-Cookie unquoted —
unlike a comma, which Python escapes as ``\\054``.
"""

from collections.abc import Iterable
from dataclasses import dataclass

TIMINGS_WINDOW = 25
MAX_ELAPSED_MS = 10 * 60 * 1000
_SEPARATOR = "|"


@dataclass(frozen=True, slots=True)
class Timing:
    correct: bool
    elapsed_ms: int


def parse_timings(cookie_value: str | None) -> list[Timing]:
    """Decode a comma-joined cookie into an ordered list of timings.

    Most recent first, capped at :data:`TIMINGS_WINDOW`. Malformed entries are
    silently skipped — the cookie is user-controlled, so we accept best-effort.
    """
    if not cookie_value:
        return []
    parsed: list[Timing] = []
    for raw in cookie_value.split(_SEPARATOR):
        entry = _parse_entry(raw)
        if entry is None:
            continue
        parsed.append(entry)
        if len(parsed) >= TIMINGS_WINDOW:
            break
    return parsed


def _parse_entry(raw: str) -> Timing | None:
    parts = raw.strip().split(":")
    if len(parts) != 2:
        return None
    flag, ms_str = parts[0].strip(), parts[1].strip()
    if flag not in ("0", "1") or not ms_str.isdigit():
        return None
    ms = int(ms_str)
    if ms < 0 or ms > MAX_ELAPSED_MS:
        return None
    return Timing(correct=flag == "1", elapsed_ms=ms)


def push_timing(timings: Iterable[Timing], correct: bool, elapsed_ms: int) -> list[Timing]:
    """Prepend a new entry, window-trim. Clamps ``elapsed_ms`` to a sane range."""
    clamped = max(0, min(elapsed_ms, MAX_ELAPSED_MS))
    new_entry = Timing(correct=correct, elapsed_ms=clamped)
    return [new_entry, *timings][:TIMINGS_WINDOW]


def serialize_timings(timings: Iterable[Timing]) -> str:
    return _SEPARATOR.join(f"{1 if t.correct else 0}:{t.elapsed_ms}" for t in timings)


def average_correct_ms(timings: Iterable[Timing]) -> int | None:
    """Mean of correct-answer elapsed times, rounded. ``None`` if no corrects."""
    correct_times = [t.elapsed_ms for t in timings if t.correct]
    if not correct_times:
        return None
    return round(sum(correct_times) / len(correct_times))


def current_streak(timings: Iterable[Timing]) -> int:
    """Count of trailing corrects from the most recent entry.

    ``timings`` is most-recent-first, so we just walk from index 0 until a
    wrong answer or the end of the window.
    """
    count = 0
    for t in timings:
        if not t.correct:
            return count
        count += 1
    return count


def parse_best_streak(cookie_value: str | None) -> int:
    """Decode the best-streak cookie. Returns ``0`` for missing/invalid."""
    if not cookie_value:
        return 0
    raw = cookie_value.strip()
    if not raw.isdigit():
        return 0
    return int(raw)


def update_best_streak(previous_best: int, new_streak: int) -> int:
    return max(previous_best, new_streak)
