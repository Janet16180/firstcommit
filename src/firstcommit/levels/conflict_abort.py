"""
Abort the docking: a pull stopped with conflicts, and ``git merge --abort`` is the safe way back.

Wave 2, conflict 6-2 (docs/drafts/chapters-3-7.md), a situation. Setup builds the playground:
you and Alex each added a line to both files, Alex pushed, and you have an uncommitted note in
``todo.txt``, a file nobody else touched. The goals: your own pull, which starts the merge and
stops with both files in conflict (a pull or merge that ended with status 1; a plain ``git pull``
and one with ``--rebase`` are refused, the second because of your note, and Rama names both); ``git status`` typed
after it (looking is the lesson); then no merge in progress, ``main`` where it was before the
pull, and both files as your commit holds them, with your note kept. A note gone for good
(``git reset --hard``) or the merge finished instead is lost for this play.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Abort the docking"
DIFFICULTY = 2
XP = 150
COMMAND = "git merge --abort"
PAR = 3
CARD = kit.CommandCard(
    command="git merge --abort",
    text="Stops a paused merge and puts the branch and its files back as they were before it began. Commit or stash your own changes before a merge, so it never has to rebuild them.",
)
SCENE = [
    kit.SceneFrame(art="collision", text="Friday, six o'clock. Alex pushed lines to the same two files you changed."),
    kit.SceneFrame(art="collision", text="Pull before you go. If Git stops, you can answer it now, or step back to where you were and answer on Monday."),
]

FILES = ("README.md", "notes.txt")
TODO = "todo.txt"
TODO_START = "Monday:\n"
TODO_NOTE = "Monday:\n- check the docking clamps\n"
STATUS = r"git status\b"
PULL = r"git pull\b"
REBASING_PULL = r"git pull\b.*--rebase\b"
MERGE_START = r"git (pull|merge)\b(?!.*--rebase\b)"
CONFLICT_STATUS = 1
REFUSED_STATUS = 128

BRIEFING = """
It is Friday at six. You committed a line in `README.md` and `notes.txt`, and Alex pushed lines of
their own to both. Your note for Monday in `todo.txt` is not committed. Bring Alex's work in with
`git pull --no-rebase` before you go.

Alex, on the comms: "Both files changed on my side too, and only I know why. If the pull stops,
don't guess at my lines tonight. Call the merge off, and we'll answer it together on Monday."

The mission is done when your pull has started the merge, you have looked with `git status`, no
merge is in progress, `main` and both files are as your commit left them, and `todo.txt` still
holds your note.
"""

HINTS = [
    "`git pull --no-rebase` brings Alex's commits in and starts the merge. `git status` then says a merge is in progress and lists the conflicted files.",
    "`git merge --abort` steps back out of the paused merge.",
    "Every line of the mission, in order:\n\n    $ git pull --no-rebase\n    $ git status\n    $ git merge --abort",
]

DEBRIEF = """
Your `git pull --no-rebase` started the merge and stopped halfway: both of you had changed the
same lines. `git status` showed the merge paused, with both files unmerged. `git merge --abort` stepped back
out of it: `main` was where your commit left it, both files held your lines again, and your note
in `todo.txt` was still there, because the merge never touched that file.

`git merge --abort` is the safe door, and the merge can wait for Monday: Alex's commit stays on
the remote (the mothership), and `git pull` will try again. Git can rebuild your uncommitted changes only in
some cases, so commit or stash them before a merge. `git reset --hard` would also end the merge,
but it throws away every uncommitted change to tracked files, your note too.

Commands to keep:

    $ git pull --no-rebase  # bring the remote's commits in; a conflict pauses the merge
    $ git status            # is a merge in progress, and which files are in conflict?
    $ git merge --abort     # step back to where you were before the merge
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_PULLED = "Bring Alex's work in first: `git pull --no-rebase`."
HOW_TO_JOIN = "Git fetched Alex's commits and stopped: both of you added commits, so it asks how to join them. `git pull --no-rebase` joins them with a merge."
PAUSED = "The pull stopped halfway: Git found conflicts in `README.md` and `notes.txt`, and the merge waits for you."
REBASE_REFUSED = "Git refused: a pull with `--rebase` needs every change in a commit, and your note in `todo.txt` is not. `git pull --no-rebase` merges instead, and a merge leaves a file it does not change alone."
LOOKED = "`git status` shows the merge in progress, and the two files in conflict."
NOT_LOOKED = "Look first: `git status`."
STILL_PAUSED = "The merge is still paused. Step back out of it: `git merge --abort`."
MERGED = "The merge is finished: `main` holds Alex's commit now. Stepping back was the mission: start it again."
NOT_BACK = "`main` or its files are not as your commit left them. `git merge --abort` puts them back."
NOTE_LOST = "Your note in `todo.txt` is gone: it was in no commit, and nothing can bring it back. Start the mission again."
BACK = "No merge in progress: `main` and both files are as your commit left them, and your note is still there."
RESET = "`git reset --hard` throws away every uncommitted change to tracked files, not only the merge. `git merge --abort` was the safe door."

REACTIONS = [
    kit.ReactionRule(line=r"git reset\b.*--hard\b", mood="warn", text=RESET, outcome="ok"),
]


