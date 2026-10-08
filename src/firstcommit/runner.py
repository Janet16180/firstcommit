"""
The levels and their labs: read every level module once into a typed record, and own the lab a level is played in.

A level module follows the contract of AUTHORING.md section 3.3. A module that breaks it is a bug
in the content, so reading it raises with the module's name and what is wrong. Its texts in Spanish
live in a sibling module, ``<module>_es`` (`load`), which is never read as a level itself.

There is one lab at a time, ``<home>/labs/<level id>/``. Starting a level removes every lab first
(through `termlab.sandbox`, which never deletes outside the home), so nothing a player did in an
earlier level can leak into the next one. Every lab starts with the game's git configuration in
place, whoever starts it (the game or the tests).
"""

import functools
import importlib
import pkgutil
import re
import typing
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any

from termlab import sandbox

from firstcommit import gitcmd, kit, levels, reactions, save
from firstcommit.chapters import CHAPTERS
from firstcommit.records import Art, Language, Mood, View

MODULE_NAME = re.compile(r"([a-z]+)_[a-z0-9_]+")
DIFFICULTIES = (1, 2, 3)
MIN_HINTS = 2
MAX_HINTS = 4
MIN_OPTIONS = 2
MAX_OPTIONS = 3

Setup = Callable[[kit.Lab], kit.State]
Check = Callable[[kit.Lab, kit.State, str | None, kit.Typed], kit.Verdict]
Solve = Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]
QuestAction = Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]
"""The player's part of one quest step (a module's ``QUEST_ACTIONS``): it types the step's lines, and gives the answer for a step that asks one."""


SPANISH_SUFFIX = "_es"
TEXT_NAMES = ("TITLE", "BRIEFING", "QUESTION", "PLACEHOLDER", "HINTS", "DEBRIEF", "CARD", "SCENE", "STEPS")
"""The names of a level's Spanish module that are not messages."""


@dataclass(frozen=True)
class LevelTexts:
    """
    Every text of a level in one language.

    ``card`` is the command card's text, ``scene`` the scene frames' texts in order, and ``steps``
    the quest steps' texts by step id. ``messages`` turns each English message the level's code
    returns (a module constant: a watch's or check's message, a reaction's text) into this
    language's; it is empty for English.
    """

    title: str
    briefing: str
    question: str
    placeholder: str
    hints: tuple[str, ...]
    debrief: str
    card: str
    scene: tuple[str, ...]
    steps: Mapping[str, kit.StepText]
    messages: Mapping[str, str]


@dataclass(frozen=True)
class Level:
    """
    One level, as read from its module.

    ``id`` is the module name with ``_`` turned into ``-``; ``chapter`` is the part before the
    first ``_``. The other fields are the module's names of AUTHORING.md section 3.3;
    ``scene``, ``reactions`` and ``events`` are empty for a level without them, and ``view``, the
    level screen's main view, is your station for a level that names none; ``tape`` says whether
    the level shows the black box's tape of HEAD's moves; ``actions`` is the module's
    ``QUEST_ACTIONS``, the player's part of each step, read by the level tests and by dev mode. ``challenge``
    marks a level whose quest is goals met in any order, with no guidance. ``texts`` holds every
    text the player reads, by language; the cards, scene frames and steps keep the English ones
    the module wrote, with what is not text (the command, the pictures, the checks).
    """

    id: str
    chapter: str
    difficulty: int
    xp: int
    command: str
    par: int
    card: kit.CommandCard
    scene: tuple[kit.SceneFrame, ...]
    view: View
    tape: bool
    actions: Mapping[str, QuestAction]
    reactions: tuple[kit.ReactionRule, ...]
    events: tuple[kit.LevelEvent, ...]
    challenge: bool
    quest: tuple[kit.Step, ...]
    texts: Mapping[Language, LevelTexts]
    setup: Setup
    check: Check
    solve: Solve


