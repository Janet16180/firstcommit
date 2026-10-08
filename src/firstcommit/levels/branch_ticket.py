"""
Your first ticket: the boss of the branch chapter. A fix goes up on its own branch, and ``main`` is left to the team.

Wave 2, branch 5-4 (docs/drafts/chapters-3-7.md), a challenge combining the vault (commit), the
mothership (push, pull) and this chapter (a branch made with your edit in hand, pushed by name).
Setup builds the playground with the base's lights settings on ``main``, and leaves your fix to
them uncommitted in your clone. Alex's push to ``main`` is a level event, run after the page's
first look. The goals are end states, met in any order: the mothership has ``fix-lights`` with
your fix, and its ``main`` holds no commit of yours; your ``main`` is the mothership's, Alex's
commit included. The fix gone from every place, a commit of yours on either ``main``, or Alex's
commit dropped by a forced push, is lost for this play.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Your first ticket"
DIFFICULTY = 3
XP = 250
COMMAND = "branch, commit, push"
PAR = 5
CHALLENGE = True
CARD = kit.CommandCard(
    command="git switch -c <branch>",
    text="Makes a new branch on the commit you are on and moves you onto it. Changes you have not committed come with you.",
)
SCENE = [
    kit.SceneFrame(art="alarm", text="Your first ticket: the hall lights are off. You already found the fix."),
    kit.SceneFrame(art="alarm", text="The crew's rule: nobody commits on `main`. Fixes go up on their own branch, for review."),
]

LIGHTS = "lights.cfg"
BROKEN = "deck=dim\nhall=off\n"
FIXED = "deck=dim\nhall=on\n"
BRANCH = "fix-lights"
ROBIN = kit.Person("Robin Park", "robin@example.com")
FORCE = r"git push\b.*( -f\b| --force\b| --force-with-lease\b| \+)"

BRIEFING = """
Your first ticket: the hall lights are off. You found the fix, and `lights.cfg` in your working
folder already has it, in no commit yet. The crew never commits on `main`: a fix goes up on its own
branch for review. Alex is working too.

The mission is done when the mothership has a branch `fix-lights` holding your fix and its `main`
holds no commit of yours, and your `main` is the same as the mothership's.
"""

HINTS = [
    "This is the vault, the mothership and this chapter: a commit, a push and a pull, and a branch of your own.",
    "Your edit is on no branch yet: a new branch made now takes it along. Commit it there, send that branch by name, then bring your `main` up to the mothership's.",
]

DEBRIEF = """
`git switch -c fix-lights` made the branch and took your uncommitted edit along: changes you have
not committed belong to no branch. You committed the fix there and pushed `fix-lights` by name,
so the team can review it, while the mothership's `main` kept only the team's work. Then, back on
`main`, a pull brought Alex's commit in.

That is your first day at work: a branch per ticket, pushed by name, and `main` pulled, never
committed on.

Commands to keep:

    $ git switch -c fix-lights          # a new branch; your edits come along
    $ git commit -am "Fix the hall lights"
    $ git push -u origin fix-lights     # send the ticket's branch for review
    $ git switch main && git pull       # and keep main up to date
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
FIX_LOST = "Your fix to `lights.cfg` is in no commit and no longer in the working folder: it is gone. Start the mission again."
MAIN_TOUCHED = "The mothership's `main` holds a commit of yours: the fix skipped review. Taking a commit back comes in a later chapter: start the mission again."
ALEX_DROPPED = "The mothership's `main` no longer holds Alex's commit: a forced push replaced it. Start the mission again."
MINE_ON_MAIN = "Your `main` holds a commit of yours, and the crew never commits on `main`. Moving a commit off a branch comes in a later chapter: start the mission again."
WAITING = "Alex is still on the way. Wait a moment."
UP_FOR_REVIEW = "The mothership has `fix-lights` with your fix, and its `main` holds none of your commits."
NOT_UP = "The mothership has no `fix-lights` holding your fix yet."
LEVEL = "Your `main` is the mothership's, Alex's commit included."
NOT_LEVEL = "Your `main` is not the same as the mothership's yet."
FORCED = "`--force` replaced a branch on the mothership with yours. On a team, that can erase someone's work."

REACTIONS = [
    kit.ReactionRule(line=FORCE, mood="err", text=FORCED, outcome="ok"),
]


