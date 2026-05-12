from fastapi.testclient import TestClient


def test_home_returns_200_and_lists_chord_notes_exercise(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "Chord Note Recognition" in body
    assert 'href="/exercises/chord-notes"' in body


def test_home_renders_with_exercise_card_class(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "exercise-card" in response.text