def load(module: ModuleType, spanish: ModuleType | None = None) -> Level:
    """
    Read a level module and its Spanish sibling into a record, checking their contract.

    Parameters
    ----------
    module : ModuleType
        A module named ``<chapter>_<slug>``.
    spanish : ModuleType | None
        Its texts in Spanish (AUTHORING.md section 3.3), or None, which shows the English ones.

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
    values: dict[str, Any] = {
        key: getattr(module, key, None) for key in ("TITLE", "DIFFICULTY", "XP", "COMMAND", "PAR", "CARD", "BRIEFING", "HINTS", "DEBRIEF", "setup", "check", "solve")
    }
    scene = getattr(module, "SCENE", [])
    view: Any = getattr(module, "VIEW", "station")
    tape = getattr(module, "TAPE", False)
    actions = getattr(module, "QUEST_ACTIONS", {})
    level_reactions = getattr(module, "REACTIONS", [])
    events = getattr(module, "EVENTS", [])
    challenge = getattr(module, "CHALLENGE", False)
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
            or _orbit_problem(values)
            or _scene_problem(scene)
            or _view_problem(view)
            or (None if isinstance(tape, bool) else "TAPE must be True or False")
            or (None if isinstance(actions, dict) and all(callable(action) for action in actions.values()) else "QUEST_ACTIONS must map step ids to functions")
            or _reactions_problem(level_reactions)
            or _quest_problem(quest)
            or _events_problem(events, quest)
            or _challenge_problem(challenge, quest)
        )
    if problem is not None:
        raise ValueError(f"level module {module.__name__}: {problem}")
    english = LevelTexts(
        title=values["TITLE"],
        briefing=values["BRIEFING"],
        question=question,
        placeholder=placeholder,
        hints=tuple(values["HINTS"]),
        debrief=values["DEBRIEF"],
        card=values["CARD"].text,
        scene=tuple(frame.text for frame in scene),
        steps=MappingProxyType({step.id: step_text(step) for step in quest}),
        messages=MappingProxyType({}),
    )
    translated = english if spanish is None else _spanish_texts(spanish, module, english)
    return Level(
        id=name.replace("_", "-"),
        chapter=name.split("_", 1)[0],
        difficulty=values["DIFFICULTY"],
        xp=values["XP"],
        command=values["COMMAND"],
        par=values["PAR"],
        card=values["CARD"],
        scene=tuple(scene),
        view=view,
        tape=tape,
        actions=MappingProxyType(dict(actions)),
        reactions=tuple(level_reactions),
        events=tuple(events),
        challenge=challenge,
        quest=tuple(quest),
        texts=MappingProxyType({"en": english, "es": translated}),
        setup=values["setup"],
        check=values["check"],
        solve=values["solve"],
    )


def step_text(step: kit.Step) -> kit.StepText:
    """
    Gather a quest step's texts.

    Parameters
    ----------
    step : kit.Step
        The step.

    Returns
    -------
    kit.StepText
        Its text and more, plus its question, placeholder, options and reveal where its kind has them.
    """
    found = kit.StepText(text=step.text, more=step.more)
    if isinstance(step, kit.AnswerStep):
        found = kit.StepText(text=step.text, more=step.more, question=step.question, placeholder=step.placeholder)
    elif isinstance(step, kit.ChoiceStep):
        found = kit.StepText(text=step.text, more=step.more, question=step.question, options=step.options, reveal=step.reveal)
    return found


def _spanish_texts(spanish: ModuleType, module: ModuleType, english: LevelTexts) -> LevelTexts:
    """
    Read a level's Spanish module, checking it holds the same texts as the English one.

    Parameters
    ----------
    spanish : ModuleType
        The module ``<module>_es``.
    module : ModuleType
        The level's own module, already read.
    english : LevelTexts
        Its texts.

    Returns
    -------
    LevelTexts
        The texts in Spanish; ``messages`` maps the value of each English constant the Spanish
        module also defines to the Spanish one.

    Raises
    ------
    ValueError
        If the Spanish module lacks a text, has one the English module does not, or one of
        another shape; the message names the module and the name.
    """
    names = [name for name in vars(spanish) if name.isupper() and name not in TEXT_NAMES]
    problem = _spanish_problem(spanish, english) or next(
        (f"{name} must be text, as the English module's" for name in names if not isinstance(getattr(spanish, name), str) or not isinstance(getattr(module, name, None), str)),
        None,
    )
    if problem is not None:
        raise ValueError(f"level module {spanish.__name__}: {problem}")
    return LevelTexts(
        title=spanish.TITLE,
        briefing=spanish.BRIEFING,
        question=getattr(spanish, "QUESTION", ""),
        placeholder=getattr(spanish, "PLACEHOLDER", ""),
        hints=tuple(spanish.HINTS),
        debrief=spanish.DEBRIEF,
        card=spanish.CARD,
        scene=tuple(getattr(spanish, "SCENE", [])),
        steps=MappingProxyType(dict(getattr(spanish, "STEPS", {}))),
        messages=MappingProxyType({getattr(module, name): getattr(spanish, name) for name in names}),
    )


def _spanish_problem(spanish: ModuleType, english: LevelTexts) -> str | None:
    """
    Check that a level's Spanish module has a text for each of the English ones, and only those.

    Parameters
    ----------
    spanish : ModuleType
        The module ``<module>_es``.
    english : LevelTexts
        The level's English texts.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    texts = {key: getattr(spanish, key, None) for key in ("TITLE", "BRIEFING", "DEBRIEF", "CARD")}
    hints = getattr(spanish, "HINTS", None)
    scene = getattr(spanish, "SCENE", [])
    steps = getattr(spanish, "STEPS", {})
    blank = [key for key, value in texts.items() if not _is_text(value)]
    problem = None
    if blank:
        problem = f"{blank[0]} must be text that is not empty"
    elif _is_text(getattr(spanish, "QUESTION", "")) != bool(english.question) or _is_text(getattr(spanish, "PLACEHOLDER", "")) != bool(english.placeholder):
        problem = "QUESTION and PLACEHOLDER must be there exactly when the English module has them"
    elif not isinstance(hints, list) or len(hints) != len(english.hints) or not all(_is_text(hint) for hint in hints):
        problem = f"HINTS must be {len(english.hints)} texts, one per English hint"
    elif not isinstance(scene, list) or len(scene) != len(english.scene) or not all(_is_text(text) for text in scene):
        problem = f"SCENE must be {len(english.scene)} texts, one per scene frame"
    elif not isinstance(steps, dict) or set(steps) != set(english.steps) or not all(isinstance(text, kit.StepText) for text in steps.values()):
        problem = f"STEPS must give a kit.StepText for each quest step: {', '.join(english.steps) or 'none'}"
    else:
        problem = next((found for step_id, text in steps.items() if (found := _step_text_problem(step_id, text, english.steps[step_id])) is not None), None)
    return problem


