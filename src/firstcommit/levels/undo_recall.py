"""
Recall the capsule: ``git revert`` undoes a shared commit by adding one, and everyone gets the undo by pulling.

Wave 2, undo 7-2 (docs/drafts/chapters-5-9.md), a situation. Setup builds the playground: you
pushed a commit that set the lights to strobe, then a good one with a night route, and Alex
pulled both. The goals: the history read with ``git log`` (typed); a commit on your ``main``
that undoes the strobe while every shared commit stays in the history; and the mothership's
``main`` holding it. Once it is pushed, a level event has Alex pull, so the undo reaches Alex's
station the normal way. A forced push that drops the shared commits is lost for this play; a
reset that only moved your own ``main`` back is undone by a pull.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Recall the capsule"
DIFFICULTY = 2
XP = 150
COMMAND = "git revert"
PAR = 3
VIEW = "history"
CARD = kit.CommandCard(
    command="git revert <commit>",
    text="Makes a new commit that undoes an earlier one. The earlier commit stays in the history, so it is safe on a branch others have pulled.",
)
SCENE = [
    kit.SceneFrame(art="capsule", text="A capsule you launched set the station's lights to strobe, and Alex already has it."),
    kit.SceneFrame(art="chain", text="Capsules others have pulled stay in the chain. To take one back, you send a new capsule that undoes it."),
]

LIGHTS = "lights.cfg"
ROUTE = "route.txt"
STEADY = "lights=steady\n"
STROBE = "lights=strobe\n"
BAD_MESSAGE = "Try strobe lights"
LOOK = r"git log\b"
ROBIN = kit.Person("Robin Park", "robin@example.com")

BRIEFING = """
Yesterday you pushed a commit that set the station's lights to strobe, then a good one with the
night route. Alex has pulled both, and the strobe is giving everyone headaches. Undo the strobe for
the whole crew, and keep the night route.

The mission is done when you have read the history with `git log`, your `main` has a commit that
undoes the strobe, and the mothership's `main` has it too.
"""

HINTS = [
    "`git log --oneline` lists the commits, newest first: the strobe one is second from the top, `HEAD~1`.",
    "`git revert HEAD~1` makes a new commit that undoes it; then `git push` sends that commit up.",
    "Every line of the mission, in order:\n\n    $ git log --oneline\n    $ git revert HEAD~1\n    $ git push",
]

DEBRIEF = """
`git revert HEAD~1` did not remove the strobe commit: it made a new commit that does the opposite,
and the night route after it stayed. The history now tells the whole story: the strobe, and its
undo.

Because nothing in the shared history changed, `git push` went through like any other push, and
Alex's next `git pull` brought the undo to Alex's station. That is why revert is the tool for a
commit others already have. Moving `main` back with `git reset` would have needed a forced push,
which breaks everyone else's copy.

Commands to keep:

    $ git log --oneline     # find the commit to undo
    $ git revert HEAD~1     # a new commit that undoes it
    $ git push              # everyone gets the undo by pulling
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOOKED = "`git log` lists the strobe commit, with the night route after it."
NOT_LOOKED = "Read the history first: `git log --oneline`."
NOT_REVERTED = "The lights are still on strobe in your `main`. Undo that commit with a new one: `git revert HEAD~1`."
BEHIND = "Your `main` no longer holds the shared commits; the mothership still has them. `git pull` brings them back, then revert."
PAUSED = "A revert is paused. Finish it with `git revert --continue`, or call it off with `git revert --abort`."
ROUTE_LOST = "The night route is gone from your `main`. Only the strobe should be undone: `git revert HEAD~1` undoes that one commit."
REVERTED = "Your `main` has a commit that undoes the strobe, and the shared history is all still there."
NOT_PUSHED = "The mothership's `main` does not have your undo yet: `git push`."
PUSHED = "The mothership's `main` has your undo, so everyone gets it with their next pull."
REWRITTEN = (
    "The mothership's `main` no longer holds the commits Alex pulled: a forced push rewrote shared history. "
    "Start the mission again."
)
RESET_SHARED = (
    "That moved your `main` back, but the mothership and Alex still have those commits. To make the mothership "
    "forget them you would need `git push --force`, and that breaks everyone else's copy. `git pull` brings them back; "
    "`git revert` undoes a commit without rewriting anything."
)
FORCED = "`--force` replaced the mothership's `main` with yours, and the commits Alex pulled are gone from it."
FORCE = r"git push\b.*( -f\b| --force\b| --force-with-lease\b| \+)"

