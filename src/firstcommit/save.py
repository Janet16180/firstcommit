"""
The player's saved game: where it lives and the shape of its records.

Files under the game home (`home`):
- ``progress.json``: a `Progress` record;
- ``active.json``: an `Active` record while a level is being played;
- ``gitconfig``: the game's own global git configuration (see `firstcommit.gitcmd`);
- ``labs/<level>/``: the lab of the level being played.

The files are written atomically under one lock (termlab's store), so the command line and the
web server never lose each other's update.
"""

from pathlib import Path
from typing import Any, TypedDict

from termlab import store

HOME_VARIABLE = "FIRSTCOMMIT_HOME"
DEFAULT_HOME = "~/.firstcommit"


class LevelRecord(TypedDict):
    """A level the player has finished: when, and the XP paid the first time."""

    finished: str
    xp: int


class CardEntry(TypedDict):
    """A flashcard's place in the Leitner schedule: its box and the day it is due again."""

    box: int
    due: str


class Payout(TypedDict):
    """What the last finished level paid, kept so any view can celebrate it."""

    level: str
    xp: int
    first_time: bool
    rank_before: str
    rank_after: str


class Progress(TypedDict):
    """Everything the player has earned."""

    xp: int
    levels: dict[str, LevelRecord]
    cards: dict[str, CardEntry]
    streak: int
    best_streak: int
    last_payout: Payout | None


class Active(TypedDict):
    """
    The level being played.

    ``step`` is the index of the current guided-quest step; it equals the number of steps once
    the quest is done (and is 0 for a level without a quest).
    """

    level: str
    started: str
    step: int
    hints: int
    attempts: int
    state: dict[str, Any]


def home() -> Path:
    """
    Give the game's home folder, from ``FIRSTCOMMIT_HOME`` or ``~/.firstcommit``.

    Returns
    -------
    Path
        The absolute home folder (it may not exist yet).

    Raises
    ------
    ValueError
        If ``FIRSTCOMMIT_HOME`` is set to a relative or empty path.
    """
    return store.home(HOME_VARIABLE, DEFAULT_HOME)
