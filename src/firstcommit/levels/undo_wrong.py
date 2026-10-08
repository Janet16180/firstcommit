"""
Wrong course: ``git reset`` moves a label, and the commits it leaves stay in Git.

Wave 2, undo 7-3 (docs/drafts/chapters-5-9.md), a situation with a prediction. Setup builds the
playground and makes two commits of a survey on your ``main``, not pushed: they belonged on a
branch. One reset mode is taught, ``--hard``, on commits nobody else has. The goals: a branch
``rescue`` holding the two commits; then ``main`` back where the mothership's ``main`` is, with
the working folder matching it. A reset first is not a loss: the commits become ghosts that the
reflog still reaches, and ``rescue`` can be put on them afterwards (7-4 pays this off). The two
commits pushed to the mothership's ``main`` are lost for this play. The black box's tape is born
here, under history.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Wrong course"
DIFFICULTY = 2
XP = 150
COMMAND = "git reset --hard"
PAR = 2
TAPE = True
VIEW = "history"
CARD = kit.CommandCard(
    command="git reset --hard <commit>",
    text="Moves the branch you are on to another commit, and makes the staging area and the working folder match it. The commits it leaves stay in Git; a label keeps them easy to find.",
)
SCENE = [
    kit.SceneFrame(art="timeline", text="Two capsules of a survey landed on `main`. They belonged on a course of their own."),
    kit.SceneFrame(art="blackbox", text="Moving a label leaves a tick on the flight recorder's tape, and the capsules stay where they were."),
]

SURVEY = "survey.txt"
RESCUE = "rescue"
RESET_LINE = r"git reset\b"

BRIEFING = """
You made two commits of a survey on `main` by mistake: they belong on a branch of their own, and
the mothership has not seen them. Put a label on them, then move `main` back to where the
mothership's `main` is.

The mission is done when a branch `rescue` holds your two commits, and `main` is back on
`origin/main` with the working folder matching it.
"""

HINTS = [
    "`git branch rescue` puts a new label on the commit you are on, so the two commits keep a name.",
    "`git reset --hard origin/main` moves `main` back to the mothership's `main`, files included.",
    "Every line of the mission, in order:\n\n    $ git branch rescue\n    $ git reset --hard origin/main",
]

DEBRIEF = """
`git reset --hard origin/main` moved the `main` label back down the chain, and made the staging
area and the working folder match that commit. It deleted no commit: your two commits are still
there, held by `rescue`, ready to be worked on as a branch.

Without a label, they would still exist for a while, as ghosts that no label holds; the reflog,
Git's flight recorder, remembers where `main` was. Reset only commits nobody else has: on a pushed
branch, `git revert` is the safe undo.

`--soft` and `--mixed` move the label too, but keep your changes staged or in the working folder;
`--hard` is the one that rewrites the files.

Commands to keep:

    $ git branch rescue              # a label on the commits first
    $ git reset --hard origin/main   # then move main back
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_LABELLED = "Put a label on your two commits first: `git branch rescue`."
LABELLED = "`rescue` holds your two commits."
GHOSTS = (
    "`main` moved back and no label holds your two commits now, but Git still has them: the reflog remembers where `main` "
    "was. `git branch rescue HEAD@{1}` puts the label on them."
)
NOT_RESET = "`main` still holds the two commits. Move it back: `git reset --hard origin/main`."
DIRTY = "`main` is back, but the working folder does not match it. `git reset --hard origin/main` makes it match."
RESET = "`main` is back on `origin/main`, and `rescue` holds your two commits."
SHARED = "The mothership's `main` has your two survey commits now: others can pull them. Start the mission again."
MOVED_BACK = (
    "`main` moved back. The commits it left are still in Git: held by a label if you made one, or as ghosts that the "
    "reflog still reaches."
)

REACTIONS = [
    kit.ReactionRule(line=RESET_LINE, mood="info", text=MOVED_BACK, outcome="ok", event="branch-moved"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You label your two commits `rescue`, then move `main` back with `git reset --hard origin/main`. Where are the two commits after the reset?",
    options=("Deleted", "Still there, held by rescue"),
    reveal="Still there, held by `rescue`. A reset moves a label; it deletes no commit.",
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


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="rescue", text="Put a label on your two commits.", command=f"git branch {RESCUE}", watch=watch_rescue),
    kit.WatchStep(id="reset", text="Move `main` back to the mothership's `main`.", command="git reset --hard origin/main", watch=watch_reset),
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
    kit.setup_playground(lab)
    origin = kit.git(lab.project, "rev-parse", "main").strip()
    for day, line in enumerate(("Crater A: 4 km wide\n", "Crater B: 9 km wide\n"), start=1):
        with (lab.project / SURVEY).open("a") as survey:
            survey.write(line)
        kit.git(lab.project, "add", SURVEY)
        kit.git(lab.project, "commit", "-q", "-m", f"Survey day {day}", author=kit.PLAYER, when=f"2026-07-2{day}T09:00:00+00:00")
    return {"origin": origin, "tip": kit.git(lab.project, "rev-parse", "main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once ``rescue`` holds the survey and ``main`` is back on ``origin/main``, clean.

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
    return watch_reset(lab, state, typed)


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


def guess(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Pick the prediction the myth makes.

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


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "guess": guess,
    "rescue": kit.typing(f"git branch {RESCUE}"),
    "reset": kit.typing("git reset --hard origin/main"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
