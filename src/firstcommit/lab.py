"""
The folders of a level's lab: plain paths, so the toolkit and the modules that build labs share one layout.

`firstcommit.runner` owns where a lab lives (``<home>/labs/<level id>``) and its lifecycle; a level
creates the parts it needs (`firstcommit.kit` re-exports `Lab`).
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Lab:
    """
    The folders of one level's lab. Everything a level creates lives under ``root``.

    ``project`` is the player's repository (the terminal opens there when it exists, else in
    ``root``); ``github`` is the bare repository that stands in for GitHub, for levels with a
    remote; ``teammate`` is a teammate's clone of it, for levels where someone else shares the
    remote. A level creates only the parts it needs.
    """

    root: Path

    @property
    def project(self) -> Path:
        """The player's working folder."""
        return self.root / "project"

    @property
    def github(self) -> Path:
        """The bare repository that plays GitHub."""
        return self.root / "github.com" / "moonbase" / "project.git"

    @property
    def teammate(self) -> Path:
        """A teammate's working folder: their own clone of the stand-in GitHub."""
        return self.root / "teammate" / "project"

    def github_url(self, clone: Path) -> str:
        """
        Give the URL a clone uses to reach the stand-in GitHub: its path from the clone's top folder.

        ``git clone`` records GitHub's absolute path, and git then prints it in push, fetch and
        pull output and writes it into merge commits ("Merge branch 'main' of /home/..."). Git
        reads a relative path from the clone's top folder, from any folder inside it, so every
        level that clones `github` sets this right after cloning, with
        ``git remote set-url origin <url>``. ``git remote -v`` then shows it as it is: the game's
        GitHub is a folder next to the player's.

        Parameters
        ----------
        clone : Path
            The clone's top folder, inside the lab, such as `project` or `teammate`.

        Returns
        -------
        str
            The relative path, such as ``../github.com/moonbase/project.git``.

        Raises
        ------
        ValueError
            If ``clone`` lies outside the lab.
        """
        if not clone.is_relative_to(self.root):
            raise ValueError(f"{clone} is outside the lab {self.root}")
        return os.path.relpath(self.github, clone)
