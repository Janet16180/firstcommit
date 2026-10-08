"""
One step: ``git switch -c`` makes a name where you are and moves HEAD onto it; ``git checkout -b`` and ``git checkout`` are the older forms.

Name tags 5-4 (docs/drafts/sector5/5-4-script.md), guided, with a prediction. Setup rebuilds the
story to 5-3's end, back on ``main`` with ``dim.txt`` waiting in the folder
(`_names_story.one_step`). The goals: ``dim-lights`` made and moved onto in one step; ``dim.txt``
committed there, a third side line; the tree drawn with ``git log --oneline --graph --all``;
``quiet-engine`` reached and ``night-watch`` made the older ways (the newer ones count too, read
from the lines typed with `kit.switching` and `kit.creating`); and the branches listed.
"""

from collections.abc import Callable

from firstcommit import kit
from firstcommit.levels import _names_story as story

TITLE = "One step"
DIFFICULTY = 2
XP = 150
COMMAND = "git switch -c"
PAR = 7
VIEW = "history"
CARD = kit.CommandCard(
    command="git switch -c <name>",
    text="Makes a new branch on the commit you are on and moves `HEAD` onto it, in one step. `git checkout -b <name>` is the older form.",
)
SCENE = [
    kit.SceneFrame(
        art="fork",
        text="Last time, starting an experiment took two commands: `git branch quiet-engine`, then `git switch quiet-engine`. Today's command is `git switch -c dim-lights`. The `-c` means create.",
    ),
]

DIM = "dim-lights"
DIM_FILE = "dim.txt"
QUIET = "quiet-engine"
NIGHT = "night-watch"
GRAPH = r"git log\b(?=.* --graph\b)(?=.* --all\b)"
LIST = r"git branch( -v+| --verbose)+( |$)"

BRIEFING = """
A third experiment: dim lights, from `main`, where you are. `dim.txt` is already in your folder.
Rama has a shorter command to show you, and then the older ones you will see in tutorials and at
work.

The mission is done when `dim-lights` holds a commit with `dim.txt`, you have drawn the tree, you
have tried `git checkout` and `git checkout -b`, and you have listed your branches.
"""

HINTS = [
    "`git switch -c <name>` is `git branch <name>` and `git switch <name>` together.",
    "`git checkout <name>` does what `git switch <name>` does; `git checkout -b <name>` does what `git switch -c <name>` does.",
    'Every line of the mission, in order:\n\n    $ git switch -c dim-lights\n    $ git add dim.txt\n    $ git commit -m "Try dim lights"\n    $ git log --oneline --graph --all\n    $ git checkout quiet-engine\n    $ git checkout -b night-watch\n    $ git branch -v',
]

DEBRIEF = """
`git switch -c dim-lights` made the name where you were and moved `HEAD` onto it; your commit then
grew a third side line. `git checkout -b` and `git checkout` are the older forms of `git switch -c`
and `git switch`: they do the same, and the game accepts either.

`git checkout` is older and does many jobs, even restoring files, so Git added `git switch` for
just one job: moving between branches. Use `switch`; read `checkout` when you see it.

Commands to keep:

    $ git switch -c dim-lights      # a new branch, and go there
    $ git checkout -b dim-lights    # the same, older form
    $ git checkout main             # the same as git switch main
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_MADE = "Try the short command: `git switch -c dim-lights`."
MADE = '"A new branch", and you are on it, in one step.'
NOT_ON_DIM = "Commit on `dim-lights`: `git switch dim-lights` takes you back to it."
NOT_COMMITTED = 'Commit `dim.txt` on `dim-lights`: `git add dim.txt`, then `git commit -m "Try dim lights"`.'
COMMITTED = "A third side line off the same commit."
DIM_ON_MAIN = "`main` holds `dim.txt`: that commit went onto `main`. Start the mission again, and commit it on `dim-lights`."
DRAWN = (
    "Git's drawing grows a third line too. It draws the newest experiment first, and each side line closes with its own `|/`. "
    "Match it with the chain by name, not by place."
)
NOT_DRAWN = "Draw the tree: `git log --oneline --graph --all`."
OLDER_WAY = (
    "Same as `git switch quiet-engine`. You will also meet `git checkout` in tutorials and at work: it is older and does many "
    "jobs, even restoring files, so Git added `git switch` for just one, moving between branches. Use `switch`; read `checkout` when you see it."
)
NOT_OLDER_WAY = "Go to `quiet-engine`, the older way: `git checkout quiet-engine`."
NIGHT_MADE = "Same as `git switch -c night-watch`: a new name where you are, and you on it."
NOT_NIGHT = "The short command, the older way: `git checkout -b night-watch`, from `quiet-engine`."
NIGHT_ELSEWHERE = "`night-watch` is not on `quiet-engine`'s commit. Take it off with `git branch -D night-watch` from another branch, then make it again from `quiet-engine`."
LISTED = "Six names now. `night-watch` and `quiet-engine` name the same commit."
NOT_LISTED = "List your branches: `git branch -v`."

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You type `git switch -c dim-lights` while on `main`. Where is `HEAD` afterwards?",
    options=("On `main`", "On `dim-lights`", "On a new commit"),
    reveal="On `dim-lights`. Git makes the name `dim-lights` on the commit you are on, then moves `HEAD` onto it: both of last time's commands in one. No commit is made.",
)


def _tip(lab: kit.Lab, ref: str) -> str:
    """
    Give the commit a ref points at.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    ref : str
        The ref's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such ref.
    """
    return kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def _holds_dim(lab: kit.Lab, ref: str) -> bool:
    """
    Tell whether a branch's commit holds ``dim.txt``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    ref : str
        The branch's full name.

    Returns
    -------
    bool
        True when its tree has the file.
    """
    return kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{ref}:{DIM_FILE}").returncode == 0


def watch_made(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``dim-lights`` was made and moved onto in one step.

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
    made = bool(_tip(lab, f"refs/heads/{DIM}")) and kit.typed(typed, kit.creating(DIM), "ok")
    message = MADE if made else NOT_MADE
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == MADE, message)


def _committed(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Tell whether ``dim-lights`` holds ``dim.txt`` in a commit ``main`` lacks, wherever HEAD is.

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
        Passed once ``dim-lights`` holds it; lost once ``main`` holds it too.
    """
    made = watch_made(lab, state, typed)
    on_main = _holds_dim(lab, "refs/heads/main")
    message = COMMITTED if _holds_dim(lab, f"refs/heads/{DIM}") else NOT_COMMITTED
    if on_main:
        message = DIM_ON_MAIN
    verdict = kit.Verdict(message == COMMITTED, message, lost=on_main)
    return verdict if made.solved or on_main else made


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``dim.txt`` is committed on ``dim-lights``, with HEAD still there.

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
        The step's verdict.
    """
    committed = _committed(lab, state, typed)
    on_dim = kit.snapshot(lab.project)["branch"] == DIM
    return committed if not committed.solved or on_dim else kit.Verdict(False, NOT_ON_DIM)


def watch_graph(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the tree was drawn after the commit.

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
        The step's verdict; the commit comes first.
    """
    committed = _committed(lab, state, typed)
    drawn = kit.typed(kit.after(typed, r"git commit\b"), GRAPH, "ok")
    verdict = kit.Verdict(drawn, DRAWN if drawn else NOT_DRAWN)
    return verdict if committed.solved else committed


