"""
Cargo inspection: the vault's challenge. One clean capsule holds the reactor patch; the keys and the debug log are in none.

Wave 1, vault 3-5 (docs/drafts/chapters-3-7.md), a challenge combining cargo (staging by name,
unstaging) and vault (commit). Setup commits the base, then patches the reactor and leaves the
keys and a debug log untracked; a level event runs ``git add .`` after the page's first look,
so the keys and the log ride onto the dock with the patch (the stowaways arrive). The three goals are end states, met in any order, read from
the repository only: the patch in a new commit on top of setup's, the keys in no commit and in
the working folder, the debug log untracked. A secret or the log sealed in a commit, or the keys
deleted from every area, are lost for this play.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Cargo inspection"
DIFFICULTY = 3
XP = 250
COMMAND = "cargo + vault"
PAR = 4
CHALLENGE = True
CARD = kit.CommandCard(
    command="git diff --staged",
    text="Shows exactly what the next commit will take. Look at it before every commit.",
)
SCENE = [
    kit.SceneFrame(art="alarm", text="Inspection at dawn. The inspector opens every capsule in your repository (the vault), and a password must be in none."),
]

REACTOR = "reactor.cfg"
KEYS = "keys.txt"
LOG = "debug.log"
START = {REACTOR: "core=stable\nlimit=80\n", "crew.txt": "Robin\nAlex\n"}
PATCH = "core=stable\nlimit=75\n"
KEYS_TEXT = "airlock password: orion-7\n"
LOG_TEXT = "12:01 reactor warm\n12:02 reactor warm\n"

BRIEFING = """
The inspector arrives at dawn. Someone ran `git add .` to stage the reactor patch, and that took
`keys.txt` and `debug.log` too.

The mission is done when the reactor patch is saved in a new capsule, `keys.txt` is in no capsule
and still in the working folder, and `debug.log` is untracked.
"""

HINTS = [
    "This is the staging area (the cargo dock) and the vault together: what is staged goes into the next capsule.",
    "Take the stowaways off the dock first, keep their files, then seal what is left.",
    'Every line of the mission, in order:\n\n    $ git restore --staged keys.txt\n    $ git restore --staged debug.log\n    $ git commit -m "Lower the reactor limit"',
]

DEBRIEF = """
You took the keys and the debug log off the staging area, kept both files, and sealed only the
reactor patch. A capsule holds exactly what was staged when you
sealed it, so the moment to look is before the commit: `git status`, or `git diff --staged`.

Commands to keep:

    $ git restore --staged keys.txt    # take a file off the staging area, keep it
    $ git diff --staged                # what the next commit will take
    $ git commit -m "Lower the reactor limit"
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
REACTOR_SAVED = "The reactor patch is sealed in a new capsule."
REACTOR_NOT_SAVED = "The reactor patch is in no new capsule yet."
KEYS_SAFE = "`keys.txt` is in no capsule, and still in the working folder."
KEYS_ABOARD = "`keys.txt` is staged: the next capsule would carry the password."
KEYS_DELETED = "`keys.txt` is gone from the working folder."
KEYS_LOST = "`keys.txt` is in no area of the repository and no capsule: that copy of the password is lost. Start the mission again."
KEYS_SEALED = "The password in `keys.txt` is sealed in a capsule. Taking a commit back comes in a later chapter: start the mission again."
LOG_SAFE = "`debug.log` is untracked, in the working folder."
LOG_ABOARD = "`debug.log` is staged: the next capsule would carry it."
LOG_DELETED = "`debug.log` is gone from the working folder."
LOG_SEALED = "`debug.log` is sealed in a capsule. Taking a commit back comes in a later chapter: start the mission again."
EVERYTHING_STAGED = "That staged every file in the folder again: `keys.txt` and `debug.log` are on the dock."

REACTIONS = [kit.ReactionRule(line=r"git add( \S+)* (\.|-A|--all)( |$)", mood="warn", text=EVERYTHING_STAGED, event="file-staged")]


