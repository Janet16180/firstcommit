"""
Flashcards: loading and validating the decks, the Leitner schedule, and judging an answer. No printing.

A chapter's deck is ``content/cards/<chapter>.toml`` (AUTHORING.md section 4). Decks are content
written by people, so every card is checked when its deck is read: a broken card is a bug in the
content and raises with the file, the card and the field.
"""

import functools
import random
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal, cast

from firstcommit import score
from firstcommit.chapters import CHAPTERS
from firstcommit.save import CardEntry

CardKind = Literal["choice", "text", "predict"]

DECKS = Path(__file__).parent / "content" / "cards"
KINDS: tuple[CardKind, ...] = ("choice", "text", "predict")
LEVELS = tuple(score.CARD_XP)
"""Card levels: exactly the levels the scoring pays for (`firstcommit.score.CARD_XP`)."""
MIN_WRONG = 2
MAX_WRONG = 5
INTERVALS = (0, 1, 3, 7, 16, 35)
"""Days until a card in Leitner box N is due again."""

COMMON_FIELDS = {"id", "kind", "level", "prompt", "explain", "source"}
KIND_FIELDS: dict[CardKind, set[str]] = {
    "choice": {"correct", "wrong"},
    "predict": {"code", "correct", "wrong"},
    "text": {"accept"},
}
OPTIONAL_FIELDS: dict[CardKind, set[str]] = {"choice": {"verify"}, "predict": {"verify"}, "text": {"verify", "placeholder"}}
DECK_KEYS = {"notes", "card"}


@dataclass(frozen=True)
class Card:
    """
    One flashcard, as validated from its deck.

    Fields a kind does not use are empty: ``correct`` and ``wrong`` belong to choice and predict
    cards, ``code`` to predict cards, ``accept`` and ``placeholder`` to text cards.
    """

    id: str
    chapter: str
    kind: CardKind
    level: int
    prompt: str
    explain: str
    source: str
    verify: str = ""
    correct: str = ""
    wrong: tuple[str, ...] = ()
    code: str = ""
    accept: tuple[str, ...] = ()
    placeholder: str = ""


@dataclass(frozen=True)
class Deck:
    """A chapter's cards and its cheat sheet."""

    chapter: str
    notes: str
    cards: tuple[Card, ...]


def deck(chapter: str) -> Deck:
    """
    Load a chapter's deck from `DECKS`.

    Parameters
    ----------
    chapter : str
        A chapter id.

    Returns
    -------
    Deck
        The deck; empty when the chapter has no deck file yet.

    Raises
    ------
    KeyError
        If `chapter` is not a chapter id.
    ValueError
        If the deck file is broken.
    """
    if chapter not in CHAPTERS:
        raise KeyError(chapter)
    path = DECKS / f"{chapter}.toml"
    return load_deck(path) if path.exists() else Deck(chapter, "", ())


def find(card_id: str) -> Card:
    """
    Look a card up by its id.

    Parameters
    ----------
    card_id : str
        ``<chapter>-<slug>``.

    Returns
    -------
    Card
        The card.

    Raises
    ------
    KeyError
        If no deck holds a card with this id.
    """
    chapter = card_id.split("-", 1)[0]
    matches = [card for card in deck(chapter).cards if card.id == card_id] if chapter in CHAPTERS else []
    if not matches:
        raise KeyError(card_id)
    return matches[0]


@functools.cache
def load_deck(path: Path) -> Deck:
    """
    Read and validate one deck file, once per process (decks ship with the game, like its levels).

    Parameters
    ----------
    path : Path
        ``<chapter>.toml``.

    Returns
    -------
    Deck
        Its notes and cards, in file order.

    Raises
    ------
    ValueError
        If the file is not named after a chapter, is not valid TOML, has unknown keys, or holds a
        broken card; the message names the file (and the card and field).
    """
    chapter = path.stem
    if chapter not in CHAPTERS:
        raise ValueError(f"{path}: the file name must be a chapter id, one of {', '.join(CHAPTERS)}")
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"{path}: not valid TOML: {error}") from error
    unknown = sorted(set(data) - DECK_KEYS)
    entries = data.get("card", [])
    notes = data.get("notes", "")
    if unknown:
        raise ValueError(f"{path}: `{unknown[0]}` is not a key of a deck (only `notes` and `[[card]]`)")
    if not isinstance(notes, str):
        raise ValueError(f"{path}: `notes` must be text")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError(f"{path}: `card` must be a list of [[card]] tables")
    loaded: list[Card] = []
    for number, entry in enumerate(entries, start=1):
        problem = _card_problem(entry, chapter)
        if problem is None and any(other.id == entry["id"] for other in loaded):
            problem = f"the id `{entry['id']}` is used twice"
        if problem is not None:
            raise ValueError(f"{path}: card {number} ({entry.get('id', 'no id')}): {problem}")
        loaded.append(_card(entry, chapter))
    return Deck(chapter, notes, tuple(loaded))


