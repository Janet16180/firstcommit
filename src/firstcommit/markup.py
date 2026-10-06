"""
The one parser for the game's text: lessons, quest steps, briefings, hints, debriefs, cards and notes.

Text is written as described in AUTHORING.md section 6 and parsed here into blocks; the command
line and the page only render blocks, so the layout rules live in one place.
"""

from typing import Literal, TypedDict


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

    Parameters
    ----------
    text : str
        Text written by the rules of AUTHORING.md section 6.

    Returns
    -------
    list[Block]
        Its blocks, in order.
    """
    raise NotImplementedError
