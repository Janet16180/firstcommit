"""
The game's merge tool: what ``git mergetool`` runs on each file in conflict (`firstcommit.gitcmd.MERGETOOL_SETTINGS`).

It tells the page through the terminal's title, ``firstcommit-mergetool <file>``, as the editor
wrappers do (`firstcommit.commands.EDITOR_TITLE`), and sends it again every `RETITLE` seconds, so
a page that lost it finds it again and a page that stops hearing it knows the tool is gone. Then
it waits for the file: the page's merge panel writes the sides the player picked into it
(`firstcommit.markers.resolve`). Once the file is a plain file with no conflict block, the tool
ends with status 0 and git adds the file; Ctrl-C, typed by the player or by the panel's Cancel,
ends it with status 1 and git puts the file back as it was. A file that disappears, or stops
being a plain file, ends it with status 1 too.

While it waits on a terminal, the terminal neither echoes nor turns Ctrl-C into a signal: a
signal would kill git-mergetool with it, leaving its temporary copies behind and the player
without git's own word on what happened. Keys typed meanwhile are dropped when it ends, so none
reaches the shell after it. Without a terminal (the levels' tests) it only waits for the file.
"""

import os
import re
import select
import termios
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal, TextIO

from firstcommit import markers
from firstcommit.records import Language

TITLE = "firstcommit-mergetool"
"""The first word of the terminal title while the tool waits, such as ``firstcommit-mergetool launch.txt``."""
CANCEL = b"\x03"
"""The key that cancels: Ctrl-C, read as a byte while the terminal sends no signals."""
POLL = 0.2
"""Seconds between two looks at the file."""
RETITLE = 2.0
"""Seconds between two sendings of the title; the page treats it as gone a few seconds after the last."""
CONTROLS = re.compile(r"[\x00-\x1f\x7f-\x9f]")

Ending = Literal["answered", "cancelled", "gone"]

WAITING: dict[Language, str] = {
    "en": "Waiting for the merge panel: pick a side for each conflict in {path}, then Write.\nTo stop without changing the file: Cancel in the panel, or Ctrl-C here.",
    "es": "Esperando el panel de merge: elige un lado para cada conflicto en {path}, y luego Escribir.\nPara parar sin cambiar el archivo: Cancelar en el panel, o Ctrl-C aquí.",
}
NO_MARKERS: dict[Language, str] = {
    "en": "{path} has no conflict markers left: Git stages it as it is.",
    "es": "{path} ya no tiene marcadores de conflicto: Git lo agrega al staging area tal como está.",
}
GONE: dict[Language, str] = {
    "en": "{path} is gone from the working folder.",
    "es": "{path} ya no está en la carpeta de trabajo.",
}


def title(path: str) -> str:
    """
    Give the terminal title the tool sets while it waits for a file.

    Parameters
    ----------
    path : str
        The file, as git names it.

    Returns
    -------
    str
        `TITLE` and the path, its control characters dropped, so a file name cannot end the title early.
    """
    return f"{TITLE} {CONTROLS.sub('', path)}"


def answered(path: Path) -> bool:
    """
    Tell whether a file in conflict has been answered: it is a plain file with no conflict block.

    Parameters
    ----------
    path : Path
        The file.

    Returns
    -------
    bool
        True for a regular file (not a symbolic link) whose content holds no complete conflict block.
    """
    plain = path.is_file() and not path.is_symlink()
    return plain and not any(part["kind"] == "block" for part in markers.parts(path.read_bytes()))


def wait(path: Path, keys: int | None, retitle: Callable[[], None], *, poll: float = POLL, every: float = RETITLE) -> Ending:
    """
    Wait until a file in conflict is answered, the player cancels, or the file is gone.

    Parameters
    ----------
    path : Path
        The file, with conflict blocks.
    keys : int | None
        A file descriptor to read keys from (a terminal with no line editing), or None.
    retitle : Callable[[], None]
        Sends the title again; called every `every` seconds.
    poll : float
        Seconds between two looks at the file.
    every : float
        Seconds between two calls of `retitle`.

    Returns
    -------
    Ending
        ``"answered"`` once `answered`, ``"cancelled"`` on a `CANCEL` byte (other keys are
        ignored), ``"gone"`` once the path is no regular file.
    """
    watched = [keys] if keys is not None else []
    titled = time.monotonic()
    ending: Ending | None = None
    while ending is None:
        if answered(path):
            ending = "answered"
        elif not path.is_file() or path.is_symlink():
            ending = "gone"
        elif select.select(watched, [], [], poll)[0] and keys is not None and CANCEL in os.read(keys, 64):
            ending = "cancelled"
        elif time.monotonic() - titled >= every:
            retitle()
            titled = time.monotonic()
    return ending


def run(path: Path, language: Language, stdin: TextIO, stdout: TextIO) -> int:
    """
    Be the merge tool for one file: tell the page, wait, and give git its exit status.

    Parameters
    ----------
    path : Path
        The file in conflict, as git hands it (``$MERGED``).
    language : Language
        The player's language, for the lines it prints.
    stdin : TextIO
        Where keys come from; a terminal is set to no echo and no signals while the tool waits,
        and given back as it was.
    stdout : TextIO
        Where its lines go; on a terminal the title goes there too.

    Returns
    -------
    int
        0 when the file is answered (git then adds it), 1 when the player cancels or the file is gone.
    """
    named = str(path)
    if answered(path):
        print(NO_MARKERS[language].format(path=named), file=stdout, flush=True)
        return 0
    titled = stdout.isatty()

    def send(text: str) -> None:
        if titled:
            stdout.write(f"\x1b]0;{text}\x07")
            stdout.flush()

    send(title(named))
    print(WAITING[language].format(path=named), file=stdout, flush=True)
    keys = stdin.fileno() if stdin.isatty() else None
    kept = termios.tcgetattr(keys) if keys is not None else None
    if keys is not None and kept is not None:
        quiet = termios.tcgetattr(keys)
        quiet[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
        termios.tcsetattr(keys, termios.TCSANOW, quiet)
    try:
        ending = wait(path, keys, lambda: send(title(named)))
    finally:
        if keys is not None and kept is not None:
            termios.tcsetattr(keys, termios.TCSAFLUSH, kept)
        send("")
    if ending == "gone":
        print(GONE[language].format(path=named), file=stdout, flush=True)
    return 0 if ending == "answered" else 1
