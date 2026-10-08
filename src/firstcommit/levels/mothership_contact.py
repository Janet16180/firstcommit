"""
Make contact: give the mothership's address a name with ``git remote add``; nothing travels.

Wave 1, mothership 4-1 (docs/drafts/chapters-3-7.md), guided, with a prediction. Setup makes a
repository with two commits and an empty stand-in GitHub. The prediction breaks the myth that
adding a remote uploads anything. The first goal reads the repository's configuration
(``origin`` names the lab's GitHub, by its relative path); the second reads the lines typed (a
``git remote -v`` that worked after the remote was set).
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Make contact"
DIFFICULTY = 1
XP = 100
COMMAND = "git remote add"
PAR = 2
CARD = kit.CommandCard(
    command="git remote add <name> <address>",
    text="Gives another repository's address a short name in yours, such as `origin`. Nothing is sent: it only writes the name down.",
)
SCENE = [
    kit.SceneFrame(art="orbit", text="The mothership circles above the base. It keeps a copy of the work of every crew."),
    kit.SceneFrame(art="orbit", text="Before you can send it anything, your repository needs its address, under a short name."),
]

REMOTE = "origin"
REMOTE_SET = r"git remote (add|set-url)\b"
LIST = r"git remote( -v| --verbose)\b"
FILES = {"map.txt": "Route: Earth, Moon, Mars\n", "journal.txt": "Day 1: landed without trouble.\n"}

BRIEFING = """
Your base has two commits, and the mothership is waiting for them at `../github/project.git`.
First, make contact: give that address the name `origin` in your repository.

The mission is done when `origin` names `../github/project.git` and you have listed the remotes
with `git remote -v`.
"""

HINTS = [
    "`git remote add` takes a name, then the address: `git remote add origin ../github/project.git`.",
    "`git remote -v` lists each remote's name with its address.",
]

DEBRIEF = """
`origin` is now a name for the mothership's address, kept in your repository's configuration.
Nothing travelled: the mothership is still empty, and your commits are only here. Sending them
is the next mission.

At work the address is the one GitHub shows for your project, such as
`https://github.com/<you>/<project>.git`; `origin` is the name everyone uses for it.

Commands to keep:

    $ git remote add origin ../github/project.git   # name the mothership's address
    $ git remote -v                                 # list the remotes and their addresses
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NO_REMOTE = "Your repository knows no remote yet. Name the mothership's address: `git remote add origin ../github/project.git`."
OTHER_NAME = "The mothership's address has another name. This mission calls it `origin`: `git remote add origin ../github/project.git`."
WRONG_URL = "`origin` names another address. The mothership is at `../github/project.git`: `git remote set-url origin ../github/project.git` changes it."
CONTACT = "`origin` now names the mothership's address."
LISTED = "`git remote -v` lists `origin` with its address, once for fetching and once for pushing."
NOT_LISTED = "Now list the remotes with `git remote -v`."
REMOTE_EXISTS = "`origin` already exists. To change its address, use `git remote set-url origin` and the new address."
HTTPS_URL = (
    "In this game the mothership is a folder next to your base, `../github/project.git`. At work the address "
    "would start with `https://`; here, `git remote set-url origin ../github/project.git` points it at the mothership."
)

REACTIONS = [
    kit.ReactionRule(line=r"git remote add origin\b", mood="err", text=REMOTE_EXISTS, outcome="failed", repository=True),
    kit.ReactionRule(line=r"git remote (add|set-url) \S+ (https?|ssh)://", mood="warn", text=HTTPS_URL, outcome="ok"),
    kit.ReactionRule(line=r"git remote (add|set-url) \S+ git@", mood="warn", text=HTTPS_URL, outcome="ok"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="Once your repository knows the mothership's address, what does the mothership hold?",
    options=("Your two commits", "Nothing yet", "A copy of your files"),
    reveal="Nothing yet: naming a remote only writes its address in your repository. Nothing travels until you send it.",
)


def watch_remote(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``origin`` names the lab's GitHub by the address the briefing gives.

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
    exists = kit.snapshot(lab.project)["exists"]
    remotes = kit.git_run(lab.project, "remote").stdout.split() if exists else []
    url = kit.git_run(lab.project, "remote", "get-url", REMOTE).stdout.strip() if REMOTE in remotes else ""
    message = CONTACT
    if not exists:
        message = NO_REPOSITORY
    elif not remotes:
        message = NO_REMOTE
    elif REMOTE not in remotes:
        message = OTHER_NAME
    elif not kit.reaches_github(lab, lab.project, url):
        message = WRONG_URL
    return kit.Verdict(message == CONTACT, message)


def watch_list(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git remote -v`` worked after the last line that set a remote, with ``origin`` right.

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
        The step's verdict; the remote comes first.
    """
    contact = watch_remote(lab, state, typed)
    listed = kit.typed(kit.after(typed, REMOTE_SET), LIST, "ok")
    verdict = kit.Verdict(listed, LISTED if listed else NOT_LISTED)
    return verdict if contact.solved else contact


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="remote", text="Name the mothership's address `origin`.", command="git remote add origin ../github/project.git", watch=watch_remote),
    kit.WatchStep(id="list", text="List the remotes your repository knows.", command="git remote -v", watch=watch_list),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with two commits, and an empty stand-in GitHub.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the level has nothing to remember.
    """
    kit.setup_github(lab)
    kit.git(lab.root, "init", "-q", str(lab.project))
    for day, (name, text) in enumerate(FILES.items(), start=1):
        (lab.project / name).write_text(text)
        kit.git(lab.project, "add", name)
        kit.git(lab.project, "commit", "-q", "-m", f"Add {name}", when=f"2026-05-0{day}T09:00:00+00:00")
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once ``origin`` is right and listed; the mothership may hold anything by then.

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
        The last goal's verdict, which checks the remote too.
    """
    return watch_list(lab, state, typed)


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


def guess(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Pick the prediction most players make.

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
        One of the options.
    """
    return GUESS.options[0]


def add_remote(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git remote add origin ../github/project.git`` in the project folder.

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
    typed.append(kit.type_line(lab.project, f"git remote add {REMOTE} {lab.github_url(lab.project)}"))
    return None


def list_remotes(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git remote -v`` in the project folder.

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
    typed.append(kit.type_line(lab.project, "git remote -v"))
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"guess": guess, "remote": add_remote, "list": list_remotes}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
