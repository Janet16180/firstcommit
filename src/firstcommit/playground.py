"""
The two-person playground: you and Alex share one remote, and each of you has the same buttons.

GitHub is the lab's bare repository; your clone is the lab's project, where the player's
terminal opens, and Alex's is the lab's teammate folder. Every button runs one fixed line in the
clone of the person who pressed it, so what the figure draws afterwards is what git did, and
the player can type the same line in the terminal and get the same result. No line takes text
from the player: file names come from `FILES`, and a commit's message is built from them.

A line may depend on the state it is pressed in (`buttons` gives each one as it stands now):
``git commit`` keeps git's message while a merge is paused, and Edit appends the writer's next
numbered line. Some buttons are shown only when they fit: ``git pull --no-rebase`` while the
branches have diverged, and ``git merge --abort`` with Keep mine and Keep theirs for each
conflicted file while a merge is paused. A button pressed out of its state still runs, and git
answers. A button is off, with its reason, only where pressing it would act outside the
project: when the person's folder is gone or is a link, and Edit on a file that is not a plain
file any more.

Git lines run as on the player's terminal (`firstcommit.gitcmd.run_on_terminal`), with the
identity the terminal would use: yours from the game's global configuration, Alex's from Alex's
clone. Edit is written in Python, never through a link, with exactly the bytes its line writes.
"""

import os
import re
import shlex
import stat
from collections.abc import Mapping
from pathlib import Path

from firstcommit import gitcmd, repomap
from firstcommit.lab import Lab
from firstcommit.records import FILE_MODE, ButtonView, ConfigFacts, Facts, FileKind, FolderFacts, Press, Snapshot, Who

ALEX = gitcmd.Person("Alex", "alex@example.com")
"""Alex's identity, set in Alex's clone's own configuration by `setup`."""
PEOPLE: dict[Who, str] = {"you": "You", "alex": "Alex"}
"""The playground's people, and how each one's Edit signs the line it appends."""
FILES = ("README.md", "notes.txt")
"""The files the buttons act on, in bar order; both people have both."""
FIRST_LINES = {"README.md": "# Project", "notes.txt": "Notes"}
"""Each file's content in GitHub's first commit."""

LINES = {
    "status": "git status",
    "push": "git push",
    "fetch": "git fetch",
    "pull": "git pull",
    "pull-no-rebase": "git pull --no-rebase --no-edit",
    "merge-abort": "git merge --abort",
    "add": "git add {file}",
    "keep-ours": "git restore --ours {file}",
    "keep-theirs": "git restore --theirs {file}",
}
"""The lines that do not depend on the state, by kind; ``commit`` and ``edit`` are built by `_line`."""
LABELS = {
    "status": "git status",
    "commit": "git commit",
    "push": "git push",
    "fetch": "git fetch",
    "pull": "git pull",
    "pull-no-rebase": "git pull --no-rebase",
    "merge-abort": "git merge --abort",
    "edit": "Edit {file}",
    "add": "git add {file}",
    "keep-ours": "Keep mine in {file}",
    "keep-theirs": "Keep theirs in {file}",
}
"""What each kind of button says on it."""
FILE_KINDS = ("edit", "add", "keep-ours", "keep-theirs")
"""The kinds of button that act on one of `FILES`; their ids are ``<kind>:<file>``."""
MAIN = ("status", "commit", "push", "fetch", "pull")
"""The buttons every bar starts with, in order; then each file's Edit and git add."""
BUTTON_IDS = frozenset([*(kind for kind in LABELS if kind not in FILE_KINDS), *(f"{kind}:{name}" for kind in FILE_KINDS for name in FILES)])
"""Every button id that can ever be shown, whatever the state."""

FALLBACK_MESSAGE = "Save my work"
"""The commit message when nothing is staged, or a staged path is not one of `FILES`."""
VERBS = {"added": "add", "modified": "update", "typechange": "update", "deleted": "delete"}
GONE = "The project folder is gone: start the playground again."
READ_LIMIT = 64 * 1024
"""How much of a button file is read for its facts; a longer file is numbered from its start only."""
MARKER = re.compile(rb"^<<<<<<< ", re.MULTILINE)
"""The line git starts a conflict with in a file."""


class ButtonOffError(Exception):
    """A button pressed while it is off; the message is the reason the button shows."""


