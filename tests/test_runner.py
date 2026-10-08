import dataclasses
import importlib
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from firstcommit import gitcmd, kit, records, runner
from sample_levels import cargo_sample, cargo_sample_es

SPANISH = ["TITLE", "BRIEFING", "HINTS", "DEBRIEF", "CARD", "SCENE", "STEPS", "HELLO_STAGED", "STAGED", "NOT_STAGED", "RIGHT", "LOOK", "COMMITTED", "NOT_COMMITTED"]
CONTRACT = ["TITLE", "DIFFICULTY", "XP", "COMMAND", "PAR", "CARD", "SCENE", "QUEST", "BRIEFING", "HINTS", "DEBRIEF", "REACTIONS", "setup", "check", "solve"]


def level_module(name: str = "cargo_sample", **changes: Any) -> types.ModuleType:
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
        setattr(module, key, getattr(cargo_sample, key))
    for key, value in changes.items():
        if value is ...:
            delattr(module, key)
        else:
            setattr(module, key, value)
    return module


def spanish_module(**changes: Any) -> types.ModuleType:
    """
    Make the Spanish sibling of a level module from the sample's, with some names changed (or removed when given ``...``).

    Parameters
    ----------
    **changes : Any
        Names to set, or ``...`` to leave out.

    Returns
    -------
    types.ModuleType
        The module.
    """
    module = types.ModuleType("sample_levels.cargo_sample_es")
    for key in SPANISH:
        setattr(module, key, getattr(cargo_sample_es, key))
    for key, value in changes.items():
        if value is ...:
            delattr(module, key)
        else:
            setattr(module, key, value)
    return module


def test_a_level_reads_its_texts_in_english_and_in_spanish_from_its_sibling() -> None:
    level = runner.load(cargo_sample, cargo_sample_es)
    english, spanish = level.texts["en"], level.texts["es"]
    assert (english.title, english.card, english.hints) == ("Say hello", cargo_sample.CARD.text, tuple(cargo_sample.HINTS))
    assert (spanish.title, spanish.briefing, spanish.card) == ("Di hola", cargo_sample_es.BRIEFING, cargo_sample_es.CARD)
    assert spanish.scene == tuple(cargo_sample_es.SCENE)
    assert spanish.steps["branch"] == kit.StepText(text="Encuentra el branch.", question="¿Qué branch es `{{branch}}`?", placeholder="un nombre de branch")
    assert english.steps["branch"] == kit.StepText(text="Find the branch.", question="Which branch is `{{branch}}`?", placeholder="a branch name")
    assert spanish.messages[cargo_sample.LOOK] == cargo_sample_es.LOOK
    assert spanish.messages[cargo_sample.HELLO_STAGED] == cargo_sample_es.HELLO_STAGED
    assert english.messages == {}


def test_without_a_spanish_sibling_a_level_shows_its_english_texts() -> None:
    level = runner.load(cargo_sample)
    assert level.texts["es"] == dataclasses.replace(level.texts["en"])


def test_a_level_module_is_read_into_a_typed_record() -> None:
    level = runner.load(cargo_sample)
    english = level.texts["en"]
    assert (level.id, level.chapter, english.title, level.difficulty, level.xp) == ("cargo-sample", "cargo", "Say hello", 1, 100)
    assert level.quest == tuple(cargo_sample.QUEST)
    assert english.hints == tuple(cargo_sample.HINTS)
    assert (english.briefing, english.debrief) == (cargo_sample.BRIEFING, cargo_sample.DEBRIEF)
    assert (level.setup, level.check, level.solve) == (cargo_sample.setup, cargo_sample.check, cargo_sample.solve)
    assert (english.question, english.placeholder) == ("", "")
    assert (level.command, level.par, level.card) == ("git add", 3, cargo_sample.CARD)
    assert (level.scene, level.reactions) == (tuple(cargo_sample.SCENE), tuple(cargo_sample.REACTIONS))


def test_a_level_without_a_scene_or_reactions_has_empty_ones() -> None:
    level = runner.load(level_module(SCENE=..., REACTIONS=...))
    assert (level.scene, level.reactions) == ((), ())


def test_a_level_keeps_the_players_actions_it_declares_for_its_tests_and_dev_mode() -> None:
    assert runner.load(level_module()).actions == {}
    actions = {"look": lambda lab, state, typed: None}
    assert runner.load(level_module(QUEST_ACTIONS=actions)).actions == actions


