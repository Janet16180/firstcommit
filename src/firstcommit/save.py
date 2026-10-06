"""
The player's saved game: where it lives and the shape of its records.

Files under the game home (`home`):
- ``progress.json``: a `Progress` record;
- ``active.json``: an `Active` record while a level is being played;
- ``observed.json``: an `Observed` record, the lab as the page last saw it;
- ``gitconfig``: the game's own global git configuration (see `firstcommit.gitcmd`);
- ``labs/<level>/``: the lab of the level being played (`firstcommit.runner` owns it).
- ``lessons/``: temporary folders where lessons run (`firstcommit.demos` owns them).

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
from pathlib import Path
from typing import Any, TypedDict, cast

from termlab import store

HOME_VARIABLE = "FIRSTCOMMIT_HOME"
DEFAULT_HOME = "~/.firstcommit"
PROGRESS_FILE = "progress.json"
ACTIVE_FILE = "active.json"
OBSERVED_FILE = "observed.json"
GITCONFIG_FILE = "gitconfig"
LABS_FOLDER = "labs"
LESSONS_FOLDER = "lessons"


class SaveError(ValueError):
    """A save file that does not hold the record it should: damaged, or edited by hand."""


class LevelRecord(TypedDict):
    """
    A level the player has finished: when and the XP paid, both the first time, and the state of the last play.

    ``state`` is the level state of the most recent solve (replays included), so its debrief can
    be filled in after the level in progress is gone.
    """

    finished: str
    xp: int
    state: dict[str, Any]


class CardEntry(TypedDict):
    """A flashcard's place in the Leitner schedule: its box and the day it is due again."""

    box: int
    due: str


class Payout(TypedDict):
    """What the last finished level paid, kept so any view can celebrate it."""

    level: str
    xp: int
    first_time: bool
    rank_before: str
    rank_after: str


class Progress(TypedDict):
    """Everything the player has earned."""

    xp: int
    levels: dict[str, LevelRecord]
    cards: dict[str, CardEntry]
    streak: int
    best_streak: int
    last_payout: Payout | None


class Active(TypedDict):
    """
    The level being played.

    ``step`` is the index of the current guided-quest step; it equals the number of steps once
    the quest is done (and is 0 for a level without a quest).
    """

    level: str
    started: str
    step: int
    hints: int
    attempts: int
    state: dict[str, Any]


class Observed(TypedDict):
    """
    The lab of the level in progress as last observed (`firstcommit.repomap.Snapshot` records).

    ``github`` is None when the level has no stand-in GitHub.
    """

    level: str
    project: dict[str, Any]
    github: dict[str, Any] | None


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
        If ``FIRSTCOMMIT_HOME`` is set to a relative or empty path.
    """
    return store.home(HOME_VARIABLE, DEFAULT_HOME)


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
        No XP, no levels, no cards, no streak and no payout.
    """
    return {"xp": 0, "levels": {}, "cards": {}, "streak": 0, "best_streak": 0, "last_payout": None}


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

    Returns
    -------
    Observed | None
        The record, or None if nothing was observed since the level started.

    Raises
    ------
    SaveError
        If ``observed.json`` does not hold a valid `Observed` record.
    """
    return cast(Observed | None, _read(OBSERVED_FILE, Observed))


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


def ensure_gitconfig(initial: str) -> Path:
    """
    Create the game's global git configuration if it does not exist yet.

    An existing file is never overwritten: the player sets their name in it while playing.

    Parameters
    ----------
    initial : str
        Content of a new file (`firstcommit.gitcmd.BASE_CONFIG`).

    Returns
    -------
    Path
        The configuration file.
    """
    path = home() / GITCONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    # Mode "x" creates the file only if it is missing, in one step, so two processes cannot both write it.
    with contextlib.suppress(FileExistsError), path.open("x") as handle:
        handle.write(initial)
    return path


def erase() -> None:
    """Delete the progress, the level in progress, the last observation and the game's git configuration, damaged or not."""
    for name in (PROGRESS_FILE, ACTIVE_FILE, OBSERVED_FILE, GITCONFIG_FILE):
        (home() / name).unlink(missing_ok=True)


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
    path = home() / name
    try:
        data = store.read_json(path)
    except ValueError as error:
        raise SaveError(f"{path} is damaged: {error}") from error
    if data is not None:
        problem = _mismatch(data, record, "")
        if problem is not None:
            raise SaveError(f"{path} is damaged: {problem}")
    return data


def _mismatch(value: Any, expected: Any, where: str) -> str | None:
    """
    Compare a JSON value with a type from the records above.

    Parameters
    ----------
    value : Any
        Value read from JSON.
    expected : Any
        A `TypedDict`, ``dict[str, X]``, ``X | None``, ``int``, ``str``, ``bool`` or ``Any``.
    where : str
        Dotted path of the value in its file, for the message; empty for the whole record.

    Returns
    -------
    str | None
        What is wrong with the first field that does not match, or None if the value matches.
    """
    problem = None
    if typing.is_typeddict(expected):
        problem = _record_mismatch(value, expected, where)
    elif typing.get_origin(expected) is dict:
        problem = _mapping_mismatch(value, typing.get_args(expected)[1], where)
    elif typing.get_origin(expected) is types.UnionType:
        (present,) = [option for option in typing.get_args(expected) if option is not type(None)]
        problem = None if value is None else _mismatch(value, present, where)
    elif expected is int and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
        problem = f"`{where}` must be a whole number, zero or more, not {value!r}"
    elif expected in (str, bool) and not isinstance(value, expected):
        problem = f"`{where}` must be a {expected.__name__}, not {value!r}"
    return problem


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
    fields = typing.get_type_hints(record)
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


def _mapping_mismatch(value: Any, item: Any, where: str) -> str | None:
    """
    Compare a JSON value with ``dict[str, item]``.

    Parameters
    ----------
    value : Any
        Value read from JSON.
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
    return _first(_mismatch(entry, item, f"{where}.{key}") for key, entry in value.items())


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
