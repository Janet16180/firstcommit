"""
A snapshot of a repository, as the player's map shows it and as level checks read it.

The map, the "what just happened" feed (`firstcommit.changes`), the lesson figures
(`firstcommit.demos`) and the level checks all read this one snapshot, so what the player sees
and what a check decides can never disagree. Everything comes from git plumbing, never from
the wording of git's human-readable output.

The three areas of a file are given as blob ids and modes, the way git itself compares them: a
file is untracked when it is in the folder but not in the staging area, staged when its
staging-area blob or mode differs from HEAD's, and changed but not staged when its folder blob
or mode differs from the staging area's.

The records themselves live in `firstcommit.records`; this module re-exports them.
"""

import hashlib
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from firstcommit import gitcmd
from firstcommit.records import (
    EXECUTABLE_MODE,
    FILE_MODE,
    GITLINK_MODE,
    LINK_MODE,
    Change,
    Commit,
    FileEntry,
    FolderChange,
    ObjectInfo,
    ObjectType,
    Operation,
    Ref,
    RefKind,
    Snapshot,
)

__all__ = [
    "EXECUTABLE_MODE",
    "FILE_MODE",
    "GITLINK_MODE",
    "LINK_MODE",
    "MAX_COMMITS",
    "MAX_FILES",
    "Area",
    "Change",
    "Commit",
    "FileEntry",
    "FolderChange",
    "ObjectInfo",
    "ObjectType",
    "Operation",
    "Ref",
    "RefKind",
    "Snapshot",
    "conflicted",
    "history",
    "mode_changed",
    "nested",
    "objects",
    "snapshot",
    "staged",
    "unstaged",
    "untracked",
    "version",
]

MAX_COMMITS = 200
MAX_FILES = 300

Area = Literal["head", "index", "folder"]

BRANCH_PREFIX = "refs/heads/"
REF_KINDS: tuple[tuple[str, RefKind], ...] = ((BRANCH_PREFIX, "branch"), ("refs/remotes/", "remote"), ("refs/tags/", "tag"))
STASH = "refs/stash"
REF_FORMAT = "%(refname)%00%(objectname)%00%(*objectname)%00%(symref)"
COMMIT_FORMAT = "%H%x00%h%x00%P%x00%an%x00%at%x00%s"
PUSHED = "update by push"
"""Git's fixed reflog message for a remote-tracking branch that a push from this repository moved (transport.c)."""
MAX_REFLOG_ENTRIES = 1000
"""How many reflog entries of the remote-tracking branches a snapshot reads at most, all branches together."""
COMMIT_FIELDS = 6
OBJECT_FORMAT = "%(objectname) %(objecttype) %(objectsize)"
NOWHERE: tuple[None, None] = (None, None)
KINDS = {FILE_MODE: "file", EXECUTABLE_MODE: "file", LINK_MODE: "link", GITLINK_MODE: "repository"}
"""What a mode makes a path: a change between two of these is a type change, as git calls it."""
OPERATION_MARKERS: tuple[tuple[str, Operation], ...] = (
    ("rebase-merge", "rebase"),
    ("rebase-apply", "rebase"),
    ("MERGE_HEAD", "merge"),
    ("CHERRY_PICK_HEAD", "cherry-pick"),
    ("REVERT_HEAD", "revert"),
    ("BISECT_LOG", "bisect"),
)

# Paths come back C-quoted and pure ASCII, so a name that is not valid UTF-8 survives the round
# trip through text to `hash-object --stdin-paths`, which unquotes them.
QUOTED_PATHS = ("-c", "core.quotepath=on")
QUOTED_CHARACTER = re.compile(rb'\\([0-7]{3}|[abtnvfr"\\])')
ESCAPES = {b"a": b"\a", b"b": b"\b", b"t": b"\t", b"n": b"\n", b"v": b"\v", b"f": b"\f", b"r": b"\r", b'"': b'"', b"\\": b"\\"}
ESCAPE_LETTERS = {byte[0]: letter.decode() for letter, byte in ESCAPES.items()}
"""The letter git writes after a backslash for each byte it escapes by name; it writes others in octal."""
DEFAULT_OBJECT_FORMAT = "sha1"
"""The hash function of ``git hash-object`` outside a repository, and of a new one."""


