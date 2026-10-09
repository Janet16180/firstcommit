"""
Wrong course: ``git reset --hard`` moves the branch you are on back, and the commits it leaves stay in Git.

Time travel 8-3 (docs/drafts/sector8/8-3-script.md), guided, with a prediction. Setup builds the
playground and makes two commits of a survey on your ``main``, not pushed: they belonged on a
branch. One reset mode is taught, ``--hard``, on commits nobody else has. The goals: a branch
``rescue`` holding the two commits; the prediction (how many commits ``git log`` lists after the
reset); ``main`` back where the mothership's ``main`` is, with the working folder matching it; and
``git log --oneline`` read after it. The chain then plays its WHAT IF: the same reset without
``rescue``, the two commits faded. A reset first is not a loss: the commits are ghosts the reflog
still reaches, which the next mission teaches to find. The two commits pushed to the mothership's
``main`` are lost for this play.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit
from firstcommit.levels import _undo_survey as survey

TITLE = "Wrong course"
DIFFICULTY = 2
XP = 150
COMMAND = "git reset --hard"
PAR = 3
PICTURES = kit.pictures("chain", folder=True, mothership=True, ghosts=True, whatif={"without": ["rescue"], "after": "log"})
CARD = kit.CommandCard(
    command="git reset --hard <commit>",
    text="Moves the branch you are on to another commit, and makes your folder match it. The commits it leaves stay in Git; a branch on them keeps them easy to find.",
)
SCENE = [
    kit.SceneFrame(
        art="chain",
        text="Two survey commits landed on `main` by mistake. The pin of the remote (the mothership) is two commits below: it has not seen them. Your folder has `survey.txt`, from those commits.",
    ),
]

SURVEY = survey.SURVEY
RESCUE = "rescue"
RESET_LINE = r"git reset\b"
LOG = r"git log\b"

BRIEFING = """
You made two survey commits on `main` by mistake: they belong on a branch of their own, and the
mothership has not seen them. Keep them on a branch `rescue`, and get `main` back to where the
mothership's `main` is.

The mission is done when `rescue` holds your two commits, `main` is back on `origin/main` with your
folder matching it, and you have checked the history.
"""

HINTS = [
    "`git branch rescue` puts a new name on the commit you are on, so the two commits keep a name.",
    "`git reset --hard origin/main` moves the branch you are on, `main`, to where `origin/main` is, and makes your files match.",
    "Every line of the mission, in order:\n\n    $ git branch rescue\n    $ git reset --hard origin/main\n    $ git log --oneline",
]

DEBRIEF = """
`git reset --hard origin/main` moved the branch you were on, `main`, back down the chain, and made
your folder match that commit. It deleted no commit: your two commits are still there, held by
`rescue`.

Without `--hard`, reset moves the branch and leaves your files as they are. Use reset only on
commits nobody else has: on a branch others have pulled, `git revert` is the safe undo.

Commands to keep:

    $ git branch rescue              # a name on the commits first
    $ git reset --hard origin/main   # then move main back
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_LABELLED = "Keep your commits on a branch first: `git branch rescue`."
LABELLED = (
    "`rescue` is a second name on the same commit. Nothing else changed: no new commit, no file. `HEAD` still rides `main`. "
    "Next, `git reset --hard origin/main` moves the branch you are on, `main`, to the commit your `origin/main` bookmark is on, "
    "*Start the project*. `--hard` also makes your folder match that commit; without it, the branch moves and your files stay as they are."
)
GHOSTS = (
    "No branch leads to your two commits now, but Git still has them. The next mission shows how to find them; for now, "
    "start again with Restart."
)
NOT_RESET = "`main` still holds the two commits. Move it back: `git reset --hard origin/main`."
DIRTY = "`main` is back, but your folder does not match it. `git reset --hard origin/main` makes it match."
RESET = (
    '`main` slid down two commits, and `HEAD` rode it: "HEAD is now at" names where you are. The commits did not move: '
    "`rescue` still holds them. `survey.txt` left your folder."
)
LOGGED = (
    "One commit, as predicted. `git log` walks down from `HEAD`, and nothing below *Start the project* leads up to the survey "
    "commits. They are still in Git: `rescue` leads to them. What if you had not made the branch? No branch would lead to the "
    "two commits. Git keeps commits no branch leads to for about 30 days, then may delete them, and `git log` would not list them."
)
NOT_LOGGED = "Check: `git log --oneline`."
SHARED = "The mothership's `main` has your two survey commits now: others can pull them. Start the mission again."
MOVED_BACK = "`main` moved back. The commits it left are still in Git."