def stowaways_arrive(lab: kit.Lab, state: kit.State) -> None:
    """
    Stage everything in the folder, as someone did before the inspection: the patch, the keys and the log.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    kit.git(lab.project, "add", ".")


EVENTS = [kit.LevelEvent(id="stowaways", run=stowaways_arrive)]


def _file(lab: kit.Lab, path: str) -> kit.FileEntry | None:
    """
    Find one file of the project in its snapshot.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    path : str
        The file's path.

    Returns
    -------
    kit.FileEntry | None
        Its entry, or None where no area holds it (or there is no repository).
    """
    return next((file for file in kit.snapshot(lab.project)["files"] if file["path"] == path), None)


def watch_reactor(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a new commit on top of setup's holds the reactor patch.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: setup's commit and the patch's blob id.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The goal's verdict.
    """
    snap = kit.snapshot(lab.project)
    reactor = _file(lab, REACTOR)
    saved = snap["head"] not in (None, state["start"]) and reactor is not None and reactor["head"] == state["patch"]
    message = REACTOR_SAVED if saved else REACTOR_NOT_SAVED
    if not snap["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == REACTOR_SAVED, message)


def _kept(lab: kit.Lab, path: str, messages: tuple[str, str, str, str, str]) -> kit.Verdict:
    """
    Judge one file that must stay in the working folder and out of every commit and the staging area.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    path : str
        The file.
    messages : tuple[str, str, str, str, str]
        What to say when it is safe, staged, deleted, lost and sealed, in that order.

    Returns
    -------
    kit.Verdict
        The goal's verdict; lost once the file is sealed, or in no area at all.
    """
    safe, aboard, deleted, lost, sealed = messages
    file = _file(lab, path)
    in_folder = file is not None and file["folder"] is not None
    staged = file is not None and file["index"] is not None
    message = safe
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    elif kit.in_history(lab.project, path):
        message = sealed
    elif not in_folder and not staged:
        message = lost
    elif not in_folder:
        message = deleted
    elif staged:
        message = aboard
    return kit.Verdict(message == safe, message, lost=message in (lost, sealed))


def watch_keys(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the keys are in no commit, not staged, and in the working folder.

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
        The goal's verdict.
    """
    return _kept(lab, KEYS, (KEYS_SAFE, KEYS_ABOARD, KEYS_DELETED, KEYS_LOST, KEYS_SEALED))


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the debug log is untracked: in no commit, not staged, in the working folder.

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
        The goal's verdict; a deleted log is no lost work, so it is only asked back.
    """
    verdict = _kept(lab, LOG, (LOG_SAFE, LOG_ABOARD, LOG_DELETED, LOG_DELETED, LOG_SEALED))
    return kit.Verdict(verdict.solved, verdict.message, lost=verdict.message == LOG_SEALED)


QUEST: list[kit.Step] = [
    kit.WatchStep(id="keys", text="`keys.txt` is in no capsule, and still in the working folder.", watch=watch_keys),
    kit.WatchStep(id="log", text="`debug.log` is untracked.", watch=watch_log),
    kit.WatchStep(id="reactor", text="The reactor patch is saved in a new capsule.", watch=watch_reactor),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Commit the base, then patch the reactor and leave the keys and a debug log untracked.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``start``: setup's commit; ``patch``: the patched reactor's blob id.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for name, text in START.items():
        (lab.project / name).write_text(text)
    kit.git(lab.project, "add", *START)
    kit.git(lab.project, "commit", "-q", "-m", "Set up the reactor and the crew", when="2026-05-10T18:00:00+00:00")
    for name, text in {REACTOR: PATCH, KEYS: KEYS_TEXT, LOG: LOG_TEXT}.items():
        (lab.project / name).write_text(text)
    return {"start": kit.git(lab.project, "rev-parse", "HEAD").strip(), "patch": kit.git(lab.project, "hash-object", REACTOR).strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once all three goals hold; else the first one that does not, lost ones first.

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
        The verdict.
    """
    verdicts = [step.watch(lab, state, typed) for step in QUEST if isinstance(step, kit.WatchStep)]
    unmet = sorted((verdict for verdict in verdicts if not verdict.solved), key=lambda verdict: not verdict.lost)
    return unmet[0] if unmet else verdicts[0]


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the challenge like a player, after the stowaways' event: look, unstage the keys and the log, commit.

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
    for line in ("git status", f"git restore --staged {KEYS} {LOG}", "git diff --staged", 'git commit -m "Lower the reactor limit"'):
        typed.append(kit.type_line(lab.project, line))
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "keys": kit.typing(f"git restore --staged {KEYS}"),
    "log": kit.typing(f"git restore --staged {LOG}"),
    "reactor": kit.typing('git commit -m "Lower the reactor limit"'),
}
"""The player's part of each goal, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
