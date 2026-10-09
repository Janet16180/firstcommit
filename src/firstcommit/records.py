"""
The records of a repository snapshot: plain data, saved with the game and sent to the page.

`firstcommit.repomap` fills them from git; the save keeps the last ones observed, and the page
renders them. They live in the data layer, apart from the code that reads git, so the save can
type and check them without depending on it.
"""

from typing import Literal, TypedDict

RefKind = Literal["branch", "remote", "tag"]
Operation = Literal["merge", "rebase", "cherry-pick", "revert", "bisect"]
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


class Remote(TypedDict):
    """A remote a repository names: its name and its address as configured (``remote.<name>.url``)."""

    name: str
    url: str


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

    ``remotes`` lists the remotes the repository names, sorted by name, each with its address as
    written in its configuration; empty without a repository or without remotes.
    """

    exists: bool
    bare: bool
    head: str | None
    branch: str | None
    commits: list[Commit]
    refs: list[Ref]
    pushed: list[str]
    remotes: list[Remote]
    files: list[FileEntry]
    operation: Operation | None
    stash: int
    truncated: bool


class ConflictSide(TypedDict):
    """
    One side of a file in conflict: where it came from and the file as that side has it.

    ``label`` is the branch the side came from (the branch HEAD is on, or the merged branch or
    remote-tracking branch, such as ``scout`` or ``origin/main``), else the commit's short hash,
    or empty when git records no incoming commit (a rebase, say). ``author`` is the name on that
    side's commit, empty when there is none. ``lines`` is the file's text as that side has it,
    one line each without its newline, or None when that side deleted the file.
    """

    label: str
    author: str
    lines: list[str] | None


class Conflict(TypedDict):
    """
    A file in conflict, read from the staging area's three stages, so it stays true while the player edits the file.

    ``you`` is the side of the branch you are on (stage 2), ``them`` the incoming side (stage 3),
    and ``base`` the version both started from (stage 1), None when the two sides each added the
    file.
    """

    path: str
    you: ConflictSide
    them: ConflictSide
    base: list[str] | None


class CleanPart(TypedDict):
    """Lines of a file outside every conflict block, as they are; each without its line ending."""

    kind: Literal["clean"]
    lines: list[str]


class BlockPart(TypedDict):
    """
    One conflict block of a file, as git wrote it between its markers.

    ``yours`` are the lines between ``<<<<<<<`` and ``=======`` (or the ``|||||||`` of the base
    version, which is left out), ``theirs`` those between ``=======`` and ``>>>>>>>``, each without
    its line ending. ``yours_label`` and ``theirs_label`` are the words after the opening and
    closing markers, as git wrote them, such as ``HEAD`` and a full commit hash.
    """

    kind: Literal["block"]
    yours: list[str]
    theirs: list[str]
    yours_label: str
    theirs_label: str


MarkedPart = CleanPart | BlockPart
"""A run of a file's lines: clean lines, or one conflict block."""


class MarkedFile(TypedDict):
    """
    A file read for its conflict blocks (`firstcommit.markers`): its lines in order, and the hash of the bytes they were read from.

    ``read`` is the SHA-256 of the file's bytes, in hex; a resolve sends it back, so a file that
    changed since it was read is never overwritten.
    """

    path: str
    read: str
    parts: list[MarkedPart]


Keep = Literal["yours", "theirs", "both"]
"""What to keep of one conflict block: your side, theirs, or both, yours first."""


class ReflogEntry(TypedDict):
    """
    One move of HEAD, as its reflog records it: from where, to where, and git's note of why.

    ``old`` is the commit HEAD left, empty for the first move; ``new`` the commit it moved to;
    ``message`` git's own words, such as ``reset: moving to HEAD~1`` or ``commit: Add the map``;
    ``line`` the whole line ``git reflog`` prints for it on a terminal, without colour, such as
    ``3727643 (HEAD -> side) HEAD@{0}: checkout: moving from main to side``.
    """

    old: str
    new: str
    message: str
    line: str


ReviewVerdict = Literal["approved", "changes-requested", "commented"]
"""What a review says: approved, changes requested, or only a comment."""
PullState = Literal["open", "merged", "closed"]
"""Where a pull request stands."""


