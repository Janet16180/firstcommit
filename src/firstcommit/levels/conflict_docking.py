"""
Docking collision: the boss of the collisions chapter. A refused push, a conflict, and Alex moves again.

Wave 2, conflict 6-4 (docs/drafts/chapters-3-7.md), a challenge combining the vault (commit), the
mothership (refused push, pull, push) and this chapter (a conflict answered). Setup builds the
playground with a docking plan: you committed bay 5, and Alex pushed bay 4 with the reason (bay 5
lost its clamps); your commit also holds a checklist, the work of yours that survives either
pull. The goals are end states, met in any order: your ``main`` holds Alex's commit and your
checklist, docking at bay 4 with no markers; and the mothership's ``main`` is yours. Once
the first is met, a level event has Alex push again, so the second needs one more pull. Alex's
commits dropped from the mothership by a forced push, or your checklist in no commit any more, are
lost for this play.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Docking collision"
DIFFICULTY = 3
XP = 300
COMMAND = "pull, answer, push"
PAR = 8
CHALLENGE = True
CARD = kit.CommandCard(
    command="git commit --no-edit",
    text="Commits with the message as Git prepared it, without asking for one: during a merge, the merge's own message. It finishes a merge once every conflict is added.",
)
SCENE = [
    kit.SceneFrame(art="alarm", text="On approach: you and Alex both rewrote the docking line, and Alex sent theirs first."),
    kit.SceneFrame(art="collision", text="Get both crews' work onto the mothership, with the bay that is safe."),
]

DOCKING = "docking.txt"
START = "Dock at bay 2\n"
MINE = "Dock at bay 5\n"
ALEXS = "Dock at bay 4\n"
MARKER = "<<<<<<<"
CHECKLIST = "checklist.txt"
CHECKS = "Approach checklist:\n- clamps\n- airlock seal\n"
ALEX = kit.Person("Alex", "alex@example.com")
FORCE = r"git push\b.*( -f\b| --force\b| --force-with-lease\b| \+)"

BRIEFING = """
On approach, you wrote the approach checklist and changed the docking plan to bay 5, in one commit.
Alex changed the same line to bay 4 and pushed first: bay 5 lost its clamps. Get both crews' work
onto the mothership, docking at the safe bay.

The mission is done when your `main` holds Alex's commit and your checklist, and `docking.txt`
there docks at bay 4 with no conflict markers, and the mothership's `main` is the same as yours.
"""

HINTS = [
    "This is the mothership and this chapter: a refused push, a pull, a conflict to answer, and a push.",
    "Your push is refused until your `main` holds Alex's commit. Pull, answer the conflict with Alex's bay, add, commit, and push; if Alex moved again, pull once more.",
    "Every line, in order; Alex pushes again after your merge, so the second push bounces and the next pull fixes it:\n\n    $ git push\n    $ git pull --no-rebase\n    $ git restore --theirs docking.txt\n    $ git add docking.txt\n    $ git commit --no-edit\n    $ git push\n    $ git pull --no-rebase --no-edit\n    $ git push",
]

DEBRIEF = """
Your push bounced: the mothership had Alex's commit. The pull stopped on the docking line, both
sides changed it, so you read the two, kept Alex's bay 4, added the file and finished the pull:
`git commit --no-edit` after a merge, `git rebase --continue` after a rebase. Your checklist came
along either way. By then Alex had pushed again, so your next push bounced too; one more pull
joined that commit without a conflict, and the push went through.

That is how a busy team works: pull, answer what Git asks, push, and pull again when someone was
quicker. Never `--force` a shared branch.
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
ALEX_DROPPED = "The mothership's `main` no longer holds Alex's work: a forced push replaced it. Start the mission again."
NOT_JOINED = "Your `main` does not hold Alex's commit and your checklist yet."
CHECKLIST_LOST = "Your checklist is in no commit any more: it is gone. Start the mission again."
PAUSED = "A merge is paused: answer the conflict, add the file and commit."
NOT_BAY_4 = "Your `main` holds Alex's commit and your checklist, but `docking.txt` there does not dock at bay 4 with no markers."
JOINED = "Your `main` holds Alex's commit and your checklist, and docks at bay 4."
NOT_SENT = "The mothership's `main` is not the same as yours yet."
SENT = "The mothership's `main` is yours."
FORCED = "`--force` replaced the mothership's `main` with yours. On a team, that erases someone's work."

REACTIONS = [
    kit.ReactionRule(line=FORCE, mood="err", text=FORCED, outcome="ok"),
]


