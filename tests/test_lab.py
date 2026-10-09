from pathlib import Path

import pytest

from firstcommit.lab import Lab


def test_a_lab_keeps_the_project_and_the_stand_in_github_under_its_root(tmp_path: Path) -> None:
    lab = Lab(tmp_path)
    assert lab.project == tmp_path / "project"
    assert lab.github == tmp_path / "github.com" / "moonbase" / "project.git"


def test_a_lab_keeps_the_teammates_clone_apart_from_the_players_project(tmp_path: Path) -> None:
    lab = Lab(tmp_path)
    assert lab.teammate == tmp_path / "teammate" / "project"
    assert lab.teammate.parent != lab.project.parent


def test_a_clone_reaches_the_stand_in_github_by_a_path_from_its_own_top_folder(tmp_path: Path) -> None:
    lab = Lab(tmp_path)
    assert lab.github_url(lab.project) == "../github.com/moonbase/project.git"
    assert lab.github_url(lab.teammate) == "../../github.com/moonbase/project.git"


def test_a_folder_outside_the_lab_has_no_url_for_its_github(tmp_path: Path) -> None:
    lab = Lab(tmp_path / "lab")
    with pytest.raises(ValueError, match="outside the lab"):
        lab.github_url(tmp_path / "elsewhere")


def test_a_lab_keeps_the_pull_requests_beside_the_stand_in_github_not_inside_it(tmp_path: Path) -> None:
    lab = Lab(tmp_path)
    assert lab.pulls == lab.github.parent / "pulls.json"
