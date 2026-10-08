"""
Seal the capsule: commit what is in the staging area; the commit stays on this computer.

Wave 1, vault 3-1 (docs/drafts/chapters-3-7.md), guided, with a prediction. Setup makes a new
repository with the map staged and the journal untracked, next to an empty stand-in GitHub that
no remote names, so the page shows the mothership staying dark. The prediction breaks the myth
that a commit sends anything. The first goal reads the repository (a commit holds the map and
not the journal); the second reads the lines typed (a ``git log`` that worked after the last
commit that worked). A journal sealed into a capsule cannot be taken back yet, so the level
says so and offers to start again.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Seal the capsule"
DIFFICULTY = 1
XP = 100
COMMAND = "git commit -m"
PAR = 2
CARD = kit.CommandCard(
    command='git commit -m "<message>"',
    text="Seals what is in the staging area into a new commit in your repository, with your message. It stays on this computer until you push.",
)
SCENE = [
    kit.SceneFrame(art="capsule", text="A commit seals the staging area into a capsule: a snapshot of the files in it, with your message."),
    kit.SceneFrame(art="chain", text="Each new capsule hangs on the one before it. That chain is your project's history, kept in your vault."),
]

CARGO = "map.txt"
KEPT = "journal.txt"
FILES = {CARGO: "Route: Earth, Moon, Mars\n", KEPT: "Day 1: landed without trouble.\n"}
COMMIT = r"git commit\b"
LOG = r"git log\b"

BRIEFING = """
The map is in the staging area, and the journal is not ready yet. Seal the map into your first
capsule, with a message that says what it holds.

The mission is done when a commit holds `map.txt`, `journal.txt` is still only in the working
folder, and you have looked at the history with `git log`.
"""

HINTS = [
    "`git commit` takes a message with `-m`, in quotes.",
    'Type `git commit -m "Add the map"`, then `git log`.',
    'Every line of the mission, in order:\n\n    $ git commit -m "Add the map"\n    $ git log',
]

DEBRIEF = """
`git commit` sealed what was in the staging area, the map, into a capsule with your message, your
name and a hash. The journal was never staged, so it stays in the working folder, untracked.

The capsule is in your vault, on this computer only: the mothership is still empty. Sending
capsules to it is the next chapter.

Commands to keep:

    $ git commit -m "Add the map"   # seal the staging area into a commit
    $ git log                       # the history, newest commit first
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NO_COMMIT = 'No capsule yet. Seal the staging area with a message: `git commit -m "Add the map"`.'
MAP_MISSING = "Your commit does not hold `map.txt`. Stage it with `git add map.txt`, then commit again."
JOURNAL_SEALED = (
    "`journal.txt` is in a commit too, and it was not ready. Taking a commit back comes in a later chapter: "
    "start the mission again."
)
JOURNAL_STAGED = "`journal.txt` is staged, and it is not ready. `git rm --cached journal.txt` takes it back out; the file stays."
SEALED = "The map is sealed in a capsule, and the journal stays in the working folder."
LOOKED = "`git log` lists your capsule: its hash, your name, the date and your message."
NOT_LOOKED = "Now look at the history: type `git log`."

REACTIONS = [kit.ReactionRule(line=r"git add( \S+)* (\.|-A|--all|journal\.txt)( |$)", mood="warn", text=JOURNAL_STAGED, event="file-staged")]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You seal the map into a capsule. Where is the capsule afterwards?",
    options=("Only in your vault, on this computer", "In your vault and on the mothership", "Only on the mothership"),
    reveal="Only in your vault: a commit goes into your repository, on this computer. Nothing reaches the mothership until you push it.",
)


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a commit holds the map and none holds the journal.

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
        The step's verdict, with the next thing to do; lost once the journal is in a commit.
    """
    snap = kit.snapshot(lab.project)
    journal = kit.in_history(lab.project, KEPT)
    message = SEALED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif journal:
        message = JOURNAL_SEALED
    elif KEPT in kit.staged(snap):
        message = JOURNAL_STAGED
    elif not snap["commits"]:
        message = NO_COMMIT
    elif not kit.in_history(lab.project, CARGO):
        message = MAP_MISSING
    return kit.Verdict(message == SEALED, message, lost=journal)


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked after the last commit that worked, with the capsule right.

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
    sealed = watch_commit(lab, state, typed)
    looked = kit.typed(kit.after(typed, COMMIT), LOG, "ok")
    verdict = kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)
    return verdict if sealed.solved else sealed


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="commit", text="Seal the map into a capsule.", command='git commit -m "Add the map"', watch=watch_commit),
    kit.WatchStep(id="log", text="Look at the history.", command="git log", watch=watch_log),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a new repository with the map staged and the journal untracked, and an empty stand-in GitHub.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the level has nothing to remember.
    """
    kit.setup_github(lab)
    kit.git(lab.root, "init", "-q", str(lab.project))
    for name, text in FILES.items():
        (lab.project / name).write_text(text)
    kit.git(lab.project, "add", CARGO)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the map is committed without the journal and ``git log`` was typed after.

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
        The last goal's verdict, which checks the commit too.
    """
    return watch_log(lab, state, typed)


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
    Pick the prediction many players make.

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
    "commit": kit.typing('git commit -m "Add the map"'),
    "log": kit.typing("git log"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
