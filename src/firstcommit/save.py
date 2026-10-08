"""
The player's saved game: where it lives and the shape of its records.

Files under the game home (`home`):
- ``progress.json``: a `Progress` record;
- ``active.json``: an `Active` record while a level is being played;
- ``observed.json``: an `Observed` record, the lab as the page last saw it;
- ``gitconfig``: the game's own global git configuration (see `firstcommit.gitcmd`);
- ``labs/<level>/``: the lab of the level being played (`firstcommit.runner` owns it);
- ``playground.json``: a `Playground` record, once the free playground has been opened;
- ``playground/``: the free playground's lab (`firstcommit.freeplay` owns it), apart from the labs;
- ``playground-shells/<person>/``: the files of the playground's shell of each person, yours and
  Alex's: its startup file, typed-command log, history and ``.hushlogin``, and for Alex a git
  configuration of Alex's own; Alex's shell has it as its ``HOME``.

The files are written atomically (termlab's store). Callers hold `lock` around every
read-modify-write, so the command line and the web server never lose each other's update.

Every record is checked against its `TypedDict` when it is read: a file damaged or edited by
hand raises `SaveError` naming the file and the field, instead of failing later somewhere else.
Every whole number in a record is zero or more.
"""

import contextlib
import types
import typing
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict, cast

from termlab import sandbox, store

from firstcommit.records import Command, Language, PlaygroundView, PullRequest, Seen, Snapshot, StartId, Who

HOME_VARIABLE = "FIRSTCOMMIT_HOME"
DEFAULT_HOME = "~/.firstcommit"
PROGRESS_FILE = "progress.json"
ACTIVE_FILE = "active.json"
OBSERVED_FILE = "observed.json"
GITCONFIG_FILE = "gitconfig"
STARTUP_FILE = "bashrc"
HUSHLOGIN_FILE = ".hushlogin"
COMMANDS_FILE = "commands.log"
HISTORY_FILE = "history"
LABS_FOLDER = "labs"
PLAYGROUND_FILE = "playground.json"
PLAYGROUND_FOLDER = "playground"
PLAYGROUND_SHELLS_FOLDER = "playground-shells"
START_OVER = (
    "A save written by an older version of the game reads this way too. To start over, run "
    "`firstcommit reset --yes`, or the `reset` command of the script that starts the game; either erases your progress."
)


IsoDate = Annotated[str, date]
"""A day written as ISO 8601, such as ``2026-10-06``; the save checks it reads as a `datetime.date`."""
IsoTime = Annotated[str, datetime]
"""A moment written as ISO 8601, such as ``2026-10-06T10:00:00+02:00``; the save checks it reads as a `datetime.datetime`."""


class SaveError(ValueError):
    """A save file that does not hold the record it should: damaged, edited by hand, or written by an older version of the game."""


def damaged(path: Path, problem: str) -> SaveError:
    """
    Make the error for a save file that does not hold its record, saying how to start over.

    Parameters
    ----------
    path : Path
        The file.
    problem : str
        What is wrong with it.

    Returns
    -------
    SaveError
        The error, naming the file, the problem and `START_OVER`.
    """
    return SaveError(f"{path} is damaged: {problem}. {START_OVER}")


class LevelRecord(TypedDict):
    """
    A level the player has finished: when and the XP paid, both the first time, the best stars, and the state of the last play.

    ``stars`` is the most any solve of the level earned (`firstcommit.score.stars`), 1 to 3.
    ``state`` is the level state of the most recent solve (replays included), so its debrief can
    be filled in after the level in progress is gone.
    """

    finished: IsoTime
    xp: int
    stars: int
    state: dict[str, Any]


class CardEntry(TypedDict):
    """A flashcard's place in the Leitner schedule: its box and the day it is due again."""

    box: int
    due: IsoDate


class Payout(TypedDict):
    """What the last finished level paid, kept so any view can celebrate it."""

    level: str
    xp: int
    first_time: bool
    rank_before: str
    rank_after: str


