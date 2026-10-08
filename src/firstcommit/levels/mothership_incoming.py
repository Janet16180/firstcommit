"""
Incoming transmission: ``git status`` knows the mothership only as of the last fetch.

Wave 1, mothership 4-3 (docs/drafts/chapters-3-7.md), a situation with a prediction. Setup builds
the playground (GitHub, your clone and Alex's). Alex's commit and push is a level event, run
after the page's first look, so the page animates the capsule docking at the mothership while
your ``origin/main`` stays where it was. The goals: look with ``git status`` (it still says up
to date), ``git fetch`` (``origin/main`` moves), ``git status`` again (now behind), then
``git pull`` (Alex's commit in your ``main``). Each goal reads the repository where it can and
the lines typed where looking is the lesson; a ``git pull`` first is a safe path, and the goals
it satisfies pass with it. Until Alex has pushed, nothing counts.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Incoming transmission"
DIFFICULTY = 2
XP = 150
COMMAND = "git fetch · git pull"
PAR = 4
VIEW = "crew"
CARD = kit.CommandCard(
    command="git fetch",
    text="Asks the remote what it holds now and updates `origin/main`, your repository's copy of its news. Your own `main` and your files stay as they are.",
)
SCENE = [
    kit.SceneFrame(art="pull", text="Alex, on the night shift, just sent a report to the remote (the mothership)."),
    kit.SceneFrame(art="orbit", text="Your repository does not watch the mothership. It knows only what it heard the last time it asked."),
]

STATUS = r"git status\b"
NEWS = r"git (fetch|pull)\b"
REPORT = "notes.txt"

BRIEFING = """
Alex pushed a report to the mothership a moment ago. Find out what your repository knows about
it, ask the mothership for news, and bring the report into your `main`.

The mission is done when you have looked with `git status` before and after `git fetch`, and
Alex's commit is in your `main`.
"""

HINTS = [
    "`git status` compares your `main` with `origin/main`, which changes only when you fetch.",
    "`git fetch` brings the news; `git pull` brings Alex's commit into your `main`.",
    "Every line of the mission, in order:\n\n    $ git status\n    $ git fetch\n    $ git status\n    $ git pull",
]

DEBRIEF = """
`git status` said up to date because it compares your `main` with `origin/main`: your
repository's copy of the mothership's `main`, as of the last time it asked. `git fetch` asked,
and `origin/main` moved to Alex's commit, so `git status` said behind by one. `git pull` fetched
again and brought that commit into your `main`, and Alex's line into `notes.txt`.

Commands to keep:

    $ git fetch     # ask the remote for news; your main and files stay as they are
    $ git pull      # fetch, then bring the news into your branch
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
WAITING = "The mothership has no news yet. Wait a moment for Alex's report."
LOOKED = "`git status` says up to date: it compares with `origin/main`, which has not heard of Alex's push."
NOT_LOOKED = "Ask your repository what it knows: type `git status`."
FETCHED = "`origin/main` now holds Alex's commit: your repository has the news."
NOT_FETCHED = "Your repository has not heard of Alex's commit. Ask the mothership: `git fetch`."
BEHIND = "`git status` compares with the new `origin/main`."
NOT_AGAIN = "Now ask `git status` again: `origin/main` has moved."
PULLED = "Alex's commit is in your `main`, and their line is in `notes.txt`."
NOT_PULLED = "Alex's commit is not in your `main` yet: `git pull` brings it."

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="Alex pushed a minute ago. What will `git status` say about your `main`?",
    options=("Up to date with `origin/main`", "Behind `origin/main` by 1 commit"),
    reveal=(
        "Up to date: `git status` compares your `main` with `origin/main`, your repository's last news of the mothership, "
        "and it has not asked since Alex pushed."
    ),
)


def alex_pushes(lab: kit.Lab, state: kit.State) -> None:
    """
    Have Alex add a line to ``notes.txt``, commit it and push it, with the playground's buttons.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    for button in (f"edit:{REPORT}", f"add:{REPORT}", "commit", "push"):
        kit.press(lab, "alex", button)


EVENTS = [kit.LevelEvent(id="alex-pushes", run=alex_pushes)]


def _news(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Give Alex's commit once Alex has pushed it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: GitHub's first commit.

    Returns
    -------
    str | None
        The mothership's ``main`` once it moved past the first commit, else None.
    """
    tip = kit.git_run(lab.github, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    return tip if tip and tip != state["start"] else None


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked after Alex pushed.

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
    looked = kit.typed(typed, STATUS, "ok")
    message = LOOKED if looked else NOT_LOOKED
    if _news(lab, state) is None:
        message = WAITING
    return kit.Verdict(message == LOOKED, message)


def watch_fetch(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``origin/main`` in your repository holds Alex's commit.

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
        The step's verdict.
    """
    news = _news(lab, state)
    exists = kit.snapshot(lab.project)["exists"]
    message = FETCHED
    if not exists:
        message = NO_REPOSITORY
    elif news is None:
        message = WAITING
    elif not kit.is_ancestor(lab.project, news, "refs/remotes/origin/main"):
        message = NOT_FETCHED
    return kit.Verdict(message == FETCHED, message)


def watch_again(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked after the last fetch or pull that worked, with the news fetched.

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
        The step's verdict; the fetch comes first.
    """
    fetched = watch_fetch(lab, state, typed)
    again = kit.typed(kit.after(typed, NEWS), STATUS, "ok")
    verdict = kit.Verdict(again, BEHIND if again else NOT_AGAIN)
    return verdict if fetched.solved else fetched


def watch_pull(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds Alex's commit.

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
        The step's verdict; the fetch comes first.
    """
    fetched = watch_fetch(lab, state, typed)
    news = _news(lab, state)
    pulled = news is not None and kit.is_ancestor(lab.project, news, "refs/heads/main")
    verdict = kit.Verdict(pulled, PULLED if pulled else NOT_PULLED)
    return verdict if fetched.solved else fetched


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="status", text="Ask your repository how `main` stands.", command="git status", watch=watch_status),
    kit.WatchStep(id="fetch", text="Ask the mothership for news.", command="git fetch", watch=watch_fetch),
    kit.WatchStep(id="again", text="Ask `git status` again.", command="git status", watch=watch_again),
    kit.WatchStep(id="pull", text="Bring Alex's commit into your `main`.", command="git pull", watch=watch_pull),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground: GitHub with one commit, your clone and Alex's.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``start``: GitHub's first commit, so the check knows when Alex has pushed.
    """
    kit.setup_playground(lab)
    return {"start": kit.git(lab.github, "rev-parse", "refs/heads/main").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once Alex's commit is in your ``main``; the quest keeps the looks in order.

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
        The last goal's verdict.
    """
    return watch_pull(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player, after Alex's push: every quest step's action, in order.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab, after the event.
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


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "guess": kit.picking(GUESS.options[1]),
    "status": kit.typing("git status"),
    "fetch": kit.typing("git fetch"),
    "again": kit.typing("git status"),
    "pull": kit.typing("git pull"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
