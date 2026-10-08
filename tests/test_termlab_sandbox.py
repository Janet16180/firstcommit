import stat
from pathlib import Path

import pytest

from firstcommit.termlab import sandbox


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """
    Make an empty game home inside the test's own folder.

    Parameters
    ----------
    tmp_path : Path
        The test's folder; it holds the home, so it is outside it.

    Returns
    -------
    Path
        ``<tmp_path>/home``.
    """
    path = tmp_path / "home"
    path.mkdir()
    return path


@pytest.fixture
def outside(tmp_path: Path) -> Path:
    """
    Make a folder outside the home that stands for the player's own files: mode 755, one file.

    Parameters
    ----------
    tmp_path : Path
        The test's folder.

    Returns
    -------
    Path
        ``<tmp_path>/outside``, holding ``notes.txt``.
    """
    path = tmp_path / "outside"
    path.mkdir()
    (path / "notes.txt").write_text("mine")
    path.chmod(0o755)
    return path


def mode(path: Path) -> int:
    """
    Read the permission bits of a file or folder, following symbolic links.

    Parameters
    ----------
    path : Path
        File or folder.

    Returns
    -------
    int
        The permission bits, e.g. ``0o755``.
    """
    return stat.S_IMODE(path.stat().st_mode)


def test_remove_tree_refuses_paths_outside_home(tmp_path: Path, home: Path) -> None:
    with pytest.raises(ValueError, match="refusing to delete"):
        sandbox.remove_tree(tmp_path, home)
    assert home.is_dir()


def test_remove_tree_handles_locked_directories(home: Path) -> None:
    lab = home / "lab" / "x"
    locked = lab / "locked"
    locked.mkdir(parents=True)
    (locked / "file").write_text("data")
    locked.chmod(0)
    sandbox.remove_tree(lab, home)
    assert not lab.exists()


def test_remove_tree_accepts_a_lab_that_does_not_exist(home: Path) -> None:
    sandbox.remove_tree(home / "lab" / "never-started", home)
    assert list(home.iterdir()) == []


def test_remove_tree_refuses_the_home_itself(home: Path) -> None:
    (home / "save.json").write_text("{}")
    with pytest.raises(ValueError, match="refusing to delete"):
        sandbox.remove_tree(home, home)
    assert (home / "save.json").exists()


def test_remove_tree_refuses_a_path_that_climbs_out_of_home(home: Path, outside: Path) -> None:
    (home / "lab").mkdir()
    with pytest.raises(ValueError, match="refusing to delete"):
        sandbox.remove_tree(home / "lab" / ".." / ".." / "outside", home)
    assert (outside / "notes.txt").read_text() == "mine"


def test_remove_tree_refuses_a_lab_that_is_a_symlink_out_of_home(home: Path, outside: Path) -> None:
    lab = home / "lab" / "x"
    lab.parent.mkdir()
    lab.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="refusing to delete"):
        sandbox.remove_tree(lab, home)
    assert mode(outside) == 0o755
    assert (outside / "notes.txt").read_text() == "mine"


def test_remove_tree_deletes_a_link_to_a_folder_outside_home_but_not_the_folder_or_its_mode(
    home: Path, outside: Path
) -> None:
    lab = home / "lab" / "x"
    (lab / "deep").mkdir(parents=True)
    (lab / "deep" / "mine").symlink_to(outside, target_is_directory=True)
    sandbox.remove_tree(lab, home)
    assert not lab.exists()
    assert mode(outside) == 0o755
    assert (outside / "notes.txt").read_text() == "mine"


def test_remove_tree_deletes_a_link_to_a_file_outside_home_but_not_the_file_or_its_mode(
    home: Path, outside: Path
) -> None:
    target = outside / "notes.txt"
    target.chmod(0o640)
    lab = home / "lab" / "x"
    lab.mkdir(parents=True)
    (lab / "notes").symlink_to(target)
    sandbox.remove_tree(lab, home)
    assert not lab.exists()
    assert mode(target) == 0o640
    assert target.read_text() == "mine"


def test_remove_tree_reopens_locked_folders_at_every_depth_and_the_lab_itself(home: Path) -> None:
    lab = home / "lab" / "x"
    inner = lab / "a" / "b"
    inner.mkdir(parents=True)
    (inner / "file").write_text("data")
    for folder in (inner, inner.parent, lab):
        folder.chmod(0)
    sandbox.remove_tree(lab, home)
    assert not lab.exists()
