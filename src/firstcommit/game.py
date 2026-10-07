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
from its English text (`_messages`). Lessons, the changes the page animates and the
playground's explanations are in English only.

Records returned here are the API contract of the web routes: changing a field is a change to
the page too. Every field the player reads is parsed blocks; every value the page sends back
(a step's command, a card option's ``value``, an answer) stays a raw string. Text the player sends (answers, card replies) may hold anything; characters that
UTF-8 cannot encode, such as the lone surrogates JSON can carry, are replaced here, so levels and
cards only ever see a wrong answer. Errors the interfaces handle:

- `UnknownIdError`: an unknown level, chapter or card id, or a playground person or button (the
  routes answer 404). It is raised only by the one lookup of each kind of id, at the top of a
  function, so a ``KeyError`` from a level's setup, the scoring or a lesson stays what it is: a bug;
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
import os
import random
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, get_args

from firstcommit import (
    cards,
    changes,
    commands,
    demos,
    explanations,
    gitcmd,
    kit,
    markup,
    playground,
    reactions,
    repomap,
    runner,
    save,
    score,
)
from firstcommit import guide as map_guide
from firstcommit.cards import CardKind
from firstcommit.changes import Event
from firstcommit.chapters import BLURBS, CHAPTERS
from firstcommit.demos import Line
from firstcommit.lab import Lab
from firstcommit.markup import Block
from firstcommit.playground import ButtonOffError as ButtonOffError
from firstcommit.reactions import ReactionRule
from firstcommit.records import Art, ButtonView, Command, Language, Mood, Press, Who
from firstcommit.repomap import ObjectInfo, Snapshot
from firstcommit.save import Payout
from firstcommit.save import SaveError as SaveError
from firstcommit.save import home as home
from firstcommit.score import Rank

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
MIN_GIT = (2, 32)
TARGET_GIT = (2, 43)
MIN_PYTHON = (3, 12)
GIT_VERSION = re.compile(r"git version (\d+)\.(\d+)")
CHALLENGE_MOODS = ("warn", "err")
"""What Rama still says in a challenge: danger and errors, never guidance."""
QUEST_FIRST = "The guided quest is not finished yet: step {step} of {steps} is next."
LANGUAGES: tuple[Language, ...] = get_args(Language)
SPANISH = {
    QUEST_FIRST: "La misión guiada aún no ha terminado: el siguiente es el paso {step} de {steps}.",
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
    has_lesson: bool
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
    """What Rama says about one typed line (`firstcommit.reactions`)."""

    line: str
    mood: Mood
    text: list[Block]


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
    one the game speaks.
    """

    language: Language
    xp: int
    rank: Rank
    chapters: list[ChapterSummary]
    active: ActiveView | None
    last_payout: Payout | None
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
    """

    id: str
    kind: Literal["answer", "watch", "read", "choice"]
    text: list[Block]
    command: str
    question: list[Block]
    placeholder: str
    choices: list[Choice]
    more: list[Block]


class LevelView(TypedDict):
    """
    A level's page: what to do, the quest steps and how many hints exist.

    ``question`` and ``placeholder`` are empty for a level checked against the repository only.
    ``hints`` are the hints already revealed while this level is in progress (empty otherwise),
    so a reloaded page can show what the player paid for. ``debrief`` is set once the player has
    finished the level, filled from its last play, so it shows even when the level was solved
    from the terminal. ``scene`` is empty for a level without one; ``scene_seen`` says whether
    the player has seen it (`see_scene`). ``challenge`` marks a level whose goals are met in any
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
    card: CommandCard | None
    challenge: bool
    briefing: list[Block]
    question: list[Block]
    placeholder: str
    steps: list[StepView]
    hints_total: int
    has_lesson: bool
    hints: list[list[Block]]
    debrief: list[Block] | None


class EventView(TypedDict):
    """One "what just happened" event, its text parsed like every other text the page shows."""

    kind: str
    text: list[Block]


class SlideView(TypedDict):
    """One lesson slide with its figure, and what its commands changed, told as the live feed tells it."""

    id: str
    title: str
    text: list[Block]
    view: Literal["map", "areas", "places", "objects", "terminal", "none"]
    transcript: list[Line]
    map: Snapshot
    objects: list[ObjectInfo]
    events: list[EventView]
    more: list[Block]


class LessonView(TypedDict):
    """A level's lesson."""

    level: str
    title: str
    slides: list[SlideView]


class FigureView(TypedDict):
    """One figure of the map guide: its repository before and after one change, and that change's real commands and output."""

    before: Snapshot
    after: Snapshot
    transcript: list[Line]


GuideView = dict[str, FigureView]
"""The map guide's figures by section id, in the guide's order (`firstcommit.guide.FIGURES`)."""


class StepResult(TypedDict):
    """The result of a quest step: whether a goal was met, feedback, and where the quest stands now (``done``, as in `ActiveView`)."""

    correct: bool
    message: list[Block]
    step: int
    quest_done: bool
    done: list[str]


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
        "card": _command_card(entry, language) if finished is not None or not entry.challenge else None,
        "challenge": entry.challenge,
        "briefing": _blocks(texts.briefing, state),
        "question": _blocks(texts.question, state),
        "placeholder": _fill(texts.placeholder, state),
        "steps": [_step_view(step, texts.steps[step.id], state) for step in entry.quest],
        "hints_total": len(texts.hints),
        "has_lesson": bool(entry.lesson),
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


def lesson(level_id: str) -> LessonView:
    """
    Give a level's lesson, each slide with the figure its commands really produce.

    Parameters
    ----------
    level_id : str
        The level's id.

    Returns
    -------
    LessonView
        The slides; none for a level without a lesson. Each slide's events are what changed
        from the slide before (the first slide's from the lesson's empty folder).

    Raises
    ------
    UnknownIdError
        If no level has this id.
    """
    entry = _level(level_id)
    frames = demos.frames(entry.lesson)
    befores = [repomap.empty(), *(frame["map"] for frame in frames[:-1])]
    slides: list[SlideView] = [
        {
            "id": slide.id,
            "title": slide.title,
            "text": markup.parse(slide.text),
            "view": slide.view,
            "transcript": frame["transcript"],
            "map": frame["map"],
            "objects": frame["objects"],
            "events": _event_views(changes.describe(before, frame["map"])),
            "more": markup.parse(slide.more),
        }
        for slide, frame, before in zip(entry.lesson, frames, befores, strict=True)
    ]
    return {"level": entry.id, "title": entry.texts[_language()].title, "slides": slides}


def guide() -> GuideView:
    """
    Give the map guide's figures, drawn from real git like a lesson's.

    Each figure runs as a two-slide lesson (`firstcommit.guide.lesson`): the first slide builds
    its repository, the second makes the change its section is about. `firstcommit.demos`
    keeps the frames per process, so only the first call runs git.

    Returns
    -------
    GuideView
        Every figure of `firstcommit.guide.FIGURES`, by section id: the first slide's map, the
        second slide's map, and the second slide's commands with their output.
    """
    figures: GuideView = {}
    for figure in map_guide.FIGURES:
        before, after = demos.frames(map_guide.lesson(figure))
        figures[figure.section] = {"before": before["map"], "after": after["map"], "transcript": after["transcript"]}
    return figures


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
    return _active_view(active, entry)


def quest_step(answer: str | None) -> StepResult:
    """
    Check the current step of the guided quest, and move on if it passed.

    Only the current step is ever checked, so a guided quest is played in order; a challenge's
    goals are all checked, and any of them may be met first. An answer step is
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
        if not _quest_done(active, entry):
            verdicts = [(step.id, _check_step(step, entry.texts[language].steps[step.id], lab, active, _typed(answer), _messages(entry, language))) for step in _pending(active, entry)]
            reached = [step_id for step_id, verdict in verdicts if verdict.solved]
            unmet = [verdict for _, verdict in verdicts if not verdict.solved]
            message = markup.parse((unmet[0] if unmet else verdicts[-1][1]).message)
        if reached:
            active["done"] = [step.id for step in entry.quest if step.id in {*active["done"], *reached}]
            active["step"] = len(active["done"])
            save.write_active(active)
        for goal in reached:
            active = _fire(entry, active, goal)
    return {"correct": bool(reached), "message": message, "step": active["step"], "quest_done": _quest_done(active, entry), "done": active["done"]}


def check(answer: str | None, auto: bool) -> CheckResult:
    """
    Check the level in progress, and pay for it once solved.

    While the guided quest is unfinished, an automatic check (the page polling) never solves the
    level: its message points to the next step, so the player sees the end of the lesson, unless
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
    whichever process asks; the first observation of a level has no events, and right after it
    the level's events with no goal run (`firstcommit.kit.LevelEvent`), so the next observation
    tells their changes. The lines typed
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
        now, typed = _look(entry.id, lab, last, active["typed"])
        observation = _observation(last, now, _buttons(lab, now), typed, _rules(entry), _messages(entry, _language()))
        if now != last:
            save.write_observed(now)
        if last is None or last["level"] != entry.id:
            _fire(entry, active, "")
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
        before = _observation(last, then, _buttons(lab, then), typed_before, _rules(entry), messages)
        facts = playground.facts(lab, who, _clones(then)[who], then["github"])
        pressed = playground.press(lab, who, which)
        active = _catch_up(active)
        now, typed_during = _look(entry.id, lab, then, active["typed"])
        observation = _observation(then, now, _buttons(lab, now), typed_during, _rules(entry), messages)
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
    """End the level in progress and erase all progress, damaged files included; the game's git configuration starts over too."""
    with save.lock():
        runner.remove_labs()
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
    return [_card_view(card, cards.is_due(progress["cards"].get(card.id), today), rng) for card in _cards_to_review(chapter, progress, limit)]


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
    machine, and each command line typed logged in the game home for `observe`. The page's
    terminal and ``firstcommit shell`` both run it.

    Returns
    -------
    list[str]
        The program and its arguments.
    """
    home = save.home()
    startup = save.write_shell_startup(commands.startup(home / save.COMMANDS_FILE, home / save.HISTORY_FILE))
    return ["bash", "--noprofile", "--rcfile", str(startup), "-i"]


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
        git (at least `MIN_GIT`; the lessons are checked against `TARGET_GIT`), Python (at least
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


def _playground_id[Name: str](name: str, names: Iterable[Name], what: str) -> Name:
    """
    Look a playground person or button up by its name.

    Parameters
    ----------
    name : str
        The name the page sent.
    names : Iterable[Name]
        The playground's names of that kind.
    what : str
        The kind, for the message: ``"person"`` or ``"button"``.

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
        The moment: empty for right after the first observation, else the id of the goal just reached.

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
    typed: list[Command],
    rules: tuple[ReactionRule, ...],
    messages: Mapping[str, str],
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
    typed : list[Command]
        The commands typed between the two (`_look`).
    rules : tuple[ReactionRule, ...]
        The level's reaction rules (`_rules`).
    messages : Mapping[str, str]
        The messages in the player's language (`_messages`).

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
    said = [(command, reactions.react(command, kinds, now["project"]["exists"], staged, rules)) for command in typed]
    return {
        "level": now["level"],
        "project": now["project"],
        "github": now["github"],
        "teammate": now["teammate"],
        "events": _event_views(events),
        "teammate_events": _event_views(teammate_events),
        "buttons": buttons,
        "commands": typed,
        "reactions": [{"line": command["line"], "mood": rule.mood, "text": markup.parse(_say(rule.text, messages))} for command, rule in said if rule is not None],
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
        "has_lesson": bool(entry.lesson),
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
    }


def _card_view(card: cards.Card, pays: bool, rng: random.Random) -> CardView:
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
        "level_name": cards.LEVEL_NAMES[card.level],
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
    wanted = f"{MIN_GIT[0]}.{MIN_GIT[1]} or newer is needed, {TARGET_GIT[0]}.{TARGET_GIT[1]} is what the lessons were checked with"
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
