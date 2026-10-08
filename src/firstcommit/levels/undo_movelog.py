"""
The move log: ``git reflog`` lists every place HEAD has been, and ``HEAD@{n}`` names one, so a branch brings back commits no branch led to.

Time travel 8-4 (docs/drafts/sector8/8-4-script.md), guided, with a prediction. Setup makes 8-3's
two survey commits, then moves ``main`` back with ``git reset --hard origin/main`` and names them
nothing. The goals: ``git log`` typed (it cannot list them); ``git reflog`` typed; a branch
``survey`` on Survey day 2; the prediction (the line's number after a move); HEAD on ``survey``;
and ``git reflog`` typed again, to see the numbers shift. The commits erased for good are lost for
this play.
"""

from collections.abc import Callable

from firstcommit import kit
from firstcommit.levels import _undo_survey as survey

TITLE = "The move log"
DIFFICULTY = 2
XP = 150
COMMAND = "git reflog"
PAR = 5
PICTURES = kit.pictures("movelog", small="chain", ghosts=True)
CARD = kit.CommandCard(
    command="git reflog",
    text="The move log: every place `HEAD` has been, newest first. `HEAD@{1}` names where `HEAD` was one move ago.",
)
SCENE = [
    kit.SceneFrame(
        art="chain",
        text="The next day, the same mistake: two survey commits on `main`. This time you moved `main` back and forgot to name them. The chain shows only Start the project: no branch leads to the survey commits, and you have not looked for them yet.",
    ),
]

BRANCH = "survey"
LOG = r"git log\b"
REFLOG = r"git reflog(?! (expire|delete)\b)( |$)"
NAME = rf"git branch {BRANCH} \S+"
WRONG_LINE_TYPED = rf"git branch {BRANCH} HEAD@\{{0\}}( |$)"
WIPE_LINE = r"git (gc|prune|reflog (expire|delete))\b"

BRIEFING = """
The next day, the same mistake: two survey commits on `main`. This time you moved `main` back with
`git reset --hard origin/main` and forgot to name them. Find the two commits and put a branch
`survey` on them.

The mission is done when `survey` holds both survey commits, you are on it, and you have read the
move log again.
"""

HINTS = [
    "`git log` only walks back from where you are. `git reflog` lists every place `HEAD` has been, even commits no branch leads to.",
    "Find the line `commit: Survey day 2` in the move log; the `HEAD@{n}` after its hash names that commit. `git branch survey` followed by that name puts a name on it.",
    "Every line of the mission, in order:\n\n    $ git log --oneline\n    $ git reflog\n    $ git branch survey HEAD@{1}\n    $ git switch survey\n    $ git reflog",
]

DEBRIEF = """
`git log` only walks back from `HEAD` through the parents, so it could not see the survey. `git
reflog` lists every move of `HEAD`, newest first, and `HEAD@{1}` named the commit from one move
ago. `git branch survey HEAD@{1}` put a name on it, and both commits came back.

The hash at the start of each line works too, and unlike `HEAD@{n}` it never shifts. The move log
lives only in your repository, and Git keeps commits no branch leads to for about 30 days. A
branch keeps them for good.

Commands to keep:

    $ git reflog                    # every place HEAD has been
    $ git branch survey HEAD@{1}    # a name on a commit from the move log
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOGGED = "`git log` starts at `HEAD` and walks back through the parents. The survey commits came after Start the project, and no branch leads to them, so `git log` cannot list them."
NOT_LOGGED = "Look for them in the history: `git log --oneline`."
READ = (
    "`git log` is the story of your commits. `git reflog` is the story of your moves: every place `HEAD` has been, newest at "
    "the top, like your browser's history, which lists even the pages you closed. It lives only on your computer. Read it from "
    "the bottom up: the clone, your two survey commits, then the reset back to where you are now. Each line's `HEAD@{n}` names "
    "that place: `HEAD@{0}` is where you are now, `HEAD@{1}` where you were one move ago. `HEAD~1` walks back along the "
    "parents; `HEAD@{1}` walks back through your own moves."
)
NOT_READ = "Read the move log: `git reflog`."
NOT_NAMED = "Put a branch `survey` on Survey day 2: `git branch survey` and the `HEAD@{n}` of its line."
WRONG_LINE = "`survey` is on Start the project, where you are now. Survey day 2 is one move back: `HEAD@{1}`. Take the name off with `git branch -d survey` and try again."
NAMED = "A name on Survey day 2, and both survey commits are solid again: Survey day 1 is its parent. They were never gone."
NOT_ON = "Go there: `git switch survey`."
ON = "You are on `survey`, and `survey.txt` is back in your folder. Read the move log again."
READ_AGAIN = (
    "One new line on top, and every number grew by one: Survey day 2 was `HEAD@{1}`, now it is `HEAD@{2}`. The numbers count "
    "back from now, so read the move log right before you use it, or use the hash at the start of the line: it never shifts. "
    "The new line says `checkout`: that is the older name of `git switch`."
)
NOT_READ_AGAIN = "Read the move log again: `git reflog`."
ERASED = "The survey commits are gone for good. Start the mission again."
WIPE = "That cleans up commits no branch leads to: they can be erased for good once the move log forgets them. Give them a name first."
WRONG_LINE_SAID = "`survey` is on Start the project, where you are now. Survey day 2 is one move back: `HEAD@{1}`."

REACTIONS = [
    kit.ReactionRule(line=WIPE_LINE, mood="warn", text=WIPE, repository=True),
    kit.ReactionRule(line=WRONG_LINE_TYPED, mood="warn", text=WRONG_LINE_SAID, outcome="ok"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="Next you go to the branch with `git switch survey`. After that, which number will the line `commit: Survey day 2` have?",
    options=("Still `HEAD@{1}`", "`HEAD@{2}`", "`HEAD@{0}`"),
    reveal="`HEAD@{2}`. Going to a branch is a move, so it becomes the newest line, `HEAD@{0}`, and every older line counts one further back.",
)


def _erased(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Tell whether the survey's last commit is gone from the repository.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the survey's last commit.

    Returns
    -------
    kit.Verdict
        Lost once it is gone; else not solved, with no message.
    """
    gone = kit.git_run(lab.project, "cat-file", "-e", f"{state['tip']}^{{commit}}").returncode != 0
    return kit.Verdict(False, ERASED if gone else "", lost=gone)


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git log`` worked.

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


