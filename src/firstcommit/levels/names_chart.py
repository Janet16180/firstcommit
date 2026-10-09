"""
Match the chart: make the names on a small forked tree stand where the captain's chart says, leaving every commit as it is.

Name tags 5-5 (docs/drafts/sector5/5-5-script.md), the sector's challenge. Setup rebuilds the story
to 5-3's end, a new day: 5-4's names cleared, and ``fuel-test`` on the fuel note with HEAD on it
(`_names_story.match_chart`). The one goal: every branch on the commit the chart gives it (matched
by subject, as the page's chart is), no branch the chart lacks, and HEAD on ``lights-v2``. Two
traps: ``git branch -d`` refuses the name HEAD is on, and a new name lands where HEAD is, so
``lights-v2`` made from ``main`` sits on the wrong side line. A new commit, or ``main`` moved, is
lost: the chart keeps every commit as it is.
"""

from collections.abc import Callable

from firstcommit import kit
from firstcommit.levels import _names_story as story

TITLE = "Match the chart"
DIFFICULTY = 3
XP = 200
COMMAND = "git branch"
PAR = 5
CHALLENGE = True
PICTURES = kit.pictures("chain")
TARGET: kit.Target = {
    "commits": [
        {"id": "start", "parents": [], "subject": "Start the project"},
        {"id": "route", "parents": ["start"], "subject": "Plot the route"},
        {"id": "crew", "parents": ["route"], "subject": "Add the crew list"},
        {"id": "fuel", "parents": ["crew"], "subject": story.FUEL_MESSAGE},
        {"id": "fix", "parents": ["fuel"], "subject": "Fix the route"},
        {"id": "bright", "parents": ["fix"], "subject": "Try bright lights"},
        {"id": "quiet", "parents": ["fix"], "subject": "Try a quiet engine"},
    ],
    "names": {
        "main": "fix",
        "release": "fix",
        story.FIRST_ROUTE: "route",
        "bright-lights": "bright",
        "lights-v2": "bright",
        "quiet-engine": "quiet",
    },
    "head": "lights-v2",
}
CARD = kit.CommandCard(
    command="git branch -d <name>",
    text="Takes a name off a commit; the commit stays. Git refuses to take off the name `HEAD` is on: move `HEAD` first.",
)
SCENE = [
    kit.SceneFrame(art="chain", text="Left: your chain. Right: the captain's chart. Make your names match."),
]

DELETE_FUEL_TEST = rf"git branch (-d|-D|--delete) {story.FUEL_TEST}( |$)"

BRIEFING = """
A new day. Overnight the captain kept your two experiments and cleared the other test names,
except one: you left `HEAD` on `fuel-test`. The chart shows how the names should stand for the
launch. Make your chain match it. The commits are already right, and so is your `origin/main`
bookmark: leave it.
"""

HINTS = [
    "Compare the two pictures one name at a time, `HEAD` included.",
    "`git branch <name>`, `git branch -d <name>`, `git switch <branch>` and `git switch -c <name>` are all you need. A new name lands where `HEAD` is.",
    "Every line of the mission, in order:\n\n    $ git switch main\n    $ git branch -d fuel-test\n    $ git branch release\n    $ git switch bright-lights\n    $ git switch -c lights-v2",
]

DEBRIEF = """
Not one commit changed: only names moved on the tree. You took `HEAD` off `fuel-test` before
removing it, put `release` where `HEAD` was, and crossed to the other side line before making
`lights-v2`, because a new name always lands where `HEAD` is.

Commands to keep:

    $ git switch main             # move HEAD off a name before taking it off
    $ git branch -d fuel-test     # take a name off
    $ git switch -c lights-v2     # a name where HEAD is, and go there
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
MATCHED = "Your names match the captain's chart, and git's drawing in the terminal agrees: `HEAD -> lights-v2` on the bright-lights experiment."
NOT_MATCHED = "Your names do not match the captain's chart yet."
WRONG_SIDE = "`lights-v2` is where `HEAD` was, on `main`'s commit. The chart wants it on *Try bright lights*: go to `bright-lights` first."
COMMITS_CHANGED = "The chart keeps every commit as it is. Start the mission again to try again."
USED_BY_WORKTREE = '"Used by worktree" means your folder is showing that branch: `HEAD` is on it. Git will not take off the name `HEAD` is on. Move `HEAD` first.'

REACTIONS = [
    kit.ReactionRule(line=DELETE_FUEL_TEST, mood="warn", text=USED_BY_WORKTREE, outcome="failed", branch=story.FUEL_TEST),
]


def _names(lab: kit.Lab) -> dict[str, str]:
    """
    Give each branch of your clone with its commit's subject.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    dict[str, str]
        The subject of each branch's commit, by branch.
    """
    lines = kit.git_run(lab.project, "for-each-ref", "--format=%(refname:short)%09%(subject)", "refs/heads").stdout.splitlines()
    return dict(line.split("\t", 1) for line in lines if "\t" in line)


def _wanted() -> dict[str, str]:
    """
    Give each name of the chart with the subject of the commit it should be on.

    Returns
    -------
    dict[str, str]
        The subject, by name.
    """
    subjects = {commit["id"]: commit["subject"] for commit in TARGET["commits"]}
    return {name: subjects[label] for name, label in TARGET["names"].items()}


def _commits_changed(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Tell whether a commit was made or ``main`` moved since the start.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the commits at the start and ``main``'s.

    Returns
    -------
    kit.Verdict
        Lost when either happened; else not solved, with no message.
    """
    commits = set(kit.git_run(lab.project, "rev-list", "--all").stdout.split())
    main = kit.git_run(lab.project, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    changed = bool(commits - set(state["commits"])) or main not in ("", state["main"])
    return kit.Verdict(False, COMMITS_CHANGED if changed else "", lost=changed)


def watch_chart(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once every name stands where the chart says, with no other name, and HEAD on the chart's.

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
        The goal's verdict; lost once a commit was made or ``main`` moved.
    """
    changed = _commits_changed(lab, state)
    names = _names(lab)
    matched = names == _wanted() and kit.snapshot(lab.project)["branch"] == TARGET["head"]
    message = MATCHED if matched else NOT_MATCHED
    if names.get("lights-v2") == "Fix the route":
        message = WRONG_SIDE
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    verdict = kit.Verdict(message == MATCHED, message)
    return changed if changed.lost else verdict


QUEST: list[kit.Step] = [
    kit.WatchStep(id="chart", text="Your names match the captain's chart.", watch=watch_chart),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Rebuild the story to 5-5's start.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``commits``: every commit at the start; ``main``: its commit.
    """
    story.match_chart(lab)
    return {"commits": kit.git(lab.project, "rev-list", "--all").split(), "main": kit.git(lab.project, "rev-parse", "main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the names match the chart; lost once a commit was made or ``main`` moved.

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
        The goal's verdict.
    """
    return watch_chart(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: the last hint's lines, in order (AUTHORING section 3.6).

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


def match(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type the lines that make the names match the chart.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : list[kit.Command]
        The lines typed so far; each line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    for line in ("git switch main", f"git branch -d {story.FUEL_TEST}", "git branch release", "git switch bright-lights", "git switch -c lights-v2"):
        kit.typing(line)(lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"chart": match}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