def test_a_level_reads_the_answer_to_its_own_question_only_when_it_declares_how() -> None:
    assert runner.load(level_module()).answer is None
    read = lambda lab, state: "Robin"  # noqa: E731
    assert runner.load(level_module(QUESTION="Who?", ANSWER=read)).answer is read


def test_a_level_shows_the_tape_only_when_it_says_so() -> None:
    assert runner.load(level_module()).tape is False
    assert runner.load(level_module(TAPE=True)).tape is True


def test_a_level_is_played_in_the_view_it_names_and_in_your_station_without_one() -> None:
    assert runner.load(level_module()).view == "station"
    assert runner.load(level_module(VIEW="history")).view == "history"


CHART: records.Target = {
    "commits": [{"id": "a", "parents": [], "subject": "Start"}, {"id": "b", "parents": ["a"], "subject": "Next"}],
    "names": {"main": "b", "old": "a"},
    "head": "main",
}


def test_a_level_names_the_pictures_it_shows_and_its_target_or_none() -> None:
    assert (runner.load(level_module()).pictures, runner.load(level_module()).target) == (None, None)
    pictures = kit.pictures("chain", folder=True, kept="stage", whatif={"without": ["scout"], "after": "branch"})
    level = runner.load(level_module(PICTURES=pictures, TARGET=CHART))
    assert (level.pictures, level.target) == (pictures, CHART)


def test_pictures_start_with_every_mark_off() -> None:
    assert kit.pictures("movelog") == {
        "large": "movelog", "small": None, "folder": False, "mothership": False, "alex": False, "ghosts": False, "kept": None, "lines": [], "graph": False, "whatif": None,
    }


def test_a_step_rings_nothing_unless_it_says_what() -> None:
    assert kit.ReadStep(id="a", text="Read.").look == ()
    assert kit.WatchStep(id="a", text="Do.", watch=cargo_sample.is_staged, look=("HEAD", "Add the map")).look == ("HEAD", "Add the map")


def nothing(lab: kit.Lab, state: kit.State) -> None:
    """
    Do nothing, as a level event's action.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level's state.
    """


def test_a_level_reads_its_events_and_has_none_by_default() -> None:
    events = [kit.LevelEvent(id="arrive", run=nothing), kit.LevelEvent(id="push", run=nothing, goal="stage")]
    assert runner.load(level_module(EVENTS=events)).events == tuple(events)
    assert runner.load(level_module()).events == ()


def test_a_level_solved_by_a_typed_answer_reads_its_question_and_placeholder() -> None:
    level = runner.load(level_module(QUESTION="Which commit broke it?", PLACEHOLDER="a short hash"))
    assert (level.texts["en"].question, level.texts["en"].placeholder) == ("Which commit broke it?", "a short hash")


def test_a_level_record_cannot_be_changed() -> None:
    level = runner.load(cargo_sample)
    with pytest.raises(dataclasses.FrozenInstanceError):
        level.xp = 1_000_000  # type: ignore[misc]


def test_a_level_without_a_quest_has_an_empty_one() -> None:
    level = runner.load(level_module(QUEST=...))
    assert level.quest == ()


def step(step_id: str) -> kit.ReadStep:
    """
    Make a read step.

    Parameters
    ----------
    step_id : str
        Its id.

    Returns
    -------
    kit.ReadStep
        The step.
    """
    return kit.ReadStep(id=step_id, text="Do it.")


