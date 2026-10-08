"""
Every player action, in one place: the only module the command line and the web routes call.

Each function that changes the save holds its lock (termlab's store) for the whole
read-modify-write, and returns a plain record that is ready to send as JSON. A level's text is
filled from its state (``{{key}}``) and parsed into blocks (`firstcommit.markup`), so the
interfaces only render. In a step's command each value is filled as one shell word. A check's
or a watch's message is parsed only, never filled: it may hold names the player chose. Game
rules never live in the interfaces (Ring Zero audit ARCH-1).

The game speaks the player's language (`set_language`): a level's, a deck's and a chapter's
texts are read in it, and a message (a verdict, a reaction, the game's own) is turned into it
from its English text (`_messages`). The changes the page animates and the playground's
explanations are in English only.

Records returned here are the API contract of the web routes: changing a field is a change to
the page too. Every field the player reads is parsed blocks; every value the page sends back
(a step's command, a card option's ``value``, an answer) stays a raw string. Text the player sends (answers, card replies) may hold anything; characters that
UTF-8 cannot encode, such as the lone surrogates JSON can carry, are replaced here, so levels and
cards only ever see a wrong answer. Errors the interfaces handle:

- `UnknownIdError`: an unknown level, chapter or card id, or a playground person or button (the
  routes answer 404). It is raised only by the one lookup of each kind of id, at the top of a
  function, so a ``KeyError`` from a level's setup or the scoring stays what it is: a bug;
- `NotPlayingError`: an action on the level in progress when there is none (409);
- `NoPlaygroundError`: a playground button pressed in a level that has no playground (409);
- `ButtonOffError`: a playground button pressed while it is off (409); its message is the
  reason, as the button shows it (handed on from `firstcommit.playground`);
- `SaveError`: a damaged save file (``firstcommit reset --yes`` starts over).

The interfaces import nothing else from the game's lower layers: `SaveError` and `home` are
handed on from `firstcommit.save`, and `shell_environment` builds the player's shell.

Anything else is a bug.
"""

import dataclasses
import functools
import os
import random
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, get_args

from firstcommit import (
    cards,
    changes,
    commands,
    explanations,
    freeplay,
    gitcmd,
    kit,
    markers,
    markup,
    playground,
    reactions,
    repomap,
    runner,
    save,
    score,
)
from firstcommit.cards import CardKind
from firstcommit.changes import Event
from firstcommit.chapters import BLURBS, CHAPTERS
from firstcommit.lab import Lab
from firstcommit.markup import Block
from firstcommit.playground import ButtonOffError as ButtonOffError
from firstcommit.reactions import ReactionRule
from firstcommit.records import (
    Art,
    ButtonView,
    Command,
    Commit,
    Conflict,
    FileTexts,
    Language,
    MarkedFile,
    Moment,
    Mood,
    Pictures,
    PlaygroundView,
    Press,
    ReflogEntry,
    Seen,
    StartId,
    Target,
    View,
)
from firstcommit.records import Keep as Keep
from firstcommit.records import Who as Who
from firstcommit.repomap import Snapshot
from firstcommit.save import Payout
from firstcommit.save import SaveError as SaveError
from firstcommit.save import home as home
from firstcommit.score import Rank

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
SHOWN_LINE = re.compile(r"^ *\$ (.+)$", re.MULTILINE)
"""A shell line a hint shows: ``$ `` and the line, in a code block."""
DEV_VARIABLE = "FIRSTCOMMIT_DEV"
"""Set to ``1`` (``firstcommit serve --dev``) for dev mode: each level's solution on its page."""
MIN_GIT = (2, 32)
TARGET_GIT = (2, 43)
MIN_PYTHON = (3, 12)
GIT_VERSION = re.compile(r"git version (\d+)\.(\d+)")
CHALLENGE_MOODS = ("warn", "err")
"""What Rama still says in a challenge: danger and errors, never guidance."""
QUEST_FIRST = "The guided quest is not finished yet: step {step} of {steps} is next."
LANGUAGES: tuple[Language, ...] = get_args(Language)
SEEN: tuple[Seen, ...] = get_args(Seen)
PLAYGROUND_VIEWS: tuple[PlaygroundView, ...] = get_args(PlaygroundView)
"""The free playground's views."""
PEOPLE: tuple[Who, ...] = get_args(Who)
"""The free playground's two people: you and Alex."""
KEEPS: tuple[Keep, ...] = get_args(Keep)
"""What a resolve may keep of a conflict block."""
SPANISH = {
    QUEST_FIRST: "La misión guiada todavía no termina: el siguiente es el paso {step} de {steps}.",
    kit.PICK_ONE: "Elige una de las opciones.",
}
"""The game's own messages in Spanish, by their English text."""


class LevelSummary(TypedDict):
    """
    A level as the map of chapters lists it.

    ``stars`` is its best result, 0 while it is not done, else 1 to 3; ``challenge`` marks a
    level the map shows as a boss node.
    """

    id: str
    title: str
    difficulty: int
    xp: int
    command: str
    stars: int
    challenge: bool
    done: bool
    has_quest: bool


class ChapterSummary(TypedDict):
    """A chapter and its levels, in play order; ``blurb`` is one line under its name."""

    id: str
    title: str
    blurb: str
    levels: list[LevelSummary]
    cards: int


class CommandCard(TypedDict):
    """The card a level adds to the player's collection once solved: its command as written, and what it does."""

    level: str
    command: str
    text: list[Block]


class SceneFrameView(TypedDict):
    """One picture of a level's scene and what Rama says under it."""

    art: Art
    text: list[Block]


class Reaction(TypedDict):
    """What Rama says about one typed line (`firstcommit.reactions`), and the moment the page plays with it, if any."""

    line: str
    mood: Mood
    text: list[Block]
    moment: Moment | None


class ActiveView(TypedDict):
    """
    The level being played: how far the quest is, and the hints, attempts and lines typed so far.

    ``auto_check`` says whether the page may check the level by itself: only once the quest is
    done (`check` refuses an automatic check before that anyway). ``commands`` counts the lines
    typed in the game's terminal since the level started, and ``stars`` the stars still in play
    (`firstcommit.score.stars`). ``done`` holds the ids of the quest's goals met so far, in quest
    order: the first ``step`` ones in a guided quest, any of them in a challenge.
    """

    level: str
    step: int
    steps: int
    hints: int
    hints_total: int
    attempts: int
    started: str
    auto_check: bool
    commands: int
    stars: int
    done: list[str]


class Status(TypedDict):
    """
    The dashboard; ``max_difficulty`` is the highest difficulty a level can have, so the page can show the scale.

    ``chapters`` lists every chapter; one with no level yet is still to come.
    ``collection`` holds the card of each finished level, in play order. ``language`` is the
    one the game speaks. ``dev`` says whether dev mode is on (`dev_mode`).
    """

    language: Language
    xp: int
    rank: Rank
    chapters: list[ChapterSummary]
    active: ActiveView | None
    last_payout: Payout | None
    dev: bool
    cards_due: int
    max_difficulty: int
    collection: list[CommandCard]


class Choice(TypedDict):
    """One option of a choice or predict card, or of a prediction step: the page shows ``text`` and sends ``value`` back as the reply."""

    value: str
    text: list[Block]


class StepView(TypedDict):
    """
    A guided-quest step as the page shows it (its checks stay on the server).

    ``question`` is empty unless it is an answer or a choice step; ``placeholder`` is empty unless
    it is an answer step; ``choices`` are a choice step's options, empty for every other kind.
    ``look`` names what the page rings in gold while the step is current: commit subjects or
    ``"HEAD"``, empty for most steps.
    """

    id: str
    kind: Literal["answer", "watch", "read", "choice"]
    text: list[Block]
    command: str
    question: list[Block]
    placeholder: str
    choices: list[Choice]
    more: list[Block]
    look: list[str]


class Solution(TypedDict):
    """
    How a level in progress is solved, for dev mode only (`dev_mode`).

    ``lines`` are the shell lines of the level's last hint, in order, its placeholders filled
    (`solution_lines`); ``answers`` the answer of each answer or choice step by step id, None
    while the lab cannot give it yet (a count read from a clone not made yet); ``answer`` the
    answer to the level's own question (`runner.Level` ``answer``), None for a level without one
    or while the lab cannot give it yet.
    """

    lines: list[str]
    answers: dict[str, str | None]
    answer: str | None


class LevelView(TypedDict):
    """
    A level's page: what to do, the quest steps and how many hints exist.

    ``question`` and ``placeholder`` are empty for a level checked against the repository only.
    ``hints`` are the hints already revealed while this level is in progress (empty otherwise),
    so a reloaded page can show what the player paid for. ``debrief`` is set once the player has
    finished the level, filled from its last play, so it shows even when the level was solved
    from the terminal. ``scene`` is empty for a level without one; ``scene_seen`` says whether
    the player has seen it (`see_scene`). ``view`` is the view the level screen opens on, ``tape`` says whether it shows the black box's
    tape of HEAD's moves (`Observation` ``reflog``), ``pictures`` the teaching pictures the level
    shows and ``target`` a challenge's target chart (`firstcommit.records.Pictures`, `Target`),
    each None for a level that keeps its view and tabs, and
    ``solution`` is None unless dev mode is on and the level is in progress (`Solution`).
    ``views_seen`` every view (and the band) the page has shown being born, in the order seen
    (`see_view`), your station from the start, the same for every level. ``challenge`` marks a level whose goals are met in any
    order, with no guidance; its ``card`` is None until the player has solved it once, since the
    card names the command.
    """

    id: str
    chapter: str
    chapter_title: str
    title: str
    difficulty: int
    xp: int
    command: str
    par: int
    scene: list[SceneFrameView]
    scene_seen: bool
    view: View
    tape: bool
    pictures: Pictures | None
    target: Target | None
    views_seen: list[Seen]
    solution: Solution | None
    card: CommandCard | None
    challenge: bool
    briefing: list[Block]
    question: list[Block]
    placeholder: str
    steps: list[StepView]
    hints_total: int
    hints: list[list[Block]]
    debrief: list[Block] | None


