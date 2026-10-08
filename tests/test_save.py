import json
from pathlib import Path
from typing import Any

import pytest

from firstcommit import records, save

PAYOUT: save.Payout = {"level": "liftoff-aboard", "xp": 85, "first_time": True, "rank_before": "Untracked", "rank_after": "Untracked"}
PROGRESS: save.Progress = {
    "xp": 95,
    "levels": {"liftoff-aboard": {"finished": "2026-10-06T10:00:00+02:00", "xp": 85, "stars": 2, "state": {"branch": "main"}}},
    "cards": {"cargo-staging-area": {"box": 2, "due": "2026-10-09"}},
    "streak": 1,
    "best_streak": 3,
    "last_payout": PAYOUT,
    "scenes": ["liftoff-aboard"],
    "views": ["station", "crew", "band"],
    "language": "es",
}
ACTIVE: save.Active = {
    "level": "liftoff-aboard",
    "started": "2026-10-06T10:00:00+02:00",
    "step": 1,
    "hints": 0,
    "attempts": 2,
    "state": {"answer": "abc", "nested": {"list": [1, 2]}},
    "log_offset": 40,
    "typed": [{"line": "git status", "status": 128}, {"line": "ls", "status": 0}],
    "events": ["alex-pushes"],
    "done": ["init"],
}


def test_a_new_player_has_no_progress(game_home: Path) -> None:
    assert save.load_progress() == {"xp": 0, "levels": {}, "cards": {}, "streak": 0, "best_streak": 0, "last_payout": None, "scenes": [], "views": ["station"], "language": "en"}
    assert not (game_home / "progress.json").exists()


def test_progress_reads_back_as_written(game_home: Path) -> None:
    save.write_progress(PROGRESS)
    assert save.load_progress() == PROGRESS
    assert json.loads((game_home / "progress.json").read_text()) == PROGRESS


def test_no_level_is_in_progress_until_one_is_written() -> None:
    assert save.load_active() is None
    save.write_active(ACTIVE)
    assert save.load_active() == ACTIVE


def test_clearing_the_active_level_forgets_it(game_home: Path) -> None:
    save.write_active(ACTIVE)
    save.clear_active()
    save.clear_active()
    assert save.load_active() is None


HASH = "e" * 40
SNAPSHOT: records.Snapshot = {
    "exists": True,
    "bare": False,
    "head": HASH,
    "branch": "main",
    "commits": [{"hash": HASH, "short": HASH[:7], "parents": [], "subject": "Add a README", "author": "Ada Tester", "time": 1760000000}],
    "refs": [{"name": "main", "kind": "branch", "target": HASH}],
    "pushed": [],
    "remotes": [{"name": "origin", "url": "../github.com/moonbase/project.git"}],
    "files": [
        {
            "path": "README.md",
            "head": HASH,
            "index": HASH,
            "folder": HASH,
            "head_mode": "100644",
            "index_mode": "100644",
            "folder_mode": "100644",
            "index_change": None,
            "folder_change": None,
            "ignored": False,
            "conflicted": False,
            "repository": False,
        }
    ],
    "operation": None,
    "stash": 0,
    "truncated": False,
}
OBSERVED: save.Observed = {"level": "liftoff-aboard", "project": SNAPSHOT, "github": {**SNAPSHOT, "bare": True, "files": []}, "teammate": SNAPSHOT, "told": 2, "fresh": False}


@pytest.mark.parametrize("observed", [OBSERVED, {**OBSERVED, "github": None, "teammate": None}], ids=["playground", "project only"])
def test_observed_snapshots_read_back_and_clear(observed: save.Observed) -> None:
    assert save.load_observed() is None
    save.write_observed(observed)
    assert save.load_observed() == observed
    save.clear_observed()
    assert save.load_observed() is None


