"""
Conflict markers in a file: read its conflict blocks, and write the sides chosen for each.

Git marks a conflict in a file with a line ``<<<<<<< <label>``, your side, a line ``=======``,
their side and a line ``>>>>>>> <label>``; with ``merge.conflictStyle=diff3`` (or ``zdiff3``) the
base version sits between your side and ``=======``, after a line ``||||||| <label>``. Each marker
is seven characters, alone on its line or followed by a space and a label. A run of lines that
does not complete that shape is plain text: a block never closed before the end of the file, or
one that a new ``<<<<<<<`` line starts again.

The file is read as bytes, so a resolve keeps every byte outside the blocks, line endings
included; the lines given back are decoded as UTF-8, undecodable bytes replaced.
"""

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from firstcommit.records import BlockPart, CleanPart, Keep, MarkedFile, MarkedPart

YOURS = re.compile(rb"<{7}(?: (.*))?")
BASE = re.compile(rb"\|{7}(?: .*)?")
SPLIT = b"======="
THEIRS = re.compile(rb">{7}(?: (.*))?")


@dataclass
class _Block:
    """A conflict block as it is read: every line so far, markers included, and each side's lines."""

    raw: list[bytes]
    yours_label: bytes
    side: str = "yours"
    yours: list[bytes] = field(default_factory=list)
    theirs: list[bytes] = field(default_factory=list)


Run = list[bytes] | tuple[_Block, bytes]
"""Clean lines, or a closed block with its closing label."""


def _bare(line: bytes) -> bytes:
    """
    Take a line's ending off.

    Parameters
    ----------
    line : bytes
        A line, with its line ending if it has one.

    Returns
    -------
    bytes
        The line alone.
    """
    return line.removesuffix(b"\n").removesuffix(b"\r")


def _runs(data: bytes) -> list[Run]:
    """
    Split a file into runs of clean lines and closed conflict blocks.

    Parameters
    ----------
    data : bytes
        The file's bytes.

    Returns
    -------
    list[Run]
        The runs in order; each line keeps its ending.
    """
    runs: list[Run] = []
    clean: list[bytes] = []
    block: _Block | None = None
    for line in data.splitlines(keepends=True):
        bare = _bare(line)
        opening = YOURS.fullmatch(bare)
        if opening is not None:
            clean += block.raw if block is not None else []
            block = _Block([line], opening[1] or b"")
            continue
        if block is None:
            clean.append(line)
            continue
        block.raw.append(line)
        closing = THEIRS.fullmatch(bare) if block.side == "theirs" else None
        if closing is not None:
            runs += [clean] if clean else []
            runs.append((block, closing[1] or b""))
            clean, block = [], None
        else:
            _add(block, line, bare)
    clean += block.raw if block is not None else []
    return runs + ([clean] if clean else [])


def _add(block: _Block, line: bytes, bare: bytes) -> None:
    """
    Add a line inside an open block: a side's line, or the marker that moves to the next part.

    Parameters
    ----------
    block : _Block
        The open block.
    line : bytes
        The line, with its ending.
    bare : bytes
        The line without its ending.
    """
    if block.side == "yours" and BASE.fullmatch(bare):
        block.side = "base"
    elif block.side in ("yours", "base") and bare == SPLIT:
        block.side = "theirs"
    elif block.side == "yours":
        block.yours.append(line)
    elif block.side == "theirs":
        block.theirs.append(line)


def _text(lines: list[bytes]) -> list[str]:
    """
    Decode lines for the page, without their endings.

    Parameters
    ----------
    lines : list[bytes]
        Lines with their endings.

    Returns
    -------
    list[str]
        Each line as UTF-8, undecodable bytes replaced.
    """
    return [_bare(line).decode("utf-8", "replace") for line in lines]


def parts(data: bytes) -> list[MarkedPart]:
    """
    Read a file's clean lines and conflict blocks, in order.

    Parameters
    ----------
    data : bytes
        The file's bytes.

    Returns
    -------
    list[MarkedPart]
        Clean runs and blocks; a file without a block is one clean run, and an empty file none.
    """
    found: list[MarkedPart] = []
    for run in _runs(data):
        if isinstance(run, list):
            clean: CleanPart = {"kind": "clean", "lines": _text(run)}
            found.append(clean)
            continue
        block, closing = run
        conflict: BlockPart = {
            "kind": "block",
            "yours": _text(block.yours),
            "theirs": _text(block.theirs),
            "yours_label": block.yours_label.decode("utf-8", "replace"),
            "theirs_label": closing.decode("utf-8", "replace"),
        }
        found.append(conflict)
    return found


def marked(path: str, data: bytes) -> MarkedFile:
    """
    Read a file for the page's conflict panel.

    Parameters
    ----------
    path : str
        The file's path in its repository.
    data : bytes
        Its bytes.

    Returns
    -------
    MarkedFile
        Its parts (`parts`) and the SHA-256 of ``data``.
    """
    return {"path": path, "read": hashlib.sha256(data).hexdigest(), "parts": parts(data)}


def resolve(data: bytes, choices: Sequence[Keep]) -> bytes:
    """
    Replace each conflict block of a file with the sides chosen for it, keeping every other byte.

    Parameters
    ----------
    data : bytes
        The file's bytes.
    choices : Sequence[Keep]
        One per block, in order: ``"yours"``, ``"theirs"`` or ``"both"`` (yours, then theirs).

    Returns
    -------
    bytes
        The file with its blocks replaced and its markers gone.

    Raises
    ------
    ValueError
        If there is not exactly one choice per block.
    """
    runs = _runs(data)
    blocks = [run for run in runs if isinstance(run, tuple)]
    if len(blocks) != len(choices):
        raise ValueError(f"{len(blocks)} conflict blocks, {len(choices)} choices")
    kept = iter(choices)
    written: list[bytes] = []
    for run in runs:
        if isinstance(run, list):
            written += run
            continue
        choice = next(kept)
        written += run[0].yours if choice in ("yours", "both") else []
        written += run[0].theirs if choice in ("theirs", "both") else []
    return b"".join(written)
