"""
Run git for the game, kept apart from the player's own Git settings.

The game's own git commands and the shell it gives the player share three variables
(`isolation`): git reads only the game's global configuration file, skips the system one, and
never looks for a repository above the labs folder. A player's credential helpers, aliases,
``push.autoSetupRemote`` or a repository in their home folder can therefore never change what a
level does.

`run_on_terminal` runs a command as the player's terminal would show it, for the playground's
buttons; `as_on_terminal` applies carriage returns as a terminal does, for it and the lessons.
"""

import errno
import os
import pty
import select
import signal
import subprocess
import termios
import time
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

NO_PROGRAMS = {"core.fsmonitor": "false", "core.hooksPath": "/dev/null", "log.showSignature": "false"}
"""
Settings that keep the game's own git commands from running programs a repository names.

They go in as ``GIT_CONFIG_COUNT`` entries, which outrank every configuration file (git(1)), so
the snapshot polled every 1.5 s never starts a file system monitor, a hook or a signature
program from a lab's ``.git/config``. The player's shell keeps the repository's settings.
"""

PLAYER = Person("Cadet", "cadet@example.com")
"""The player's identity until they set their own (the "Your real setup" chapter teaches ``git config``)."""

BASE_CONFIG = (
    "[init]\n\tdefaultBranch = main\n[core]\n\tpager = less -FRX\n\teditor = true\n\texcludesFile =\n\tattributesFile =\n"
    f"[user]\n\tname = {PLAYER.name}\n\temail = {PLAYER.email}\n\tuseConfigOnly = true\n"
)
"""
The game's global git configuration when it starts: the player's shell and the lessons share it.

``core.pager`` is what git uses when ``LESS`` is unset (git-config(1), core.pager): short output
is printed without stopping in the pager, whatever ``LESS`` the player's shell sets.
``core.excludesFile`` and ``core.attributesFile`` are empty, so git does not read the player's
personal ignore and attributes files (``~/.config/git/ignore`` and ``attributes``, which it reads
by default even when ``GIT_CONFIG_GLOBAL`` names another file): a lab shows the same files on
every machine. A chapter that teaches a global ignore file sets ``core.excludesFile`` itself.
``core.editor = true`` means no editor ever opens for the player, whatever their ``EDITOR`` or
``VISUAL`` (git-var(1): ``core.editor`` comes before both): a bare ``git commit`` stops with an
empty message and commits nothing, while ``git merge``, a merging ``git pull``, ``git revert`` and
``git commit --no-edit`` keep the message git prepared.
``user.name`` and ``user.email`` sign the player's commits as `PLAYER`, so the first commit is
about the staging area, not about an identity; the player's own ``git config --global`` replaces
them. ``user.useConfigOnly`` makes a commit without a configured name or email stop with the same
message on every machine, ``EMAIL`` ignored, instead of using a guessed address built from the
login and host names: no machine-dependent identity, and no login or host name in a pushed
commit.
"""

PLAYER_SETTINGS = {"core.editor": "true"}
"""
Settings every git the game starts keeps, the player's shell included, whatever its configuration
files say: no editor ever opens (`BASE_CONFIG` explains why). As ``GIT_CONFIG_COUNT`` entries
they reach a game home whose configuration is older than the setting, and outrank a
``git config --global core.editor`` the player runs.
"""

TERMINAL_SETTINGS = {**NO_PROGRAMS, "color.ui": "never"}
"""Settings of `run_on_terminal`: `NO_PROGRAMS` and no colours, as ``GIT_CONFIG_COUNT`` entries that outrank every configuration file."""


