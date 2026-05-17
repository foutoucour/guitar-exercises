import os
import subprocess
from datetime import UTC, datetime
from functools import lru_cache

_SHORT_SHA_LEN = 7


def _resolve_commit() -> str:
    commit = os.getenv("RENDER_GIT_COMMIT")
    if commit:
        return commit[:_SHORT_SHA_LEN]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return "dev"
    return result.stdout.strip() or "dev"


def _build_version() -> str:
    date = datetime.now(UTC).strftime("%Y.%m.%d")
    return f"{date}+{_resolve_commit()}"


@lru_cache(maxsize=1)
def get_version() -> str:
    """Return the app version as ``YYYY.MM.DD+<commit>``.

    Resolved once at first call. The date is the process boot date in UTC; on
    Render this approximates the deploy date since each deploy restarts the
    service. The commit comes from the ``RENDER_GIT_COMMIT`` env var when set,
    otherwise from ``git rev-parse`` for local dev, falling back to ``dev``.
    """
    return _build_version()
