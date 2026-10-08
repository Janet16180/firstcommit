"""Save helpers: a game's home directory, a lock on it, and JSON files replaced atomically."""

import contextlib
import fcntl
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def home(variable: str, default: str) -> Path:
    """
    Return the directory where a game keeps its files.

    Parameters
    ----------
    variable : str
        Environment variable that overrides the default, e.g. ``"GAME_HOME"``.
    default : str
        Directory used when the variable is not set, e.g. ``"~/.game"``.

    Returns
    -------
    Path
        ``$variable`` with ``~`` expanded if set, otherwise ``default`` expanded.

    Raises
    ------
    ValueError
        If the result is not an absolute path (an empty variable included):
        a relative one would split the save between processes in different directories.
    """
    configured = os.environ.get(variable, default)
    # os.path keeps an unknown ~user as written; Path.expanduser would raise RuntimeError.
    path = Path(os.path.expanduser(configured))
    if not path.is_absolute():
        raise ValueError(f"{variable} must be an absolute path (or start with ~), not {configured!r}")
    return path


@contextlib.contextmanager
def lock(home: Path) -> Iterator[None]:
    """
    Hold an exclusive lock on a game's save files for the duration of a block.

    The lock is an ``flock`` on ``<home>/.lock``, so it holds across processes: a command
    line and a web server changing the same save take turns.

    Parameters
    ----------
    home : Path
        The game's home directory, as returned by `home`; created if missing.

    Yields
    ------
    None
        Control returns to the block while the lock is held.
    """
    path = home / ".lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def read_json(path: Path) -> dict[str, Any] | None:
    """
    Read a JSON file.

    Parameters
    ----------
    path : Path
        File to read.

    Returns
    -------
    dict[str, Any] | None
        The parsed object, or None if the file does not exist.

    Raises
    ------
    ValueError
        If the file is not valid JSON, or holds something other than an object.
    """
    try:
        text = path.read_text()
    except FileNotFoundError:
        return None
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not hold a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    """
    Atomically and durably replace a JSON file.

    The new content is written to a temporary file and synced to disk before it replaces the
    file, and the folder is synced after, so a crash leaves either the old file or the new one,
    never an empty one.

    Parameters
    ----------
    path : Path
        File to write; missing parent directories are created.
    data : dict[str, Any]
        JSON-serializable object, written with sorted keys and an indent of 2.

    Raises
    ------
    TypeError
        If `data` is not JSON-serializable; the file is then left as it was.
    """
    text = json.dumps(data, indent=2, sort_keys=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    folder = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(folder)
    finally:
        os.close(folder)
