import json
import re
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from firstcommit import game, gitcmd, kit, runner, save
from firstcommit import guide as map_guide
from firstcommit.web import routes

STATIC = Path(routes.__file__).parent / "static"
LEVELS = Path(game.__file__).parent / "levels"
# The page's own text, which the scans below read; the rest of static/ is fonts and their licences.
PAGE_TEXT = {".html", ".js", ".css"}
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
    assert "`firstcommit serve`" in refused[2]
    assert refused[1]["Server"].startswith("FirstCommit")


def test_the_page_loads_nothing_from_outside_the_server(site: Site) -> None:
    status, headers, _ = call(site, "/")
    assert status == 200
    assert "https:" not in headers["Content-Security-Policy"]
    for path in sorted(entry for entry in STATIC.iterdir() if entry.suffix in PAGE_TEXT):
        text = path.read_text()
        assert not re.search(r"https?://(?!www\.w3\.org/2000/svg|localhost)", text), path.name


def test_every_static_file_is_page_text_a_font_or_a_font_licence() -> None:
    for path in STATIC.iterdir():
        assert path.suffix in PAGE_TEXT or path.suffix == ".woff2" or path.name.endswith("-OFL.txt"), path.name


def test_every_file_the_page_references_is_served(site: Site) -> None:
    _, _, page = call(site, "/")
    names = re.findall(r'(?:src|href)="/static/([^"]+)"', page)
    assert "app.js" in names and "client.js" in names and "terminal.js" in names
    for name in names:
        assert call(site, f"/static/{name}")[0] == 200, name


def test_the_page_contains_no_level_ids() -> None:
    level_ids = [path.stem.replace("_", "-") for path in LEVELS.glob("*.py") if path.stem != "__init__"]
    for path in sorted(entry for entry in STATIC.iterdir() if entry.suffix in PAGE_TEXT):
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
    record(monkeypatch, route.removeprefix("/api/"), error=game.UnknownIdError("nope"))
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
    record(monkeypatch, "start", error=game.UnknownIdError("nope"))
    assert api(site, "/api/start", {"level": "nope"})[0] == 404


def test_seeing_a_scene_marks_it_seen_for_its_level(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = record(monkeypatch, "see_scene", None)
    assert api(site, "/api/scene", {"level": "some-level"}) == (200, {})
    assert calls == [("some-level",)]


@pytest.mark.parametrize(
    "body", [{}, {"level": None}, {"level": 3}, {"level": ""}, {"level": ["a"]}, {"level": "x" * 101}]
)
def test_seeing_a_scene_needs_a_level_id(site: Site, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]) -> None:
    calls = record(monkeypatch, "see_scene", None)
    assert api(site, "/api/scene", body)[0] == 400
    assert calls == []


def test_seeing_the_scene_of_an_unknown_level_is_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "see_scene", error=game.UnknownIdError("nope"))
    assert api(site, "/api/scene", {"level": "nope"})[0] == 404


def test_the_real_game_remembers_a_seen_scene_until_a_reset(site: Site, sample_level: runner.Level) -> None:
    assert api(site, "/api/scene", {"level": sample_level.id}) == (200, {})
    assert api(site, f"/api/level?id={sample_level.id}")[1]["scene_seen"] is True
    assert api(site, "/api/reset", {"confirm": True})[0] == 200
    assert api(site, f"/api/level?id={sample_level.id}")[1]["scene_seen"] is False


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
        ("/api/press", {"person": "you", "button": "edit:notes.txt"}, "press"),
    ],
)
def test_actions_on_the_level_in_progress_conflict_when_there_is_none(
    site: Site, monkeypatch: pytest.MonkeyPatch, route: str, body: Any, name: str
) -> None:
    record(monkeypatch, name, error=game.NotPlayingError("no level is in progress"))
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
    record(monkeypatch, "due_cards", error=game.UnknownIdError("nope"))
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
    record(monkeypatch, "answer_card", error=game.UnknownIdError("nope"))
    assert api(site, "/api/card", {"id": "nope", "reply": "a"})[0] == 404


