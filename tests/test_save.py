import json
from pathlib import Path
from typing import Any

import pytest

from firstcommit import records, save

PAYOUT: save.Payout = {"level": "basics-first-commit", "xp": 85, "first_time": True, "rank_before": "Untracked", "rank_after": "Untracked"}
PROGRESS: save.Progress = {
    "xp": 95,
    "levels": {"basics-first-commit": {"finished": "2026-10-06T10:00:00+02:00", "xp": 85, "state": {"branch": "main"}}},
    "cards": {"basics-staging-area": {"box": 2, "due": "2026-10-09"}},
    "streak": 1,
    "best_streak": 3,
    "last_payout": PAYOUT,
}
ACTIVE: save.Active = {
    "level": "basics-first-commit",
    "started": "2026-10-06T10:00:00+02:00",
    "step": 1,
    "hints": 0,
    "attempts": 2,
    "state": {"answer": "abc", "nested": {"list": [1, 2]}},
}


def test_a_new_player_has_no_progress(game_home: Path) -> None:
    assert save.load_progress() == {"xp": 0, "levels": {}, "cards": {}, "streak": 0, "best_streak": 0, "last_payout": None}
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
            "index_change": None,
            "folder_change": None,
        }
    ],
    "operation": None,
    "stash": 0,
    "truncated": False,
}
OBSERVED: save.Observed = {"level": "basics-first-commit", "project": SNAPSHOT, "github": {**SNAPSHOT, "bare": True, "files": []}}


def test_observed_snapshots_read_back_and_clear() -> None:
    observed = OBSERVED
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
        Path to the field, such as ``"levels.basics-first-commit.xp"``; a number picks a list item.
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
    ("levels.basics-first-commit.finished", None),
    ("levels.basics-first-commit.xp", "85"),
    ("levels.basics-first-commit.bonus", 1),
    ("levels.basics-first-commit.state", ["main"]),
    ("levels.basics-first-commit.state", ...),
    ("cards.basics-staging-area.box", ...),
    ("cards.basics-staging-area.due", 20261009),
    ("cards.basics-staging-area.due", "tomorrow"),
    ("cards.basics-staging-area.due", "2026-02-30"),
    ("levels.basics-first-commit.finished", "yesterday"),
    ("streak", None),
    ("best_streak", -3),
    ("last_payout.first_time", "yes"),
    ("last_payout.rank_after", 3),
    ("last_payout", "basics-first-commit"),
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
    (game_home / "labs").mkdir()
    save.erase()
    save.erase()
    assert sorted(path.name for path in game_home.iterdir()) == ["labs"]


def test_erasing_works_when_the_save_files_are_damaged(game_home: Path) -> None:
    (game_home / "progress.json").write_text("{damaged")
    (game_home / "active.json").write_text("[]")
    save.erase()
    assert save.load_progress()["xp"] == 0
    assert save.load_active() is None


def test_the_home_must_be_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", "relative/home")
    with pytest.raises(ValueError, match="FIRSTCOMMIT_HOME"):
        save.home()


def test_the_home_must_not_hold_a_colon(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(tmp_path / "a:b"))
    with pytest.raises(ValueError, match="FIRSTCOMMIT_HOME.*':'"):
        save.home()