def version(file: FileEntry, area: Area) -> tuple[str | None, str | None]:
    """
    Give a file's id and mode in one area.

    Two areas, or one area in two snapshots, agree only when their versions are equal, as
    ``git status`` compares them: ``chmod +x`` changes the version but not the id.

    Parameters
    ----------
    file : FileEntry
        The file.
    area : Area
        ``"head"``, ``"index"`` (the staging area) or ``"folder"`` (the working folder).

    Returns
    -------
    tuple[str | None, str | None]
        The id and the mode; both None where the file is absent.
    """
    versions = {
        "head": (file["head"], file["head_mode"]),
        "index": (file["index"], file["index_mode"]),
        "folder": (file["folder"], file["folder_mode"]),
    }
    return versions[area]


def untracked(snap: Snapshot) -> list[str]:
    """
    List the untracked files, as `git status` lists them, nested repositories aside.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    list[str]
        Their paths, in the snapshot's order.
    """
    return [file["path"] for file in snap["files"] if file["folder_change"] == "untracked" and not file["repository"]]


def nested(snap: Snapshot) -> list[str]:
    """
    List the repositories nested in the working folder that `git status` lists as untracked folders.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    list[str]
        Their paths, without a final ``/``, in the snapshot's order.
    """
    return [file["path"] for file in snap["files"] if file["folder_change"] == "untracked" and file["repository"]]


def staged(snap: Snapshot) -> list[str]:
    """
    List the files with changes to be committed: the staging area differs from HEAD.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    list[str]
        Their paths, in the snapshot's order.
    """
    return [file["path"] for file in snap["files"] if file["index_change"] is not None]


def unstaged(snap: Snapshot) -> list[str]:
    """
    List the tracked files with changes not staged: modified, deleted or changed in type in the working folder.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    list[str]
        Their paths, in the snapshot's order; conflicted files are listed by `conflicted`.
    """
    return [file["path"] for file in snap["files"] if file["folder_change"] in ("modified", "deleted", "typechange")]


def mode_changed(snap: Snapshot) -> list[str]:
    """
    List the files whose only change not staged is their mode (``chmod +x``): same content as the staging area.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    list[str]
        Their paths, in the snapshot's order.
    """
    return [file["path"] for file in snap["files"] if file["folder_change"] == "modified" and file["folder"] == file["index"]]


def conflicted(snap: Snapshot) -> list[str]:
    """
    List the files in conflict (unmerged), which `git status` lists apart from staged and unstaged changes.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    list[str]
        Their paths, in the snapshot's order.
    """
    return [file["path"] for file in snap["files"] if file["conflicted"]]


@dataclass(frozen=True)
class _Repository:
    """The repository of a folder: its git folder, whether it is bare, and its hash function."""

    git_dir: Path
    bare: bool
    object_format: str


def history(snap: Snapshot, start: str | None) -> set[str]:
    """
    Collect a commit and every ancestor of it that a snapshot lists.

    Parameters
    ----------
    snap : Snapshot
        A repository.
    start : str | None
        A commit's full hash, or None.

    Returns
    -------
    set[str]
        The hashes; empty for None, or for a commit the snapshot does not list.
    """
    parents = {commit["hash"]: commit["parents"] for commit in snap["commits"]}
    seen: set[str] = set()
    pending = [start] if start is not None else []
    while pending:
        current = pending.pop()
        if current in parents and current not in seen:
            seen.add(current)
            pending.extend(parents[current])
    return seen


def snapshot(path: Path) -> Snapshot:
    """
    Read the state of the repository in a folder.

    The repository is the folder's own: ``path`` is the top of its working folder, or the bare
    repository itself. A folder inside a repository that starts higher up (a ``git init`` typed
    one folder too high, a subfolder, the ``.git`` folder) holds no repository of its own, so a
    check can never pass on the wrong repository. Nothing in the repository changes, and the
    staging area is never locked, so the page can poll while the player types.

    Whatever a player does to the folder gives a snapshot rather than an error:

    - a missing folder, an empty one, or a ``.git`` folder git does not recognise (an empty one,
      or one missing ``HEAD``, ``objects`` or ``refs``) holds no repository: ``exists`` is False;
    - a folder that no repository holds lists its own files in the working folder only, as
      ``git init`` would find them untracked; one inside a repository that starts higher up
      lists none, since that repository may hold them;
    - in a damaged repository (missing objects, a deleted staging area), the parts git cannot
      read are left empty and the rest is read as usual;
    - a bare repository has no working folder, so ``files`` is empty;
    - a file that cannot be read (no permission, or deleted while it is read) has no ``folder``
      id; a symbolic link's ``folder`` id is that of the link itself, as ``git add`` stores it;
    - a nested repository or submodule is one entry, never the files inside it; its folder id
      ignores changes inside it that are not committed there. Ignored files are the first to go
      when there are more than `MAX_FILES` paths;
    - stash commits are left out of ``commits`` and ``refs``; ``stash`` counts them.

    Parameters
    ----------
    path : Path
        A working folder or a bare repository. It may hold no repository, or not exist.

    Returns
    -------
    Snapshot
        Its state.
    """
    repo = _find(path)
    if repo is None:
        return _no_repository(path)
    head = _head(path)
    refs, stashed = _refs(path)
    commits, commits_cut = _commits(path, head)
    files, files_cut = ([], False) if repo.bare else _files(path, head, repo.object_format)
    return {
        "exists": True,
        "bare": repo.bare,
        "head": head,
        "branch": _branch(path),
        "commits": commits,
        "refs": refs,
        "pushed": _pushed(path, refs),
        "files": files,
        "operation": next((operation for marker, operation in OPERATION_MARKERS if os.path.exists(repo.git_dir / marker)), None),
        "stash": _stash_count(path) if stashed else 0,
        "truncated": commits_cut or files_cut,
    }