def test_notes_are_looked_up_by_chapter(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    notes = {"chapter": "basics", "title": "The three areas", "notes": []}
    calls = record(monkeypatch, "notes", notes)
    assert api(site, "/api/notes?chapter=basics") == (200, notes)
    assert api(site, "/api/notes")[0] == 400
    assert calls == [("basics",)]


def test_notes_of_an_unknown_chapter_are_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "notes", error=game.UnknownIdError("nope"))
    assert api(site, "/api/notes?chapter=nope")[0] == 404


def test_a_key_error_in_a_levels_setup_is_a_bug_not_an_unknown_level(
    site: Site, sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch
) -> None:
    def setup(lab: kit.Lab) -> kit.State:
        raise KeyError("players_name")

    broken = replace(sample_level, setup=setup)
    monkeypatch.setattr(runner, "catalogue", lambda: {broken.id: broken})
    assert api(site, "/api/start", {"level": broken.id}) == (500, {"error": "KeyError: 'players_name'", "kind": "bug"})


def test_a_key_error_outside_a_lookup_is_a_bug_not_an_unknown_id(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "status", error=KeyError("bug"))
    assert api(site, "/api/status") == (500, {"error": "KeyError: 'bug'", "kind": "bug"})


def test_the_terminal_keeps_git_to_the_games_configuration_and_labs(
    game_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_DIR", "/elsewhere/.git")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/home/player/.gitconfig")
    monkeypatch.setenv("TMUX", "/tmp/tmux-1/default")
    env = routes.TERMINAL.environment()
    assert {name: env[name] for name in gitcmd.isolation(game_home)} == gitcmd.isolation(game_home)
    assert env["FIRSTCOMMIT_HOME"] == str(game_home)
    assert "GIT_DIR" not in env
    assert "TMUX" not in env


def test_the_terminal_opens_in_the_folder_the_game_names(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    record(monkeypatch, "terminal_folder", str(tmp_path))
    assert routes.TERMINAL.start_folder() == tmp_path


def test_the_terminal_runs_the_games_shell_so_typed_commands_are_logged(game_home: Path) -> None:
    assert routes.TERMINAL.shell is not None
    assert list(routes.TERMINAL.shell()) == game.shell_command()


def test_serving_on_a_busy_port_fails_with_a_hint(site: Site, capsys: pytest.CaptureFixture[str]) -> None:
    port = int(site.url.rsplit(":", 1)[1])
    assert routes.serve(port) == 1
    assert f"firstcommit serve --port {port + 1}" in capsys.readouterr().out


def test_a_save_from_an_older_game_reaches_the_page_with_how_to_start_over(site: Site, sample_level: runner.Level, game_home: Path) -> None:
    progress = dict(save.new_progress())
    del progress["scenes"]
    (game_home / "progress.json").write_text(json.dumps(progress))
    status, reply = api(site, "/api/status")
    assert (status, reply["kind"]) == (500, "save")
    assert "progress.json" in reply["error"] and "`scenes` is missing" in reply["error"] and "`firstcommit reset --yes`" in reply["error"]


@pytest.mark.parametrize(
    ("route", "body", "name"),
    [
        ("/api/status", None, "status"),
        ("/api/level?id=x", None, "level"),
        ("/api/start", {"level": "x"}, "start"),
        ("/api/observe", None, "observe"),
        ("/api/cards", None, "due_cards"),
        ("/api/reset", {"confirm": True}, "reset"),
    ],
)
def test_a_damaged_save_is_a_server_error_of_kind_save_that_names_the_file(
    site: Site, monkeypatch: pytest.MonkeyPatch, route: str, body: Any, name: str
) -> None:
    record(monkeypatch, name, error=save.SaveError("progress.json: xp should be a number"))
    assert api(site, route, body) == (500, {"error": "progress.json: xp should be a number", "kind": "save"})


@pytest.mark.parametrize(
    ("route", "body", "name"),
    [("/api/status", None, "status"), ("/api/check", {"answer": None, "auto": False}, "check")],
)
def test_a_bug_in_the_game_is_a_server_error_of_kind_bug_and_its_traceback_goes_to_the_server_terminal(
    site: Site, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], route: str, body: Any, name: str
) -> None:
    record(monkeypatch, name, error=IndexError("tuple index out of range"))
    assert api(site, route, body) == (500, {"error": "IndexError: tuple index out of range", "kind": "bug"})
    logged = capsys.readouterr().err
    assert "Traceback (most recent call last)" in logged
    assert "IndexError: tuple index out of range" in logged