def watch_reflog(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git reflog`` worked.

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
    read = kit.typed(typed, REFLOG, "ok")
    verdict = kit.Verdict(read, READ if read else NOT_READ)
    return verdict if logged.solved else logged


def _named(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Tell whether ``survey`` names Survey day 2, wherever HEAD is; lost once the commits are erased.

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
        The verdict.
    """
    erased = _erased(lab, state)
    at = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"refs/heads/{BRANCH}^{{commit}}").stdout.strip()
    message = NAMED
    if not at:
        message = NOT_NAMED
    elif at == state["origin"]:
        message = WRONG_LINE
    elif at != state["tip"]:
        message = NOT_NAMED
    verdict = kit.Verdict(message == NAMED, message)
    return erased if erased.lost else verdict


def watch_named(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``survey`` names Survey day 2, after the move log was read.

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
        The step's verdict; the move log comes first.
    """
    read = watch_reflog(lab, state, typed)
    named = _named(lab, state, typed)
    return named if read.solved or named.lost else read


def watch_on(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once HEAD is on ``survey``, which names Survey day 2.

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
        The step's verdict; the name comes first.
    """
    named = _named(lab, state, typed)
    on = kit.snapshot(lab.project)["branch"] == BRANCH
    verdict = kit.Verdict(on, ON if on else NOT_ON)
    return verdict if named.solved else named


def watch_reflog_again(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git reflog`` worked after the switch to ``survey``.

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
        The step's verdict; HEAD on ``survey`` comes first.
    """
    on = watch_on(lab, state, typed)
    read = kit.typed(kit.after(typed, kit.switching(BRANCH)), REFLOG, "ok")
    verdict = kit.Verdict(read, READ_AGAIN if read else NOT_READ_AGAIN)
    return verdict if on.solved else on


QUEST: list[kit.Step] = [
    kit.WatchStep(id="log", text="Look for them in the history.", command="git log --oneline", watch=watch_log),
    kit.WatchStep(id="reflog", text="Read the move log.", command="git reflog", watch=watch_reflog),
    kit.WatchStep(id="name", text="Put a branch `survey` on Survey day 2.", command=f"git branch {BRANCH} HEAD@{{1}}", watch=watch_named),
    GUESS,
    kit.WatchStep(id="switch", text="Go there.", command=f"git switch {BRANCH}", watch=watch_on),
    kit.WatchStep(id="reflog-again", text="Read the move log again.", command="git reflog", watch=watch_reflog_again),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make the two survey commits on ``main``, then move ``main`` back to ``origin/main`` with no name on them.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``origin``: the mothership's ``main``; ``tip``: Survey day 2.
    """
    state = survey.survey(lab)
    kit.git(lab.project, "reset", "-q", "--hard", "origin/main")
    return state


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the move log was read on ``survey``; lost once the survey commits are erased.

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
        The last goal's verdict, or the loss.
    """
    erased = _erased(lab, state)
    return erased if erased.lost else watch_reflog_again(lab, state, typed)


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
    "log": kit.typing("git log --oneline"),
    "reflog": kit.typing("git reflog"),
    "name": kit.typing(f"git branch {BRANCH} HEAD@{{1}}"),
    "guess": kit.picking(GUESS.options[0]),
    "switch": kit.typing(f"git switch {BRANCH}"),
    "reflog-again": kit.typing("git reflog"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