class Progress(TypedDict):
    """
    Everything the player has earned, and what the game remembers for them.

    ``scenes`` holds the ids of the levels whose scene the player has seen, in the order seen,
    ``views`` what the page has shown being born (`Seen`), in the order seen, your station from the start,
    and ``language`` the language the game speaks.
    """

    xp: int
    levels: dict[str, LevelRecord]
    cards: dict[str, CardEntry]
    streak: int
    best_streak: int
    last_payout: Payout | None
    scenes: list[str]
    views: list[Seen]
    language: Language


class Active(TypedDict):
    """
    The level being played.

    ``step`` is the index of the current guided-quest step; it equals the number of steps once
    the quest is done (and is 0 for a level without a quest). ``typed`` holds every line typed
    in the game's terminal since the level started, oldest first, read from the log of typed
    commands (`COMMANDS_FILE`, `firstcommit.commands`) up to ``log_offset``. ``events`` lists the
    ids of the level's events (`firstcommit.kit.LevelEvent`) that have run in this play, and
    ``done`` the ids of the quest's goals met so far, in quest order; ``step`` always equals its
    length (a challenge's goals are met in any order).
    """

    level: str
    started: IsoTime
    step: int
    hints: int
    attempts: int
    state: dict[str, Any]
    log_offset: int
    typed: list[Command]
    events: list[str]
    done: list[str]


class Observed(TypedDict):
    """
    The lab of the level in progress as last observed.

    ``github`` is None when the level has no stand-in GitHub, and ``teammate`` when it has no
    teammate's clone (`firstcommit.playground`). ``told`` counts the lines of the level's
    ``Active.typed`` that observations have told already. ``fresh`` marks the lab as it was set
    up, before the level's events, snapshotted when the level started and not yet shown. The snapshots are
    checked field by field like every record, so one of another shape (written by another
    version of the game) is dropped on load (`load_observed`).
    """

    level: str
    project: Snapshot
    github: Snapshot | None
    teammate: Snapshot | None
    told: int
    fresh: bool


class Playground(TypedDict):
    """
    Where the player left the free playground.

    ``start`` is the starting point its lab was last built from, and ``view`` and ``whose`` the
    view shown and whose repository it draws. ``alex_shown`` holds, for each start the player
    has been in, whether Alex's terminal was shown; a start missing from it shows Alex as the
    start's default does (`firstcommit.freeplay.Start.alex`).
    """

    start: StartId
    alex_shown: dict[StartId, bool]
    view: PlaygroundView
    whose: Who


def home() -> Path:
    """
    Give the game's home folder, from ``FIRSTCOMMIT_HOME`` or ``~/.firstcommit``.

    Returns
    -------
    Path
        The absolute home folder (it may not exist yet).

    Raises
    ------
    ValueError
        If ``FIRSTCOMMIT_HOME`` is set to a relative or empty path, or to one holding ``:``,
        which git's list of ceiling folders would split in two.
    """
    path = store.home(HOME_VARIABLE, DEFAULT_HOME)
    if ":" in str(path):
        raise ValueError(f"{HOME_VARIABLE} must not contain ':', since git splits its folder lists at ':', not {str(path)!r}")
    return path


def lock() -> contextlib.AbstractContextManager[None]:
    """
    Hold the save's lock, across processes, for the duration of a ``with`` block.

    Returns
    -------
    contextlib.AbstractContextManager[None]
        The lock on the game home.
    """
    return store.lock(home())


def new_progress() -> Progress:
    """
    Give the progress of a new player.

    Returns
    -------
    Progress
        No XP, no levels, no cards, no streak, no payout, no scene seen and only your station's view, in English.
    """
    return {"xp": 0, "levels": {}, "cards": {}, "streak": 0, "best_streak": 0, "last_payout": None, "scenes": [], "views": ["station"], "language": "en"}


def load_progress() -> Progress:
    """
    Read the player's progress.

    Returns
    -------
    Progress
        The saved progress, or `new_progress` if there is none yet.

    Raises
    ------
    SaveError
        If ``progress.json`` does not hold a valid `Progress` record.
    """
    data = _read(PROGRESS_FILE, Progress)
    return new_progress() if data is None else cast(Progress, data)


def write_progress(progress: Progress) -> None:
    """
    Replace the player's progress.

    Parameters
    ----------
    progress : Progress
        The whole record.
    """
    store.write_json(home() / PROGRESS_FILE, dict(progress))


