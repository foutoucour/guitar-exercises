import re
from datetime import UTC, datetime

import pytest

from guitar_exercises import version as version_module
from guitar_exercises.version import get_version

_VERSION_PATTERN = re.compile(r"^\d{4}\.\d{2}\.\d{2}\+[0-9a-f]{1,7}|^\d{4}\.\d{2}\.\d{2}\+dev$")


@pytest.fixture(autouse=True)
def clear_version_cache() -> None:
    get_version.cache_clear()


def test_version_format_is_yyyy_mm_dd_plus_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234def5678")

    today = datetime.now(UTC).strftime("%Y.%m.%d")
    assert get_version() == f"{today}+abc1234"


def test_version_uses_render_env_var_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123456789abcdef")

    version = get_version()

    assert version.endswith("+0123456")


def test_version_falls_back_to_dev_when_no_env_and_no_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)

    def fake_run(*_args: object, **_kwargs: object) -> object:
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(version_module.subprocess, "run", fake_run)

    version = get_version()

    assert version.endswith("+dev")


def test_version_matches_expected_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "deadbeefcafe")

    assert _VERSION_PATTERN.match(get_version())


def test_version_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "1111111")
    first = get_version()

    monkeypatch.setenv("RENDER_GIT_COMMIT", "2222222")
    second = get_version()

    assert first == second
