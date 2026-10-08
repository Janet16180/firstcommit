"""
Selective cargo: stage two files of three by name, so the keys stay in the working folder.

Wave 1, cargo 2-2 (docs/drafts/chapters-3-7.md). It starts in a new repository with three
untracked files. The first goal reads the staging area: the engine and the route are in it (or
already committed), the keys are not; ``git add .`` is the beginner's wrong path, with
``git rm --cached`` as the way back before the first commit. The second goal reads the lines
typed: a ``git status`` that worked after the last ``git add`` that worked. Keys that reach a
commit are lost for this play: nothing taught yet takes a commit back, so the level offers to
start again.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Selective cargo"
DIFFICULTY = 1
XP = 100
COMMAND = "git add <file> <file>"
PAR = 2
CARD = kit.CommandCard(
    command="git add <file> <file>",
    text="Stages the files you name, and only those: the others stay in the working folder as they are.",
)

CARGO = ("engine.cfg", "route.txt")
KEYS = "keys.txt"
FILES = {"engine.cfg": "power=80\n", "route.txt": "Route: Earth, Moon, Mars\n", KEYS: "airlock password: orion-7\n"}
ADD = r"git add\b"
STATUS = r"git status\b"

BRIEFING = """
The next cargo is the engine settings and the route. The folder also holds `keys.txt`, with the
airlock password: it must never leave this base.

The mission is done when `engine.cfg` and `route.txt` are staged, `keys.txt` is not, and you have
looked with `git status`.
"""

HINTS = [
    "`git add` takes several names on one line, separated by spaces.",
    "Type `git add engine.cfg route.txt`, then `git status`.",
    "Every line of the mission, in order:\n\n    $ git add engine.cfg route.txt\n    $ git status",
]

DEBRIEF = """
You staged the two files by name, and `keys.txt` stayed in the working folder, untracked. Naming
the files is how you choose what goes into a commit: `git add .` would have taken the keys too.

Commands to keep:

    $ git add engine.cfg route.txt   # stage the files you name
    $ git rm --cached keys.txt       # unstage a file, before the first commit
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOADED = "`engine.cfg` and `route.txt` are staged, and `keys.txt` stays in the working folder."
NOT_LOADED = "Stage the engine settings and the route by name: `git add engine.cfg route.txt`."
ONE_MISSING = "One of the two is staged. Stage the other one too: `git add` takes its name."
KEYS_STAGED = (
    "`keys.txt` is staged, and the password must stay here. `git rm --cached keys.txt` takes it back out "
    "of the staging area; the file stays in the working folder."
)
KEYS_COMMITTED = (
    "`keys.txt` is in a commit now, so the password is in this repository's history. Taking a commit back "
    "comes in a later chapter: start the mission again."
)
LOOKED = "`git status` shows the engine and the route staged, and the keys untracked."
NOT_LOOKED = "Now look with `git status`: it lists what is staged and what is not."
EVERYTHING_STAGED = (
    "That staged every file in the folder, `keys.txt` too. `git rm --cached keys.txt` takes the keys back out; "
    "next time, name the files you want."
)
NOTHING_TO_RESTORE = (
    "`git restore --staged` puts back the version of your last commit, and this repository has no commit yet. "
    "Before the first commit, `git rm --cached keys.txt` takes a file out of the staging area and leaves it in the working folder."
)

REACTIONS = [
    kit.ReactionRule(line=r"git add( \S+)* (\.|-A|--all)( |$)", mood="warn", text=EVERYTHING_STAGED, event="file-staged"),
    kit.ReactionRule(line=r"git restore\b.* --staged\b", mood="err", text=NOTHING_TO_RESTORE, outcome="failed", repository=True),
]


def watch_stage(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the engine and the route are in the staging area (staged or committed) and the keys in no area of git.

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
        The step's verdict, with the next thing to do; lost once the keys are in a commit.
    """
    snap = kit.snapshot(lab.project)
    indexed = {file["path"] for file in snap["files"] if file["index"] is not None}
    loaded = [name for name in CARGO if name in indexed]
    committed = kit.in_history(lab.project, KEYS)
    message = LOADED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif committed:
        message = KEYS_COMMITTED
    elif KEYS in indexed:
        message = KEYS_STAGED
    elif not loaded:
        message = NOT_LOADED
    elif len(loaded) < len(CARGO):
        message = ONE_MISSING
    return kit.Verdict(message == LOADED, message, lost=committed)


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked after the last ``git add`` that worked, with the cargo right.

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
    kit.WatchStep(id="stage", text="Stage the engine settings and the route, and only those.", command="git add engine.cfg route.txt", watch=watch_stage),
    kit.WatchStep(id="look", text="Look at the staging area with `git status`.", command="git status", watch=watch_status),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make the project folder a new repository holding three untracked files, the keys among them.

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
    Solved once the cargo is right and ``git status`` was typed after the last staging.

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


def stage_cargo(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git add engine.cfg route.txt`` in the project folder.

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
    typed.append(kit.type_line(lab.project, f"git add {' '.join(CARGO)}"))
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


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"stage": stage_cargo, "look": look}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