def test_a_fresh_game_lists_its_chapters_and_has_no_level_in_progress(site: Site, sample_level: runner.Level) -> None:
    status, dashboard = api(site, "/api/status")
    assert status == 200
    assert dashboard["active"] is None
    assert [level["id"] for chapter in dashboard["chapters"] for level in chapter["levels"]] == [sample_level.id]


def test_the_real_game_answers_404_for_an_unknown_level_and_409_with_no_level_in_progress(
    site: Site, sample_level: runner.Level
) -> None:
    assert api(site, "/api/level?id=no-such-level")[0] == 404
    assert api(site, "/api/start", {"level": "no-such-level"})[0] == 404
    assert api(site, "/api/observe")[0] == 409
    assert api(site, "/api/hint", {})[0] == 409
    assert api(site, "/api/step", {"answer": None})[0] == 409
    assert api(site, "/api/check", {"answer": None, "auto": True})[0] == 409
    assert api(site, "/api/abort", {}) == (200, {"level": None})


def test_a_level_is_played_through_the_routes_from_start_to_payout(site: Site, sample_level: runner.Level) -> None:
    assert api(site, "/api/start", {"level": sample_level.id})[1]["steps"] == 3
    project = Path(routes.TERMINAL.start_folder())
    assert (project / "hello.txt").is_file()
    assert api(site, "/api/observe")[1]["project"]["branch"] == "trunk"
    assert api(site, "/api/step", {"answer": None})[1]["correct"] is True
    assert api(site, "/api/step", {"answer": None})[1]["correct"] is False
    gitcmd.output(project, "add", "hello.txt")
    assert api(site, "/api/step", {"answer": None})[1]["correct"] is True
    assert api(site, "/api/step", {"answer": "main"})[1]["correct"] is False
    assert api(site, "/api/step", {"answer": "trunk"})[1]["quest_done"] is True
    assert api(site, "/api/check", {"answer": None, "auto": True})[1]["solved"] is False
    gitcmd.output(project, "commit", "-q", "-m", "Say hello")
    status, result = api(site, "/api/check", {"answer": None, "auto": True})
    assert (status, result["solved"], result["payout"]["xp"]) == (200, True, 100)
    assert api(site, "/api/status")[1]["active"] is None
    assert api(site, f"/api/level?id={sample_level.id}")[1]["debrief"]


def test_a_lesson_comes_with_its_figures_from_real_git(site: Site, sample_level: runner.Level) -> None:
    status, lesson = api(site, f"/api/lesson?id={sample_level.id}")
    assert status == 200
    assert [slide["view"] for slide in lesson["slides"]] == ["terminal", "objects"]
    assert lesson["slides"][1]["objects"]


def test_cards_and_notes_come_from_the_decks(site: Site, sample_decks: Path) -> None:
    cards = api(site, "/api/cards?chapter=basics&limit=3")[1]["cards"]
    assert len(cards) == 3
    status, result = api(site, "/api/card", {"id": cards[0]["id"], "reply": "nonsense"})
    assert (status, result["correct"]) == (200, False)
    assert api(site, "/api/notes?chapter=basics")[1]["title"] == "The three areas"


def test_a_press_sends_who_pressed_which_button_and_gives_the_games_view(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    view = {"press": {"person": "alex", "button": "push", "command": "git push", "status": 0, "output": ""}, "explanation": None, "observation": {}}
    calls = record(monkeypatch, "press", view)
    assert api(site, "/api/press", {"person": "alex", "button": "push"}) == (200, view)
    assert calls == [("alex", "push")]


@pytest.mark.parametrize(
    "body",
    [{}, {"person": "you"}, {"button": "push"}, {"person": None, "button": "push"}, {"person": "you", "button": 3}, {"person": "you", "button": "x" * 101}],
)
def test_a_press_needs_a_person_and_a_button_as_text(site: Site, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]) -> None:
    calls = record(monkeypatch, "press", {})
    assert api(site, "/api/press", body)[0] == 400
    assert calls == []