def _step_text_problem(step_id: str, text: kit.StepText, english: kit.StepText) -> str | None:
    """
    Check one step's Spanish texts against its English ones: the same fields, and as many options.

    Parameters
    ----------
    step_id : str
        The step's id.
    text : kit.StepText
        Its Spanish texts.
    english : kit.StepText
        Its English texts.

    Returns
    -------
    str | None
        What is wrong, naming the step, or None.
    """
    fields = ("text", "more", "question", "placeholder", "reveal")
    differ = [field for field in fields if _is_text(getattr(text, field)) != _is_text(getattr(english, field))]
    problem = None
    if differ:
        problem = f"STEPS: step {step_id!r} must have its {differ[0]} exactly when the English step has one"
    elif len(text.options) != len(english.options) or not all(_is_text(option) for option in text.options):
        problem = f"STEPS: step {step_id!r} must have {len(english.options)} options"
    return problem


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


def _orbit_problem(values: dict[str, Any]) -> str | None:
    """
    Check the command label, par and card of a level module.

    Parameters
    ----------
    values : dict[str, Any]
        The module's names, None where missing.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    par = values["PAR"]
    card = values["CARD"]
    problem = None
    if not _is_text(values["COMMAND"]):
        problem = "COMMAND must be text that is not empty"
    elif not isinstance(par, int) or isinstance(par, bool) or par <= 0:
        problem = "PAR must be a whole number above zero"
    elif not isinstance(card, kit.CommandCard) or not _is_text(card.command) or not _is_text(card.text):
        problem = "CARD must be a kit.CommandCard whose command and text are not empty"
    return problem


def _scene_problem(scene: Any) -> str | None:
    """
    Check a level's scene: frames, each with a picture the page draws and some text.

    Parameters
    ----------
    scene : Any
        The module's ``SCENE``.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    pictures = typing.get_args(Art)
    problem = None
    if not isinstance(scene, list) or not all(isinstance(frame, kit.SceneFrame) for frame in scene):
        problem = "SCENE must be a list of kit.SceneFrame"
    elif not all(frame.art in pictures and _is_text(frame.text) for frame in scene):
        problem = f"SCENE frames need text and a picture among {', '.join(pictures)}"
    return problem


def _view_problem(view: Any) -> str | None:
    """
    Check a level's main view: one the page draws.

    Parameters
    ----------
    view : Any
        The module's ``VIEW``.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    views = typing.get_args(View)
    return None if view in views else f"VIEW must be one of {', '.join(views)}"


def _reactions_problem(rules: Any) -> str | None:
    """
    Check a level's own reactions: rules whose line is a regular expression, with a known mood and outcome and some text.

    Parameters
    ----------
    rules : Any
        The module's ``REACTIONS``.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    problem = None
    if not isinstance(rules, list) or not all(isinstance(rule, kit.ReactionRule) for rule in rules):
        problem = "REACTIONS must be a list of kit.ReactionRule"
    else:
        problem = next((found for rule in rules if (found := _rule_problem(rule)) is not None), None)
    return problem


