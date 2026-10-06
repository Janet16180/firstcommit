"""
The web interface: the JSON routes, the page's terminal and the server, on termlab's web shell.

Each route checks its query or body (400 when it is not what the page sends), calls one
`firstcommit.game` function and sends its record back as JSON. An unknown level, card or
chapter is a 404 and an action on the level in progress when there is none a 409. No game rule
lives here (Ring Zero audit ARCH-1): the routes only translate between HTTP and `game`.
"""

import os
import re
from collections.abc import Callable, Mapping
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, TypeGuard

from termlab.web import shell, terminal

from firstcommit import game, gitcmd, save

STATIC = Path(__file__).parent / "static"
PORT = 8820
SETTINGS = shell.ShellSettings(name="FirstCommit", command="firstcommit", token_header="X-FirstCommit-Token")
BANNER = "  First Commit: learn Git by doing"

MAX_ID = 100
MAX_ANSWER = 1000
DEFAULT_CARDS = 20
MAX_CARDS = 100
# A count in a query: 1 to 3 ASCII digits (str.isdigit() lets "²" through, which int() rejects).
COUNT = re.compile(r"[0-9]{1,3}")

Reply = tuple[HTTPStatus, dict[str, Any]]


class NoLevelError(Exception):
    """Placeholder for the exception `game` raises when an action needs a level in progress and none is."""


NO_LEVEL: type[Exception] = NoLevelError
"""The exception mapped to 409; the one place to name `game`'s own once it exists."""


def shell_environment() -> dict[str, str]:
    """
    Build the environment of the page's shell, again for each new terminal.

    Inherited ``GIT_*`` variables are dropped first, as for the game's own git commands
    (`firstcommit.gitcmd.environment`), so a ``GIT_DIR`` set around the server cannot redirect
    the player's git.

    Returns
    -------
    dict[str, str]
        The server's environment as a new terminal window would have it, with git kept to the
        game's own configuration and stopped from finding a repository above the labs.
    """
    inherited_git = {name for name in os.environ if name.startswith("GIT_")}
    return {**terminal.player_env(os.environ, drop=inherited_git), **gitcmd.isolation(save.home())}


def shell_folder() -> Path:
    """
    Give the folder a new terminal opens in.

    Returns
    -------
    Path
        The folder `firstcommit.game.terminal_folder` names.
    """
    return Path(game.terminal_folder())


TERMINAL = terminal.TerminalSettings(
    protocol="firstcommit", notice_prefix="firstcommit", environment=shell_environment, start_folder=shell_folder
)


def bad(message: str) -> Reply:
    """
    Refuse a request the page would never send.

    Parameters
    ----------
    message : str
        What the route expects.

    Returns
    -------
    Reply
        400 and the message.
    """
    return HTTPStatus.BAD_REQUEST, {"error": message}


def found(lookup: Callable[[], Mapping[str, Any]]) -> Reply:
    """
    Run a lookup by id, where a KeyError means the id is unknown.

    Parameters
    ----------
    lookup : Callable[[], Mapping[str, Any]]
        Calls `game` and gives the reply.

    Returns
    -------
    Reply
        200 and the reply, or 404 for an unknown id.
    """
    status, payload = HTTPStatus.OK, {}
    try:
        payload = dict(lookup())
    except KeyError as error:
        status, payload = HTTPStatus.NOT_FOUND, {"error": f"unknown id: {error.args[0] if error.args else ''}"}
    return status, payload


def playing(action: Callable[[], Mapping[str, Any]]) -> Reply:
    """
    Run an action on the level in progress.

    Parameters
    ----------
    action : Callable[[], Mapping[str, Any]]
        Calls `game` and gives the reply.

    Returns
    -------
    Reply
        200 and the reply, or 409 when no level is in progress.
    """
    status, payload = HTTPStatus.OK, {}
    try:
        payload = dict(action())
    except NO_LEVEL as error:
        status, payload = HTTPStatus.CONFLICT, {"error": str(error) or "no level is in progress"}
    return status, payload


def is_id(value: Any) -> TypeGuard[str]:
    """
    Tell whether a value can be a level, card or chapter id (whether it exists is `game`'s to say).

    Parameters
    ----------
    value : Any
        A query value or body field.

    Returns
    -------
    TypeGuard[str]
        True for a non-empty string of at most `MAX_ID` characters.
    """
    return isinstance(value, str) and 0 < len(value) <= MAX_ID


