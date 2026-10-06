"""
The generic level harness of AUTHORING.md section 3.6, run over every level.

The game's own levels are joined by the sample level of ``tests/sample_levels``, so the harness
itself is exercised even before a chapter has levels.
"""

import hashlib
import importlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from termlab import sandbox

import sample_levels
from firstcommit import kit, levels, runner

HOSTILE = [
    "",
    " ",
    "\t\n",
    "\x00",
    "²",
    "٣",
    "-1",
    "0",
    "9" * 5000,
    "word " + "9" * 5000,
    "-",
    "--help",
    "HEAD~999",
    "../../../etc/passwd",
    "$(touch pwned); `touch pwned`",
    "日本語の答え",
    "é" * 20_000,
    "x" * 60_000,
]
PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
QuestAction = Callable[[kit.Lab, kit.State], str | None]

CASES = [(levels, level) for level in runner.catalogue().values()] + [(sample_levels, level) for level in runner.discover(sample_levels).values()]
IDS = [level.id for _, level in CASES]


def module_of(package: ModuleType, level: runner.Level) -> ModuleType:
    """
    Import a level's module.

    Parameters
    ----------
    package : ModuleType
        The package it was discovered in.
    level : runner.Level
        The level.

    Returns
    -------
    ModuleType
        Its module (named after its id, with ``_`` for ``-``).
    """
    return importlib.import_module(f"{package.__name__}.{level.id.replace('-', '_')}")


def quest_actions(package: ModuleType, level: runner.Level) -> dict[str, QuestAction]:
    """
    Read the player's action for each quest step, declared by the level for these tests.

    Parameters
    ----------
    package : ModuleType
        The package the level was discovered in.
    level : runner.Level
        The level.

    Returns
    -------
    dict[str, QuestAction]
        The module's ``QUEST_ACTIONS``, empty when it declares none.
    """
    actions: dict[str, QuestAction] = getattr(module_of(package, level), "QUEST_ACTIONS", {})
    return actions


def tree(root: Path) -> dict[str, str]:
    """
    Fingerprint every file and link under a folder, to tell whether anything changed.

    Parameters
    ----------
    root : Path
        The folder.

    Returns
    -------
    dict[str, str]
        Relative path to a digest of its mode and content (or link target).
    """
    prints = {}
    for path in sorted(root.rglob("*")):
        content = str(path.readlink()).encode() if path.is_symlink() else path.read_bytes() if path.is_file() else b""
        prints[str(path.relative_to(root))] = f"{path.lstat().st_mode:o}:{hashlib.sha256(content).hexdigest()}"
    return prints


def texts(level: runner.Level) -> list[str]:
    """
    List every text of a level that may hold ``{{key}}`` placeholders.

    Parameters
    ----------
    level : runner.Level
        The level.

    Returns
    -------
    list[str]
        Briefing, hints, debrief, and each quest step's text, command, question and placeholder.
    """
    steps = [field for step in level.quest for field in (step.text, step.command, step.question, step.placeholder)]
    return [level.briefing, *level.hints, level.debrief, *steps]


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_the_quest_actions_name_every_step_the_player_must_act_on(package: ModuleType, level: runner.Level) -> None:
    actions = quest_actions(package, level)
    acting = {step.id for step in level.quest if step.check is not None or step.watch is not None}
    assert set(actions) <= {step.id for step in level.quest}
    assert acting <= set(actions)
    assert all(callable(action) for action in actions.values())


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_setup_gives_a_json_state_that_fills_every_placeholder(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    json.dumps(state)
    missing = {key for text in texts(level) for key in PLACEHOLDER.findall(text)} - set(state)
    assert not missing, f"no state for the placeholders {sorted(missing)}"


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_before_solving_a_check_fails_with_no_answer_and_any_wrong_one_and_changes_nothing(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    before = tree(lab.root)
    for answer in [None, *HOSTILE]:
        verdict = level.check(lab, state, answer)
        assert isinstance(verdict, kit.Verdict) and isinstance(verdict.message, str)
        assert not verdict.solved, f"solved with {answer!r:.40}"
    assert tree(lab.root) == before


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_hostile_answers_never_crash_or_pass_a_quest_step(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    for step in level.quest:
        if step.check is not None:
            verdicts = [step.check(lab, state, answer) for answer in HOSTILE]
            assert all(isinstance(verdict, kit.Verdict) and not verdict.solved for verdict in verdicts), step.id


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_each_quest_step_passes_only_after_the_players_action(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    actions = quest_actions(package, level)
    for step in level.quest:
        if step.watch is not None:
            assert not step.watch(lab, state).solved, f"step {step.id} passed before the player acted"
        answer = actions[step.id](lab, state) if step.id in actions else None
        if step.watch is not None:
            assert step.watch(lab, state).solved, f"step {step.id} did not pass after the player acted"
        if step.check is not None:
            assert not step.check(lab, state, "").solved, f"step {step.id} passed with an empty answer"
            assert answer is not None and step.check(lab, state, answer).solved, f"step {step.id} refused the player's answer {answer!r}"


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_the_reference_solution_solves_the_level_and_the_lab_is_removed_afterwards(package: ModuleType, level: runner.Level, game_home: Path) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    answer = level.solve(lab, state)
    assert level.check(lab, state, answer).solved
    runner.remove_labs()
    assert not (game_home / "labs").exists()


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
@pytest.mark.parametrize("wreck", ["the .git folder", "the project folder"])
def test_checks_survive_a_lab_the_player_wrecked(package: ModuleType, level: runner.Level, wreck: str, game_home: Path) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    sandbox.remove_tree(lab.project / ".git" if wreck == "the .git folder" else lab.project, game_home)
    verdicts = [level.check(lab, state, None), level.check(lab, state, "x")]
    verdicts += [step.watch(lab, state) for step in level.quest if step.watch is not None]
    verdicts += [step.check(lab, state, "x") for step in level.quest if step.check is not None]
    assert all(isinstance(verdict, kit.Verdict) for verdict in verdicts)
