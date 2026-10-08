"""
New recruit: clone the outpost's repository and see that the clone holds its whole history.

Wave 2, branch 5-1 (docs/drafts/chapters-3-7.md), guided, with a counted answer. Setup gives the
stand-in GitHub a history of five to eight commits by three people, a number drawn at random so
it cannot be remembered, and no project folder: the terminal opens in the lab, next to
``github``. The goals: a clone in ``project`` whose ``origin`` is the outpost; its history listed
with ``git log`` (looking is the lesson); the number of its commits, typed; and its branches,
listed with ``git branch -a``, where ``main`` and ``origin/main`` show as two labels.
"""

import random
from collections.abc import Callable

from firstcommit import kit

TITLE = "New recruit"
DIFFICULTY = 1
XP = 100
COMMAND = "git clone"
PAR = 3
VIEW = "history"
CARD = kit.CommandCard(
    command="git clone <address>",
    text="Copies a repository into a new folder named after it: its whole history, a remote named `origin` for the address, and a branch such as `main` to work on.",
)
SCENE = [
    kit.SceneFrame(art="orbit", text="Outpost 3 is calling a new recruit: you. Its repository waits on the mothership."),
    kit.SceneFrame(art="chain", text="A clone copies the whole chain of capsules down, not only the latest files."),
]

PEOPLE = [kit.Person("Robin Park", "robin@example.com"), kit.Person("Alex", "alex@example.com"), kit.Person("Sam Ortiz", "sam@example.com")]
HISTORY = [
    ("Found the outpost", "outpost.txt", "Outpost 3: one dome\n"),
    ("Add the crew list", "crew.txt", "Robin\n"),
    ("Add the supply route", "route.txt", "Route: Earth, Moon\n"),
    ("Add Alex to the crew", "crew.txt", "Robin\nAlex\n"),
    ("Build a second dome", "outpost.txt", "Outpost 3: two domes\n"),
    ("Extend the route to Mars", "route.txt", "Route: Earth, Moon, Mars\n"),
    ("Add Sam to the crew", "crew.txt", "Robin\nAlex\nSam\n"),
    ("Add a landing pad", "outpost.txt", "Outpost 3: two domes and a landing pad\n"),
]
"""The outpost's history, oldest first: each commit's message, and the file it writes with its content."""
FEWEST = 5
CLONE = r"git clone\b"
LOG = r"(cd project && )?git log\b"
BRANCHES = r"(cd project && )?git branch( -a| --all| -r| --remotes)\b"

BRIEFING = """
You join Outpost 3 today. Its repository is on the mothership, at `github.com/moonbase/project.git` from the
folder your terminal opens in. Get your own copy, and find out how much of the outpost's history
came with it.

The mission is done when `project` is your clone of the outpost, you have read its history and
counted its commits, and you have listed its branches with `git branch -a`.
"""

HINTS = [
    "`git clone` takes the address and makes a folder named after it: `git clone github.com/moonbase/project.git` makes `project`.",
    "Go into the clone first: `cd project && git log --oneline` prints one line per commit.",
    "`git branch -a` lists your branches and the remote's, such as `remotes/origin/main`.",
    "Every line, in order; the answer is the number of lines the log prints:\n\n    $ git clone github.com/moonbase/project.git\n    $ cd project && git log --oneline\n    $ git branch -a",
]

DEBRIEF = """
`git clone` copied the outpost's whole history into `project`: every commit, not only the latest
files. It named the address `origin`, and made your own branch `main` on the commit the outpost's
`main` was on.

`git log --oneline` showed both labels on the newest commit: `main` is your branch, and
`origin/main` is your repository's record of where the mothership's `main` was when you last
heard from it. A branch is a label on a commit; the next mission makes one of your own.

At work, the first thing you do on a team is clone its repository, with the address GitHub shows.

Commands to keep:

    $ git clone github.com/moonbase/project.git   # copy a repository and its whole history
    $ git log --oneline                           # one line per commit, with its labels
    $ git branch -a                               # your branches, and the remote's
"""

NOT_CLONED = "There is no clone in `project` yet. Copy the outpost: `git clone github.com/moonbase/project.git`."
NOT_A_CLONE = "`project` is not a clone of the outpost: its `origin` is not `github.com/moonbase/project.git`. Leave the level and start it again."
CLONED = "`project` is your clone of the outpost."
READ = "That is the outpost's whole history, newest commit first, with the labels on it."
NOT_READ = "Read your clone's history: `cd project && git log --oneline`."
RIGHT_COUNT = "Right: your clone holds every commit the outpost has, not only its latest files."
WRONG_COUNT = "That is not how many commits your clone holds. `git log --oneline` prints one line per commit: count them."
NOT_A_NUMBER = "Type the number of commits, such as 3."
LISTED = "`main` is your branch; `remotes/origin/main` is where the mothership's `main` was when you cloned."
NOT_LISTED = "List the branches, the remote's too: `git branch -a`."
NOT_CLONED_YET = "There is no repository here yet. Clone the outpost first: `git clone github.com/moonbase/project.git`."
OUTSIDE_THE_CLONE = "Your terminal is not in the clone yet: it is in the folder that holds it. Go into it: `cd project`."

