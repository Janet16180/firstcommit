"""
A name on any commit: names can be taken off and put on any commit, and the commits stay.

Name tags 5-2 (docs/drafts/sector5/5-2-script.md), guided, with two predictions. Setup rebuilds
the story to 5-1's end and the ``git pull`` it ended on (`_names_story.any_commit`): ``main`` on
Alex's route fix, ``test-run`` still on the first commit. The goals: the history read; ``test-run``
taken off, the history read again (still five commits); ``first-route`` put on Plot the route by
its hash; and the history read a third time.
"""

from collections.abc import Callable

from firstcommit import kit
from firstcommit.levels import _names_story as story

TITLE = "A name on any commit"
DIFFICULTY = 1
XP = 100
COMMAND = "git branch <name> <commit>"
PAR = 5
VIEW = "history"
CARD = kit.CommandCard(
    command="git branch <name> <commit>",
    text="Puts a new name on any commit, given by its hash. You stay where you are, and your folder does not change.",
)
SCENE = [
    kit.SceneFrame(
        art="chain",
        text="After your pull, `main` slid up to Alex's fix, and your bookmark and the mothership's pin are there too. `test-run` is still on Start the project.",
    ),
]

LOG = r"git log\b"
DELETE = rf"git branch (-d|-D|--delete)( -\S+)* {story.OLD_NAME}( |$)"
NAME = rf"git branch {story.FIRST_ROUTE} \S+"
TO_FIRST_ROUTE = kit.switching(story.FIRST_ROUTE)

BRIEFING = """
Before this mission you ran `git pull`, the step the last mission ended on, so `main` is on Alex's
fix, Fix the route. `test-run`, an old name on Start the project, can go. Then the captain wants
the commit where the route was first plotted easy to find, under a name `first-route`.

The mission is done when `test-run` is gone, `first-route` names Plot the route, and you have
checked the history after each change.
"""

HINTS = [
    "`git branch -d <name>` takes a name off. Each line of `git log --oneline` starts with the commit's hash.",
    "`git branch <name> <hash>` puts a name on that commit.",
    "Every line of the mission, in order:\n\n    $ git log --oneline\n    $ git branch -d test-run\n    $ git log --oneline\n    $ git branch first-route {{route}}\n    $ git log --oneline",
]

DEBRIEF = """
`git branch -d test-run` took a name off and the commit stayed: names point at commits, they are
not the commits. `git branch first-route <hash>` put a name on an old commit without moving you.

Each commit remembers the one before it, its parent, so a name leads down to every older commit:
that is how `git log` starts at `main` and walks down to the first commit.

Commands to keep:

    $ git branch -d test-run          # take a name off; the commit stays
    $ git branch first-route <hash>   # a name on any commit
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOGGED = (
    "Each line starts with the commit's hash: the way to name a commit to Git. Each commit remembers the one before it, "
    "its parent: `git log` starts at `main`'s commit and follows those lines down to the first commit, Start the project, with `test-run` on it."
)
NOT_LOGGED = "Read the history: `git log --oneline`."
NOT_DELETED = "`test-run` is still there. Take the name off: `git branch -d test-run`."
DELETED = 'Git says which commit the name pointed at: look at "was" and the hash after it. The commit is still there.'
LOGGED_AGAIN = "Still five commits. Only a name went. Now find Plot the route, one line up: its hash is the one you need next."
NOT_LOGGED_AGAIN = "Check the history: `git log --oneline`."
NOT_NAMED = "There is no `first-route` yet. Put it on Plot the route: `git branch first-route` and that commit's hash, from `git log --oneline`."
ELSEWHERE = "`first-route` is on another commit. Take it off with `git branch -d first-route`, then put it on Plot the route, by the hash `git log --oneline` shows for it."
NAMED = "A name on an old commit, and nothing else moved. Without a hash, `git branch` puts the name where you are."
LOGGED_THIRD = "`git log` shows the new name in brackets on its commit."
NOT_LOGGED_THIRD = "Check the history: `git log --oneline`."
MOVED_ONTO = "You moved `HEAD` onto `first-route`, and your folder now shows that commit's files. `git switch main` brings you back."

REACTIONS = [
    kit.ReactionRule(line=TO_FIRST_ROUTE, mood="info", text=MOVED_ONTO, outcome="ok"),
]

DELETE_GUESS = kit.ChoiceStep(
    id="guess-delete",
    text="Predict first.",
    question="You take the name `test-run` off with `git branch -d test-run`. What happens to the Start the project commit?",
    options=("It is deleted too", "It stays"),
    reveal="It stays. A name points at a commit; it is not the commit. And `main` still leads down the lines to it.",
)
NAME_GUESS = kit.ChoiceStep(
    id="guess-name",
    text="Predict first.",
    question="You put a new name `first-route` on Plot the route, by its hash. What happens to your folder?",
    options=("It shows that commit's files", "Nothing changes"),
    reveal="Nothing changes. `git branch` only writes a name. `HEAD` stays on `main`, so your files stay as they are.",
)


def _tip(lab: kit.Lab, ref: str) -> str:
    """
    Give the commit a ref points at.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    ref : str
        The ref's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such ref.
    """
    return kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked.

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
        The step's verdict.
    """
    message = LOGGED if kit.typed(typed, LOG, "ok") else NOT_LOGGED
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == LOGGED, message)


