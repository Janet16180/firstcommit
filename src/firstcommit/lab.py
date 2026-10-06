"""
The folders of a level's lab: plain paths, so the toolkit and the modules that build labs share one layout.

`firstcommit.runner` owns where a lab lives (``<home>/labs/<level id>``) and its lifecycle; a level
creates the parts it needs (`firstcommit.kit` re-exports `Lab`).
"""

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
        return self.root / "github" / "project.git"

    @property
    def teammate(self) -> Path:
        """A teammate's working folder: their own clone of the stand-in GitHub."""
        return self.root / "teammate" / "project"
