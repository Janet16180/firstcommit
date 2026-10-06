import dataclasses
import importlib
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from firstcommit import gitcmd, kit, runner
from sample_levels import basics_sample

CONTRACT = ["TITLE", "DIFFICULTY", "XP", "LESSON", "QUEST", "BRIEFING", "HINTS", "DEBRIEF", "setup", "check", "solve"]


def level_module(name: str = "basics_sample", **changes: Any) -> types.ModuleType:
    """
    Make a level module from the sample level, with some names changed (or removed when given ``...``).

    Parameters
    ----------
    name : str
        The module's own name, inside a package.
    **changes : Any
        Names to set, or ``...`` to leave out.

    Returns
    -------
    types.ModuleType
        The module.
    """
    module = types.ModuleType(f"sample_levels.{name}")
    for key in CONTRACT:
        setattr(module, key, getattr(basics_sample, key))
    for key, value in changes.items():
        if value is ...:
            delattr(module, key)
        else:
            setattr(module, key, value)
    return module


def test_a_level_module_is_read_into_a_typed_record() -> None:
    level = runner.load(basics_sample)
    assert (level.id, level.chapter, level.title, level.difficulty, level.xp) == ("basics-sample", "basics", "Say hello", 1, 100)
    assert level.lesson == tuple(basics_sample.LESSON)
    assert level.quest == tuple(basics_sample.QUEST)
    assert level.hints == tuple(basics_sample.HINTS)
    assert (level.briefing, level.debrief) == (basics_sample.BRIEFING, basics_sample.DEBRIEF)
    assert (level.setup, level.check, level.solve) == (basics_sample.setup, basics_sample.check, basics_sample.solve)
    assert (level.question, level.placeholder) == ("", "")


def test_a_level_solved_by_a_typed_answer_reads_its_question_and_placeholder() -> None:
    level = runner.load(level_module(QUESTION="Which commit broke it?", PLACEHOLDER="a short hash"))
    assert (level.question, level.placeholder) == ("Which commit broke it?", "a short hash")


def test_a_level_record_cannot_be_changed() -> None:
    level = runner.load(basics_sample)
    with pytest.raises(dataclasses.FrozenInstanceError):
        level.xp = 1_000_000  # type: ignore[misc]


def test_a_level_without_a_lesson_or_a_quest_has_empty_ones() -> None:
    level = runner.load(level_module(LESSON=..., QUEST=...))
    assert (level.lesson, level.quest) == ((), ())


def step(step_id: str, **fields: Any) -> kit.Step:
    """
    Make a quest step.

    Parameters
    ----------
    step_id : str
        Its id.
    **fields : Any
        Other fields of `kit.Step`.

    Returns
    -------
    kit.Step
        The step.
    """
    return kit.Step(id=step_id, text="Do it.", **fields)


BROKEN: dict[str, tuple[types.ModuleType, str]] = {
    "an unknown chapter": (level_module("nowhere_sample"), "chapter"),
    "a name without a slug": (level_module("basics"), "chapter"),
    "a missing title": (level_module(TITLE=...), "TITLE"),
    "an empty title": (level_module(TITLE=" "), "TITLE"),
    "a difficulty of 4": (level_module(DIFFICULTY=4), "DIFFICULTY"),
    "a difficulty that is a boolean": (level_module(DIFFICULTY=True), "DIFFICULTY"),
    "no XP": (level_module(XP=0), "XP"),
    "XP as text": (level_module(XP="100"), "XP"),
    "a missing briefing": (level_module(BRIEFING=...), "BRIEFING"),
    "a debrief that is not text": (level_module(DEBRIEF=["x"]), "DEBRIEF"),
    "one hint": (level_module(HINTS=["only"]), "HINTS"),
    "five hints": (level_module(HINTS=["a", "b", "c", "d", "e"]), "HINTS"),
    "an empty hint": (level_module(HINTS=["a", ""]), "HINTS"),
    "a lesson of strings": (level_module(LESSON=["slide"]), "LESSON"),
    "two slides with one id": (level_module(LESSON=[basics_sample.LESSON[0]] * 2), "init"),
    "a quest that is not a list": (level_module(QUEST=step("a")), "QUEST"),
    "two steps with one id": (level_module(QUEST=[step("a"), step("a")]), "a"),
    "a question without a check": (level_module(QUEST=[step("a", question="Which?")]), "a"),
    "a check without a question": (level_module(QUEST=[step("a", check=basics_sample.names_the_branch)]), "a"),
    "a step with a check and a watch": (level_module(QUEST=[step("a", question="Q?", check=basics_sample.names_the_branch, watch=basics_sample.is_staged)]), "a"),
    "a setup that is not a function": (level_module(setup="setup"), "setup"),
    "a missing check": (level_module(check=...), "check"),
    "a question that is not text": (level_module(QUESTION=3), "QUESTION"),
    "a placeholder that is not text": (level_module(QUESTION="Which?", PLACEHOLDER=None), "PLACEHOLDER"),
    "a placeholder without a question": (level_module(PLACEHOLDER="a short hash"), "PLACEHOLDER"),
}


