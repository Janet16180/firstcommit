"""
The level authors' toolkit: what a level is made of, and the helpers a level may use.

A level module imports this module and the standard library only (AUTHORING.md section 3):
the types of its scene, card, lesson, quest and reactions, its lab, git kept to the game's configuration, the snapshot
its checks read, helpers that parse what a player types, and the two-person playground
(`setup_playground` builds it in a lab; `press` runs one of its buttons, the same real command
the page's button runs, so a level can prepare a state such as "Alex already pushed").
"""

import hashlib
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from firstcommit.commands import type_line
from firstcommit.gitcmd import GAME, Person
from firstcommit.gitcmd import output as git
from firstcommit.gitcmd import run as git_run
from firstcommit.lab import Lab
from firstcommit.markup import code
from firstcommit.playground import press, setup_github
from firstcommit.playground import setup as setup_playground
from firstcommit.reactions import LIST_HIDDEN, Outcome, ReactionRule, matches
from firstcommit.records import Art, Command
from firstcommit.repomap import (
    Commit,
    FileEntry,
    Ref,
    Snapshot,
    conflicted,
    mode_changed,
    nested,
    snapshot,
    staged,
    unstaged,
    untracked,
    version,
)

__all__ = [
    "GAME",
    "LIST_HIDDEN",
    "AnswerCheck",
    "AnswerStep",
    "ChoiceStep",
    "Art",
    "Command",
    "CommandCard",
    "Commit",
    "FileEntry",
    "Lab",
    "LevelEvent",
    "Person",
    "ReactionRule",
    "ReadStep",
    "Ref",
    "SceneFrame",
    "Slide",
    "Snapshot",
    "State",
    "Step",
    "Typed",
    "Verdict",
    "Watch",
    "WatchStep",
    "after",
    "answer_is",
    "choose",
    "code",
    "conflicted",
    "digest",
    "git",
    "git_run",
    "is_hash_of",
    "mode_changed",
    "nested",
    "parse_int",
    "press",
    "type_line",
    "typed",
    "setup_github",
    "setup_playground",
    "snapshot",
    "staged",
    "unstaged",
    "untracked",
    "version",
]

INTEGER = re.compile(r"[0-9]{1,10}")
HEX = re.compile(r"[0-9a-f]+")
MIN_HASH_PREFIX = 4

State = dict[str, Any]


@dataclass(frozen=True)
class Verdict:
    """
    The result of a check: whether it passed, and what to tell the player.

    ``lost`` says the player's work is gone for good (read from facts `setup` saved), so the page
    offers to start the level again; a solved verdict is never lost.
    """

    solved: bool
    message: str
    lost: bool = False

    def __post_init__(self) -> None:
        """Refuse a verdict that is both solved and lost: a bug in the level."""
        if self.solved and self.lost:
            raise ValueError("a solved verdict cannot say the work is lost")


Typed = Sequence[Command]
"""Every line typed in the game's terminal since the level started, oldest first, with its exit status."""

AnswerCheck = Callable[[Lab, State, str], Verdict]
Watch = Callable[[Lab, State, Typed], Verdict]


@dataclass(frozen=True)
class SceneFrame:
    """
    One picture of a level's scene, Rama's short animated explanation shown the first time the level opens.

    ``art`` names the picture (the page draws it); ``text`` is what Rama says under it, as
    markup. A scene's text is never filled from a level's state: it is shown before the level
    starts.
    """

    art: Art
    text: str


@dataclass(frozen=True)
class CommandCard:
    """
    The card a level adds to the player's collection once solved: a command and what it does.

    ``command`` is shown as written (``git add <file>``); ``text`` is markup.
    """

    command: str
    text: str


@dataclass(frozen=True)
class Slide:
    """
    One slide of a lesson.

    ``run`` holds shell lines added to the lesson's demonstration repository. The game runs
    the lesson's ``run`` lines in order, in an empty folder, with a fixed identity and date,
    and shows each of this slide's commands with its real output; ``view`` picks the figure:
    the repository map, the three areas, your computer's places (working folder, staging area
    and repository, with the arrows the slide's change lit), the object database, the commands
    only, or nothing. ``more`` is optional text the page folds under "More", below ``text``.
    """

    id: str
    title: str
    text: str
    run: str = ""
    view: Literal["map", "areas", "places", "objects", "terminal", "none"] = "map"
    more: str = ""