class Review(TypedDict):
    """
    A review of a pull request, a game record that git never sees, as on GitHub.

    ``commit`` is the pull request's head commit the reviewer saw; once the branch moves past it,
    the review is stale.
    """

    reviewer: str
    verdict: ReviewVerdict
    body: str
    commit: str


class PullRequest(TypedDict):
    """
    A pull request on the stand-in GitHub: a game record kept beside the bare repository (`firstcommit.pulls`).

    ``number`` counts from 1; ``head`` is the branch asking to be merged and ``base`` the branch it
    asks to join; ``merge_commit`` is the commit the merge made, None until it is merged.
    """

    number: int
    title: str
    author: str
    head: str
    base: str
    state: PullState
    reviews: list[Review]
    merge_commit: str | None


class ReviewView(Review):
    """
    A review as the board shows it: ``stale`` once the pull request's head has moved past the commit it saw.

    GitHub calls such an approval stale, and a branch protection rule may dismiss it. "Outdated"
    is GitHub's word for a line comment whose line a later commit changed, which reviews here do
    not have yet.
    """

    stale: bool


class PullView(TypedDict):
    """
    A pull request as the review board (V7) draws it, read from the stand-in GitHub now.

    ``head_commit`` is the head branch's commit (``refs/pull/<n>/head`` once the branch is gone);
    ``commits`` the pull request's own commits, newest first; ``files`` the paths it changes from
    where it left ``base``; ``mergeable`` and ``conflicts`` what a merge into ``base`` would do now
    (a merged one is mergeable, with no conflicts).
    """

    number: int
    title: str
    author: str
    head: str
    base: str
    state: PullState
    head_commit: str
    commits: list[Commit]
    files: list[str]
    mergeable: bool
    conflicts: list[str]
    reviews: list[ReviewView]


class Command(TypedDict):
    """
    One command line the player typed in the game's terminal (`firstcommit.commands`), and how it ended.

    ``line`` is the whole line as the shell's history keeps it (``git add a.txt && git commit``
    is one line); ``status`` is the exit status of the last part that ran, 130 when it was
    stopped with Ctrl-C.
    """

    line: str
    status: int

Mood = Literal["info", "ok", "warn", "err"]
"""How Rama says something about a typed line (`firstcommit.reactions`): neutral, pleased, careful or about a failure."""
Moment = Literal["secret-leak", "launch", "junk-flood", "force-break", "unreviewed-main"]
"""
A one-time moment the page plays over the zones when a reaction carries it: a secret leaking into
every copy, a ship launching, generated files flooding into every copy, a forced push breaking
Alex's chain on the mothership, or an unreviewed commit on the mothership's ``main`` landing at
Alex's station.
"""
Art = Literal["space", "timeline", "terminal", "planet", "flag", "zones", "conveyor", "capsule", "chain", "orbit", "rocket", "pull", "alarm", "fork", "merge", "collision", "blackbox", "meteor", "simulator"]
"""The pictures a level's scene can show; the page draws each one (its art files)."""
View = Literal["station", "crew", "history", "sides", "blackbox", "board", "focus"]
"""
The views of the level screen (docs/drafts/chapters-5-9.md, the view ladder): your station's four
zones, the crew view, history, a conflict's two sides, the black box, the review board, and your
branch and main.
"""
Picture = Literal["chain", "desk", "movelog", "sides"]
"""
The teaching pictures (docs/drafts/teaching-pictures.md): the chain of commits with their names,
HEAD and pins; the desk (working folder and staging area); the move log (``git reflog``, one row
per line); and a conflict's two sides.
"""


class WhatIf(TypedDict):
    """
    The chain's one-time WHAT IF, played once the step ``after`` passes.

    It shows the same chain with the names in ``without`` taken off, and the commits only they
    reached drawn as ghosts.
    """

    without: list[str]
    after: str


