"""
The one parser for the game's text: lessons, quest steps, briefings, hints, debriefs, cards and notes.

Text is written as described in AUTHORING.md section 6 and parsed here into blocks; the command
line and the page only render blocks, so the layout rules live in one place.
"""

import re
import textwrap
from typing import Literal, TypedDict

PARAGRAPH_BREAK = re.compile(r"\n(?:[ \t]*\n)+")
CODE_SPAN = re.compile(r"`([^`]+)`")
VERBATIM_STARTS = (" ", "\t", "$ ")
BULLET = "- "


class Span(TypedDict):
    """A run of text inside a paragraph or bullet; ``code`` marks text written in backticks."""

    text: str
    code: bool


class Para(TypedDict):
    """A paragraph."""

    kind: Literal["para"]
    spans: list[Span]


class Code(TypedDict):
    """A verbatim block (commands, output, file contents), shown as written, without its common indentation."""

    kind: Literal["code"]
    text: str


class Bullets(TypedDict):
    """A list; each item is a list of spans."""

    kind: Literal["bullets"]
    items: list[list[Span]]


Block = Para | Code | Bullets


def parse(text: str) -> list[Block]:
    """
    Parse game text into blocks.

    The text is dedented as a whole first, so it may be written as an indented triple-quoted
    string. Then blank lines split it into paragraphs; a paragraph whose lines all start with
    whitespace or ``$ `` is a verbatim `Code` block, any other is prose: its lines before the
    first ``- `` line make a `Para`, and each ``- `` line starts an item of one `Bullets` block.

    Parameters
    ----------
    text : str
        Text written by the rules of AUTHORING.md section 6.

    Returns
    -------
    list[Block]
        Its blocks, in order; empty for blank text.
    """
    blocks: list[Block] = []
    for paragraph in PARAGRAPH_BREAK.split(textwrap.dedent(text).strip("\n")):
        if not paragraph.strip():
            continue
        lines = paragraph.split("\n")
        if all(line.startswith(VERBATIM_STARTS) for line in lines):
            blocks.append(_code(paragraph))
        else:
            blocks.extend(_prose(lines))
    return blocks


def _code(paragraph: str) -> Code:
    """
    Make a verbatim block of a paragraph.

    Parameters
    ----------
    paragraph : str
        Lines that all start with whitespace or ``$ ``.

    Returns
    -------
    Code
        The lines without their common indentation and trailing whitespace.
    """
    lines = textwrap.dedent(paragraph).split("\n")
    return {"kind": "code", "text": "\n".join(line.rstrip() for line in lines)}


def _prose(lines: list[str]) -> list[Block]:
    """
    Make a paragraph, a list or both of the lines of one prose paragraph.

    Parameters
    ----------
    lines : list[str]
        The paragraph's lines, none of them blank.

    Returns
    -------
    list[Block]
        A `Para` of the lines before the first bullet, if any, then a `Bullets` block, if any.
    """
    lead: list[str] = []
    items: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(BULLET):
            items.append([stripped[len(BULLET) :]])
        elif items:
            items[-1].append(stripped)
        else:
            lead.append(stripped)
    blocks: list[Block] = []
    if lead:
        blocks.append({"kind": "para", "spans": _spans(" ".join(lead))})
    if items:
        blocks.append({"kind": "bullets", "items": [_spans(" ".join(item)) for item in items]})
    return blocks


def _spans(text: str) -> list[Span]:
    """
    Split prose into plain text and the code written between backticks.

    Parameters
    ----------
    text : str
        One paragraph or bullet; runs of whitespace become one space.

    Returns
    -------
    list[Span]
        Non-empty spans, in order.
    """
    spans: list[Span] = []
    for position, piece in enumerate(CODE_SPAN.split(" ".join(text.split()))):
        if piece:
            spans.append({"text": piece, "code": position % 2 == 1})
    return spans