def is_answer(body: dict[str, Any]) -> bool:
    """
    Tell whether a body carries an answer: text of at most `MAX_ANSWER` characters, or null.

    Parameters
    ----------
    body : dict[str, Any]
        The JSON body.

    Returns
    -------
    bool
        True if ``answer`` is present and is null or such a text.
    """
    if "answer" not in body:
        return False
    answer = body["answer"]
    return answer is None or (isinstance(answer, str) and len(answer) <= MAX_ANSWER)


def api_status(query: dict[str, Any]) -> Reply:
    """
    GET /api/status: the dashboard.

    Parameters
    ----------
    query : dict[str, Any]
        Unused.

    Returns
    -------
    Reply
        200 and `game.Status`.
    """
    return HTTPStatus.OK, dict(game.status())


def api_level(query: dict[str, Any]) -> Reply:
    """
    GET /api/level?id=: a level's page.

    Parameters
    ----------
    query : dict[str, Any]
        ``id``, the level.

    Returns
    -------
    Reply
        200 and `game.LevelView`; 400 without an id, 404 for an unknown one.
    """
    level_id = query.get("id")
    if not is_id(level_id):
        return bad("send ?id=<level id>")
    return found(lambda: game.level(level_id))


def api_lesson(query: dict[str, Any]) -> Reply:
    """
    GET /api/lesson?id=: a level's lesson.

    Parameters
    ----------
    query : dict[str, Any]
        ``id``, the level.

    Returns
    -------
    Reply
        200 and `game.LessonView`; 400 without an id, 404 for an unknown one.
    """
    level_id = query.get("id")
    if not is_id(level_id):
        return bad("send ?id=<level id>")
    return found(lambda: game.lesson(level_id))


def api_start(body: dict[str, Any]) -> Reply:
    """
    POST /api/start {"level": id}: start a level in a fresh lab.

    Parameters
    ----------
    body : dict[str, Any]
        The JSON body.

    Returns
    -------
    Reply
        200 and `game.ActiveView`; 400 without a level id, 404 for an unknown one.
    """
    level_id = body.get("level")
    if not is_id(level_id):
        return bad('send {"level": "<level id>"}')
    return found(lambda: game.start(level_id))


def api_step(body: dict[str, Any]) -> Reply:
    """
    POST /api/step {"answer": text or null}: check the current quest step.

    Parameters
    ----------
    body : dict[str, Any]
        The JSON body.

    Returns
    -------
    Reply
        200 and `game.StepResult`; 400 without an answer, 409 with no level in progress.
    """
    if not is_answer(body):
        return bad('send {"answer": "<text>"} or {"answer": null}')
    return playing(lambda: game.quest_step(body["answer"]))


def api_check(body: dict[str, Any]) -> Reply:
    """
    POST /api/check {"answer": text or null, "auto": bool}: check the level.

    Parameters
    ----------
    body : dict[str, Any]
        The JSON body; ``auto`` is true when the page polls rather than the player asking.

    Returns
    -------
    Reply
        200 and `game.CheckResult`; 400 for a malformed body, 409 with no level in progress.
    """
    auto = body.get("auto")
    if not is_answer(body) or not isinstance(auto, bool):
        return bad('send {"answer": "<text>" or null, "auto": true or false}')
    return playing(lambda: game.check(body["answer"], auto))


def api_hint(body: dict[str, Any]) -> Reply:
    """
    POST /api/hint {}: reveal the next hint.

    Parameters
    ----------
    body : dict[str, Any]
        Unused.

    Returns
    -------
    Reply
        200 and `game.HintView`; 409 with no level in progress.
    """
    return playing(game.hint)


def api_observe(query: dict[str, Any]) -> Reply:
    """
    GET /api/observe: the live lab and what changed since the last look.

    Parameters
    ----------
    query : dict[str, Any]
        Unused.

    Returns
    -------
    Reply
        200 and `game.Observation`; 409 with no level in progress.
    """
    return playing(game.observe)


def api_abort(body: dict[str, Any]) -> Reply:
    """
    POST /api/abort {}: end the level in progress.

    Parameters
    ----------
    body : dict[str, Any]
        Unused.

    Returns
    -------
    Reply
        200 and ``{"level": id or null}``, the level that ended.
    """
    return HTTPStatus.OK, {"level": game.abort()}


