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
"""

import re
import shlex
from pathlib import Path

from firstcommit.records import Command

RECORD = re.compile(rb"\d+\t(\d+)\t(.*)", re.DOTALL)
"""A whole record without its NUL: the history number, the exit status and the line."""

STARTUP = r"""
PS1='\W $ '
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
"""
"""
The startup file, with the history file and the log to fill in.

The first prompt only notes the newest history entry, read back from the history file, so a new
shell never logs what an earlier one typed. After that, a prompt logs the newest entry only when
its number changed. The history is not filtered (``HISTCONTROL`` and ``HISTIGNORE`` unset), so
every line typed gets a number of its own. A log that cannot be written is skipped silently,
rather than printing an error at every prompt.
"""


def startup(log: Path, history: Path) -> str:
    """
    Write the game's bash startup file.

    Parameters
    ----------
    log : Path
        The log the shell appends each command line to.
    history : Path
        The shell's history file.

    Returns
    -------
    str
        The startup file's text, the paths quoted for bash.
    """
    return STARTUP.format(log=shlex.quote(str(log)), history=shlex.quote(str(history)))


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
