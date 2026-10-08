"""
Two experiments: two branches off one commit make the chain fork, and ``git switch`` moves between them with the folder following.

Name tags 5-3 (docs/drafts/sector5/5-3-script.md), guided, with a prediction. Setup rebuilds the
story to 5-2's end with ``bright-lights`` made yesterday and ``engine.txt`` waiting in the folder,
on ``main`` (`_names_story.experiments`). The goals: ``quiet-engine`` made on ``main``'s commit;
HEAD on it; ``engine.txt`` committed there, so the chain forks; HEAD on ``bright-lights``, where
the folder swaps the two files; and the tree drawn with ``git log --oneline --graph --all``. A
commit that moves ``main`` is lost: the captain wanted ``main`` left as it is.
"""

from collections.abc import Callable

from firstcommit import kit
from firstcommit.levels import _names_story as story

TITLE = "Two experiments"
DIFFICULTY = 2
XP = 150
COMMAND = "git switch"
PAR = 6
PICTURES = kit.pictures("chain", folder=True, graph=True)
CARD = kit.CommandCard(
    command="git switch <branch>",
    text="Moves `HEAD` onto another branch, and your folder changes to show that branch's commit.",
)
SCENE = [
    kit.SceneFrame(
        art="fork",
        text="Yesterday's experiment is the side line on the right: `bright-lights` and its commit, Try bright lights, joined to Fix the route. You are back on `main`. The row under the chain is your working folder: `engine.txt` is waiting there, not in Git yet.",
    ),
]

QUIET = "quiet-engine"
BRIGHT = "bright-lights"
ENGINE = "engine.txt"
LIGHTS = "lights.txt"
GRAPH = r"git log\b(?=.* --graph\b)(?=.* --all\b)"
OLDER_FORM = r"git checkout (?!-)\S+( |$)"

BRIEFING = """
Yesterday you started one experiment, `bright-lights`, on its own branch, and came back to `main`.
Today the captain wants a second one, `quiet-engine`, tried beside it; `engine.txt` is already
written and waiting in your folder. `main` stays as it is.

The mission is done when `quiet-engine` holds a commit with `engine.txt`, you are on
`bright-lights`, and you have drawn the tree.
"""

HINTS = [
    "`git branch <name>` makes a name where you are; `git switch <name>` moves `HEAD` onto it.",
    "`git add engine.txt`, then `git commit -m`, while on `quiet-engine`.",
    'Every line of the mission, in order:\n\n    $ git branch quiet-engine\n    $ git switch quiet-engine\n    $ git add engine.txt\n    $ git commit -m "Try a quiet engine"\n    $ git switch bright-lights\n    $ git log --oneline --graph --all',
]

DEBRIEF = """
Two branches made from the same commit made the chain fork. `git switch` moved `HEAD` from one
experiment to the other, and each time your folder changed to show that branch's commit. A commit
moves only the name `HEAD` is on, so `main` never moved.

`git log --oneline --graph --all` draws the whole tree in the terminal, every branch included.

Commands to keep:

    $ git switch bright-lights            # move HEAD to another branch
    $ git log --oneline --graph --all     # the whole tree, drawn
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_NAMED = "Put a name on `main`'s commit: `git branch quiet-engine`."
NAMED = "A second name on `main`'s commit. `HEAD` is still on `main`."
NOT_ON_QUIET = "Go there: `git switch quiet-engine`."
ON_QUIET = "`HEAD` moved to `quiet-engine`. Your folder did not change: both names are on the same commit, and `engine.txt` is not in Git yet, so a switch leaves it alone."
NOT_COMMITTED = 'Commit `engine.txt` on `quiet-engine`: `git add engine.txt`, then `git commit -m "Try a quiet engine"`.'
COMMITTED = "`quiet-engine` moved up to the new commit, and `main` stayed. Two side lines off the same commit: the chain forks, like a tree. Each experiment has its own name and its own commit."
MAIN_MOVED = "`main` moved, and the captain wanted it left as it is. Start the mission again to try again."
NOT_ON_BRIGHT = "Switch to the other experiment: `git switch bright-lights`."
ON_BRIGHT = "`HEAD` jumped across the tree to the other experiment, and the folder followed: `lights.txt` in, `engine.txt` out."
DRAWN = (
    "The same tree, drawn by git in the terminal. Each `*` is a commit, and `|` and `/` are the lines between them. "
    "`--all` shows every branch, not just the line you are on. Your two experiments are lit in both pictures."
)
NOT_DRAWN = "Draw the tree: `git log --oneline --graph --all`."
OLDER_FORM_WORKS = "That works too: `git checkout <name>` is the older form of `git switch <name>`."

REACTIONS = [
    kit.ReactionRule(line=OLDER_FORM, mood="info", text=OLDER_FORM_WORKS, outcome="ok"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You switch to `bright-lights`. Is `engine.txt` still in your folder?",
    options=("Yes", "No"),
    reveal="No. The folder shows `bright-lights`' commit: `lights.txt` comes back and `engine.txt` goes. Both files are safe in their commits.",
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


def _main_moved(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Tell whether ``main`` moved off the commit it started on.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: ``main``'s commit at the start.

    Returns
    -------
    kit.Verdict
        Lost when ``main`` moved; else not solved, with no message.
    """
    moved = _tip(lab, "refs/heads/main") not in ("", state["main"])
    return kit.Verdict(False, MAIN_MOVED if moved else "", lost=moved)


