"""
Two crews meet: a merge slides the label when it can, and otherwise joins two histories in a commit with two parents.

Wave 2, conflict 6-1 (docs/drafts/chapters-3-7.md), guided, with a prediction. Setup makes a
repository whose ``main`` has moved on since ``scout`` left it, and a branch ``beacon`` one
commit ahead of ``main``. The prediction breaks the myth that a merge always makes a commit. The
goals read the repository: ``beacon`` brought in by a fast-forward (``main`` on its commit, and
that commit on ``main``'s first-parent line); ``scout`` brought in by a merge commit with two
parents; and, read from the lines typed, ``git log --oneline --graph`` after that merge.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Two crews meet"
DIFFICULTY = 1
XP = 120
COMMAND = "git merge"
PAR = 3
CARD = kit.CommandCard(
    command="git merge <branch>",
    text="Brings a branch's commits into the branch you are on. When yours has nothing new, your label slides up; otherwise Git joins the two histories in a merge commit with two parents.",
)
SCENE = [
    kit.SceneFrame(art="merge", text="Two crews worked apart: one on the route, one on the crew list."),
    kit.SceneFrame(art="merge", text="A merge brings their histories together. Sometimes it only moves a label; sometimes it makes a capsule with two parents."),
]

BEACON = "beacon"
SCOUT = "scout"
BASE = {"route.txt": "Route: Earth, Moon\n", "crew.txt": "Robin\n"}
GRAPH = r"git log\b.*--graph\b"
MERGE = r"git (merge|pull)\b"

BRIEFING = """
Two crews worked apart. `beacon` added a beacon on top of `main`; `scout` added Alex to the crew
list while `main` extended the route. Bring both into `main`.

The mission is done when `main` holds `beacon` by a fast-forward, holds `scout` through a merge
commit, and you have looked at the history with `git log --oneline --graph`.
"""

HINTS = [
    "`git merge beacon` first: `main` has nothing `beacon` lacks, so its label only slides up.",
    "Then `git merge --no-edit scout`: both sides have new commits, so Git makes a merge commit and keeps its prepared message.",
    "`git log --oneline --graph` draws the two lines and where they join.",
]

DEBRIEF = """
`git merge beacon` made no commit: `main` had nothing `beacon` lacked, so Git only slid the `main`
label up to `beacon`'s commit. Git calls that a fast-forward.

`git merge --no-edit scout` was different: both sides had commits the other lacked, so Git made a
merge commit with two parents, one on each line, and kept both changes: the longer route and the
longer crew list. `--no-edit` keeps the message Git prepared; without it, Git opens an editor for
it on a terminal.

Commands to keep:

    $ git merge beacon               # nothing new on main: the label slides up
    $ git merge --no-edit scout      # both moved on: a merge commit with two parents
    $ git log --oneline --graph      # the history, with its lines drawn
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_FORWARDED = "`main` does not hold `beacon` yet. Bring it in: `git merge beacon`."
FORWARDED = "`main` slid up to `beacon`'s commit: no new commit."
MERGED_BEACON = "`beacon` came in through a merge commit, because `main` had already moved on. Start the mission again, and merge `beacon` first."
NOT_MERGED = "`main` does not hold `scout` yet. Bring it in: `git merge --no-edit scout`."
PAUSED = "A merge is paused. Finish it with `git commit --no-edit`, or step back with `git merge --abort`."
MERGED = "`main` holds `scout` through a merge commit with two parents: both crews' work is in it."
LOOKED = "The graph shows the two lines joining in the merge commit."
NOT_LOOKED = "Look at the history with its lines drawn: `git log --oneline --graph`."

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="`beacon` is one commit ahead of `main`, and `main` has nothing `beacon` lacks. How many new commits will `git merge beacon` make?",
    options=("None: the label slides up", "One merge commit"),
    reveal="None. When your branch has nothing new, `git merge` only slides your label up to the other branch's commit: a fast-forward.",
)