def alex_pushes(lab: kit.Lab, state: kit.State) -> None:
    """
    Have Alex add a line to the notes, commit it and push it to ``main``, with the playground's buttons.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    for button in ("edit:notes.txt", "add:notes.txt", "commit", "push"):
        kit.press(lab, "alex", button)


EVENTS = [kit.LevelEvent(id="alex-pushes", run=alex_pushes)]


def _tip(folder: Path, ref: str) -> str:
    """
    Give the commit a branch points at in a repository.

    Parameters
    ----------
    folder : Path
        The repository: your clone, Alex's or the stand-in GitHub.
    ref : str
        The branch's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such branch (or no repository).
    """
    return kit.git_run(folder, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def _alex(lab: kit.Lab, state: kit.State) -> str:
    """
    Give Alex's commit once Alex has made it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the mothership's ``main`` at setup.

    Returns
    -------
    str
        The tip of Alex's ``main`` once it moved past setup's, else empty.
    """
    tip = _tip(lab.teammate, "refs/heads/main")
    return tip if tip != state["start"] else ""


def _added(folder: Path, ref: str, known: list[str]) -> bool:
    """
    Tell whether a branch holds a commit that none of the known commits leads to.

    Parameters
    ----------
    folder : Path
        The repository.
    ref : str
        The branch's full name; a missing branch holds nothing.
    known : list[str]
        The commits that are not yours: setup's ``main``, and Alex's once made.

    Returns
    -------
    bool
        True when ``git rev-list <ref> --not <known>`` lists a commit; a known commit this
        repository has not fetched leads nowhere here.
    """
    tip = _tip(folder, ref)
    return bool(tip) and bool(kit.git_run(folder, "rev-list", "--ignore-missing", tip, "--not", *known).stdout.strip())


def _dropped(lab: kit.Lab, alex: str) -> bool:
    """
    Tell whether the mothership's ``main`` lost Alex's commit after Alex pushed it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    alex : str
        Alex's commit, or empty before Alex made it.

    Returns
    -------
    bool
        True when the mothership had it (its reflog says so) and its ``main`` no longer leads to it.
    """
    pushed = bool(alex) and alex in kit.git_run(lab.github, "reflog", "--format=%H", "main").stdout.split()
    return pushed and not kit.is_ancestor(lab.github, alex, "refs/heads/main")


def _fix_kept(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether your fix is still somewhere: the working folder, the staging area or a commit a ref reaches.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the fixed file's blob id.

    Returns
    -------
    bool
        True while the fix can still be committed or is already in a commit, here or on the mothership.
    """
    entries = [entry for entry in kit.snapshot(lab.project)["files"] if entry["path"] == LIGHTS]
    in_areas = any(state["fix"] in (entry["folder"], entry["index"]) for entry in entries)
    objects = [kit.git_run(folder, "rev-list", "--all", "--objects").stdout for folder in (lab.project, lab.github)]
    return in_areas or any(line.startswith(state["fix"]) for listing in objects for line in listing.splitlines())


def _lost(lab: kit.Lab, state: kit.State) -> str:
    """
    Say what was lost for good, if anything.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.

    Returns
    -------
    str
        The message for the loss, or empty.
    """
    alex = _alex(lab, state)
    known = [state["start"], *([alex] if alex else [])]
    message = ""
    if not _fix_kept(lab, state):
        message = FIX_LOST
    elif _added(lab.github, "refs/heads/main", known):
        message = MAIN_TOUCHED
    elif _dropped(lab, alex):
        message = ALEX_DROPPED
    elif _added(lab.project, "refs/heads/main", known):
        message = MINE_ON_MAIN
    return message


def watch_review(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``fix-lights`` holds your fix, and its ``main`` none of your commits.

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
        The goal's verdict; lost as `_lost` says.
    """
    lost = _lost(lab, state)
    sent = kit.git_run(lab.github, "rev-parse", "-q", "--verify", f"refs/heads/{BRANCH}:{LIGHTS}").stdout.strip() == state["fix"]
    message = UP_FOR_REVIEW if sent else NOT_UP
    if lost:
        message = lost
    return kit.Verdict(message == UP_FOR_REVIEW, message, lost=bool(lost))


def watch_level(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` is the mothership's, with Alex's commit.

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
        The goal's verdict; lost as `_lost` says.
    """
    lost = _lost(lab, state)
    alex = _alex(lab, state)
    mine = _tip(lab.project, "refs/heads/main")
    level = bool(alex) and mine == _tip(lab.github, "refs/heads/main") and kit.is_ancestor(lab.project, alex, mine)
    message = LEVEL if level else NOT_LEVEL
    if lost:
        message = lost
    elif not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    elif not alex:
        message = WAITING
    return kit.Verdict(message == LEVEL, message, lost=bool(lost))


QUEST: list[kit.Step] = [
    kit.WatchStep(id="review", text="The mothership has `fix-lights` holding your fix, and its `main` holds no commit of yours.", watch=watch_review),
    kit.WatchStep(id="level", text="Your `main` is the same as the mothership's.", watch=watch_level),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground with the lights settings on ``main``, and leave your fix to them uncommitted.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``start``: the mothership's ``main``; ``fix``: the blob id of the fixed ``lights.cfg``.
    """
    kit.setup_playground(lab)
    (lab.project / LIGHTS).write_text(BROKEN)
    kit.git(lab.project, "add", LIGHTS)
    kit.git(lab.project, "commit", "-q", "-m", "Add the lights settings", author=ROBIN, when="2026-06-01T09:00:00+00:00")
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    (lab.project / LIGHTS).write_text(FIXED)
    return {"start": _tip(lab.github, "refs/heads/main"), "fix": kit.git(lab.project, "hash-object", LIGHTS).strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once every goal holds; else the first that does not, lost ones first.

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
    Play the boss like a player, after Alex's push: every goal's action, in order (AUTHORING section 3.6).

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
    "review": kit.typing(f'git switch -c {BRANCH} && git commit -am "Fix the hall lights" && git push -u origin {BRANCH}'),
    "level": kit.typing("git switch main && git pull"),
}
"""The player's part of each goal, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
