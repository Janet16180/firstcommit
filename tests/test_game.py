import dataclasses
import json
import os
import stat
import threading
from collections.abc import Callable, Sequence
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from termlab import sandbox

from firstcommit import changes, demos, game, gitcmd, kit, markup, repomap, runner, save, score
from firstcommit.chapters import CHAPTERS

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
    files: list[repomap.FileEntry] = [{"path": name, "head": None, "index": None, "folder": "0" * 40, "ignored": False, "conflicted": False} for name in names]
    return {"exists": path.is_dir(), "bare": False, "head": None, "branch": None, "commits": [], "refs": [], "files": files, "operation": None, "stash": 0, "truncated": False}


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


def solve(level: runner.Level) -> None:
    """
    Play the sample level's reference solution in its lab.

    Parameters
    ----------
    level : runner.Level
        The level in progress.
    """
    level.solve(runner.lab_of(level.id), active_record()["state"])


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
    basics = status["chapters"][1]
    assert basics["levels"] == [{"id": "basics-sample", "title": "Say hello", "difficulty": 1, "xp": 100, "done": False, "has_lesson": True, "has_quest": True}]
    assert basics["cards"] == 12
    assert status["chapters"][0]["levels"] == []


def test_the_dashboard_shows_the_level_in_progress(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.hint()
    active = game.status()["active"]
    assert active is not None
    assert {key: value for key, value in active.items() if key != "started"} == {"level": "basics-sample", "step": 0, "steps": 3, "hints": 1, "hints_total": 3, "attempts": 0}


def test_an_unknown_level_id_raises_key_error(sample_level: runner.Level) -> None:
    for action in (game.level, game.lesson, game.start):
        with pytest.raises(KeyError):
            action("basics-nothing")


def test_starting_an_unknown_level_leaves_the_level_in_progress_alone(sample_level: runner.Level, game_home: Path) -> None:
    game.start(sample_level.id)
    with pytest.raises(KeyError):
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
    assert (view["question"], view["placeholder"], view["debrief"]) == ("", "", None)


def test_a_level_solved_by_a_typed_answer_shows_its_question_filled_from_its_state(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    level = dataclasses.replace(sample_level, question="Which branch is `{{branch}}` on?", placeholder="like {{branch}}")
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    view = game.level(level.id)
    assert (view["question"], view["placeholder"]) == ("Which branch is `trunk` on?", "like trunk")


def test_text_of_the_level_in_progress_is_filled_from_its_state(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    view = game.level(sample_level.id)
    assert "trunk" in text_of(view["briefing"])
    assert view["steps"][2]["question"] == "Which branch is `trunk`?"


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


def test_a_lesson_shows_the_real_commands_their_output_and_the_repository_they_leave(sample_level: runner.Level) -> None:
    first, second = game.lesson(sample_level.id)["slides"]
    assert first["transcript"] == [{"command": "git init -q demo", "output": ""}]
    assert [line["command"] for line in second["transcript"]] == ["cd demo", "printf 'hello\\n' > hello.txt", "git add hello.txt", "git ls-files --stage"]
    assert second["transcript"][-1]["output"] == f"100644 {HELLO_BLOB} 0\thello.txt\n"
    assert (second["view"], second["map"]["branch"]) == ("objects", "main")
    assert [(entry["path"], entry["head"], entry["index"]) for entry in second["map"]["files"]] == [("hello.txt", None, HELLO_BLOB)]
    assert second["objects"] == [{"hash": HELLO_BLOB, "type": "blob", "size": 6}]


def test_starting_a_level_builds_its_lab_and_records_it(sample_level: runner.Level, game_home: Path) -> None:
    view = game.start(sample_level.id)
    assert (view["level"], view["step"], view["steps"], view["hints"], view["hints_total"], view["attempts"]) == ("basics-sample", 0, 3, 0, 3, 0)
    assert datetime.fromisoformat(view["started"]).tzinfo is not None
    assert (lab_project(game_home) / "hello.txt").exists()
    assert save.load_active() == {"level": "basics-sample", "started": view["started"], "step": 0, "hints": 0, "attempts": 0, "state": {"branch": "trunk"}}


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


@pytest.mark.parametrize("action", [lambda: game.quest_step(None), lambda: game.check(None, auto=True), game.hint, game.observe])
def test_actions_on_a_level_need_a_level_in_progress(sample_level: runner.Level, action: Callable[[], object]) -> None:
    with pytest.raises(game.NotPlayingError):
        action()


def test_a_level_in_progress_that_no_longer_exists_counts_as_none(sample_level: runner.Level) -> None:
    save.write_active({"level": "basics-gone", "started": "2026-10-06T10:00:00+00:00", "step": 0, "hints": 0, "attempts": 0, "state": {}})
    assert game.status()["active"] is None
    with pytest.raises(game.NotPlayingError):
        game.check(None, auto=False)


def test_a_read_step_passes_whatever_is_typed(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    assert game.quest_step("anything") == {"correct": True, "message": [], "step": 1, "quest_done": False}


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
    assert game.quest_step(" trunk ") == {"correct": True, "message": markup.parse("Right."), "step": 3, "quest_done": True}


def test_a_finished_quest_checks_nothing_more(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    save.write_active({**active_record(), "step": 3})
    assert game.quest_step("trunk") == {"correct": False, "message": [], "step": 3, "quest_done": True}


def test_quest_steps_never_count_as_attempts(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.quest_step(None)
    game.quest_step("x")
    assert active_record()["attempts"] == 0


def test_a_check_the_player_asks_for_counts_as_an_attempt_and_an_automatic_one_does_not(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    result = game.check(None, auto=True)
    assert (result["solved"], result["payout"], result["debrief"]) == (False, None, None)
    assert result["message"] == markup.parse("`hello.txt` is not in a commit yet.")
    game.check("x", auto=False)
    game.check(None, auto=False)
    game.check(None, auto=True)
    assert active_record()["attempts"] == 2


def test_a_blank_answer_counts_as_no_answer(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str | None] = []

    def recording_check(lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict:
        seen.append(answer)
        return kit.Verdict(False, "no")

    level = dataclasses.replace(sample_level, check=recording_check)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    game.start(level.id)
    game.check("  \t", auto=False)
    game.check("", auto=False)
    game.check(" main ", auto=False)
    assert seen == [None, None, " main "]


def secret_is_main(lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict:
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

    Returns
    -------
    kit.Verdict
        Whether the answer is ``main``.
    """
    right = kit.answer_is(answer, kit.digest("main"))
    return kit.Verdict(right, "Right." if right else "No.")


def test_text_the_player_sends_that_utf8_cannot_encode_is_only_a_wrong_answer(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> None:
    secret_step = kit.Step(id="secret", text="Which branch?", question="Which?", check=secret_is_main)
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

    def recording_check(lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict:
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
    result = game.check(None, auto=True)
    payout: save.Payout = {"level": "basics-sample", "xp": 100, "first_time": True, "rank_before": "Untracked", "rank_after": "Untracked"}
    assert (result["solved"], result["payout"]) == (True, payout)
    assert result["debrief"] == markup.parse("`hello.txt` is now in a commit on `trunk`.")
    progress = save.load_progress()
    assert (progress["xp"], progress["last_payout"]) == (100, payout)
    assert {key: value for key, value in progress["levels"]["basics-sample"].items() if key != "finished"} == {"xp": 100, "state": {"branch": "trunk"}}
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


def test_a_level_is_solved_even_before_its_quest_is_finished(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    solve(sample_level)
    assert game.check(None, auto=False)["solved"] is True


def test_hints_lower_what_a_level_pays(sample_level: runner.Level) -> None:
    game.start(sample_level.id)
    game.hint()
    solve(sample_level)
    payout = game.check(None, auto=False)["payout"]
    assert payout is not None and payout["xp"] == score.level_reward(100, 1, first_time=True) == 85


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
    assert save.load_progress()["levels"]["basics-sample"] == {**first, "state": {"branch": "main"}}
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
    assert (choice["kind"], sorted(choice["choices"]), choice["code"]) == ("choice", ["right", "worse", "wrong"], "")
    assert choice["prompt"] == markup.parse("Which one is `right`?")
    assert (predict["code"], sorted(predict["choices"])) == ("echo hi", ["ha", "hi", "ho"])
    assert (text["choices"], text["placeholder"]) == ([], "a branch")
    assert "correct" not in choice and "accept" not in text


def test_an_unknown_chapter_or_card_raises_key_error(sample_level: runner.Level) -> None:
    with pytest.raises(KeyError):
        game.due_cards("nowhere", 5)
    with pytest.raises(KeyError):
        game.answer_card("basics-nothing", "right")
    with pytest.raises(KeyError):
        game.notes("nowhere")


def test_a_right_answer_to_a_new_card_pays_and_schedules_it(sample_level: runner.Level) -> None:
    result = game.answer_card("basics-predict", "hi")
    assert result == {"correct": True, "answer": "hi", "explain": markup.parse("It echoes."), "xp": 20, "streak": 1, "bonus": 0}
    progress = save.load_progress()
    assert (progress["xp"], progress["streak"], progress["best_streak"]) == (20, 1, 1)
    assert progress["cards"]["basics-predict"] == {"box": 1, "due": (date.today() + timedelta(days=1)).isoformat()}


def test_a_wrong_answer_pays_nothing_and_brings_the_card_back_today(sample_level: runner.Level) -> None:
    game.answer_card("basics-c01", "right")
    result = game.answer_card("basics-text", "master")
    assert (result["correct"], result["answer"], result["xp"], result["streak"]) == (False, "main", 0, 0)
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


def test_opening_a_terminal_gives_the_game_its_base_git_config(sample_level: runner.Level, game_home: Path) -> None:
    game.terminal_folder()
    assert (game_home / "gitconfig").read_text() == gitcmd.BASE_CONFIG


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
    for record in (game.status(), game.level(sample_level.id), game.lesson(sample_level.id), game.observe(), game.due_cards("basics", 3)):
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