class EventView(TypedDict):
    """One "what just happened" event, its text parsed like every other text the page shows."""

    kind: str
    text: list[Block]


class StepResult(TypedDict):
    """
    The result of a quest step: whether a goal was met, feedback, and where the quest stands now (``done``, as in `ActiveView`).

    ``lost`` says a step checked (in a challenge, any goal not met yet) found the player's work
    gone for good; its message is then the feedback, and the page offers to start again.
    """

    correct: bool
    message: list[Block]
    step: int
    quest_done: bool
    done: list[str]
    lost: bool


class CheckResult(TypedDict):
    """
    The result of checking the level; ``payout`` and ``debrief`` are set once it is solved.

    ``stars`` are the stars the solve earned, 0 while unsolved; ``new_card`` is the level's card
    the first time it is solved, else None. ``lost`` says the player's work is gone for good, so
    the page offers to start the level again (never while solved).
    """

    solved: bool
    message: list[Block]
    payout: Payout | None
    debrief: list[Block] | None
    stars: int
    new_card: CommandCard | None
    lost: bool


class HintView(TypedDict):
    """A revealed hint, how many are used out of how many, and what this one cost."""

    hint: list[Block]
    used: int
    total: int
    cost: int


class Observation(TypedDict):
    """
    The live lab and what changed in it since the last observation.

    ``github`` and ``teammate`` (the teammate's clone of the playground, `firstcommit.playground`)
    are None when the level has none. ``events`` tells the changes in the player's repository and
    the stand-in GitHub; ``teammate_events`` those in the teammate's clone, kept apart because an
    event's sentence does not say which clone it happened in. ``buttons`` is each person's bar of
    the playground as it stands now (`firstcommit.playground.buttons`), and empty for a level
    without one. ``commands`` are the lines typed in the game's terminal since the last
    observation, oldest first (`firstcommit.commands`); like the events, there are none at a
    level's first observation. ``reactions`` are what Rama says about those lines, one per line
    a rule fits, oldest first (`firstcommit.reactions`, the level's own rules first).
    ``conflicts`` gives both sides of each file in conflict in the player's repository
    (`firstcommit.repomap.conflicts`), empty when there is none. ``reflog`` gives HEAD's moves in
    the player's repository, newest first (`firstcommit.repomap.reflog`), and ``ghosts`` the
    commits only those moves still reach (`firstcommit.repomap.ghosts`). ``texts`` are the
    folder's and the staging area's texts of the files the level's desk draws
    (`firstcommit.repomap.file_texts`), empty for a level without; ``graph`` the lines of
    ``git log --oneline --graph --all`` (`firstcommit.repomap.graph`), None unless the level shows
    it.
    """

    level: str
    project: Snapshot
    github: Snapshot | None
    teammate: Snapshot | None
    events: list[EventView]
    teammate_events: list[EventView]
    buttons: dict[Who, list[ButtonView]]
    commands: list[Command]
    reactions: list[Reaction]
    conflicts: list[Conflict]
    reflog: list[ReflogEntry]
    ghosts: list[Commit]
    texts: list[FileTexts]
    graph: list[str] | None


class ChapterName(TypedDict):
    """A chapter's id and its title in the player's language."""

    id: str
    title: str


class StartView(TypedDict):
    """
    One starting point of the free playground, in the player's language (`firstcommit.freeplay.Start`).

    ``alex`` says whether Alex's terminal is shown at first, and ``uses`` the chapters whose
    commands the start uses, in order; none of them locks it.
    """

    id: StartId
    title: str
    blurb: str
    banner: str
    view: PlaygroundView
    mothership: bool
    alex: bool
    uses: list[ChapterName]


class PlaygroundPrefs(TypedDict):
    """
    Where the player is in the free playground: the start, the view, whether Alex's terminal is shown, and whose repository the view draws.

    ``started`` changes each time the start is built, a Start over included, so the page knows to
    open new terminals in the new clones. ``alex`` is remembered for each start; ``view`` and ``whose`` go back to the start's own view
    and to you when a start is built.
    """

    start: StartId
    started: str
    view: PlaygroundView
    alex: bool
    whose: Who


class PlaygroundStatus(TypedDict):
    """The free playground's starts and where the player left it, None before the first visit."""

    starts: list[StartView]
    current: PlaygroundPrefs | None


class CloneView(TypedDict):
    """
    One person's repository in the free playground, as the views draw it beside its snapshot.

    ``conflicts`` are its files in conflict (`firstcommit.repomap.conflicts`) and ``marked`` the
    same files read for their conflict blocks (`firstcommit.markers`), for those that are plain
    files of at most `firstcommit.repomap.MAX_TEXT` bytes. ``texts`` are every file of the working
    folder (`firstcommit.repomap.file_texts`). ``graph`` is ``git log --oneline --graph --all``,
    None without a repository. ``typed`` are the lines typed in that person's terminal since the
    start was built, oldest first.
    """

    conflicts: list[Conflict]
    marked: list[MarkedFile]
    reflog: list[ReflogEntry]
    ghosts: list[Commit]
    texts: list[FileTexts]
    graph: list[str] | None
    typed: list[Command]


class PlaygroundObservation(TypedDict):
    """
    The free playground as it is now: each repository's snapshot, and each person's repository as the views draw it.

    ``started`` is the build it was read from (`PlaygroundPrefs`). ``github`` and ``teammate``
    (Alex's clone) are None in a start without a mothership, and ``alex`` with them.
    """

    start: StartId
    started: str
    project: Snapshot
    github: Snapshot | None
    teammate: Snapshot | None
    you: CloneView
    alex: CloneView | None


class ResolveView(TypedDict):
    """A file of the free playground as a resolve wrote it, read again for the conflict panel."""

    file: MarkedFile


class PressView(TypedDict):
    """
    One press of a playground button: the command and what it printed, the lab before and after it, and what it shows.

    ``before`` is the lab just before the press: its events are what the terminal changed since
    the last observation. ``observation`` is the lab right after it: its events are the press's
    own. ``explanation`` says why the press turned out as it did (`firstcommit.explanations`), or is
    None when the figure says enough; ``fix`` is a button id it offers, or None, and ``fix_line`` a
    line to type in the terminal instead, or "".
    """

    press: Press
    before: Observation
    observation: Observation
    explanation: list[Block] | None
    fix: str | None
    fix_line: str


class CardView(TypedDict):
    """A flashcard to answer. Choices are shuffled on the server; the right answer is not sent."""

    id: str
    chapter: str
    kind: CardKind
    level: int
    level_name: str
    prompt: list[Block]
    code: str
    choices: list[Choice]
    placeholder: str
    pays: bool


class CardResult(TypedDict):
    """
    The result of answering a card.

    ``answer`` is the right reply as sent (for choice and predict cards, the ``value`` of one
    `Choice`, so the page can mark it); ``answer_text`` is how to show it.
    """

    correct: bool
    answer: str
    answer_text: list[Block]
    explain: list[Block]
    xp: int
    streak: int
    bonus: int


class Notes(TypedDict):
    """A chapter's cheat sheet."""

    chapter: str
    title: str
    notes: list[Block]


class Diagnosis(TypedDict):
    """One check of the machine the game runs on: what it checks, whether it passed, and the details."""

    check: str
    ok: bool
    detail: str


class UnknownIdError(LookupError):
    """A level, chapter or card id the game does not have (the web routes answer 404)."""


class NotPlayingError(Exception):
    """No level is in progress, for an action that needs one (the web routes answer 409)."""


class PlaygroundNotOpenError(Exception):
    """The free playground was asked about before any start was built in it."""


class NoAlexError(Exception):
    """Alex was asked for in a free playground start without a mothership, so without Alex."""


class FileChangedError(Exception):
    """A file to resolve that changed since the page read it, or that is no plain file any more: nothing was written."""


class WrongChoicesError(ValueError):
    """A resolve whose choices are not one per conflict block of the file."""


class NoPlaygroundError(Exception):
    """The level in progress has no playground, for a button press (the web routes answer 409)."""


def status() -> Status:
    """
    Give the dashboard.

    Returns
    -------
    Status
        XP and rank, every chapter with its levels, the level in progress (its typed lines
        counted up to now), the last payout, how many cards wait for review (see `due_cards`),
        and the collected command cards.

    Raises
    ------
    firstcommit.save.SaveError
        If a save file is damaged.
    """
    progress = save.load_progress()
    language = progress["language"]
    active = save.load_active()
    levels = runner.catalogue()
    chapters: list[ChapterSummary] = [
        {
            "id": chapter,
            "title": titles[language],
            "blurb": BLURBS[chapter][language],
            "levels": [_level_summary(entry, progress["levels"].get(entry.id), language) for entry in levels.values() if entry.chapter == chapter],
            "cards": len(cards.deck(chapter, language).cards),
        }
        for chapter, titles in CHAPTERS.items()
    ]
    return {
        "language": language,
        "xp": progress["xp"],
        "rank": score.rank(progress["xp"]),
        "chapters": chapters,
        "active": _active_view(_caught_up(active), levels[active["level"]]) if active is not None and active["level"] in levels else None,
        "last_payout": progress["last_payout"],
        "dev": dev_mode(),
        "cards_due": len(_cards_to_review(None, progress, sys.maxsize)),
        "max_difficulty": max(runner.DIFFICULTIES),
        "collection": [_command_card(entry, language) for entry in levels.values() if entry.id in progress["levels"]],
    }


def set_language(language: str) -> None:
    """
    Make the game speak a language from now on.

    Parameters
    ----------
    language : str
        One of `LANGUAGES`.

    Raises
    ------
    ValueError
        If the game does not speak it; nothing changes then.
    """
    if language not in LANGUAGES:
        raise ValueError(f"the game speaks {', '.join(LANGUAGES)}, not {language!r}")
    with save.lock():
        progress = save.load_progress()
        progress["language"] = language
        save.write_progress(progress)


