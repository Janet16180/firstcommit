from collections.abc import Callable
from pathlib import Path

import pytest

from firstcommit import kit
from firstcommit.levels import _names_story as story


def built(tmp_path: Path, name: str, build: Callable[[kit.Lab], None]) -> kit.Lab:
    """
    Build one level's start of the story in a fresh lab.

    Parameters
    ----------
    tmp_path : Path
        Where the lab goes.
    name : str
        The lab's folder name.
    build : Callable[[kit.Lab], None]
        One of the story's builders.

    Returns
    -------
    kit.Lab
        The lab.
    """
    lab = kit.Lab(tmp_path / name)
    lab.root.mkdir()
    build(lab)
    return lab


def commits(lab: kit.Lab) -> dict[str, str]:
    """
    Give every commit your clone holds, by message.

    Parameters
    ----------
    lab : kit.Lab
        The lab.

    Returns
    -------
    dict[str, str]
        Each commit's hash by its message.
    """
    lines = kit.git(lab.project, "log", "--all", "--format=%s\t%H").splitlines()
    return dict(line.split("\t") for line in lines)


@pytest.mark.parametrize("build", [story.name_tags, story.any_commit, story.experiments, story.one_step])
def test_each_level_holds_the_same_commits_as_the_one_before_it_with_the_same_hashes(tmp_path: Path, build: Callable[[kit.Lab], None]) -> None:
    first = commits(built(tmp_path, "first", story.name_tags))
    later = commits(built(tmp_path, "later", build))
    assert {message: later[message] for message in first} == first


def test_a_name_on_any_commit_starts_after_the_pull_on_alexs_route_fix_with_test_run_still_there(tmp_path: Path) -> None:
    lab = built(tmp_path, "lab", story.any_commit)
    assert kit.git(lab.project, "log", "--format=%an %s", "main").splitlines()[:2] == ["Alex Fix the route", f"{kit.PLAYER.name} {story.FUEL_MESSAGE}"]
    assert kit.git(lab.project, "rev-parse", "main", "origin/main").split() == [kit.git(lab.github, "rev-parse", "main").strip()] * 2
    assert kit.git(lab.project, "log", "-1", "--format=%s", story.OLD_NAME).strip() == "Start the project"
    assert kit.git(lab.project, "status", "--porcelain") == ""


def test_one_step_starts_on_main_with_two_experiments_first_route_and_dim_txt_waiting(tmp_path: Path) -> None:
    lab = built(tmp_path, "lab", story.one_step)
    assert kit.git(lab.project, "branch", "--format=%(refname:short)").split() == ["bright-lights", story.FIRST_ROUTE, "main", "quiet-engine"]
    assert kit.snapshot(lab.project)["branch"] == "main"
    assert kit.git(lab.project, "log", "-1", "--format=%s", story.FIRST_ROUTE).strip() == "Plot the route"
    assert kit.git(lab.project, "status", "--porcelain").strip() == "?? dim.txt"