BROKEN: dict[str, tuple[types.ModuleType, str]] = {
    "an unknown chapter": (level_module("nowhere_sample"), "chapter"),
    "a name without a slug": (level_module("cargo"), "chapter"),
    "a missing title": (level_module(TITLE=...), "TITLE"),
    "an empty title": (level_module(TITLE=" "), "TITLE"),
    "a difficulty of 4": (level_module(DIFFICULTY=4), "DIFFICULTY"),
    "a difficulty that is a boolean": (level_module(DIFFICULTY=True), "DIFFICULTY"),
    "no XP": (level_module(XP=0), "XP"),
    "XP as text": (level_module(XP="100"), "XP"),
    "a missing briefing": (level_module(BRIEFING=...), "BRIEFING"),
    "a missing command label": (level_module(COMMAND=...), "COMMAND"),
    "a blank command label": (level_module(COMMAND=" "), "COMMAND"),
    "a par of zero": (level_module(PAR=0), "PAR"),
    "a par that is a boolean": (level_module(PAR=True), "PAR"),
    "a missing card": (level_module(CARD=...), "CARD"),
    "a card that is text": (level_module(CARD="git add"), "CARD"),
    "a card without text": (level_module(CARD=kit.CommandCard(command="git add", text=" ")), "CARD"),
    "a scene of strings": (level_module(SCENE=["frame"]), "SCENE"),
    "a scene frame with a picture nobody drew": (level_module(SCENE=[kit.SceneFrame(art="dragon", text="Hi.")]), "SCENE"),  # type: ignore[arg-type]
    "a scene frame without text": (level_module(SCENE=[kit.SceneFrame(art="space", text="")]), "SCENE"),
    "a view nobody drew": (level_module(VIEW="map"), "VIEW"),
    "a tape flag that is not a boolean": (level_module(TAPE="yes"), "TAPE"),
    "pictures that are not pictures": (level_module(PICTURES="chain"), "PICTURES"),
    "a large picture nobody drew": (level_module(PICTURES={**kit.pictures("chain"), "large": "map"}), "PICTURES"),
    "a small picture that cannot be small": (level_module(PICTURES=kit.pictures("chain", small="movelog")), "PICTURES"),  # type: ignore[arg-type]
    "a kept outline on a step the quest does not have": (level_module(PICTURES=kit.pictures("desk", kept="fly")), "PICTURES"),
    "lines of a blank path": (level_module(PICTURES=kit.pictures("desk", lines=[" "])), "PICTURES"),
    "a what-if after a step the quest does not have": (level_module(PICTURES=kit.pictures("chain", whatif={"without": ["scout"], "after": "fly"})), "PICTURES"),
    "a what-if without a name": (level_module(PICTURES=kit.pictures("chain", whatif={"without": [], "after": "stage"})), "PICTURES"),
    "a target name on a commit it does not list": (level_module(TARGET={**CHART, "names": {"main": "z"}}), "TARGET"),
    "a target head that is no name": (level_module(TARGET={**CHART, "head": "scout"}), "TARGET"),
    "a target parent it does not list": (level_module(TARGET={**CHART, "commits": [{"id": "b", "parents": ["a"], "subject": "Next"}]}), "TARGET"),
    "a target that is not a chart": (level_module(TARGET=["main"]), "TARGET"),
    "a step whose look is not text": (level_module(QUEST=[kit.ReadStep(id="a", text="Read.", look=("HEAD", 3))]), "look"),  # type: ignore[arg-type]
    "an answer that is not a function": (level_module(QUESTION="Who?", ANSWER="Robin"), "ANSWER"),
    "an answer with no question": (level_module(ANSWER=lambda lab, state: "Robin"), "ANSWER"),
    "the band, a birth mark and not a view to open on": (level_module(VIEW="band"), "VIEW"),
    "reactions that are not rules": (level_module(REACTIONS=["git add"]), "REACTIONS"),
    "a reaction whose line is not a pattern": (level_module(REACTIONS=[kit.ReactionRule(line="git (add", mood="ok", text="Hi.")]), "REACTIONS"),
    "a reaction with an unknown mood": (level_module(REACTIONS=[kit.ReactionRule(line="git", mood="happy", text="Hi.")]), "REACTIONS"),  # type: ignore[arg-type]
    "a reaction with an unknown outcome": (level_module(REACTIONS=[kit.ReactionRule(line="git", mood="ok", text="Hi.", outcome="won")]), "REACTIONS"),  # type: ignore[arg-type]
    "a reaction without text": (level_module(REACTIONS=[kit.ReactionRule(line="git", mood="ok", text="")]), "REACTIONS"),
    "a choice step with one option": (level_module(QUEST=[kit.ChoiceStep(id="g", text="Guess.", question="Q?", options=("Yes",), reveal="R.")]), "options"),
    "a choice step with four options": (level_module(QUEST=[kit.ChoiceStep(id="g", text="Guess.", question="Q?", options=("a", "b", "c", "d"), reveal="R.")]), "options"),
    "a choice step with an option twice": (level_module(QUEST=[kit.ChoiceStep(id="g", text="Guess.", question="Q?", options=("a", "a"), reveal="R.")]), "options"),
    "a choice step with a blank option": (level_module(QUEST=[kit.ChoiceStep(id="g", text="Guess.", question="Q?", options=("a", " "), reveal="R.")]), "options"),
    "a choice step without a reveal": (level_module(QUEST=[kit.ChoiceStep(id="g", text="Guess.", question="Q?", options=("a", "b"), reveal="")]), "reveal"),
    "a challenge flag that is not a boolean": (level_module(CHALLENGE="yes"), "CHALLENGE"),
    "a challenge with a step that is not a goal to watch": (level_module(CHALLENGE=True), "CHALLENGE"),
    "events that are not level events": (level_module(EVENTS=["push"]), "EVENTS"),
    "two events with one id": (level_module(EVENTS=[kit.LevelEvent(id="a", run=nothing)] * 2), "EVENTS"),
    "an event on a goal the quest does not have": (level_module(EVENTS=[kit.LevelEvent(id="a", run=nothing, goal="fly")]), "EVENTS"),
    "an event whose action is not a function": (level_module(EVENTS=[kit.LevelEvent(id="a", run="push")]), "EVENTS"),  # type: ignore[arg-type]
    "a debrief that is not text": (level_module(DEBRIEF=["x"]), "DEBRIEF"),
    "one hint": (level_module(HINTS=["only"]), "HINTS"),
    "five hints": (level_module(HINTS=["a", "b", "c", "d", "e"]), "HINTS"),
    "an empty hint": (level_module(HINTS=["a", ""]), "HINTS"),
    "a quest that is not a list": (level_module(QUEST=step("a")), "QUEST"),
    "two steps with one id": (level_module(QUEST=[step("a"), step("a")]), "a"),
    "a quest holding a scene frame": (level_module(QUEST=[cargo_sample.SCENE[0]]), "QUEST"),
    "a setup that is not a function": (level_module(setup="setup"), "setup"),
    "a missing check": (level_module(check=...), "check"),
    "a question that is not text": (level_module(QUESTION=3), "QUESTION"),
    "a placeholder that is not text": (level_module(QUESTION="Which?", PLACEHOLDER=None), "PLACEHOLDER"),
    "a placeholder without a question": (level_module(PLACEHOLDER="a short hash"), "PLACEHOLDER"),
    "a placeholder with backticks": (level_module(QUESTION="Which?", PLACEHOLDER="a `short` hash"), "PLACEHOLDER"),
    "a step placeholder with backticks": (
        level_module(QUEST=[kit.AnswerStep(id="a", text="Do it.", question="Q?", placeholder="`main`", check=cargo_sample.names_the_branch)]),
        "a",
    ),
}