def level(level_id: str) -> LevelView:
    """
    Give a level's page.

    Parameters
    ----------
    level_id : str
        The level's id.

    Returns
    -------
    LevelView
        Its briefing, question and quest steps, filled from its state while it is in progress,
        and its debrief once finished.

    Raises
    ------
    UnknownIdError
        If no level has this id.
    """
    entry = _level(level_id)
    progress = save.load_progress()
    language = progress["language"]
    texts = entry.texts[language]
    finished = progress["levels"].get(level_id)
    active = save.load_active()
    playing = active if active is not None and active["level"] == level_id else None
    state = playing["state"] if playing is not None else {}
    revealed = texts.hints[: playing["hints"]] if playing is not None else ()
    return {
        "id": entry.id,
        "chapter": entry.chapter,
        "chapter_title": CHAPTERS[entry.chapter][language],
        "title": texts.title,
        "difficulty": entry.difficulty,
        "xp": entry.xp,
        "command": entry.command,
        "par": entry.par,
        "scene": [{"art": frame.art, "text": markup.parse(text)} for frame, text in zip(entry.scene, texts.scene, strict=True)],
        "scene_seen": entry.id in progress["scenes"],
        "view": entry.view,
        "tape": entry.tape,
        "pictures": entry.pictures,
        "target": entry.target,
        "views_seen": progress["views"],
        "solution": _solution(entry, state) if dev_mode() and playing is not None else None,
        "card": _command_card(entry, language) if finished is not None or not entry.challenge else None,
        "challenge": entry.challenge,
        "briefing": _blocks(texts.briefing, state),
        "question": _blocks(texts.question, state),
        "placeholder": _fill(texts.placeholder, state),
        "steps": [_step_view(step, texts.steps[step.id], state) for step in entry.quest],
        "hints_total": len(texts.hints),
        "hints": [_blocks(hint_text, state) for hint_text in revealed],
        "debrief": _blocks(texts.debrief, finished["state"]) if finished is not None else None,
    }


def see_scene(level_id: str) -> None:
    """
    Remember that the player has seen a level's scene, so the page plays it by itself only once; `reset` forgets it.

    Parameters
    ----------
    level_id : str
        The level's id.

    Raises
    ------
    UnknownIdError
        If no level has this id.
    """
    entry = _level(level_id)
    with save.lock():
        progress = save.load_progress()
        if entry.id not in progress["scenes"]:
            progress["scenes"].append(entry.id)
            save.write_progress(progress)


def dev_mode() -> bool:
    """
    Tell whether dev mode is on: `DEV_VARIABLE` is ``1`` (``firstcommit serve --dev``).

    Returns
    -------
    bool
        True in dev mode.
    """
    return os.environ.get(DEV_VARIABLE) == "1"


def solution_lines(entry: runner.Level, state: Mapping[str, Any]) -> list[str]:
    """
    Read the shell lines a level's last hint shows, in order, its placeholders filled as the page fills them.

    The level tests type exactly these lines to solve every level, and dev mode shows them.

    Parameters
    ----------
    entry : runner.Level
        The level.
    state : Mapping[str, Any]
        Its state.

    Returns
    -------
    list[str]
        Each ``$ `` line of the last English hint, without the ``$ ``; none for a level without such lines.
    """
    return SHOWN_LINE.findall(_fill(entry.texts["en"].hints[-1], state))


def _solution(entry: runner.Level, state: Mapping[str, Any]) -> Solution:
    """
    Gather how a level in progress is solved, for dev mode.

    Parameters
    ----------
    entry : runner.Level
        The level, in progress.
    state : Mapping[str, Any]
        Its state.

    Returns
    -------
    Solution
        The last hint's lines, and each answer or choice step's answer from the level's own
        actions (`runner.Level` ``actions``), read from the lab as it is now.
    """
    lab = runner.lab_of(entry.id)
    asking = [step.id for step in entry.quest if isinstance(step, kit.AnswerStep | kit.ChoiceStep) and step.id in entry.actions]
    return {
        "lines": solution_lines(entry, state),
        "answers": {step_id: _answer(functools.partial(entry.actions[step_id], lab, dict(state), [])) for step_id in asking},
        "answer": _answer(functools.partial(entry.answer, lab, dict(state))) if entry.answer is not None else None,
    }


def _answer(read: Callable[[], str | None]) -> str | None:
    """
    Read an answer from the lab: a step's action, whose typed lines are not kept, or a level's ``ANSWER``.

    Parameters
    ----------
    read : Callable[[], str | None]
        Reads it.

    Returns
    -------
    str | None
        The answer, or None while the lab cannot give it yet: a git command the action needs
        fails, such as a log in a clone not made yet.
    """
    try:
        found = read()
    except subprocess.CalledProcessError:
        found = None
    return found


def see_view(view: str) -> None:
    """
    Remember that the page has shown a view (or the band) being born, so it plays the birth only once; `reset` forgets it.

    Parameters
    ----------
    view : str
        One of `SEEN`.

    Raises
    ------
    ValueError
        If the page draws no such view; nothing changes then.
    """
    if view not in SEEN:
        raise ValueError(f"the level screen's births are {', '.join(SEEN)}, not {view!r}")
    with save.lock():
        progress = save.load_progress()
        if view not in progress["views"]:
            progress["views"].append(view)
            save.write_progress(progress)


def start(level_id: str) -> ActiveView:
    """
    Start a level in a fresh lab, ending any level in progress.

    Parameters
    ----------
    level_id : str
        The level's id.

    Returns
    -------
    ActiveView
        The new level in progress, at the first quest step; only lines typed from now on count for it.
        Its events with no goal (`firstcommit.kit.LevelEvent`) have run, so no line typed meets
        the lab without them; the first `observe` still shows the lab as it was before them.

    Raises
    ------
    UnknownIdError
        If no level has this id; the level in progress is then left alone.
    """
    entry = _level(level_id)
    with save.lock():
        save.clear_active()
        save.clear_observed()
        state = runner.start_lab(entry)
        lab = runner.lab_of(entry.id)
        active: save.Active = {
            "level": entry.id,
            "started": _now(),
            "step": 0,
            "hints": 0,
            "attempts": 0,
            "state": state,
            "log_offset": commands.end(save.home() / save.COMMANDS_FILE),
            "typed": [],
            "events": [],
            "done": [],
        }
        save.write_active(active)
        set_up, _ = _look(entry.id, lab, None, [])
        save.write_observed({**set_up, "fresh": True})
        active = _fire(entry, active, "")
    return _active_view(active, entry)


def quest_step(answer: str | None) -> StepResult:
    """
    Check the current step of the guided quest, and move on if it passed.

    Only the current step is ever checked, so a guided quest is played in order; a challenge's
    goals are all checked, and any of them may be met first. The message is a loss when one is
    found, else the first goal met now, else the first goal still unmet. An answer step is
    checked with ``answer`` (a missing or blank one counts as empty), a watch step against the lab
    and every line typed since the level started (the page polls it with None; the log is read
    first), and a read step always passes. Once the quest is done, nothing is checked and the
    result says so.

    Parameters
    ----------
    answer : str | None
        What the player typed, or None.

    Returns
    -------
    StepResult
        Whether the step passed, its feedback, and the step the quest is at now.

    Raises
    ------
    NotPlayingError
        If no level is in progress.
    """
    with save.lock():
        active, entry = _playing()
        active = _catch_up(active)
        lab = runner.lab_of(entry.id)
        language = _language()
        reached: list[str] = []
        message: list[Block] = []
        lost = False
        if not _quest_done(active, entry):
            verdicts = [(step.id, _check_step(step, entry.texts[language].steps[step.id], lab, active, _typed(answer), _messages(entry, language))) for step in _pending(active, entry)]
            reached = [step_id for step_id, verdict in verdicts if verdict.solved]
            unmet = sorted((verdict for _, verdict in verdicts if not verdict.solved), key=lambda verdict: not verdict.lost)
            met = [verdict for _, verdict in verdicts if verdict.solved]
            lost = bool(unmet) and unmet[0].lost
            said = unmet[0] if lost or not met else met[0]
            message = markup.parse(said.message)
        if reached:
            active["done"] = [step.id for step in entry.quest if step.id in {*active["done"], *reached}]
            active["step"] = len(active["done"])
            save.write_active(active)
        for goal in reached:
            active = _fire(entry, active, goal)
    return {"correct": bool(reached), "message": message, "step": active["step"], "quest_done": _quest_done(active, entry), "done": active["done"], "lost": lost}


def check(answer: str | None, auto: bool) -> CheckResult:
    """
    Check the level in progress, and pay for it once solved.

    While the guided quest is unfinished, an automatic check (the page polling) never solves the
    level: its message points to the next step, so the player sees the end of the quest, unless
    the level's check says the work is lost for good, which it reports at once. A check the player asks for runs the level's check at any time,
    so the level may be solved before its quest is finished. A blank answer counts as no
    answer. A check the player asks for that fails counts as an attempt; an automatic one never
    does. Solving ends the level: the payout and the best stars are kept in the progress (so any
    view can celebrate them) and the lab stays until another level starts. The stars count every
    line typed since the level started, read from the log first.

    Parameters
    ----------
    answer : str | None
        What the player typed, or None.
    auto : bool
        Whether the page asked by itself rather than the player.

    Returns
    -------
    CheckResult
        Whether the level is solved, the check's feedback, and once solved the payout, the
        debrief, the stars and, the first time, the level's card.

    Raises
    ------
    NotPlayingError
        If no level is in progress.
    """
    typed = _typed(answer)
    with save.lock():
        active, entry = _playing()
        active = _catch_up(active)
        language = _language()
        messages = _messages(entry, language)
        verdict = entry.check(runner.lab_of(entry.id), active["state"], typed, active["typed"])
        message = _say(verdict.message, messages)
        if auto and not _quest_done(active, entry) and not verdict.lost:
            verdict = kit.Verdict(False, QUEST_FIRST)
            message = _say(QUEST_FIRST, messages).format(step=active["step"] + 1, steps=len(entry.quest))
        payout = None
        stars = 0
        if verdict.solved:
            stars = _stars(active, entry)
            payout = _pay(entry, active, stars)
        elif not auto:
            active["attempts"] += 1
            save.write_active(active)
    return {
        "solved": verdict.solved,
        "message": markup.parse(message),
        "payout": payout,
        "debrief": _blocks(entry.texts[language].debrief, active["state"]) if verdict.solved else None,
        "stars": stars,
        "new_card": _command_card(entry, language) if payout is not None and payout["first_time"] else None,
        "lost": verdict.lost,
    }