def _rule_problem(rule: kit.ReactionRule) -> str | None:
    """
    Check one reaction rule of a level.

    Parameters
    ----------
    rule : kit.ReactionRule
        The rule.

    Returns
    -------
    str | None
        What is wrong, naming the rule's line, or None.
    """
    try:
        re.compile(rule.line)
        pattern = True
    except re.error:
        pattern = False
    problem = None
    if not pattern:
        problem = f"REACTIONS: {rule.line!r} is not a regular expression"
    elif rule.mood not in typing.get_args(Mood) or rule.outcome not in typing.get_args(reactions.Outcome):
        problem = f"REACTIONS: the rule for {rule.line!r} has an unknown mood or outcome"
    elif not _is_text(rule.text):
        problem = f"REACTIONS: the rule for {rule.line!r} needs text"
    return problem


def _quest_problem(quest: Any) -> str | None:
    """
    Check a level's quest: a list of steps, each of one kind (answer, watch, read or choice).

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
        return "QUEST must be a list of kit.AnswerStep, kit.WatchStep, kit.ReadStep and kit.ChoiceStep"
    marked = [step.id for step in quest if isinstance(step, kit.AnswerStep) and "`" in step.placeholder]
    choices = [step for step in quest if isinstance(step, kit.ChoiceStep)]
    problem = _duplicate_problem("step", [step.id for step in quest])
    if problem is None and marked:
        problem = f"step {marked[0]!r}: its placeholder is plain text: no backticks"
    if problem is None:
        problem = next((found for step in choices if (found := _choice_problem(step)) is not None), None)
    return problem


def _challenge_problem(challenge: Any, quest: list[kit.Step]) -> str | None:
    """
    Check a level's challenge flag: a boolean, and for a challenge a quest of goals to watch only.

    Parameters
    ----------
    challenge : Any
        The module's ``CHALLENGE``.
    quest : list[kit.Step]
        The module's quest, already checked.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    problem = None
    if not isinstance(challenge, bool):
        problem = "CHALLENGE must be True or False"
    elif challenge and not all(isinstance(step, kit.WatchStep) for step in quest):
        problem = "CHALLENGE: a challenge's quest holds only goals to watch (kit.WatchStep), met in any order"
    return problem


def _choice_problem(step: kit.ChoiceStep) -> str | None:
    """
    Check a prediction: two or three different options that are not blank, and a reveal.

    Parameters
    ----------
    step : kit.ChoiceStep
        The step.

    Returns
    -------
    str | None
        What is wrong, naming the step, or None.
    """
    options = step.options
    problem = None
    if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS or len(set(options)) != len(options) or not all(_is_text(option) for option in options):
        problem = f"step {step.id!r}: a choice step needs {MIN_OPTIONS} to {MAX_OPTIONS} different options that are not blank"
    elif not _is_text(step.reveal):
        problem = f"step {step.id!r}: a choice step needs a reveal, said whichever option is chosen"
    return problem


def _events_problem(events: Any, quest: list[kit.Step]) -> str | None:
    """
    Check a level's events: each with its own id, a function to run, and no goal or one of the quest's step ids.

    Parameters
    ----------
    events : Any
        The module's ``EVENTS``.
    quest : list[kit.Step]
        The module's quest, already checked.

    Returns
    -------
    str | None
        What is wrong, or None.
    """
    goals = {"", *(step.id for step in quest)}
    problem = None
    if not isinstance(events, list) or not all(isinstance(event, kit.LevelEvent) for event in events):
        problem = "EVENTS must be a list of kit.LevelEvent"
    elif not all(callable(event.run) for event in events):
        problem = "EVENTS: each event's run must be a function"
    elif any(event.goal not in goals for event in events):
        problem = "EVENTS: an event's goal must be empty or the id of a quest step"
    else:
        problem = _duplicate_problem("EVENTS: event", [event.id for event in events])
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

    Modules whose name starts with ``_`` are helpers and are not imported here; a module ending in
    ``_es`` is the Spanish texts of the level it names, read with it.

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
    names = {info.name for info in pkgutil.iter_modules(package.__path__) if not info.name.startswith("_")}
    found = [
        load(importlib.import_module(f"{package.__name__}.{name}"), _spanish_module(package, name, names))
        for name in sorted(names)
        if not name.endswith(SPANISH_SUFFIX)
    ]
    found.sort(key=lambda level: (order.index(level.chapter), level.difficulty, level.id))
    return {level.id: level for level in found}


def _spanish_module(package: ModuleType, name: str, names: set[str]) -> ModuleType | None:
    """
    Import a level's Spanish sibling, if the package has one.

    Parameters
    ----------
    package : ModuleType
        The package of level modules.
    name : str
        The level module's name.
    names : set[str]
        Every module name in the package.

    Returns
    -------
    ModuleType | None
        The module ``<name>_es``, or None.
    """
    sibling = name + SPANISH_SUFFIX
    return importlib.import_module(f"{package.__name__}.{sibling}") if sibling in names else None


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

    The game's git configuration is made ready first (`firstcommit.gitcmd.ensure_config`), so
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
    gitcmd.ensure_config()
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