@pytest.mark.parametrize("case", BROKEN.values(), ids=list(BROKEN))
def test_a_broken_level_module_is_a_bug_named_after_its_module(case: tuple[types.ModuleType, str]) -> None:
    module, problem = case
    with pytest.raises(ValueError, match=rf"{module.__name__}.*{problem}"):
        runner.load(module)


@pytest.fixture
def level_package(tmp_path: Path) -> Iterator[types.ModuleType]:
    """
    Make an importable package of minimal level modules, plus a helper module.

    Parameters
    ----------
    tmp_path : Path
        Where to write it.

    Yields
    ------
    types.ModuleType
        The imported package; it is forgotten afterwards.
    """
    package = tmp_path / "fakelevels"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "_shared.py").write_text("raise RuntimeError('a helper is not a level')\n")
    for name, difficulty in [("basics_b", 2), ("basics_a", 2), ("start_z", 3), ("basics_c", 1)]:
        (package / f"{name}.py").write_text(f"from sample_levels.basics_sample import *\nDIFFICULTY = {difficulty}\n")
    sys.path.insert(0, str(tmp_path))
    yield importlib.import_module("fakelevels")
    sys.path.remove(str(tmp_path))
    for module in [name for name in sys.modules if name.split(".")[0] == "fakelevels"]:
        del sys.modules[module]


def test_levels_are_found_in_chapter_then_difficulty_then_id_order_without_helpers(level_package: types.ModuleType) -> None:
    assert list(runner.discover(level_package)) == ["start-z", "basics-c", "basics-a", "basics-b"]


def test_the_catalogue_is_read_once() -> None:
    assert runner.catalogue() is runner.catalogue()


def test_the_catalogue_holds_the_games_own_levels() -> None:
    assert all(level_id == level.id for level_id, level in runner.catalogue().items())


def test_a_lab_lives_under_the_game_home(game_home: Path) -> None:
    assert runner.lab_of("basics-sample") == kit.Lab(game_home / "labs" / "basics-sample")


def test_starting_a_lab_runs_setup_in_an_empty_folder(game_home: Path) -> None:
    leftover = game_home / "labs" / "basics-sample" / "left-from-before.txt"
    leftover.parent.mkdir(parents=True)
    leftover.write_text("old\n")
    state = runner.start_lab(runner.load(basics_sample))
    assert state == {"branch": "trunk"}
    assert sorted(path.name for path in (game_home / "labs" / "basics-sample").iterdir()) == ["project"]
    assert (game_home / "labs" / "basics-sample" / "project" / "hello.txt").read_text() == "hello\n"


def test_starting_a_lab_removes_every_other_lab(game_home: Path) -> None:
    other = game_home / "labs" / "other-level" / "project"
    other.mkdir(parents=True)
    other.chmod(0o500)
    (game_home / "labs" / "stray.txt").write_text("x")
    runner.start_lab(runner.load(basics_sample))
    assert [path.name for path in (game_home / "labs").iterdir()] == ["basics-sample"]


def plain_init(lab: kit.Lab) -> kit.State:
    """
    Set up a level the way a player starts: a plain ``git init``, with no branch named.

    Parameters
    ----------
    lab : kit.Lab
        The empty lab.

    Returns
    -------
    kit.State
        No state.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    return {}


def test_a_lab_starts_from_the_games_git_config_so_a_plain_init_is_on_main(game_home: Path) -> None:
    runner.start_lab(dataclasses.replace(runner.load(basics_sample), setup=plain_init))
    assert (game_home / "gitconfig").read_text() == gitcmd.BASE_CONFIG
    assert kit.git(runner.lab_of("basics-sample").project, "symbolic-ref", "--short", "HEAD") == "main\n"


def test_starting_a_lab_keeps_the_game_git_config_the_player_changed(game_home: Path) -> None:
    (game_home / "gitconfig").write_text("[user]\n\tname = Ada\n")
    runner.start_lab(runner.load(basics_sample))
    assert (game_home / "gitconfig").read_text() == "[user]\n\tname = Ada\n"


def test_a_failed_setup_leaves_no_lab_and_raises(game_home: Path) -> None:
    def broken_setup(lab: kit.Lab) -> kit.State:
        (lab.root / "half-built").write_text("x")
        raise RuntimeError("setup broke")

    with pytest.raises(RuntimeError, match="setup broke"):
        runner.start_lab(dataclasses.replace(runner.load(basics_sample), setup=broken_setup))
    assert not (game_home / "labs" / "basics-sample").exists()


def test_a_setup_that_returns_no_state_is_a_bug_and_leaves_no_lab(game_home: Path) -> None:
    def forgetful_setup(lab: kit.Lab) -> kit.State:
        return None  # type: ignore[return-value]

    with pytest.raises(ValueError, match="basics-sample.*setup"):
        runner.start_lab(dataclasses.replace(runner.load(basics_sample), setup=forgetful_setup))
    assert not (game_home / "labs" / "basics-sample").exists()


def test_removing_the_labs_deletes_them_all_and_tolerates_none(game_home: Path) -> None:
    runner.start_lab(runner.load(basics_sample))
    runner.remove_labs()
    runner.remove_labs()
    assert not (game_home / "labs").exists()
