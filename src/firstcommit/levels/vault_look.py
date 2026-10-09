"""
Look before you seal: ``git diff`` shows what changed, ``git diff --staged`` what the commit will take.

Wave 1, vault 3-2 (docs/drafts/chapters-3-7.md), guided. Setup commits the route and the engine
settings; the overnight edits (the new stop the crew's note asks for in the route, and an
accidental change to the engine) are a level event, run after the page's first look, so the page
shows both files changing. The goals: read the changes with ``git diff`` (typed), name the file
that changed by accident (an answer), stage only the route and check it with
``git diff --staged`` (typed after the last add), then commit it. The stage and commit goals read
the blob ids setup saved, so a staged or committed route counts and the accidental change never
may. An accidental change sealed in a capsule cannot be taken back yet: the level says so and
offers to start again.
"""

from collections.abc import Callable
from typing import Literal

from firstcommit import kit

TITLE = "Look before you seal"
DIFFICULTY = 2
XP = 150
COMMAND = "git diff"
PAR = 4
CARD = kit.CommandCard(
    command="git diff",
    text="Shows the lines you changed in the working folder and have not staged. `git diff --staged` shows what the next commit will take.",
)
SCENE = [
    kit.SceneFrame(art="zones", text="Someone worked on the base overnight. Before you seal anything, look at what changed."),
]

ROUTE = "route.txt"
ENGINE = "engine.cfg"
START = {ROUTE: "Route: Earth, Moon, Mars\n", ENGINE: "power=85\n"}
OVERNIGHT = {ROUTE: "Route: Earth, Moon, Phobos, Mars\n", ENGINE: "power=85sdfghjkl\n"}
ACCIDENT_NAMES = ("engine.cfg", "engine")
ROUTE_NAMES = ("route.txt", "route")
DIFF = r"git diff( --no-color)?$"
STAGED_DIFF = r"git diff( \S+)* (--staged|--cached)\b"
ADD = r"git add\b"

BRIEFING = """
Someone edited two files overnight. The night crew left a note: only `route.txt` was meant to
change, to add a stop. Read the changes, then seal only the route's change into a capsule.

The mission is done when you have read the changes with `git diff`, named the file that changed
by accident, checked the staging area with `git diff --staged`, and a new commit holds the
route's change and not the other one.
"""

HINTS = [
    "`git diff` shows each changed line twice: `-` before it, `+` after it.",
    "Stage only the route with `git add route.txt`, check it with `git diff --staged`, then commit.",
    'Every line of the mission, in order:\n\n    $ git diff\n    $ git add route.txt\n    $ git diff --staged\n    $ git commit -m "Add the Phobos stop"',
]

DEBRIEF = """
`git diff` compared the working folder with the staging area and showed both edits. Once the
route was staged, `git diff --staged` showed exactly what the commit would take: the new stop,
and not the accidental change. That change is still in `engine.cfg`, in the working folder,
sealed in no capsule.

At work, a look at `git diff` before each commit catches the edits you never meant to make.

Commands to keep:

    $ git diff            # what changed and is not staged
    $ git diff --staged   # what the next commit will take
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
WAITING = "Nothing has changed yet. Wait a moment for the overnight edits."
DIFFED = "`git diff` shows each changed line: `-` the line before, `+` the line now."
NOT_DIFFED = "Read the changes first: type `git diff`."
ACCIDENT_FOUND = "Right: `engine.cfg` changed by accident, to `power=85sdfghjkl`. The note asked only for the route's new stop."
ROUTE_IS_MEANT = "`route.txt` holds the change the note asks for: a new stop. Look again at the line `git diff` shows for `engine.cfg`."
NOT_A_FILE = "Type the name of one of the two files `git diff` shows."
ROUTE_STAGED = "The route's change is staged, and the accidental one stays in the working folder."
ROUTE_NOT_STAGED = "Stage only the route: `git add route.txt`."
ACCIDENT_STAGED = "The accidental change in `engine.cfg` is staged too. `git restore --staged engine.cfg` takes it out; the file keeps the edit."
ACCIDENT_SEALED = (
    "The accidental change in `engine.cfg` is in a commit now. Taking a commit back comes in a later chapter: "
    "start the mission again."
)
CHECKED = "`git diff --staged` shows what the next commit will take: the route's new stop, and nothing else."
NOT_CHECKED = "Check what the next commit will take: `git diff --staged`."
SEALED = "The route's change is sealed in a capsule, and the accidental one is in none."
NOT_SEALED = 'Seal the route\'s change into a capsule: `git commit -m "Add the Phobos stop"`.'
EVERYTHING_STAGED = "That staged the accidental change too. `git diff --staged` shows it; `git restore --staged engine.cfg` takes it back out."

REACTIONS = [kit.ReactionRule(line=r"git add( \S+)* (\.|-A|--all|engine\.cfg)( |$)", mood="warn", text=EVERYTHING_STAGED, event="file-staged")]


def overnight_edits(lab: kit.Lab, state: kit.State) -> None:
    """
    Make the overnight edits: the new stop in the route and the accidental change to the engine settings.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    for name, text in OVERNIGHT.items():
        (lab.project / name).write_text(text)


