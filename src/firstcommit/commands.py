r"""
The commands the player types in the game's terminal, logged so the figure can show what really ran.

The game's terminal runs bash with `startup` as its startup file: a plain prompt (the folder's
name, never the user's or the machine's), its history kept in the game home, and a
``PROMPT_COMMAND`` that appends each new command line with its exit status to a log in the game
home. A line is one history entry, so ``git add a.txt && git commit`` is one command with the
status of the last part that ran; a command stopped with Ctrl-C has status 130. Empty lines and
lines dropped with Ctrl-C at the prompt add no history entry, and lines of spaces are skipped,
so none of them is logged; the same line typed twice is logged twice. A shell started without the startup file (``exec bash``)
logs nothing.

Each record is ``<history number>\t<status>\t<line>`` and a NUL byte. Bash strings cannot hold
NUL, so a line with tabs or newlines is still one record. `since` reads the log back from a
position; only whole records count, so a record the shell is still writing is read next time.

`type_line` runs one line the way a player would type it, for the levels' reference solutions
and their tests.
"""

import os
import re
import shlex
import subprocess
from pathlib import Path

from firstcommit import gitcmd, save
from firstcommit.records import Command

COMPLETION = Path("/usr/share/bash-completion/bash_completion")
"""Tab completion for git and the other commands, as Ubuntu's bash-completion package installs it."""

RECORD = re.compile(rb"\d+\t(\d+)\t(.*)", re.DOTALL)
"""A whole record without its NUL: the history number, the exit status and the line."""

PLAYER_HOME = "FIRSTCOMMIT_PLAYER_HOME"
"""Where `shell` keeps the player's ``HOME`` while bash reads the system's startup file."""

PROMPT = r"\W $ "
"""The game's prompt: the folder's name, never the user's or the machine's, such as ``project $``."""
ALEX_PROMPT = r"\[\e[32m\]alex: \W\[\e[0m\] $ "
"""The prompt of Alex's shell in the playground: ``alex: project $``, with ``alex: project`` in green."""

STARTUP = r"""
HOME=${{{player_home}:-$HOME}}
unset {player_home}
if [[ -r {completion} ]]; then
    . {completion}
fi
PS1={prompt}
PS2='> '
HISTFILE={history}
unset HISTCONTROL HISTIGNORE HISTTIMEFORMAT
__firstcommit_seen=
__firstcommit_log() {{
    local status=$? entry number= line= pattern='^ *([0-9]+)[ *] (.*)$'
    entry=$(builtin history 1)
    if [[ $entry =~ $pattern ]]; then
        number=${{BASH_REMATCH[1]}} line=${{BASH_REMATCH[2]}}
    fi
    if [[ -n $__firstcommit_seen && -n $number && $number != "$__firstcommit_seen" && $line == *[![:space:]]* ]]; then
        printf '%s\t%s\t%s\0' "$number" "$status" "$line" 2>/dev/null >> {log}
    fi
    __firstcommit_seen=${{number:-0}}
}}
PROMPT_COMMAND=__firstcommit_log
{banner}"""
"""
The startup file, with the history file, the log, the tab completion, the prompt and a first line to fill in.

Bash reads this file instead of the player's ``~/.bashrc``, which is where Ubuntu turns tab
completion on, so it loads the completion itself when it is installed.

It first gives the shell back the player's ``HOME``, which `shell` set aside, or keeps the one it
has when started some other way.

The first prompt only notes the newest history entry, read back from the history file, so a new
shell never logs what an earlier one typed. After that, a prompt logs the newest entry only when
its number changed. The history is not filtered (``HISTCONTROL`` and ``HISTIGNORE`` unset), so
every line typed gets a number of its own. A log that cannot be written is skipped silently,
rather than printing an error at every prompt.
"""


def startup(log: Path, history: Path, prompt: str = PROMPT, banner: str = "") -> str:
    """
    Write the game's bash startup file.

    Parameters
    ----------
    log : Path
        The log the shell appends each command line to.
    history : Path
        The shell's history file.
    prompt : str
        The prompt, as bash's ``PS1``.
    banner : str
        One line the shell prints before its first prompt, as given; none when empty.

    Returns
    -------
    str
        The startup file's text, the paths, the prompt and the line quoted for bash.
    """
    first_line = f"printf '%s\\n' {shlex.quote(banner)}\n" if banner else ""
    return STARTUP.format(
        log=shlex.quote(str(log)),
        history=shlex.quote(str(history)),
        completion=shlex.quote(str(COMPLETION)),
        player_home=PLAYER_HOME,
        prompt=shlex.quote(prompt),
        banner=first_line,
    )


