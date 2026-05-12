import random
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.main import create_app


@pytest.fixture
def seeded_rng() -> random.Random:
    return random.Random(42)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
