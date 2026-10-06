"""Shared test setup: every test gets its own game home, so no test touches the player's ~/.firstcommit; plus the sample level (also with a two-person playground) and decks."""

import dataclasses
from collections.abc import Iterator
from pathlib import Path

import pytest

from firstcommit import cards, kit, runner
from sample_levels import basics_sample


@pytest.fixture(autouse=True)
def game_home(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """
    Point ``FIRSTCOMMIT_HOME`` at a fresh folder for one test.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Pytest's temporary folder factory.
    monkeypatch : pytest.MonkeyPatch
        Pytest's environment patcher.

    Yields
    ------
    Path
        The test's game home (created, empty).
    """
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(home))
    yield home


@pytest.fixture
def sample_level(monkeypatch: pytest.MonkeyPatch) -> runner.Level:
    """
    Make the game's catalogue hold only the sample level of ``tests/sample_levels``.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.

    Returns
    -------
    runner.Level
        The sample level, ``basics-sample``.
    """
    level = runner.load(basics_sample)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    return level



def playground_setup(lab: kit.Lab) -> kit.State:
    """
    Set a lab up as the two-person playground, as a level with one does.

    Parameters
    ----------
    lab : kit.Lab
        The empty lab.

    Returns
    -------
    kit.State
        The branch name.
    """
    kit.setup_playground(lab)
    return {"branch": "main"}


@pytest.fixture
def playground_level(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch) -> runner.Level:
    """
    Make the game's catalogue hold only the sample level, its lab set up as the two-person playground.

    Parameters
    ----------
    sample_level : runner.Level
        The sample level.
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.

    Returns
    -------
    runner.Level
        The sample level with `playground_setup` as its setup.
    """
    level = dataclasses.replace(sample_level, setup=playground_setup)
    monkeypatch.setattr(runner, "catalogue", lambda: {level.id: level})
    return level


CHOICE_CARDS = 10


def choice_card(card_id: str) -> str:
    """
    Write a level-1 choice card whose right option is ``right``.

    Parameters
    ----------
    card_id : str
        The card's id.

    Returns
    -------
    str
        Its TOML table.
    """
    return f"""
[[card]]
id = "{card_id}"
kind = "choice"
level = 1
prompt = "Which one is `right`?"
correct = "right"
wrong = ["wrong", "worse"]
explain = "Because it is."
source = "test"
"""


@pytest.fixture
def sample_decks(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Point the decks at test decks: ``basics`` with `CHOICE_CARDS` choice cards, a predict and a text card, and ``hash`` with one card.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Pytest's temporary folder factory.
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.

    Returns
    -------
    Path
        The deck folder.
    """
    folder = tmp_path_factory.mktemp("decks")
    basics = 'notes = """\nThe `three` areas.\n"""\n' + "".join(choice_card(f"basics-c{number:02}") for number in range(1, CHOICE_CARDS + 1))
    basics += """
[[card]]
id = "basics-predict"
kind = "predict"
level = 2
prompt = "What does it print?"
code = "echo hi"
correct = "hi"
wrong = ["ho", "ha"]
explain = "It echoes."
source = "bash(1)"

[[card]]
id = "basics-text"
kind = "text"
level = 3
prompt = "Name the default branch."
accept = ["main"]
placeholder = "a branch"
explain = "The game sets it."
source = "git-init(1)"
"""
    (folder / "basics.toml").write_text(basics)
    (folder / "hash.toml").write_text(choice_card("hash-c01"))
    monkeypatch.setattr(cards, "DECKS", folder)
    return folder
