"""
Lesson figures built from real git.

Each slide shows real commands, their real output, and the repository they leave behind.

A lesson's ``run`` lines (`firstcommit.kit.Slide`) are run in order in an empty temporary
folder with a fixed identity, date and locale and no global configuration, so every hash and
line of output a lesson shows is what git really prints, the same on every run.

The lesson runs in one bash shell, so ``cd``, variables and ``$?`` carry over from line to line
and slide to slide. Its home folder is shown as `SHOWN_HOME` and it starts in the empty folder
``project`` there. After each slide the whole home folder is copied aside, and the slide's
figure is read from the copy once the shell is done.

Lessons run without a terminal, but show what the player's terminal shows: `TERMINAL_CONFIG`
turns on what git only does on a terminal, and carriage returns are applied as a terminal
applies them. Colours, the pager and progress lines stay off.
"""

import copy
import functools
import os
import re
import secrets
import shlex
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from termlab import sandbox, snippets

from firstcommit import gitcmd, repomap, save
from firstcommit.kit import Slide
from firstcommit.repomap import ObjectInfo, Snapshot

AUTHOR = gitcmd.Person("Sam Lee", "sam@example.com")
DATE = "2026-01-15T09:00:00+00:00"
PATH = "/usr/local/bin:/usr/bin:/bin"
SHOWN_HOME = "/home/you"
"""How the lesson's home folder appears in the output, instead of its random temporary path."""
TERMINAL_CONFIG = "[log]\n\tdecorate = short\n"
"""
Git settings that make lessons print what a terminal shows.

``log.decorate`` defaults to ``auto``: ``short`` on a terminal, no decorations otherwise
(git-config(1)), so without it ``git log --oneline`` would lose its ``(HEAD -> main)``.
"""
PROJECT = "project"
MUST_FAIL = "! "
COPY_FAILED = 97
CACHED_LESSONS = 64

# The shell's own status variable and the function that restores $? before each line, so a
# line such as `echo $?` sees the status of the line before it, not of the game's bookkeeping.
PROLOGUE = 'umask 022\n__fc_status() { return "$1"; }\n__fc=0\n'


class Line(TypedDict):
    """One command a slide runs, and what it printed (standard output and error, interleaved)."""

    command: str
    output: str


class Frame(TypedDict):
    """A slide's figure: its commands with their output, and the repository and its objects after them."""

    transcript: list[Line]
    map: Snapshot
    objects: list[ObjectInfo]


@dataclass(frozen=True)
class _Command:
    """One line of a slide: the slide's id, the command as shown, and whether it must fail."""

    slide: str
    text: str
    must_fail: bool