def watch_named(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``quiet-engine`` exists, made on ``main``'s commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: ``main``'s commit.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    at = _tip(lab, f"refs/heads/{QUIET}")
    named = at != "" and kit.is_ancestor(lab.project, state["main"], at)
    message = NAMED if named else NOT_NAMED
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == NAMED, message)


def watch_on_quiet(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once HEAD is on ``quiet-engine``.

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
    named = watch_named(lab, state, typed)
    on = kit.snapshot(lab.project)["branch"] == QUIET
    verdict = kit.Verdict(on, ON_QUIET if on else NOT_ON_QUIET)
    return verdict if named.solved else named


def _committed(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Tell whether ``quiet-engine`` holds ``engine.txt`` in a commit, wherever HEAD is; lost once ``main`` moved.

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
    moved = _main_moved(lab, state)
    named = watch_named(lab, state, typed)
    committed = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"refs/heads/{QUIET}:{ENGINE}").returncode == 0
    verdict = kit.Verdict(committed, COMMITTED if committed else NOT_COMMITTED)
    if not named.solved:
        verdict = named
    return moved if moved.lost else verdict


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``engine.txt`` is committed on ``quiet-engine``; lost once ``main`` moved.

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
    return _committed(lab, state, typed)


def watch_on_bright(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once HEAD is on ``bright-lights``, after the commit on ``quiet-engine``.

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
    on = kit.snapshot(lab.project)["branch"] == BRIGHT
    verdict = kit.Verdict(on, ON_BRIGHT if on else NOT_ON_BRIGHT)
    return verdict if committed.solved else committed


def watch_graph(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the tree was drawn after the switch to ``bright-lights``.

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
        The step's verdict; HEAD on ``bright-lights`` comes first.
    """
    on = watch_on_bright(lab, state, typed)
    drawn = kit.typed(kit.after(typed, kit.switching(BRIGHT)), GRAPH, "ok")
    verdict = kit.Verdict(drawn, DRAWN if drawn else NOT_DRAWN)
    return verdict if on.solved else on


QUEST: list[kit.Step] = [
    kit.WatchStep(id="branch", text="Put a name on `main`'s commit.", command=f"git branch {QUIET}", watch=watch_named),
    kit.WatchStep(id="switch", text="Go there.", command=f"git switch {QUIET}", watch=watch_on_quiet),
    kit.WatchStep(id="commit", text="Commit `engine.txt` there.", command=f'git add {ENGINE} && git commit -m "Try a quiet engine"', watch=watch_commit),
    GUESS,
    kit.WatchStep(id="bright", text="Switch to the other experiment.", command=f"git switch {BRIGHT}", watch=watch_on_bright),
    kit.WatchStep(
        id="graph",
        text="Draw the tree.",
        command="git log --oneline --graph --all",
        watch=watch_graph,
        look=("Try a quiet engine", "Try bright lights"),
    ),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Rebuild the story to 5-2's end, with ``bright-lights`` made yesterday and ``engine.txt`` waiting.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``main``: its commit, which must not move.
    """
    story.experiments(lab)
    return {"main": kit.git(lab.project, "rev-parse", "main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the tree was drawn on ``bright-lights``; lost once ``main`` moved.

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
    moved = _main_moved(lab, state)
    return moved if moved.lost else watch_graph(lab, state, typed)


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
    "branch": kit.typing(f"git branch {QUIET}"),
    "switch": kit.typing(f"git switch {QUIET}"),
    "commit": kit.typing(f'git add {ENGINE} && git commit -m "Try a quiet engine"'),
    "guess": kit.picking(GUESS.options[0]),
    "bright": kit.typing(f"git switch {BRIGHT}"),
    "graph": kit.typing("git log --oneline --graph --all"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
