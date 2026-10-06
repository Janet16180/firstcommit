"""
Every player action, in one place: the only module the command line and the web routes call.

Each function that changes the save holds its lock (termlab's store) for the whole
read-modify-write, and returns a plain record that is ready to send as JSON. Text fields are
filled from the level's state (``{{key}}``) and parsed into blocks (`firstcommit.markup`), so the
interfaces only render. Game rules never live in the interfaces (Ring Zero audit ARCH-1).

Records returned here are the API contract of the web routes: changing a field is a change to
the page too. Errors the interfaces handle:

- ``KeyError``: an unknown level, chapter or card id (the routes answer 404);
- `NotPlayingError`: an action on the level in progress when there is none (409);
- `firstcommit.save.SaveError`: a damaged save file (``firstcommit reset --yes`` starts over).

Anything else is a bug.
"""

import os
import random
import re
import subprocess
import sys
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from firstcommit import cards, changes, demos, gitcmd, kit, markup, repomap, runner, save, score
from firstcommit.cards import CardKind
from firstcommit.changes import Event
from firstcommit.chapters import CHAPTERS
from firstcommit.demos import Line
from firstcommit.markup import Block
from firstcommit.repomap import ObjectInfo, Snapshot
from firstcommit.save import Payout
from firstcommit.score import Rank

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
MIN_GIT = (2, 32)
TARGET_GIT = (2, 43)
MIN_PYTHON = (3, 12)
GIT_VERSION = re.compile(r"git version (\d+)\.(\d+)")


class LevelSummary(TypedDict):
    """A level as the map of chapters lists it."""

    id: str
    title: str
    difficulty: int
    xp: int
    done: bool
    has_lesson: bool
    has_quest: bool


class ChapterSummary(TypedDict):
    """A chapter and its levels, in play order."""

    id: str
    title: str
    levels: list[LevelSummary]
    cards: int


class ActiveView(TypedDict):
    """The level being played: how far the quest is, and the hints and attempts used."""

    level: str
    step: int
    steps: int
    hints: int
    hints_total: int
    attempts: int
    started: str


class Status(TypedDict):
    """The dashboard."""

    xp: int
    rank: Rank
    chapters: list[ChapterSummary]
    active: ActiveView | None
    last_payout: Payout | None
    cards_due: int


class StepView(TypedDict):
    """A guided-quest step as the page shows it (its checks stay on the server)."""

    id: str
    kind: Literal["answer", "watch", "read"]
    text: list[Block]
    command: str
    question: str
    placeholder: str


class LevelView(TypedDict):
    """
    A level's page: what to do, the quest steps and how many hints exist.

    ``hints`` are the hints already revealed while this level is in progress (empty otherwise),
    so a reloaded page can show what the player paid for.
    """

    id: str
    chapter: str
    chapter_title: str
    title: str
    difficulty: int
    xp: int
    briefing: list[Block]
    steps: list[StepView]
    hints_total: int
    has_lesson: bool
    hints: list[list[Block]]


class SlideView(TypedDict):
    """One lesson slide with its figure."""

    id: str
    title: str
    text: list[Block]
    view: Literal["map", "areas", "objects", "terminal", "none"]
    transcript: list[Line]
    map: Snapshot
    objects: list[ObjectInfo]


class LessonView(TypedDict):
    """A level's lesson."""

    level: str
    title: str
    slides: list[SlideView]


class StepResult(TypedDict):
    """The result of a quest step: right or not, feedback, and where the quest stands now."""

    correct: bool
    message: list[Block]
    step: int
    quest_done: bool


class CheckResult(TypedDict):
    """The result of checking the level; ``payout`` and ``debrief`` are set once it is solved."""

    solved: bool
    message: list[Block]
    payout: Payout | None
    debrief: list[Block] | None


class HintView(TypedDict):
    """A revealed hint, how many are used out of how many, and what this one cost."""

    hint: list[Block]
    used: int
    total: int
    cost: int


class Observation(TypedDict):
    """The live lab: the player's repository, the stand-in GitHub (if the level has one), and what changed."""

    level: str
    project: Snapshot
    github: Snapshot | None
    events: list[Event]


