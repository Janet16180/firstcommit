"""
The levels and their labs: read every level module once into a typed record, and own the lab a level is played in.

A level module follows the contract of AUTHORING.md section 3.3. A module that breaks it is a bug
in the content, so reading it raises with the module's name and what is wrong.

There is one lab at a time, ``<home>/labs/<level id>/``. Starting a level removes every lab first
(through `termlab.sandbox`, which never deletes outside the home), so nothing a player did in an
earlier level can leak into the next one. Every lab starts with the game's git configuration in
place, whoever starts it (the game or the tests).
"""

import functools
import importlib
import pkgutil
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any

from termlab import sandbox

from firstcommit import gitcmd, kit, levels, save
from firstcommit.chapters import CHAPTERS

MODULE_NAME = re.compile(r"([a-z]+)_[a-z0-9_]+")
DIFFICULTIES = (1, 2, 3)
MIN_HINTS = 2
MAX_HINTS = 4

Setup = Callable[[kit.Lab], kit.State]
Check = Callable[[kit.Lab, kit.State, str | None], kit.Verdict]
Solve = Callable[[kit.Lab, kit.State], str | None]


@dataclass(frozen=True)
class Level:
    """
    One level, as read from its module.

    ``id`` is the module name with ``_`` turned into ``-``; ``chapter`` is the part before the
    first ``_``. The other fields are the module's names of AUTHORING.md section 3.3;
    ``question`` and ``placeholder`` are empty for a level checked against the repository only.
    """

    id: str
    chapter: str
    title: str
    difficulty: int
    xp: int
    lesson: tuple[kit.Slide, ...]
    quest: tuple[kit.Step, ...]
    briefing: str
    question: str
    placeholder: str
    hints: tuple[str, ...]
    debrief: str
    setup: Setup
    check: Check
    solve: Solve


def load(module: ModuleType) -> Level:
    """
    Read a level module into a record, checking its contract.

    Parameters
    ----------
    module : ModuleType
        A module named ``<chapter>_<slug>``.

    Returns
    -------
    Level
        The level.

    Raises
    ------
    ValueError
        If the module breaks the contract; the message names the module and the problem.
    """
    name = module.__name__.rsplit(".", 1)[-1]
    match = MODULE_NAME.fullmatch(name)
    values: dict[str, Any] = {key: getattr(module, key, None) for key in ("TITLE", "DIFFICULTY", "XP", "BRIEFING", "HINTS", "DEBRIEF", "setup", "check", "solve")}
    lesson = getattr(module, "LESSON", [])
    quest = getattr(module, "QUEST", [])
    question = getattr(module, "QUESTION", "")
    placeholder = getattr(module, "PLACEHOLDER", "")
    problem = None
    if match is None or match[1] not in CHAPTERS:
        problem = f"the module name must be <chapter>_<slug>, with a chapter among {', '.join(CHAPTERS)}"
    else:
        problem = (
            _texts_problem(values)
            or _question_problem(question, placeholder)
            or _numbers_problem(values)
            or _lesson_problem(lesson)
            or _quest_problem(quest)
        )
    if problem is not None:
        raise ValueError(f"level module {module.__name__}: {problem}")
    return Level(
        id=name.replace("_", "-"),
        chapter=name.split("_", 1)[0],
        title=values["TITLE"],
        difficulty=values["DIFFICULTY"],
        xp=values["XP"],
        lesson=tuple(lesson),
        quest=tuple(quest),
        briefing=values["BRIEFING"],
        question=question,
        placeholder=placeholder,
        hints=tuple(values["HINTS"]),
        debrief=values["DEBRIEF"],
        setup=values["setup"],
        check=values["check"],
        solve=values["solve"],
    )


def _is_text(value: Any) -> bool:
    """
    Tell whether a value is text that is not blank.

    Parameters
    ----------
    value : Any
        Any value.

    Returns
    -------
    bool
        True for a string with something besides whitespace.
    """
    return isinstance(value, str) and value.strip() != ""


def _texts_problem(values: dict[str, Any]) -> str | None:
    """
    Check the title, briefing, debrief and hints of a level module.

    Parameters
    ----------
    values : dict[str, Any]
        The module's names, None where missing.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    hints = values["HINTS"]
    blank = [key for key in ("TITLE", "BRIEFING", "DEBRIEF") if not _is_text(values[key])]
    problem = None
    if blank:
        problem = f"{blank[0]} must be text that is not empty"
    elif not isinstance(hints, list) or not MIN_HINTS <= len(hints) <= MAX_HINTS or not all(_is_text(hint) for hint in hints):
        problem = f"HINTS must be a list of {MIN_HINTS} to {MAX_HINTS} texts that are not empty"
    return problem


def _question_problem(question: Any, placeholder: Any) -> str | None:
    """
    Check the optional question of a level solved by a typed answer, and its placeholder.

    Parameters
    ----------
    question : Any
        The module's ``QUESTION``, ``""`` when missing.
    placeholder : Any
        The module's ``PLACEHOLDER``, ``""`` when missing.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    problem = None
    if not isinstance(question, str):
        problem = "QUESTION must be text"
    elif not isinstance(placeholder, str):
        problem = "PLACEHOLDER must be text"
    elif placeholder and not _is_text(question):
        problem = "PLACEHOLDER shows the shape of an answer, so it needs a QUESTION"
    elif "`" in placeholder:
        problem = "PLACEHOLDER is plain text: no backticks"
    return problem