def objects(path: Path) -> list[ObjectInfo]:
    """
    List every object in the object database of the repository in a folder.

    Unreachable objects are listed too, such as a blob written by ``git hash-object -w``.

    Parameters
    ----------
    path : Path
        A working folder or a bare repository. It may hold no repository, or not exist.

    Returns
    -------
    list[ObjectInfo]
        The objects, sorted by hash; empty without a repository, or when git cannot read the
        object database.
    """
    repo = _find(path)
    if repo is None:
        return []
    result = gitcmd.run(repo.git_dir, "cat-file", "--batch-all-objects", f"--batch-check={OBJECT_FORMAT}")
    found: list[ObjectInfo] = []
    for line in _lines(result):
        name, kind, size = line.split(" ")
        found.append({"hash": name, "type": cast(ObjectType, kind), "size": int(size)})
    return sorted(found, key=lambda info: info["hash"])


def _no_repository(path: Path) -> Snapshot:
    """
    Give the snapshot of a folder that holds no repository.

    Parameters
    ----------
    path : Path
        The folder. It may not exist.

    Returns
    -------
    Snapshot
        ``exists`` False and everything else empty, except the files of a folder that no
        repository holds.
    """
    files, cut = _loose_files(path) if _outside_any_repository(path) else ([], False)
    return {
        "exists": False,
        "bare": False,
        "head": None,
        "branch": None,
        "commits": [],
        "refs": [],
        "pushed": [],
        "files": files,
        "operation": None,
        "stash": 0,
        "truncated": cut,
    }


def _find(path: Path) -> _Repository | None:
    """
    Find the folder's own repository.

    Parameters
    ----------
    path : Path
        The folder.

    Returns
    -------
    _Repository | None
        The repository whose working folder starts at ``path``, or the bare repository at
        ``path``; None if the folder is missing, cannot be entered, or is not the top of one.
    """
    result = gitcmd.run(
        path, "rev-parse", "--is-bare-repository", "--is-inside-work-tree", "--show-object-format", "--show-cdup", "--absolute-git-dir"
    )
    if result.returncode != 0:
        return None
    bare, inside, object_format, rest = result.stdout.removesuffix("\n").split("\n", 3)
    # Outside a working folder, --show-cdup prints no line at all; at the top it prints an empty one.
    up, git_dir = rest.split("\n", 1) if inside == "true" else (None, rest)
    if up != "" and not (bare == "true" and Path(git_dir) == path.resolve()):
        return None
    return _Repository(Path(git_dir), bare == "true", object_format)


def _outside_any_repository(path: Path) -> bool:
    """
    Tell whether no repository holds a folder, neither its own nor one that starts higher up.

    Parameters
    ----------
    path : Path
        The folder.

    Returns
    -------
    bool
        True if git finds no repository there (also when the folder is missing).
    """
    return gitcmd.run(path, "rev-parse", "--git-dir").returncode != 0


