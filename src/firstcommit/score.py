"""
The scoring rules, in one place: ranks, what a level pays, what a hint costs, a level's stars, card XP and the streak bonus.

Pure functions of plain numbers: the save and the game decide when to call them.
"""

from dataclasses import dataclass
from typing import TypedDict

RANKS: tuple[tuple[int, str], ...] = (
    (0, "Untracked"),
    (150, "Staged"),
    (400, "Committed"),
    (800, "Branched"),
    (1400, "Merged"),
    (2200, "Pushed"),
    (3400, "Reviewed"),
    (5000, "Maintainer"),
)
"""XP floor and title of each rank, lowest first: the path of a change through Git, then the people who keep a project."""

HINT_PENALTY_PERCENT = 15
REWARD_FLOOR_PERCENT = 50
CARD_XP = {1: 10, 2: 20, 3: 30}
STREAK_LENGTH = 5
STREAK_BONUS = 25
MAX_STARS = 3
PAR_MARGIN = 3
"""Lines a player may type beyond a level's par before it costs a star."""


class Rank(TypedDict):
    """The player's rank: its title, the XP it starts at, and the next rank (None at the top)."""

    title: str
    floor: int
    next_title: str | None
    next_at: int | None


@dataclass(frozen=True)
class CardScore:
    """What one card answer earns: its XP, the streak after it, and the streak bonus it completes."""

    xp: int
    streak: int
    bonus: int


def rank(xp: int) -> Rank:
    """
    Find the rank earned with an amount of XP.

    Parameters
    ----------
    xp : int
        Total experience points.

    Returns
    -------
    Rank
        The highest rank whose floor is reached, and the rank after it.

    Raises
    ------
    ValueError
        If `xp` is negative (a bug: XP is never taken away).
    """
    if xp < 0:
        raise ValueError(f"xp must not be negative, got {xp}")
    index = max(position for position, (floor, _) in enumerate(RANKS) if floor <= xp)
    floor, title = RANKS[index]
    next_at, next_title = RANKS[index + 1] if index + 1 < len(RANKS) else (None, None)
    return {"title": title, "floor": floor, "next_title": next_title, "next_at": next_at}


def level_reward(xp: int, hints: int, first_time: bool) -> int:
    """
    Compute what solving a level pays.

    Each hint takes `HINT_PENALTY_PERCENT` of the level's XP off, but a first solve always pays
    at least `REWARD_FLOOR_PERCENT` of it. Solving a level again pays nothing.

    Parameters
    ----------
    xp : int
        The level's XP.
    hints : int
        Hints revealed while playing it.
    first_time : bool
        Whether the player solves this level for the first time.

    Returns
    -------
    int
        XP to award.

    Raises
    ------
    ValueError
        If `xp` or `hints` is negative (a bug in the caller).
    """
    if xp < 0 or hints < 0:
        raise ValueError(f"xp and hints must not be negative, got xp={xp}, hints={hints}")
    reward = 0
    if first_time:
        penalised = xp * (100 - HINT_PENALTY_PERCENT * hints) // 100
        reward = max(penalised, xp * REWARD_FLOOR_PERCENT // 100)
    return reward


def hint_cost(xp: int, used: int, first_time: bool) -> int:
    """
    Compute what revealing a hint took off a level's reward.

    Parameters
    ----------
    xp : int
        The level's XP.
    used : int
        Hints revealed, this one included (at least 1).
    first_time : bool
        Whether the level would be solved for the first time.

    Returns
    -------
    int
        The reward with one hint fewer, minus the reward now.

    Raises
    ------
    ValueError
        If `used` is below 1 (a bug in the caller).
    """
    if used < 1:
        raise ValueError(f"used counts the hint just revealed and must be at least 1, got {used}")
    return level_reward(xp, used - 1, first_time) - level_reward(xp, used, first_time)


def stars(hints: int, commands: int, par: int) -> int:
    """
    Count the stars a play of a level earns.

    It starts at `MAX_STARS`, loses one once a hint is used and one once the lines typed pass
    ``par + PAR_MARGIN``, and never goes below 1.

    Parameters
    ----------
    hints : int
        Hints revealed in this play.
    commands : int
        Lines typed in the game's terminal since the level started.
    par : int
        The level's par: the lines its shortest play types.

    Returns
    -------
    int
        1 to `MAX_STARS`.

    Raises
    ------
    ValueError
        If `hints` or `commands` is negative (a bug in the caller).
    """
    if hints < 0 or commands < 0:
        raise ValueError(f"hints and commands must not be negative, got hints={hints}, commands={commands}")
    lost = (hints > 0) + (commands > par + PAR_MARGIN)
    return max(1, MAX_STARS - lost)


def card_score(level: int, correct: bool, pays: bool, streak: int) -> CardScore:
    """
    Score one flashcard answer.

    Only a right answer to a card that pays (new or due) earns XP and extends the streak; any
    other answer resets the streak, so re-quizzing known cards earns nothing (Ring Zero
    decision H2). Every `STREAK_LENGTH`-th answer of a streak earns `STREAK_BONUS`.

    Parameters
    ----------
    level : int
        The card's level, a key of `CARD_XP`.
    correct : bool
        Whether the answer was right.
    pays : bool
        Whether the card was new or due when it was asked.
    streak : int
        Paying right answers in a row before this one.

    Returns
    -------
    CardScore
        XP, the new streak and the bonus.

    Raises
    ------
    KeyError
        If `level` is not a card level (a bug: decks are validated on load).
    """
    card_xp = CARD_XP[level]
    paying = correct and pays
    new_streak = streak + 1 if paying else 0
    bonus = STREAK_BONUS if paying and new_streak % STREAK_LENGTH == 0 else 0
    return CardScore(xp=card_xp if paying else 0, streak=new_streak, bonus=bonus)
