"""
Plant the flag: make the folder a repository with ``git init``, see ``.git`` with ``ls -a``, then a ``git status`` that works.

The second Orbit level (design 1-2). The first goal reads the repository; the other two read the
lines the player typed. An ``ls -a`` counts only after the last ``git init`` that worked, since
before it there is no ``.git`` to see.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Plant the flag"
DIFFICULTY = 1
XP = 100
COMMAND = "git init"
PAR = 3
CARD = kit.CommandCard(command="git init", text="Makes the current folder a new repository: Git creates the hidden `.git` folder in it.")
SCENE = [
    kit.SceneFrame(art="planet", text="This folder is only a folder. Git keeps no history of it yet."),
    kit.SceneFrame(art="flag", text="With `git init` you plant the flag: Git creates a hidden folder named `.git`."),
    kit.SceneFrame(art="flag", text="`.git` is the base's black box. The whole history lives in it, so never delete it."),
]

FILES = {"map.txt": "Route: Earth, Moon, Mars\n", "journal.txt": "Day 1: landed without trouble.\n"}
INIT = r"git init\b"
STATUS = r"git status\b"

BRIEFING = """
Make this folder a repository, so Git starts keeping its history.

The mission is done when the folder is a repository, you have seen its hidden `.git` folder with
`ls -a`, and `git status` works.
"""

HINTS = [
    "The command that makes a repository is `git init`.",
    "Names that start with a dot are hidden. `ls -a` shows them.",
]

DEBRIEF = """
`git init` created the hidden `.git` folder. From now on Git can keep this folder's history: the
repository, and every commit you make in it, live in `.git`.

Commands to keep:

    $ git init      # make this folder a repository
    $ ls -a         # list every file, the hidden ones too
"""

PLANTED = "The flag is planted: this folder is a repository now."
NOT_PLANTED = "This folder is not a repository yet: plant the flag with `git init`."
SEEN = "You saw `.git`, the hidden folder where Git keeps the history."
NOT_SEEN = "`.git` is hidden. List the folder with `ls -a` to see it."
WORKS = "`git status` works now: Git knows this folder."
NOT_WORKING = "Check with `git status`: in a repository, it works."


def watch_repository(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the project folder is a repository.

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
    planted = kit.snapshot(lab.project)["exists"]
    return kit.Verdict(planted, PLANTED if planted else NOT_PLANTED)


def watch_hidden(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once an ``ls`` that lists hidden names worked after the last ``git init`` that worked, in a repository.

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
        The step's verdict; the repository comes first.
    """
    planted = watch_repository(lab, state, typed)
    seen = kit.typed(kit.after(typed, INIT), kit.LIST_HIDDEN, "ok")
    verdict = kit.Verdict(seen, SEEN if seen else NOT_SEEN)
    return verdict if planted.solved else planted


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked, in a repository.

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
        The step's verdict; the repository comes first.
    """
    planted = watch_repository(lab, state, typed)
    works = kit.typed(typed, STATUS, "ok")
    verdict = kit.Verdict(works, WORKS if works else NOT_WORKING)
    return verdict if planted.solved else planted


QUEST: list[kit.Step] = [
    kit.WatchStep(id="init", text="Plant the flag: make this folder a repository.", command="git init", watch=watch_repository),
    kit.WatchStep(id="hidden", text="Find the hidden black box.", command="ls -a", watch=watch_hidden),
    kit.WatchStep(id="status", text="Check with `git status` that Git knows the folder now.", command="git status", watch=watch_status),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make the project folder with the base's two files, and no repository.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the level has nothing to remember.
    """
    lab.project.mkdir()
    for name, text in FILES.items():
        (lab.project / name).write_text(text)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the folder is a repository, ``ls -a`` showed ``.git`` and ``git status`` worked.

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
        The first goal not met yet, or the last goal's message once all are.
    """
    verdicts = [step.watch(lab, state, typed) for step in QUEST if isinstance(step, kit.WatchStep)]
    return next((verdict for verdict in verdicts if not verdict.solved), verdicts[-1])


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
    "init": kit.typing("git init"),
    "hidden": kit.typing("ls -a"),
    "status": kit.typing("git status"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
