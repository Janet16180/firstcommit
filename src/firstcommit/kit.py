"""
The level authors' toolkit: what a level is made of, and the helpers a level may use.

A level module imports this module and the standard library only (AUTHORING.md section 3):
the types of its scene, card, quest and reactions, its lab, git kept to the game's configuration, the snapshot
its checks read, helpers that parse what a player types, and the two-person playground
(`setup_playground` builds it in a lab; `press` runs one of its buttons, the same real command
the page's button runs, so a level can prepare a state such as "Alex already pushed").
"""

import hashlib
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from firstcommit.commands import type_line
from firstcommit.gitcmd import GAME, PLAYER, Person
from firstcommit.gitcmd import output as git
from firstcommit.gitcmd import run as git_run
from firstcommit.lab import Lab
from firstcommit.markup import code
from firstcommit.playground import on_push, press, setup_github
from firstcommit.playground import setup as setup_playground
from firstcommit.reactions import LIST_HIDDEN, Outcome, ReactionRule, matches
from firstcommit.records import Art, Command
from firstcommit.repomap import (
    Commit,
    FileEntry,
    Ref,
    Snapshot,
    conflicted,
    conflicts,
    ghosts,
    in_history,
    is_ancestor,
    mode_changed,
    nested,
    reachable,
    snapshot,
    staged,
    unstaged,
    untracked,
    version,
)

__all__ = [
    "GAME",
    "LIST_HIDDEN",
    "PICK_ONE",
    "PLAYER",
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
    "StepText",
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
    "conflicts",
    "creating",
    "ghosts",
    "digest",
    "git",
    "git_run",
    "in_history",
    "is_ancestor",
    "is_hash_of",
    "mode_changed",
    "nested",
    "on_push",
    "parse_int",
    "picking",
    "press",
    "reachable",
    "reaches_github",
    "type_line",
    "typed",
    "typing",
    "setup_github",
    "setup_playground",
    "snapshot",
    "switching",
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
class StepText:
    """
    A quest step's texts in another language, by the step's id in the level's Spanish module (``STEPS``).

    Each field matches the step's own: ``question`` for an answer or choice step, ``placeholder``
    for an answer step, ``options`` (in the same order) and ``reveal`` for a choice step; empty
    where the step has none.
    """

    text: str
    more: str = ""
    question: str = ""
    placeholder: str = ""
    options: tuple[str, ...] = ()
    reveal: str = ""


@dataclass(frozen=True)
class LevelEvent:
    """
    Something a level makes happen in its lab at a moment of the play: Alex pushing, a staged scenario.

    ``run(lab, state)`` makes the change with real git (`git`, `press`), like `setup`. With no
    ``goal`` it runs when the level starts, right after a snapshot of the lab as set up, which the
    level's first observation shows; with a quest step's id, right after the player reaches that
    goal. Either way the page's next observation tells the change,
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


CREATE_OPTIONS = r"(switch (-c|-C|--create|--force-create)|checkout (-b|-B))"
"""The options that make a branch before moving onto it: ``git switch``'s and their older ``git checkout`` forms."""


def switching(branch: str | None = None) -> str:
    """
    Give the pattern of a line that moves onto a branch, in either form: ``git switch`` or ``git checkout``.

    Parameters
    ----------
    branch : str | None
        The branch, or None for any.

    Returns
    -------
    str
        A pattern for `typed` and `after`; a line that also makes the branch (`creating`) does not fit.
    """
    name = rf"( -\S+)* {re.escape(branch)}( |$)" if branch is not None else r"\b"
    return rf"git (switch|checkout)(?!.* (-c|-C|-b|-B|--create|--force-create)\b){name}"


def creating(branch: str | None = None) -> str:
    """
    Give the pattern of a line that makes a branch and moves onto it, in either form: ``git switch -c`` or ``git checkout -b``.

    Parameters
    ----------
    branch : str | None
        The branch, or None for any.

    Returns
    -------
    str
        A pattern for `typed` and `after`.
    """
    name = rf" {re.escape(branch)}( |$)" if branch is not None else r"\b"
    return rf"git {CREATE_OPTIONS}{name}"


def typing(line: str) -> Callable[[Lab, State, list[Command]], str | None]:
    """
    Make a quest action that types one line in the project folder, for a level's ``QUEST_ACTIONS``.

    Parameters
    ----------
    line : str
        The line, as the player types it.

    Returns
    -------
    Callable[[Lab, State, list[Command]], str | None]
        The action: it types the line with `type_line`, adds it to the lines typed, and returns
        None, as a watch step takes no answer.
    """

    def act(lab: Lab, state: State, typed: list[Command]) -> str | None:
        typed.append(type_line(lab.project, line))
        return None

    return act


def picking(option: str) -> Callable[[Lab, State, list[Command]], str | None]:
    """
    Make a quest action that answers a prediction with one of its options, for a level's ``QUEST_ACTIONS``.

    Parameters
    ----------
    option : str
        One of the choice step's options.

    Returns
    -------
    Callable[[Lab, State, list[Command]], str | None]
        The action: it types nothing and returns the option.
    """

    def act(lab: Lab, state: State, typed: list[Command]) -> str | None:
        return option

    return act


PICK_ONE = "Pick one of the options."
"""What `choose` says to an answer that is none of the options."""


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
    return Verdict(chosen, step.reveal if chosen else PICK_ONE)


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


def reaches_github(lab: Lab, clone: Path, url: str) -> bool:
    """
    Tell whether a remote's address leads to the lab's stand-in GitHub, however it is written.

    Git reads a relative path from the clone's top folder, so ``../github.com/moonbase/project.git``,
    ``./../github.com/moonbase/project.git``, a trailing slash, the absolute path and a ``file://`` address all
    reach the same repository.

    Parameters
    ----------
    lab : Lab
        The lab, with its GitHub.
    clone : Path
        The top folder of the clone whose remote it is.
    url : str
        The remote's address, as ``git remote get-url`` prints it.

    Returns
    -------
    bool
        True when the address names the lab's GitHub folder.
    """
    path = Path(url.removeprefix("file://"))
    target = path if path.is_absolute() else clone / path
    return bool(url) and target.resolve() == lab.github.resolve()
