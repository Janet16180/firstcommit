"""
Push refused: Alex pushed first, your push bounces, and a pull joins the two histories.

Wave 1, mothership 4-4 (docs/drafts/chapters-3-7.md), a situation. Setup builds the playground
and your morning's commit of the route. Alex's commit and push is a level event, run after the
page's first look, so the page animates Alex's capsule docking while yours waits on the ground.
The goals: a push that git refuses (typed: the refusal is the lesson), Alex's commit in your
``main`` (``git pull --no-rebase`` or ``--rebase``, both pass: the goal reads the history), and
the mothership holding both commits. ``pull.rebase`` stays unset, so a plain ``git pull`` stops
with git's question and Rama names the two answers. A forced push that drops Alex's commit from
the mothership is lost for this play.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Push refused"
DIFFICULTY = 2
XP = 180
COMMAND = "git pull --no-rebase"
PAR = 3
CARD = kit.CommandCard(
    command="git pull --no-rebase",
    text="Brings the remote's commits into your branch and joins the two histories with a merge commit. `--rebase` replays your commits on top of the remote's instead.",
)
SCENE = [
    kit.SceneFrame(art="rocket", text="Your capsule is ready on the launch pad, and Alex is working too."),
    kit.SceneFrame(art="orbit", text="When two crews send capsules to the same place, the mothership takes the first and refuses to drop it."),
]

ROUTE = "route.txt"
REPORT = "notes.txt"
PUSH = r"git push\b"
FORCE = r"git push\b.*( -f\b| --force\b| --force-with-lease\b| \+)"

BRIEFING = """
You committed the route this morning. Alex has just pushed a report to the mothership. Send your
commit up, and keep Alex's.

The mission is done when you have seen your push refused, Alex's commit is in your `main`, and the
mothership holds both commits.
"""

HINTS = [
    "A refused push loses nothing: bring Alex's commit into your `main` first, then push again.",
    "`git pull --no-rebase` joins the two histories with a merge commit; `git pull --rebase` puts your commit on top of Alex's. Then `git push`.",
]

DEBRIEF = """
Git refused your push because the mothership had a commit your `main` did not: taking yours would
have dropped Alex's. Nothing was lost. `git pull` with `--no-rebase` joined the two histories in a
merge commit, or with `--rebase` replayed your commit on top of Alex's; either way your `main`
then held both, and the push went through.

Merge commits get their own chapter: Collisions.

Commands to keep:

    $ git pull --no-rebase   # bring the remote's commits in, joined by a merge commit
    $ git pull --rebase      # or replay your commits on top of the remote's
    $ git push
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
WAITING = "Alex is still on the way. Wait a moment for the report."
BOUNCED = "Git refused the push: the mothership has Alex's commit, and your `main` does not."
NOT_BOUNCED = "Send your commit up: `git push`."
JOINED = "Your `main` holds Alex's commit and yours."
NOT_JOINED = "Your `main` does not hold Alex's commit yet. Bring it in: `git pull --no-rebase`."
SENT = "The mothership holds Alex's commit and yours."
NOT_SENT = "Send the joined history up: `git push`."
ALEX_DROPPED = (
    "The mothership's `main` no longer holds Alex's commit: a forced push replaced it with yours. At work, that erases "
    "a teammate's work. Start the mission again."
)
CHOOSE = (
    "Git stopped: both you and Alex added commits, so it asks how to join them. `git pull --no-rebase` joins the two histories "
    "with a merge commit; `git pull --rebase` replays your commit on top of Alex's. Either works here."
)
FORCED = "`--force` replaced the mothership's `main` with yours, and Alex's commit is gone from it. A refused push never needs it."

REACTIONS = [
    kit.ReactionRule(line=r"git pull$", mood="info", text=CHOOSE, outcome="failed", repository=True),
    kit.ReactionRule(line=FORCE, mood="err", text=FORCED, outcome="ok"),
]


