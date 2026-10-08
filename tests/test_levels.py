"""
The generic level harness of AUTHORING.md section 3.6, run over every level.

The game's own levels are joined by the sample level of ``tests/sample_levels``, so the harness
itself is exercised even before a chapter has levels.
"""

import hashlib
import json
import re
from pathlib import Path
from types import ModuleType

import pytest
from termlab import sandbox

import sample_levels
from firstcommit import game, kit, levels, runner
from game_words import unpaired

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
HOSTILE_LINES: list[kit.Command] = [{"line": line, "status": status} for line in HOSTILE for status in (0, 1, 127)]

CASES = [(levels, level) for level in runner.catalogue().values()] + [(sample_levels, level) for level in runner.discover(sample_levels).values()]
IDS = [level.id for _, level in CASES]


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
    actions = level.actions
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
    actions = level.actions
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
    actions = level.actions
    commands = game.solution_lines(level, state)
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


def command_shape(line: str) -> str | None:
    """
    Give the shape of a git line a hint shows: its subcommand and its options, its names left out.

    ``HEAD~2`` and ``HEAD@{3}`` keep their kind with the number made ``n``, and ``origin`` stays, so
    ``git push -u origin scout`` and ``git push -u origin main`` are one shape.

    Parameters
    ----------
    line : str
        A line after ``$ ``, perhaps with a comment.

    Returns
    -------
    str | None
        The shape, or None when the line is not a git command.
    """
    words = line.split("#")[0].split()
    shape = None
    if words[:1] == ["git"] and len(words) > 1:
        kept = [word for word in words[2:] if word.startswith(("-", "HEAD")) or word == "origin"]
        shape = " ".join([words[1], *(re.sub(r"\{\d+\}", "{n}", re.sub(r"~\d+", "~n", word)) for word in kept)])
    return shape


def test_a_challenge_only_asks_for_commands_an_earlier_guided_level_taught() -> None:
    taught: set[str] = set()
    untaught = {}
    for level in runner.catalogue().values():
        shapes = {shape for shape in map(command_shape, game.SHOWN_LINE.findall(level.texts["en"].hints[-1])) if shape}
        if level.challenge and shapes - taught:
            untaught[level.id] = sorted(shapes - taught)
        if not level.challenge:
            taught |= shapes
    assert untaught == {}


def test_a_commands_shape_keeps_its_options_and_drops_its_names() -> None:
    assert command_shape("git push -u origin scout") == command_shape("git push -u origin main") == "push -u origin"
    assert command_shape("git reset --hard HEAD@{2}   # back") == "reset --hard HEAD@{n}"
    assert command_shape("git revert HEAD~1") == "revert HEAD~n"
    assert (command_shape("ls"), command_shape("cd project && git log")) == (None, None)


def every_text(level: runner.Level, language: str) -> str:
    """
    Join every text a player reads in a level, in one language.

    Parameters
    ----------
    level : runner.Level
        The level.
    language : str
        ``"en"`` or ``"es"``.

    Returns
    -------
    str
        Title, card, scene, briefing, question, steps, hints, debrief and messages.
    """
    text = level.texts[language]  # type: ignore[index]
    steps = [field for step in text.steps.values() for field in (step.text, step.more, step.question, step.reveal, *step.options)]
    messages = list(level.texts["es"].messages.values() if language == "es" else level.texts["es"].messages)
    return "\n".join([text.title, text.card, *text.scene, text.briefing, text.question, *steps, *text.hints, text.debrief, *messages])


@pytest.mark.parametrize("level", runner.catalogue().values(), ids=lambda level: level.id)
@pytest.mark.parametrize("language", ["en", "es"])
def test_a_level_that_uses_a_game_word_says_once_what_it_really_is(level: runner.Level, language: str) -> None:
    assert unpaired(every_text(level, language), language) == []


def test_every_level_that_asks_its_own_question_says_how_to_read_the_answer() -> None:
    asking = [level.id for level in runner.catalogue().values() if level.texts["en"].question]
    assert asking and all(runner.catalogue()[level_id].answer is not None for level_id in asking)


def test_the_name_tags_levels_draw_the_chain() -> None:
    drawn = {level.id: level.pictures["large"] for level in runner.catalogue().values() if level.chapter == "names" and level.pictures is not None}
    assert drawn == {"names-tags": "chain", "names-any": "chain", "names-experiments": "chain", "names-step": "chain", "names-chart": "chain"}


@pytest.mark.parametrize("level", [level for level in runner.catalogue().values() if any(step.look for step in level.quest)], ids=lambda level: level.id)
def test_a_steps_look_names_head_or_a_commit_its_lab_holds_once_solved(level: runner.Level, game_home: Path) -> None:
    state = runner.start_lab(level)
    level.solve(runner.lab_of(level.id), state, [])
    subjects = set(kit.git(runner.lab_of(level.id).project, "log", "--all", "--format=%s").splitlines())
    assert {subject for step in level.quest for subject in step.look} <= subjects | {"HEAD"}


def test_each_level_opens_on_the_main_view_of_the_plan() -> None:
    views = {level.id: level.view for level in runner.catalogue().values() if level.view != "station"}
    assert views == {
        "mothership-halves": "crew",
        "mothership-incoming": "crew",
        "mothership-refused": "crew",
        "mothership-recruit": "history",
        "branch-send": "history",
        "branch-ticket": "history",
        "conflict-meet": "history",
        "conflict-collision": "sides",
        "conflict-docking": "history",
    }
