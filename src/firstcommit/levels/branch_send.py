"""
Send a course up: a push sends one branch, and a new branch goes up by name.

Wave 2, branch 5-3 (docs/drafts/chapters-3-7.md), guided. Setup builds the playground and, in
your clone, a branch ``scout`` with two commits of a survey, while ``main`` is level with the
mothership. The goals: a plain ``git push`` on ``main`` that worked (typed: it breaks the myth
that a push sends everything); the mothership holding ``scout`` at your ``scout``'s commit, its
``main`` unchanged; and the remote-tracking branches listed with ``git branch -r`` after that.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Send a course up"
DIFFICULTY = 2
XP = 150
COMMAND = "git push -u origin <branch>"
PAR = 3
CARD = kit.CommandCard(
    command="git push origin <branch>",
    text="Sends that branch to the remote, by name, from whichever branch you are on. A plain `git push` sends only the branch you are on, to its upstream.",
)
SCENE = [
    kit.SceneFrame(art="rocket", text="Your survey sits on a second course, `scout`, two capsules long."),
    kit.SceneFrame(art="orbit", text="The mothership gets only what you send it, one branch at a time."),
]

BRANCH = "scout"
SURVEY = "survey.txt"
SURVEYS = [("Survey crater A", "Crater A: ice\n"), ("Survey crater B", "Crater A: ice\nCrater B: iron\n")]
PLAIN_PUSH = r"git push$"
SEND = r"git push\b"
LIST = r"git branch( -r| --remotes| -a| --all)\b"

BRIEFING = """
Your survey is on the branch `scout`, two commits long. `main` is level with the mothership. The
team wants to review the survey, so it must reach the mothership, and its `main` must not change.

The mission is done when you have pushed from `main`, the mothership has `scout` at your
`scout`'s commit with its `main` unchanged, and you have listed the remote's branches with
`git branch -r`.
"""

HINTS = [
    "On `main`, `git push` sends `main` only. Look at what the mothership has afterwards.",
    "Name the branch to send it: `git push -u origin scout` works from any branch.",
    "`git branch -r` lists what your repository knows of the remote's branches, such as `origin/main`.",
]

DEBRIEF = """
A plain `git push` on `main` sent `main`, which had nothing new, and left `scout` here. A push
sends one branch unless you ask for more. `git push -u origin scout` named the branch: the
mothership now has `scout` for the team to review, and its `main` did not move. `-u` made
`origin/scout` the upstream of your `scout`, so a plain `git push` on `scout` sends it next time.

`git branch -r` lists your repository's records of the remote's branches: `origin/main`, and now
`origin/scout`.

At work, you push your task's branch by name and ask for a review; `main` changes only when the
review is merged.

Commands to keep:

    $ git push -u origin scout   # send a new branch, by name, and track it
    $ git branch -r              # the remote's branches, as last heard
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_PUSHED = "Push from `main` first: `git push`."
PUSHED_MAIN = "A plain `git push` sent `main` only. The mothership still has no `scout`."
NOT_SENT = "The mothership has no `scout` yet. Send it by name: `git push -u origin scout`."
BEHIND = "The mothership's `scout` is not at your `scout`'s commit. Send it again: `git push origin scout`."
MAIN_MOVED = "The mothership's `main` changed: the survey should reach it only through review. Start the mission again."
SENT = "The mothership has `scout` now, with both survey commits; its `main` did not change."
LISTED = "`origin/scout` sits next to `origin/main`: your repository's record of the mothership's branches."
NOT_LISTED = "List the remote's branches: `git branch -r`."
NO_UPSTREAM = (
    "`scout` has no upstream yet, so a plain `git push` does not know where to send it. Name the remote and the "
    "branch once: `git push -u origin scout`."
)

REACTIONS = [
    kit.ReactionRule(line=PLAIN_PUSH, mood="info", text=NO_UPSTREAM, outcome="failed", repository=True),
]


def _tip(folder: Path, ref: str) -> str:
    """
    Give the commit a branch points at in a repository.

    Parameters
    ----------
    folder : Path
        The repository: your clone or the stand-in GitHub.
    ref : str
        The branch's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such branch (or no repository).
    """
    return kit.git_run(folder, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def watch_push(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a plain ``git push`` worked.

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
    pushed = kit.typed(typed, PLAIN_PUSH, "ok")
    return kit.Verdict(pushed, PUSHED_MAIN if pushed else NOT_PUSHED)


def watch_send(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``scout`` is your ``scout``, and its ``main`` is as setup left it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the mothership's ``main``.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; lost once the mothership's ``main`` moved.
    """
    mine = _tip(lab.project, f"refs/heads/{BRANCH}")
    theirs = _tip(lab.github, f"refs/heads/{BRANCH}")
    moved = _tip(lab.github, "refs/heads/main") != state["main"]
    message = SENT
    if moved:
        message = MAIN_MOVED
    elif not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    elif not theirs:
        message = NOT_SENT
    elif theirs != mine:
        message = BEHIND
    return kit.Verdict(message == SENT, message, lost=moved)


def watch_list(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git branch -r`` (or ``-a``) worked after the last push that worked.

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
        The step's verdict; the mothership's ``scout`` comes first.
    """
    sent = watch_send(lab, state, typed)
    listed = kit.typed(kit.after(typed, SEND), LIST, "ok")
    verdict = kit.Verdict(listed, LISTED if listed else NOT_LISTED)
    return verdict if sent.solved else sent


QUEST: list[kit.Step] = [
    kit.WatchStep(id="push", text="Push from `main`, as in the last chapter.", command="git push", watch=watch_push),
    kit.WatchStep(id="send", text="Send `scout` to the mothership, by name.", command=f"git push -u origin {BRANCH}", watch=watch_send),
    kit.WatchStep(id="list", text="List the remote's branches.", command="git branch -r", watch=watch_list),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground, and a branch ``scout`` with two commits of a survey in your clone.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``main``: the mothership's ``main``, which must not change.
    """
    kit.setup_playground(lab)
    kit.git(lab.project, "switch", "-q", "-c", BRANCH)
    for day, (message, text) in enumerate(SURVEYS, start=1):
        (lab.project / SURVEY).write_text(text)
        kit.git(lab.project, "add", SURVEY)
        kit.git(lab.project, "commit", "-q", "-m", message, author=kit.PLAYER, when=f"2026-06-0{day}T09:00:00+00:00")
    kit.git(lab.project, "switch", "-q", "main")
    return {"main": _tip(lab.github, "refs/heads/main")}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once ``scout`` is on the mothership and the remote's branches were listed.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the repositories and what was typed.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The last goal's verdict.
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
        None: the level reads the repositories and what was typed.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "push": kit.typing("git push"),
    "send": kit.typing(f"git push -u origin {BRANCH}"),
    "list": kit.typing("git branch -r"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
