"""The content of every deck file: its format, the answer-length tells, and every claim its snippets make."""

import subprocess
from pathlib import Path

import pytest
from termlab import snippets

from firstcommit import cards, demos

MAX_EXTRA_LENGTH = 15
DECK_FILES = sorted(path for path in cards.DECKS.glob("*.toml") if not path.name.endswith(f"{cards.SPANISH_SUFFIX}.toml"))


def valid_decks() -> list[cards.Deck]:
    """
    Load every deck file that loads; a broken one fails `test_every_deck_file_is_valid` instead.

    Returns
    -------
    list[cards.Deck]
        The decks, in file name order.
    """
    decks = []
    for path in DECK_FILES:
        try:
            decks.append(cards.load_deck(path))
        except ValueError:
            continue
    return decks


DECKS = valid_decks()
ALL_CARDS = [card for deck in DECKS for card in deck.cards]
CHOICE_CARDS = [card for card in ALL_CARDS if card.kind == "choice"]
PREDICT_CARDS = [card for card in ALL_CARDS if card.kind == "predict"]
VERIFIED_CARDS = [card for card in ALL_CARDS if card.verify]


def ids(entries: list[cards.Card]) -> list[str]:
    """
    Name parametrized cases after their cards.

    Parameters
    ----------
    entries : list[cards.Card]
        The cards.

    Returns
    -------
    list[str]
        Their ids.
    """
    return [card.id for card in entries]


def run_snippet(code: str, folder: Path) -> subprocess.CompletedProcess[str]:
    """
    Run a card's snippet with bash in an empty folder, in the fixed environment of the lessons.

    Parameters
    ----------
    code : str
        The snippet.
    folder : Path
        An empty folder for the snippet's home and its working folder.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Its exit status and output.
    """
    env = demos.environment(folder / "home")
    work = folder / "work"
    work.mkdir()
    return snippets.run(code, work, env)


@pytest.mark.parametrize("path", DECK_FILES, ids=[path.name for path in DECK_FILES])
def test_every_deck_file_is_valid(path: Path) -> None:
    cards.load_deck(path)


@pytest.mark.parametrize("card", CHOICE_CARDS, ids=ids(CHOICE_CARDS))
def test_the_right_option_is_at_most_15_characters_longer_than_the_longest_distractor(card: cards.Card) -> None:
    assert len(card.correct) <= max(len(option) for option in card.wrong) + MAX_EXTRA_LENGTH


@pytest.mark.parametrize("deck", DECKS, ids=[deck.chapter for deck in DECKS])
def test_the_right_option_is_the_longest_in_at_most_half_of_a_decks_choice_cards(deck: cards.Deck) -> None:
    choice_cards = [card for card in deck.cards if card.kind == "choice"]
    longest = [card.id for card in choice_cards if len(card.correct) > max(len(option) for option in card.wrong)]
    assert len(longest) <= len(choice_cards) / 2, f"the right option is the longest in {longest}"


@pytest.mark.parametrize("card", PREDICT_CARDS, ids=ids(PREDICT_CARDS))
def test_a_predict_card_prints_its_right_option(card: cards.Card, tmp_path: Path) -> None:
    result = run_snippet(card.code, tmp_path)
    if result.returncode == snippets.SKIP_STATUS:
        pytest.skip(f"{card.id} cannot be checked on this machine")
    assert result.stdout.rstrip("\n") == card.correct, result.stderr


@pytest.mark.parametrize("card", VERIFIED_CARDS, ids=ids(VERIFIED_CARDS))
def test_a_verify_snippet_holds(card: cards.Card, tmp_path: Path) -> None:
    result = run_snippet(card.verify, tmp_path)
    if result.returncode == snippets.SKIP_STATUS:
        pytest.skip(f"{card.id} cannot be checked on this machine")
    assert result.returncode == 0, result.stdout + result.stderr
