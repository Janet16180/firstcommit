"""
Every player action, in one place: the only module the command line and the web routes call.

Each function reads and changes the save under one lock (termlab's store) and returns a plain
record that is ready to send as JSON. Text fields are parsed into blocks (`firstcommit.markup`),
so the interfaces only render. Game rules never live in the interfaces (Ring Zero audit ARCH-1).

Records returned here are the API contract of the web routes: changing a field is a change to
the page too.
"""

from typing import Literal, TypedDict

from firstcommit.cards import CardKind
from firstcommit.changes import Event
from firstcommit.demos import Line
from firstcommit.markup import Block
from firstcommit.repomap import Snapshot
from firstcommit.save import Payout


class LevelSummary(TypedDict):
    """A level as the map of chapters lists it."""

    id: str
    title: str
    difficulty: int
    xp: int
    done: bool
    has_lesson: bool
    has_quest: bool


class ChapterSummary(TypedDict):
    """A chapter and its levels, in play order."""

    id: str
    title: str
    levels: list[LevelSummary]
    cards: int


class Rank(TypedDict):
    """The player's rank: its title, the XP it starts at, and the next rank (None at the top)."""

    title: str
    floor: int
    next_title: str | None
    next_at: int | None


class ActiveView(TypedDict):
    """The level being played: how far the quest is, and the hints and attempts used."""

    level: str
    step: int
    steps: int
    hints: int
    hints_total: int
    attempts: int
    started: str


class Status(TypedDict):
    """The dashboard."""

    xp: int
    rank: Rank
    chapters: list[ChapterSummary]
    active: ActiveView | None
    last_payout: Payout | None
    cards_due: int


class StepView(TypedDict):
    """A guided-quest step as the page shows it (its checks stay on the server)."""

    id: str
    kind: Literal["answer", "watch", "read"]
    text: list[Block]
    command: str
    question: str
    placeholder: str


class LevelView(TypedDict):
    """A level's page: what to do, the quest steps and how many hints exist."""

    id: str
    chapter: str
    chapter_title: str
    title: str
    difficulty: int
    xp: int
    briefing: list[Block]
    steps: list[StepView]
    hints_total: int
    has_lesson: bool


class SlideView(TypedDict):
    """One lesson slide with its figure."""

    id: str
    title: str
    text: list[Block]
    view: Literal["map", "areas", "objects", "terminal", "none"]
    transcript: list[Line]
    map: Snapshot


class LessonView(TypedDict):
    """A level's lesson."""

    level: str
    title: str
    slides: list[SlideView]


class StepResult(TypedDict):
    """The result of a quest step: right or not, feedback, and where the quest stands now."""

    correct: bool
    message: list[Block]
    step: int
    quest_done: bool


class CheckResult(TypedDict):
    """The result of checking the level; ``payout`` and ``debrief`` are set once it is solved."""

    solved: bool
    message: list[Block]
    payout: Payout | None
    debrief: list[Block] | None


class HintView(TypedDict):
    """A revealed hint, how many are used out of how many, and what this one cost."""

    hint: list[Block]
    used: int
    total: int
    cost: int


class Observation(TypedDict):
    """The live lab: the player's repository, the stand-in GitHub (if the level has one), and what changed."""

    level: str
    project: Snapshot
    github: Snapshot | None
    events: list[Event]


class CardView(TypedDict):
    """A flashcard to answer. Choices are shuffled on the server; the right answer is not sent."""

    id: str
    chapter: str
    kind: CardKind
    level: int
    prompt: list[Block]
    code: str
    choices: list[str]
    placeholder: str
    pays: bool


class CardResult(TypedDict):
    """The result of answering a card."""

    correct: bool
    answer: str
    explain: list[Block]
    xp: int
    streak: int
    bonus: int


class Notes(TypedDict):
    """A chapter's cheat sheet."""

    chapter: str
    title: str
    notes: list[Block]


def status() -> Status:
    """Give the dashboard."""
    raise NotImplementedError


def level(level_id: str) -> LevelView:
    """Give a level's page (raises KeyError for an unknown id)."""
    raise NotImplementedError


def lesson(level_id: str) -> LessonView:
    """Give a level's lesson with its figures (raises KeyError for an unknown id)."""
    raise NotImplementedError


def start(level_id: str) -> ActiveView:
    """Start a level in a fresh lab, ending any level in progress (raises KeyError for an unknown id)."""
    raise NotImplementedError


def quest_step(answer: str | None) -> StepResult:
    """Check the current quest step: an answer step with ``answer``, a watch step with None."""
    raise NotImplementedError


def check(answer: str | None, auto: bool) -> CheckResult:
    """Check the level; an automatic check (the page polling) never counts as an attempt."""
    raise NotImplementedError


def hint() -> HintView:
    """Reveal the next hint of the level in progress."""
    raise NotImplementedError


def observe() -> Observation:
    """Snapshot the lab of the level in progress and tell what changed since the last observation."""
    raise NotImplementedError


def abort() -> str | None:
    """End the level in progress and remove its lab; give its id, or None if none was in progress."""
    raise NotImplementedError


def reset() -> None:
    """End the level in progress and erase all progress."""
    raise NotImplementedError


def due_cards(chapter: str | None, limit: int) -> list[CardView]:
    """Give up to ``limit`` cards to review: due ones first, then new ones."""
    raise NotImplementedError


def answer_card(card_id: str, reply: str) -> CardResult:
    """Judge a reply to a card, reschedule it and pay XP if it was new or due (raises KeyError for an unknown id)."""
    raise NotImplementedError


def notes(chapter: str) -> Notes:
    """Give a chapter's cheat sheet (raises KeyError for an unknown chapter)."""
    raise NotImplementedError


def terminal_folder() -> str:
    """Give the folder the page's terminal opens in: the lab's project, else the lab, else the player's home."""
    raise NotImplementedError
