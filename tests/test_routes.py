import json
import re
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from firstcommit import game
from firstcommit.web import routes

STATIC = Path(routes.__file__).parent / "static"
LEVELS = Path(game.__file__).parent / "levels"
HEADER = "X-FirstCommit-Token"


@dataclass(frozen=True)
class Site:
    """A running server: its address and the access key from its link."""

    url: str
    token: str


@pytest.fixture
def site() -> Iterator[Site]:
    """
    Run the game's server on a free port, on a thread, for one test.

    Yields
    ------
    Site
        Its address and access key.
    """
    server, link = routes.create_server(0)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    base, token = link.split("/#token=")
    yield Site(base, token)
    server.shutdown()
    server.server_close()


def call(site: Site, path: str, body: Any = None, token: str | None = None) -> tuple[int, dict[str, Any], str]:
    """
    Send one request the way the page does, with the key in the token header.

    Parameters
    ----------
    site : Site
        The running server.
    path : str
        Path and query.
    body : Any
        JSON body to POST, or None to GET.
    token : str | None
        Key to send instead of the site's own.

    Returns
    -------
    tuple[int, dict[str, Any], str]
        Status, response headers and body text.
    """
    data = None if body is None else json.dumps(body).encode()
    headers = {HEADER: site.token if token is None else token, "Content-Type": "application/json"}
    request = urllib.request.Request(
        site.url + path, data=data, headers=headers, method="GET" if body is None else "POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, dict(response.headers), response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read().decode()


def api(site: Site, path: str, body: Any = None) -> tuple[int, Any]:
    """
    Call a JSON route and decode its reply.

    Parameters
    ----------
    site : Site
        The running server.
    path : str
        Path and query.
    body : Any
        JSON body to POST, or None to GET.

    Returns
    -------
    tuple[int, Any]
        Status and decoded reply.
    """
    status, _, text = call(site, path, body)
    return status, json.loads(text)


def record(
    monkeypatch: pytest.MonkeyPatch, name: str, result: Any = None, error: Exception | None = None
) -> list[tuple[Any, ...]]:
    """
    Replace one `game` function with a stand-in that remembers its arguments.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.
    name : str
        Name of the `game` function.
    result : Any
        What the stand-in returns.
    error : Exception | None
        What it raises instead, if anything.

    Returns
    -------
    list[tuple[Any, ...]]
        The positional arguments of every call, in order.
    """
    calls: list[tuple[Any, ...]] = []

    def stand_in(*args: Any) -> Any:
        calls.append(args)
        if error is not None:
            raise error
        return result

    monkeypatch.setattr(game, name, stand_in)
    return calls


LEVEL_VIEW = {
    "id": "some-level",
    "chapter": "basics",
    "chapter_title": "The three areas",
    "title": "A level",
    "difficulty": 1,
    "xp": 100,
    "briefing": [{"kind": "para", "spans": [{"text": "Do it.", "code": False}]}],
    "steps": [],
    "hints_total": 2,
    "has_lesson": False,
}


def test_the_server_names_the_game_and_asks_for_the_key_from_its_link(site: Site) -> None:
    refused = call(site, "/api/status", token="wrong")
    assert refused[0] == 403
    assert "`firstcommit`" in refused[2]
    assert refused[1]["Server"].startswith("FirstCommit")


def test_the_page_loads_nothing_from_outside_the_server(site: Site) -> None:
    status, headers, _ = call(site, "/")
    assert status == 200
    assert "https:" not in headers["Content-Security-Policy"]
    for path in sorted(STATIC.iterdir()):
        text = path.read_text()
        assert not re.search(r"https?://(?!www\.w3\.org/2000/svg|localhost)", text), path.name


def test_every_file_the_page_references_is_served(site: Site) -> None:
    _, _, page = call(site, "/")
    names = re.findall(r'(?:src|href)="/static/([^"]+)"', page)
    assert "app.js" in names and "client.js" in names and "terminal.js" in names
    for name in names:
        assert call(site, f"/static/{name}")[0] == 200, name


def test_the_page_contains_no_level_ids() -> None:
    level_ids = [path.stem.replace("_", "-") for path in LEVELS.glob("*.py") if path.stem != "__init__"]
    for path in sorted(STATIC.iterdir()):
        text = path.read_text()
        assert not [level_id for level_id in level_ids if level_id in text], path.name


def test_status_returns_the_dashboard(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    dashboard = {"xp": 120, "cards_due": 3, "active": None}
    record(monkeypatch, "status", dashboard)
    assert api(site, "/api/status") == (200, dashboard)


def test_a_level_is_looked_up_by_its_id(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = record(monkeypatch, "level", LEVEL_VIEW)
    assert api(site, "/api/level?id=some-level") == (200, LEVEL_VIEW)
    assert calls == [("some-level",)]


@pytest.mark.parametrize("route", ["/api/level", "/api/lesson"])
@pytest.mark.parametrize("query", ["", "?id=", "?other=x", "?id=" + "a" * 101])
def test_a_level_or_lesson_without_a_sensible_id_is_refused(
    site: Site, monkeypatch: pytest.MonkeyPatch, route: str, query: str
) -> None:
    calls = record(monkeypatch, route.removeprefix("/api/"), LEVEL_VIEW)
    status, reply = api(site, route + query)
    assert status == 400
    assert reply["error"]
    assert calls == []


@pytest.mark.parametrize("route", ["/api/level", "/api/lesson"])
def test_an_unknown_level_is_not_found(site: Site, monkeypatch: pytest.MonkeyPatch, route: str) -> None:
    record(monkeypatch, route.removeprefix("/api/"), error=KeyError("nope"))
    status, reply = api(site, route + "?id=nope")
    assert status == 404
    assert "nope" in reply["error"]


def test_a_lesson_is_looked_up_by_its_level_id(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    lesson = {"level": "some-level", "title": "A level", "slides": []}
    calls = record(monkeypatch, "lesson", lesson)
    assert api(site, "/api/lesson?id=some-level") == (200, lesson)
    assert calls == [("some-level",)]


def test_starting_a_level_returns_the_active_level(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    active = {"level": "some-level", "step": 0, "steps": 3, "hints": 0, "hints_total": 2, "attempts": 0, "started": "t"}
    calls = record(monkeypatch, "start", active)
    assert api(site, "/api/start", {"level": "some-level"}) == (200, active)
    assert calls == [("some-level",)]


@pytest.mark.parametrize(
    "body", [{}, {"level": None}, {"level": 3}, {"level": ""}, {"level": ["a"]}, {"level": "x" * 101}]
)
def test_starting_needs_a_level_id(site: Site, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]) -> None:
    calls = record(monkeypatch, "start", {})
    assert api(site, "/api/start", body)[0] == 400
    assert calls == []


def test_starting_an_unknown_level_is_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "start", error=KeyError("nope"))
    assert api(site, "/api/start", {"level": "nope"})[0] == 404


@pytest.mark.parametrize("answer", ["abc123", None, ""])
def test_a_quest_step_is_checked_with_the_answer_or_none(
    site: Site, monkeypatch: pytest.MonkeyPatch, answer: str | None
) -> None:
    result = {"correct": True, "message": [], "step": 1, "quest_done": False}
    calls = record(monkeypatch, "quest_step", result)
    assert api(site, "/api/step", {"answer": answer}) == (200, result)
    assert calls == [(answer,)]


@pytest.mark.parametrize("body", [{}, {"answer": 3}, {"answer": True}, {"answer": {"a": 1}}, {"answer": "x" * 1001}])
def test_a_quest_step_needs_a_text_or_null_answer(
    site: Site, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]
) -> None:
    calls = record(monkeypatch, "quest_step", {})
    assert api(site, "/api/step", body)[0] == 400
    assert calls == []


def test_checking_passes_the_answer_and_whether_the_page_polled(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    result = {"solved": False, "message": [], "payout": None, "debrief": None}
    calls = record(monkeypatch, "check", result)
    assert api(site, "/api/check", {"answer": None, "auto": True}) == (200, result)
    assert api(site, "/api/check", {"answer": "42", "auto": False}) == (200, result)
    assert calls == [(None, True), ("42", False)]


@pytest.mark.parametrize(
    "body",
    [
        {"answer": None},
        {"auto": True},
        {"answer": None, "auto": 1},
        {"answer": None, "auto": "yes"},
        {"answer": 4, "auto": False},
    ],
)
def test_checking_needs_an_answer_and_a_boolean_auto(
    site: Site, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]
) -> None:
    calls = record(monkeypatch, "check", {})
    assert api(site, "/api/check", body)[0] == 400
    assert calls == []


@pytest.mark.parametrize(
    ("route", "body", "name"),
    [
        ("/api/step", {"answer": None}, "quest_step"),
        ("/api/check", {"answer": None, "auto": True}, "check"),
        ("/api/hint", {}, "hint"),
        ("/api/observe", None, "observe"),
    ],
)
def test_actions_on_the_level_in_progress_conflict_when_there_is_none(
    site: Site, monkeypatch: pytest.MonkeyPatch, route: str, body: Any, name: str
) -> None:
    record(monkeypatch, name, error=routes.NO_LEVEL("no level is in progress"))
    status, reply = api(site, route, body)
    assert status == 409
    assert reply["error"]


def test_a_hint_is_revealed(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    hint = {"hint": [], "used": 1, "total": 3, "cost": 10}
    calls = record(monkeypatch, "hint", hint)
    assert api(site, "/api/hint", {}) == (200, hint)
    assert calls == [()]


def test_observing_returns_the_live_lab(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    observation: dict[str, Any] = {"level": "some-level", "project": {"exists": False}, "github": None, "events": []}
    record(monkeypatch, "observe", observation)
    assert api(site, "/api/observe") == (200, observation)


@pytest.mark.parametrize("ended", ["some-level", None])
def test_aborting_tells_which_level_ended(site: Site, monkeypatch: pytest.MonkeyPatch, ended: str | None) -> None:
    record(monkeypatch, "abort", ended)
    assert api(site, "/api/abort", {}) == (200, {"level": ended})


def test_resetting_needs_an_explicit_confirmation(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = record(monkeypatch, "reset", None)
    for body in ({}, {"confirm": "true"}, {"confirm": 1}, {"confirm": False}):
        assert api(site, "/api/reset", body)[0] == 400
    assert calls == []
    assert api(site, "/api/reset", {"confirm": True}) == (200, {})
    assert calls == [()]


def test_cards_are_listed_for_a_chapter_or_all_with_a_limit(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    card = {"id": "basics-x", "chapter": "basics", "kind": "choice", "prompt": [], "choices": ["a", "b"]}
    calls = record(monkeypatch, "due_cards", [card])
    assert api(site, "/api/cards?chapter=basics&limit=5") == (200, {"cards": [card]})
    assert api(site, "/api/cards") == (200, {"cards": [card]})
    assert api(site, "/api/cards?chapter=&limit=100") == (200, {"cards": [card]})
    assert calls == [("basics", 5), (None, routes.DEFAULT_CARDS), (None, 100)]


@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?limit=-1",
        "?limit=ten",
        "?limit=1.5",
        "?limit=%C2%B2",
        "?limit=" + "9" * 20,
        "?chapter=" + "c" * 101,
    ],
)
def test_cards_need_a_limit_between_one_and_a_hundred(site: Site, monkeypatch: pytest.MonkeyPatch, query: str) -> None:
    calls = record(monkeypatch, "due_cards", [])
    assert api(site, "/api/cards" + query)[0] == 400
    assert calls == []


def test_cards_of_an_unknown_chapter_are_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "due_cards", error=KeyError("nope"))
    assert api(site, "/api/cards?chapter=nope")[0] == 404


def test_a_card_reply_is_judged(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    result = {"correct": True, "answer": "a", "explain": [], "xp": 5, "streak": 2, "bonus": 0}
    calls = record(monkeypatch, "answer_card", result)
    assert api(site, "/api/card", {"id": "basics-x", "reply": "a"}) == (200, result)
    assert calls == [("basics-x", "a")]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"id": "basics-x"},
        {"reply": "a"},
        {"id": 3, "reply": "a"},
        {"id": "basics-x", "reply": None},
        {"id": "", "reply": "a"},
        {"id": "basics-x", "reply": "a" * 1001},
    ],
)
def test_a_card_reply_needs_an_id_and_a_text_reply(
    site: Site, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]
) -> None:
    calls = record(monkeypatch, "answer_card", {})
    assert api(site, "/api/card", body)[0] == 400
    assert calls == []