REACTIONS = [
    kit.ReactionRule(line=r"git (?!clone\b)", mood="info", text=NOT_CLONED_YET, outcome="failed", repository=False),
    kit.ReactionRule(line=r"git (log|status|branch)\b", mood="info", text=OUTSIDE_THE_CLONE, outcome="failed", repository=True),
]


def _is_clone(lab: kit.Lab) -> bool:
    """
    Tell whether ``project`` is a repository whose ``origin`` is the lab's GitHub.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    bool
        True when ``origin``'s address, read from the clone's top folder, is the lab's GitHub.
    """
    exists = kit.snapshot(lab.project)["exists"]
    url = kit.git_run(lab.project, "remote", "get-url", "origin").stdout.strip() if exists else ""
    return kit.reaches_github(lab, lab.project, url)


def watch_clone(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``project`` is a clone of the lab's GitHub.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    message = CLONED
    if not lab.project.is_dir():
        message = NOT_CLONED
    elif not _is_clone(lab):
        message = NOT_A_CLONE
    return kit.Verdict(message == CLONED, message)


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked after the clone.

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
        The step's verdict; the clone comes first.
    """
    cloned = watch_clone(lab, state, typed)
    read = kit.typed(kit.after(typed, CLONE), LOG, "ok")
    verdict = kit.Verdict(read, READ if read else NOT_READ)
    return verdict if cloned.solved else cloned


def counts_the_commits(lab: kit.Lab, state: kit.State, answer: str) -> kit.Verdict:
    """
    Pass for the number of commits the outpost's history holds.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused: the number is in the state).
    state : kit.State
        The level's state: the number's digest.
    answer : str
        What the player typed.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    number = kit.parse_int(answer)
    message = NOT_A_NUMBER
    if number is not None:
        message = RIGHT_COUNT if kit.answer_is(str(number), state["count"]) else WRONG_COUNT
    return kit.Verdict(message == RIGHT_COUNT, message)


def watch_branches(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git branch -a`` (or ``-r``) worked after the clone.

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
        The step's verdict; the clone comes first.
    """
    cloned = watch_clone(lab, state, typed)
    listed = kit.typed(kit.after(typed, CLONE), BRANCHES, "ok")
    verdict = kit.Verdict(listed, LISTED if listed else NOT_LISTED)
    return verdict if cloned.solved else cloned


QUEST: list[kit.Step] = [
    kit.WatchStep(id="clone", text="Clone the outpost's repository.", command="git clone github.com/moonbase/project.git", watch=watch_clone),
    kit.WatchStep(id="log", text="Go into your clone and read its history.", command="cd project && git log --oneline", watch=watch_log),
    kit.AnswerStep(id="count", text="Count the commits that came with the clone.", question="How many commits does your clone hold?", placeholder="a number", check=counts_the_commits),
    kit.WatchStep(id="branches", text="List the branches, the remote's too.", command="git branch -a", watch=watch_branches),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Give the stand-in GitHub a history of five to eight commits by three people, and leave no project folder.

    Each commit is written straight into GitHub with git's plumbing (``hash-object``, ``mktree``,
    ``commit-tree``), as `kit.setup_playground` writes its first one.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``count``: the digest of the number of commits.
    """
    commits = random.Random().randint(FEWEST, len(HISTORY))
    kit.setup_github(lab)
    blobs: dict[str, str] = {}
    parent: list[str] = []
    for day, (message, name, text) in enumerate(HISTORY[:commits], start=1):
        blobs[name] = kit.git(lab.github, "hash-object", "-w", "--stdin", stdin=text).strip()
        tree = kit.git(lab.github, "mktree", stdin="".join(f"100644 blob {blob}\t{path}\n" for path, blob in sorted(blobs.items()))).strip()
        when = f"2026-03-{day:02}T10:00:00+00:00"
        commit = kit.git(lab.github, "commit-tree", tree, *parent, "-m", message, author=PEOPLE[day % len(PEOPLE)], when=when).strip()
        parent = ["-p", commit]
    kit.git(lab.github, "update-ref", "refs/heads/main", commit)
    return {"count": kit.digest(str(commits))}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the clone is there and its branches were listed; the quest keeps the count before.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the clone and what was typed.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The last goal's verdict.
    """
    return watch_branches(lab, state, typed)


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
        None: the level reads the clone and what was typed.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


def clone(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git clone github.com/moonbase/project.git`` in the lab, where the terminal opens.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.root, "git clone github.com/moonbase/project.git"))
    return None


def read_history(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``cd project && git log --oneline`` in the lab, where the terminal still is.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.root, "cd project && git log --oneline"))
    return None


def count(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Count the lines ``git log --oneline`` prints in the clone.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far (unused).

    Returns
    -------
    str | None
        The number, as the player would type it.
    """
    return str(len(kit.git(lab.project, "log", "--oneline").splitlines()))


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "clone": clone,
    "log": read_history,
    "count": count,
    "branches": kit.typing("git branch -a"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