def test_a_press_by_someone_or_on_a_button_the_playground_does_not_have_is_not_found(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "press", error=game.UnknownIdError("no person 'bob'"))
    assert api(site, "/api/press", {"person": "bob", "button": "push"}) == (404, {"error": "no person 'bob'"})


def test_a_press_in_a_level_without_a_playground_conflicts(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "press", error=game.NoPlaygroundError("this level has no playground"))
    assert api(site, "/api/press", {"person": "you", "button": "push"}) == (409, {"error": "this level has no playground"})


def test_a_button_that_is_off_conflicts_with_its_reason_and_says_so_with_kind_off(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "press", error=game.ButtonOffError("notes.txt is not a plain file any more."))
    assert api(site, "/api/press", {"person": "you", "button": "edit:notes.txt"}) == (409, {"error": "notes.txt is not a plain file any more.", "kind": "off"})


def test_a_press_with_no_level_in_progress_conflicts_without_a_kind(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    record(monkeypatch, "press", error=game.NotPlayingError("no level is in progress"))
    assert api(site, "/api/press", {"person": "you", "button": "push"}) == (409, {"error": "no level is in progress"})


def test_the_real_playground_runs_each_press_and_a_failed_command_is_an_answer_not_an_error(site: Site, playground_level: runner.Level) -> None:
    assert api(site, "/api/start", {"level": playground_level.id})[0] == 200
    assert api(site, "/api/observe")[1]["teammate"] is not None
    status, edited = api(site, "/api/press", {"person": "alex", "button": "edit:notes.txt"})
    assert status == 200
    assert (edited["press"]["person"], edited["press"]["button"], edited["press"]["status"]) == ("alex", "edit:notes.txt", 0)
    assert [event["kind"] for event in edited["observation"]["teammate_events"]] == ["file-changed"]
    status, failed = api(site, "/api/press", {"person": "you", "button": "commit"})
    assert status == 200
    assert failed["press"]["status"] != 0
    assert failed["press"]["output"].strip()


def test_the_real_game_refuses_a_press_without_a_playground(site: Site, sample_level: runner.Level) -> None:
    assert api(site, "/api/press", {"person": "you", "button": "edit:notes.txt"})[0] == 409
    assert api(site, "/api/start", {"level": sample_level.id})[0] == 200
    assert api(site, "/api/press", {"person": "you", "button": "edit:notes.txt"})[0] == 409
    assert api(site, "/api/press", {"person": "bob", "button": "edit:notes.txt"})[0] == 404
    assert api(site, "/api/press", {"person": "you", "button": "edit"})[0] == 404


def test_the_real_playground_refuses_an_off_button_with_its_reason_and_runs_nothing(site: Site, playground_level: runner.Level) -> None:
    assert api(site, "/api/start", {"level": playground_level.id})[0] == 200
    notes = runner.lab_of(playground_level.id).project / "notes.txt"
    notes.unlink()
    notes.mkdir()
    reason = "notes.txt is not a plain file any more."
    assert next(view for view in api(site, "/api/observe")[1]["buttons"]["you"] if view["id"] == "edit:notes.txt")["off"] == reason
    assert api(site, "/api/press", {"person": "you", "button": "edit:notes.txt"}) == (409, {"error": reason, "kind": "off"})
    assert list(notes.iterdir()) == []


def test_the_guide_gives_the_games_figures_by_section(site: Site, monkeypatch: pytest.MonkeyPatch) -> None:
    figures = {"commit": {"before": {"exists": False}, "after": {"exists": True}, "transcript": [{"command": "git commit", "output": ""}]}}
    calls = record(monkeypatch, "guide", figures)
    assert api(site, "/api/guide") == (200, figures)
    assert calls == [()]


@pytest.mark.slow
def test_the_real_guide_draws_every_section_in_the_guides_order_from_real_git(site: Site) -> None:
    status, figures = api(site, "/api/guide")
    assert status == 200
    assert list(figures) == [figure.section for figure in map_guide.FIGURES]
    assert all(figure["transcript"] and figure["after"]["exists"] for figure in figures.values())


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
        ("GET", "/api/guide"),
        ("POST", "/api/press"),
        ("POST", "/api/scene"),
    }
    assert set(routes.ROUTES) == expected