BROKEN_SPANISH: dict[str, tuple[types.ModuleType, str]] = {
    "no title": (spanish_module(TITLE=...), "TITLE"),
    "a blank briefing": (spanish_module(BRIEFING=" "), "BRIEFING"),
    "one hint fewer": (spanish_module(HINTS=cargo_sample_es.HINTS[:2]), "HINTS"),
    "no card text": (spanish_module(CARD=...), "CARD"),
    "a scene frame fewer": (spanish_module(SCENE=cargo_sample_es.SCENE[:1]), "SCENE"),
    "a step missing": (spanish_module(STEPS={key: value for key, value in cargo_sample_es.STEPS.items() if key != "stage"}), "STEPS"),
    "a step the quest does not have": (spanish_module(STEPS={**cargo_sample_es.STEPS, "fly": kit.StepText(text="Vuela.")}), "STEPS"),
    "a step without its question": (spanish_module(STEPS={**cargo_sample_es.STEPS, "branch": kit.StepText(text="Encuentra la rama.")}), "branch"),
    "a message the level does not have": (spanish_module(EXTRA="Sobra."), "EXTRA"),
    "a message that is not text": (spanish_module(RIGHT=3), "RIGHT"),
}


@pytest.mark.parametrize("case", BROKEN_SPANISH.values(), ids=list(BROKEN_SPANISH))
def test_a_broken_spanish_sibling_is_a_bug_named_after_its_module(case: tuple[types.ModuleType, str]) -> None:
    spanish, problem = case
    with pytest.raises(ValueError, match=rf"cargo_sample_es.*{problem}"):
        runner.load(cargo_sample, spanish)


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
    for name, difficulty in [("cargo_b", 2), ("cargo_a", 2), ("start_z", 3), ("cargo_c", 1)]:
        (package / f"{name}.py").write_text(f"from sample_levels.cargo_sample import *\nDIFFICULTY = {difficulty}\n")
    (package / "cargo_a_es.py").write_text("from sample_levels.cargo_sample_es import *\n")
    sys.path.insert(0, str(tmp_path))
    yield importlib.import_module("fakelevels")
    sys.path.remove(str(tmp_path))
    for module in [name for name in sys.modules if name.split(".")[0] == "fakelevels"]:
        del sys.modules[module]


