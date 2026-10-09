from pathlib import Path
from typing import get_args

import pytest

from firstcommit import chapters, freeplay, gitcmd, records, runner, save
from firstcommit.lab import Lab


def git(folder: Path, *args: str) -> str:
    """
    Run a git command in a playground folder, as the player's terminal would see the repository.

    Parameters
    ----------
    folder : Path
        Where to run it.
    *args : str
        Arguments after ``git``.

    Returns
    -------
    str
        Its standard output, stripped.
    """
    return gitcmd.output(folder, *args).strip()


def subjects(folder: Path, *refs: str) -> list[str]:
    """
    List the subjects of the commits that refs reach, newest first.

    Parameters
    ----------
    folder : Path
        A clone.
    *refs : str
        The refs, such as ``main``.

    Returns
    -------
    list[str]
        Each commit's subject.
    """
    return git(folder, "log", "--format=%s", *refs).splitlines()


def test_the_registry_holds_the_seven_starting_points_in_picker_order() -> None:
    assert list(freeplay.STARTS) == list(get_args(records.StartId))
    assert list(freeplay.STARTS) == ["empty", "changes", "branches", "alex-ahead", "both", "conflict", "lost"]


def test_every_start_has_a_title_and_a_one_line_suggestion_in_every_language() -> None:
    languages = set(get_args(records.Language))
    for start in freeplay.STARTS.values():
        for texts in (start.title, start.blurb, start.banner):
            assert set(texts) == languages
            assert all(text.strip() and "\n" not in text for text in texts.values())


def test_every_start_names_real_chapters_and_opens_on_a_playground_view() -> None:
    for start in freeplay.STARTS.values():
        assert set(start.uses) <= set(chapters.CHAPTERS)
        assert start.view in get_args(records.PlaygroundView)
        assert start.view != "graph"


def test_alex_is_shown_at_first_only_in_the_starts_about_two_people_and_absent_without_a_mothership() -> None:
    assert [start_id for start_id, start in freeplay.STARTS.items() if start.alex] == ["alex-ahead", "conflict"]
    assert [start_id for start_id, start in freeplay.STARTS.items() if not start.mothership] == ["empty"]


def commits(lab: Lab) -> list[str]:
    """
    List every commit of a playground's repositories, with its hash, in every ref and the move log.

    Parameters
    ----------
    lab : Lab
        The playground's lab.

    Returns
    -------
    list[str]
        ``<hash> <subject>`` lines, yours then GitHub's; empty for a folder that is no repository.
    """
    found = []
    for folder in (lab.project, lab.github):
        if (folder / ".git").exists() or (folder / "HEAD").exists():
            found += git(folder, "log", "--all", "--reflog", "--format=%H %s").splitlines()
    return found


@pytest.mark.parametrize("start_id", list(get_args(records.StartId)))
def test_a_start_is_the_same_commits_with_the_same_hashes_every_time(start_id: records.StartId) -> None:
    lab = freeplay.build(start_id)
    first = commits(lab)
    assert freeplay.build(start_id) == lab
    assert commits(lab) == first


@pytest.mark.parametrize("start_id", [start_id for start_id in get_args(records.StartId) if start_id != "empty"])
def test_every_start_with_a_mothership_has_the_same_names_the_field_guide_tries(start_id: records.StartId) -> None:
    lab = freeplay.build(start_id)
    assert git(lab.project, "remote", "get-url", "origin") == "../github.com/moonbase/project.git"
    for folder in (lab.project, lab.teammate):
        assert {"README.md", "notes.txt", "route.txt", "crew.txt"} <= set(git(folder, "ls-files").split())
    assert git(lab.teammate, "config", "user.name") == "Alex"


def test_empty_is_two_files_with_no_repository_even_inside_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gitcmd.output(tmp_path, "init", "--quiet")
    monkeypatch.setenv(save.HOME_VARIABLE, str(tmp_path / "home"))
    lab = freeplay.build("empty")
    assert sorted(path.name for path in lab.project.iterdir()) == ["README.md", "notes.txt"]
    assert not lab.github.exists() and not lab.teammate.exists()
    assert "not a git repository" in gitcmd.run(lab.project, "status").stderr


