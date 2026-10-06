"""
"What just happened": the difference between two snapshots of a repository, told in plain words.

The page shows these events after every command the player types. They are computed from the
real state before and after, never from the command line the player typed, so they stay true
whatever command (or editor, or file manager) caused the change.
"""

from typing import TypedDict

from firstcommit.repomap import Snapshot


class Event(TypedDict):
    """
    One change, for a beginner.

    ``kind`` is a short stable identifier (such as ``"commit-created"`` or ``"file-staged"``) the
    page may style by; ``text`` is one plain sentence that names the real files, branches and
    short hashes involved.
    """

    kind: str
    text: str


def describe(before: Snapshot, after: Snapshot) -> list[Event]:
    """
    Tell what changed between two snapshots of the same repository.

    Parameters
    ----------
    before : Snapshot
        The earlier state.
    after : Snapshot
        The later state.

    Returns
    -------
    list[Event]
        The changes, most important first; empty when nothing changed.
    """
    raise NotImplementedError
