"""The content of every deck file: its format, the answer-length tells, and every claim its snippets make."""

import subprocess
from pathlib import Path

import pytest
from termlab import snippets

from firstcommit import cards, gitcmd
from game_words import unpaired

MAX_EXTRA_LENGTH = 15
AUTHOR = gitcmd.Person("Sam Lee", "sam@example.com")
DATE = "2026-01-15T09:00:00+00:00"
PATH = "/usr/local/bin:/usr/bin:/bin"
TERMINAL_CONFIG = "[log]\n\tdecorate = short\n"
"""
Git settings that make snippets print what a terminal shows.

``log.decorate`` defaults to ``auto``: ``short`` on a terminal, no decorations otherwise
(git-config(1)), so without it ``git log --oneline`` would lose its ``(HEAD -> main)``.
"""
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


def environment(home: Path) -> dict[str, str]:
    """
    Create the home folder of a snippet and give its whole, fixed environment.

    This is the one definition of the environment "predict" cards and "verify" snippets run
    in: a minimal ``PATH``, the C locale, a dumb terminal (so git never opens an editor or a
    pager), UTC, git's global configuration in ``home`` holding
    `firstcommit.gitcmd.BASE_CONFIG` then `TERMINAL_CONFIG`, no system configuration, and a
    fixed author, committer and date, so commit hashes are the same on every run. Git never
    looks for a repository in or above the folder that holds ``home``.

    ``GIT_MERGE_AUTOEDIT=yes`` makes ``git merge`` and ``git pull`` want an editor for a merge
    commit, as they do on a terminal, and ``GIT_EDITOR=false`` (which comes before the base
    configuration's ``core.editor``) makes that editor fail, so a snippet has to write
    ``--no-edit`` or ``-m``, the way levels and cards are written.

    Run the code in a new folder next to ``home`` or inside it, never in ``home`` itself, where
    the configuration file would show up as an untracked file.

    Parameters
    ----------
    home : Path
        The home folder to create; its parent must exist.

    Returns
    -------
    dict[str, str]
        Every variable of the environment; nothing is meant to be inherited.

    Raises
    ------
    FileExistsError
        If ``home`` already exists.
    """
    home.mkdir()
    (home / ".gitconfig").write_text(gitcmd.BASE_CONFIG + TERMINAL_CONFIG)
    return {
        "PATH": PATH,
        "HOME": str(home),
        "LC_ALL": "C",
        "TERM": "dumb",
        "TZ": "UTC",
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": str(home.parent),
        "GIT_MERGE_AUTOEDIT": "yes",
        "GIT_EDITOR": "false",
        "GIT_AUTHOR_NAME": AUTHOR.name,
        "GIT_AUTHOR_EMAIL": AUTHOR.email,
        "GIT_AUTHOR_DATE": DATE,
        "GIT_COMMITTER_NAME": AUTHOR.name,
        "GIT_COMMITTER_EMAIL": AUTHOR.email,
        "GIT_COMMITTER_DATE": DATE,
    }


def run_snippet(code: str, folder: Path) -> subprocess.CompletedProcess[str]:
    """
    Run a card's snippet with bash in an empty folder, in the fixed `environment`.

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
    env = environment(folder / "home")
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


@pytest.mark.parametrize("chapter", [path.stem for path in DECK_FILES])
@pytest.mark.parametrize("language", ["en", "es"])
def test_a_deck_that_uses_a_game_word_says_once_what_it_really_is(chapter: str, language: str) -> None:
    deck = cards.deck(chapter, language)  # type: ignore[arg-type]
    texts = [deck.notes, *(field for card in deck.cards for field in (card.prompt, card.explain, card.correct, *card.wrong))]
    assert unpaired("\n".join(texts), language) == []
