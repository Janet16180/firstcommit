"""
A snapshot of a repository, as the player's map shows it and as level checks read it.

The map, the "what just happened" feed (`firstcommit.changes`), the lesson figures
(`firstcommit.demos`) and the level checks all read this one snapshot, so what the player sees
and what a check decides can never disagree. Everything comes from git plumbing, never from
the wording of git's human-readable output.

The three areas of a file are given as blob ids, the way git itself compares them: a file is
untracked when it is in the folder but not in the staging area, staged when its staging-area
blob differs from HEAD's, and changed but not staged when its folder blob differs from the
staging area's.
"""

from pathlib import Path
from typing import Literal, TypedDict

MAX_COMMITS = 200
MAX_FILES = 300


class Commit(TypedDict):
    """One commit."""

    hash: str
    short: str
    parents: list[str]
    subject: str
    author: str
    time: int


class Ref(TypedDict):
    """A branch, remote-tracking branch or tag, and the commit it names (annotated tags peeled)."""

    name: str
    kind: Literal["branch", "remote", "tag"]
    target: str


class FileEntry(TypedDict):
    """
    One path and its blob id in each of the three areas.

    ``head``, ``index`` and ``folder`` are None where the file is absent. ``folder`` is the id
    the working copy would get if it were added (as ``git hash-object`` computes it).
    ``conflicted`` paths have no single staging-area blob, so their ``index`` is None.
    """

    path: str
    head: str | None
    index: str | None
    folder: str | None
    ignored: bool
    conflicted: bool


class Snapshot(TypedDict):
    """
    The state of one repository.

    ``exists`` is False when the folder holds no repository (all else empty). ``branch`` names
    the branch HEAD is on, even before its first commit (when ``head`` is None); it is None when
    HEAD is detached. ``operation`` names a merge, rebase, cherry-pick, revert or bisect in
    progress. ``commits`` lists every commit reachable from HEAD and the refs, newest first, at
    most `MAX_COMMITS`; ``files`` lists at most `MAX_FILES` paths, sorted; ``truncated`` says
    whether either was cut.
    """

    exists: bool
    bare: bool
    head: str | None
    branch: str | None
    commits: list[Commit]
    refs: list[Ref]
    files: list[FileEntry]
    operation: Literal["merge", "rebase", "cherry-pick", "revert", "bisect"] | None
    stash: int
    truncated: bool


def snapshot(path: Path) -> Snapshot:
    """
    Read the state of the repository in a folder.

    Parameters
    ----------
    path : Path
        A working folder or a bare repository. It may hold no repository, or not exist.

    Returns
    -------
    Snapshot
        Its state.
    """
    raise NotImplementedError
