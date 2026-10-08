"""
Collision: a conflict is a question. Read both sides, choose, add, and commit the merge.

Wave 2, conflict 6-3 (docs/drafts/chapters-3-7.md), guided. Setup makes a repository where
``main`` moved the docking to bay 3 while ``scout`` moved it to bay 4, its message saying bay 3
is closed for repairs. The goals: the merge paused with ``docking.txt`` in conflict; the file
read with ``cat`` (typed: reading both sides is the lesson); bay 4 in the working folder with no
markers; the file added, so no conflict is left; and ``main``'s last commit holding bay 4 with
``scout`` in its history. Markers or bay 3 committed are named, with the way to fix them.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Collision"
DIFFICULTY = 2
XP = 180
COMMAND = "git restore --theirs"
PAR = 5
VIEW = "sides"
CARD = kit.CommandCard(
    command="git restore --theirs <file>",
    text="During a merge conflict, puts the incoming branch's version of the file in the working folder; `--ours` puts your branch's. `git add` then marks the conflict solved. During a rebase the two can appear swapped.",
)
SCENE = [
    kit.SceneFrame(art="collision", text="Both crews changed the same line of the docking plan, and the file cracked."),
    kit.SceneFrame(art="collision", text="A conflict is Git asking a question it cannot answer alone: which version is right?"),
]

DOCKING = "docking.txt"
SCOUT = "scout"
START = "Dock at bay 2\n"
OURS = "Dock at bay 3\n"
THEIRS = "Dock at bay 4\n"
MARKER = "<<<<<<<"
MERGE = r"git merge\b"
READ = r"cat docking\.txt\b"

BRIEFING = """
`main` moved the docking to bay 3. `scout` moved it to bay 4, and its commit says why: bay 3 is
closed for repairs. Bring `scout` into `main`, and answer the conflict with the right bay.

The mission is done when you have read both sides of the conflict with `cat docking.txt`, and
`main`'s last commit holds `scout`'s work and docks at bay 4, with no conflict markers.
"""

HINTS = [
    "`git merge --no-edit scout` stops with `docking.txt` in conflict; `cat docking.txt` shows both sides between markers.",
    "Bay 4 is `scout`'s side, the incoming one: `git restore --theirs docking.txt` keeps it.",
    "`git add docking.txt` marks the conflict solved; `git commit --no-edit` then finishes the merge with Git's message.",
    "Every line of the mission, in order:\n\n    $ git merge --no-edit scout\n    $ cat docking.txt\n    $ git restore --theirs docking.txt\n    $ git add docking.txt\n    $ git commit --no-edit",
]

DEBRIEF = """
The merge stopped because both sides changed the same line, and Git cannot know which is right.
`cat docking.txt` showed both: yours between `<<<<<<<` and `=======`, `scout`'s between `=======` and
`>>>>>>>`. `scout`'s commit gave the reason, so you kept its side with `git restore --theirs`, or by
writing the file yourself. `git add` marked the conflict solved, and `git commit --no-edit` finished
the merge with two parents.

A conflict is a question, not a breakage: nothing was lost while the merge was paused, and
`git merge --abort` was always there.

