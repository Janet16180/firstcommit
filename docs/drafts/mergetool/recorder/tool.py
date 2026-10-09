"""
Prototype of the game's merge tool, for the recorder only: what plan.md proposes as
`python -m firstcommit mergetool <file>`.

It sets the terminal title, prints one line, then waits until the file has no conflict block
(exit 0) or the player cancels with Ctrl-C (exit 1), or the file stops being a plain file (exit 1). While it waits the terminal does not
echo or turn Ctrl-C into a signal, so git-mergetool survives a cancel and cleans up, and nothing
typed meanwhile reaches bash afterwards. The recorder plays the panel's Write by rewriting the
file with firstcommit.markers.resolve from another process.
"""

import os
import select
import sys
import termios
import time
from pathlib import Path

sys.path.insert(0, os.environ["FIRSTCOMMIT_SRC"])

from firstcommit import markers  # noqa: E402

TITLE = "firstcommit-mergetool"
POLL = 0.2
CANCEL = b"\x03"
RETITLE = 2.0


def has_blocks(path: Path) -> bool:
    return any(part["kind"] == "block" for part in markers.parts(path.read_bytes()))


def plain(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def title(text: str) -> None:
    if not sys.stdout.isatty():
        return
    sys.stdout.write(f"\033]0;{text}\007")
    sys.stdout.flush()


def wait(path: Path) -> int:
    keys = [sys.stdin] if sys.stdin.isatty() else []
    shown = time.monotonic()
    status = 0
    while plain(path) and has_blocks(path):
        ready, _, _ = select.select(keys, [], [], POLL)
        if ready and os.read(sys.stdin.fileno(), 1) == CANCEL:
            status = 1
            break
        if time.monotonic() - shown > RETITLE:
            title(f"{TITLE} {path}")
            shown = time.monotonic()
    if not plain(path):
        print(f"{path} is gone from the working folder.")
        status = 1
    return status


def main() -> int:
    path = Path(sys.argv[1])
    if plain(path) and not has_blocks(path):
        print(f"{path} has no conflict markers left: Git stages it as it is.")
        return 0
    tty = sys.stdin.isatty()
    saved = termios.tcgetattr(sys.stdin) if tty else None
    title(f"{TITLE} {path}")
    print(f"Waiting for the merge panel: pick a side for each conflict in {path}, then Write.")
    print("To stop without changing the file: Cancel in the panel, or Ctrl-C here.", flush=True)
    if saved is not None:
        quiet = termios.tcgetattr(sys.stdin)
        quiet[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
        termios.tcsetattr(sys.stdin, termios.TCSANOW, quiet)
    try:
        status = wait(path)
    finally:
        if saved is not None:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, saved)
        title("")
    return status


sys.exit(main())
