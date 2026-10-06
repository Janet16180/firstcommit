"""
The level authors' toolkit: what a level is made of, and the helpers a level may use.

A level module imports this module and the standard library only (AUTHORING.md section 3):
the types of its lesson and quest, its lab, git kept to the game's configuration, the snapshot
its checks read, and helpers that parse what a player types.
"""

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from firstcommit.gitcmd import GAME, Person
from firstcommit.gitcmd import output as git
from firstcommit.gitcmd import run as git_run
from firstcommit.repomap import Snapshot, snapshot

__all__ = [
    "GAME",
    "AnswerCheck",
    "Lab",
    "Person",
    "Slide",
    "Snapshot",
    "State",
    "Step",
    "Verdict",
    "Watch",
    "answer_is",
    "digest",
    "git",
    "git_run",
    "is_hash_of",
    "parse_int",
    "snapshot",
]

INTEGER = re.compile(r"[0-9]{1,10}")
HEX = re.compile(r"[0-9a-f]+")
MIN_HASH_PREFIX = 4

State = dict[str, Any]


@dataclass(frozen=True)
class Verdict:
    """The result of a check: whether it passed, and what to tell the player."""

    solved: bool
    message: str


@dataclass(frozen=True)
class Lab:
    """
    The folders of one level's lab. Everything a level creates lives under ``root``.

    ``project`` is the player's repository (the terminal opens there when it exists, else in
    ``root``); ``github`` is the bare repository that stands in for GitHub, for levels with a
    remote.
    """

    root: Path

    @property
    def project(self) -> Path:
        """The player's working folder."""
        return self.root / "project"

    @property
    def github(self) -> Path:
        """The bare repository that plays GitHub."""
        return self.root / "github" / "project.git"


AnswerCheck = Callable[[Lab, State, str], Verdict]
Watch = Callable[[Lab, State], Verdict]


@dataclass(frozen=True)
class Slide:
    """
    One slide of a lesson.

    ``run`` holds shell lines added to the lesson's demonstration repository. The game runs
    the lesson's ``run`` lines in order, in an empty folder, with a fixed identity and date,
    and shows each of this slide's commands with its real output; ``view`` picks the figure:
    the repository map, the three areas, the object database, the commands only, or nothing.
    """

    id: str
    title: str
    text: str
    run: str = ""
    view: Literal["map", "areas", "objects", "terminal", "none"] = "map"


@dataclass(frozen=True)
class Step:
    """
    One step of a guided quest.

    A step is one of three kinds:

    - an answer step has a ``question`` and a ``check`` of the player's answer;
    - a watch step has a ``watch`` that passes once the lab shows the step was done;
    - a read step has neither, and the player continues when ready.

    ``command`` is a suggestion the page can type into the terminal (never with Enter).
    """

    id: str
    text: str
    command: str = ""
    question: str = ""
    placeholder: str = ""
    check: AnswerCheck | None = None
    watch: Watch | None = None


def parse_int(text: str | None) -> int | None:
    """
    Read a small non-negative integer typed by the player.

    Only 1 to 10 ASCII digits are accepted: ``str.isdigit()`` lets through characters such as
    ``"²"`` that ``int()`` rejects, and ``int()`` refuses strings longer than 4300 digits.

    Parameters
    ----------
    text : str | None
        Raw answer; surrounding whitespace is ignored.

    Returns
    -------
    int | None
        The number, or None if the text is not one.
    """
    if text is None or not INTEGER.fullmatch(text.strip()):
        return None
    return int(text.strip())


def is_hash_of(text: str | None, full_hash: str) -> bool:
    """
    Tell whether the player typed an object id, whole or abbreviated, as git accepts it.

    Parameters
    ----------
    text : str | None
        Raw answer; surrounding whitespace and letter case are ignored.
    full_hash : str
        The full object id it should name.

    Returns
    -------
    bool
        True for at least `MIN_HASH_PREFIX` hexadecimal characters that start ``full_hash``.
    """
    typed = "" if text is None else text.strip().lower()
    return len(typed) >= MIN_HASH_PREFIX and HEX.fullmatch(typed) is not None and full_hash.lower().startswith(typed)


def digest(answer: str) -> str:
    """
    Hash an answer so the expected value is not stored in clear text.

    Parameters
    ----------
    answer : str
        Answer text; surrounding whitespace is ignored.

    Returns
    -------
    str
        Hex SHA-256 of the stripped answer.
    """
    return hashlib.sha256(answer.strip().encode()).hexdigest()


def answer_is(answer: str | None, expected_digest: str) -> bool:
    """
    Compare a submitted answer with a stored digest.

    Parameters
    ----------
    answer : str | None
        What the player submitted.
    expected_digest : str
        Value produced by `digest` during setup.

    Returns
    -------
    bool
        True if the answer matches.
    """
    return answer is not None and digest(answer) == expected_digest