def hint() -> HintView:
    """
    Reveal the next hint of the level in progress.

    Once every hint is revealed, the last one is shown again and costs nothing.

    Returns
    -------
    HintView
        The hint, how many are used out of how many, and what it took off the reward.

    Raises
    ------
    NotPlayingError
        If no level is in progress.
    """
    with save.lock():
        active, entry = _playing()
        hints = entry.texts[_language()].hints
        cost = 0
        if active["hints"] < len(hints):
            active["hints"] += 1
            save.write_active(active)
            first_time = entry.id not in save.load_progress()["levels"]
            cost = score.hint_cost(entry.xp, active["hints"], first_time)
    return {"hint": _blocks(hints[active["hints"] - 1], active["state"]), "used": active["hints"], "total": len(hints), "cost": cost}


def observe() -> Observation:
    """
    Snapshot the lab of the level in progress and tell what changed since the last observation.

    The snapshots are kept in the save (only when they changed), so the events are right
    whichever process asks. The first observation of a level shows the lab as `start` snapshotted
    it, before the level's events with no goal (`firstcommit.kit.LevelEvent`), and has no events
    and no lines; the next one tells what changed since, the events' changes and the lines typed
    meanwhile, so the page animates them. The lines typed
    since the last look are read into the level's record first (`save.Active` ``typed``), so a
    goal still sees them after this observation has told them.

    Returns
    -------
    Observation
        The player's repository, the stand-in GitHub and the teammate's clone (each None when
        the level has none), and the changes.

    Raises
    ------
    NotPlayingError
        If no level is in progress.
    """
    with save.lock():
        active, entry = _playing()
        active = _catch_up(active)
        lab = runner.lab_of(entry.id)
        last = save.load_observed()
        typed: list[Command] = []
        if last is not None and last["fresh"]:
            now: save.Observed = {**last, "fresh": False}
            last = None
        else:
            now, typed = _look(entry.id, lab, last, active["typed"])
        messages = _messages(entry, _language())
        observation = _lost_over_pleased(_observation(last, now, _buttons(lab, now), lab.project, typed, _rules(entry), messages, entry.pictures), _loss(entry, active, lab, messages))
        if now != last:
            save.write_observed(now)
    return observation


def press(person: str, button: str) -> PressView:
    """
    Press one person's playground button in the level in progress, observing the lab before and after.

    The button's command runs for real in that person's clone (`firstcommit.playground.press`);
    a command that fails is reported with its status, as a terminal shows it. The observation
    before, the press and the observation after hold the save's lock together, so what the
    player typed before is told apart from the press's own changes, and no other observation
    can come in between. Nothing is saved until the press has run: a press that raises leaves
    the typed changes to the next observation.

    Parameters
    ----------
    person : str
        Who pressed (`firstcommit.records.Who`).
    button : str
        Which button: one of `firstcommit.playground.BUTTON_IDS`.

    Returns
    -------
    PressView
        The press, the lab before and after it, and its explanation; a later `observe` does not
        tell the same changes again.

    Raises
    ------
    UnknownIdError
        If the person or the button is not the playground's; checked before anything else.
    NotPlayingError
        If no level is in progress.
    NoPlaygroundError
        If the level in progress has no playground: its lab has no teammate's clone.
    ButtonOffError
        If the button is off now; nothing runs, and the message says why.
    subprocess.TimeoutExpired
        If the command runs longer than `firstcommit.gitcmd.TIMEOUT` seconds.
    """
    who = _playground_id(person, playground.PEOPLE, "person")
    which = _playground_id(button, playground.BUTTON_IDS, "button")
    with save.lock():
        active, entry = _playing()
        lab = runner.lab_of(entry.id)
        if not lab.teammate.exists():
            raise NoPlaygroundError(f"the level {entry.id!r} has no playground")
        last = save.load_observed()
        active = _catch_up(active)
        messages = _messages(entry, _language())
        then, typed_before = _look(entry.id, lab, last, active["typed"])
        before = _observation(last, then, _buttons(lab, then), lab.project, typed_before, _rules(entry), messages, entry.pictures)
        facts = playground.facts(lab, who, _clones(then)[who], then["github"])
        pressed = playground.press(lab, who, which)
        active = _catch_up(active)
        now, typed_during = _look(entry.id, lab, then, active["typed"])
        observation = _observation(then, now, _buttons(lab, now), lab.project, typed_during, _rules(entry), messages, entry.pictures)
        if now != last:
            save.write_observed(now)
    found = explanations.explain(pressed, _clones(then)[who], _clones(now)[who], facts, playground.BUTTON_IDS)
    return {
        "press": pressed,
        "before": before,
        "observation": observation,
        "explanation": markup.parse(found["text"]) if found["tag"] else None,
        "fix": found["fix"] or None,
        "fix_line": found["fix_line"],
    }


def abort() -> str | None:
    """
    End the level in progress and remove its lab.

    Returns
    -------
    str | None
        The id of the level that was in progress, or None if there was none.
    """
    with save.lock():
        active = save.load_active()
        save.clear_active()
        save.clear_observed()
        runner.remove_labs()
    return active["level"] if active is not None else None


def reset() -> None:
    """End the level in progress, remove the playground and erase all progress, damaged files included; the game's git configuration starts over too."""
    with save.lock():
        runner.remove_labs()
        freeplay.remove()
        save.erase()
        gitcmd.ensure_config()


def due_cards(chapter: str | None, limit: int) -> list[CardView]:
    """
    Give cards to review: due ones first (oldest first), then new ones (easiest first).

    Without a chapter, due cards come from every chapter, and new cards only from chapters in
    which the player has finished a level, so nobody is quizzed on what they have not met yet.

    Parameters
    ----------
    chapter : str | None
        A chapter id, or None for every chapter.
    limit : int
        Most cards to give (zero or more).

    Returns
    -------
    list[CardView]
        The cards, with their choices shuffled.

    Raises
    ------
    UnknownIdError
        If `chapter` is not a chapter id.
    """
    progress = save.load_progress()
    if chapter is not None:
        _chapter(chapter, progress["language"])
    today = date.today()
    rng = random.Random()
    return [_card_view(card, cards.is_due(progress["cards"].get(card.id), today), rng, progress["language"]) for card in _cards_to_review(chapter, progress, limit)]


def answer_card(card_id: str, reply: str) -> CardResult:
    """
    Judge a reply to a card, reschedule the card, and pay if it was new or due.

    Parameters
    ----------
    card_id : str
        The card's id.
    reply : str
        The chosen option, or the typed answer.

    Returns
    -------
    CardResult
        Whether the reply was right, the right answer and its explanation, and the XP, streak and bonus.

    Raises
    ------
    UnknownIdError
        If no card has this id.
    """
    card = _card(card_id)
    today = date.today()
    correct = cards.judge(card, _encodable(reply))
    with save.lock():
        progress = save.load_progress()
        entry = progress["cards"].get(card_id)
        earned = score.card_score(card.level, correct, cards.is_due(entry, today), progress["streak"])
        progress["xp"] += earned.xp + earned.bonus
        progress["streak"] = earned.streak
        progress["best_streak"] = max(progress["best_streak"], earned.streak)
        progress["cards"][card_id] = cards.reschedule(entry, correct, today)
        save.write_progress(progress)
    right = cards.answer(card)
    return {
        "correct": correct,
        "answer": right,
        "answer_text": _option_text(card, right),
        "explain": markup.parse(card.explain),
        "xp": earned.xp,
        "streak": earned.streak,
        "bonus": earned.bonus,
    }


def notes(chapter: str) -> Notes:
    """
    Give a chapter's cheat sheet.

    Parameters
    ----------
    chapter : str
        A chapter id.

    Returns
    -------
    cheat_sheet : Notes
        Its notes; empty when the chapter has no deck yet.

    Raises
    ------
    UnknownIdError
        If `chapter` is not a chapter id.
    """
    language = _language()
    return {"chapter": chapter, "title": _chapter(chapter, language), "notes": markup.parse(cards.deck(chapter, language).notes)}


def shell_environment(base: Mapping[str, str]) -> dict[str, str]:
    """
    Build the environment of a shell the game opens for the player, ready to use.

    Git there is kept to the game (`firstcommit.gitcmd.shell_environment`), and the game's git
    configuration that it names is created first if it is missing (never overwritten), so the
    player's first ``git init`` is on ``main``.

    Parameters
    ----------
    base : Mapping[str, str]
        The environment to start from (the web terminal's or the command line's); not changed.

    Returns
    -------
    dict[str, str]
        ``base`` without its git variables, plus the game's isolation.
    """
    gitcmd.ensure_config()
    return gitcmd.shell_environment(base, save.home())


