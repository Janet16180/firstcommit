"""
The records of a repository snapshot: plain data, saved with the game and sent to the page.

`firstcommit.repomap` fills them from git; the save keeps the last ones observed, and the page
renders them. They live in the data layer, apart from the code that reads git, so the save can
type and check them without depending on it.
"""

from typing import Literal, TypedDict

RefKind = Literal["branch", "remote", "tag"]
Operation = Literal["merge", "rebase", "cherry-pick", "revert", "bisect"]
ObjectType = Literal["blob", "tree", "commit", "tag"]
Change = Literal["added", "modified", "deleted", "typechange"]
"""How the staging area differs from HEAD, as `git status` letters it: A, M, D, T."""
FolderChange = Literal["modified", "deleted", "typechange", "untracked", "ignored"]
"""How the working folder differs from the staging area, as `git status` letters it: M, D, T, ?? and !!."""

FILE_MODE = "100644"
EXECUTABLE_MODE = "100755"
LINK_MODE = "120000"
GITLINK_MODE = "160000"


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
    kind: RefKind
    target: str


class FileEntry(TypedDict):
    """
    One path and its blob id and mode in each of the three areas.

    ``head``, ``index`` and ``folder`` are None where the file is absent. ``folder`` is the id
    the working copy would get if it were added (as ``git hash-object`` computes it).
    ``conflicted`` paths have no single staging-area blob, so their ``index`` is None.

    ``head_mode``, ``index_mode`` and ``folder_mode`` are git's modes: `FILE_MODE` for a file,
    `EXECUTABLE_MODE` for an executable one, `LINK_MODE` for a symbolic link and `GITLINK_MODE`
    for a repository; None exactly where the id is None. Two areas agree when both the id and
    the mode agree, so ``chmod +x`` alone is a change, as ``git status`` shows it.

    ``repository`` marks a folder holding a repository of its own: one nested in the working
    folder (``git status`` lists it as an untracked folder; its ``folder`` is its HEAD commit, or
    None before its first commit) or one recorded as a submodule (its ids are commits). Git
    never looks at the files inside it.

    ``index_change`` and ``folder_change`` classify the file the way ``git status`` does, in its
    two columns. ``index_change`` is how the staging area differs from HEAD ("Changes to be
    committed"); ``folder_change`` is how the working folder differs from the staging area
    ("Changes not staged for commit"), or ``"untracked"`` / ``"ignored"`` for a path the staging
    area does not have. Either is None where the two areas agree. A mode change (``chmod +x``)
    is ``"modified"``; a file that became a link or a repository is ``"typechange"``. After
    ``git rm --cached`` a file is ``"deleted"`` and ``"untracked"`` at once, as git lists it twice.
    A ``conflicted`` path has neither: git lists it apart, as unmerged.
    """

    path: str
    head: str | None
    index: str | None
    folder: str | None
    head_mode: str | None
    index_mode: str | None
    folder_mode: str | None
    ignored: bool
    conflicted: bool
    repository: bool
    index_change: Change | None
    folder_change: FolderChange | None


class Snapshot(TypedDict):
    """
    The state of one repository.

    ``exists`` is False when the folder holds no repository. All else is then empty, except that
    a folder no repository holds lists its own files in ``files`` (cut as below), with only
    ``folder``, ``folder_mode`` and ``repository`` set: no area of git holds them. ``branch`` names
    the branch HEAD is on, even before its first commit (when ``head`` is None); it is None when
    HEAD is detached. ``operation`` names a merge, rebase, cherry-pick, revert or bisect in
    progress. ``commits`` lists every commit reachable from HEAD and the refs, newest first, at
    most `firstcommit.repomap.MAX_COMMITS`; ``files`` lists at most `firstcommit.repomap.MAX_FILES` paths, sorted; ``truncated`` says
    whether either was cut.

    ``pushed`` names the remote-tracking branches that a push from this repository moved last,
    as their reflogs record it, so a commit that reached one by a push was here before the
    remote had it. Invariant: a sorted subset of the names of ``refs`` of kind ``"remote"``;
    empty when there are none, or when their reflogs are off.
    """

    exists: bool
    bare: bool
    head: str | None
    branch: str | None
    commits: list[Commit]
    refs: list[Ref]
    pushed: list[str]
    files: list[FileEntry]
    operation: Operation | None
    stash: int
    truncated: bool


class ObjectInfo(TypedDict):
    """One object in a repository's object database."""

    hash: str
    type: ObjectType
    size: int


Who = Literal["you", "alex"]
"""The two people of the playground (`firstcommit.playground`), who share one remote."""
Button = Literal["edit", "add", "commit", "push", "fetch", "pull", "pull-no-rebase", "status"]
"""
The kinds of the playground's buttons. A button's id is its kind, or ``"<kind>:<file>"`` for a
kind that acts on one file (``"add:notes.txt"``, ``"keep-ours:README.md"``).
"""


class ButtonView(TypedDict):
    """
    A playground button as the page draws it now.

    ``id`` is what the page sends back to press it; ``line`` is the exact line it runs in the
    current state; ``off`` says why it cannot be pressed now, or is empty.
    """

    id: str
    label: str
    line: str
    off: str


class Press(TypedDict):
    """
    One press of a playground button: who pressed which button (its id), the command it ran, and what that printed.

    ``command`` is exactly what ran, as the player could type it; ``status`` is its exit status
    and ``output`` its standard output and error, interleaved, as a terminal shows them.
    """

    person: Who
    button: str
    command: str
    status: int
    output: str