def _ended(typed: kit.Typed, pattern: str, status: int) -> bool:
    """
    Tell whether a typed line fits a pattern and ended with a given status.

    Parameters
    ----------
    typed : kit.Typed
        The lines typed since the level started.
    pattern : str
        A pattern for `kit.typed`.
    status : int
        The exit status asked for.

    Returns
    -------
    bool
        True if any such line ended so.
    """
    return any(kit.typed([line], pattern) and line["status"] == status for line in typed)


def _merge_started(typed: kit.Typed) -> bool:
    """
    Tell whether a pull or merge of yours started the merge and stopped on its conflicts.

    Parameters
    ----------
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    bool
        True once a ``git pull`` or ``git merge`` (not a rebasing pull) ended with status 1.
    """
    return _ended(typed, MERGE_START, CONFLICT_STATUS)


def _since_merge_started(typed: kit.Typed) -> kit.Typed:
    """
    Give the lines typed after the last pull or merge that stopped on its conflicts.

    Parameters
    ----------
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Typed
        Those lines; none before such a pull.
    """
    starts = [index for index, line in enumerate(typed) if kit.typed([line], MERGE_START) and line["status"] == CONFLICT_STATUS]
    return typed[starts[-1] + 1 :] if starts else []


def watch_pull(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your pull started the merge and stopped on its conflicts.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict, naming a refused plain pull and a refused pull with ``--rebase``.
    """
    message = NOT_PULLED
    if kit.snapshot(lab.project)["operation"] == "merge" or _merge_started(typed):
        message = PAUSED
    elif _ended(typed, REBASING_PULL, REFUSED_STATUS):
        message = REBASE_REFUSED
    elif _ended(typed, PULL, REFUSED_STATUS):
        message = HOW_TO_JOIN
    return kit.Verdict(message == PAUSED, message)


def _paused(snap: kit.Snapshot) -> bool:
    """
    Tell whether a merge is paused.

    Parameters
    ----------
    snap : kit.Snapshot
        Your clone.

    Returns
    -------
    bool
        True while git has a merge in progress.
    """
    return snap["operation"] == "merge"


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked after your pull stopped.

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
        The step's verdict; the pull comes first.
    """
    looked = kit.typed(_since_merge_started(typed), STATUS, "ok")
    message = LOOKED if looked else NOT_LOOKED
    if not _merge_started(typed):
        message = NOT_PULLED
    return kit.Verdict(message == LOOKED, message)


def _pulled(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether your pull has run: your clone has fetched Alex's commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: Alex's commit.

    Returns
    -------
    bool
        True once the commit is in your clone.
    """
    return kit.git_run(lab.project, "cat-file", "-e", f"{state['alex']}^{{commit}}").returncode == 0


def watch_abort(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once no merge is paused, ``main`` is your commit, both files are its, and the note is kept.

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
        The step's verdict; lost once the note is gone or the merge is finished.
    """
    snap = kit.snapshot(lab.project)
    entries = {entry["path"]: entry for entry in snap["files"]}
    note = entries.get(TODO)
    note_kept = note is not None and state["note"] in (note["folder"], note["index"])
    main = kit.git_run(lab.project, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    merged = bool(main) and _pulled(lab, state) and kit.is_ancestor(lab.project, state["alex"], main)
    files_back = all(name in entries and entries[name]["folder"] == entries[name]["head"] for name in FILES)
    message = BACK if main == state["mine"] and files_back else NOT_BACK
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif not note_kept:
        message = NOTE_LOST
    elif not _merge_started(typed):
        message = NOT_PULLED
    elif merged:
        message = MERGED
    elif _paused(snap):
        message = STILL_PAUSED
    return kit.Verdict(message == BACK, message, lost=message in (NOTE_LOST, MERGED))


QUEST: list[kit.Step] = [
    kit.WatchStep(id="pull", text="Bring Alex's work in.", command="git pull --no-rebase", watch=watch_pull),
    kit.WatchStep(id="status", text="Find out where the pull stopped.", command="git status", watch=watch_status),
    kit.WatchStep(id="abort", text="Step back to where you were before the pull.", command="git merge --abort", watch=watch_abort),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground with ``todo.txt``, a line of yours committed and one of Alex's pushed in each file, and your note uncommitted.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``mine``: your commit; ``alex``: Alex's; ``note``: the blob id of ``todo.txt`` with your note.
    """
    kit.setup_playground(lab)
    (lab.project / TODO).write_text(TODO_START)
    kit.git(lab.project, "add", TODO)
    kit.git(lab.project, "commit", "-q", "-m", "Add the list for Monday", author=kit.PLAYER, when="2026-06-05T09:00:00+00:00")
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    for person in ("alex", "you"):
        for name in FILES:
            kit.press(lab, person, f"edit:{name}")
            kit.press(lab, person, f"add:{name}")
        kit.press(lab, person, "commit")
    kit.press(lab, "alex", "push")
    (lab.project / TODO).write_text(TODO_NOTE)
    return {
        "mine": kit.git(lab.project, "rev-parse", "HEAD").strip(),
        "alex": kit.git(lab.teammate, "rev-parse", "HEAD").strip(),
        "note": kit.git(lab.project, "hash-object", TODO).strip(),
    }


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once you stepped back out of the merge with your note kept; the quest keeps the look first.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the repository.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The last goal's verdict.
    """
    return watch_abort(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : list[kit.Command]
        The lines typed so far; each line typed here is added.

    Returns
    -------
    str | None
        None: the level reads the repository.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "pull": kit.typing("git pull --no-rebase"),
    "status": kit.typing("git status"),
    "abort": kit.typing("git merge --abort"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