def damaged(record: dict[str, Any], dotted: str, value: Any) -> dict[str, Any]:
    """
    Copy a record with one field, named by a dotted path, replaced (or removed when `value` is `...`).

    Parameters
    ----------
    record : dict[str, Any]
        A valid record.
    dotted : str
        Path to the field, such as ``"levels.liftoff-aboard.xp"``; a number picks a list item.
    value : Any
        The new value, or ``...`` to delete the field.

    Returns
    -------
    dict[str, Any]
        The damaged copy.
    """
    copy: dict[str, Any] = json.loads(json.dumps(record))
    *parents, name = dotted.split(".")
    target: Any = copy
    for parent in parents:
        target = target[int(parent)] if isinstance(target, list) else target[parent]
    key: Any = int(name) if isinstance(target, list) else name
    if value is ...:
        del target[key]
    else:
        target[key] = value
    return copy


PROGRESS_DAMAGE = [
    ("xp", "95"),
    ("xp", True),
    ("xp", 9.5),
    ("xp", -1),
    ("xp", ...),
    ("levels", []),
    ("levels.liftoff-aboard.finished", None),
    ("levels.liftoff-aboard.xp", "85"),
    ("levels.liftoff-aboard.bonus", 1),
    ("levels.liftoff-aboard.state", ["main"]),
    ("levels.liftoff-aboard.state", ...),
    ("levels.liftoff-aboard.stars", ...),
    ("levels.liftoff-aboard.stars", "3"),
    ("scenes", ...),
    ("scenes", "liftoff-aboard"),
    ("scenes.0", 3),
    ("views", ...),
    ("views.0", "map"),
    ("language", ...),
    ("language", "fr"),
    ("cards.cargo-staging-area.box", ...),
    ("cards.cargo-staging-area.due", 20261009),
    ("cards.cargo-staging-area.due", "tomorrow"),
    ("cards.cargo-staging-area.due", "2026-02-30"),
    ("levels.liftoff-aboard.finished", "yesterday"),
    ("streak", None),
    ("best_streak", -3),
    ("last_payout.first_time", "yes"),
    ("last_payout.rank_after", 3),
    ("last_payout", "liftoff-aboard"),
    ("surprise", 1),
]


@pytest.mark.parametrize(("field", "value"), PROGRESS_DAMAGE, ids=[f"{field}={value!r}" for field, value in PROGRESS_DAMAGE])
def test_a_damaged_progress_file_names_the_file_and_the_field(game_home: Path, field: str, value: Any) -> None:
    (game_home / "progress.json").write_text(json.dumps(damaged(dict(PROGRESS), field, value)))
    with pytest.raises(save.SaveError, match=r"progress\.json") as raised:
        save.load_progress()
    assert f"`{field}`" in str(raised.value)


ACTIVE_DAMAGE = [
    ("level", 3),
    ("started", ...),
    ("started", "this morning"),
    ("step", "1"),
    ("hints", False),
    ("attempts", -2),
    ("state", []),
    ("log_offset", -1),
    ("typed", ...),
    ("typed.0.line", None),
    ("typed.0.status", "128"),
    ("events", ...),
    ("events.0", 3),
    ("done", ...),
    ("done", "init"),
    ("extra", "x"),
]


@pytest.mark.parametrize(("field", "value"), ACTIVE_DAMAGE, ids=[f"{field}={value!r}" for field, value in ACTIVE_DAMAGE])
def test_a_damaged_active_file_names_the_file_and_the_field(game_home: Path, field: str, value: Any) -> None:
    (game_home / "active.json").write_text(json.dumps(damaged(dict(ACTIVE), field, value)))
    with pytest.raises(save.SaveError, match=r"active\.json") as raised:
        save.load_active()
    assert f"`{field}`" in str(raised.value)


def test_a_level_state_may_hold_any_json(game_home: Path) -> None:
    active = damaged(dict(ACTIVE), "state", {"n": 1.5, "flag": True, "none": None, "deep": {"x": ["y"]}})
    (game_home / "active.json").write_text(json.dumps(active))
    assert save.load_active() == active