def watch_older_way(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a move onto ``quiet-engine`` worked after the tree was drawn.

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
        The step's verdict; the tree comes first.
    """
    drawn = watch_graph(lab, state, typed)
    moved = kit.typed(kit.after(typed, GRAPH), kit.switching(QUIET), "ok")
    verdict = kit.Verdict(moved, OLDER_WAY if moved else NOT_OLDER_WAY)
    return verdict if drawn.solved else drawn


def watch_night(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``night-watch`` was made in one step on ``quiet-engine``'s commit.

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
        The step's verdict; reaching ``quiet-engine`` comes first.
    """
    moved = watch_older_way(lab, state, typed)
    at = _tip(lab, f"refs/heads/{NIGHT}")
    message = NIGHT_MADE
    if not at or not kit.typed(kit.after(typed, kit.switching(QUIET)), kit.creating(NIGHT), "ok"):
        message = NOT_NIGHT
    elif at != _tip(lab, f"refs/heads/{QUIET}"):
        message = NIGHT_ELSEWHERE
    verdict = kit.Verdict(message == NIGHT_MADE, message)
    return verdict if moved.solved else moved


def watch_list(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the branches were listed after ``night-watch`` was made.

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
        The step's verdict; ``night-watch`` comes first.
    """
    night = watch_night(lab, state, typed)
    listed = kit.typed(kit.after(typed, kit.creating(NIGHT)), LIST, "ok")
    verdict = kit.Verdict(listed, LISTED if listed else NOT_LISTED)
    return verdict if night.solved else night


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="make", text="Try the short command.", command=f"git switch -c {DIM}", watch=watch_made),
    kit.WatchStep(id="commit", text="Commit `dim.txt`.", command=f'git add {DIM_FILE} && git commit -m "Try dim lights"', watch=watch_commit),
    kit.WatchStep(id="graph", text="Draw the tree.", command="git log --oneline --graph --all", watch=watch_graph),
    kit.WatchStep(id="checkout", text="Go to `quiet-engine`, the older way.", command=f"git checkout {QUIET}", watch=watch_older_way),
    kit.WatchStep(id="checkout-b", text="The short command, the older way.", command=f"git checkout -b {NIGHT}", watch=watch_night),
    kit.WatchStep(id="list", text="List your branches.", command="git branch -v", watch=watch_list),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Rebuild the story to 5-3's end, back on ``main`` with ``dim.txt`` in the folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the goals read the repository and what was typed.
    """
    story.one_step(lab)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the branches were listed after ``night-watch`` was made; lost once ``main`` holds ``dim.txt``.

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
    committed = _committed(lab, state, typed)
    return committed if committed.lost else watch_list(lab, state, typed)


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
    "guess": kit.picking(GUESS.options[2]),
    "make": kit.typing(f"git switch -c {DIM}"),
    "commit": kit.typing(f'git add {DIM_FILE} && git commit -m "Try dim lights"'),
    "graph": kit.typing("git log --oneline --graph --all"),
    "checkout": kit.typing(f"git checkout {QUIET}"),
    "checkout-b": kit.typing(f"git checkout -b {NIGHT}"),
    "list": kit.typing("git branch -v"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