def ensure_config() -> Path:
    """
    Create the game's global git configuration if it is missing, and sign an older one as `PLAYER`.

    A configuration made before the game set an identity has neither ``user.name`` nor
    ``user.email``; both are added to it, once. One that has either is left as it is, so a name
    the player set is never replaced.

    Returns
    -------
    Path
        The configuration file.
    """
    path = save.ensure_gitconfig(BASE_CONFIG)
    unsigned = all(run(path.parent, "config", "--file", str(path), "--get", key).returncode != 0 for key in ("user.name", "user.email"))
    if unsigned:
        output(path.parent, "config", "--file", str(path), "user.name", PLAYER.name)
        output(path.parent, "config", "--file", str(path), "user.email", PLAYER.email)
    return path


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
        ``GIT_CONFIG_GLOBAL``, ``GIT_CONFIG_NOSYSTEM``, ``GIT_CEILING_DIRECTORIES`` (the labs
        folder and the lessons folder, where `firstcommit.demos` runs lessons), and
        `PLAYER_SETTINGS` as ``GIT_CONFIG_COUNT`` entries.
    """
    return {
        "GIT_CONFIG_GLOBAL": str(home / save.GITCONFIG_FILE),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": f"{home / save.LABS_FOLDER}:{home / save.LESSONS_FOLDER}",
        **config_entries(PLAYER_SETTINGS),
    }


def config_entries(settings: Mapping[str, str]) -> dict[str, str]:
    """
    Write settings as ``GIT_CONFIG_COUNT`` entries, which outrank every configuration file (git(1)).

    Parameters
    ----------
    settings : Mapping[str, str]
        Setting names and values, such as ``{"core.editor": "true"}``.

    Returns
    -------
    dict[str, str]
        ``GIT_CONFIG_COUNT`` and a ``GIT_CONFIG_KEY_<n>`` and ``GIT_CONFIG_VALUE_<n>`` per setting.
    """
    entries = {"GIT_CONFIG_COUNT": str(len(settings))}
    for index, (key, value) in enumerate(settings.items()):
        entries[f"GIT_CONFIG_KEY_{index}"] = key
        entries[f"GIT_CONFIG_VALUE_{index}"] = value
    return entries


def shell_environment(base: Mapping[str, str], home: Path) -> dict[str, str]:
    """
    Build the environment of a shell the game gives the player (the page's terminal, ``firstcommit shell``).

    Every inherited ``GIT_*`` variable is dropped first, so a ``GIT_DIR`` or ``GIT_INDEX_FILE``
    set around the server cannot redirect the player's commands; then git is kept to the game's
    configuration and labs. Everything else is kept; the player's ``EDITOR`` and ``VISUAL`` stay
    too, though the game's ``core.editor`` comes first (`BASE_CONFIG`).

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
        `shell_environment`, plus the identity, the C locale (so output can be parsed),
        `NO_PROGRAMS`, no optional locks (the page checks the lab while the player types, and a ``git status``
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
    env.update(config_entries({**PLAYER_SETTINGS, **NO_PROGRAMS}))
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


def run_on_terminal(cwd: Path, *args: str) -> tuple[int, str]:
    """
    Run one git command as the player's terminal would, and give what the terminal would show.

    Git's standard output and error both go to a pseudo-terminal, so git behaves as it does for
    the player (progress lines, the order of its lines: through a pipe git holds its standard
    output back, so a refused ``git pull`` prints ``Updating`` after ``Aborting``). The command
    runs with the player's shell environment (`shell_environment`), so no author variable is
    set and the configured identity applies, plus the C locale (so the output can be read
    back), a dumb terminal (no escape sequences), no colours, ``cat`` as the pager and no
    editor (the message git suggests is kept, as when the player closes the editor unchanged).
    Nothing can wait for an answer: standard input is empty, git's terminal prompts are off and
    the command has no controlling terminal. As in `run`, git starts as ``git -C <cwd>`` from
    ``/``, and its output is decoded as UTF-8 with undecodable bytes replaced.

    The command is the game's, even when the player chose it, so it runs no program a
    repository names (`NO_PROGRAMS`), and a hook that hangs cannot turn it into a timeout. The
    cost: hooks a player installs run in their terminal but not here; no level teaches hooks.

    Parameters
    ----------
    cwd : Path
        Folder to run in. It may not exist.
    *args : str
        Arguments after ``git``.

    Returns
    -------
    tuple[int, str]
        Git's exit status, and its output as a terminal shows it (`as_on_terminal`).

    Raises
    ------
    subprocess.TimeoutExpired
        If the command runs longer than `TIMEOUT` seconds; it is stopped first, with every
        process it started.
    """
    env = shell_environment(os.environ, save.home())
    env.update({"LC_ALL": "C", "TERM": "dumb", "GIT_PAGER": "cat", "GIT_EDITOR": ":", "GIT_TERMINAL_PROMPT": "0"})
    env.update(config_entries({**PLAYER_SETTINGS, **TERMINAL_SETTINGS}))
    deadline = time.monotonic() + TIMEOUT
    controller, terminal = pty.openpty()
    modes = termios.tcgetattr(terminal)
    modes[1] &= ~termios.ONLCR  # keep git's "\n" instead of the "\r\n" a terminal sends to the screen
    termios.tcsetattr(terminal, termios.TCSANOW, modes)
    try:
        process = subprocess.Popen(
            ["git", "-C", str(cwd), *args],
            cwd="/",
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=terminal,
            stderr=terminal,
            start_new_session=True,
        )
    finally:
        os.close(terminal)
    try:
        printed = _read_to_the_end(controller, process, deadline)
        status = process.wait()
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise
    finally:
        os.close(controller)
    return status, as_on_terminal(printed.decode("utf-8", "replace"))


def _read_to_the_end(controller: int, process: subprocess.Popen[bytes], deadline: float) -> bytes:
    """
    Read what a command prints to a pseudo-terminal until every process holding it has closed it.

    Parameters
    ----------
    controller : int
        The pseudo-terminal's controlling end.
    process : subprocess.Popen[bytes]
        The command, for the timeout's message.
    deadline : float
        When to give up, on the `time.monotonic` clock.

    Returns
    -------
    bytes
        Everything printed.

    Raises
    ------
    subprocess.TimeoutExpired
        If the deadline passes first.
    """
    printed = bytearray()
    chunk = b"started"
    while chunk:
        ready, _, _ = select.select([controller], [], [], max(deadline - time.monotonic(), 0))
        if not ready:
            raise subprocess.TimeoutExpired(process.args, TIMEOUT)
        try:
            chunk = os.read(controller, 65536)
        except OSError as error:
            # Linux reports a pseudo-terminal whose other end is closed as EIO, not as an empty read.
            if error.errno != errno.EIO:
                raise
            chunk = b""
        printed += chunk
    return bytes(printed)


def as_on_terminal(output: str) -> str:
    """
    Apply carriage returns as a terminal does.

    A carriage return sends the cursor back to the start of the line, so later text overwrites
    earlier text; progress counters (``Rebasing (1/1)``) leave only their last state.

    Parameters
    ----------
    output : str
        What a command printed.

    Returns
    -------
    str
        What stays on the screen. Lines without a carriage return are unchanged; the others
        lose the spaces left at their end.
    """
    shown_lines = []
    for line in output.split("\n"):
        shown = ""
        for part in line.split("\r"):
            shown = part + shown[len(part) :]
        shown_lines.append(shown.rstrip(" ") if "\r" in line else shown)
    return "\n".join(shown_lines)


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