def alex_pushes(lab: kit.Lab, state: kit.State) -> None:
    """
    Have Alex add a line to the report, commit it and push it, with the playground's buttons.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    for button in (f"edit:{REPORT}", f"add:{REPORT}", "commit", "push"):
        kit.press(lab, "alex", button)


EVENTS = [kit.LevelEvent(id="alex-pushes", run=alex_pushes)]


def _alex(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Give Alex's commit once Alex has made it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: GitHub's first commit.

    Returns
    -------
    str | None
        The tip of Alex's ``main`` once it moved past the first commit, else None.
    """
    tip = kit.git_run(lab.teammate, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    return tip if tip and tip != state["start"] else None


def _dropped(lab: kit.Lab, alex: str | None) -> bool:
    """
    Tell whether the mothership's ``main`` lost Alex's commit after Alex pushed it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    alex : str | None
        Alex's commit, or None before Alex made it.

    Returns
    -------
    bool
        True when GitHub had it (its reflog says so) and its ``main`` no longer leads to it.
    """
    pushed = alex is not None and alex in kit.git_run(lab.github, "reflog", "--format=%H", "main").stdout.split()
    return pushed and not kit.is_ancestor(lab.github, alex or "", "refs/heads/main")


def watch_bounce(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git push`` failed after Alex pushed.

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
        The step's verdict.
    """
    bounced = kit.typed(typed, PUSH, "failed")
    message = BOUNCED if bounced else NOT_BOUNCED
    if _alex(lab, state) is None:
        message = WAITING
    return kit.Verdict(message == BOUNCED, message)


def watch_join(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds Alex's commit and your route.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; lost once a forced push dropped Alex's commit.
    """
    alex = _alex(lab, state)
    exists = kit.snapshot(lab.project)["exists"]
    dropped = _dropped(lab, alex)
    joined = alex is not None and kit.is_ancestor(lab.project, alex, "refs/heads/main") and _holds_route(lab.project, "refs/heads/main")
    message = JOINED if joined else NOT_JOINED
    if not exists:
        message = NO_REPOSITORY
    elif dropped:
        message = ALEX_DROPPED
    elif alex is None:
        message = WAITING
    return kit.Verdict(message == JOINED, message, lost=dropped)


def watch_send(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``main`` holds Alex's commit and your route.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; your ``main`` comes first.
    """
    joined = watch_join(lab, state, typed)
    alex = _alex(lab, state)
    sent = alex is not None and kit.is_ancestor(lab.github, alex, "refs/heads/main") and _holds_route(lab.github, "refs/heads/main")
    verdict = kit.Verdict(sent, SENT if sent else NOT_SENT)
    return verdict if joined.solved else joined


def _holds_route(folder: Path, ref: str) -> bool:
    """
    Tell whether a branch's last commit holds the route.

    Parameters
    ----------
    folder : Path
        A repository.
    ref : str
        The branch.

    Returns
    -------
    bool
        True when its tree has ``route.txt``.
    """
    return kit.git_run(folder, "rev-parse", "-q", "--verify", f"{ref}:{ROUTE}").returncode == 0


QUEST: list[kit.Step] = [
    kit.WatchStep(id="push", text="Send your commit to the mothership.", command="git push", watch=watch_bounce),
    kit.WatchStep(id="pull", text="Bring Alex's commit into your `main`.", command="git pull --no-rebase", watch=watch_join),
    kit.WatchStep(id="send", text="Send both commits up.", command="git push", watch=watch_send),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground and commit the route in your clone, as you did this morning.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``start``: GitHub's first commit, so the check knows when Alex has pushed.
    """
    kit.setup_playground(lab)
    (lab.project / ROUTE).write_text("Route: Earth, Moon, Mars\n")
    kit.git(lab.project, "add", ROUTE)
    kit.git(lab.project, "commit", "-q", "-m", "Add the route", author=kit.PLAYER)
    return {"start": kit.git(lab.github, "rev-parse", "refs/heads/main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the mothership holds both commits; the quest keeps the refusal first.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the repositories.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The last goal's verdict.
    """
    return watch_send(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player, after Alex's push: every quest step's action, in order.

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
        None: the level reads the repositories.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "push": kit.typing("git push"),
    "pull": kit.typing("git pull --no-rebase"),
    "send": kit.typing("git push"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