@pytest.mark.parametrize("content", ["{not json", "[1, 2]", ""])
def test_a_save_file_that_is_not_a_json_object_is_damaged(game_home: Path, content: str) -> None:
    (game_home / "progress.json").write_text(content)
    with pytest.raises(save.SaveError, match=r"progress\.json"):
        save.load_progress()


@pytest.mark.parametrize(
    "content",
    [
        "{damaged",
        "[]",
        json.dumps({"level": "x", "project": [], "github": None}),
        json.dumps({"level": "x", "project": {}}),
        json.dumps({"level": "x", "project": {}, "github": None, "extra": 1}),
    ],
)
def test_an_observation_that_does_not_match_counts_as_nothing_observed_yet(game_home: Path, content: str) -> None:
    (game_home / "observed.json").write_text(content)
    assert save.load_observed() is None


OBSERVATION_DAMAGE = [
    ("project.files.0.repository", ...),
    ("project.files.0.head", 3),
    ("project.files.0.folder_change", "renamed"),
    ("project.commits.0.parents", "none"),
    ("project.commits.0.parents", [3]),
    ("project.commits.0.time", -1),
    ("project.refs.0.kind", "remote-tracking"),
    ("project.operation", "squash"),
    ("project.stash", True),
    ("github.exists", None),
    ("github", {"exists": True}),
    ("teammate", ...),
    ("teammate.branch", 3),
    ("teammate", []),
    ("told", ...),
    ("told", -1),
    ("told", "2"),
    ("fresh", ...),
    ("fresh", "no"),
]


@pytest.mark.parametrize(("field", "value"), OBSERVATION_DAMAGE, ids=[f"{field}={value!r}" for field, value in OBSERVATION_DAMAGE])
def test_a_snapshot_of_another_shape_counts_as_nothing_observed_yet(game_home: Path, field: str, value: Any) -> None:
    (game_home / "observed.json").write_text(json.dumps(damaged(dict(OBSERVED), field, value)))
    assert save.load_observed() is None


def test_the_game_git_config_starts_from_the_text_given(game_home: Path) -> None:
    path = save.ensure_gitconfig("[init]\n\tdefaultBranch = main\n")
    assert path == game_home / "gitconfig"
    assert path.read_text() == "[init]\n\tdefaultBranch = main\n"


def test_the_game_git_config_is_never_overwritten(game_home: Path) -> None:
    (game_home / "gitconfig").write_text("[user]\n\tname = Ada\n")
    save.ensure_gitconfig("[init]\n\tdefaultBranch = main\n")
    assert (game_home / "gitconfig").read_text() == "[user]\n\tname = Ada\n"


def test_the_game_git_config_is_created_in_a_new_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(tmp_path / "new" / "home"))
    assert save.ensure_gitconfig("x\n").read_text() == "x\n"


def test_erasing_removes_every_save_file_and_the_git_config(game_home: Path) -> None:
    save.write_progress(PROGRESS)
    save.write_active(ACTIVE)
    save.write_observed(OBSERVED)
    save.ensure_gitconfig("x\n")
    save.write_shell_startup("PS1='$ '\n")
    save.ensure_hushlogin()
    save.write_playground(PLAYGROUND)
    for name in (save.COMMANDS_FILE, save.HISTORY_FILE):
        (game_home / name).write_text("typed\n")
    (game_home / "labs").mkdir()
    save.erase()
    save.erase()
    assert sorted(path.name for path in game_home.iterdir()) == ["labs"]


PLAYGROUND: save.Playground = {"start": "conflict", "alex_shown": {"conflict": True, "branches": False}, "view": "conflict", "whose": "you"}
PLAYGROUND_DAMAGE = [("start", "nowhere"), ("alex_shown.conflict", "yes"), ("alex_shown.nowhere", True), ("view", "station"), ("whose", "bob"), ("view", ...)]


def test_the_playground_has_no_record_until_one_is_written_and_reads_back_as_written() -> None:
    assert save.load_playground() is None
    save.write_playground(PLAYGROUND)
    assert save.load_playground() == PLAYGROUND