def _card_problem(entry: dict[str, Any], chapter: str) -> str | None:
    """
    Find what is wrong with one card table, if anything.

    Parameters
    ----------
    entry : dict[str, Any]
        The ``[[card]]`` table.
    chapter : str
        The deck's chapter id.

    Returns
    -------
    str | None
        The first problem found, naming the field, or None for a valid card.
    """
    kind = entry.get("kind")
    if kind not in KINDS:
        return f"`kind` must be one of {', '.join(KINDS)}, not {kind!r}"
    allowed = COMMON_FIELDS | KIND_FIELDS[kind] | OPTIONAL_FIELDS[kind]
    unknown = sorted(set(entry) - allowed)
    missing = sorted((COMMON_FIELDS | KIND_FIELDS[kind]) - set(entry))
    texts = sorted(field for field in allowed - {"kind", "level", "wrong", "accept"} if field in entry)
    bad_texts = [field for field in texts if not isinstance(entry[field], str) or not entry[field].strip()]
    problem = None
    if unknown:
        problem = f"`{unknown[0]}` is not a field of a {kind} card"
    elif missing:
        problem = f"`{missing[0]}` is missing"
    elif not isinstance(entry["id"], str) or not entry["id"].startswith(f"{chapter}-") or entry["id"] == f"{chapter}-":
        problem = f"`id` must start with `{chapter}-` and name the card"
    elif not isinstance(entry["level"], int) or isinstance(entry["level"], bool) or entry["level"] not in LEVELS:
        problem = f"`level` must be one of {LEVELS}"
    elif bad_texts:
        problem = f"`{bad_texts[0]}` must be text that is not empty"
    elif "`" in entry.get("placeholder", ""):
        problem = "`placeholder` is plain text: no backticks"
    elif kind == "text":
        problem = _list_problem(entry["accept"], "accept", 1, None)
    else:
        problem = _list_problem(entry["wrong"], "wrong", MIN_WRONG, MAX_WRONG)
        if problem is None and entry["correct"] in entry["wrong"]:
            problem = "`wrong` must not contain the right option"
    return problem


def _list_problem(value: Any, field: str, least: int, most: int | None) -> str | None:
    """
    Check a list of distinct, non-empty strings of a bounded length.

    Parameters
    ----------
    value : Any
        The field's value.
    field : str
        Its name, for the message.
    least : int
        Fewest items.
    most : int | None
        Most items, or None for no limit.

    Returns
    -------
    str | None
        The problem, or None if the list is valid.
    """
    bounds = f"at least {least}" if most is None else f"{least} to {most}"
    problem = None
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        problem = f"`{field}` must be a list of texts that are not empty"
    elif len(value) < least or (most is not None and len(value) > most):
        problem = f"`{field}` must hold {bounds} items, not {len(value)}"
    elif len(set(value)) != len(value):
        problem = f"`{field}` holds the same text twice"
    return problem


def _card(entry: dict[str, Any], chapter: str) -> Card:
    """
    Build a card from a valid card table.

    Parameters
    ----------
    entry : dict[str, Any]
        A ``[[card]]`` table that `_card_problem` accepted.
    chapter : str
        The deck's chapter id.

    Returns
    -------
    Card
        The card.
    """
    return Card(
        id=entry["id"],
        chapter=chapter,
        kind=cast(CardKind, entry["kind"]),
        level=entry["level"],
        prompt=entry["prompt"],
        explain=entry["explain"],
        source=entry["source"],
        verify=entry.get("verify", ""),
        correct=entry.get("correct", ""),
        wrong=tuple(entry.get("wrong", ())),
        code=entry.get("code", ""),
        accept=tuple(entry.get("accept", ())),
        placeholder=entry.get("placeholder", ""),
    )