def shell_command() -> list[str]:
    """
    Give the command of the shell the game opens for the player, writing its startup file first.

    Whatever the player's own shell, it is bash with the game's startup file
    (`firstcommit.commands.startup`): a plain prompt naming the folder, never the user or the
    machine, and each command line typed logged in the game home for `observe`. It starts on the
    game home, which holds a ``.hushlogin``, so Ubuntu's ``sudo`` notice stays out of it
    (`firstcommit.commands.shell`). The page's terminal and ``firstcommit shell`` both run it.

    Returns
    -------
    list[str]
        The program and its arguments.
    """
    home = save.home()
    startup = save.write_shell_startup(commands.startup(home / save.COMMANDS_FILE, home / save.HISTORY_FILE))
    return commands.shell(startup, save.ensure_hushlogin().parent)


def playground_environment(person: Who, base: Mapping[str, str]) -> dict[str, str]:
    """
    Build the environment of one person's playground shell.

    Yours is the game shell's (`shell_environment`). Alex's has Alex's own ``HOME``, the folder of
    Alex's shell, and Alex's own global git configuration there, which signs Alex's commits as
    Alex; it is created if missing, and never overwritten.

    Parameters
    ----------
    person : Who
        ``"you"`` or ``"alex"``.
    base : Mapping[str, str]
        The environment to start from; not changed.

    Returns
    -------
    dict[str, str]
        The shell's environment.
    """
    environment = shell_environment(base)
    if person == "alex":
        folder = save.ensure_playground_shell(person)
        config = save.ensure_gitconfig(gitcmd.base_config(playground.ALEX), folder)
        environment.update({"HOME": str(folder), "GIT_CONFIG_GLOBAL": str(config)})
    return environment


def playground_shell_command(person: Who) -> list[str]:
    """
    Give the command of one person's playground shell, writing its startup file first.

    Each person's shell is the game's bash (`firstcommit.commands.startup`) with a startup file,
    a typed-command log, a history and a quiet home of its own (`firstcommit.save.ensure_playground_shell`).
    Alex's prompt is ``alex: project $`` in green. Yours prints the current start's suggestion
    first, in the player's language: the only guidance free play gives.

    Parameters
    ----------
    person : Who
        ``"you"`` or ``"alex"``.

    Returns
    -------
    list[str]
        The program and its arguments.
    """
    folder = save.ensure_playground_shell(person)
    left = save.load_playground()
    banner = freeplay.STARTS[left["start"]].banner[_language()] if person == "you" and left is not None else ""
    prompt = commands.ALEX_PROMPT if person == "alex" else commands.PROMPT
    text = commands.startup(folder / save.COMMANDS_FILE, folder / save.HISTORY_FILE, prompt=prompt, banner=banner)
    startup = folder / save.STARTUP_FILE
    startup.write_text(text)
    return commands.shell(startup, folder)


def playground_folder(person: Who) -> str:
    """
    Give the folder one person's playground terminal opens in: that person's clone, else the playground, else the player's home.

    Parameters
    ----------
    person : Who
        ``"you"`` or ``"alex"``.

    Returns
    -------
    str
        The folder.
    """
    lab = freeplay.lab()
    clone = lab.project if person == "you" else lab.teammate
    folder = Path.home()
    if clone.is_dir():
        folder = clone
    elif lab.root.is_dir():
        folder = lab.root
    return str(folder)


def playground_typed(person: Who) -> list[Command]:
    """
    Give the lines typed in one person's playground terminal since the current start began, oldest first.

    Parameters
    ----------
    person : Who
        ``"you"`` or ``"alex"``.

    Returns
    -------
    list[Command]
        Each line and its exit status (`firstcommit.commands.since`).
    """
    return commands.since(save.home() / save.PLAYGROUND_SHELLS_FOLDER / person / save.COMMANDS_FILE, 0)[0]


def playground_status() -> PlaygroundStatus:
    """
    Give the free playground's starts and where the player left it.

    Returns
    -------
    PlaygroundStatus
        Every start in the picker's order, in the player's language, and the current one, None
        before the first visit.
    """
    language = _language()
    left = save.load_playground()
    starts: list[StartView] = [
        {
            "id": start_id,
            "title": start.title[language],
            "blurb": start.blurb[language],
            "banner": start.banner[language],
            "view": start.view,
            "mothership": start.mothership,
            "alex": start.alex,
            "uses": [{"id": chapter, "title": CHAPTERS[chapter][language]} for chapter in start.uses],
        }
        for start_id, start in freeplay.STARTS.items()
    ]
    return {"starts": starts, "current": _prefs(left) if left is not None else None}


def start_playground(start_id: str) -> PlaygroundStatus:
    """
    Build the free playground afresh from a starting point, as Start over and Choose another do.

    The view goes back to the start's own, the view draws your repository, and Alex's terminal
    is shown as the player last had it in this start, else as the start wants. The lines typed
    in either terminal before are forgotten, so `observe_playground` tells only this start's.

    Parameters
    ----------
    start_id : str
        The start the page sent.

    Returns
    -------
    PlaygroundStatus
        The starts and the new current one.

    Raises
    ------
    UnknownIdError
        If there is no such start.
    """
    start = _playground_id(start_id, freeplay.STARTS, "start")
    with save.lock():
        freeplay.build(start)
        for person in PEOPLE:
            (save.ensure_playground_shell(person) / save.COMMANDS_FILE).unlink(missing_ok=True)
        left = save.load_playground()
        shown = left["alex_shown"] if left is not None else {}
        started = datetime.now(UTC).isoformat()
        save.write_playground({"start": start, "started": started, "alex_shown": shown, "view": freeplay.STARTS[start].view, "whose": "you"})
    return playground_status()


def set_playground_prefs(view: str | None, alex: bool | None, whose: str | None) -> PlaygroundStatus:
    """
    Remember the view, whether Alex's terminal is shown in the current start, and whose repository the view draws.

    Parameters
    ----------
    view : str | None
        The view the page sent, or None to keep the current one.
    alex : bool | None
        Whether Alex's terminal is shown, or None to keep it as it is.
    whose : str | None
        ``"you"`` or ``"alex"``, or None to keep it.

    Returns
    -------
    PlaygroundStatus
        The starts and the current one, changed.

    Raises
    ------
    UnknownIdError
        If there is no such view or person.
    PlaygroundNotOpenError
        If no start was built yet.
    NoAlexError
        If Alex is asked for in a start without a mothership.
    """
    chosen_view = _playground_id(view, PLAYGROUND_VIEWS, "view") if view is not None else None
    chosen_whose = _playground_id(whose, PEOPLE, "person") if whose is not None else None
    with save.lock():
        left = save.load_playground()
        if left is None:
            raise PlaygroundNotOpenError("the playground has no start yet: start one first")
        start = freeplay.STARTS[left["start"]]
        if not start.mothership and (alex or chosen_whose == "alex"):
            raise NoAlexError(f"{start.title['en']} has no mothership, so no Alex")
        shown = {**left["alex_shown"], left["start"]: alex} if alex is not None else left["alex_shown"]
        save.write_playground({**left, "alex_shown": shown, "view": chosen_view or left["view"], "whose": chosen_whose or left["whose"]})
    return playground_status()


def observe_playground() -> PlaygroundObservation:
    """
    Read the free playground as it is now.

    Returns
    -------
    PlaygroundObservation
        Each repository's snapshot, and your repository and Alex's as the views draw them.

    Raises
    ------
    PlaygroundNotOpenError
        If no start was built yet.
    """
    left = save.load_playground()
    if left is None:
        raise PlaygroundNotOpenError("the playground has no start yet: start one first")
    lab = freeplay.lab()
    has_alex = freeplay.STARTS[left["start"]].mothership
    project = repomap.snapshot(lab.project)
    teammate = repomap.snapshot(lab.teammate) if has_alex else None
    return {
        "start": left["start"],
        "started": left["started"],
        "project": project,
        "github": repomap.snapshot(lab.github) if has_alex else None,
        "teammate": teammate,
        "you": _clone_view(lab.project, project, "you"),
        "alex": _clone_view(lab.teammate, teammate, "alex") if teammate is not None else None,
    }


def resolve_playground(person: str, file: str, read: str, choices: Sequence[Keep]) -> ResolveView:
    """
    Write the sides chosen for each conflict block into one person's file in the free playground.

    Only the blocks change (`firstcommit.markers.resolve`); git is never run, so the file stays
    in conflict until the player types ``git add``. The file is written only if it is still a
    plain file, inside that person's clone, whose bytes hash to ``read``.

    Parameters
    ----------
    person : str
        Whose file, as the page sent it.
    file : str
        The file's path in that person's clone: one of its files in conflict.
    read : str
        The SHA-256 of the file as the page read it (`firstcommit.records.MarkedFile`).
    choices : Sequence[Keep]
        One per conflict block, in order.

    Returns
    -------
    ResolveView
        The file as written.

    Raises
    ------
    UnknownIdError
        If there is no such person, or the file is not one of that person's files in conflict.
    PlaygroundNotOpenError
        If no start was built yet.
    NoAlexError
        If Alex is asked for in a start without a mothership.
    FileChangedError
        If the file changed since it was read, or is no plain file in the clone; nothing is written.
    WrongChoicesError
        If there is not one choice per block; nothing is written.
    """
    who = _playground_id(person, PEOPLE, "person")
    left = save.load_playground()
    if left is None:
        raise PlaygroundNotOpenError("the playground has no start yet: start one first")
    if who == "alex" and not freeplay.STARTS[left["start"]].mothership:
        raise NoAlexError(f"{freeplay.STARTS[left['start']].title['en']} has no mothership, so no Alex")
    lab = freeplay.lab()
    clone = lab.project if who == "you" else lab.teammate
    path = clone / _playground_id(file, [conflict["path"] for conflict in repomap.conflicts(clone)], "file in conflict")
    data = repomap.folder_bytes(path)
    if data is None or not path.resolve().is_relative_to(clone.resolve()) or markers.marked(file, data)["read"] != read:
        raise FileChangedError(f"{file} changed since it was read: look at it again")
    try:
        written = markers.resolve(data, choices)
    except ValueError as error:
        raise WrongChoicesError(str(error)) from error
    descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(written)
    return {"file": markers.marked(file, written)}