@pytest.mark.parametrize(("field", "value"), PLAYGROUND_DAMAGE, ids=[f"{field}={value!r}" for field, value in PLAYGROUND_DAMAGE])
def test_a_damaged_playground_file_names_the_file_and_the_field(game_home: Path, field: str, value: Any) -> None:
    (game_home / "playground.json").write_text(json.dumps(damaged(dict(PLAYGROUND), field, value)))
    with pytest.raises(save.SaveError, match=r"playground\.json") as raised:
        save.load_playground()
    assert f"`{field}`" in str(raised.value)


def test_erasing_works_when_the_save_files_are_damaged(game_home: Path) -> None:
    (game_home / "progress.json").write_text("{damaged")
    (game_home / "active.json").write_text("[]")
    save.erase()
    assert save.load_progress()["xp"] == 0
    assert save.load_active() is None


def test_the_shell_startup_file_is_written_anew_each_time_in_a_new_home_too(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(tmp_path / "new" / "home"))
    save.write_shell_startup("old\n")
    path = save.write_shell_startup("PS1='$ '\n")
    assert (path, path.read_text()) == (tmp_path / "new" / "home" / save.STARTUP_FILE, "PS1='$ '\n")


def test_the_hushlogin_file_is_an_empty_file_in_a_new_home_and_stays_put(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(tmp_path / "new" / "home"))
    path = save.ensure_hushlogin()
    assert (path, path.read_text(), save.ensure_hushlogin()) == (tmp_path / "new" / "home" / save.HUSHLOGIN_FILE, "", path)


def test_the_home_must_be_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", "relative/home")
    with pytest.raises(ValueError, match="FIRSTCOMMIT_HOME"):
        save.home()


def test_the_home_must_not_hold_a_colon(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(tmp_path / "a:b"))
    with pytest.raises(ValueError, match="FIRSTCOMMIT_HOME.*':'"):
        save.home()


OLDER_SHAPES = [
    ("progress.json", damaged(dict(PROGRESS), "scenes", ...), save.load_progress),
    ("progress.json", damaged(dict(PROGRESS), "levels.liftoff-aboard.stars", ...), save.load_progress),
    ("active.json", damaged(dict(ACTIVE), "typed", ...), save.load_active),
    ("active.json", damaged(damaged(dict(ACTIVE), "typed", ...), "log_offset", ...), save.load_active),
]


@pytest.mark.parametrize(("name", "record", "load"), OLDER_SHAPES, ids=[f"{name} without a field" for name, _, _ in OLDER_SHAPES])
def test_a_save_written_by_an_older_game_names_the_file_and_how_to_start_over(game_home: Path, name: str, record: dict[str, Any], load: Any) -> None:
    (game_home / name).write_text(json.dumps(record))
    with pytest.raises(save.SaveError) as raised:
        load()
    message = str(raised.value)
    assert name in message and "older version of the game" in message
    assert "`firstcommit reset --yes`" in message and "`reset`" in message


PULL: records.PullRequest = {
    "number": 1,
    "title": "Fix the lights",
    "author": "you",
    "head": "fix-lights",
    "base": "main",
    "state": "open",
    "reviews": [{"reviewer": "Robin", "verdict": "approved", "body": "", "commit": "a" * 40}],
    "merge_commit": None,
}


def test_pull_requests_read_back_as_written_and_none_before_any(tmp_path: Path) -> None:
    path = tmp_path / "github.com" / "moonbase" / "pulls.json"
    assert save.load_pulls(path) == []
    save.write_pulls(path, [PULL])
    assert save.load_pulls(path) == [PULL]


@pytest.mark.parametrize(("key", "value"), [("number", "1"), ("state", "draft"), ("reviews", [{"verdict": "yes"}]), ("merge_commit", 3)])
def test_a_damaged_pull_request_file_is_a_save_error(tmp_path: Path, key: str, value: object) -> None:
    path = tmp_path / "pulls.json"
    path.write_text(json.dumps({"pulls": [{**PULL, key: value}]}))
    with pytest.raises(save.SaveError, match=key):
        save.load_pulls(path)