def test_changes_has_notes_edited_on_main_and_a_branch_the_edit_comes_along_to() -> None:
    lab = freeplay.build("changes")
    assert git(lab.project, "status", "--porcelain") == "M notes.txt"
    assert git(lab.project, "branch", "--show-current") == "main"
    git(lab.project, "switch", "bright-lights")
    assert git(lab.project, "status", "--porcelain") == "M notes.txt"


def test_branches_has_two_experiments_off_mains_commit_and_you_on_main() -> None:
    lab = freeplay.build("branches")
    main = git(lab.project, "rev-parse", "main")
    for branch, file in [("bright-lights", "lights.txt"), ("quiet-engine", "engine.txt")]:
        assert git(lab.project, "rev-parse", f"{branch}^") == main
        assert git(lab.project, "diff", "--name-only", "main", branch) == file
    assert git(lab.project, "branch", "--show-current") == "main"
    assert git(lab.project, "status", "--porcelain") == ""


def test_alex_ahead_has_two_commits_of_alex_on_the_mothership_that_you_have_not_fetched() -> None:
    lab = freeplay.build("alex-ahead")
    assert git(lab.github, "rev-list", "--count", "main", "^" + git(lab.project, "rev-parse", "origin/main")) == "2"
    assert set(git(lab.github, "log", "-2", "--format=%an", "main").split()) == {"Alex"}
    assert git(lab.teammate, "rev-parse", "main") == git(lab.github, "rev-parse", "main")


def test_both_has_main_and_origin_main_diverged_and_a_pull_merges_without_a_conflict() -> None:
    lab = freeplay.build("both")
    assert git(lab.project, "rev-list", "--left-right", "--count", "main...origin/main") == "1\t1"
    assert subjects(lab.project, "-1", "origin/main") == subjects(lab.github, "-1", "main")
    assert gitcmd.run(lab.project, "pull", "--no-rebase", "--no-edit").returncode == 0


def test_conflict_stops_your_pull_with_markers_in_the_checklist() -> None:
    lab = freeplay.build("conflict")
    assert (lab.project / ".git" / "MERGE_HEAD").exists()
    assert git(lab.project, "diff", "--name-only", "--diff-filter=U") == "checklist.txt"
    assert "<<<<<<< HEAD\n" in (lab.project / "checklist.txt").read_text()
    assert subjects(lab.teammate, "-1") == ["Head for Jupiter"]


def test_lost_has_the_thrusters_branch_deleted_and_its_last_commit_one_move_back() -> None:
    lab = freeplay.build("lost")
    assert git(lab.project, "branch", "--list", "thrusters") == ""
    assert subjects(lab.project, "-1", "HEAD@{1}") == ["Test the right thruster"]
    assert git(lab.project, "branch", "--show-current") == "main"


def test_a_build_replaces_the_playground_and_leaves_the_level_labs_alone_as_a_level_leaves_it() -> None:
    level_lab = runner.lab_of("cargo-first")
    level_lab.root.mkdir(parents=True)
    lab = freeplay.build("branches")
    (lab.project / "scratch.txt").write_text("mine\n")
    assert freeplay.build("lost") == freeplay.lab() == Lab(save.home() / save.PLAYGROUND_FOLDER)
    assert not (lab.project / "scratch.txt").exists()
    assert level_lab.root.exists()
    runner.remove_labs()
    assert lab.project.exists()


def test_removing_the_playground_removes_its_lab() -> None:
    lab = freeplay.build("conflict")
    freeplay.remove()
    assert not lab.root.exists()
    freeplay.remove()


def test_building_or_removing_the_playground_removes_what_a_killed_git_mergetool_left() -> None:
    left = save.ensure_tmp() / "git-mergetool-Ab12Cd"
    left.mkdir()
    freeplay.build("conflict")
    assert not left.exists()
    left.mkdir()
    freeplay.remove()
    assert not left.exists()