def load_active() -> Active | None:
    """
    Read the level in progress.

    Returns
    -------
    Active | None
        The record, or None if no level is in progress.

    Raises
    ------
    SaveError
        If ``active.json`` does not hold a valid `Active` record.
    """
    return cast(Active | None, _read(ACTIVE_FILE, Active))


def write_active(active: Active) -> None:
    """
    Replace the record of the level in progress.

    Parameters
    ----------
    active : Active
        The whole record.

    Raises
    ------
    TypeError
        If the level's state is not JSON-serialisable (a bug in the level); the file is left as it was.
    """
    store.write_json(home() / ACTIVE_FILE, dict(active))


def clear_active() -> None:
    """Forget the level in progress, if any."""
    (home() / ACTIVE_FILE).unlink(missing_ok=True)


def load_observed() -> Observed | None:
    """
    Read the lab as it was last observed.

    The observation is only a cache of what the page saw last. A file that is damaged, or that
    another version of the game wrote in another shape, counts as nothing observed yet: the next
    observation then tells no changes and writes a fresh one. This is the one save file whose
    mismatch is not a `SaveError`.

    Returns
    -------
    Observed | None
        The record, or None if nothing valid was observed since the level started.
    """
    try:
        observed = _read(OBSERVED_FILE, Observed)
    except SaveError:
        observed = None
    return cast(Observed | None, observed)


def write_observed(observed: Observed) -> None:
    """
    Replace the record of the lab as last observed.

    Parameters
    ----------
    observed : Observed
        The whole record.
    """
    store.write_json(home() / OBSERVED_FILE, dict(observed))


def clear_observed() -> None:
    """Forget the last observation, if any."""
    (home() / OBSERVED_FILE).unlink(missing_ok=True)


def load_playground() -> Playground | None:
    """
    Read where the player left the free playground.

    Returns
    -------
    Playground | None
        The record, or None if the playground was never opened.

    Raises
    ------
    SaveError
        If ``playground.json`` does not hold a valid `Playground` record.
    """
    return cast(Playground | None, _read(PLAYGROUND_FILE, Playground))


def write_playground(playground: Playground) -> None:
    """
    Replace the record of where the player left the free playground.

    Parameters
    ----------
    playground : Playground
        The whole record.
    """
    store.write_json(home() / PLAYGROUND_FILE, dict(playground))


def ensure_gitconfig(initial: str, folder: Path | None = None) -> Path:
    """
    Create a global git configuration of the game's if it does not exist yet.

    An existing file is never overwritten: the player sets their name in it while playing.

    Parameters
    ----------
    initial : str
        Content of a new file (`firstcommit.gitcmd.base_config`).
    folder : Path | None
        Where it goes, such as Alex's playground shell (`ensure_playground_shell`); None is the
        game home, for the game's own configuration.

    Returns
    -------
    Path
        The configuration file.
    """
    path = (home() if folder is None else folder) / GITCONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    # Mode "x" creates the file only if it is missing, in one step, so two processes cannot both write it.
    with contextlib.suppress(FileExistsError), path.open("x") as handle:
        handle.write(initial)
    return path


def write_shell_startup(text: str) -> Path:
    """
    Write the startup file of the game's shell (`firstcommit.commands.startup`), replacing any older one.

    Parameters
    ----------
    text : str
        The file's text.

    Returns
    -------
    Path
        The file, in the game home (created if missing).
    """
    path = home() / STARTUP_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def ensure_hushlogin() -> Path:
    """
    Create the empty ``.hushlogin`` file that keeps the game's shell quiet (`firstcommit.commands.shell`), if it is missing.

    Returns
    -------
    Path
        The file, in the game home (created if missing).
    """
    path = home() / HUSHLOGIN_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def ensure_playground_shell(person: Who) -> Path:
    """
    Make the folder of one person's playground shell, with the ``.hushlogin`` that keeps it quiet, if it is missing.

    Parameters
    ----------
    person : Who
        ``"you"`` or ``"alex"``.

    Returns
    -------
    Path
        ``<home>/playground-shells/<person>``.
    """
    folder = home() / PLAYGROUND_SHELLS_FOLDER / person
    folder.mkdir(parents=True, exist_ok=True)
    (folder / HUSHLOGIN_FILE).touch()
    return folder


