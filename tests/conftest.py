"""Shared test setup: every test gets its own game home, so no test touches the player's ~/.firstcommit."""

from collections.abc import Iterator
from pathlib import Path

import pytest


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