def _numbers_problem(values: dict[str, Any]) -> str | None:
    """
    Check the difficulty, XP and functions of a level module.

    Parameters
    ----------
    values : dict[str, Any]
        The module's names, None where missing.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    difficulty = values["DIFFICULTY"]
    xp = values["XP"]
    missing = [key for key in ("setup", "check", "solve") if not callable(values[key])]
    problem = None
    if not isinstance(difficulty, int) or isinstance(difficulty, bool) or difficulty not in DIFFICULTIES:
        problem = f"DIFFICULTY must be one of {DIFFICULTIES}"
    elif not isinstance(xp, int) or isinstance(xp, bool) or xp <= 0:
        problem = "XP must be a whole number above zero"
    elif missing:
        problem = f"{missing[0]} must be a function"
    return problem


def _lesson_problem(lesson: Any) -> str | None:
    """
    Check a level's lesson.

    Parameters
    ----------
    lesson : Any
        The module's ``LESSON``.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    problem = None
    if not isinstance(lesson, list) or not all(isinstance(slide, kit.Slide) for slide in lesson):
        problem = "LESSON must be a list of kit.Slide"
    else:
        problem = _duplicate_problem("slide", [slide.id for slide in lesson])
    return problem


def _quest_problem(quest: Any) -> str | None:
    """
    Check a level's quest: a list of steps, each of one kind (answer, watch or read).

    Parameters
    ----------
    quest : Any
        The module's ``QUEST``.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    if not isinstance(quest, list) or not all(isinstance(step, kit.Step) for step in quest):
        return "QUEST must be a list of kit.AnswerStep, kit.WatchStep and kit.ReadStep"
    marked = [step.id for step in quest if isinstance(step, kit.AnswerStep) and "`" in step.placeholder]
    problem = _duplicate_problem("step", [step.id for step in quest])
    if problem is None and marked:
        problem = f"step {marked[0]!r}: its placeholder is plain text: no backticks"
    return problem


def _duplicate_problem(kind: str, ids: list[str]) -> str | None:
    """
    Check that ids are unique and not empty.

    Parameters
    ----------
    kind : str
        What they identify, for the message.
    ids : list[str]
        The ids, in order.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    seen: set[str] = set()
    problem = None
    for item in ids:
        if problem is None and (not item or item in seen):
            problem = f"{kind} id {item!r} is empty or used twice"
        seen.add(item)
    return problem


def discover(package: ModuleType) -> dict[str, Level]:
    """
    Read every level module of a package, in play order.

    Modules whose name starts with ``_`` are helpers and are not imported here.

    Parameters
    ----------
    package : ModuleType
        A package of level modules, such as `firstcommit.levels`.

    Returns
    -------
    dict[str, Level]
        Levels by id, sorted by chapter order, then difficulty, then id.

    Raises
    ------
    ValueError
        If a module breaks the level contract.
    """
    order = list(CHAPTERS)
    found = [load(importlib.import_module(f"{package.__name__}.{info.name}")) for info in pkgutil.iter_modules(package.__path__) if not info.name.startswith("_")]
    found.sort(key=lambda level: (order.index(level.chapter), level.difficulty, level.id))
    return {level.id: level for level in found}


@functools.cache
def catalogue() -> Mapping[str, Level]:
    """
    Give the game's levels, read once per process.

    Returns
    -------
    Mapping[str, Level]
        The levels of `firstcommit.levels` by id, in play order (read-only).

    Raises
    ------
    ValueError
        If a level module breaks the contract.
    """
    return MappingProxyType(discover(levels))


def labs_folder() -> Path:
    """
    Give the folder that holds the lab.

    Returns
    -------
    Path
        ``<home>/labs``.
    """
    return save.home() / save.LABS_FOLDER


def lab_of(level_id: str) -> kit.Lab:
    """
    Give the lab a level is played in.

    Parameters
    ----------
    level_id : str
        The level's id.

    Returns
    -------
    kit.Lab
        ``<home>/labs/<level id>``; it may not exist.
    """
    return kit.Lab(labs_folder() / level_id)


def start_lab(level: Level) -> kit.State:
    """
    Build a fresh lab for a level: remove every lab, make an empty one, and run the level's setup.

    The game's git configuration is created first if it is missing (never overwritten), so
    setup and the player's ``git init`` start from `firstcommit.gitcmd.BASE_CONFIG`. If setup
    fails, its lab is removed and the error raised again.

    Parameters
    ----------
    level : Level
        The level.

    Returns
    -------
    kit.State
        The state setup returned.

    Raises
    ------
    ValueError
        If setup returns something other than a dict (a bug in the level).
    """
    lab = lab_of(level.id)
    remove_labs()
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    lab.root.mkdir(parents=True)
    try:
        state = level.setup(lab)
        if not isinstance(state, dict):
            raise ValueError(f"level {level.id}: setup must return a dict of state, not {state!r}")
    except BaseException:
        remove_labs()
        raise
    return state


def remove_labs() -> None:
    """Remove every lab, even one whose folders a player locked."""
    sandbox.remove_tree(labs_folder(), save.home())