def erase() -> None:
    """Delete the progress, the level in progress, the last observation, the playground's record and shells, the game's git configuration and its shell's files (startup file, hushlogin, typed-command log, history), damaged or not."""
    for name in (PROGRESS_FILE, ACTIVE_FILE, OBSERVED_FILE, PLAYGROUND_FILE, GITCONFIG_FILE, STARTUP_FILE, HUSHLOGIN_FILE, COMMANDS_FILE, HISTORY_FILE):
        (home() / name).unlink(missing_ok=True)
    sandbox.remove_tree(home() / PLAYGROUND_SHELLS_FOLDER, home())


class Pulls(TypedDict):
    """The stand-in GitHub's pull requests, as their file holds them (`firstcommit.lab.Lab` ``pulls``)."""

    pulls: list[PullRequest]


def load_pulls(path: Path) -> list[PullRequest]:
    """
    Read the stand-in GitHub's pull requests.

    Parameters
    ----------
    path : Path
        Their file (`firstcommit.lab.Lab` ``pulls``).

    Returns
    -------
    list[PullRequest]
        The pull requests, or none if the file does not exist yet.

    Raises
    ------
    SaveError
        If the file does not hold a valid `Pulls` record.
    """
    data = _read_file(path, Pulls)
    return [] if data is None else cast(Pulls, data)["pulls"]


def write_pulls(path: Path, pulls: list[PullRequest]) -> None:
    """
    Replace the stand-in GitHub's pull requests.

    Parameters
    ----------
    path : Path
        Their file; missing folders are made.
    pulls : list[PullRequest]
        Every pull request.
    """
    store.write_json(path, {"pulls": pulls})


def _read(name: str, record: type) -> dict[str, Any] | None:
    """
    Read one save file and check it holds a record of the given type.

    Parameters
    ----------
    name : str
        File name under the home.
    record : type
        The `TypedDict` the file must hold.

    Returns
    -------
    dict[str, Any] | None
        The record, or None if the file does not exist.

    Raises
    ------
    SaveError
        If the file is not a JSON object or does not match the record.
    """
    return _read_file(home() / name, record)


def _read_file(path: Path, record: type) -> dict[str, Any] | None:
    """
    Read a JSON file and check it holds a record of the given type.

    Parameters
    ----------
    path : Path
        The file.
    record : type
        The `TypedDict` the file must hold.

    Returns
    -------
    dict[str, Any] | None
        The record, or None if the file does not exist.

    Raises
    ------
    SaveError
        If the file is not a JSON object or does not match the record.
    """
    try:
        data = store.read_json(path)
    except ValueError as error:
        raise damaged(path, str(error)) from error
    if data is not None:
        problem = _mismatch(data, record, "")
        if problem is not None:
            raise damaged(path, problem)
    return data


def _mismatch(value: Any, expected: Any, where: str) -> str | None:
    """
    Compare a JSON value with a type from the records above.

    Parameters
    ----------
    value : Any
        Value read from JSON.
    expected : Any
        A `TypedDict`, ``dict[K, X]`` (``K`` is ``str`` or a ``Literal``), ``list[X]``, ``Literal[...]``, ``X | None``, `IsoDate`,
        `IsoTime`, ``int``, ``str``, ``bool`` or ``Any``.
    where : str
        Dotted path of the value in its file, for the message; empty for the whole record.

    Returns
    -------
    str | None
        What is wrong with the first field that does not match, or None if the value matches.

    Raises
    ------
    TypeError
        If `expected` is none of the types above (a record this checker was not taught).
    """
    origin = typing.get_origin(expected)
    problem = None
    if typing.is_typeddict(expected):
        problem = _record_mismatch(value, expected, where)
    elif origin is dict:
        key, item = typing.get_args(expected)
        problem = _mapping_mismatch(value, key, item, where)
    elif origin is list:
        problem = _list_mismatch(value, typing.get_args(expected)[0], where)
    elif origin is Annotated:
        problem = _iso_mismatch(value, typing.get_args(expected)[1], where)
    elif origin is Literal:
        allowed = typing.get_args(expected)
        problem = None if value in allowed and isinstance(value, str) else f"`{where}` must be one of {', '.join(allowed)}, not {value!r}"
    elif origin in (types.UnionType, typing.Union):
        (present,) = [option for option in typing.get_args(expected) if option is not type(None)]
        problem = None if value is None else _mismatch(value, present, where)
    elif expected is int:
        problem = None if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else f"`{where}` must be a whole number, zero or more, not {value!r}"
    elif expected in (str, bool):
        problem = None if isinstance(value, expected) else f"`{where}` must be a {expected.__name__}, not {value!r}"
    elif expected is not Any:
        raise TypeError(f"the save cannot check values of type {expected!r}")
    return problem