def environment(home: Path) -> dict[str, str]:
    """
    Create the home folder of a lesson or snippet and give its whole, fixed environment.

    This is the one definition of the environment lessons, "predict" cards and "verify"
    snippets run in: a minimal ``PATH``, the C locale, a dumb terminal (so git never opens an
    editor or a pager), UTC, git's global configuration in ``home`` holding
    `firstcommit.gitcmd.BASE_CONFIG` then `TERMINAL_CONFIG`, no system configuration, and a
    fixed author, committer and date, so commit hashes are the same on every run. Git never
    looks for a repository in or above the folder that holds ``home``.

    ``GIT_MERGE_AUTOEDIT=yes`` makes ``git merge`` and ``git pull`` want an editor for a merge
    commit, as they do on a terminal; with no editor they fail, so a lesson has to write
    ``--no-edit`` or ``-m`` and cannot hide the editor the player will meet.

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
        "GIT_AUTHOR_NAME": AUTHOR.name,
        "GIT_AUTHOR_EMAIL": AUTHOR.email,
        "GIT_AUTHOR_DATE": DATE,
        "GIT_COMMITTER_NAME": AUTHOR.name,
        "GIT_COMMITTER_EMAIL": AUTHOR.email,
        "GIT_COMMITTER_DATE": DATE,
    }


def frames(slides: Sequence[Slide]) -> list[Frame]:
    """
    Run a lesson's slides and capture each one's figure.

    Each non-blank line of a slide's ``run`` is one command. A line starting with ``! `` must
    fail; any other must succeed. Results are kept in memory by lesson content, so asking for
    the same lesson again does not run it again.

    Parameters
    ----------
    slides : Sequence[Slide]
        The lesson, in order.

    Returns
    -------
    list[Frame]
        One frame per slide: its own commands and their output, and the repository in the
        shell's current folder once its lines have run. The caller may change them freely.

    Raises
    ------
    RuntimeError
        If a command exits with an error the lesson did not expect, a ``! `` line succeeds, a
        line ends the shell, or a slide ends outside the lesson's home folder (a bug in the
        lesson).
    subprocess.TimeoutExpired
        If the lesson runs longer than termlab's snippet timeout.
    """
    return copy.deepcopy(_frames(tuple((slide.id, slide.run) for slide in slides)))


@functools.lru_cache(maxsize=CACHED_LESSONS)
def _frames(lesson: tuple[tuple[str, str], ...]) -> list[Frame]:
    """
    Run a lesson in a temporary folder of its own, and remove the folder afterwards.

    The folder is in the game's ``lessons`` folder, which git never looks above
    (`firstcommit.gitcmd.isolation`), so a lesson's map can never show a repository that
    happens to contain the game's home.

    Parameters
    ----------
    lesson : tuple[tuple[str, str], ...]
        Each slide's id and ``run`` lines.

    Returns
    -------
    list[Frame]
        One frame per slide.
    """
    lessons = save.home() / "lessons"
    lessons.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="lesson-", dir=lessons)).resolve()
    try:
        built = _run(lesson, root)
    finally:
        sandbox.remove_tree(root, save.home())
    return built


def _run(lesson: tuple[tuple[str, str], ...], root: Path) -> list[Frame]:
    """
    Run a lesson in one shell and read each slide's figure.

    Parameters
    ----------
    lesson : tuple[tuple[str, str], ...]
        Each slide's id and ``run`` lines.
    root : Path
        An empty folder for the lesson's home and the copies taken after each slide.

    Returns
    -------
    list[Frame]
        One frame per slide.
    """
    home = root / "home"
    env = environment(home)
    (home / PROJECT).mkdir()
    (root / "frames").mkdir()
    token = secrets.token_hex(8)
    commands = [_commands(slide, run) for slide, run in lesson]
    result = snippets.run(_script(commands, token, root, home), home / PROJECT, env)
    printed = (root / "output").read_bytes().decode("utf-8", errors="replace")
    transcripts = _transcripts(printed, result.returncode, token, commands, home)
    return [_frame(lesson[index][0], transcript, root / "frames" / str(index), home) for index, transcript in enumerate(transcripts)]


def _commands(slide: str, run: str) -> list[_Command]:
    """
    Read a slide's ``run`` lines.

    Parameters
    ----------
    slide : str
        The slide's id.
    run : str
        Its lines.

    Returns
    -------
    list[_Command]
        One command per non-blank line, without surrounding spaces or the ``! `` mark.
    """
    commands: list[_Command] = []
    for line in run.splitlines():
        text = line.strip()
        must_fail = text.startswith(MUST_FAIL)
        if text:
            commands.append(_Command(slide, text.removeprefix(MUST_FAIL).strip(), must_fail))
    return commands


def _script(commands: list[list[_Command]], token: str, root: Path, home: Path) -> str:
    """
    Write the bash script that runs a lesson.

    Everything the shell prints goes to the file ``output``, read later as bytes: a pipe read
    as text would turn carriage returns into line breaks. Each command runs through ``eval``,
    so a line that is not a whole command fails on its own instead of swallowing the lines
    after it. A marker with the command's exit status follows
    its output. After each slide, the top of the repository the shell is in (or the shell's
    folder, outside one) is saved in ``frames/<n>.cwd``, and the home folder is copied to
    ``frames/<n>``.

    Parameters
    ----------
    commands : list[list[_Command]]
        Each slide's commands.
    token : str
        A random marker that no command prints.
    root : Path
        The lesson's temporary folder.
    home : Path
        The lesson's home folder.

    Returns
    -------
    str
        The script.
    """
    lines = [f"exec >{shlex.quote(str(root / 'output'))} 2>&1\n", PROLOGUE]
    for index, slide in enumerate(commands):
        for command in slide:
            lines.append(f'__fc_status "$__fc"; eval {shlex.quote(command.text)}\n')
            lines.append(f"__fc=$?; printf '\\0%s %d\\0' {token} \"$__fc\"\n")
        frame = shlex.quote(str(root / "frames" / str(index)))
        where = "{ git rev-parse --show-toplevel 2>/dev/null || pwd -P; }"
        lines.append(f"{where} > {frame}.cwd && cp -a {shlex.quote(str(home))} {frame} || exit {COPY_FAILED}\n")
    return "".join(lines)


def _transcripts(printed: str, status: int, token: str, commands: list[list[_Command]], home: Path) -> list[list[Line]]:
    """
    Split a lesson's output into each command's output, and check each command's exit status.

    Parameters
    ----------
    printed : str
        Everything the lesson script printed.
    status : int
        The script's exit status.
    token : str
        The marker the script printed after each command.
    commands : list[list[_Command]]
        Each slide's commands.
    home : Path
        The lesson's home folder, shown as `SHOWN_HOME`.

    Returns
    -------
    list[list[Line]]
        Each slide's commands and their output.

    Raises
    ------
    RuntimeError
        If a command failed unexpectedly, a ``! `` command succeeded, the shell stopped early,
        or the lesson folder could not be copied.
    """
    pieces = re.split(f"\0{token} ([0-9]+)\0", printed.replace(str(home), SHOWN_HOME))
    statuses = [int(status) for status in pieces[1::2]]
    outputs = [_as_on_terminal(output) for output in pieces[0::2]]
    flat = [command for slide in commands for command in slide]
    if status == COPY_FAILED:
        raise RuntimeError(f"the lesson folder could not be copied:\n{outputs[-1]}")
    if len(statuses) < len(flat):
        stopped = flat[len(statuses)]
        raise RuntimeError(f"slide {stopped.slide!r}: the shell stopped at {stopped.text!r}:\n{outputs[-1]}")
    for command, status, output in zip(flat, statuses, outputs, strict=False):
        if command.must_fail and status == 0:
            raise RuntimeError(f"slide {command.slide!r}: {command.text!r} was expected to fail, and succeeded:\n{output}")
        if not command.must_fail and status != 0:
            raise RuntimeError(f"slide {command.slide!r}: {command.text!r} failed with status {status}:\n{output}")
    lines = iter([Line(command=command.text, output=output) for command, output in zip(flat, outputs, strict=False)])
    return [[next(lines) for _ in slide] for slide in commands]


def _as_on_terminal(output: str) -> str:
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


def _frame(slide: str, transcript: list[Line], copy_of_home: Path, home: Path) -> Frame:
    """
    Read a slide's figure from the copy of the home folder taken after it.

    Parameters
    ----------
    slide : str
        The slide's id.
    transcript : list[Line]
        Its commands and their output.
    copy_of_home : Path
        The copy; the folder whose repository the figure shows is saved next to it, in
        ``<copy>.cwd``.
    home : Path
        The lesson's home folder.

    Returns
    -------
    Frame
        The figure.

    Raises
    ------
    RuntimeError
        If the slide ended outside the lesson's home folder.
    """
    cwd = Path(os.fsdecode(copy_of_home.with_name(copy_of_home.name + ".cwd").read_bytes().removesuffix(b"\n")))
    if not cwd.is_relative_to(home):
        raise RuntimeError(f"slide {slide!r} ends outside the lesson's home folder, in {cwd}")
    folder = copy_of_home / cwd.relative_to(home)
    return {"transcript": transcript, "map": repomap.snapshot(folder), "objects": repomap.objects(folder)}
