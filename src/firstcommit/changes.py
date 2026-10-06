"""
"What just happened": the difference between two snapshots of a repository, told in plain words.

The page shows these events after every command the player types. They are computed from the
real state before and after, never from the command line the player typed, so they stay true
whatever command (or editor, or file manager) caused the change.

Event kinds, most important first:

- ``repository-created``, ``repository-removed`` (told alone);
- ``<operation>-finished``, ``<operation>-aborted`` and ``<operation>-started``, where the
  operation is ``merge``, ``rebase``, ``cherry-pick``, ``revert`` or ``bisect`` (a bisect only
  starts and finishes);
- ``conflict``, ``conflict-resolved``;
- ``commit-created`` (a merge commit included), ``commit-replaced`` (an amended commit);
- ``branch-switched``, ``head-detached``, ``head-moved`` (a detached HEAD moved);
- ``branch-renamed``, ``branch-created``, ``branch-moved``, ``branch-deleted``;
- ``tag-created``, ``tag-moved``, ``tag-deleted``;
- ``remote-updated`` (a remote-tracking branch created, moved or deleted);
- ``push-received`` (any branch or tag update in a bare repository, which only a push changes);
- ``stash-saved``, ``stash-applied``, ``stash-dropped``;
- ``file-staged``, ``file-unstaged``, ``file-created``, ``file-changed``, ``file-deleted``,
  ``file-ignored``, ``file-unignored``.

Names and short hashes in the text are in backticks, commit subjects in double quotes.
"""

from dataclasses import dataclass
from typing import Literal, TypedDict

from firstcommit.repomap import Commit, FileEntry, RefKind, Snapshot

MAX_FILE_EVENTS = 4
"""More events of one kind about files are told as one, naming the first `NAMES_SHOWN` paths."""
NAMES_SHOWN = 3

SUMMARIES = {
    "conflict": "{count} files have conflicts: {names}.",
    "conflict-resolved": "{count} files are resolved: {names}.",
    "file-staged": "{count} files were staged: {names}.",
    "file-unstaged": "{count} files were unstaged: {names}.",
    "file-created": "{count} files were created in the working folder: {names}.",
    "file-changed": "{count} files changed in the working folder: {names}.",
    "file-deleted": "{count} files were deleted from the working folder: {names}.",
    "file-ignored": "{count} files are now ignored by Git: {names}.",
    "file-unignored": "{count} files are no longer ignored: {names}.",
}
STARTED = {
    "merge": "A merge is in progress{on}.",
    "rebase": "A rebase is in progress: Git replays commits one at a time, with HEAD detached until the rebase ends.",
    "cherry-pick": "A cherry-pick is in progress{on}.",
    "revert": "A revert is in progress{on}.",
    "bisect": "A bisect is in progress.",
}

Ancestry = Literal["forward", "back", "rewritten", "unknown"]
FileNews = tuple[str, str, str]
"""What happened to one file: the event kind, the path and the sentence."""


class Event(TypedDict):
    """
    One change, for a beginner.

    ``kind`` is a short stable identifier (such as ``"commit-created"`` or ``"file-staged"``) the
    page may style by; ``text`` is one plain sentence that names the real files, branches and
    short hashes involved.
    """

    kind: str
    text: str


@dataclass(frozen=True)
class _Change:
    """Two snapshots of one repository, and every commit either of them lists, by hash."""

    before: Snapshot
    after: Snapshot
    commits: dict[str, Commit]