@dataclass(frozen=True)
class AnswerStep:
    """
    A quest step that asks the player a question about what they saw.

    ``check`` judges the answer. ``command`` is a suggestion the page can type into the terminal
    (never with Enter); ``placeholder`` is plain text shown in the empty answer box; ``more`` is
    optional text the page folds under "More", below ``text``.
    """

    id: str
    text: str
    question: str
    check: AnswerCheck
    command: str = ""
    placeholder: str = ""
    more: str = ""


@dataclass(frozen=True)
class WatchStep:
    """
    A quest step that passes once the lab shows the player did it.

    ``watch`` is polled while the player works; its message is shown live (AUTHORING 3.3).
    ``more`` is optional text the page folds under "More", below ``text``.
    """

    id: str
    text: str
    watch: Watch
    command: str = ""
    more: str = ""


@dataclass(frozen=True)
class ReadStep:
    """A quest step the player reads, then continues when ready; ``more`` is folded under "More"."""

    id: str
    text: str
    command: str = ""
    more: str = ""


@dataclass(frozen=True)
class ChoiceStep:
    """
    A quest step that asks the player to predict, from two or three options, before they see.

    Any option passes and nothing is lost for a wrong guess: ``reveal`` then says what really
    happens, whichever was chosen (`choose`). ``options`` are both the text the page shows and
    the value it sends back. ``more`` is folded under "More", as on every step.
    """

    id: str
    text: str
    question: str
    options: tuple[str, ...]
    reveal: str
    command: str = ""
    more: str = ""


@dataclass(frozen=True)
class LevelEvent:
    """
    Something a level makes happen in its lab at a moment of the play: Alex pushing, a staged scenario.

    ``run(lab, state)`` makes the change with real git (`git`, `press`), like `setup`. With no
    ``goal`` it runs right after the level's first observation; with a quest step's id, right
    after the player reaches that goal. Either way the page's next observation tells the change,
    so it animates what really happened. Each event runs once per play.
    """

    id: str
    run: Callable[[Lab, State], None]
    goal: str = ""


Step = AnswerStep | WatchStep | ReadStep | ChoiceStep
"""One step of a guided quest: each kind carries exactly what it needs, so no other shape exists."""


def typed(lines: Typed, pattern: str, outcome: Outcome = "any") -> bool:
    r"""
    Tell whether the player typed a line that starts as a pattern says and ended as asked.

    Parameters
    ----------
    lines : Typed
        The lines typed since the level started.
    pattern : str
        A regular expression matched at the start of each line, its runs of spaces made single,
        such as ``git status\b``.
    outcome : Outcome
        How the line must have ended: ``"any"``, ``"ok"`` (status 0), ``"failed"`` or
        ``"unknown-command"``.

    Returns
    -------
    bool
        True if any line fits.
    """
    return any(matches(line, pattern, outcome) for line in lines)


def after(lines: Typed, pattern: str) -> list[Command]:
    """
    Give the lines typed after the last line that fits a pattern and worked (status 0).

    Parameters
    ----------
    lines : Typed
        The lines typed since the level started.
    pattern : str
        A regular expression matched at the start of each line, as in `typed`.

    Returns
    -------
    list[Command]
        The lines after it, oldest first; every line when none fits.
    """
    worked = [index for index, line in enumerate(lines) if matches(line, pattern, "ok")]
    return list(lines[worked[-1] + 1 :] if worked else lines)


def choose(step: ChoiceStep, answer: str) -> Verdict:
    """
    Judge a prediction: any of the step's options passes, with its reveal.

    Parameters
    ----------
    step : ChoiceStep
        The step.
    answer : str
        What the page sent back.

    Returns
    -------
    Verdict
        Passed with ``step.reveal`` for an option, exactly as written; else not passed.
    """
    chosen = answer in step.options
    return Verdict(chosen, step.reveal if chosen else "Pick one of the options.")


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
