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
SHOWN_COMMAND = re.compile(r"^ *\$ (.+)$", re.MULTILINE)
QuestAction = Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]
HOSTILE_LINES: list[kit.Command] = [{"line": line, "status": status} for line in HOSTILE for status in (0, 1, 127)]

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
    List every text of a level that may hold ``{{key}}`` placeholders, in every language.

    Parameters
    ----------
    level : runner.Level
        The level.

    Returns
    -------
    list[str]
        Briefing, question, placeholder, hints, debrief, each quest step's command, and each
        step's text, more, question and placeholder.
    """
    found = [step.command for step in level.quest]
    for text in level.texts.values():
        steps = [field for step in text.steps.values() for field in (step.text, step.more, step.question, step.placeholder)]
        found += [text.briefing, text.question, text.placeholder, *text.hints, text.debrief, *steps]
    return found


def fire(level: runner.Level, lab: kit.Lab, state: kit.State, goal: str) -> None:
    """
    Run a level's events for a moment of the play, as the game does.

    Parameters
    ----------
    level : runner.Level
        The level.
    lab : kit.Lab
        Its lab.
    state : kit.State
        Its state.
    goal : str
        Empty for right after the first look at the lab, else the goal just reached.
    """
    for event in level.events:
        if event.goal == goal:
            event.run(lab, state)


def assert_spoken(level: runner.Level, verdicts: list[kit.Verdict]) -> None:
    """
    Check that every message a level gave has its Spanish.

    Parameters
    ----------
    level : runner.Level
        The level.
    verdicts : list[kit.Verdict]
        What its checks and watches answered.
    """
    unspoken = {verdict.message for verdict in verdicts if verdict.message} - set(level.texts["es"].messages)
    assert not unspoken, f"no Spanish for {sorted(unspoken)}"


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_the_quest_actions_name_every_step_the_player_must_act_on(package: ModuleType, level: runner.Level) -> None:
    actions = quest_actions(package, level)
    acting = {step.id for step in level.quest if not isinstance(step, kit.ReadStep)}
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
    verdicts = []
    for answer in [None, *HOSTILE]:
        verdict = level.check(lab, state, answer, [])
        assert isinstance(verdict, kit.Verdict) and isinstance(verdict.message, str)
        assert not verdict.solved, f"solved with {answer!r:.40}"
        verdicts.append(verdict)
    assert tree(lab.root) == before
    assert_spoken(level, verdicts)


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_hostile_typed_lines_never_crash_a_check_or_a_watch_or_solve_the_level(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    verdicts = [level.check(lab, state, None, HOSTILE_LINES)]
    verdicts += [step.watch(lab, state, HOSTILE_LINES) for step in level.quest if isinstance(step, kit.WatchStep)]
    assert all(isinstance(verdict, kit.Verdict) for verdict in verdicts)
    assert not verdicts[0].solved
    assert_spoken(level, verdicts)


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_hostile_answers_never_crash_or_pass_a_quest_step(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    for step in level.quest:
        if isinstance(step, kit.AnswerStep):
            verdicts = [step.check(lab, state, answer) for answer in HOSTILE]
            assert all(isinstance(verdict, kit.Verdict) and not verdict.solved for verdict in verdicts), step.id
            assert_spoken(level, verdicts)
        if isinstance(step, kit.ChoiceStep):
            assert not any(kit.choose(step, answer).solved for answer in HOSTILE if answer not in step.options), step.id


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_each_quest_step_passes_only_after_the_players_action(package: ModuleType, level: runner.Level) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    actions = quest_actions(package, level)
    typed: list[kit.Command] = []
    verdicts = []
    fire(level, lab, state, "")
    for step in level.quest:
        if isinstance(step, kit.WatchStep):
            verdicts.append(step.watch(lab, state, typed))
            assert not verdicts[-1].solved, f"step {step.id} passed before the player acted"
        answer = actions[step.id](lab, state, typed) if step.id in actions else None
        if isinstance(step, kit.WatchStep):
            verdicts.append(step.watch(lab, state, typed))
            assert verdicts[-1].solved, f"step {step.id} did not pass after the player acted"
        if isinstance(step, kit.ChoiceStep):
            assert answer in step.options and all(kit.choose(step, option).solved for option in step.options), f"step {step.id} refused an option"
        if isinstance(step, kit.AnswerStep):
            assert not step.check(lab, state, "").solved, f"step {step.id} passed with an empty answer"
            assert answer is not None and step.check(lab, state, answer).solved, f"step {step.id} refused the player's answer {answer!r}"
            verdicts += [step.check(lab, state, ""), step.check(lab, state, answer)]
        fire(level, lab, state, step.id)
    verdicts.append(level.check(lab, state, None, typed))
    assert_spoken(level, verdicts)


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_the_reference_solution_solves_the_level_and_the_lab_is_removed_afterwards(package: ModuleType, level: runner.Level, game_home: Path) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    typed: list[kit.Command] = []
    fire(level, lab, state, "")
    answer = level.solve(lab, state, typed)
    assert (answer is not None) == bool(level.texts["en"].question), "solve returns an answer exactly when the level asks a QUESTION"
    verdict = level.check(lab, state, answer, typed)
    assert verdict.solved
    assert_spoken(level, [verdict])
    runner.remove_labs()
    assert not (game_home / "labs").exists()


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
@pytest.mark.parametrize("wreck", ["the .git folder", "the project folder"])
def test_checks_survive_a_lab_the_player_wrecked(package: ModuleType, level: runner.Level, wreck: str, game_home: Path) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    sandbox.remove_tree(lab.project / ".git" if wreck == "the .git folder" else lab.project, game_home)
    verdicts = [level.check(lab, state, None, []), level.check(lab, state, "x", [])]
    verdicts += [step.watch(lab, state, []) for step in level.quest if isinstance(step, kit.WatchStep)]
    verdicts += [step.check(lab, state, "x") for step in level.quest if isinstance(step, kit.AnswerStep)]
    assert all(isinstance(verdict, kit.Verdict) for verdict in verdicts)
    assert_spoken(level, verdicts)


@pytest.mark.parametrize(("package", "level"), CASES, ids=IDS)
def test_every_reaction_of_a_level_has_its_spanish(package: ModuleType, level: runner.Level) -> None:
    assert_spoken(level, [kit.Verdict(False, rule.text) for rule in level.reactions])


def shown_commands(level: runner.Level, state: kit.State) -> list[str]:
    """
    Read the commands a level's last hint shows, its placeholders filled as the page fills them.

    Parameters
    ----------
    level : runner.Level
        The level.
    state : kit.State
        Its state.

    Returns
    -------
    list[str]
        Each ``$ `` line of the last English hint, without the ``$ ``.
    """
    hint = PLACEHOLDER.sub(lambda match: str(state[match[1]]), level.texts["en"].hints[-1])
    return SHOWN_COMMAND.findall(hint)


def type_in_one_shell(lab: kit.Lab, folder: Path, line: str) -> tuple[kit.Command, Path]:
    """
    Type a line in a terminal that is in a folder, and tell where the terminal is afterwards.

    Parameters
    ----------
    lab : kit.Lab
        The lab, for a scratch file outside the player's folders.
    folder : Path
        Where the terminal is.
    line : str
        The line.

    Returns
    -------
    tuple[kit.Command, Path]
        The line as typed with its status, and the terminal's folder after it (a ``cd`` moves it).
    """
    where = lab.root.parent / f"{lab.root.name}.cwd"
    ran = kit.type_line(folder, f'{line}\nstatus=$?; pwd > "{where}"; exit $status')
    after = Path(where.read_text().strip())
    where.unlink()
    return {"line": line, "status": ran["status"]}, after


@pytest.mark.parametrize("level", list(runner.catalogue().values()), ids=list(runner.catalogue()))
def test_the_last_hint_shows_commands_that_solve_the_level_typed_as_written(level: runner.Level, game_home: Path) -> None:
    state = runner.start_lab(level)
    lab = runner.lab_of(level.id)
    fire(level, lab, state, "")
    actions = quest_actions(levels, level)
    commands = shown_commands(level, state)
    assert commands, "the last hint shows the commands that solve the level, each on a `$ ` line"
    typed: list[kit.Command] = []
    folder = lab.project if lab.project.is_dir() else lab.root
    done: list[str] = []

    def advance() -> None:
        for step in level.quest:
            if step.id in done or (not level.challenge and len(done) < level.quest.index(step)):
                continue
            answer = actions[step.id](lab, state, []) if not isinstance(step, kit.WatchStep) else None
            verdict = step.watch(lab, state, typed) if isinstance(step, kit.WatchStep) else kit.Verdict(True, "")
            if isinstance(step, kit.AnswerStep):
                verdict = step.check(lab, state, answer or "")
            if verdict.solved:
                done.append(step.id)
                fire(level, lab, state, step.id)

    advance()
    for line in commands:
        command, folder = type_in_one_shell(lab, folder, line)
        typed.append(command)
        advance()
    answer = level.solve(lab, state, []) if level.texts["en"].question else None
    assert done == [step.id for step in level.quest] or (level.challenge and sorted(done) == sorted(step.id for step in level.quest))
    assert level.check(lab, state, answer, typed).solved


def test_each_level_opens_on_the_main_view_of_the_plan() -> None:
    views = {level.id: level.view for level in runner.catalogue().values() if level.view != "station"}
    assert views == {
        "mothership-halves": "crew",
        "mothership-incoming": "crew",
        "mothership-refused": "crew",
        "branch-recruit": "history",
        "branch-course": "history",
        "branch-send": "history",
        "branch-switch": "history",
        "branch-ticket": "history",
        "conflict-meet": "history",
        "conflict-abort": "history",
        "conflict-collision": "sides",
        "conflict-docking": "history",
        "undo-blackbox": "blackbox",
        "undo-recall": "history",
        "undo-scrap": "blackbox",
        "undo-wrong": "history",
    }