def setup_github(lab: Lab) -> None:
    """
    Create a lab's stand-in GitHub: an empty bare repository on ``main``, keeping a reflog.

    A bare repository keeps no reflog unless asked (git-config(1), ``core.logAllRefUpdates``), so
    this one sets it: a forced push can then be seen and undone there, as on a real host's
    records.

    Parameters
    ----------
    lab : Lab
        The lab; its root exists, and its GitHub folder does not.

    Raises
    ------
    subprocess.CalledProcessError
        If git fails, for example because GitHub already exists.
    """
    lab.github.parent.mkdir(exist_ok=True)
    gitcmd.output(lab.github.parent, "init", "--quiet", "--bare", "--initial-branch=main", lab.github.name)
    gitcmd.output(lab.github, "config", "core.logAllRefUpdates", "true")


def setup(lab: Lab) -> None:
    """
    Create the playground: GitHub with one commit of `FILES`, and a clone of it for each person.

    Each clone reaches GitHub by `Lab.github_url`. Only Alex's clone has an identity of its own.

    Parameters
    ----------
    lab : Lab
        The lab; its root exists, and its GitHub, project and teammate folders do not.

    Raises
    ------
    FileExistsError
        If the teammate's folder already exists.
    subprocess.CalledProcessError
        If git fails, for example because GitHub or the project already exists.
    """
    setup_github(lab)
    entries = [f"{FILE_MODE} blob {_blob(lab, FIRST_LINES[name] + "\n")}\t{name}\n" for name in FILES]
    tree = gitcmd.output(lab.github, "mktree", stdin="".join(entries)).strip()
    commit = gitcmd.output(lab.github, "commit-tree", tree, "-m", "Start the project").strip()
    gitcmd.output(lab.github, "update-ref", "refs/heads/main", commit)
    lab.teammate.parent.mkdir()
    for person in PEOPLE:
        folder = _clone(lab, person)
        gitcmd.output(folder.parent, "clone", "--quiet", str(lab.github), folder.name)
        gitcmd.output(folder, "remote", "set-url", "origin", lab.github_url(folder))
    gitcmd.output(lab.teammate, "config", "user.name", ALEX.name)
    gitcmd.output(lab.teammate, "config", "user.email", ALEX.email)


def buttons(lab: Lab, snapshots: Mapping[Who, Snapshot]) -> dict[Who, list[ButtonView]]:
    """
    Give each person's bar as it stands now: the buttons shown, in order, each with its line and whether it is off.

    Parameters
    ----------
    lab : Lab
        The lab, set up by `setup`; the player may have changed anything since.
    snapshots : Mapping[Who, Snapshot]
        Each person's clone, as just read.

    Returns
    -------
    dict[Who, list[ButtonView]]
        Each person's buttons: `MAIN`, Edit and git add for each of `FILES`, then
        ``merge-abort`` with Keep mine, Keep theirs and git add for each conflicted file while a
        merge is paused, then ``pull-no-rebase`` while the branches have diverged.
    """
    return {person: [_view(button, person, snapshots[person], folder_facts(lab, person)) for button in _shown(snapshots[person])] for person in PEOPLE}


def press(lab: Lab, person: Who, button: str) -> Press:
    """
    Run one person's button in their clone, in the state it is in now.

    Parameters
    ----------
    lab : Lab
        The lab, set up by `setup`; the player may have changed anything since.
    person : Who
        Who pressed.
    button : str
        One of `BUTTON_IDS`, shown now or not.

    Returns
    -------
    Press
        The line that ran and what the terminal would have shown. A command that fails is
        reported with its non-zero status.

    Raises
    ------
    KeyError
        If ``person`` or ``button`` is not one of the playground's.
    ButtonOffError
        If the button is off now; nothing runs.
    subprocess.TimeoutExpired
        If a git line runs longer than `firstcommit.gitcmd.TIMEOUT` seconds.
    """
    if button not in BUTTON_IDS:
        raise KeyError(f"no button {button!r} in the playground")
    clone, folder = _clone(lab, person), folder_facts(lab, person)
    view = _view(button, person, repomap.snapshot(clone), folder)
    if view["off"]:
        raise ButtonOffError(view["off"])
    kind, _, name = button.partition(":")
    status, output = 0, ""
    if kind == "edit":
        _append(clone / name, _edit_text(person, name, folder))
    else:
        status, output = gitcmd.run_on_terminal(clone, *shlex.split(view["line"])[1:])
    return {"person": person, "button": button, "command": view["line"], "status": status, "output": output}