Commands to keep:

    $ git merge --no-edit scout          # stops when both sides changed the same lines
    $ cat docking.txt                    # read both sides between the markers
    $ git restore --theirs docking.txt   # keep the incoming side (--ours: yours)
    $ git add docking.txt                # mark the conflict solved
    $ git commit --no-edit               # finish the merge
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_STARTED = "Bring `scout` in: `git merge --no-edit scout`."
CONFLICT = "The merge stopped: `docking.txt` is in conflict, and Git waits for your answer."
READ_BOTH = "Both sides are there: bay 3 is yours, bay 4 is `scout`'s."
NOT_READ = "Read both sides of the conflict: `cat docking.txt`."
MARKERS = "`docking.txt` still holds the conflict markers. Keep one side: `git restore --theirs docking.txt`."
BAY_3 = "`docking.txt` docks at bay 3, which is closed for repairs. `scout`'s side is right: `git restore --theirs docking.txt`."
CHOSEN = "`docking.txt` docks at bay 4, with no markers."
OTHER = "`docking.txt` should say `Dock at bay 4`, the incoming side: `git restore --theirs docking.txt`."
NOT_ADDED = "Mark the conflict solved: `git add docking.txt`."
ADDED = "No conflict left: the staging area holds bay 4."
NOT_COMMITTED = "Finish the merge: `git commit --no-edit`."
NOT_BAY_4_COMMITTED = "`main`'s last commit does not dock at bay 4. Write bay 4 in `docking.txt`, then add it and commit again."
BAY_3_COMMITTED = "`main`'s last commit docks at bay 3, which is closed. Write bay 4 in `docking.txt` (`git restore --source=scout docking.txt`), then add it and commit again."
DONE = "`main`'s last commit holds `scout`'s work and docks at bay 4."
ANSWER_FIRST = "Git cannot commit while a file is in conflict. Answer it first: choose a side, then `git add` the file."

SIDE = "That side is in the working folder now. The conflict stays open until you `git add` the file."

REACTIONS = [
    kit.ReactionRule(line=r"git commit\b", mood="err", text=ANSWER_FIRST, outcome="failed", repository=True),
    kit.ReactionRule(line=r"git restore (--ours|--theirs)\b", mood="info", text=SIDE, outcome="ok", repository=True),
]


def _merging(lab: kit.Lab) -> bool:
    """
    Tell whether the merge of ``scout`` has started: paused, or finished into ``main``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    bool
        True while a merge is paused, or once ``main`` holds ``scout``.
    """
    paused = kit.snapshot(lab.project)["operation"] == "merge"
    scout = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"refs/heads/{SCOUT}").stdout.strip()
    return paused or (bool(scout) and kit.is_ancestor(lab.project, scout, "refs/heads/main"))


def watch_merge(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the merge of ``scout`` has started.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    message = CONFLICT if _merging(lab) else NOT_STARTED
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == CONFLICT, message)