def terminal_folder() -> str:
    """
    Give the folder a new terminal opens in: the lab's project, else the lab, else the player's home.

    Returns
    -------
    str
        The folder.
    """
    active = save.load_active()
    lab = runner.lab_of(active["level"]) if active is not None else None
    folder = Path.home()
    if lab is not None and lab.project.is_dir():
        folder = lab.project
    elif lab is not None and lab.root.is_dir():
        folder = lab.root
    return str(folder)


def doctor() -> list[Diagnosis]:
    """
    Check that this machine can run the game.

    Returns
    -------
    list[Diagnosis]
        git (at least `MIN_GIT`; the levels are checked against `TARGET_GIT`), Python (at least
        `MIN_PYTHON`), and the game home (absolute and writable), in that order.
    """
    return [_git_diagnosis(), _python_diagnosis(), _home_diagnosis()]


def _level(level_id: str) -> runner.Level:
    """
    Look a level up by its id.

    Parameters
    ----------
    level_id : str
        The id the player or the page sent.

    Returns
    -------
    runner.Level
        The level.

    Raises
    ------
    UnknownIdError
        If no level has this id.
    """
    levels = runner.catalogue()
    if level_id not in levels:
        raise UnknownIdError(f"no level has the id {level_id!r}")
    return levels[level_id]


def _chapter(chapter: str, language: Language) -> str:
    """
    Look a chapter up by its id.

    Parameters
    ----------
    chapter : str
        The id the player or the page sent.
    language : Language
        The language of its title.

    Returns
    -------
    str
        The chapter's title.

    Raises
    ------
    UnknownIdError
        If no chapter has this id.
    """
    if chapter not in CHAPTERS:
        raise UnknownIdError(f"no chapter has the id {chapter!r}")
    return CHAPTERS[chapter][language]


def _card(card_id: str) -> cards.Card:
    """
    Look a card up by its id; the one place where a missing card becomes an unknown id.

    Parameters
    ----------
    card_id : str
        The id the player or the page sent.

    Returns
    -------
    cards.Card
        The card, in the language the game speaks.

    Raises
    ------
    UnknownIdError
        If no deck holds a card with this id.
    """
    try:
        card = cards.find(card_id, _language())
    except KeyError as error:
        raise UnknownIdError(f"no card has the id {card_id!r}") from error
    return card


def _prefs(left: save.Playground) -> PlaygroundPrefs:
    """
    Read where the player is in the free playground from its record.

    Parameters
    ----------
    left : save.Playground
        The record.

    Returns
    -------
    PlaygroundPrefs
        The start, view and whose, and whether Alex is shown: as remembered for this start, else
        as the start wants.
    """
    start = left["start"]
    return {"start": start, "started": left["started"], "view": left["view"], "alex": left["alex_shown"].get(start, freeplay.STARTS[start].alex), "whose": left["whose"]}


def _clone_view(folder: Path, snap: Snapshot, person: Who) -> CloneView:
    """
    Read one person's repository in the free playground as the views draw it.

    Parameters
    ----------
    folder : Path
        That person's working folder.
    snap : Snapshot
        Its snapshot now.
    person : Who
        Whose it is, for the lines typed in that person's terminal.

    Returns
    -------
    CloneView
        Its conflicts, marked files, reflog, ghosts, texts, graph and typed lines.
    """
    conflicts = repomap.conflicts(folder)
    read = [(conflict["path"], repomap.folder_bytes(folder / conflict["path"])) for conflict in conflicts]
    return {
        "conflicts": conflicts,
        "marked": [markers.marked(path, data) for path, data in read if data is not None and len(data) <= repomap.MAX_TEXT],
        "reflog": repomap.reflog(folder),
        "ghosts": repomap.ghosts(folder),
        "texts": repomap.file_texts(folder, [file["path"] for file in snap["files"]]),
        "graph": repomap.graph(folder) if snap["exists"] else None,
        "typed": playground_typed(person),
    }


def _playground_id[Name: str](name: str, names: Iterable[Name], what: str) -> Name:
    """
    Look a playground person, button, start or view up by its name.

    Parameters
    ----------
    name : str
        The name the page sent.
    names : Iterable[Name]
        The playground's names of that kind.
    what : str
        The kind, for the message, such as ``"person"`` or ``"start"``.

    Returns
    -------
    Name
        The name, as one of the playground's.

    Raises
    ------
    UnknownIdError
        If the playground has no such name.
    """
    known = [candidate for candidate in names if candidate == name]
    if not known:
        raise UnknownIdError(f"the playground has no {what} {name!r}")
    return known[0]


def _look(level_id: str, lab: Lab, last: save.Observed | None, typed: list[Command]) -> tuple[save.Observed, list[Command]]:
    """
    Snapshot every repository of a level's lab, and pick the typed lines no observation has told yet.

    The caller has just read the log into the level's lines (`_catch_up`), so every line
    returned had finished before the snapshots were taken, and its changes are in them.

    Parameters
    ----------
    level_id : str
        The level in progress.
    lab : Lab
        Its lab.
    last : save.Observed | None
        The observation to go on from. With none, or one of another level, the lines typed so
        far are skipped: a level's first observation tells none, as it tells no events.
    typed : list[Command]
        Every line typed since the level started (`save.Active` ``typed``).

    Returns
    -------
    tuple[save.Observed, list[Command]]
        The player's repository, the stand-in GitHub and the teammate's clone where they exist,
        and how many lines are told; then the lines typed since ``last``, oldest first.
    """
    told = last["told"] if last is not None and last["level"] == level_id else len(typed)
    now: save.Observed = {
        "level": level_id,
        "project": repomap.snapshot(lab.project),
        "github": repomap.snapshot(lab.github) if lab.github.exists() else None,
        "teammate": repomap.snapshot(lab.teammate) if lab.teammate.exists() else None,
        "told": len(typed),
        "fresh": False,
    }
    return now, typed[told:]


def _caught_up(active: save.Active) -> save.Active:
    """
    Read the lines typed since the level's record was last brought up to date, without saving them.

    Parameters
    ----------
    active : save.Active
        The record of the level in progress.

    Returns
    -------
    save.Active
        A copy whose ``typed`` ends with the lines logged after its ``log_offset``, and whose
        ``log_offset`` is where the log's whole records end now.
    """
    new, offset = commands.since(save.home() / save.COMMANDS_FILE, active["log_offset"])
    return {**active, "typed": [*active["typed"], *new], "log_offset": offset}


def _catch_up(active: save.Active) -> save.Active:
    """
    Bring the level's record up to date with the log of typed lines, saving it when that changed it; the caller holds the save's lock.

    Parameters
    ----------
    active : save.Active
        The record of the level in progress.

    Returns
    -------
    save.Active
        The record up to date (`_caught_up`).
    """
    caught = _caught_up(active)
    if caught != active:
        save.write_active(caught)
    return caught


def _fire(entry: runner.Level, active: save.Active, goal: str) -> save.Active:
    """
    Run the level's events for a moment of the play that have not run yet, and record them; the caller holds the save's lock.

    Parameters
    ----------
    entry : runner.Level
        The level in progress.
    active : save.Active
        Its record.
    goal : str
        The moment: empty for when the level starts, else the id of the goal just reached.

    Returns
    -------
    save.Active
        The record, with the events that ran added to ``events`` (saved when any ran).
    """
    due = [event for event in entry.events if event.goal == goal and event.id not in active["events"]]
    lab = runner.lab_of(entry.id)
    for event in due:
        event.run(lab, active["state"])
    fired: save.Active = {**active, "events": [*active["events"], *(event.id for event in due)]}
    if due:
        save.write_active(fired)
    return fired


def _rules(entry: runner.Level) -> tuple[ReactionRule, ...]:
    """
    Give a level's reaction rules, in the order they are tried.

    Parameters
    ----------
    entry : runner.Level
        The level.

    Returns
    -------
    tuple[ReactionRule, ...]
        The level's own rules, then the shared `firstcommit.reactions.RULES`; in a challenge only
        those about danger and errors (`CHALLENGE_MOODS`).
    """
    rules = (*entry.reactions, *reactions.RULES)
    return tuple(rule for rule in rules if rule.mood in CHALLENGE_MOODS) if entry.challenge else rules


def _buttons(lab: Lab, now: save.Observed) -> dict[Who, list[ButtonView]]:
    """
    Give each person's playground buttons for the lab as just snapshotted.

    Parameters
    ----------
    lab : Lab
        The level's lab.
    now : save.Observed
        Its snapshots.

    Returns
    -------
    dict[Who, list[ButtonView]]
        Each person's bar, or nothing when the lab has no teammate's clone (no playground).
    """
    clones = _clones(now)
    return playground.buttons(lab, clones) if clones else {}


def _clones(observed: save.Observed) -> dict[Who, Snapshot]:
    """
    Give each person's clone among a lab's snapshots.

    Parameters
    ----------
    observed : save.Observed
        The lab's snapshots.

    Returns
    -------
    dict[Who, Snapshot]
        Your project and Alex's clone, or nothing when the lab has no teammate's clone (no playground).
    """
    teammate = observed["teammate"]
    return {"you": observed["project"], "alex": teammate} if teammate is not None else {}


