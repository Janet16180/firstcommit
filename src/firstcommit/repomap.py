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

import hashlib
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict, cast

from firstcommit import gitcmd

MAX_COMMITS = 200
MAX_FILES = 300

RefKind = Literal["branch", "remote", "tag"]
Operation = Literal["merge", "rebase", "cherry-pick", "revert", "bisect"]
ObjectType = Literal["blob", "tree", "commit", "tag"]

BRANCH_PREFIX = "refs/heads/"
REF_KINDS: tuple[tuple[str, RefKind], ...] = ((BRANCH_PREFIX, "branch"), ("refs/remotes/", "remote"), ("refs/tags/", "tag"))
STASH = "refs/stash"
REF_FORMAT = "%(refname)%00%(objectname)%00%(*objectname)%00%(symref)"
COMMIT_FORMAT = "%H%x00%h%x00%P%x00%an%x00%at%x00%s"
COMMIT_FIELDS = 6
OBJECT_FORMAT = "%(objectname) %(objecttype) %(objectsize)"
GITLINK_MODE = "160000"
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
    operation: Operation | None
    stash: int
    truncated: bool


class ObjectInfo(TypedDict):
    """One object in a repository's object database."""

    hash: str
    type: ObjectType
    size: int



@dataclass(frozen=True)
class _Repository:
    """The repository of a folder: its git folder, whether it is bare, and its hash function."""

    git_dir: Path
    bare: bool
    object_format: str


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
    - in a damaged repository (missing objects, a deleted staging area), the parts git cannot
      read are left empty and the rest is read as usual;
    - a bare repository has no working folder, so ``files`` is empty;
    - a file that cannot be read (no permission, or deleted while it is read) has no ``folder``
      id; a symbolic link's ``folder`` id is that of the link itself, as ``git add`` stores it;
    - nested repositories and submodules are left out of ``files``, and ignored files are the
      first to go when there are more than `MAX_FILES` paths;
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
        return _no_repository()
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


def _no_repository() -> Snapshot:
    """
    Give the snapshot of a folder that holds no repository.

    Returns
    -------
    Snapshot
        ``exists`` False and everything else empty.
    """
    return {
        "exists": False,
        "bare": False,
        "head": None,
        "branch": None,
        "commits": [],
        "refs": [],
        "files": [],
        "operation": None,
        "stash": 0,
        "truncated": False,
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
    List every path in HEAD, the staging area and the working folder, with its blob ids.

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
    ignored = set(_others(top, "--ignored"))
    shown = set(in_head) | set(in_index) | conflicted | set(_others(top))
    kept = (sorted(shown, key=_display) + sorted(ignored, key=_display))[:MAX_FILES]
    folder = _folder_ids(top, kept, object_format)
    files: list[FileEntry] = [
        {
            "path": _display(key),
            "head": in_head.get(key),
            "index": in_index.get(key),
            "folder": folder.get(key),
            "ignored": key in ignored,
            "conflicted": key in conflicted,
        }
        for key in kept
    ]
    return sorted(files, key=lambda file: file["path"]), len(shown) + len(ignored) > MAX_FILES


def _tree(top: Path, commit: str) -> dict[str, str]:
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
    dict[str, str]
        Blob id by quoted path; submodules are left out.
    """
    result = gitcmd.run(top, *QUOTED_PATHS, "ls-tree", "-r", commit)
    blobs: dict[str, str] = {}
    for line in _lines(result):
        meta, key = line.split("\t", 1)
        _mode, kind, blob = meta.split(" ")
        if kind == "blob":
            blobs[key] = blob
    return blobs


def _index(top: Path) -> tuple[dict[str, str], set[str]]:
    """
    List the files of the staging area.

    Parameters
    ----------
    top : Path
        The top of the working folder.

    Returns
    -------
    tuple[dict[str, str], set[str]]
        Blob id by quoted path, and the quoted paths in conflict; submodules are left out.
    """
    result = gitcmd.run(top, *QUOTED_PATHS, "ls-files", "--stage")
    staged: dict[str, str] = {}
    conflicted: set[str] = set()
    for line in _lines(result):
        meta, key = line.split("\t", 1)
        mode, blob, stage = meta.split(" ")
        if mode == GITLINK_MODE:
            continue
        if stage == "0":
            staged[key] = blob
        else:
            conflicted.add(key)
    return staged, conflicted


def _others(top: Path, *options: str) -> list[str]:
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
    list[str]
        Quoted paths; nested repositories (listed as folders) are left out.
    """
    result = gitcmd.run(top, *QUOTED_PATHS, "ls-files", "--others", "--exclude-standard", *options)
    return [key for key in _lines(result) if not _unquote(key).endswith(b"/")]


def _folder_ids(top: Path, keys: list[str], object_format: str) -> dict[str, str]:
    """
    Compute the blob id each path in the working folder would get if it were added.

    Parameters
    ----------
    top : Path
        The top of the working folder.
    keys : list[str]
        Quoted paths.
    object_format : str
        The repository's hash function, ``sha1`` or ``sha256``.

    Returns
    -------
    dict[str, str]
        Blob id by quoted path, for the paths that are readable files or symbolic links.
    """
    files: list[str] = []
    ids: dict[str, str] = {}
    for key in keys:
        full = os.fsencode(top) + b"/" + _unquote(key)
        mode = _mode(full)
        link_id = _link_id(full, object_format) if mode is not None and stat.S_ISLNK(mode) else None
        if mode is not None and stat.S_ISREG(mode):
            files.append(key)
        elif link_id is not None:
            ids[key] = link_id
    ids.update(_hash_files(top, files))
    return ids


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
