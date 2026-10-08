"""
Black box: the boss of the time-travel chapter. A deleted branch, found again in the reflog, labelled and launched.

Wave 2, undo 7-4 (docs/drafts/chapters-5-9.md), a challenge combining the vault (commits),
branches (a label, a push by name) and this chapter (the reflog finds commits no label holds).
Setup builds the playground and, in your clone, two commits on a branch ``thrusters``; then you
switched to ``main`` and deleted the branch, unpushed. The goals are end states, met in any
order: a branch ``thrusters`` in your repository holding both commits; and the mothership holding
``thrusters`` with them, its ``main`` untouched. The commits erased for good (a pruned reflog), or
pushed onto the mothership's ``main``, are lost for this play.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Black box"
DIFFICULTY = 3
XP = 250
COMMAND = "git reflog"
PAR = 3
TAPE = True
VIEW = "blackbox"
CHALLENGE = True
CARD = kit.CommandCard(
    command="git reflog",
    text="Lists where `HEAD` has been, newest first, as `HEAD@{0}`, `HEAD@{1}` and so on. Commits no label holds any more can be found there and given a label again.",
)
SCENE = [
    kit.SceneFrame(art="alarm", text="Alarm on the engine deck: two days of thruster work vanished with its branch."),
    kit.SceneFrame(art="blackbox", text="Nothing was pushed. But the flight recorder was running the whole time."),
]

BRANCH = "thrusters"
THRUSTERS = "thrusters.cfg"
WIPE_LINE = r"git (gc|prune|reflog (expire|delete))\b"

BRIEFING = """
Last night you worked two days of thruster tuning into commits on a branch `thrusters`. Then,
half asleep, you switched to `main` and deleted the branch with `git branch -D`. It was never
pushed, and the review is this morning.

The mission is done when your repository has a branch `thrusters` holding both commits again, and
the mothership has `thrusters` too, with its `main` untouched.
"""

HINTS = [
    "This is the vault, branches and this chapter: commits no label holds, a label, and a push by name.",
    "The reflog lists where `HEAD` has been: the line before the switch to `main` names the branch's last commit. A label on it brings both commits back.",
    "Every line of the mission, in order:\n\n    $ git reflog\n    $ git branch thrusters HEAD@{1}\n    $ git push -u origin thrusters",
]

DEBRIEF = """
`git branch -D` removed a label, not the commits: they stayed in Git as ghosts no label held.
`git reflog` showed every move of `HEAD`, and `HEAD@{1}`, where it was one move before the switch
to `main`, was the branch's last commit. `git branch thrusters HEAD@{1}` gave it its label back,
both commits with it, and `git push -u origin thrusters` sent them up for review.

The reflog lives in your repository only, and by default it keeps entries like these, for commits
no label holds, for about a month. The mothership and every other clone have recorders of their
own.

Commands to keep:

    $ git reflog                       # where HEAD has been
    $ git branch thrusters HEAD@{1}    # a label on a commit from the reflog
    $ git push -u origin thrusters     # and up it goes
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_RESCUED = "Your repository has no branch `thrusters` holding both commits."
RESCUED = "`thrusters` holds both commits again."
NOT_LAUNCHED = "The mothership has no `thrusters` holding both commits."
LAUNCHED = "The mothership has `thrusters` with both commits, and its `main` is untouched."
ERASED = "The thruster commits are gone for good: the black box was wiped and Git pruned them. Start the mission again."
MAIN_TOUCHED = "The mothership's `main` holds the thruster commits now, without review. Start the mission again."
WIPE = (
    "That cleans Git's black box: commits no label holds can be erased for good once the reflog forgets them. "
    "Give them a label first."
)

REACTIONS = [
    kit.ReactionRule(line=WIPE_LINE, mood="warn", text=WIPE, repository=True),
]


def _tip(folder: Path, ref: str) -> str:
    """
    Give the commit a ref points at.

    Parameters
    ----------
    folder : Path
        A folder of the repository.
    ref : str
        The ref's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such ref.
    """
    return kit.git_run(folder, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def _loss(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Name the way the work is lost for this play, if it is.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the branch's last commit and the mothership's ``main``.

    Returns
    -------
    str | None
        `MAIN_TOUCHED`, `ERASED` or `NO_REPOSITORY`, or None while the work can still be saved.
    """
    exists = kit.snapshot(lab.project)["exists"]
    kept = exists and kit.git_run(lab.project, "cat-file", "-e", f"{state['tip']}^{{commit}}").returncode == 0
    loss = None
    if not exists:
        loss = NO_REPOSITORY
    elif _tip(lab.github, "refs/heads/main") != state["main"]:
        loss = MAIN_TOUCHED
    elif not kept:
        loss = ERASED
    return loss


def watch_rescued(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a branch ``thrusters`` holds the branch's last commit.

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
        The goal's verdict; lost once the work is.
    """
    loss = _loss(lab, state)
    branch = _tip(lab.project, f"refs/heads/{BRANCH}") if loss is None else ""
    held = bool(branch) and kit.is_ancestor(lab.project, state["tip"], branch)
    message = loss or (RESCUED if held else NOT_RESCUED)
    return kit.Verdict(message == RESCUED, message, lost=loss is not None)


def watch_launched(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``thrusters`` holds the branch's last commit and its ``main`` is untouched.

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
        The goal's verdict; lost once the work is.
    """
    loss = _loss(lab, state)
    branch = _tip(lab.github, f"refs/heads/{BRANCH}") if loss is None else ""
    held = bool(branch) and kit.is_ancestor(lab.github, state["tip"], branch)
    message = loss or (LAUNCHED if held else NOT_LAUNCHED)
    return kit.Verdict(message == LAUNCHED, message, lost=loss is not None)


QUEST: list[kit.Step] = [
    kit.WatchStep(id="rescued", text="Your repository has a branch `thrusters` holding both commits.", watch=watch_rescued),
    kit.WatchStep(id="launched", text="The mothership has `thrusters` with both commits, and its `main` is untouched.", watch=watch_launched),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground, make two commits on ``thrusters`` in your clone, then switch to ``main`` and delete the branch.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``tip``: the branch's last commit; ``main``: the mothership's ``main``.
    """
    kit.setup_playground(lab)
    kit.git(lab.project, "switch", "-q", "-c", BRANCH)
    for day, line in enumerate(("thrust=80\n", "thrust=80\nburn=12s\n"), start=1):
        (lab.project / THRUSTERS).write_text(line)
        kit.git(lab.project, "add", THRUSTERS)
        kit.git(lab.project, "commit", "-q", "-m", f"Tune the thrusters, day {day}", author=kit.PLAYER, when=f"2026-08-0{day}T21:00:00+00:00")
    tip = kit.git(lab.project, "rev-parse", "HEAD").strip()
    kit.git(lab.project, "switch", "-q", "main")
    kit.git(lab.project, "branch", "-q", "-D", BRANCH)
    return {"tip": tip, "main": kit.git(lab.github, "rev-parse", "main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once both goals are met; a lost verdict comes first.

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
        The verdict.
    """
    verdicts = [step.watch(lab, state, typed) for step in QUEST if isinstance(step, kit.WatchStep)]
    unmet = sorted((verdict for verdict in verdicts if not verdict.solved), key=lambda verdict: not verdict.lost)
    return unmet[0] if unmet else verdicts[-1]


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every goal's action, in order (AUTHORING section 3.6).

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
        None: the level reads the repositories.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "rescued": kit.typing(f"git branch {BRANCH} HEAD@{{1}}"),
    "launched": kit.typing(f"git push -u origin {BRANCH}"),
}
"""The player's part of each goal, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
