"""
Welcome aboard: look at a folder with ``ls``, then ask ``git status``, which fails there.

The first Orbit level (design 1-1). The folder is not a repository, so the failed ``git status``
is the lesson: Git works only inside a repository, and the next level makes one. Both goals read
the lines the player typed, since neither changes the folder.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Welcome aboard"
DIFFICULTY = 1
XP = 100
COMMAND = "ls · git status"
PAR = 2
CARD = kit.CommandCard(
    command="ls",
    text="Lists the files in the current folder. `ls -a` lists the hidden ones too: those whose names start with a dot.",
)
SCENE = [
    kit.SceneFrame(art="space", text="I am Rama, the ship's computer. I will be with you while you train."),
    kit.SceneFrame(art="space", text="The job: build bases across the galaxy without ever losing a line of work."),
    kit.SceneFrame(
        art="timeline",
        text="For that we use Git. Each time you ask it to, Git saves a snapshot of your project, and you can go back to any snapshot you saved.",
    ),
    kit.SceneFrame(
        art="terminal",
        text="You give Git orders by typing in the terminal. Mistakes are safe here: this is a practice folder, and every error message tells you something.",
    ),
]

FILES = {"map.txt": "Route: Earth, Moon, Mars\n", "journal.txt": "Day 1: landed without trouble.\n"}
LIST = r"ls\b"
STATUS = r"git status\b"

BRIEFING = """
You are at your moon base, in the folder `project`. Look at what is in the folder, then ask Git
how things stand.

The mission is done when you have listed the folder with `ls` and typed `git status`.
"""

HINTS = [
    "Type `ls` and press Enter. It lists what is in the folder.",
    "Now type `git status`. If it prints an error, good: read what it says.",
]

DEBRIEF = """
Git works only inside a repository, a folder it keeps the history of. Your folder is not one
yet, so `git status` stopped with an error and changed nothing. The next mission makes this
folder a repository with `git init`.

Commands to keep:

    $ ls            # list the files in this folder
    $ git status    # ask Git how things stand
"""

LISTED = "These are the folder's files: `map.txt` and `journal.txt`, plain files that no repository keeps yet."
NOT_LISTED = "Type `ls` and press Enter to list the files in the folder."
REFUSED = "Git refused: this folder is not a repository yet. The next mission makes it one."
ANSWERED = "Git answered: this folder is a repository, so `git status` can tell how things stand."
NOT_ASKED = "Now ask Git how things stand: type `git status`."
NO_REPOSITORY_YET = (
    "Git found no repository here, so it has nothing to report. That is the lesson: Git works only inside a repository. "
    "The next mission makes this folder one."
)

REACTIONS = [kit.ReactionRule(line=STATUS, mood="info", text=NO_REPOSITORY_YET, outcome="failed", repository=False)]


def watch_list(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the player has listed the folder with an ``ls`` that worked.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused).
    state : kit.State
        The level's state (unused).
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    listed = kit.typed(typed, LIST, "ok")
    return kit.Verdict(listed, LISTED if listed else NOT_LISTED)


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the player has typed ``git status``, whether it worked or not.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused).
    state : kit.State
        The level's state (unused).
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; its message says what the last ``git status`` met.
    """
    asked = [line for line in typed if kit.typed([line], STATUS)]
    message = NOT_ASKED
    if asked and asked[-1]["status"] == 0:
        message = ANSWERED
    elif asked:
        message = REFUSED
    return kit.Verdict(bool(asked), message)


QUEST: list[kit.Step] = [
    kit.WatchStep(id="look", text="Look at what is in the folder.", command="ls", watch=watch_list),
    kit.WatchStep(id="ask", text="Ask Git how things stand.", command="git status", watch=watch_status),
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
    Solved once ``ls`` worked and ``git status`` was typed.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads what was typed.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The first goal not met yet, or the last goal's message once both are.
    """
    listed = watch_list(lab, state, typed)
    return listed if not listed.solved else watch_status(lab, state, typed)


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
        None: the level reads what was typed.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


def list_folder(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``ls`` in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; ``ls`` is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.project, "ls"))
    return None


def ask_status(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git status`` in the project folder, where it fails.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; ``git status`` is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.project, "git status"))
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"look": list_folder, "ask": ask_status}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
