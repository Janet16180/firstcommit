"""
The one parser for the game's text: scenes, quest steps, briefings, hints, debriefs, cards and notes.

Text is written as described in AUTHORING.md section 6 and parsed here into blocks; the command
line and the page only render blocks, so the layout rules live in one place.

A code span is a run of backticks, its text, and a run of as many backticks (as in CommonMark),
so `code` can write any name or subject a player chose as one code span that can never forge
paragraphs, bullets or other code in the game's voice.
"""

import re
import textwrap
from typing import Literal, TypedDict

PARAGRAPH_BREAK = re.compile(r"\n(?:[ \t]*\n)+")
# An opening run of backticks, the shortest text, then a closing run of exactly as many.
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
BACKTICK_RUN = re.compile(r"`+")
WHITESPACE = re.compile(r"\s+")
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f]")
GIT_ESCAPES = {"\a": "\\a", "\b": "\\b", "\t": "\\t", "\n": "\\n", "\v": "\\v", "\f": "\\f", "\r": "\\r"}
"""The letter escapes git uses when it quotes a name; other control characters become octal bytes."""
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
    position = 0
    for match in CODE_SPAN.finditer(text):
        spans += _prose_span(text[position : match.start()])
        spans.append({"text": _code_text(match[2]), "code": True})
        position = match.end()
    return spans + _prose_span(text[position:])


def _prose_span(text: str) -> list[Span]:
    """
    Make the plain text between code spans into a span.

    Parameters
    ----------
    text : str
        The text; runs of whitespace become one space.

    Returns
    -------
    list[Span]
        One span, or none for empty text.
    """
    collapsed = WHITESPACE.sub(" ", text)
    return [{"text": collapsed, "code": False}] if collapsed else []


def _code_text(content: str) -> str:
    """
    Give the text a code span shows; its spaces are kept.

    Parameters
    ----------
    content : str
        What stands between the opening and the closing backticks.

    Returns
    -------
    str
        The content without one space at each end when it has one at both and is not only
        spaces, so a code span can start or end with a backtick (as in CommonMark).
    """
    padded = content.startswith(" ") and content.endswith(" ") and content.strip(" ") != ""
    return content[1:-1] if padded else content


def visible(text: str) -> str:
    r"""
    Show the control characters of a text as git does when it quotes a name.

    Parameters
    ----------
    text : str
        Any text, such as a file name or a commit subject a player chose.

    Returns
    -------
    str
        The text with each C0 control character, DEL and C1 control character replaced by its
        escape: ``\n``, ``\t`` and git's other letter escapes, else the octal UTF-8 bytes
        (``\033`` for ESC). Everything else is kept, backslashes included.
    """
    return CONTROL.sub(_escape, text)


def _escape(match: re.Match[str]) -> str:
    """
    Give git's escape for one control character.

    Parameters
    ----------
    match : re.Match[str]
        A match of `CONTROL`.

    Returns
    -------
    str
        Its letter escape, or its UTF-8 bytes in octal.
    """
    char = match[0]
    return GIT_ESCAPES.get(char) or "".join(f"\\{byte:03o}" for byte in char.encode())


def code(text: str) -> str:
    """
    Write any text as markup for one code span that shows it, and nothing else.

    The fence is one backtick longer than the longest run of backticks inside, and the text is
    padded with a space at each end when it starts or ends with a backtick or a space, so
    `parse` reads back exactly `visible(text)`. Control characters are shown escaped, so the
    text can never start a new paragraph, a bullet or another code span.

    Parameters
    ----------
    text : str
        Any text, such as a file name, a branch or a commit subject.

    Returns
    -------
    str
        The markup. An empty text gives a code span of one space, since a code span cannot
        be empty.
    """
    shown = visible(text) or " "
    fence = "`" * (1 + max((len(run) for run in BACKTICK_RUN.findall(shown)), default=0))
    padded = f" {shown} " if shown.strip(" ") and (shown[0] in "` " or shown[-1] in "` ") else shown
    return f"{fence}{padded}{fence}"