class Pictures(TypedDict):
    """
    The pictures a level shows and the marks on them, written with `firstcommit.kit.pictures`.

    ``large`` is the main picture and ``small`` a second, smaller one or None. ``folder`` adds the
    working-folder row under the chain; ``mothership`` the mothership's pins and the commits only
    it has; ``alex`` Alex's pins; ``ghosts`` the commits only the reflog reaches
    (`Observation` ``ghosts``). ``kept`` is the step after which the desk outlines Git's copy, or
    None; ``lines`` the files whose lines the desk draws (`Observation` ``texts``); ``graph`` shows
    git's own ``git log --oneline --graph --all`` beside the chain (`Observation` ``graph``);
    ``whatif`` the chain's WHAT IF, or None.
    """

    large: Picture
    small: Literal["chain", "desk"] | None
    folder: bool
    mothership: bool
    alex: bool
    ghosts: bool
    kept: str | None
    lines: list[str]
    graph: bool
    whatif: WhatIf | None


class TargetCommit(TypedDict):
    """One commit of a challenge's target chart: a label of the level's own, its parents' labels and its subject."""

    id: str
    parents: list[str]
    subject: str


class Target(TypedDict):
    """
    A challenge's target chart: the commits by label, the name each branch should be on, and the branch HEAD should be on.

    A name counts as placed when the player's branch is on a commit whose subject is the one of
    the commit ``names`` gives it; labels, not hashes, since hashes exist only after setup.
    """

    commits: list[TargetCommit]
    names: dict[str, str]
    head: str


class FileTexts(TypedDict):
    """A file's text in the working folder and in the staging area, None where it is not, for the desk's lines."""

    path: str
    folder: str | None
    index: str | None


Seen = Literal[View, "band", "tape", "mergetool"]
"""
What the page marks seen once its birth has played: a view; ``band``, the crew view flattened
into Alex's band above another view (born in 5-3); ``tape``, the black box's tape of HEAD's
moves under history (born in 7-3); or ``mergetool``, the game's merge tool panel, whose first
opening Rama explains git's words for the two sides (7-4). No level opens on ``band``, ``tape``
or ``mergetool``.
"""

Language = Literal["en", "es"]
"""The languages every text the player reads is written in: English and Spanish."""

Who = Literal["you", "alex"]
"""The two people of the playground (`firstcommit.playground`), who share one remote."""
StartId = Literal["empty", "changes", "branches", "alex-ahead", "both", "conflict", "lost"]
"""The free playground's starting points, in the picker's order (`firstcommit.freeplay.STARTS`)."""
PlaygroundView = Literal["chain", "history", "desk", "crew", "conflict", "movelog", "graph"]
"""
The free playground's views: the chain, history (your repository beside the mothership), the desk,
the crew, a conflict's file, the move log (``git reflog``) and git's own graph.
"""
Button = Literal["edit", "add", "commit", "push", "fetch", "pull", "pull-no-rebase", "status", "merge-abort", "keep-ours", "keep-theirs"]
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


FileKind = Literal["file", "missing", "other"]
"""What a path is in a working folder: a regular file, nothing, or anything else (a folder, a link)."""


class FolderFacts(TypedDict):
    """
    A person's playground folder, as its buttons and their explanations need it, read from disk.

    ``usable`` says that the folder is where the lab puts it, with no link on the way; the other
    fields are empty when it is not. ``kinds`` says what each button file is there; ``lines``
    counts the line breaks of each regular one (in its first 64 KiB), and ``marked`` lists, sorted,
    those holding a conflict marker line. ``locked`` says whether ``.git/index.lock`` exists:
    a git command is changing the staging area, or stopped halfway.
    """

    usable: bool
    kinds: dict[str, FileKind]
    lines: dict[str, int]
    marked: list[str]
    locked: bool


class ConfigFacts(TypedDict):
    """What a person's repository configuration holds: a name and an email, a remote, and an upstream for the current branch."""

    name: bool
    email: bool
    remote: bool
    upstream: bool


class Facts(TypedDict):
    """
    What a press's explanation is chosen from, besides the person's repository before and after it.

    All of it is read just before the press. ``github`` is the stand-in GitHub then, or None
    in a playground without one.
    """

    github: Snapshot | None
    folder: FolderFacts
    config: ConfigFacts
