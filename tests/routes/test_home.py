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


def test_home_footer_renders_version(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert 'class="sitefoot"' in response.text
    assert 'class="sitefoot-version"' in response.text


def test_base_template_loads_shared_auto_advance_script(client: TestClient) -> None:
    # auto-advance.js owns the site-wide "wait between exercises" delay; every
    # page must load it so individual feedback fragments can call into the
    # shared helper.
    response = client.get("/")
    assert "/static/js/auto-advance.js" in response.text


def test_shared_auto_advance_script_is_served(client: TestClient) -> None:
    response = client.get("/static/js/auto-advance.js")
    assert response.status_code == 200
    body = response.text
    # The whole point of centralising the helper is a single tunable constant.
    assert "autoAdvanceMs" in body
    assert "advanceTo" in body