def _loose_files(top: Path) -> tuple[list[FileEntry], bool]:
    """
    List the files of a folder that no repository holds, with the id and mode each would get.

    No area of git holds them, so only ``folder`` and ``folder_mode`` are set (and
    ``repository`` for a repository inside the folder); ``git init`` makes them untracked
    with the same paths, ids and modes.

    Parameters
    ----------
    top : Path
        The folder.

    Returns
    -------
    tuple[list[FileEntry], bool]
        At most `MAX_FILES` entries sorted by path, and whether there were more.
    """
    keys, nested = _loose_keys(top)
    kept = sorted(keys, key=_display)[:MAX_FILES]
    in_folder = _folder_versions(top, kept, {}, DEFAULT_OBJECT_FORMAT)
    files: list[FileEntry] = []
    for key in kept:
        folder_id, folder_mode = in_folder.get(key, NOWHERE)
        files.append(
            {
                "path": _display(key),
                "head": None,
                "index": None,
                "folder": folder_id,
                "head_mode": None,
                "index_mode": None,
                "folder_mode": folder_mode,
                "ignored": False,
                "conflicted": False,
                "repository": key in nested,
                "index_change": None,
                "folder_change": None,
            }
        )
    return sorted(files, key=lambda file: file["path"]), len(keys) > MAX_FILES


def _loose_keys(top: Path) -> tuple[list[str], set[str]]:
    """
    Find the files of a folder that no repository holds, as ``git ls-files --others`` would once one did.

    Regular files and symbolic links are listed; a folder that is a repository of its own is one
    path, and nothing inside it is. A ``.git`` folder or file is never listed, nor is an empty
    folder. A folder that cannot be read lists nothing.

    Parameters
    ----------
    top : Path
        The folder.

    Returns
    -------
    tuple[list[str], set[str]]
        Paths quoted as git quotes them, and those of them that are repositories.
    """
    keys: list[str] = []
    nested: set[str] = set()
    pending = [b""]
    while pending:
        prefix = pending.pop()
        for entry in _entries(os.fsencode(top) + b"/" + prefix):
            name = prefix + entry.name
            is_folder = entry.is_dir(follow_symlinks=False)
            if entry.name == b".git" or not (is_folder or entry.is_file(follow_symlinks=False) or entry.is_symlink()):
                continue
            if is_folder and not _is_repository(entry.path):
                pending.append(name + b"/")
                continue
            keys.append(_quote(name))
            if is_folder:
                nested.add(keys[-1])
    return keys, nested


def _is_repository(folder: bytes) -> bool:
    """
    Tell whether a folder is the top of a repository of its own.

    Parameters
    ----------
    folder : bytes
        The folder's path.

    Returns
    -------
    bool
        True if it holds a ``.git`` that git recognises; git is asked only when one is there.
    """
    return os.path.lexists(folder + b"/.git") and _find(Path(os.fsdecode(folder))) is not None


def _entries(folder: bytes) -> list[os.DirEntry[bytes]]:
    """
    List a folder's entries.

    Parameters
    ----------
    folder : bytes
        The folder's path.

    Returns
    -------
    list[os.DirEntry[bytes]]
        Its entries, or none if it is gone, is not a folder or cannot be read.
    """
    try:
        with os.scandir(folder) as found:
            entries = list(found)
    except (FileNotFoundError, NotADirectoryError, PermissionError):  # the player may remove or lock it at any time
        entries = []
    return entries


def _lines(result: subprocess.CompletedProcess[str]) -> list[str]:
    """
    Split a git command's output into lines.

    Parameters
    ----------
    result : subprocess.CompletedProcess[str]
        The finished command.

    Returns
    -------
    list[str]
        Its non-empty lines, or none if it failed.
    """
    lines = result.stdout.split("\n") if result.returncode == 0 else []
    return [line for line in lines if line]


