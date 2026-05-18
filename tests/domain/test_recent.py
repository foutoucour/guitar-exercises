from guitar_exercises.domain.recent import (
    RECENT_WINDOW,
    parse_recent,
    push_recent,
    serialize_recent,
)


def test_parse_recent_returns_empty_list_for_missing_cookie() -> None:
    assert parse_recent(None) == []
    assert parse_recent("") == []


def test_parse_recent_strips_whitespace_and_empties() -> None:
    assert parse_recent("a, b ,, c") == ["a", "b", "c"]


def test_parse_recent_deduplicates_preserving_first_occurrence() -> None:
    assert parse_recent("a,b,a,c") == ["a", "b", "c"]


def test_parse_recent_caps_at_window() -> None:
    raw = ",".join(f"k{i}" for i in range(RECENT_WINDOW + 10))
    parsed = parse_recent(raw)
    assert len(parsed) == RECENT_WINDOW
    assert parsed[0] == "k0"


def test_push_recent_prepends_new_key() -> None:
    assert push_recent(["b", "c"], "a") == ["a", "b", "c"]


def test_push_recent_moves_repeat_to_front() -> None:
    # Re-asking the same key should bump it to the most-recent slot rather
    # than creating a duplicate entry.
    assert push_recent(["a", "b", "c"], "b") == ["b", "a", "c"]


def test_push_recent_enforces_window() -> None:
    seed = [f"k{i}" for i in range(RECENT_WINDOW)]
    pushed = push_recent(seed, "new")
    assert len(pushed) == RECENT_WINDOW
    assert pushed[0] == "new"
    # The oldest entry must be dropped to stay within the window.
    assert seed[-1] not in pushed


def test_serialize_round_trip() -> None:
    original = ["a", "b", "c"]
    assert parse_recent(serialize_recent(original)) == original
