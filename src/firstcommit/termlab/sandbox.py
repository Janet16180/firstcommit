"""Lab cleanup that never deletes outside a game's home and never follows symbolic links."""

import os
import shutil
from pathlib import Path


def _make_writable(path: Path) -> None:
    """
    Give the owner full access to every directory in a tree so it can be deleted.

    Symbolic links are skipped so nothing outside the tree is touched.

    Parameters
    ----------
    path : Path
        Root of the tree.
    """
    path.chmod(0o700)
    for root, dirs, _ in os.walk(path):
        for name in dirs:
            child = Path(root) / name
            if not child.is_symlink():
                child.chmod(0o700)


def remove_tree(path: Path, home: Path) -> None:
    """
    Delete a lab directory, even if a lesson removed permissions inside it.

    Locked folders inside the lab are opened again first. Symbolic links are deleted, never
    followed, so a link to a player's own files leaves those files and their modes alone.

    Parameters
    ----------
    path : Path
        Directory to delete; must be inside `home`. A missing one is not an error.
    home : Path
        The game's home directory.

    Raises
    ------
    ValueError
        If the path is outside `home`.
    """
    if home.resolve() not in path.resolve().parents:
        raise ValueError(f"refusing to delete {path}: not inside {home}")
    if not path.exists():
        return
    _make_writable(path)
    shutil.rmtree(path)