class CardView(TypedDict):
    """A flashcard to answer. Choices are shuffled on the server; the right answer is not sent."""

    id: str
    chapter: str
    kind: CardKind
    level: int
    prompt: list[Block]
    code: str
    choices: list[str]
    placeholder: str
    pays: bool


class CardResult(TypedDict):
    """The result of answering a card."""

    correct: bool
    answer: str
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


class NotPlayingError(Exception):
    """No level is in progress, for an action that needs one (the web routes answer 409)."""


def status() -> Status:
    """
    Give the dashboard.

    Returns
    -------
    Status
        XP and rank, every chapter with its levels, the level in progress, the last payout and
        how many cards wait for review (see `due_cards`).

    Raises
    ------
    firstcommit.save.SaveError
        If a save file is damaged.
    """
    progress = save.load_progress()
    active = save.load_active()
    levels = runner.catalogue()
    chapters: list[ChapterSummary] = [
        {
            "id": chapter,
            "title": title,
            "levels": [_level_summary(entry, entry.id in progress["levels"]) for entry in levels.values() if entry.chapter == chapter],
            "cards": len(cards.deck(chapter).cards),
        }
        for chapter, title in CHAPTERS.items()
    ]
    return {
        "xp": progress["xp"],
        "rank": score.rank(progress["xp"]),
        "chapters": chapters,
        "active": _active_view(active, levels[active["level"]]) if active is not None and active["level"] in levels else None,
        "last_payout": progress["last_payout"],
        "cards_due": len(_cards_to_review(None, progress, sys.maxsize)),
    }


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
        Its briefing and quest steps, filled from its state while it is in progress.

    Raises
    ------
    KeyError
        If no level has this id.
    """
    entry = runner.catalogue()[level_id]
    active = save.load_active()
    playing = active if active is not None and active["level"] == level_id else None
    state = playing["state"] if playing is not None else {}
    revealed = entry.hints[: playing["hints"]] if playing is not None else ()
    return {
        "id": entry.id,
        "chapter": entry.chapter,
        "chapter_title": CHAPTERS[entry.chapter],
        "title": entry.title,
        "difficulty": entry.difficulty,
        "xp": entry.xp,
        "briefing": _blocks(entry.briefing, state),
        "steps": [_step_view(step, state) for step in entry.quest],
        "hints_total": len(entry.hints),
        "has_lesson": bool(entry.lesson),
        "hints": [_blocks(hint_text, state) for hint_text in revealed],
    }


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
        The slides; none for a level without a lesson.

    Raises
    ------
    KeyError
        If no level has this id.
    """
    entry = runner.catalogue()[level_id]
    slides: list[SlideView] = [
        {
            "id": slide.id,
            "title": slide.title,
            "text": markup.parse(slide.text),
            "view": slide.view,
            "transcript": frame["transcript"],
            "map": frame["map"],
            "objects": frame["objects"],
        }
        for slide, frame in zip(entry.lesson, demos.frames(entry.lesson), strict=True)
    ]
    return {"level": entry.id, "title": entry.title, "slides": slides}


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
        The new level in progress, at the first quest step.

    Raises
    ------
    KeyError
        If no level has this id; the level in progress is then left alone.
    """
    entry = runner.catalogue()[level_id]
    with save.lock():
        save.clear_active()
        save.clear_observed()
        save.ensure_gitconfig(gitcmd.BASE_CONFIG)
        state = runner.start_lab(entry)
        active: save.Active = {"level": entry.id, "started": _now(), "step": 0, "hints": 0, "attempts": 0, "state": state}
        save.write_active(active)
    return _active_view(active, entry)


def quest_step(answer: str | None) -> StepResult:
    """
    Check the current step of the guided quest, and move on if it passed.

    Only the current step is ever checked, so the quest is played in order. An answer step is
    checked with ``answer`` (None counts as an empty answer), a watch step against the lab (the
    page polls it with None), and a read step always passes. Once the quest is done, nothing is
    checked and the result says so.

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
        correct = False
        message: list[Block] = []
        if active["step"] < len(entry.quest):
            verdict = _check_step(entry.quest[active["step"]], runner.lab_of(entry.id), active["state"], answer)
            correct = verdict.solved
            message = _blocks(verdict.message, active["state"])
        if correct:
            active["step"] += 1
            save.write_active(active)
    return {"correct": correct, "message": message, "step": active["step"], "quest_done": active["step"] >= len(entry.quest)}


