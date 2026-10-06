from pathlib import Path

from firstcommit.lab import Lab


def test_a_lab_keeps_the_project_and_the_stand_in_github_under_its_root(tmp_path: Path) -> None:
    lab = Lab(tmp_path)
    assert lab.project == tmp_path / "project"
    assert lab.github == tmp_path / "github" / "project.git"


def test_a_lab_keeps_the_teammates_clone_apart_from_the_players_project(tmp_path: Path) -> None:
    lab = Lab(tmp_path)
    assert lab.teammate == tmp_path / "teammate" / "project"
    assert lab.teammate.parent != lab.project.parent