REACTIONS = [
    kit.ReactionRule(line=FORCE, mood="err", text=FORCED, outcome="ok", moment="force-break"),
    kit.ReactionRule(line=r"git reset\b", mood="warn", text=RESET_SHARED, outcome="ok", event="branch-moved", branch="main", moment="force-break"),
]


def alex_pulls(lab: kit.Lab, state: kit.State) -> None:
    """
    Have Alex pull, with the playground's button, so the undo reaches Alex's station.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    kit.press(lab, "alex", "pull")


EVENTS = [kit.LevelEvent(id="alex-pulls", run=alex_pulls, goal="push")]


def _tip(folder: Path, ref: str) -> str:
    """
    Give the commit a branch points at.

    Parameters
    ----------
    folder : Path
        A folder of the repository.
    ref : str
        The branch's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such branch.
    """
    return kit.git_run(folder, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def _rewritten(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether the mothership's ``main`` lost the commits Alex pulled.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the shared ``main``'s commit.

    Returns
    -------
    bool
        True once the mothership's ``main`` no longer holds it.
    """
    tip = _tip(lab.github, "refs/heads/main")
    return not tip or not kit.is_ancestor(lab.github, state["main"], tip)


def watch_look(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked.

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
    looked = kit.typed(typed, LOOK, "ok")
    return kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)


def watch_revert(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds the shared history and, on top, steady lights with the night route.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the shared ``main``'s commit.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; lost once the mothership's history was rewritten.
    """
    snap = kit.snapshot(lab.project)
    main = _tip(lab.project, "refs/heads/main") if snap["exists"] else ""
    holds = bool(main) and kit.is_ancestor(lab.project, state["main"], main)
    lights = kit.git_run(lab.project, "show", f"{main}:{LIGHTS}").stdout if holds else ""
    route = kit.git_run(lab.project, "cat-file", "-e", f"{main}:{ROUTE}").returncode == 0 if holds else False
    message = REVERTED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif _rewritten(lab, state):
        message = REWRITTEN
    elif snap["operation"] == "revert":
        message = PAUSED
    elif not holds:
        message = BEHIND
    elif not route:
        message = ROUTE_LOST
    elif lights != STEADY:
        message = NOT_REVERTED
    return kit.Verdict(message == REVERTED, message, lost=message == REWRITTEN)


def watch_push(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``main`` holds your reverted ``main``.

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
        The step's verdict; the revert's comes first.
    """
    reverted = watch_revert(lab, state, typed)
    main = _tip(lab.project, "refs/heads/main")
    up = _tip(lab.github, "refs/heads/main")
    pushed = bool(main) and bool(up) and kit.is_ancestor(lab.github, main, up)
    verdict = kit.Verdict(pushed, PUSHED if pushed else NOT_PUSHED)
    return verdict if reverted.solved else reverted


QUEST: list[kit.Step] = [
    kit.WatchStep(id="look", text="Find the strobe commit in the history.", command="git log --oneline", watch=watch_look),
    kit.WatchStep(id="revert", text="Undo the strobe with a new commit, and keep the night route.", command="git revert HEAD~1", watch=watch_revert),
    kit.WatchStep(id="push", text="Send the undo to the mothership.", command="git push", watch=watch_push),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground with steady lights, then your strobe commit and a night route, pushed and pulled by Alex.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``main``: the shared ``main``'s commit, the night route.
    """
    kit.setup_playground(lab)
    (lab.project / LIGHTS).write_text(STEADY)
    kit.git(lab.project, "add", LIGHTS)
    kit.git(lab.project, "commit", "-q", "-m", "Set the station lights", author=ROBIN, when="2026-07-10T09:00:00+00:00")
    (lab.project / LIGHTS).write_text(STROBE)
    kit.git(lab.project, "commit", "-q", "-am", BAD_MESSAGE, author=kit.PLAYER, when="2026-07-11T09:00:00+00:00")
    (lab.project / ROUTE).write_text("Night route: Moon, Phobos\n")
    kit.git(lab.project, "add", ROUTE)
    kit.git(lab.project, "commit", "-q", "-m", "Add the night route", author=kit.PLAYER, when="2026-07-11T10:00:00+00:00")
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    return {"main": kit.git(lab.project, "rev-parse", "main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the undo is on the mothership's ``main`` and the history was read.

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
        The push's verdict (it says when the work is lost) unless the look is missing.
    """
    pushed = watch_push(lab, state, typed)
    looked = watch_look(lab, state, typed)
    return looked if pushed.solved and not looked.solved else pushed


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
    "look": kit.typing("git log --oneline"),
    "revert": kit.typing("git revert HEAD~1"),
    "push": kit.typing("git push"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