def facts(lab: Lab, person: Who, snap: Snapshot, github: Snapshot | None) -> Facts:
    """
    Read what a press's explanation is chosen from, just before the press.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : Who
        Who is about to press.
    snap : Snapshot
        Their clone, as just read.
    github : Snapshot | None
        The stand-in GitHub, as just read, or None when the lab has none.

    Returns
    -------
    Facts
        GitHub (None when it holds no repository), the person's folder and configuration.
    """
    there = github if github is not None and github["exists"] else None
    return {"github": there, "folder": folder_facts(lab, person), "config": config_facts(lab, person, snap)}


def folder_facts(lab: Lab, person: Who) -> FolderFacts:
    """
    Read a person's working folder, as the buttons and their explanations need it.

    Each button file is looked at without following a link, and only its first `READ_LIMIT`
    bytes are read.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : Who
        Whose folder.

    Returns
    -------
    FolderFacts
        Whether the folder can be used and, if so, what each of `FILES` is there.
    """
    path = _clone(lab, person)
    usable = path.is_dir() and path.resolve() == lab.root.resolve() / path.relative_to(lab.root)
    kinds = {name: _kind(path / name) for name in FILES} if usable else {}
    starts = {name: _start_of(path / name) for name, kind in kinds.items() if kind == "file"}
    return {
        "usable": usable,
        "kinds": kinds,
        "lines": {name: start.count(b"\n") for name, start in starts.items()},
        "marked": sorted(name for name, start in starts.items() if MARKER.search(start)),
        "locked": usable and (path / ".git" / "index.lock").exists(),
    }


def config_facts(lab: Lab, person: Who, snap: Snapshot) -> ConfigFacts:
    """
    Read what a person's repository configuration holds, with read-only git commands.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : Who
        Whose repository.
    snap : Snapshot
        Their clone, as just read.

    Returns
    -------
    ConfigFacts
        Whether git has a name and an email for them (from any configuration file), whether the
        repository has a remote, and whether its current branch has an upstream.
    """
    path = _clone(lab, person)
    remote = snap["exists"] and gitcmd.run(path, "remote").stdout.strip() != ""
    upstream = snap["exists"] and snap["branch"] is not None and gitcmd.run(path, "config", f"branch.{snap['branch']}.merge").returncode == 0
    return {
        "name": gitcmd.run(path, "config", "user.name").returncode == 0,
        "email": gitcmd.run(path, "config", "user.email").returncode == 0,
        "remote": remote,
        "upstream": upstream,
    }


def message(snap: Snapshot) -> str:
    """
    Name what the staging area would commit, as a commit subject.

    Parameters
    ----------
    snap : Snapshot
        The repository.

    Returns
    -------
    str
        "Update notes.txt", "Add notes.txt and update README.md"...: one clause per kind of
        change, in the order add, update, delete; `FALLBACK_MESSAGE` when nothing is staged or a
        staged path is not one of `FILES`, so a name the player chose never reaches a line.
    """
    changes = {entry["path"]: VERBS[entry["index_change"]] for entry in snap["files"] if entry["index_change"] is not None}
    clauses = [f"{verb} {_joined(sorted(path for path, said in changes.items() if said == verb))}" for verb in ("add", "update", "delete") if verb in changes.values()]
    subject = FALLBACK_MESSAGE
    if clauses and all(path in FILES for path in changes):
        joined = _joined(clauses)
        subject = joined[0].upper() + joined[1:]
    return subject


def _shown(snap: Snapshot) -> list[str]:
    """
    List the buttons a person sees in this state, in bar order.

    Parameters
    ----------
    snap : Snapshot
        The person's clone.

    Returns
    -------
    list[str]
        Button ids, each once.
    """
    ids = [*MAIN, *(f"{kind}:{name}" for name in FILES for kind in ("edit", "add"))]
    if snap["operation"] == "merge":
        unmerged = [path for path in repomap.conflicted(snap) if path in FILES]
        ids += ["merge-abort", *(f"{kind}:{path}" for path in unmerged for kind in ("keep-ours", "keep-theirs", "add"))]
    if _diverged(snap):
        ids.append("pull-no-rebase")
    return list(dict.fromkeys(ids))


def _view(button: str, person: Who, snap: Snapshot, folder: FolderFacts) -> ButtonView:
    """
    Give a button as it stands in this state.

    Parameters
    ----------
    button : str
        One of `BUTTON_IDS`.
    person : Who
        Whose button.
    snap : Snapshot
        The person's clone.
    folder : FolderFacts
        The person's working folder.

    Returns
    -------
    ButtonView
        Its id, label, line and the reason it is off (empty when it is on).
    """
    kind, _, name = button.partition(":")
    off = ""
    if not folder["usable"]:
        off = GONE
    elif kind == "edit" and folder["kinds"][name] == "other":
        off = f"{name} is not a plain file any more."
    return {"id": button, "label": LABELS[kind].format(file=name), "line": _line(kind, name, person, snap, folder), "off": off}