def describe(before: Snapshot, after: Snapshot) -> list[Event]:
    """
    Tell what changed between two snapshots of the same repository.

    Files that changed only because HEAD moved (a switch, a fast-forward, a reset) are not
    told one by one: the commit or branch event explains them. Snapshots of any shape are
    accepted; facts a snapshot lacks (a commit cut off by `firstcommit.repomap.MAX_COMMITS`)
    make the sentence vaguer, never wrong.

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
    change = _Change(before, after, {commit["hash"]: commit for commit in [*before["commits"], *after["commits"]]})
    if before["exists"] != after["exists"] or before["bare"] != after["bare"]:
        events = [_repository_event(change)]
    elif not after["exists"]:
        events = []
    elif after["bare"]:
        events = _push_events(change)
    else:
        events = _working_events(change)
    return events


def _repository_event(change: _Change) -> Event:
    """
    Tell that a repository appeared in the folder or left it.

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    Event
        The event.
    """
    after = change.after
    kind = "repository-created"
    if not after["exists"]:
        kind, text = "repository-removed", "The repository is gone: Git no longer finds one in this folder."
    elif after["bare"]:
        text = "A bare repository was created here: it keeps commits and branches, with no working folder."
    elif after["head"] is None:
        text = f"A new repository was created in this folder, on {_place(after)} with no commits yet."
    else:
        text = f"A repository appeared in this folder, with {_place(after)} at {_at(change, after['head'])}."
    return {"kind": kind, "text": text}


def _working_events(change: _Change) -> list[Event]:
    """
    Tell what changed in a repository with a working folder.

    Parameters
    ----------
    change : _Change
        The two snapshots, both of an existing repository.

    Returns
    -------
    list[Event]
        The events, most important first.
    """
    before, after = change.before, change.after
    ended = before["operation"] is not None and before["operation"] != after["operation"]
    aborted = ended and not _branch_moved(change)
    commit = _new_head_commit(change)
    renamed = _renamed_branch(change)
    tidied = aborted or after["stash"] > before["stash"]
    head_explained = ended or commit is not None or (renamed is not None and renamed[0] == before["branch"])
    return [
        *_operation_events(change, aborted),
        *_conflict_events(change, aborted),
        *_commit_events(change, commit),
        *([] if head_explained else _head_events(change)),
        *_branch_events(change, commit, renamed),
        *_tag_events(change),
        *_remote_events(change),
        *_stash_events(change),
        *_file_events(change, tidied=tidied, committed=commit is not None),
    ]


def _at(change: _Change, target: str) -> str:
    """
    Name a commit: its short hash and subject when known, else the start of its hash.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    target : str
        The commit's full hash.

    Returns
    -------
    str
        The short hash in backticks, then the subject in double quotes.
    """
    commit = change.commits.get(target)
    return f'`{commit["short"]}` "{commit["subject"]}"' if commit is not None else f"`{target[:7]}`"


def _short(change: _Change, target: str) -> str:
    """
    Give a commit's short hash in backticks.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    target : str
        The commit's full hash.

    Returns
    -------
    str
        Its short hash when known, else the start of its hash.
    """
    commit = change.commits.get(target)
    return f"`{commit['short'] if commit is not None else target[:7]}`"


def _place(snap: Snapshot) -> str:
    """
    Name where HEAD is.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.

    Returns
    -------
    str
        ``branch `main``` or ``a detached HEAD``.
    """
    return f"branch `{snap['branch']}`" if snap["branch"] is not None else "a detached HEAD"


def _count(number: int, one: str, many: str) -> str:
    """
    Write a count with its noun.

    Parameters
    ----------
    number : int
        How many.
    one : str
        The noun for one.
    many : str
        The noun for several.

    Returns
    -------
    str
        Such as ``1 commit`` or ``3 commits``.
    """
    return f"{number} {one if number == 1 else many}"


def _targets(snap: Snapshot, kind: RefKind) -> dict[str, str]:
    """
    Give the refs of one kind.

    Parameters
    ----------
    snap : Snapshot
        A snapshot.
    kind : RefKind
        Branches, remote-tracking branches or tags.

    Returns
    -------
    dict[str, str]
        Target commit by name.
    """
    return {ref["name"]: ref["target"] for ref in snap["refs"] if ref["kind"] == kind}


RefChanges = tuple[list[tuple[str, str]], list[tuple[str, str, str]], list[tuple[str, str]]]
"""Refs created (name, target), moved (name, old target, new target) and deleted (name, old target)."""


def _ref_changes(change: _Change, kind: RefKind) -> RefChanges:
    """
    List the refs of one kind that were created, moved or deleted.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    kind : RefKind
        Branches, remote-tracking branches or tags.

    Returns
    -------
    RefChanges
        The refs created, moved and deleted, each list by name.
    """
    was, now = _targets(change.before, kind), _targets(change.after, kind)
    created = [(name, now[name]) for name in sorted(now.keys() - was.keys())]
    moved = [(name, was[name], now[name]) for name in sorted(was.keys() & now.keys()) if was[name] != now[name]]
    deleted = [(name, was[name]) for name in sorted(was.keys() - now.keys())]
    return created, moved, deleted


def _reachable(change: _Change, start: str) -> set[str]:
    """
    Collect a commit and every ancestor either snapshot knows.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    start : str
        A commit's full hash.

    Returns
    -------
    set[str]
        The hashes, ``start`` included.
    """
    seen: set[str] = set()
    pending = [start]
    while pending:
        current = pending.pop()
        if current not in seen:
            seen.add(current)
            pending.extend(change.commits[current]["parents"] if current in change.commits else [])
    return seen


def _ancestry(change: _Change, was: str, now: str) -> Ancestry:
    """
    Tell how a ref moved through history.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    was : str
        The commit it pointed at.
    now : str
        The commit it points at.

    Returns
    -------
    Ancestry
        ``forward`` if the old commit is in the new one's history, ``back`` the other way round,
        ``rewritten`` if neither, ``unknown`` if a snapshot was cut too short to tell.
    """
    ancestry: Ancestry = "rewritten"
    if was in _reachable(change, now):
        ancestry = "forward"
    elif now in _reachable(change, was):
        ancestry = "back"
    elif change.before["truncated"] or change.after["truncated"]:
        ancestry = "unknown"
    return ancestry


def _branch_moved(change: _Change) -> bool:
    """
    Tell whether HEAD's branch (or a detached HEAD) points somewhere else than before.

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    bool
        True if it moved.
    """
    branch = change.after["branch"]
    moved = change.before["head"] != change.after["head"]
    if branch is not None:
        moved = _targets(change.before, "branch").get(branch) != _targets(change.after, "branch").get(branch)
    return moved


def _new_head_commit(change: _Change) -> tuple[str, Commit] | None:
    """
    Find the commit just made at HEAD, if HEAD moved to one.

    A commit counts as made here when it is new, HEAD stayed on the same branch (or stayed
    detached), and no remote-tracking branch leads to it (else it came with a fetch or pull).

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    tuple[str, Commit] | None
        ``commit-created`` and the commit when it sits on the old HEAD, ``commit-replaced`` when
        it has the old HEAD's parents (an amend), or None.
    """
    before, after = change.before, change.after
    commit = change.commits.get(after["head"]) if after["head"] is not None else None
    known = {known["hash"] for known in before["commits"]}
    remote = set().union(*(_reachable(change, target) for target in _targets(after, "remote").values()))
    if commit is None or commit["hash"] in known or commit["hash"] in remote or before["branch"] != after["branch"]:
        return None
    old = change.commits.get(before["head"]) if before["head"] is not None else None
    found: tuple[str, Commit] | None = None
    if commit["parents"][:1] == ([before["head"]] if before["head"] is not None else []):
        found = ("commit-created", commit)
    elif old is not None and commit["parents"] == old["parents"]:
        found = ("commit-replaced", commit)
    return found


def _renamed_branch(change: _Change) -> tuple[str, str] | None:
    """
    Find a branch that was renamed: exactly one branch gone and one new, at the same commit.

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    tuple[str, str] | None
        The old and new names, or None.
    """
    was, now = _targets(change.before, "branch"), _targets(change.after, "branch")
    gone, new = sorted(was.keys() - now.keys()), sorted(now.keys() - was.keys())
    renamed = None
    if len(gone) == 1 and len(new) == 1 and was[gone[0]] == now[new[0]]:
        renamed = (gone[0], new[0])
    return renamed


def _operation_events(change: _Change, aborted: bool) -> list[Event]:
    """
    Tell that a merge, rebase, cherry-pick, revert or bisect ended or started.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    aborted : bool
        Whether an operation that ended left HEAD's branch where it was.

    Returns
    -------
    list[Event]
        The end of the old operation, then the start of the new one.
    """
    was, now = change.before["operation"], change.after["operation"]
    events: list[Event] = []
    if was is not None and was != now:
        where = f"{_place(change.after)} points at {_at(change, change.after['head'])}" if change.after["head"] else f"{_place(change.after)} has no commits"
        if was == "bisect":
            events.append({"kind": "bisect-finished", "text": "The bisect is over."})
        elif aborted:
            events.append({"kind": f"{was}-aborted", "text": f"The {was} was aborted: {where}, as before it started."})
        else:
            events.append({"kind": f"{was}-finished", "text": f"The {was} is finished: {where}."})
    if now is not None and now != was:
        on = f" on {_place(change.after)}" if change.after["branch"] is not None else ""
        events.append({"kind": f"{now}-started", "text": STARTED[now].format(on=on)})
    return events


def _conflict_events(change: _Change, aborted: bool) -> list[Event]:
    """
    Tell which files came into conflict and which were resolved.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    aborted : bool
        Whether the operation was aborted, which ends its conflicts without resolving them.

    Returns
    -------
    list[Event]
        New conflicts, then resolved ones.
    """
    was = {file["path"] for file in change.before["files"] if file["conflicted"]}
    now = {file["path"]: file for file in change.after["files"] if file["conflicted"]}
    after = {file["path"]: file for file in change.after["files"]}
    news: list[FileNews] = [
        ("conflict", path, f"`{path}` has a conflict: Git could not combine the two versions by itself.") for path in sorted(now.keys() - was)
    ]
    for path in [] if aborted else sorted(was - now.keys()):
        staged = path in after and after[path]["index"] is not None
        news.append(("conflict-resolved", path, f"`{path}` is resolved: " + ("the staging area holds its new version." if staged else "it was removed.")))
    return _told(news)


def _commit_events(change: _Change, found: tuple[str, Commit] | None) -> list[Event]:
    """
    Tell about the commit just made or amended at HEAD.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    found : tuple[str, Commit] | None
        What `_new_head_commit` found.

    Returns
    -------
    list[Event]
        Zero or one event.
    """
    if found is None:
        return []
    kind, commit = found
    place, parents = _place(change.after), commit["parents"]
    if kind == "commit-replaced":
        text = f"Commit {_short(change, change.before['head'] or '')} was replaced by {_at(change, commit['hash'])} on {place}: the new commit has the same parent."
    elif len(parents) > 1:
        joined = ", ".join(_short(change, parent) for parent in parents[:-1]) + f" and {_short(change, parents[-1])}"
        text = f"Merge commit {_at(change, commit['hash'])} was made on {place}; its parents are {joined}."
    elif parents:
        text = f"Commit {_at(change, commit['hash'])} was made on {place}; its parent is {_short(change, parents[0])}."
    else:
        text = f"Commit {_at(change, commit['hash'])} was made on {place}; it has no parent, so it starts the history."
    return [{"kind": kind, "text": text}]


def _head_events(change: _Change) -> list[Event]:
    """
    Tell that HEAD switched branch, became detached, or moved while detached.

    A rebase or bisect that starts detaches HEAD; its own event says so.

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    list[Event]
        Zero or one event.
    """
    before, after = change.before, change.after
    was, now, head = before["branch"], after["branch"], after["head"]
    where = f", at {_at(change, head)}" if head is not None else ", which has no commits yet"
    events: list[Event] = []
    if was != now and was is not None and now is not None:
        events.append({"kind": "branch-switched", "text": f"HEAD switched from branch `{was}` to branch `{now}`{where}."})
    elif was != now and now is not None:
        events.append({"kind": "branch-switched", "text": f"HEAD is now on branch `{now}`{where}."})
    elif was is not None and now is None and head is not None and after["operation"] not in ("rebase", "bisect"):
        events.append({"kind": "head-detached", "text": f"HEAD is detached: it points at commit {_at(change, head)} directly, not at a branch."})
    elif was is None and now is None and head is not None and before["head"] != head:
        events.append({"kind": "head-moved", "text": f"HEAD moved to {_at(change, head)}; it is still detached."})
    return events


def _branch_events(change: _Change, found: tuple[str, Commit] | None, renamed: tuple[str, str] | None) -> list[Event]:
    """
    Tell which branches were renamed, created, moved or deleted.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    found : tuple[str, Commit] | None
        The commit just made at HEAD, which already explains its branch's move.
    renamed : tuple[str, str] | None
        A branch's old and new names.

    Returns
    -------
    list[Event]
        The rename, then the branches created, moved and deleted, each by name.
    """
    explained = {change.after["branch"]} if found is not None else set()
    events: list[Event] = []
    if renamed is not None:
        events.append({"kind": "branch-renamed", "text": f"Branch `{renamed[0]}` was renamed to `{renamed[1]}`."})
        explained |= set(renamed)
    created, moved, deleted = _ref_changes(change, "branch")
    events += [{"kind": "branch-created", "text": f"Branch `{name}` was created at {_at(change, now)}."} for name, now in created if name not in explained]
    events += [{"kind": "branch-moved", "text": _branch_moved_text(change, name, was, now)} for name, was, now in moved if name not in explained]
    events += [{"kind": "branch-deleted", "text": f"Branch `{name}` was deleted; it pointed at {_at(change, was)}."} for name, was in deleted if name not in explained]
    return events


def _branch_moved_text(change: _Change, name: str, was: str, now: str) -> str:
    """
    Tell how a branch moved.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    name : str
        The branch.
    was : str
        The commit it pointed at.
    now : str
        The commit it points at.

    Returns
    -------
    str
        The sentence.
    """
    ancestry = _ancestry(change, was, now)
    text = f"Branch `{name}` moved from {_short(change, was)} to {_at(change, now)}."
    if ancestry == "forward":
        ahead = _count(len(_reachable(change, now) - _reachable(change, was)), "commit", "commits")
        text = f"Branch `{name}` moved forward by {ahead}, from {_short(change, was)} to {_at(change, now)}."
    elif ancestry == "back":
        text = f"Branch `{name}` moved back from {_short(change, was)} to {_at(change, now)}."
    elif ancestry == "rewritten":
        text = f"Branch `{name}` now points at {_at(change, now)} instead of {_short(change, was)}: its history was rewritten."
    return text


def _tag_events(change: _Change) -> list[Event]:
    """
    Tell which tags were created, moved or deleted.

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    list[Event]
        The tags created, moved and deleted, each by name.
    """
    created, moved, deleted = _ref_changes(change, "tag")
    events: list[Event] = [{"kind": "tag-created", "text": f"Tag `{name}` was created at {_at(change, now)}."} for name, now in created]
    events += [{"kind": "tag-moved", "text": f"Tag `{name}` now points at {_at(change, now)} instead of {_short(change, was)}."} for name, was, now in moved]
    events += [{"kind": "tag-deleted", "text": f"Tag `{name}` was deleted."} for name, _ in deleted]
    return events


def _remote_events(change: _Change) -> list[Event]:
    """
    Tell which remote-tracking branches were created, moved or deleted (by a fetch, pull or push).

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    list[Event]
        One ``remote-updated`` event per remote-tracking branch: created, moved, then deleted, each by name.
    """
    created, moved, deleted = _ref_changes(change, "remote")
    texts = [f"Remote-tracking branch `{name}` was created at {_at(change, now)}{_arrived(change, set(), now)}." for name, now in created]
    texts += [
        f"Remote-tracking branch `{name}` moved from {_short(change, was)} to {_at(change, now)}{_arrived(change, _reachable(change, was), now)}."
        for name, was, now in moved
    ]
    texts += [f"Remote-tracking branch `{name}` was deleted." for name, _ in deleted]
    return [{"kind": "remote-updated", "text": text} for text in texts]


def _arrived(change: _Change, had: set[str], now: str) -> str:
    """
    Count the commits a remote-tracking branch brought that the repository did not have.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    had : set[str]
        Commits the remote-tracking branch already led to.
    now : str
        The commit it points at now.

    Returns
    -------
    str
        A clause such as ``; 2 new commits came from the remote``, or nothing.
    """
    known = {commit["hash"] for commit in change.before["commits"]}
    arrived = len(_reachable(change, now) - had - known)
    return f"; {_count(arrived, 'new commit', 'new commits')} came from the remote" if arrived else ""


def _push_events(change: _Change) -> list[Event]:
    """
    Tell what pushes did to a bare repository's branches and tags.

    Parameters
    ----------
    change : _Change
        The two snapshots of a bare repository.

    Returns
    -------
    list[Event]
        One ``push-received`` event per ref: branches then tags, each created, moved, then deleted.
    """
    events: list[Event] = []
    for kind in ("branch", "tag"):
        created, moved, deleted = _ref_changes(change, kind)
        events += [{"kind": "push-received", "text": f"A push created {kind} `{name}` at {_at(change, now)}."} for name, now in created]
        for name, was, now in moved:
            forced = _ancestry(change, was, now) in ("back", "rewritten")
            news = f" It was a force push: {_short(change, was)} is no longer in its history." if forced else ""
            events.append({"kind": "push-received", "text": f"A push moved {kind} `{name}` from {_short(change, was)} to {_at(change, now)}.{news}"})
        events += [{"kind": "push-received", "text": f"A push deleted {kind} `{name}`."} for name, _ in deleted]
    return events


def _stash_events(change: _Change) -> list[Event]:
    """
    Tell that changes were put in the stash or taken out of it.

    Parameters
    ----------
    change : _Change
        The two snapshots.

    Returns
    -------
    list[Event]
        Zero or one event.
    """
    was, now = change.before["stash"], change.after["stash"]
    holds = f"the stash now holds {_count(now, 'entry', 'entries')}"
    files_changed = [(file["index"], file["folder"]) for file in change.before["files"]] != [(file["index"], file["folder"]) for file in change.after["files"]]
    events: list[Event] = []
    if now > was:
        events.append({"kind": "stash-saved", "text": f"Changes were put away in the stash; {holds}."})
    elif now < was and files_changed:
        events.append({"kind": "stash-applied", "text": f"Changes from the stash were applied and their entry removed; {holds}."})
    elif now < was:
        events.append({"kind": "stash-dropped", "text": f"A stash entry was dropped; {holds}."})
    return events


def _file_events(change: _Change, tidied: bool, committed: bool) -> list[Event]:
    """
    Tell what changed in the staging area and the working folder, file by file.

    A file that matched HEAD before and after only followed HEAD, and is not told.

    Parameters
    ----------
    change : _Change
        The two snapshots.
    tidied : bool
        Whether a stash or an aborted operation put files back, which its own event tells.
    committed : bool
        Whether a commit was just made at HEAD.

    Returns
    -------
    list[Event]
        Staging-area events, then working-folder events, then ignore-rule events.
    """
    was = {file["path"]: file for file in change.before["files"]}
    now = {file["path"]: file for file in change.after["files"]}
    staging: list[FileNews] = []
    folder: list[FileNews] = []
    ignoring: list[FileNews] = []
    for path in sorted(was.keys() | now.keys()):
        old, new = was.get(path, _absent(path)), now.get(path, _absent(path))
        followed_head = _clean(old) and _clean(new)
        put_back = tidied and _clean(new)
        if old["conflicted"] or new["conflicted"] or followed_head or put_back:
            continue
        staging += _staging_news(old, new, committed)
        folder += _folder_news(old, new)
        ignoring += _ignore_news(old, new)
    return [*_told(staging), *_told(folder), *_told(ignoring)]


def _absent(path: str) -> FileEntry:
    """
    Give the entry of a path that a snapshot does not list.

    Parameters
    ----------
    path : str
        The path.

    Returns
    -------
    FileEntry
        The path, in no area.
    """
    return {"path": path, "head": None, "index": None, "folder": None, "ignored": False, "conflicted": False}


def _clean(file: FileEntry) -> bool:
    """
    Tell whether a file is the same in HEAD, the staging area and the working folder.

    Parameters
    ----------
    file : FileEntry
        The file.

    Returns
    -------
    bool
        True if all three areas agree (a file in none of them counts).
    """
    return file["head"] == file["index"] == file["folder"]


def _staging_news(old: FileEntry, new: FileEntry, committed: bool) -> list[FileNews]:
    """
    Tell how a file changed in the staging area.

    Parameters
    ----------
    old : FileEntry
        The file before.
    new : FileEntry
        The file after.
    committed : bool
        Whether a commit was just made, which moves HEAD to what was staged.

    Returns
    -------
    list[FileNews]
        Zero or one piece of news.
    """
    path = new["path"]
    if old["index"] == new["index"]:
        return []
    news: list[FileNews] = []
    if new["index"] == new["head"] and not committed:
        again = "it is untracked again" if new["index"] is None else "the staging area has the last commit's version again"
        news.append(("file-unstaged", path, f"`{path}` was unstaged: {again}."))
    elif new["index"] is None:
        news.append(("file-staged", path, f"`{path}` was staged for deletion."))
    elif old["index"] is None:
        news.append(("file-staged", path, f"`{path}` was staged as a new file."))
    else:
        news.append(("file-staged", path, f"`{path}` was staged."))
    return news


def _folder_news(old: FileEntry, new: FileEntry) -> list[FileNews]:
    """
    Tell how a file changed in the working folder.

    Parameters
    ----------
    old : FileEntry
        The file before.
    new : FileEntry
        The file after.

    Returns
    -------
    list[FileNews]
        Zero or one piece of news.
    """
    path, note = new["path"], _folder_note(new)
    if old["folder"] == new["folder"]:
        return []
    news: list[FileNews] = []
    if old["folder"] is None:
        news.append(("file-created", path, f"`{path}` was created in the working folder.{note}"))
    elif new["folder"] is None:
        news.append(("file-deleted", path, f"`{path}` was deleted from the working folder.{note}"))
    else:
        news.append(("file-changed", path, f"`{path}` changed in the working folder.{note}"))
    return news


def _folder_note(file: FileEntry) -> str:
    """
    Say how a file in the working folder now stands against the staging area.

    Parameters
    ----------
    file : FileEntry
        The file after its change.

    Returns
    -------
    str
        A sentence starting with a space, or nothing for an untracked file that was deleted.
    """
    note = ""
    if file["folder"] is None and file["index"] is not None:
        note = " The deletion is not staged yet."
    elif file["folder"] is None:
        note = ""
    elif file["ignored"]:
        note = " Git ignores it."
    elif file["index"] is None:
        note = " It is untracked: Git does not track it yet."
    elif file["folder"] == file["index"]:
        note = " It matches the staging area."
    else:
        note = " The change is not staged yet."
    return note


def _ignore_news(old: FileEntry, new: FileEntry) -> list[FileNews]:
    """
    Tell that an unchanged file became ignored, or stopped being ignored.

    Parameters
    ----------
    old : FileEntry
        The file before.
    new : FileEntry
        The file after.

    Returns
    -------
    list[FileNews]
        Zero or one piece of news.
    """
    path = new["path"]
    if old["folder"] is None or old["folder"] != new["folder"] or old["ignored"] == new["ignored"]:
        return []
    news: list[FileNews] = []
    if new["ignored"]:
        news.append(("file-ignored", path, f"`{path}` is now ignored by Git."))
    else:
        news.append(("file-unignored", path, f"`{path}` is no longer ignored: it is untracked."))
    return news


def _told(news: list[FileNews]) -> list[Event]:
    """
    Turn news about files into events, telling many of one kind together.

    Parameters
    ----------
    news : list[FileNews]
        Kind, path and sentence, in order.

    Returns
    -------
    list[Event]
        One event per piece of news, or one per kind for more than `MAX_FILE_EVENTS` of it,
        in the order each kind first appears.
    """
    by_kind: dict[str, list[tuple[str, str]]] = {}
    for kind, path, text in news:
        by_kind.setdefault(kind, []).append((path, text))
    events: list[Event] = []
    for kind, items in by_kind.items():
        if len(items) > MAX_FILE_EVENTS:
            names = ", ".join(f"`{path}`" for path, _ in items[:NAMES_SHOWN]) + f" and {len(items) - NAMES_SHOWN} more"
            events.append({"kind": kind, "text": SUMMARIES[kind].format(count=len(items), names=names)})
        else:
            events.extend({"kind": kind, "text": text} for _, text in items)
    return events