def is_due(entry: CardEntry | None, today: date) -> bool:
    """
    Tell whether a card should be asked, and so pays XP, today.

    Parameters
    ----------
    entry : CardEntry | None
        The card's place in the schedule, or None if it was never answered.
    today : date
        The player's date.

    Returns
    -------
    bool
        True for a new card and for a card whose due date has come.
    """
    return entry is None or date.fromisoformat(entry["due"]) <= today


def reschedule(entry: CardEntry | None, correct: bool, today: date) -> CardEntry:
    """
    Move a card between Leitner boxes after an answer.

    A right answer moves it up one box (at most the last), which spaces it further out; a
    wrong answer sends it back to box 0, due again today.

    Parameters
    ----------
    entry : CardEntry | None
        Its place in the schedule, or None for a new card.
    correct : bool
        Whether the answer was right.
    today : date
        The player's date.

    Returns
    -------
    CardEntry
        Its new box and due date.
    """
    box = min((entry["box"] if entry else 0) + 1, len(INTERVALS) - 1) if correct else 0
    return {"box": box, "due": (today + timedelta(days=INTERVALS[box])).isoformat()}


def pick(deck_cards: Sequence[Card], entries: Mapping[str, CardEntry], today: date, limit: int, rng: random.Random) -> list[Card]:
    """
    Choose cards to ask: the due ones first, oldest due date first, then new ones, easiest first.

    Cards answered before and not due yet are left out.

    Parameters
    ----------
    deck_cards : Sequence[Card]
        The candidates.
    entries : Mapping[str, CardEntry]
        Schedule entries by card id.
    today : date
        The player's date.
    limit : int
        Most cards to give (zero or more).
    rng : random.Random
        Shuffles new cards of the same level.

    Returns
    -------
    list[Card]
        Cards in the order to ask them.

    Raises
    ------
    ValueError
        If `limit` is negative (a bug in the caller).
    """
    if limit < 0:
        raise ValueError(f"limit must not be negative, got {limit}")
    due = sorted((card for card in deck_cards if card.id in entries and is_due(entries[card.id], today)), key=lambda card: entries[card.id]["due"])
    new = [card for card in deck_cards if card.id not in entries]
    rng.shuffle(new)
    new.sort(key=lambda card: card.level)
    return (due + new)[:limit]


def choices(card: Card, rng: random.Random) -> list[str]:
    """
    Give the options of a choice or predict card in a random order.

    Parameters
    ----------
    card : Card
        The card.
    rng : random.Random
        The shuffle's source.

    Returns
    -------
    list[str]
        The right option and the distractors, shuffled; empty for a text card.
    """
    options = [] if card.kind == "text" else [card.correct, *card.wrong]
    rng.shuffle(options)
    return options


def judge(card: Card, reply: str) -> bool:
    """
    Tell whether a reply to a card is right.

    Parameters
    ----------
    card : Card
        The card.
    reply : str
        A choice card's or predict card's chosen option, or the text a player typed.

    Returns
    -------
    bool
        For choice and predict cards, whether the reply is exactly the right option; for text
        cards, whether it matches an accepted spelling once case and spacing are ignored.
    """
    if card.kind == "text":
        right = normalize(reply) in {normalize(spelling) for spelling in card.accept}
    else:
        right = reply == card.correct
    return right


def normalize(text: str) -> str:
    """
    Reduce a typed answer to what matters for comparison.

    Parameters
    ----------
    text : str
        Raw text.

    Returns
    -------
    str
        Lower-cased (case-folded), with runs of whitespace made one space and the ends trimmed.
    """
    return " ".join(text.casefold().split())


def answer(card: Card) -> str:
    """
    Give the right answer of a card, as shown after a reply.

    Parameters
    ----------
    card : Card
        The card.

    Returns
    -------
    str
        The right option, or a text card's first accepted spelling.
    """
    return card.accept[0] if card.kind == "text" else card.correct
