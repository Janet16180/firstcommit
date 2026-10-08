"""
Name tags: a branch is a name for one commit, HEAD is "you are here", and ``origin/main`` is a bookmark.

Name tags 5-1 (docs/drafts/sector5/5-1-script.md), guided, with two predictions. Setup starts the
sector's story (`_names_story.name_tags`): three commits on ``main``, pushed, the old name
``test-run`` on the first, and the fuel level noted in ``notes.txt``, not committed. The goals: the
history read and the branches listed; the note committed, which moves only ``main``; the history
read again; the note pushed, inside which push Alex pushes a route fix (`kit.on_push`), so the
mothership moves on without you; your bookmark brought up to it with a fetch (a pull does too);
and ``git status`` read after it.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit
from firstcommit.levels import _names_story as story

TITLE = "Name tags"
DIFFICULTY = 1
XP = 100
COMMAND = "git branch -v"
PAR = 7
PICTURES = kit.pictures("chain", mothership=True)
CARD = kit.CommandCard(
    command="git branch -v",
    text="Lists your branches, each with the commit it names. `*` marks the branch `HEAD` is on.",
)
SCENE = [
    kit.SceneFrame(
        art="chain",
        text="New sector: Name tags. Since you met the remote (the mothership) you have typed `main` and `origin/main` in `git push` and `git status`. This sector says what they are: names. Commits are the work; names are how you find it.",
    ),
    kit.SceneFrame(
        art="chain",
        text="This is the chain: your commits, newest at the top, each joined by a line to the one before it. The commits are the work. This mission is about the names on them.",
    ),
]

LOG = r"git log\b"
BRANCHES = r"git branch( -v+| --verbose)+( |$)"
COMMIT = r"git commit\b"
NEWS = r"git (fetch|pull)\b"
STATUS = r"git status\b"

BRIEFING = """
You noted the fuel level in `notes.txt`. Commit the note and send it to the mothership, then check
for news from the crew. Watch which names move.

The mission is done when your note is on the mothership, your bookmark of the mothership has
caught up with the crew's news, and you have asked `git status` how `main` stands.
"""

HINTS = [
    "`git log --oneline` shows each commit on one line; the names in brackets are the names on that commit.",
    "`git commit -am` commits every tracked file you changed; `git push` sends `main` up; `git fetch` asks the mothership for news.",
    'Every line of the mission, in order:\n\n    $ git log --oneline\n    $ git branch -v\n    $ git commit -am "Note the fuel level"\n    $ git log --oneline\n    $ git push\n    $ git fetch\n    $ git status',
]

DEBRIEF = """
A branch is a name for one commit. `HEAD` is "you are here", and it rides the branch you are on.
When you commit, that branch moves up to the new commit and `HEAD` rides along; no other name
moves.

`origin/main` is your bookmark of the mothership's `main`. The mothership can move on without
you, as it did when Alex pushed; your bookmark catches up only when you talk to the mothership:
`git push`, `git fetch` or `git pull`.

Commands to keep:

    $ git log --oneline   # the names in brackets sit on that commit
    $ git branch -v       # each branch and the commit it names; * is where HEAD rides
    $ git fetch           # update your bookmark of the mothership
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOGGED = (
    "The names in brackets sit on that commit. `main` is a branch: a name for one commit. `test-run` is another branch, a "
    "name for an older commit. `HEAD -> main` means `HEAD` is on `main`: `HEAD` is \"you are here\", the commit your folder shows."
)
NOT_LOGGED = "Read the history: `git log --oneline`."
LISTED = (
    "That is all a branch is: a name and the hash of one commit. Two names, two commits. The `*` marks the branch `HEAD` is "
    "on. `origin/main` is your bookmark: where the mothership's `main` was the last time you talked to it."
)
NOT_LISTED = "List your branches: `git branch -v`."
NOT_COMMITTED = 'Commit your note: `git commit -am "Note the fuel level"`.'
COMMITTED = "`main` moved up to the new commit, and `HEAD` rode along. `test-run` stayed, and so did your bookmark: the mothership has not heard of this commit."
LOGGED_AGAIN = "`git log` says the same in words: `HEAD -> main` on the new commit, `origin/main` one below."
NOT_LOGGED_AGAIN = "Read the history again: `git log --oneline`."
NOT_PUSHED = "Send your note up: `git push`."
PUSHED = (
    "The push sent your commit up, and Git moved your bookmark at the same moment. News: Alex just pushed a fix, so the "
    "mothership's `main` is on Alex's commit. Your bookmark did not move: you have not talked to the mothership since."
)
NOT_FETCHED = "Ask the mothership for news: `git fetch`."
FETCHED = "Your bookmark caught up with the mothership, and Alex's commit is in your repository. `main` and `HEAD` stayed on your commit, so your folder did not change."
STATUS_READ = "`git status` compares `main` with your bookmark: one commit behind. \"Fast-forwarded\" means `main` can simply slide up to it; `git pull` would do that."
STATUS_PULLED = "`git status` compares `main` with your bookmark: your pull already slid `main` up to it, so they agree."
NOT_STATUS = "Ask how `main` stands: `git status`."
LISTS_NAMES = "Each line is a name and the commit it points at. `*` marks the one `HEAD` rides."

REACTIONS = [
    kit.ReactionRule(line=BRANCHES, mood="info", text=LISTS_NAMES, outcome="ok"),
]