def _tip(lab: kit.Lab, ref: str) -> str:
    """
    Give the commit a branch points at.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    ref : str
        The branch's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such branch (or no repository).
    """
    return kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def watch_forward(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``beacon``'s commit is on ``main``'s first-parent line: it came in by a fast-forward.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: ``beacon``'s commit.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; lost once ``beacon`` came in through a merge commit.
    """
    exists = kit.snapshot(lab.project)["exists"]
    main = _tip(lab, "refs/heads/main")
    holds = bool(main) and kit.is_ancestor(lab.project, state["beacon"], main)
    first_line = kit.git_run(lab.project, "rev-list", "--first-parent", main).stdout.split() if main else []
    merged = holds and state["beacon"] not in first_line
    message = FORWARDED if holds else NOT_FORWARDED
    if not exists:
        message = NO_REPOSITORY
    elif merged:
        message = MERGED_BEACON
    return kit.Verdict(message == FORWARDED, message, lost=merged)


def watch_merge(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``main`` holds ``scout`` through a merge commit with two parents.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: ``scout``'s commit.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; the fast-forward comes first.
    """
    forward = watch_forward(lab, state, typed)
    main = _tip(lab, "refs/heads/main")
    parents = kit.git_run(lab.project, "rev-list", "--merges", "--parents", main).stdout.split("\n") if main else []
    joined = any(state["scout"] in line.split()[1:] for line in parents if line)
    message = MERGED if joined else NOT_MERGED
    if kit.snapshot(lab.project)["operation"] == "merge":
        message = PAUSED
    verdict = kit.Verdict(message == MERGED, message)
    return verdict if forward.solved else forward


def watch_graph(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git log --graph`` worked after the last merge.

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
        The step's verdict; the merge comes first.
    """
    merged = watch_merge(lab, state, typed)
    looked = kit.typed(kit.after(typed, MERGE), GRAPH, "ok")
    verdict = kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)
    return verdict if merged.solved else merged


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="forward", text="Bring `beacon` into `main`.", command=f"git merge {BEACON}", watch=watch_forward),
    kit.WatchStep(id="merge", text="Bring `scout` into `main`.", command=f"git merge --no-edit {SCOUT}", watch=watch_merge),
    kit.WatchStep(id="graph", text="Look at the history, with its lines drawn.", command="git log --oneline --graph", watch=watch_graph),
]


def _commit(lab: kit.Lab, name: str, text: str, message: str, day: int) -> str:
    """
    Write a file, stage it and commit it on the current branch.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    name : str
        The file.
    text : str
        Its new content.
    message : str
        The commit's message.
    day : int
        The day of May 2026 it is dated.

    Returns
    -------
    str
        The new commit's hash.
    """
    (lab.project / name).write_text(text)
    kit.git(lab.project, "add", name)
    kit.git(lab.project, "commit", "-q", "-m", message, author=kit.PLAYER, when=f"2026-05-{day:02}T09:00:00+00:00")
    return kit.git(lab.project, "rev-parse", "HEAD").strip()


def setup(lab: kit.Lab) -> kit.State:
    """
    Make ``main``, a ``scout`` that left it one commit ago, and a ``beacon`` one commit ahead of it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``beacon`` and ``scout``: their commits.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for name, text in BASE.items():
        (lab.project / name).write_text(text)
    kit.git(lab.project, "add", *BASE)
    kit.git(lab.project, "commit", "-q", "-m", "Set up the base", author=kit.PLAYER, when="2026-05-01T09:00:00+00:00")
    kit.git(lab.project, "switch", "-q", "-c", SCOUT)
    scout = _commit(lab, "crew.txt", "Robin\nAlex\n", "Add Alex to the crew", 2)
    kit.git(lab.project, "switch", "-q", "main")
    _commit(lab, "route.txt", "Route: Earth, Moon, Mars\n", "Extend the route to Mars", 3)
    kit.git(lab.project, "switch", "-q", "-c", BEACON)
    beacon = _commit(lab, "beacon.txt", "Beacon: on\n", "Light the beacon", 4)
    kit.git(lab.project, "switch", "-q", "main")
    return {"beacon": beacon, "scout": scout}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once both merges are in and the graph was drawn; lost once ``beacon`` came in by a merge commit.

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
        The last goal's verdict.
    """
    return watch_graph(lab, state, typed)


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
    return GUESS.options[1]


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "guess": guess,
    "forward": kit.typing(f"git merge {BEACON}"),
    "merge": kit.typing(f"git merge --no-edit {SCOUT}"),
    "graph": kit.typing("git log --oneline --graph"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