def _observation(
    last: save.Observed | None,
    now: save.Observed,
    buttons: dict[Who, list[ButtonView]],
    project: Path,
    typed: list[Command],
    rules: tuple[ReactionRule, ...],
    messages: Mapping[str, str],
    pictures: Pictures | None,
) -> Observation:
    """
    Tell what changed in a lab between two observations, and what Rama says about the lines typed in between.

    Parameters
    ----------
    last : save.Observed | None
        The earlier observation, or None; one of another level counts as none.
    now : save.Observed
        The lab now.
    buttons : dict[Who, list[ButtonView]]
        The playground's buttons now (`_buttons`).
    project : Path
        The player's repository, read now for its conflicts, its reflog and its ghosts.
    typed : list[Command]
        The commands typed between the two (`_look`).
    rules : tuple[ReactionRule, ...]
        The level's reaction rules (`_rules`).
    messages : Mapping[str, str]
        The messages in the player's language (`_messages`).
    pictures : Pictures | None
        The level's pictures, which say whether to read the desk's texts and git's graph.

    Returns
    -------
    Observation
        The lab now, with no events when there is no earlier observation of the same level.
        Each line's reaction reads every change between the two observations.
    """
    events: list[Event] = []
    teammate_events: list[Event] = []
    if last is not None and last["level"] == now["level"]:
        events = changes.describe(last["project"], now["project"]) + _changes(last["github"], now["github"])
        teammate_events = _changes(last["teammate"], now["teammate"])
    kinds = {event["kind"] for event in events}
    staged = bool(repomap.staged(now["project"]))
    remote = bool(now["project"]["remotes"])
    ignored = any(file["ignored"] for file in now["project"]["files"])
    said = [(command, reactions.react(command, kinds, now["project"]["exists"], staged, rules, remote=remote, ignored=ignored, branch=now["project"]["branch"])) for command in typed]
    return {
        "level": now["level"],
        "project": now["project"],
        "github": now["github"],
        "teammate": now["teammate"],
        "events": _event_views(events),
        "teammate_events": _event_views(teammate_events),
        "buttons": buttons,
        "commands": typed,
        "reactions": [
            {"line": command["line"], "mood": rule.mood, "text": markup.parse(_say(rule.text, messages)), "moment": rule.moment} for command, rule in said if rule is not None
        ],
        "conflicts": repomap.conflicts(project),
        "reflog": repomap.reflog(project),
        "ghosts": repomap.ghosts(project),
        "texts": repomap.file_texts(project, pictures["lines"]) if pictures is not None else [],
        "graph": repomap.graph(project) if pictures is not None and pictures["graph"] else None,
    }


def _changes(before: Snapshot | None, after: Snapshot | None) -> list[Event]:
    """
    Tell what changed in a repository the level may not have, such as the stand-in GitHub.

    Parameters
    ----------
    before : Snapshot | None
        The last observation, or None.
    after : Snapshot | None
        The repository now, or None.

    Returns
    -------
    list[Event]
        The changes, or none when either snapshot is missing.
    """
    events: list[Event] = []
    if before is not None and after is not None:
        events = changes.describe(before, after)
    return events


def _event_views(events: list[Event]) -> list[EventView]:
    """
    Parse events for the page.

    Parameters
    ----------
    events : list[Event]
        Events of `firstcommit.changes`.

    Returns
    -------
    list[EventView]
        The same events, their text parsed into blocks.
    """
    return [{"kind": event["kind"], "text": markup.parse(event["text"])} for event in events]


def _playing() -> tuple[save.Active, runner.Level]:
    """
    Read the level in progress and its record.

    Returns
    -------
    tuple[save.Active, runner.Level]
        The saved record and the level.

    Raises
    ------
    NotPlayingError
        If no level is in progress, or the one in progress is no longer in the game.
    SaveError
        If the record counts more hints or quest steps than its level has, or its goals met do not
        match its step (a damaged save).
    """
    active = save.load_active()
    levels = runner.catalogue()
    if active is None or active["level"] not in levels:
        raise NotPlayingError("no level is in progress")
    entry = levels[active["level"]]
    hints = len(entry.texts["en"].hints)
    if active["hints"] > hints or active["step"] > len(entry.quest):
        raise save.damaged(
            save.home() / save.ACTIVE_FILE,
            f"`hints` is {active['hints']} and `step` is {active['step']}, but level {entry.id} has {hints} hints and {len(entry.quest)} quest steps",
        )
    if active["step"] != len(active["done"]) or not set(active["done"]) <= {step.id for step in entry.quest}:
        raise save.damaged(save.home() / save.ACTIVE_FILE, f"`done` must list `step` ({active['step']}) goals of level {entry.id}, not {active['done']!r}")
    return active, entry


def _pay(entry: runner.Level, active: save.Active, stars: int) -> Payout:
    """
    Record a solved level: pay it, keep the payout, the best stars and the play's state, and end the level (its lab stays).

    Parameters
    ----------
    entry : runner.Level
        The level solved.
    active : save.Active
        The record of this play: its hints, and its state for the debrief.
    stars : int
        The stars this play earned.

    Returns
    -------
    Payout
        What it paid.
    """
    progress = save.load_progress()
    first_time = entry.id not in progress["levels"]
    xp = score.level_reward(entry.xp, active["hints"], first_time)
    rank_before = score.rank(progress["xp"])["title"]
    progress["xp"] += xp
    if first_time:
        progress["levels"][entry.id] = {"finished": _now(), "xp": xp, "stars": stars, "state": active["state"]}
    record = progress["levels"][entry.id]
    record["state"] = active["state"]
    record["stars"] = max(record["stars"], stars)
    payout: Payout = {"level": entry.id, "xp": xp, "first_time": first_time, "rank_before": rank_before, "rank_after": score.rank(progress["xp"])["title"]}
    progress["last_payout"] = payout
    save.write_progress(progress)
    save.clear_active()
    save.clear_observed()
    return payout


def _check_step(step: kit.Step, text: kit.StepText, lab: kit.Lab, active: save.Active, answer: str | None, messages: Mapping[str, str]) -> kit.Verdict:
    """
    Check one quest step by its kind, its message in the player's language.

    Parameters
    ----------
    step : kit.Step
        The step.
    text : kit.StepText
        Its texts in the player's language, for a prediction's reveal.
    lab : kit.Lab
        The lab.
    active : save.Active
        The level in progress: its state, and the lines typed since it started.
    answer : str | None
        What the player answered, or None.
    messages : Mapping[str, str]
        The messages in the player's language (`_messages`).

    Returns
    -------
    kit.Verdict
        The step's verdict; a read step always passes, with no message.
    """
    verdict = kit.Verdict(True, "")
    if isinstance(step, kit.AnswerStep):
        verdict = step.check(lab, active["state"], answer or "")
    elif isinstance(step, kit.WatchStep):
        verdict = step.watch(lab, active["state"], active["typed"])
    elif isinstance(step, kit.ChoiceStep):
        verdict = kit.choose(step, answer or "")
    message = text.reveal if isinstance(step, kit.ChoiceStep) and verdict.solved else _say(verdict.message, messages)
    return dataclasses.replace(verdict, message=message)


def _loss(entry: runner.Level, active: save.Active, lab: kit.Lab, messages: Mapping[str, str]) -> str:
    """
    Say whether a step the quest checks now finds the player's work lost for good.

    Parameters
    ----------
    entry : runner.Level
        The level in progress.
    active : save.Active
        Its record, the lines typed read in.
    lab : kit.Lab
        Its lab.
    messages : Mapping[str, str]
        The messages in the player's language (`_messages`).

    Returns
    -------
    str
        The first lost verdict's message among the steps `quest_step` would check (the current
        one; in a challenge every goal not met yet), or empty when nothing is lost.
    """
    language = _language()
    pending = [] if _quest_done(active, entry) else _pending(active, entry)
    verdicts = (_check_step(step, entry.texts[language].steps[step.id], lab, active, None, messages) for step in pending)
    return next((verdict.message for verdict in verdicts if verdict.lost), "")


def _lost_over_pleased(observation: Observation, loss: str) -> Observation:
    """
    Let a loss win over what Rama would say pleased about the lines that caused it.

    Parameters
    ----------
    observation : Observation
        What changed and what Rama says (`_observation`).
    loss : str
        The loss's message (`_loss`), or empty.

    Returns
    -------
    Observation
        The same, with each ``ok`` reaction saying the loss instead, as an error, when there is one.
    """
    said: list[Reaction] = [
        {"line": reaction["line"], "mood": "err", "text": markup.parse(loss), "moment": None} if loss and reaction["mood"] == "ok" else reaction
        for reaction in observation["reactions"]
    ]
    return {**observation, "reactions": said}


def _cards_to_review(chapter: str | None, progress: save.Progress, limit: int) -> list[cards.Card]:
    """
    Choose the cards to review (see `due_cards`).

    Parameters
    ----------
    chapter : str | None
        A chapter id, or None for every chapter.
    progress : save.Progress
        The player's progress.
    limit : int
        Most cards to give.

    Returns
    -------
    list[cards.Card]
        The cards, in the order to ask them.
    """
    language = progress["language"]
    if chapter is not None:
        pool = list(cards.deck(chapter, language).cards)
    else:
        levels = runner.catalogue()
        met = {levels[level_id].chapter for level_id in progress["levels"] if level_id in levels}
        pool = [card for name in CHAPTERS for card in cards.deck(name, language).cards if card.id in progress["cards"] or name in met]
    return cards.pick(pool, progress["cards"], date.today(), limit, random.Random())


def _level_summary(entry: runner.Level, finished: save.LevelRecord | None, language: Language) -> LevelSummary:
    """
    Summarise a level for the map of chapters.

    Parameters
    ----------
    entry : runner.Level
        The level.
    finished : save.LevelRecord | None
        Its record once the player has finished it, else None.
    language : Language
        The language of its title.

    Returns
    -------
    LevelSummary
        The summary.
    """
    return {
        "id": entry.id,
        "title": entry.texts[language].title,
        "difficulty": entry.difficulty,
        "xp": entry.xp,
        "command": entry.command,
        "stars": finished["stars"] if finished is not None else 0,
        "challenge": entry.challenge,
        "done": finished is not None,
        "has_quest": bool(entry.quest),
    }


def _command_card(entry: runner.Level, language: Language) -> CommandCard:
    """
    Show a level's command card.

    Parameters
    ----------
    entry : runner.Level
        The level.
    language : Language
        The language of its text.

    Returns
    -------
    CommandCard
        Its card, the text parsed.
    """
    return {"level": entry.id, "command": entry.card.command, "text": markup.parse(entry.texts[language].card)}