def api_reset(body: dict[str, Any]) -> Reply:
    """
    POST /api/reset {"confirm": true}: erase all progress.

    Parameters
    ----------
    body : dict[str, Any]
        The JSON body.

    Returns
    -------
    Reply
        200 and ``{}``; 400 unless ``confirm`` is exactly true.
    """
    if body.get("confirm") is not True:
        return bad('send {"confirm": true} to erase all progress')
    game.reset()
    return HTTPStatus.OK, {}


def api_cards(query: dict[str, Any]) -> Reply:
    """
    GET /api/cards?chapter=&limit=: the cards to review.

    Parameters
    ----------
    query : dict[str, Any]
        ``chapter`` (empty or missing for every chapter) and ``limit``, 1 to `MAX_CARDS`
        (`DEFAULT_CARDS` when missing).

    Returns
    -------
    Reply
        200 and ``{"cards": [game.CardView, ...]}``; 400 for a bad chapter or limit, 404 for an
        unknown chapter.
    """
    chapter = query.get("chapter") or None
    limit = query.get("limit", str(DEFAULT_CARDS))
    if chapter is not None and not is_id(chapter):
        return bad("send ?chapter=<chapter id>, or no chapter for all")
    if not COUNT.fullmatch(limit) or not 1 <= int(limit) <= MAX_CARDS:
        return bad(f"send ?limit=<1 to {MAX_CARDS}>")
    return found(lambda: {"cards": game.due_cards(chapter, int(limit))})


def api_card(body: dict[str, Any]) -> Reply:
    """
    POST /api/card {"id": card id, "reply": text}: judge a reply to a card.

    Parameters
    ----------
    body : dict[str, Any]
        The JSON body.

    Returns
    -------
    Reply
        200 and `game.CardResult`; 400 for a malformed body, 404 for an unknown card.
    """
    card_id = body.get("id")
    reply = body.get("reply")
    if not is_id(card_id) or not isinstance(reply, str) or len(reply) > MAX_ANSWER:
        return bad('send {"id": "<card id>", "reply": "<text>"}')
    return found(lambda: game.answer_card(card_id, reply))


def api_notes(query: dict[str, Any]) -> Reply:
    """
    GET /api/notes?chapter=: a chapter's cheat sheet.

    Parameters
    ----------
    query : dict[str, Any]
        ``chapter``.

    Returns
    -------
    Reply
        200 and `game.Notes`; 400 without a chapter, 404 for an unknown one.
    """
    chapter = query.get("chapter")
    if not is_id(chapter):
        return bad("send ?chapter=<chapter id>")
    return found(lambda: game.notes(chapter))


ROUTES: dict[tuple[str, str], shell.Route] = {
    ("GET", "/api/status"): api_status,
    ("GET", "/api/level"): api_level,
    ("GET", "/api/lesson"): api_lesson,
    ("POST", "/api/start"): api_start,
    ("POST", "/api/step"): api_step,
    ("POST", "/api/check"): api_check,
    ("POST", "/api/hint"): api_hint,
    ("GET", "/api/observe"): api_observe,
    ("POST", "/api/abort"): api_abort,
    ("POST", "/api/reset"): api_reset,
    ("GET", "/api/cards"): api_cards,
    ("POST", "/api/card"): api_card,
    ("GET", "/api/notes"): api_notes,
}


def create_server(port: int) -> tuple[ThreadingHTTPServer, str]:
    """
    Bind the game's server to 127.0.0.1 without serving yet, for tests.

    Parameters
    ----------
    port : int
        TCP port; 0 picks a free one.

    Returns
    -------
    tuple[ThreadingHTTPServer, str]
        The server and the link that opens the page, with the access key.
    """
    return shell.create_server(port, routes=ROUTES, static_dir=STATIC, terminal=TERMINAL, settings=SETTINGS)


def serve(port: int = PORT) -> int:
    """
    Serve the game until Ctrl-C.

    Parameters
    ----------
    port : int
        TCP port on 127.0.0.1.

    Returns
    -------
    int
        Exit status: 0 after Ctrl-C, 1 if the port is in use.
    """
    return shell.serve(port, routes=ROUTES, static_dir=STATIC, terminal=TERMINAL, settings=SETTINGS, banner=BANNER)