def test_a_reply_to_an_unknown_card_is_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "answer_card", error=KeyError("nope"))
    assert api(site, "/api/card", {"id": "nope", "reply": "a"})[0] == 404


def test_notes_are_looked_up_by_chapter(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    notes = {"chapter": "basics", "title": "The three areas", "notes": []}
    calls = record(monkeypatch, "notes", notes)
    assert api(site, "/api/notes?chapter=basics") == (200, notes)
    assert api(site, "/api/notes")[0] == 400
    assert calls == [("basics",)]


def test_notes_of_an_unknown_chapter_are_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "notes", error=KeyError("nope"))
    assert api(site, "/api/notes?chapter=nope")[0] == 404


def test_a_key_error_outside_a_lookup_is_not_taken_for_an_unknown_id(monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "status", error=KeyError("bug"))
    with pytest.raises(KeyError):
        routes.ROUTES[("GET", "/api/status")]({})


def test_the_terminal_keeps_git_to_the_games_configuration_and_labs(
    game_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_DIR", "/elsewhere/.git")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/home/player/.gitconfig")
    monkeypatch.setenv("TMUX", "/tmp/tmux-1/default")
    env = routes.TERMINAL.environment()
    assert env["GIT_CONFIG_GLOBAL"] == str(game_home / "gitconfig")
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_CEILING_DIRECTORIES"] == str(game_home / "labs")
    assert env["FIRSTCOMMIT_HOME"] == str(game_home)
    assert "GIT_DIR" not in env
    assert "TMUX" not in env


def test_the_terminal_opens_in_the_folder_the_game_names(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    record(monkeypatch, "terminal_folder", str(tmp_path))
    assert routes.TERMINAL.start_folder() == tmp_path


def test_serving_on_a_busy_port_fails_with_a_hint(site: Site, capsys: pytest.CaptureFixture[str]) -> None:
    port = int(site.url.rsplit(":", 1)[1])
    assert routes.serve(port) == 1
    assert f"--port {port + 1}" in capsys.readouterr().out


def test_every_route_is_a_get_or_post_under_api() -> None:
    expected = {
        ("GET", "/api/status"),
        ("GET", "/api/level"),
        ("GET", "/api/lesson"),
        ("POST", "/api/start"),
        ("POST", "/api/step"),
        ("POST", "/api/check"),
        ("POST", "/api/hint"),
        ("GET", "/api/observe"),
        ("POST", "/api/abort"),
        ("POST", "/api/reset"),
        ("GET", "/api/cards"),
        ("POST", "/api/card"),
        ("GET", "/api/notes"),
    }
    assert set(routes.ROUTES) == expected