def _stars(active: save.Active, entry: runner.Level) -> int:
    """
    Count the stars still in play for the level in progress.

    Parameters
    ----------
    active : save.Active
        Its record, with the lines typed so far.
    entry : runner.Level
        The level.

    Returns
    -------
    int
        1 to 3 (`firstcommit.score.stars`).
    """
    return score.stars(active["hints"], len(active["typed"]), entry.par)


def _active_view(active: save.Active, entry: runner.Level) -> ActiveView:
    """
    Show the level in progress.

    Parameters
    ----------
    active : save.Active
        Its saved record.
    entry : runner.Level
        The level.

    Returns
    -------
    ActiveView
        The view.
    """
    return {
        "level": entry.id,
        "step": active["step"],
        "steps": len(entry.quest),
        "hints": active["hints"],
        "hints_total": len(entry.texts["en"].hints),
        "attempts": active["attempts"],
        "started": active["started"],
        "auto_check": _quest_done(active, entry),
        "commands": len(active["typed"]),
        "stars": _stars(active, entry),
        "done": active["done"],
    }


def _pending(active: save.Active, entry: runner.Level) -> list[kit.Step]:
    """
    Give the quest steps to check now: the current one of a guided quest, every goal not met yet of a challenge.

    Parameters
    ----------
    active : save.Active
        The record of the level in progress, its quest not done.
    entry : runner.Level
        The level.

    Returns
    -------
    list[kit.Step]
        The steps, in quest order.
    """
    pending = [entry.quest[active["step"]]]
    if entry.challenge:
        pending = [step for step in entry.quest if step.id not in active["done"]]
    return pending


def _quest_done(active: save.Active, entry: runner.Level) -> bool:
    """
    Tell whether the guided quest of the level in progress is done; a level without one is.

    Parameters
    ----------
    active : save.Active
        The saved record of the level in progress.
    entry : runner.Level
        The level.

    Returns
    -------
    bool
        True once every step has passed.
    """
    return active["step"] >= len(entry.quest)


def _step_view(step: kit.Step, text: kit.StepText, state: kit.State) -> StepView:
    """
    Show a quest step without its checks.

    Parameters
    ----------
    step : kit.Step
        The step.
    text : kit.StepText
        Its texts in the player's language; a prediction's options keep their English values.
    state : kit.State
        The level's state, to fill its text.

    Returns
    -------
    StepView
        The view.
    """
    kind: Literal["answer", "watch", "read", "choice"] = "read"
    options: tuple[str, ...] = ()
    if isinstance(step, kit.AnswerStep):
        kind = "answer"
    elif isinstance(step, kit.WatchStep):
        kind = "watch"
    elif isinstance(step, kit.ChoiceStep):
        kind, options = "choice", step.options
    return {
        "id": step.id,
        "kind": kind,
        "text": _blocks(text.text, state),
        "command": _fill(step.command, state, _shell_word),
        "question": _blocks(text.question, state),
        "placeholder": _fill(text.placeholder, state),
        "choices": [{"value": option, "text": markup.parse(shown)} for option, shown in zip(options, text.options, strict=True)],
        "more": _blocks(text.more, state),
        "look": list(step.look),
    }


def _card_view(card: cards.Card, pays: bool, rng: random.Random, language: Language) -> CardView:
    """
    Show a card without its answer.

    Parameters
    ----------
    card : cards.Card
        The card.
    pays : bool
        Whether a right answer would earn XP (the card is new or due).
    rng : random.Random
        Shuffles the choices.
    language : Language
        The language of its level's name.

    Returns
    -------
    CardView
        The view.
    """
    return {
        "id": card.id,
        "chapter": card.chapter,
        "kind": card.kind,
        "level": card.level,
        "level_name": cards.LEVEL_NAMES[language][card.level],
        "prompt": markup.parse(card.prompt),
        "code": card.code,
        "choices": [{"value": option, "text": _option_text(card, option)} for option in cards.choices(card, rng)],
        "placeholder": card.placeholder,
        "pays": pays,
    }


def _language() -> Language:
    """
    Read the language the game speaks.

    Returns
    -------
    Language
        The player's choice, English until they pick one (`set_language`).
    """
    return save.load_progress()["language"]


def _messages(entry: runner.Level, language: Language) -> Mapping[str, str]:
    """
    Give every message a level may show, turned from English into a language.

    Parameters
    ----------
    entry : runner.Level
        The level.
    language : Language
        The language.

    Returns
    -------
    Mapping[str, str]
        Empty for English, which needs no turning; else the game's own messages, the shared
        reactions' and the level's, by their English text.
    """
    found: Mapping[str, str] = {}
    if language == "es":
        found = {**SPANISH, **reactions.SPANISH, **entry.texts["es"].messages}
    return found


def _say(text: str, messages: Mapping[str, str]) -> str:
    """
    Turn a message into the player's language.

    Parameters
    ----------
    text : str
        The message in English, as the game, a reaction rule or a level's code wrote it.
    messages : Mapping[str, str]
        The messages in the player's language (`_messages`), empty for English.

    Returns
    -------
    str
        Its text in the player's language; an empty message stays empty.

    Raises
    ------
    KeyError
        If the message has no translation: a level module whose Spanish sibling lacks one of its
        messages (the level harness checks every message it meets).
    """
    return messages[text] if messages and text else text


def _typed(answer: str | None) -> str | None:
    """
    Make an answer the player typed safe for a level: blank counts as no answer.

    Parameters
    ----------
    answer : str | None
        What the player sent.

    Returns
    -------
    str | None
        The answer as `_encodable` makes it, or None if it is missing or blank.
    """
    return _encodable(answer) if answer is not None and answer.strip() else None


def _encodable(text: str) -> str:
    """
    Replace the characters UTF-8 cannot encode, such as lone surrogates, with ``?``.

    Parameters
    ----------
    text : str
        Text from the player.

    Returns
    -------
    str
        The same text where it can be encoded.
    """
    return text.encode("utf-8", "replace").decode("utf-8")


def _option_text(card: cards.Card, option: str) -> list[Block]:
    """
    Show one answer of a card: a predict card's options are program output, shown as written.

    Parameters
    ----------
    card : cards.Card
        The card, in the player's language.
    option : str
        One of its options, or its right answer, as the page sends it.

    Returns
    -------
    list[Block]
        One verbatim block for a predict card, else the parsed text in the card's language.
    """
    return [{"kind": "code", "text": option}] if card.kind == "predict" else markup.parse(card.shown[option] if card.shown else option)


def _fill(text: str, state: Mapping[str, Any], show: Callable[[Any], str] = str) -> str:
    """
    Replace ``{{key}}`` placeholders with values from a level's state.

    Parameters
    ----------
    text : str
        Text that may hold placeholders.
    state : Mapping[str, Any]
        The level's state.
    show : Callable[[Any], str]
        Writes one value into the text: as it is, or `_shell_word` in a command.

    Returns
    -------
    str
        The text; a placeholder whose key is not in the state stays as written.
    """
    return PLACEHOLDER.sub(lambda match: show(state[match[1]]) if match[1] in state else match[0], text)


def _shell_word(value: Any) -> str:
    """
    Write a value into a command the player may run, as exactly one shell word.

    Parameters
    ----------
    value : Any
        A value from a level's state, such as a branch name read from a repository.

    Returns
    -------
    str
        The value, quoted with `shlex.quote` when the shell would read anything in it.
    """
    return shlex.quote(str(value))


def _blocks(text: str, state: Mapping[str, Any]) -> list[Block]:
    """
    Fill a text's placeholders, then parse it.

    Parameters
    ----------
    text : str
        Game text.
    state : Mapping[str, Any]
        The level's state.

    Returns
    -------
    list[Block]
        Its blocks.
    """
    return markup.parse(_fill(text, state))


def _now() -> str:
    """
    Give the local time, for records the player may read.

    Returns
    -------
    str
        ISO 8601, to the second, with the UTC offset.
    """
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _git_diagnosis() -> Diagnosis:
    """
    Check the installed git.

    Returns
    -------
    Diagnosis
        Whether git is found and at least `MIN_GIT`.
    """
    try:
        printed = subprocess.run(["git", "--version"], capture_output=True, text=True, check=False, timeout=gitcmd.TIMEOUT).stdout
    except FileNotFoundError:
        printed = ""
    match = GIT_VERSION.search(printed)
    version = (int(match[1]), int(match[2])) if match else None
    wanted = f"{MIN_GIT[0]}.{MIN_GIT[1]} or newer is needed, {TARGET_GIT[0]}.{TARGET_GIT[1]} is what the levels were checked with"
    detail = f"git was not found ({wanted})" if version is None else f"git {version[0]}.{version[1]} ({wanted})"
    return {"check": "git", "ok": version is not None and version >= MIN_GIT, "detail": detail}


def _python_diagnosis() -> Diagnosis:
    """
    Check the running Python.

    Returns
    -------
    Diagnosis
        Whether it is at least `MIN_PYTHON`.
    """
    running = sys.version_info[:2]
    detail = f"Python {running[0]}.{running[1]} ({MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is needed)"
    return {"check": "python", "ok": running >= MIN_PYTHON, "detail": detail}


def _home_diagnosis() -> Diagnosis:
    """
    Check the game home: an absolute folder the game can create and write to.

    Returns
    -------
    Diagnosis
        Whether the home is usable, and where it is.
    """
    try:
        home = save.home()
        home.mkdir(parents=True, exist_ok=True)
        ok = os.access(home, os.W_OK)
        detail = f"{home} is {'' if ok else 'not '}writable"
    except ValueError as error:
        ok, detail = False, str(error)
    except OSError as error:
        ok, detail = False, f"cannot create the game home: {error}"
    return {"check": "home", "ok": ok, "detail": detail}