def watch_read(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``cat docking.txt`` worked after the merge started.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; the merge comes first.
    """
    merging = watch_merge(lab, state, typed)
    read = kit.typed(kit.after(typed, MERGE), READ, "ok")
    verdict = kit.Verdict(read, READ_BOTH if read else NOT_READ)
    return verdict if merging.solved else merging


def _kind(text: str | None) -> str:
    """
    Name what a version of the docking plan says.

    Parameters
    ----------
    text : str | None
        The version's content, or None when there is none.

    Returns
    -------
    str
        ``"bay 4"`` or ``"bay 3"`` for those plans (surrounding blank space ignored), ``"markers"``
        for a version that still holds conflict markers, ``"other"`` for anything else.
    """
    kind = "other"
    if text is not None and MARKER in text:
        kind = "markers"
    elif text is not None and text.strip() == THEIRS.strip():
        kind = "bay 4"
    elif text is not None and text.strip() == OURS.strip():
        kind = "bay 3"
    return kind


def _blob_text(lab: kit.Lab, blob: str | None) -> str | None:
    """
    Read a blob's content.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    blob : str | None
        The blob's id, or None.

    Returns
    -------
    str | None
        Its content, or None without a blob.
    """
    return kit.git_run(lab.project, "cat-file", "blob", blob).stdout if blob else None


def _entry(lab: kit.Lab) -> kit.FileEntry | None:
    """
    Find the docking plan in the snapshot.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    kit.FileEntry | None
        Its entry, or None when no area has it.
    """
    return next((entry for entry in kit.snapshot(lab.project)["files"] if entry["path"] == DOCKING), None)


def watch_choose(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the working folder's ``docking.txt`` docks at bay 4, with no markers.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; reading both sides comes first.
    """
    read = watch_read(lab, state, typed)
    path = lab.project / DOCKING
    text = path.read_text(errors="replace") if path.is_file() and not path.is_symlink() else None
    message = {"bay 4": CHOSEN, "bay 3": BAY_3, "markers": MARKERS}.get(_kind(text), OTHER)
    verdict = kit.Verdict(message == CHOSEN, message)
    return verdict if read.solved else read


def watch_add(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once no conflict is left and the staging area holds bay 4.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; the chosen side comes first.
    """
    chosen = watch_choose(lab, state, typed)
    entry = _entry(lab)
    added = entry is not None and not entry["conflicted"] and _kind(_blob_text(lab, entry["index"])) == "bay 4"
    verdict = kit.Verdict(added, ADDED if added else NOT_ADDED)
    return verdict if chosen.solved or added else chosen


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``main``'s last commit holds ``scout`` in its history and bay 4 with no markers.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; the conflict comes first while the merge is paused.
    """
    added = watch_add(lab, state, typed)
    snap = kit.snapshot(lab.project)
    scout = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"refs/heads/{SCOUT}").stdout.strip()
    joined = bool(scout) and snap["operation"] != "merge" and kit.is_ancestor(lab.project, scout, "refs/heads/main")
    message = NOT_COMMITTED
    if joined:
        committed = kit.git_run(lab.project, "show", f"refs/heads/main:{DOCKING}").stdout
        message = {"bay 4": DONE, "bay 3": BAY_3_COMMITTED}.get(_kind(committed), NOT_BAY_4_COMMITTED)
    verdict = kit.Verdict(message == DONE, message)
    return verdict if joined or added.solved else added


QUEST: list[kit.Step] = [
    kit.WatchStep(id="merge", text="Bring `scout` into `main`.", command=f"git merge --no-edit {SCOUT}", watch=watch_merge),
    kit.WatchStep(id="read", text="Read both sides of the conflict.", command=f"cat {DOCKING}", watch=watch_read),
    kit.WatchStep(id="choose", text="Keep the bay that is open.", command=f"git restore --theirs {DOCKING}", watch=watch_choose),
    kit.WatchStep(id="add", text="Mark the conflict solved.", command=f"git add {DOCKING}", watch=watch_add),
    kit.WatchStep(id="commit", text="Finish the merge.", command="git commit --no-edit", watch=watch_commit),
]


def _commit(lab: kit.Lab, text: str, message: str, day: int) -> None:
    """
    Write the docking plan and commit it on the current branch.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    text : str
        The plan's new content.
    message : str
        The commit's message.
    day : int
        The day of June 2026 it is dated.
    """
    (lab.project / DOCKING).write_text(text)
    kit.git(lab.project, "add", DOCKING)
    kit.git(lab.project, "commit", "-q", "-m", message, author=kit.PLAYER, when=f"2026-06-{day:02}T09:00:00+00:00")


def setup(lab: kit.Lab) -> kit.State:
    """
    Make ``main`` dock at bay 3 and ``scout`` at bay 4, from a plan that docked at bay 2.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the goals read the repository.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    _commit(lab, START, "Write the docking plan", 1)
    kit.git(lab.project, "switch", "-q", "-c", SCOUT)
    _commit(lab, THEIRS, "Bay 3 is closed for repairs: dock at bay 4", 2)
    kit.git(lab.project, "switch", "-q", "main")
    _commit(lab, OURS, "Move the docking to bay 3", 3)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the merge is committed with bay 4; the quest keeps reading both sides first.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the repository and what was typed.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The last goal's verdict.
    """
    return watch_commit(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order (AUTHORING section 3.6).

    Parameters
    ----------
    lab : kit.Lab
        The level's lab, as `setup` left it.
    state : kit.State
        The level's state.
    typed : list[kit.Command]
        The lines typed so far; each line typed here is added.

    Returns
    -------
    str | None
        None: the level reads the repository and what was typed.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "merge": kit.typing(f"git merge --no-edit {SCOUT}"),
    "read": kit.typing(f"cat {DOCKING}"),
    "choose": kit.typing(f"git restore --theirs {DOCKING}"),
    "add": kit.typing(f"git add {DOCKING}"),
    "commit": kit.typing("git commit --no-edit"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
