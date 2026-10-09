"""Turn a terminal's raw output into the lines it shows: a carriage return goes back to the line's start, and ESC [K clears the rest of it."""

import re
import sys


def shown(line: str) -> str:
    """
    Give what one line of terminal output leaves on screen.

    Parameters
    ----------
    line : str
        One raw line, without its newline.

    Returns
    -------
    str
        The line as the terminal shows it.
    """
    screen = ""
    for part in line.split("\r"):
        clear = part.startswith("\x1b[K")
        part = part.removeprefix("\x1b[K")
        screen = part + ("" if clear else screen[len(part) :])
    if re.search(r"\x1b", screen):
        raise ValueError(f"an escape sequence left in {screen!r}")
    return screen


sys.stdout.write("".join(shown(line) + "\n" for line in sys.stdin.read().split("\n")[:-1]))