def test_levels_are_found_in_chapter_then_difficulty_then_id_order_without_helpers(level_package: types.ModuleType) -> None:
    assert list(runner.discover(level_package)) == ["cargo-c", "cargo-a", "cargo-b", "start-z"]


def test_levels_in_the_play_order_come_in_its_order_before_the_rest_of_their_chapter(level_package: types.ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "PLAY_ORDER", ("cargo-b", "cargo-c"))
    assert list(runner.discover(level_package)) == ["cargo-b", "cargo-c", "cargo-a", "start-z"]


def test_a_spanish_sibling_is_read_with_its_level_and_is_no_level_itself(level_package: types.ModuleType) -> None:
    levels = runner.discover(level_package)
    assert (levels["cargo-a"].texts["es"].title, levels["cargo-b"].texts["es"].title) == ("Di hola", "Say hello")


def test_the_catalogue_is_read_once() -> None:
    assert runner.catalogue() is runner.catalogue()


def test_the_catalogue_holds_the_games_own_levels() -> None:
    assert all(level_id == level.id for level_id, level in runner.catalogue().items())


def test_a_lab_lives_under_the_game_home(game_home: Path) -> None:
    assert runner.lab_of("cargo-sample") == kit.Lab(game_home / "labs" / "cargo-sample")


def test_starting_a_lab_runs_setup_in_an_empty_folder(game_home: Path) -> None:
    leftover = game_home / "labs" / "cargo-sample" / "left-from-before.txt"
    leftover.parent.mkdir(parents=True)
    leftover.write_text("old\n")
    state = runner.start_lab(runner.load(cargo_sample))
    assert state == {"branch": "trunk"}
    assert sorted(path.name for path in (game_home / "labs" / "cargo-sample").iterdir()) == ["project"]
    assert (game_home / "labs" / "cargo-sample" / "project" / "hello.txt").read_text() == "hello\n"


def test_starting_a_lab_removes_every_other_lab(game_home: Path) -> None:
    other = game_home / "labs" / "other-level" / "project"
    other.mkdir(parents=True)
    other.chmod(0o500)
    (game_home / "labs" / "stray.txt").write_text("x")
    runner.start_lab(runner.load(cargo_sample))
    assert [path.name for path in (game_home / "labs").iterdir()] == ["cargo-sample"]


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
    runner.start_lab(dataclasses.replace(runner.load(cargo_sample), setup=plain_init))
    assert (game_home / "gitconfig").read_text() == gitcmd.BASE_CONFIG
    assert kit.git(runner.lab_of("cargo-sample").project, "symbolic-ref", "--short", "HEAD") == "main\n"


def test_starting_a_lab_keeps_the_game_git_config_the_player_changed(game_home: Path) -> None:
    (game_home / "gitconfig").write_text("[user]\n\tname = Ada\n")
    runner.start_lab(runner.load(cargo_sample))
    assert (game_home / "gitconfig").read_text() == "[user]\n\tname = Ada\n"


def test_a_failed_setup_leaves_no_lab_and_raises(game_home: Path) -> None:
    def broken_setup(lab: kit.Lab) -> kit.State:
        (lab.root / "half-built").write_text("x")
        raise RuntimeError("setup broke")

    with pytest.raises(RuntimeError, match="setup broke"):
        runner.start_lab(dataclasses.replace(runner.load(cargo_sample), setup=broken_setup))
    assert not (game_home / "labs" / "cargo-sample").exists()


def test_a_setup_that_returns_no_state_is_a_bug_and_leaves_no_lab(game_home: Path) -> None:
    def forgetful_setup(lab: kit.Lab) -> kit.State:
        return None  # type: ignore[return-value]

    with pytest.raises(ValueError, match="cargo-sample.*setup"):
        runner.start_lab(dataclasses.replace(runner.load(cargo_sample), setup=forgetful_setup))
    assert not (game_home / "labs" / "cargo-sample").exists()


def test_removing_the_labs_deletes_them_all_and_tolerates_none(game_home: Path) -> None:
    runner.start_lab(runner.load(cargo_sample))
    runner.remove_labs()
    runner.remove_labs()
    assert not (game_home / "labs").exists()


def test_a_level_is_a_challenge_only_when_it_says_so() -> None:
    goals = [step for step in cargo_sample.QUEST if isinstance(step, kit.WatchStep)]
    assert runner.load(level_module(CHALLENGE=True, QUEST=goals)).challenge is True
    assert runner.load(level_module()).challenge is False