def _line(kind: str, name: str, person: Who, snap: Snapshot, folder: FolderFacts) -> str:
    """
    Give the line a button runs in this state.

    Parameters
    ----------
    kind : str
        The button's kind.
    name : str
        Its file, or empty.
    person : Who
        Whose button.
    snap : Snapshot
        The person's clone.
    folder : FolderFacts
        The person's working folder.

    Returns
    -------
    str
        One line of bash the player could type with the same effect.
    """
    if kind == "commit":
        line = "git commit --no-edit" if snap["operation"] == "merge" else f'git commit -m "{message(snap)}"'
    elif kind == "edit":
        line = f'echo "{_edit_text(person, name, folder)}" >> {name}'
    else:
        line = LINES[kind].format(file=name)
    return line


def _edit_text(person: Who, name: str, folder: FolderFacts) -> str:
    """
    Give the line Edit appends: its writer and its number in the file.

    Parameters
    ----------
    person : Who
        Who edits.
    name : str
        One of `FILES`.
    folder : FolderFacts
        The person's working folder.

    Returns
    -------
    str
        Such as ``You: line 3``, without its line break.
    """
    return f"{PEOPLE[person]}: line {folder['lines'].get(name, 0) + 1}"


def _append(path: Path, text: str) -> None:
    """
    Append a line to a file as ``echo "<text>" >> <file>`` does, creating it if needed, never through a link.

    Parameters
    ----------
    path : Path
        The file.
    text : str
        The line, without its line break.
    """
    # 0o666 less the umask, as bash creates a file for >>.
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o666)
    with os.fdopen(descriptor, "ab") as file:
        file.write(f"{text}\n".encode())


def _kind(path: Path) -> FileKind:
    """
    Tell what a path is, without following a link.

    Parameters
    ----------
    path : Path
        The path.

    Returns
    -------
    FileKind
        ``file`` for a regular file, ``missing`` when nothing is there, ``other`` for anything
        else (a folder, a link) or a path that cannot be looked at.
    """
    try:
        found: FileKind = "file" if stat.S_ISREG(os.lstat(path).st_mode) else "other"
    except FileNotFoundError:
        found = "missing"
    except PermissionError:
        found = "other"
    return found


def _start_of(path: Path) -> bytes:
    """
    Read the start of a file, never through a link.

    Parameters
    ----------
    path : Path
        A regular file.

    Returns
    -------
    bytes
        Its first `READ_LIMIT` bytes; nothing when it is gone or cannot be read.
    """
    try:
        descriptor: int | None = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except (FileNotFoundError, PermissionError):  # the player may delete or lock it at any time
        descriptor = None
    start = b""
    if descriptor is not None:
        with os.fdopen(descriptor, "rb") as file:
            start = file.read(READ_LIMIT)
    return start


def _diverged(snap: Snapshot) -> bool:
    """
    Tell whether the current branch and ``origin/<branch>`` each have commits the other lacks.

    Parameters
    ----------
    snap : Snapshot
        A clone.

    Returns
    -------
    bool
        True when neither commit is in the other's history.
    """
    theirs = next((ref["target"] for ref in snap["refs"] if ref["kind"] == "remote" and ref["name"] == f"origin/{snap['branch']}"), None)
    head = snap["head"]
    return theirs is not None and head is not None and theirs not in repomap.history(snap, head) and head not in repomap.history(snap, theirs)


def _joined(items: list[str]) -> str:
    """
    Join words as a sentence lists them.

    Parameters
    ----------
    items : list[str]
        One or more words.

    Returns
    -------
    str
        "a", "a and b", "a, b and c".
    """
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} and {items[-1]}"


def _blob(lab: Lab, content: str) -> str:
    """
    Store a file's content in GitHub's object database.

    Parameters
    ----------
    lab : Lab
        The lab, with its GitHub.
    content : str
        The content.

    Returns
    -------
    str
        The blob's id.
    """
    return gitcmd.output(lab.github, "hash-object", "-w", "--stdin", stdin=content).strip()


def _clone(lab: Lab, person: Who) -> Path:
    """
    Find a person's clone in the lab.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : Who
        Who.

    Returns
    -------
    Path
        Your clone is the lab's project, where the player's terminal opens; Alex's is the
        lab's teammate folder.
    """
    return {"you": lab.project, "alex": lab.teammate}[person]