def watch_delete(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``test-run`` is gone.

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
        The step's verdict; the history comes first.
    """
    logged = watch_log(lab, state, typed)
    deleted = not _tip(lab, f"refs/heads/{story.OLD_NAME}")
    verdict = kit.Verdict(deleted, DELETED if deleted else NOT_DELETED)
    return verdict if logged.solved else logged


def watch_log_again(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked after ``test-run`` was taken off.

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
        The step's verdict; the name taken off comes first.
    """
    deleted = watch_delete(lab, state, typed)
    logged = kit.typed(kit.after(typed, DELETE), LOG, "ok")
    verdict = kit.Verdict(logged, LOGGED_AGAIN if logged else NOT_LOGGED_AGAIN)
    return verdict if deleted.solved else deleted


def watch_name(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``first-route`` names Plot the route.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: Plot the route's hash.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; the history read after the name was taken off comes first.
    """
    logged = watch_log_again(lab, state, typed)
    at = _tip(lab, f"refs/heads/{story.FIRST_ROUTE}")
    message = NAMED
    if not at:
        message = NOT_NAMED
    elif not at.startswith(state["route"]):
        message = ELSEWHERE
    verdict = kit.Verdict(message == NAMED, message)
    return verdict if logged.solved else logged


def watch_log_third(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked after ``first-route`` was put on.

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
        The step's verdict; the new name comes first.
    """
    named = watch_name(lab, state, typed)
    logged = kit.typed(kit.after(typed, NAME), LOG, "ok")
    verdict = kit.Verdict(logged, LOGGED_THIRD if logged else NOT_LOGGED_THIRD)
    return verdict if named.solved else named


QUEST: list[kit.Step] = [
    kit.WatchStep(id="log", text="Read the history.", command="git log --oneline", watch=watch_log),
    DELETE_GUESS,
    kit.WatchStep(id="delete", text="Take the old name off.", command=f"git branch -d {story.OLD_NAME}", watch=watch_delete),
    kit.WatchStep(id="log-again", text="Check the history.", command="git log --oneline", watch=watch_log_again),
    NAME_GUESS,
    kit.WatchStep(id="name", text="Name the commit where the route was first plotted.", command=f"git branch {story.FIRST_ROUTE} {{{{route}}}}", watch=watch_name),
    kit.WatchStep(id="log-third", text="Check the history.", command="git log --oneline", watch=watch_log_third),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Rebuild the story to 5-1's end and its pull.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``route``: Plot the route's short hash, for the hints.
    """
    story.any_commit(lab)
    return {"route": kit.git(lab.project, "rev-parse", "--short", "main~3").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the history was read after ``first-route`` named Plot the route.

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
    return watch_log_third(lab, state, typed)


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


def name_route(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git branch first-route`` with Plot the route's hash.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the hash.
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    return kit.typing(f"git branch {story.FIRST_ROUTE} {state['route']}")(lab, state, typed)


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "log": kit.typing("git log --oneline"),
    "guess-delete": kit.picking(DELETE_GUESS.options[0]),
    "delete": kit.typing(f"git branch -d {story.OLD_NAME}"),
    "log-again": kit.typing("git log --oneline"),
    "guess-name": kit.picking(NAME_GUESS.options[0]),
    "name": name_route,
    "log-third": kit.typing("git log --oneline"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