def _head(cwd: Path) -> str | None:
    """
    Give the commit HEAD points at.

    Parameters
    ----------
    cwd : Path
        A folder of the repository.

    Returns
    -------
    str | None
        Its full hash, or None before the first commit.
    """
    result = gitcmd.run(cwd, "rev-parse", "-q", "--verify", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def _branch(cwd: Path) -> str | None:
    """
    Give the branch HEAD is on.

    Parameters
    ----------
    cwd : Path
        A folder of the repository.

    Returns
    -------
    str | None
        The branch name, or None when HEAD is detached.
    """
    result = gitcmd.run(cwd, "symbolic-ref", "-q", "HEAD")
    target = result.stdout.removesuffix("\n")
    branch = None
    if result.returncode == 0 and target.startswith(BRANCH_PREFIX):
        branch = target.removeprefix(BRANCH_PREFIX)
    return branch


def _refs(cwd: Path) -> tuple[list[Ref], bool]:
    """
    List the branches, remote-tracking branches and tags.

    Symbolic refs such as ``origin/HEAD`` are left out: they only repeat another ref.

    Parameters
    ----------
    cwd : Path
        A folder of the repository.

    Returns
    -------
    tuple[list[Ref], bool]
        The refs sorted by kind then name, and whether a stash exists.
    """
    result = gitcmd.run(cwd, "for-each-ref", f"--format={REF_FORMAT}", "refs/heads", "refs/remotes", "refs/tags", STASH)
    refs: list[Ref] = []
    stashed = False
    for line in _lines(result):
        refname, target, peeled, symref = line.split("\0")
        stashed = stashed or refname == STASH
        for prefix, kind in REF_KINDS:
            if refname.startswith(prefix) and not symref:
                refs.append({"name": refname.removeprefix(prefix), "kind": kind, "target": peeled or target})
    return refs, stashed


def _pushed(cwd: Path, refs: list[Ref]) -> list[str]:
    """
    Name the remote-tracking branches that a push from this repository moved last.

    The newest entry of each one's reflog says what moved it: `PUSHED` for a push, the
    command's own words for a fetch or a pull (``fetch: fast-forward``). One git command reads
    the reflogs of all of them, each newest first, up to `MAX_REFLOG_ENTRIES` in all; a branch
    whose newest entry is past that, or that has no reflog, counts as not pushed.

    Parameters
    ----------
    cwd : Path
        A folder of the repository.
    refs : list[Ref]
        The repository's refs.

    Returns
    -------
    list[str]
        Names of remote-tracking branches, sorted; empty when there are none.
    """
    remote = [f"refs/remotes/{ref['name']}" for ref in refs if ref["kind"] == "remote"]
    if not remote:
        return []
    result = gitcmd.run(cwd, "log", "--walk-reflogs", "-z", f"--max-count={MAX_REFLOG_ENTRIES}", "--format=%gD%x00%gs", *remote, "--")
    fields = result.stdout.split("\0") if result.returncode == 0 else []
    messages = dict(zip(fields[0::2], fields[1::2], strict=False))
    return sorted(name.removeprefix("refs/remotes/") for name in remote if messages.get(f"{name}@{{0}}") == PUSHED)


def _stash_count(cwd: Path) -> int:
    """
    Count the entries of the stash.

    Parameters
    ----------
    cwd : Path
        A folder of the repository.

    Returns
    -------
    int
        The number of stash entries (0 if git cannot read them).
    """
    result = gitcmd.run(cwd, "rev-list", "--walk-reflogs", "--count", STASH)
    return int(result.stdout) if result.returncode == 0 else 0


def _commits(cwd: Path, head: str | None) -> tuple[list[Commit], bool]:
    """
    List the commits reachable from HEAD, the branches, the remote-tracking branches and the tags.

    Parameters
    ----------
    cwd : Path
        A folder of the repository.
    head : str | None
        The commit HEAD points at, if any.

    Returns
    -------
    tuple[list[Commit], bool]
        At most `MAX_COMMITS` commits, children before parents and newest first, and whether
        there were more.
    """
    tips = [head] if head is not None else []
    result = gitcmd.run(
        cwd, "log", "-z", "--topo-order", f"--max-count={MAX_COMMITS + 1}", f"--format={COMMIT_FORMAT}", "--branches", "--tags", "--remotes", *tips, "--"
    )
    fields = result.stdout.removesuffix("\0").split("\0") if result.returncode == 0 and result.stdout else []
    commits: list[Commit] = []
    for start in range(0, len(fields), COMMIT_FIELDS):
        full, short, parents, author, time, subject = fields[start : start + COMMIT_FIELDS]
        commits.append({"hash": full, "short": short, "parents": parents.split(), "subject": subject, "author": author, "time": int(time)})
    return commits[:MAX_COMMITS], len(commits) > MAX_COMMITS


def _files(top: Path, head: str | None, object_format: str) -> tuple[list[FileEntry], bool]:
    """
    List every path in HEAD, the staging area and the working folder, with its blob ids and modes.

    Parameters
    ----------
    top : Path
        The top of the working folder.
    head : str | None
        The commit HEAD points at, if any.
    object_format : str
        The repository's hash function, ``sha1`` or ``sha256``.

    Returns
    -------
    tuple[list[FileEntry], bool]
        At most `MAX_FILES` entries sorted by path, and whether there were more.
    """
    in_head = _tree(top, head) if head is not None else {}
    in_index, conflicted = _index(top)
    untracked, nested = _others(top)
    ignored, nested_ignored = _others(top, "--ignored")
    nested |= nested_ignored | {key for key, (_, mode) in [*in_head.items(), *in_index.items()] if mode == GITLINK_MODE}
    others = set(untracked) | set(ignored)
    shown = set(in_head) | set(in_index) | conflicted | set(untracked)
    kept = (sorted(shown, key=_display) + sorted(set(ignored), key=_display))[:MAX_FILES]
    in_folder = _folder_versions(top, kept, in_index, object_format)
    files: list[FileEntry] = []
    for key in kept:
        head_id, head_mode = in_head.get(key, NOWHERE)
        index_id, index_mode = in_index.get(key, NOWHERE)
        folder_id, folder_mode = in_folder.get(key, NOWHERE)
        listed: FolderChange = "ignored" if key in ignored else "untracked"
        index_change = None if key in conflicted else _index_change((head_id, head_mode), (index_id, index_mode))
        folder_change = None if key in conflicted else _folder_change((index_id, index_mode), (folder_id, folder_mode), listed if key in others else None)
        files.append(
            {
                "path": _display(key),
                "head": head_id,
                "index": index_id,
                "folder": folder_id,
                "head_mode": head_mode,
                "index_mode": index_mode,
                "folder_mode": folder_mode,
                "ignored": key in ignored,
                "conflicted": key in conflicted,
                "repository": key in nested,
                "index_change": index_change,
                "folder_change": folder_change,
            }
        )
    return sorted(files, key=lambda file: file["path"]), len(shown) + len(ignored) > MAX_FILES


def _index_change(head: tuple[str | None, str | None], index: tuple[str | None, str | None]) -> Change | None:
    """
    Classify how the staging area differs from HEAD, as the first column of `git status`.

    Parameters
    ----------
    head : tuple[str | None, str | None]
        The file's id and mode in HEAD.
    index : tuple[str | None, str | None]
        Its id and mode in the staging area.

    Returns
    -------
    Change | None
        ``added``, ``deleted``, ``modified`` or ``typechange``; None when they agree.
    """
    change: Change | None = _difference(head, index)
    if head[0] is None and index[0] is not None:
        change = "added"
    elif head[0] is not None and index[0] is None:
        change = "deleted"
    return change


def _folder_change(
    index: tuple[str | None, str | None], folder: tuple[str | None, str | None], listed: FolderChange | None
) -> FolderChange | None:
    """
    Classify how the working folder differs from the staging area, as the second column of `git status`.

    Parameters
    ----------
    index : tuple[str | None, str | None]
        The file's id and mode in the staging area.
    folder : tuple[str | None, str | None]
        Its id and mode in the working folder.
    listed : FolderChange | None
        ``untracked`` or ``ignored`` if ``git ls-files --others`` lists the path, else None.

    Returns
    -------
    FolderChange | None
        ``untracked`` or ``ignored`` for a path the staging area lacks, else ``deleted``,
        ``modified`` or ``typechange``; None when they agree.
    """
    change: FolderChange | None = _difference(index, folder)
    if index[0] is None:
        change = listed
    elif folder[0] is None:
        change = "deleted"
    return change


def _difference(one: tuple[str | None, str | None], other: tuple[str | None, str | None]) -> Literal["modified", "typechange"] | None:
    """
    Tell how a file present in two areas differs between them.

    Parameters
    ----------
    one : tuple[str | None, str | None]
        Its id and mode in one area.
    other : tuple[str | None, str | None]
        Its id and mode in the other.

    Returns
    -------
    Literal["modified", "typechange"] | None
        None when they agree, ``typechange`` when it became another kind of thing (a file, a
        link, a repository), ``modified`` otherwise (content or executable bit).
    """
    difference: Literal["modified", "typechange"] | None = None
    if one != other and KINDS.get(one[1] or "") != KINDS.get(other[1] or ""):
        difference = "typechange"
    elif one != other:
        difference = "modified"
    return difference


def _tree(top: Path, commit: str) -> dict[str, tuple[str, str]]:
    """
    List the files of a commit.

    Parameters
    ----------
    top : Path
        The top of the working folder.
    commit : str
        The commit's hash.

    Returns
    -------
    dict[str, tuple[str, str]]
        Id and mode by quoted path; a submodule's id is the commit it records.
    """
    result = gitcmd.run(top, *QUOTED_PATHS, "ls-tree", "-r", commit)
    versions: dict[str, tuple[str, str]] = {}
    for line in _lines(result):
        meta, key = line.split("\t", 1)
        mode, _kind, name = meta.split(" ")
        versions[key] = (name, mode)
    return versions


def _index(top: Path) -> tuple[dict[str, tuple[str, str]], set[str]]:
    """
    List the files of the staging area.

    Parameters
    ----------
    top : Path
        The top of the working folder.

    Returns
    -------
    tuple[dict[str, tuple[str, str]], set[str]]
        Id and mode by quoted path, and the quoted paths in conflict.
    """
    result = gitcmd.run(top, *QUOTED_PATHS, "ls-files", "--stage")
    staged: dict[str, tuple[str, str]] = {}
    conflicted: set[str] = set()
    for line in _lines(result):
        meta, key = line.split("\t", 1)
        mode, name, stage = meta.split(" ")
        if stage == "0":
            staged[key] = (name, mode)
        else:
            conflicted.add(key)
    return staged, conflicted


def _others(top: Path, *options: str) -> tuple[list[str], set[str]]:
    """
    List the files of the working folder that are not in the staging area.

    Parameters
    ----------
    top : Path
        The top of the working folder.
    *options : str
        ``--ignored`` for the ignored files instead of the untracked ones.

    Returns
    -------
    tuple[list[str], set[str]]
        Quoted paths, and those of them that are nested repositories (which git lists as
        folders, with a final ``/`` that is dropped here).
    """
    result = gitcmd.run(top, *QUOTED_PATHS, "ls-files", "--others", "--exclude-standard", *options)
    keys: list[str] = []
    nested: set[str] = set()
    for listed in _lines(result):
        key = listed.removesuffix("/") if not listed.endswith('/"') else listed.removesuffix('/"') + '"'
        keys.append(key)
        if key != listed:
            nested.add(key)
    return keys, nested


def _folder_versions(top: Path, keys: list[str], in_index: dict[str, tuple[str, str]], object_format: str) -> dict[str, tuple[str, str]]:
    """
    Compute the id and mode each path in the working folder would get if it were added.

    Parameters
    ----------
    top : Path
        The top of the working folder.
    keys : list[str]
        Quoted paths.
    in_index : dict[str, tuple[str, str]]
        The staging area's id and mode by quoted path.
    object_format : str
        The repository's hash function, ``sha1`` or ``sha256``.

    Returns
    -------
    dict[str, tuple[str, str]]
        Id and mode by quoted path, for the readable files, the symbolic links and the
        repositories with a commit.
    """
    trusted = _trusts_executable_bit(top)
    files: dict[str, int] = {}
    versions: dict[str, tuple[str, str]] = {}
    for key in keys:
        full = os.fsencode(top) + b"/" + _unquote(key)
        mode = _mode(full)
        if mode is not None and stat.S_ISREG(mode):
            files[key] = mode
        elif mode is not None:
            versions.update(_special_version(key, full, mode, object_format))
    for key, blob in _hash_files(top, list(files)).items():
        versions[key] = (blob, _file_mode(files[key], in_index.get(key, NOWHERE)[1], trusted))
    return versions


def _special_version(key: str, full: bytes, mode: int, object_format: str) -> dict[str, tuple[str, str]]:
    """
    Give the id and mode of a symbolic link, or of a folder that holds a repository.

    Parameters
    ----------
    key : str
        The quoted path.
    full : bytes
        Its full path.
    mode : int
        Its type and permissions, from ``lstat``.
    object_format : str
        The repository's hash function, ``sha1`` or ``sha256``.

    Returns
    -------
    dict[str, tuple[str, str]]
        The path's id and mode, or nothing for a link that vanished, an ordinary folder, a
        repository with no commit yet or anything else.
    """
    found: str | None = None
    kind = LINK_MODE
    if stat.S_ISLNK(mode):
        found = _link_id(full, object_format)
    elif stat.S_ISDIR(mode):
        found, kind = _nested_head(Path(os.fsdecode(full))), GITLINK_MODE
    return {key: (found, kind)} if found is not None else {}


def _nested_head(folder: Path) -> str | None:
    """
    Give the commit a repository nested in the working folder points at.

    Parameters
    ----------
    folder : Path
        The folder.

    Returns
    -------
    str | None
        Its HEAD commit, or None if the folder is not the top of a repository of its own or it
        has no commit yet.
    """
    repo = _find(folder)
    return _head(folder) if repo is not None and not repo.bare else None


def _trusts_executable_bit(top: Path) -> bool:
    """
    Tell whether git reads the executable bit of the files in the working folder.

    Parameters
    ----------
    top : Path
        The top of the working folder.

    Returns
    -------
    bool
        The repository's ``core.fileMode``, true unless it is set to false.
    """
    result = gitcmd.run(top, "config", "--type=bool", "--get", "core.fileMode")
    return result.stdout.strip() != "false"


def _file_mode(mode: int, index_mode: str | None, trusted: bool) -> str:
    """
    Give the mode git would record for a regular file.

    Parameters
    ----------
    mode : int
        The file's type and permissions, from ``lstat``.
    index_mode : str | None
        Its mode in the staging area, if it is there.
    trusted : bool
        Whether git reads the executable bit (``core.fileMode``).

    Returns
    -------
    str
        `EXECUTABLE_MODE` if the owner may run it, else `FILE_MODE`; when git does not read the
        bit, the staging area's mode of a file, else `FILE_MODE`.
    """
    recorded = FILE_MODE
    if trusted and mode & stat.S_IXUSR:
        recorded = EXECUTABLE_MODE
    elif not trusted and index_mode in (FILE_MODE, EXECUTABLE_MODE):
        recorded = index_mode
    return recorded


def _mode(path: bytes) -> int | None:
    """
    Give the type and permissions of a path without following a symbolic link.

    Parameters
    ----------
    path : bytes
        The path.

    Returns
    -------
    int | None
        Its mode, or None if it is gone or cannot be reached.
    """
    try:
        mode = os.lstat(path).st_mode
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        mode = None
    return mode


def _hash_files(top: Path, keys: list[str]) -> dict[str, str]:
    """
    Hash regular files as ``git add`` would store them, without writing anything.

    Parameters
    ----------
    top : Path
        The top of the working folder.
    keys : list[str]
        Quoted paths of regular files.

    Returns
    -------
    dict[str, str]
        Blob id by quoted path, for the files git could read.
    """
    ids: dict[str, str] = {}
    pending = keys
    while pending:
        result = gitcmd.run(top, "hash-object", "--stdin-paths", stdin="".join(f"{key}\n" for key in pending))
        hashed = result.stdout.split()
        ids.update(zip(pending, hashed, strict=False))
        # git stops at the first file it cannot read, after printing the ids of the files before it.
        pending = pending[len(hashed) + 1 :]
    return ids


def _link_id(path: bytes, object_format: str) -> str | None:
    """
    Compute the blob id of a symbolic link.

    Git stores a link as a blob holding its target path; ``hash-object`` would follow the link
    and hash the target's content instead.

    Parameters
    ----------
    path : bytes
        The link.
    object_format : str
        The repository's hash function, ``sha1`` or ``sha256``.

    Returns
    -------
    str | None
        The blob id, or None if the link is gone or was replaced since it was found.
    """
    try:
        target: bytes | None = os.readlink(path)
    except OSError:  # the player can delete or replace the link between lstat and readlink
        target = None
    return None if target is None else hashlib.new(object_format, b"blob %d\0" % len(target) + target).hexdigest()


def _unquote(key: str) -> bytes:
    """
    Turn a path git printed with ``core.quotepath`` back into its bytes.

    Parameters
    ----------
    key : str
        The path, C-quoted by git if it holds special or non-ASCII bytes.

    Returns
    -------
    bytes
        The path's bytes.
    """
    raw = key.encode()
    if len(key) >= 2 and key.startswith('"') and key.endswith('"'):
        raw = QUOTED_CHARACTER.sub(lambda match: ESCAPES.get(match[1]) or bytes([int(match[1], 8)]), raw[1:-1])
    return raw


def _quote(raw: bytes) -> str:
    """
    Write a path as git prints it with ``core.quotepath``, the inverse of `_unquote`.

    Parameters
    ----------
    raw : bytes
        The path's bytes.

    Returns
    -------
    str
        The path, C-quoted if it holds a control, quote, backslash or non-ASCII byte.
    """
    plain = all(0x20 <= byte < 0x7F and byte not in b'"\\' for byte in raw)
    escaped = "".join(f"\\{ESCAPE_LETTERS[byte]}" if byte in ESCAPE_LETTERS else chr(byte) if 0x20 <= byte < 0x7F else f"\\{byte:03o}" for byte in raw)
    return raw.decode() if plain else f'"{escaped}"'


def _display(key: str) -> str:
    """
    Give a path as the map shows it.

    Parameters
    ----------
    key : str
        The path as git printed it.

    Returns
    -------
    str
        The path as text, with bytes that are not UTF-8 replaced.
    """
    return _unquote(key).decode("utf-8", errors="replace")
