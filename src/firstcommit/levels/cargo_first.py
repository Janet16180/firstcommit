"""
First cargo: stage one file of two with ``git add``, then look at the result with ``git status``.

The third Orbit level (design 2-1). It starts in a new repository whose two files are untracked.
The first goal reads the staging area: only ``map.txt`` belongs in it, so ``git add .`` is a
wrong path with a way back. The second reads the lines typed: a ``git status`` that worked after
the last ``git add`` that worked, so the player sees the staged map next to the untracked journal.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "First cargo"
DIFFICULTY = 1
XP = 100
COMMAND = "git add"
PAR = 2
CARD = kit.CommandCard(
    command="git add <file>",
    text="Copies a file, as it is now, from the working folder into the staging area, ready for your next commit.",
)
SCENE = [
    kit.SceneFrame(art="zones", text="Every Git base has three places on your computer: the working folder, the staging area and the repository."),
    kit.SceneFrame(art="conveyor", text="You work freely in the working folder. When a file is ready, `git add` puts a copy of it in the staging area."),
    kit.SceneFrame(art="conveyor", text="The staging area is the loading dock: you choose what goes on it. Files with passwords stay off."),
]

CARGO = "map.txt"
KEPT = "journal.txt"
FILES = {CARGO: "Route: Earth, Moon, Mars\n", KEPT: "Day 1: landed without trouble.\n"}
ADD = r"git add\b"
STATUS = r"git status\b"

BRIEFING = """
The map is ready to be saved. Put it in the staging area, and only the map: the journal is not
ready yet.

The mission is done when `map.txt` is staged, `journal.txt` is not, and you have looked with
`git status`.
"""

HINTS = [
    "`git add` takes the name of the file: `git add map.txt`.",
    "Look at `git status`: it lists `map.txt` as staged for your next commit, and `journal.txt` as untracked. Why?",
    "Every line of the mission, in order:\n\n    $ git add map.txt\n    $ git status",
]

DEBRIEF = """
`git add` copied the map from the working folder into the staging area. `git status` now lists
`map.txt` as staged for your next commit, and `journal.txt` as untracked: a plain `git commit`
takes what is staged and leaves the rest.

Commands to keep:

    $ git add map.txt   # stage one file
    $ git status        # see what is staged and what is not
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOADED = "`map.txt` is in the staging area, and `journal.txt` stays in the working folder."
NOT_LOADED = "`map.txt` is only in the working folder: stage it with `git add map.txt`."
TOO_MUCH = (
    "`journal.txt` is staged too, and this cargo is only the map. `git rm --cached journal.txt` takes it back out "
    "of the staging area; the file stays in the working folder."
)
LOOKED = "`git status` shows the map staged and the journal untracked."
NOT_LOOKED = "Now look with `git status`: it lists what is staged and what is not."
EVERYTHING_STAGED = (
    "That staged every file in the folder, the journal too. In this mission only the map goes in: "
    "`git rm --cached journal.txt` takes the journal back out."
)
NOTHING_TO_RESTORE = (
    "`git restore --staged` puts back the version of your last commit, and this repository has no commit yet. "
    "Before the first commit, `git rm --cached journal.txt` takes a file out of the staging area and leaves it in the working folder."
)

REACTIONS = [
    kit.ReactionRule(line=r"git add( \S+)* (\.|-A|--all)( |$)", mood="warn", text=EVERYTHING_STAGED, event="file-staged"),
    kit.ReactionRule(line=r"git restore\b.* --staged\b", mood="err", text=NOTHING_TO_RESTORE, outcome="failed", repository=True),
]


def watch_stage(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``map.txt`` is staged and ``journal.txt`` is not.

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
        The step's verdict, with the next thing to do.
    """
    snap = kit.snapshot(lab.project)
    staged = kit.staged(snap)
    message = LOADED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif KEPT in staged:
        message = TOO_MUCH
    elif CARGO not in staged:
        message = NOT_LOADED
    return kit.Verdict(message == LOADED, message)


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked after the last ``git add`` that worked, with only the map staged.

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
    loaded = watch_stage(lab, state, typed)
    looked = kit.typed(kit.after(typed, ADD), STATUS, "ok")
    verdict = kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)
    return verdict if loaded.solved else loaded


QUEST: list[kit.Step] = [
    kit.WatchStep(id="stage", text="Put the map in the staging area.", command="git add map.txt", watch=watch_stage),
    kit.WatchStep(id="look", text="Look at the staging area with `git status`.", command="git status", watch=watch_status),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make the project folder a new repository holding the base's two files, both untracked.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the level has nothing to remember.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for name, text in FILES.items():
        (lab.project / name).write_text(text)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once only the map is staged and ``git status`` was typed after the staging.

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
        The last goal's verdict, which checks the first one too.
    """
    return watch_status(lab, state, typed)


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


def stage_map(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git add map.txt`` in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.project, f"git add {CARGO}"))
    return None


def look(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git status`` in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.project, "git status"))
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"stage": stage_map, "look": look}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