def alex_again(lab: kit.Lab, state: kit.State) -> None:
    """
    Have Alex add a line to the notes, commit it and push it, with the playground's buttons.

    Alex pulls first, so the push goes through whatever you pushed before.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    for button in ("pull-no-rebase", "edit:notes.txt", "add:notes.txt", "commit", "push"):
        kit.press(lab, "alex", button)


EVENTS = [kit.LevelEvent(id="alex-again", run=alex_again, goal="joined")]


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


def _dropped(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether the mothership's ``main`` lost a commit of Alex's it once had.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: Alex's first commit.

    Returns
    -------
    bool
        True when Alex's first commit, or Alex's latest once the mothership's reflog shows it
        arrived, is no longer in the mothership's ``main``.
    """
    pushed = kit.git_run(lab.github, "reflog", "--format=%H", "main").stdout.split()
    latest = _tip(lab.teammate, "refs/heads/main")
    alex = [state["alex"], *([latest] if latest in pushed else [])]
    main = _tip(lab.github, "refs/heads/main")
    return not all(kit.is_ancestor(lab.github, commit, main) for commit in alex)


def _checklist_kept(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether your checklist is still in a commit a ref reaches, here or on the mothership, or in the working folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the checklist's blob id.

    Returns
    -------
    bool
        True while it can still reach ``main``.
    """
    entries = [entry for entry in kit.snapshot(lab.project)["files"] if entry["path"] == CHECKLIST]
    in_areas = any(state["checklist"] in (entry["folder"], entry["index"]) for entry in entries)
    objects = [kit.git_run(folder, "rev-list", "--all", "--objects").stdout for folder in (lab.project, lab.github)]
    return in_areas or any(line.startswith(state["checklist"]) for listing in objects for line in listing.splitlines())


def watch_joined(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds Alex's commit and your checklist, nothing is paused, and it docks at bay 4.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: Alex's commit and your checklist.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The goal's verdict; lost once Alex's work was forced off the mothership or your checklist is gone.
    """
    snap = kit.snapshot(lab.project)
    main = _tip(lab.project, "refs/heads/main")
    checklist = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{main}:{CHECKLIST}").stdout.strip() if main else ""
    both = bool(main) and kit.is_ancestor(lab.project, state["alex"], main) and checklist == state["checklist"]
    plan = kit.git_run(lab.project, "show", f"{main}:{DOCKING}").stdout if both else ""
    safe = plan.strip() == ALEXS.strip() and MARKER not in plan
    message = NOT_JOINED
    if both:
        message = JOINED if safe else NOT_BAY_4
    dropped = _dropped(lab, state)
    lost = not _checklist_kept(lab, state)
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif dropped:
        message = ALEX_DROPPED
    elif lost:
        message = CHECKLIST_LOST
    elif snap["operation"] is not None:
        message = PAUSED
    return kit.Verdict(message == JOINED, message, lost=dropped or lost)


def watch_sent(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``main`` is your ``main``.

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
        The goal's verdict; lost once Alex's work was forced off the mothership.
    """
    dropped = _dropped(lab, state)
    mine = _tip(lab.project, "refs/heads/main")
    sent = bool(mine) and mine == _tip(lab.github, "refs/heads/main")
    message = SENT if sent else NOT_SENT
    if dropped:
        message = ALEX_DROPPED
    return kit.Verdict(message == SENT, message, lost=dropped)


QUEST: list[kit.Step] = [
    kit.WatchStep(id="joined", text="Your `main` holds Alex's commit and your checklist, and `docking.txt` there docks at bay 4 with no markers.", watch=watch_joined),
    kit.WatchStep(id="sent", text="The mothership's `main` is the same as yours.", watch=watch_sent),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground with a docking plan; commit bay 5 and a checklist in your clone, and have Alex push bay 4.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``alex``: Alex's commit; ``checklist``: your checklist's blob id.
    """
    kit.setup_playground(lab)
    (lab.project / DOCKING).write_text(START)
    kit.git(lab.project, "add", DOCKING)
    kit.git(lab.project, "commit", "-q", "-m", "Write the docking plan", author=kit.PLAYER, when="2026-06-10T09:00:00+00:00")
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    (lab.teammate / DOCKING).write_text(ALEXS)
    kit.git(lab.teammate, "commit", "-q", "-am", "Bay 5 lost its clamps: dock at bay 4", author=ALEX, when="2026-06-11T08:00:00+00:00")
    kit.git(lab.teammate, "push", "-q")
    (lab.project / DOCKING).write_text(MINE)
    (lab.project / CHECKLIST).write_text(CHECKS)
    kit.git(lab.project, "add", DOCKING, CHECKLIST)
    kit.git(lab.project, "commit", "-q", "-m", "Write the approach checklist, dock at bay 5", author=kit.PLAYER, when="2026-06-11T09:00:00+00:00")
    return {"alex": _tip(lab.teammate, "refs/heads/main"), "checklist": kit.git(lab.project, "hash-object", CHECKLIST).strip()}


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
    Play the boss like a player: every goal's action, in order, with Alex's second push between them.

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
        for event in EVENTS:
            if event.goal == quest_step.id:
                event.run(lab, state)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "joined": kit.typing(f"git pull --no-rebase; git restore --theirs {DOCKING} && git add {DOCKING} && git commit --no-edit"),
    "sent": kit.typing("git pull --no-rebase --no-edit && git push"),
}
"""The player's part of each goal, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
