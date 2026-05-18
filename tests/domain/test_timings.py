from guitar_exercises.domain.timings import (
    MAX_ELAPSED_MS,
    TIMINGS_WINDOW,
    Timing,
    average_correct_ms,
    current_streak,
    parse_best_streak,
    parse_timings,
    push_timing,
    serialize_timings,
    update_best_streak,
)


def test_parse_timings_returns_empty_list_for_missing_cookie() -> None:
    assert parse_timings(None) == []
    assert parse_timings("") == []


def test_parse_timings_decodes_correct_and_incorrect_entries() -> None:
    parsed = parse_timings("1:2500|0:4000|1:1800")
    assert parsed == [
        Timing(correct=True, elapsed_ms=2500),
        Timing(correct=False, elapsed_ms=4000),
        Timing(correct=True, elapsed_ms=1800),
    ]


def test_parse_timings_skips_malformed_entries() -> None:
    parsed = parse_timings("1:2000|bad|2:5|1:abc||0:1500")
    assert parsed == [
        Timing(correct=True, elapsed_ms=2000),
        Timing(correct=False, elapsed_ms=1500),
    ]


def test_parse_timings_rejects_out_of_range_ms() -> None:
    # Anything past MAX_ELAPSED_MS is implausible and silently dropped.
    raw = f"1:{MAX_ELAPSED_MS + 1}|1:500"
    assert parse_timings(raw) == [Timing(correct=True, elapsed_ms=500)]


def test_parse_timings_caps_at_window() -> None:
    raw = "|".join(f"1:{i}" for i in range(TIMINGS_WINDOW + 10))
    parsed = parse_timings(raw)
    assert len(parsed) == TIMINGS_WINDOW
    assert parsed[0].elapsed_ms == 0


def test_serialize_uses_pipe_separator_to_avoid_cookie_quoting() -> None:
    # Comma would force http.cookies to wrap the whole value in quotes and
    # escape commas as \054 — pipe is in LegalChars and round-trips raw.
    serialized = serialize_timings(
        [Timing(correct=True, elapsed_ms=1000), Timing(correct=False, elapsed_ms=2000)]
    )
    assert "," not in serialized
    assert serialized == "1:1000|0:2000"


def test_push_timing_prepends_new_entry() -> None:
    seed = [Timing(correct=True, elapsed_ms=1000)]
    pushed = push_timing(seed, correct=False, elapsed_ms=4200)
    assert pushed[0] == Timing(correct=False, elapsed_ms=4200)
    assert pushed[1] == seed[0]


def test_push_timing_enforces_window() -> None:
    seed = [Timing(correct=True, elapsed_ms=i) for i in range(TIMINGS_WINDOW)]
    pushed = push_timing(seed, correct=True, elapsed_ms=9999)
    assert len(pushed) == TIMINGS_WINDOW
    assert pushed[0].elapsed_ms == 9999
    # The oldest entry must be dropped to stay within the window.
    assert seed[-1] not in pushed


def test_push_timing_clamps_extreme_values() -> None:
    pushed = push_timing([], correct=True, elapsed_ms=10**9)
    assert pushed[0].elapsed_ms == MAX_ELAPSED_MS
    pushed_neg = push_timing([], correct=True, elapsed_ms=-50)
    assert pushed_neg[0].elapsed_ms == 0


def test_serialize_timings_round_trip() -> None:
    original = [
        Timing(correct=True, elapsed_ms=2500),
        Timing(correct=False, elapsed_ms=4000),
    ]
    assert parse_timings(serialize_timings(original)) == original


def test_average_correct_ms_ignores_incorrects() -> None:
    timings = [
        Timing(correct=True, elapsed_ms=2000),
        Timing(correct=False, elapsed_ms=10_000),
        Timing(correct=True, elapsed_ms=4000),
    ]
    assert average_correct_ms(timings) == 3000


def test_average_correct_ms_returns_none_when_no_corrects() -> None:
    assert average_correct_ms([]) is None
    assert average_correct_ms([Timing(correct=False, elapsed_ms=500)]) is None


def test_current_streak_counts_trailing_corrects() -> None:
    # Most-recent-first storage: streak walks from index 0 forward.
    timings = [
        Timing(correct=True, elapsed_ms=1),
        Timing(correct=True, elapsed_ms=2),
        Timing(correct=True, elapsed_ms=3),
        Timing(correct=False, elapsed_ms=4),
        Timing(correct=True, elapsed_ms=5),
    ]
    assert current_streak(timings) == 3


def test_current_streak_is_zero_when_last_answer_is_wrong() -> None:
    timings = [
        Timing(correct=False, elapsed_ms=4),
        Timing(correct=True, elapsed_ms=5),
    ]
    assert current_streak(timings) == 0


def test_current_streak_is_zero_for_empty() -> None:
    assert current_streak([]) == 0


def test_parse_best_streak_handles_missing_and_invalid() -> None:
    assert parse_best_streak(None) == 0
    assert parse_best_streak("") == 0
    assert parse_best_streak("not-a-number") == 0
    assert parse_best_streak("7") == 7


def test_update_best_streak_is_monotonic() -> None:
    assert update_best_streak(3, 5) == 5
    assert update_best_streak(7, 2) == 7
    assert update_best_streak(0, 0) == 0