REACTIONS = [
    kit.ReactionRule(line=RESET_LINE, mood="info", text=MOVED_BACK, outcome="ok", event="branch-moved"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="After the reset, how many commits will `git log --oneline` list?",
    options=("1", "3"),
    reveal="1. `git log` starts at `HEAD` and walks down the parents. `HEAD` rides `main`, which will be on *Start the project*, the oldest commit. The two survey commits sit above it, where only `rescue` leads.",
)


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


def _shared(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether the mothership's ``main`` holds the survey commits.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the survey's last commit.

    Returns
    -------
    bool
        True once they were pushed there.
    """
    tip = _tip(lab.github, "refs/heads/main")
    return bool(tip) and kit.is_ancestor(lab.github, state["tip"], tip)


def watch_rescue(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a branch ``rescue`` holds the survey's last commit.

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
        The step's verdict; lost once the survey reached the mothership's ``main``.
    """
    snap = kit.snapshot(lab.project)
    rescue = _tip(lab.project, f"refs/heads/{RESCUE}") if snap["exists"] else ""
    held = bool(rescue) and kit.is_ancestor(lab.project, state["tip"], rescue)
    ghosts = state["tip"] in {ghost["hash"] for ghost in kit.ghosts(lab.project)} if snap["exists"] else False
    message = LABELLED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif _shared(lab, state):
        message = SHARED
    elif not held:
        message = GHOSTS if ghosts else NOT_LABELLED
    return kit.Verdict(message == LABELLED, message, lost=message == SHARED)


def watch_reset(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``main`` is back on the mothership's ``main`` and the working folder matches it.

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
        The step's verdict; the label's comes first.
    """
    rescued = watch_rescue(lab, state, typed)
    snap = kit.snapshot(lab.project)
    back = _tip(lab.project, "refs/heads/main") == state["origin"]
    clean = not kit.staged(snap) and not kit.unstaged(snap)
    message = RESET
    if not back:
        message = NOT_RESET
    elif not clean:
        message = DIRTY
    verdict = kit.Verdict(message == RESET, message)
    return verdict if rescued.solved else rescued


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git log`` worked after the reset.

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
        The step's verdict; the reset comes first.
    """
    reset = watch_reset(lab, state, typed)
    logged = kit.typed(kit.after(typed, RESET_LINE), LOG, "ok")
    verdict = kit.Verdict(logged, LOGGED if logged else NOT_LOGGED)
    return verdict if reset.solved else reset


QUEST: list[kit.Step] = [
    kit.WatchStep(id="rescue", text="Keep your commits on a branch.", command=f"git branch {RESCUE}", watch=watch_rescue),
    GUESS,
    kit.WatchStep(id="reset", text="Move `main` back.", command="git reset --hard origin/main", watch=watch_reset),
    kit.WatchStep(id="log", text="Check.", command="git log --oneline", watch=watch_log),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground and commit two survey commits on your ``main``, not pushed.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``origin``: the mothership's ``main``; ``tip``: the survey's last commit.
    """
    return survey.survey(lab)


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once ``rescue`` holds the survey, ``main`` is back on ``origin/main``, clean, and the history was read.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the repository.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The last goal's verdict, which checks the label first.
    """
    return watch_log(lab, state, typed)


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
        None: the level reads the repository.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "rescue": kit.typing(f"git branch {RESCUE}"),
    "guess": kit.picking(GUESS.options[1]),
    "reset": kit.typing("git reset --hard origin/main"),
    "log": kit.typing("git log --oneline"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
