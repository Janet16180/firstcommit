"""
Stowaway: the night shift's ``git add .`` staged the keys; take them out and keep the file.

Wave 1, cargo 2-3 (docs/drafts/chapters-3-7.md), a situation. Setup commits the engine and the
route first, so ``git restore --staged`` works as ``git status`` suggests (before a first commit
it fails, as cargo-first teaches), then changes both and leaves the keys untracked. The night
shift's ``git add .`` is a level event: it runs after the page's first look, so the page
animates the keys riding onto the dock. The first goal reads the lines typed (a ``git status``
that worked); the second reads the three areas: the keys out of the staging area and still in
the working folder, the engine and the route still staged (or committed). Keys deleted from
both the folder and the staging area are lost for good, and keys in a commit are lost for this
play: the level says so and offers to start again.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Stowaway"
DIFFICULTY = 1
XP = 120
COMMAND = "git restore --staged"
PAR = 3
CARD = kit.CommandCard(
    command="git restore --staged <file>",
    text="Takes a file out of the staging area, back to its version in the last commit. The working folder keeps the file as it is.",
)

CARGO = {"engine.cfg": "power=85\n", "route.txt": "Route: Earth, Moon, Mars, Phobos\n"}
FIRST = {"engine.cfg": "power=80\n", "route.txt": "Route: Earth, Moon, Mars\n"}
KEYS = "keys.txt"
KEYS_TEXT = "airlock password: orion-7\n"
STATUS = r"git status\b"

BRIEFING = """
Overnight, the night shift updated the engine settings and the route, and ran `git add .` to
stage them. That took the airlock password in `keys.txt` too.

The mission is done when you have looked with `git status`, `keys.txt` is out of the staging area
and still in the working folder, and `engine.cfg` and `route.txt` are still staged.
"""

HINTS = [
    "`git status` names the command that takes a file out of the staging area.",
    "Type `git restore --staged keys.txt`. It keeps the file in the working folder.",
    "Every line of the mission, in order:\n\n    $ git status\n    $ git restore --staged keys.txt",
]

DEBRIEF = """
`git restore --staged keys.txt` put the staging area back to the last commit for that one file:
the commit has no `keys.txt`, so the keys left the staging area. The working folder was not
touched, so the file is still there, untracked. The engine and the route are still staged for
the next commit.

Passwords, API keys and tokens never belong in a repository: once one is in a commit, every copy
of the history holds it, and deleting the file later leaves the old commit as it was. A file
named in `.gitignore` stays out of `git add .`; the last mission of this sector teaches it.

Commands to keep:

    $ git status                        # see what is staged
    $ git restore --staged keys.txt     # unstage one file, the file kept
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOOKED = "`git status` lists the three staged files, `keys.txt` among them, and the command that unstages one."
NOT_LOOKED = "Look first: `git status` shows what the night shift staged."
KEYS_ABOARD = "`keys.txt` is still staged, so the next commit would take the password. Take it out of the staging area and keep the file."
DELETED = (
    "`keys.txt` is gone from the working folder, and it is still staged. `git restore keys.txt` copies it back "
    "from the staging area; then take it out of the staging area."
)
KEYS_LOST = (
    "`keys.txt` is in neither the working folder nor the staging area, and no commit has it: that copy of the "
    "password is lost. Unstaging never needs deleting. Start the mission again."
)
KEYS_COMMITTED = (
    "`keys.txt` is in a commit now, so the password is in this repository's history. Taking a commit back "
    "comes in a later chapter: start the mission again."
)
CARGO_UNSTAGED = "The engine settings and the route must stay staged for the next commit: `git add engine.cfg route.txt` stages them again."
UNSTAGED = "`keys.txt` is out of the staging area and still in the working folder, and the engine and the route are still staged."
WHY_SECRETS = (
    "Whatever is staged goes into the next commit, and a commit stays in the history. Once it is pushed, everyone "
    "who can read the repository has it, in every copy. Deleting the file later does not help: the old commit still "
    "holds it. That is why a secret like `keys.txt` must never be staged."
)
RM_REFUSED = (
    "Git refused, and that kept your file: without `--cached`, `git rm` deletes the file from the working folder too. "
    "`git restore --staged keys.txt` takes it out of the staging area only."
)

REACTIONS = [
    kit.ReactionRule(line=STATUS, mood="warn", text=WHY_SECRETS, outcome="ok", repository=True, staged=True, moment="secret-leak"),
    kit.ReactionRule(line=r"git rm(?!.* --cached)\b", mood="err", text=RM_REFUSED, outcome="failed", repository=True),
    kit.ReactionRule(line=r"rm\b.*keys\.txt", mood="warn", text=DELETED, event="file-deleted"),
]


def night_shift_adds(lab: kit.Lab, state: kit.State) -> None:
    """
    Stage everything in the project folder, as the night shift did, keys included.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    kit.git(lab.project, "add", ".")


EVENTS = [kit.LevelEvent(id="night-shift", run=night_shift_adds)]


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked.

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
    looked = kit.typed(typed, STATUS, "ok")
    return kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)


def watch_unstage(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the keys are out of the staging area and in the working folder, and the cargo still staged.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the cargo's blob ids, staged as the night shift left them.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict, with the next thing to do; lost once the keys are gone or committed.
    """
    snap = kit.snapshot(lab.project)
    files = {file["path"]: file for file in snap["files"]}
    keys = files.get(KEYS)
    in_folder = keys is not None and keys["folder"] is not None
    staged = keys is not None and keys["index"] is not None
    loaded = all(name in files and files[name]["index"] == blob for name, blob in state["cargo"].items())
    committed = kit.in_history(lab.project, KEYS)
    message = UNSTAGED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif committed:
        message = KEYS_COMMITTED
    elif not in_folder and not staged:
        message = KEYS_LOST
    elif not in_folder:
        message = DELETED
    elif staged:
        message = KEYS_ABOARD
    elif not loaded:
        message = CARGO_UNSTAGED
    return kit.Verdict(message == UNSTAGED, message, lost=message in (KEYS_LOST, KEYS_COMMITTED))


QUEST: list[kit.Step] = [
    kit.WatchStep(id="look", text="Find out what the night shift staged.", command="git status", watch=watch_status),
    kit.WatchStep(id="unstage", text="Take the keys out of the staging area, and keep the file.", command="git restore --staged keys.txt", watch=watch_unstage),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with one commit of the engine and the route, both changed since, and the keys untracked.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``cargo``: the blob id of each changed file, as the night shift's add stages it.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for name, text in FIRST.items():
        (lab.project / name).write_text(text)
    kit.git(lab.project, "add", *FIRST)
    kit.git(lab.project, "commit", "-q", "-m", "Load the engine and the route", when="2026-03-01T22:00:00+00:00")
    for name, text in CARGO.items():
        (lab.project / name).write_text(text)
    (lab.project / KEYS).write_text(KEYS_TEXT)
    return {"cargo": {name: kit.git(lab.project, "hash-object", name).strip() for name in CARGO}}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the keys are unstaged and kept, the cargo still staged, and ``git status`` was typed.

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
        The areas' verdict first, then the look's.
    """
    areas = watch_unstage(lab, state, typed)
    return watch_status(lab, state, typed) if areas.solved else areas


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order (AUTHORING section 3.6).

    Parameters
    ----------
    lab : kit.Lab
        The level's lab, after the night shift's event.
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


def unstage_keys(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git restore --staged keys.txt`` in the project folder.

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
    typed.append(kit.type_line(lab.project, f"git restore --staged {KEYS}"))
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"look": look, "unstage": unstage_keys}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
