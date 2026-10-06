"""
Run git for the game, kept apart from the player's own Git settings.

The game's own git commands and the shell it gives the player share three variables
(`isolation`): git reads only the game's global configuration file, skips the system one, and
never looks for a repository above the labs folder. A player's credential helpers, aliases,
``push.autoSetupRemote`` or a repository in their home folder can therefore never change what a
level does.
"""

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from firstcommit import save

TIMEOUT = 30.0


@dataclass(frozen=True)
class Person:
    """An author or committer of the commits a level builds."""

    name: str
    email: str


GAME = Person("First Commit", "game@example.com")

BASE_CONFIG = "[init]\n\tdefaultBranch = main\n"
"""The game's global git configuration when it starts: the player's shell and the lessons share it."""


def isolation(home: Path) -> dict[str, str]:
    """
    Give the variables that keep git to the game's own configuration and labs.

    Parameters
    ----------
    home : Path
        The game's home folder.

    Returns
    -------
    dict[str, str]
        ``GIT_CONFIG_GLOBAL``, ``GIT_CONFIG_NOSYSTEM`` and ``GIT_CEILING_DIRECTORIES``.
    """
    return {
        "GIT_CONFIG_GLOBAL": str(home / "gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": str(home / "labs"),
    }


def shell_environment(base: Mapping[str, str], home: Path) -> dict[str, str]:
    """
    Build the environment of a shell the game gives the player (the page's terminal, ``firstcommit shell``).

    Every inherited ``GIT_*`` variable is dropped first, so a ``GIT_DIR`` or ``GIT_INDEX_FILE``
    set around the server cannot redirect the player's commands; then git is kept to the game's
    configuration and labs. Everything else, such as the player's editor, is kept.

    Parameters
    ----------
    base : Mapping[str, str]
        The environment to start from.
    home : Path
        The game's home folder.

    Returns
    -------
    dict[str, str]
        ``base`` without its git variables, plus `isolation`.
    """
    env = {key: value for key, value in base.items() if not key.startswith("GIT_")}
    env.update(isolation(home))
    return env


def environment(base: Mapping[str, str], home: Path, author: Person, when: str | None) -> dict[str, str]:
    """
    Build the environment of one game git command: the player's shell environment, made fit for a program.

    Parameters
    ----------
    base : Mapping[str, str]
        The environment to start from, usually the server's.
    home : Path
        The game's home folder.
    author : Person
        Author and committer of any commit the command makes.
    when : str | None
        Author and committer date in a format git accepts (ISO 8601 is safest), or None for now.

    Returns
    -------
    dict[str, str]
        `shell_environment`, plus the identity, the C locale (so output can be parsed), no
        optional locks (the page checks the lab while the player types, and a ``git status``
        that refreshed the index would hold ``index.lock`` and make the player's own command
        fail), no prompts and no editor.
    """
    env = shell_environment(base, home)
    env.update(
        {
            "LC_ALL": "C",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_EDITOR": "true",
            "GIT_AUTHOR_NAME": author.name,
            "GIT_AUTHOR_EMAIL": author.email,
            "GIT_COMMITTER_NAME": author.name,
            "GIT_COMMITTER_EMAIL": author.email,
        }
    )
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    return env


def run(
    cwd: Path, *args: str, author: Person = GAME, when: str | None = None, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    """
    Run one git command for the game and return its result, whatever its exit status.

    Use it when failing is an expected outcome, such as resolving a name that may not exist.
    Git is started as ``git -C <cwd>`` from ``/``, so a folder the player deleted gives git's own
    failure (exit status 128) instead of an exception. Output is decoded as UTF-8 with
    undecodable bytes replaced, so file names a player invents can always be shown.

    Parameters
    ----------
    cwd : Path
        Folder to run in; relative paths in ``args`` resolve there. It may not exist.
    *args : str
        Arguments after ``git``.
    author : Person
        Author and committer of any commit the command makes.
    when : str | None
        Commit date, or None for now.
    stdin : str | None
        Text for the command's input, or None for no input.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Exit status, standard output and standard error.

    Raises
    ------
    subprocess.TimeoutExpired
        If git runs longer than `TIMEOUT` seconds.
    """
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        cwd="/",
        env=environment(os.environ, save.home(), author, when),
        input=stdin if stdin is not None else "",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT,
        check=False,
    )


def output(cwd: Path, *args: str, author: Person = GAME, when: str | None = None, stdin: str | None = None) -> str:
    """
    Run one git command that must succeed, and return its standard output.

    Parameters
    ----------
    cwd : Path
        Folder to run in.
    *args : str
        Arguments after ``git``.
    author : Person
        Author and committer of any commit the command makes.
    when : str | None
        Commit date, or None for now.
    stdin : str | None
        Text for the command's input, or None for no input.

    Returns
    -------
    str
        Standard output.

    Raises
    ------
    subprocess.CalledProcessError
        If git exits with a non-zero status (a bug in the level or the game).
    """
    result = run(cwd, *args, author=author, when=when, stdin=stdin)
    result.check_returncode()
    return result.stdout