def shell(startup: Path, quiet_home: Path) -> list[str]:
    """
    Give the command that starts the game's interactive bash on its startup file.

    Ubuntu's bash reads ``/etc/bash.bashrc`` before any startup file, and that file prints a
    notice about ``sudo`` unless ``$HOME`` holds ``.sudo_as_admin_successful`` or ``.hushlogin``.
    So bash starts with a ``HOME`` of the game's that holds ``.hushlogin``, never touching the
    player's real home, and the startup file (`startup`) gives the player's ``HOME`` back before
    the first prompt.

    Parameters
    ----------
    startup : Path
        The startup file.
    quiet_home : Path
        A folder holding a ``.hushlogin`` file.

    Returns
    -------
    list[str]
        The program and its arguments; the environment's ``HOME`` is read when it runs.
    """
    start = f'export {PLAYER_HOME}="$HOME" HOME="$1"; exec bash --noprofile --rcfile "$2" -i'
    return ["sh", "-c", start, "sh", str(quiet_home), str(startup)]


def since(log: Path, offset: int) -> tuple[list[Command], int]:
    """
    Read the commands logged after a position in the log.

    A log shorter than the offset (deleted, then started anew) is read from its start; a record
    of another shape (the log edited by hand) is skipped; bytes that are not UTF-8 in a line are
    replaced.

    Parameters
    ----------
    log : Path
        The log; it may not exist yet.
    offset : int
        Where the last read stopped (`since` or `end`), zero or more.

    Returns
    -------
    tuple[list[Command], int]
        The whole records after ``offset``, oldest first, and the position after the last one.
    """
    data = _contents(log)
    start = offset if offset <= len(data) else 0
    stop = max(start, data.rfind(b"\0") + 1)
    typed: list[Command] = []
    for record in data[start:stop].split(b"\0")[:-1]:
        match = RECORD.fullmatch(record)
        if match is not None:
            typed.append({"line": match[2].decode("utf-8", "replace"), "status": int(match[1])})
    return typed, stop


def end(log: Path) -> int:
    """
    Find where the log's whole records end, to read only what comes after them.

    Parameters
    ----------
    log : Path
        The log; it may not exist yet.

    Returns
    -------
    int
        The position after the last whole record; 0 for a missing or empty log.
    """
    return _contents(log).rfind(b"\0") + 1


def _contents(log: Path) -> bytes:
    """
    Read the log, which the first command typed creates.

    Parameters
    ----------
    log : Path
        The log.

    Returns
    -------
    bytes
        Its bytes; none when it does not exist yet.
    """
    try:
        data = log.read_bytes()
    except FileNotFoundError:
        data = b""
    return data


def type_line(folder: Path, line: str) -> Command:
    """
    Run one command line as the player would type it in the game's terminal, and record how it ended.

    The line runs in bash, in ``folder``, with the game shell's git isolation
    (`firstcommit.gitcmd.shell_environment`), the game home as ``HOME`` and no history, so it
    never reads or writes the player's own files. Nothing is logged: the caller keeps the
    record.

    Parameters
    ----------
    folder : Path
        The folder to run in; it must exist.
    line : str
        The command line, as typed.

    Returns
    -------
    Command
        The line as given and its exit status.

    Raises
    ------
    subprocess.TimeoutExpired
        If the line runs longer than `firstcommit.gitcmd.TIMEOUT` seconds.
    """
    home = save.home()
    env = {**gitcmd.shell_environment(os.environ, home), "HOME": str(home), "HISTFILE": "/dev/null"}
    ran = subprocess.run(["bash", "--noprofile", "--norc", "-c", line], cwd=folder, env=env, capture_output=True, stdin=subprocess.DEVNULL, timeout=gitcmd.TIMEOUT, check=False)
    return {"line": line, "status": ran.returncode}