EVENTS = [kit.LevelEvent(id="overnight", run=overnight_edits)]


def _blobs(lab: kit.Lab, area: Literal["head", "index", "folder"]) -> dict[str, str | None]:
    """
    Give the route's and the engine's blob ids in one area of the repository.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    area : Literal["head", "index", "folder"]
        ``"head"``, ``"index"`` or ``"folder"``.

    Returns
    -------
    dict[str, str | None]
        Each file's id there, None where it is absent; empty with no repository.
    """
    files = {file["path"]: file for file in kit.snapshot(lab.project)["files"]}
    return {name: files[name][area] if name in files else None for name in START}


def watch_diff(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a plain ``git diff`` worked after the overnight edits.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the blob ids.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    edited = _blobs(lab, "folder")[ENGINE] != state["start"][ENGINE]
    diffed = kit.typed(typed, DIFF, "ok")
    message = DIFFED if diffed else NOT_DIFFED
    if not edited and not diffed:
        message = WAITING
    return kit.Verdict(message == DIFFED, message)


def names_the_accident(lab: kit.Lab, state: kit.State, answer: str) -> kit.Verdict:
    """
    Pass when the player names the engine settings as the file that changed by accident.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused).
    state : kit.State
        The level's state (unused).
    answer : str
        What the player typed.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    name = answer.strip().strip("`").lower()
    message = NOT_A_FILE
    if name in ACCIDENT_NAMES:
        message = ACCIDENT_FOUND
    elif name in ROUTE_NAMES:
        message = ROUTE_IS_MEANT
    return kit.Verdict(message == ACCIDENT_FOUND, message)


def watch_stage(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the staging area holds the new route (staged or committed) and the engine as it started.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the blob ids.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict, with the next thing to do; lost once the accidental change is in a commit.
    """
    exists = kit.snapshot(lab.project)["exists"]
    head, index = _blobs(lab, "head"), _blobs(lab, "index")
    sealed = head[ENGINE] == state["accident"]
    message = ROUTE_STAGED
    if not exists:
        message = NO_REPOSITORY
    elif sealed:
        message = ACCIDENT_SEALED
    elif index[ENGINE] != state["start"][ENGINE]:
        message = ACCIDENT_STAGED
    elif index[ROUTE] != state["route"]:
        message = ROUTE_NOT_STAGED
    return kit.Verdict(message == ROUTE_STAGED, message, lost=sealed)


def watch_staged_diff(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git diff --staged`` worked after the last ``git add`` that worked, with only the route staged.

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
        The step's verdict; the staging area comes first.
    """
    staged = watch_stage(lab, state, typed)
    checked = kit.typed(kit.after(typed, ADD), STAGED_DIFF, "ok")
    verdict = kit.Verdict(checked, CHECKED if checked else NOT_CHECKED)
    return verdict if staged.solved else staged


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the last commit holds the new route and the engine as it started.

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
        The step's verdict; the staging area comes first.
    """
    staged = watch_stage(lab, state, typed)
    sealed = _blobs(lab, "head")[ROUTE] == state["route"]
    verdict = kit.Verdict(sealed, SEALED if sealed else NOT_SEALED)
    return verdict if staged.solved else staged


QUEST: list[kit.Step] = [
    kit.WatchStep(id="diff", text="Read what changed overnight.", command="git diff", watch=watch_diff),
    kit.AnswerStep(
        id="accident",
        text="Find the change nobody asked for.",
        question="Which file changed by accident?",
        placeholder="a file name",
        check=names_the_accident,
    ),
    kit.WatchStep(id="stage", text="Stage only the route.", command="git add route.txt", watch=watch_stage),
    kit.WatchStep(id="check", text="Check what the next commit will take.", command="git diff --staged", watch=watch_staged_diff),
    kit.WatchStep(id="commit", text="Seal the route's change into a capsule.", command='git commit -m "Add the Phobos stop"', watch=watch_commit),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with one commit of the route and the engine settings.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``start``: each file's blob id as committed; ``route`` and ``accident``: the route's and the
        engine's ids after the overnight edits.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for name, text in START.items():
        (lab.project / name).write_text(text)
    kit.git(lab.project, "add", *START)
    kit.git(lab.project, "commit", "-q", "-m", "Set the route and the engine", when="2026-04-01T09:00:00+00:00")
    blob = {name: kit.git(lab.project, "hash-object", "--stdin", stdin=text).strip() for name, text in OVERNIGHT.items()}
    start = {name: kit.git(lab.project, "rev-parse", f"HEAD:{name}").strip() for name in START}
    return {"start": start, "route": blob[ROUTE], "accident": blob[ENGINE]}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the route's change is committed without the accidental one.

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
    return watch_commit(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player, after the overnight edits: every quest step's action, in order.

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


def name_accident(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Name the file the diff shows changed by accident.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused).
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far (unused).

    Returns
    -------
    str | None
        The file's name.
    """
    return ENGINE


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "diff": kit.typing("git diff"),
    "accident": name_accident,
    "stage": kit.typing(f"git add {ROUTE}"),
    "check": kit.typing("git diff --staged"),
    "commit": kit.typing('git commit -m "Add the Phobos stop"'),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