def _iso_mismatch(value: Any, kind: type[date], where: str) -> str | None:
    """
    Compare a JSON value with an ISO 8601 day or moment.

    Parameters
    ----------
    value : Any
        Value read from JSON.
    kind : type[date]
        `datetime.date` for `IsoDate`, `datetime.datetime` for `IsoTime`.
    where : str
        Dotted path of the value.

    Returns
    -------
    str | None
        What is wrong, or None if the value is text that `kind` reads.
    """
    readable = isinstance(value, str)
    if readable:
        try:
            kind.fromisoformat(value)
        except ValueError:
            readable = False
    return None if readable else f"`{where}` must be a {kind.__name__} written as ISO 8601, not {value!r}"


def _list_mismatch(value: Any, item: Any, where: str) -> str | None:
    """
    Compare a JSON value with ``list[item]``.

    Parameters
    ----------
    value : Any
        Value read from JSON.
    item : Any
        The type of every item.
    where : str
        Dotted path of the value; an item's path ends with its position.

    Returns
    -------
    str | None
        What is wrong, or None if the value matches.
    """
    if not isinstance(value, list):
        return f"`{where}` must be a list, not {value!r}"
    return _first(_mismatch(entry, item, f"{where}.{position}") for position, entry in enumerate(value))


def _record_mismatch(value: Any, record: Any, where: str) -> str | None:
    """
    Compare a JSON value with a `TypedDict`: exactly its fields, each of its type.

    Parameters
    ----------
    value : Any
        Value read from JSON.
    record : Any
        The `TypedDict` class.
    where : str
        Dotted path of the value, empty for the whole file.

    Returns
    -------
    str | None
        What is wrong, or None if the value matches.
    """
    if not isinstance(value, dict):
        return f"`{where}` must be an object, not {value!r}"
    fields = typing.get_type_hints(record, include_extras=True)
    prefix = f"{where}." if where else ""
    missing = [name for name in fields if name not in value]
    unknown = [name for name in value if name not in fields]
    problem: str | None
    if missing:
        problem = f"`{prefix}{missing[0]}` is missing"
    elif unknown:
        problem = f"`{prefix}{unknown[0]}` is not a field of this file"
    else:
        problem = _first(_mismatch(value[name], kind, prefix + name) for name, kind in fields.items())
    return problem


def _mapping_mismatch(value: Any, key: Any, item: Any, where: str) -> str | None:
    """
    Compare a JSON value with ``dict[key, item]``.

    Parameters
    ----------
    value : Any
        Value read from JSON.
    key : Any
        The type of every key: ``str``, or a ``Literal`` of the keys allowed.
    item : Any
        The type of every value in the mapping.
    where : str
        Dotted path of the value.

    Returns
    -------
    str | None
        What is wrong, or None if the value matches.
    """
    if not isinstance(value, dict):
        return f"`{where}` must be an object, not {value!r}"
    return _first(_mismatch(name, key, f"{where}.{name}") or _mismatch(entry, item, f"{where}.{name}") for name, entry in value.items())


def _first(problems: Iterable[str | None]) -> str | None:
    """
    Give the first problem found.

    Parameters
    ----------
    problems : Iterable[str | None]
        Results of `_mismatch`, computed lazily.

    Returns
    -------
    str | None
        The first one that is not None, or None.
    """
    return next((problem for problem in problems if problem is not None), None)