COMMIT_GUESS = kit.ChoiceStep(
    id="guess-commit",
    text="Predict first.",
    question="You commit your fuel note now. Which names move up to the new commit?",
    options=("Only `main`", "`main` and `origin/main`", "`main` and `test-run`"),
    reveal="Only `main`, with `HEAD` riding it. A commit moves the branch `HEAD` rides. `test-run` names its own commit, and the bookmark moves only when you talk to the mothership.",
)
FETCH_GUESS = kit.ChoiceStep(
    id="guess-fetch",
    text="Predict first.",
    question="You type `git fetch`, which asks the mothership for news. Afterwards, is Alex's fix in your folder?",
    options=("Yes", "No"),
    reveal="No. A fetch brings Alex's commit into your repository and moves your bookmark to it. `main` stays where it was, so your folder, which shows `main`'s commit, does not change.",
)


def _holds_note(lab: kit.Lab, folder: str, ref: str) -> bool:
    """
    Tell whether a branch's commit holds the fuel note.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    folder : str
        ``"project"`` or ``"github"``.
    ref : str
        The branch's full name.

    Returns
    -------
    bool
        True when its ``notes.txt`` has the note.
    """
    path = lab.project if folder == "project" else lab.github
    return "Fuel: 80%" in kit.git_run(path, "show", f"{ref}:{story.NOTES}").stdout


def _tip(path: Path, ref: str) -> str:
    """
    Give the commit a ref points at.

    Parameters
    ----------
    path : kit.Path
        The repository.
    ref : str
        The ref's full name.

    Returns
    -------
    str
        Its hash, or empty when there is no such ref.
    """
    return kit.git_run(path, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked.

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


def watch_branches(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git branch -v`` worked.

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
    listed = kit.typed(typed, BRANCHES, "ok")
    verdict = kit.Verdict(listed, LISTED if listed else NOT_LISTED)
    return verdict if logged.solved else logged


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``main`` holds the fuel note.

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
    message = COMMITTED if _holds_note(lab, "project", "refs/heads/main") else NOT_COMMITTED
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == COMMITTED, message)


def watch_log_again(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked after the commit.

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
    committed = watch_commit(lab, state, typed)
    logged = kit.typed(kit.after(typed, COMMIT), LOG, "ok")
    verdict = kit.Verdict(logged, LOGGED_AGAIN if logged else NOT_LOGGED_AGAIN)
    return verdict if committed.solved else committed


def watch_push(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``main`` holds the fuel note.

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
    committed = watch_commit(lab, state, typed)
    pushed = _holds_note(lab, "github", "refs/heads/main")
    verdict = kit.Verdict(pushed, PUSHED if pushed else NOT_PUSHED)
    return verdict if committed.solved else committed


def watch_fetch(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your bookmark ``origin/main`` is where the mothership's ``main`` is, Alex's fix included.

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
        The step's verdict; the push comes first.
    """
    pushed = watch_push(lab, state, typed)
    mothership = _tip(lab.github, "refs/heads/main")
    caught_up = mothership != "" and _tip(lab.project, "refs/remotes/origin/main") == mothership and kit.typed(typed, NEWS, "ok")
    verdict = kit.Verdict(caught_up, FETCHED if caught_up else NOT_FETCHED)
    return verdict if pushed.solved else pushed


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git status`` worked after the fetch (or a pull).

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
        The step's verdict, which says whether ``main`` is behind; the fetch comes first.
    """
    fetched = watch_fetch(lab, state, typed)
    read = kit.typed(kit.after(typed, NEWS), STATUS, "ok")
    behind = _tip(lab.project, "refs/heads/main") != _tip(lab.project, "refs/remotes/origin/main")
    message = (STATUS_READ if behind else STATUS_PULLED) if read else NOT_STATUS
    verdict = kit.Verdict(read, message)
    return verdict if fetched.solved else fetched


QUEST: list[kit.Step] = [
    kit.WatchStep(id="log", text="Read the history.", command="git log --oneline", watch=watch_log),
    kit.WatchStep(id="branches", text="List your branches.", command="git branch -v", watch=watch_branches, look=("HEAD",)),
    COMMIT_GUESS,
    kit.WatchStep(id="commit", text="Commit your note.", command='git commit -am "Note the fuel level"', watch=watch_commit),
    kit.WatchStep(id="log-again", text="Read the history again.", command="git log --oneline", watch=watch_log_again),
    kit.WatchStep(id="push", text="Send it up.", command="git push", watch=watch_push),
    FETCH_GUESS,
    kit.WatchStep(id="fetch", text="Ask the mothership for news.", command="git fetch", watch=watch_fetch),
    kit.WatchStep(id="status", text="Ask how `main` stands.", command="git status", watch=watch_status),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Start the sector's story, and have Alex push a route fix inside your push of the note.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the goals read the repositories and what was typed.
    """
    story.name_tags(lab)
    kit.on_push(lab, story.NOTES, story.NOTES_WITH_FUEL, story.ALEX_FIX)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once ``git status`` was read after your bookmark caught up with the mothership.

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
    return watch_status(lab, state, typed)


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
    "log": kit.typing("git log --oneline"),
    "branches": kit.typing("git branch -v"),
    "guess-commit": kit.picking(COMMIT_GUESS.options[1]),
    "commit": kit.typing('git commit -am "Note the fuel level"'),
    "log-again": kit.typing("git log --oneline"),
    "push": kit.typing("git push"),
    "guess-fetch": kit.picking(FETCH_GUESS.options[0]),
    "fetch": kit.typing("git fetch"),
    "status": kit.typing("git status"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