def check(answer: str | None, auto: bool) -> CheckResult:
    """
    Check the level in progress, and pay for it once solved.

    The level may be solved before its quest is finished. A blank answer counts as no answer.
    A check the player asks for that fails counts as an attempt; an automatic one (the page
    polling) never does. Solving ends the level: the payout is kept in the progress (so any view
    can celebrate it) and the lab stays until another level starts.

    Parameters
    ----------
    answer : str | None
        What the player typed, or None.
    auto : bool
        Whether the page asked by itself rather than the player.

    Returns
    -------
    CheckResult
        Whether the level is solved, the check's feedback, and once solved the payout and the debrief.

    Raises
    ------
    NotPlayingError
        If no level is in progress.
    """
    typed = answer if answer is not None and answer.strip() else None
    with save.lock():
        active, entry = _playing()
        verdict = entry.check(runner.lab_of(entry.id), active["state"], typed)
        payout = None
        if verdict.solved:
            payout = _pay(entry, active["hints"])
        elif not auto:
            active["attempts"] += 1
            save.write_active(active)
    return {
        "solved": verdict.solved,
        "message": _blocks(verdict.message, active["state"]),
        "payout": payout,
        "debrief": _blocks(entry.debrief, active["state"]) if verdict.solved else None,
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
        cost = 0
        if active["hints"] < len(entry.hints):
            active["hints"] += 1
            save.write_active(active)
            first_time = entry.id not in save.load_progress()["levels"]
            cost = score.hint_cost(entry.xp, active["hints"], first_time)
    return {"hint": _blocks(entry.hints[active["hints"] - 1], active["state"]), "used": active["hints"], "total": len(entry.hints), "cost": cost}


def observe() -> Observation:
    """
    Snapshot the lab of the level in progress and tell what changed since the last observation.

    The snapshots are kept in the save (only when they changed), so the events are right
    whichever process asks; the first observation of a level has no events.

    Returns
    -------
    Observation
        The player's repository, the stand-in GitHub (None when the level has none) and the changes.

    Raises
    ------
    NotPlayingError
        If no level is in progress.
    """
    with save.lock():
        active, entry = _playing()
        lab = runner.lab_of(entry.id)
        project = repomap.snapshot(lab.project)
        github = repomap.snapshot(lab.github) if lab.github.exists() else None
        before = save.load_observed()
        events: list[Event] = []
        if before is not None and before["level"] == entry.id:
            events = changes.describe(cast(Snapshot, before["project"]), project)
            if before["github"] is not None and github is not None:
                events += changes.describe(cast(Snapshot, before["github"]), github)
        current: save.Observed = {"level": entry.id, "project": dict(project), "github": dict(github) if github is not None else None}
        if current != before:
            save.write_observed(current)
    return {"level": entry.id, "project": project, "github": github, "events": events}


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
        save.ensure_gitconfig(gitcmd.BASE_CONFIG)


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
    KeyError
        If `chapter` is not a chapter id.
    """
    progress = save.load_progress()
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
    KeyError
        If no card has this id.
    """
    card = cards.find(card_id)
    today = date.today()
    correct = cards.judge(card, reply)
    with save.lock():
        progress = save.load_progress()
        entry = progress["cards"].get(card_id)
        earned = score.card_score(card.level, correct, cards.is_due(entry, today), progress["streak"])
        progress["xp"] += earned.xp + earned.bonus
        progress["streak"] = earned.streak
        progress["best_streak"] = max(progress["best_streak"], earned.streak)
        progress["cards"][card_id] = cards.reschedule(entry, correct, today)
        save.write_progress(progress)
    return {"correct": correct, "answer": cards.answer(card), "explain": markup.parse(card.explain), "xp": earned.xp, "streak": earned.streak, "bonus": earned.bonus}


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
    KeyError
        If `chapter` is not a chapter id.
    """
    return {"chapter": chapter, "title": CHAPTERS[chapter], "notes": markup.parse(cards.deck(chapter).notes)}


def terminal_folder() -> str:
    """
    Give the folder a new terminal opens in: the lab's project, else the lab, else the player's home.

    The game's git configuration is created first if it is missing, so the shell starts from it.

    Returns
    -------
    str
        The folder.
    """
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
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
    """
    active = save.load_active()
    levels = runner.catalogue()
    if active is None or active["level"] not in levels:
        raise NotPlayingError("no level is in progress")
    return active, levels[active["level"]]


def _pay(entry: runner.Level, hints: int) -> Payout:
    """
    Record a solved level: pay it, keep the payout, and end the level (its lab stays).

    Parameters
    ----------
    entry : runner.Level
        The level solved.
    hints : int
        Hints revealed while playing it.

    Returns
    -------
    Payout
        What it paid.
    """
    progress = save.load_progress()
    first_time = entry.id not in progress["levels"]
    xp = score.level_reward(entry.xp, hints, first_time)
    rank_before = score.rank(progress["xp"])["title"]
    progress["xp"] += xp
    if first_time:
        progress["levels"][entry.id] = {"finished": _now(), "xp": xp}
    payout: Payout = {"level": entry.id, "xp": xp, "first_time": first_time, "rank_before": rank_before, "rank_after": score.rank(progress["xp"])["title"]}
    progress["last_payout"] = payout
    save.write_progress(progress)
    save.clear_active()
    save.clear_observed()
    return payout


def _check_step(step: kit.Step, lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict:
    """
    Check one quest step by its kind.

    Parameters
    ----------
    step : kit.Step
        The step.
    lab : kit.Lab
        The lab.
    state : kit.State
        The level's state.
    answer : str | None
        What the player typed, or None.

    Returns
    -------
    kit.Verdict
        The step's verdict; a read step always passes, with no message.
    """
    if step.check is not None:
        verdict = step.check(lab, state, answer or "")
    elif step.watch is not None:
        verdict = step.watch(lab, state)
    else:
        verdict = kit.Verdict(True, "")
    return verdict


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

    Raises
    ------
    KeyError
        If `chapter` is not a chapter id.
    """
    if chapter is not None:
        pool = list(cards.deck(chapter).cards)
    else:
        levels = runner.catalogue()
        met = {levels[level_id].chapter for level_id in progress["levels"] if level_id in levels}
        pool = [card for name in CHAPTERS for card in cards.deck(name).cards if card.id in progress["cards"] or name in met]
    return cards.pick(pool, progress["cards"], date.today(), limit, random.Random())


def _level_summary(entry: runner.Level, done: bool) -> LevelSummary:
    """
    Summarise a level for the map of chapters.

    Parameters
    ----------
    entry : runner.Level
        The level.
    done : bool
        Whether the player has finished it.

    Returns
    -------
    LevelSummary
        The summary.
    """
    return {"id": entry.id, "title": entry.title, "difficulty": entry.difficulty, "xp": entry.xp, "done": done, "has_lesson": bool(entry.lesson), "has_quest": bool(entry.quest)}


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
        "hints_total": len(entry.hints),
        "attempts": active["attempts"],
        "started": active["started"],
    }


def _step_view(step: kit.Step, state: kit.State) -> StepView:
    """
    Show a quest step without its checks.

    Parameters
    ----------
    step : kit.Step
        The step.
    state : kit.State
        The level's state, to fill its text.

    Returns
    -------
    StepView
        The view.
    """
    kind: Literal["answer", "watch", "read"] = "answer" if step.check is not None else "watch" if step.watch is not None else "read"
    return {
        "id": step.id,
        "kind": kind,
        "text": _blocks(step.text, state),
        "command": _fill(step.command, state),
        "question": _fill(step.question, state),
        "placeholder": _fill(step.placeholder, state),
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
        "prompt": markup.parse(card.prompt),
        "code": card.code,
        "choices": cards.choices(card, rng),
        "placeholder": card.placeholder,
        "pays": pays,
    }


def _fill(text: str, state: Mapping[str, Any]) -> str:
    """
    Replace ``{{key}}`` placeholders with values from a level's state.

    Parameters
    ----------
    text : str
        Text that may hold placeholders.
    state : Mapping[str, Any]
        The level's state.

    Returns
    -------
    str
        The text; a placeholder whose key is not in the state stays as written.
    """
    return PLACEHOLDER.sub(lambda match: str(state[match[1]]) if match[1] in state else match[0], text)


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
