"""
Lesson figures built from real git.

Each slide shows real commands, their real output, and the repository they leave behind.

A lesson's ``run`` lines (`firstcommit.kit.Slide`) are run in order in an empty temporary
folder with a fixed identity, date and locale and no global configuration, so every hash and
line of output a lesson shows is what git really prints, the same on every run.
"""

from collections.abc import Sequence
from typing import TypedDict

from firstcommit.kit import Slide
from firstcommit.repomap import Snapshot


class Line(TypedDict):
    """One command a slide runs, and what it printed (standard output and error, interleaved)."""

    command: str
    output: str


class Frame(TypedDict):
    """A slide's figure: its commands with their output, and the repository after them."""

    transcript: list[Line]
    map: Snapshot


def frames(slides: Sequence[Slide]) -> list[Frame]:
    """
    Run a lesson's slides and capture each one's figure.

    Parameters
    ----------
    slides : Sequence[Slide]
        The lesson, in order.

    Returns
    -------
    list[Frame]
        One frame per slide.

    Raises
    ------
    RuntimeError
        If a command exits with an error the lesson did not expect (a bug in the lesson).
    """
    raise NotImplementedError
