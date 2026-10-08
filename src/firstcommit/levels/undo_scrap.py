"""
Scrap the workshop: ``git restore`` replaces a file in the working folder, and lines never staged or committed are gone.

Wave 2, undo 7-1 (docs/drafts/chapters-5-9.md), guided, with a prediction. Setup makes a
repository with the engine settings committed, then an experiment in ``engine.cfg`` that was
never staged, and a change to ``notes.txt`` that is staged. The prediction breaks the myth that
Git can always give work back. The goals: ``git diff`` typed (look at what will be lost); then
``engine.cfg`` back to its committed version, with the staged notes kept. The notes thrown away
are lost for this play. The black box's boundary is born here: the staging area, the vault and the
mothership inside, the working folder outside.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Scrap the workshop"
DIFFICULTY = 1
XP = 120
COMMAND = "git restore"
PAR = 2
VIEW = "blackbox"
CARD = kit.CommandCard(
    command="git restore <file>",
    text="Replaces a file in the working folder with its version in the staging area. Lines you never staged or committed are gone for good.",
)
SCENE = [
    kit.SceneFrame(art="blackbox", text="Git keeps a flight recorder: what you staged, what you committed and what reached the mothership."),
    kit.SceneFrame(art="blackbox", text="Your working folder is outside the box. Lines you only typed there were never recorded."),
]

ENGINE = "engine.cfg"
NOTES = "notes.txt"
ENGINE_COMMITTED = "power=80\n"
ENGINE_EXPERIMENT = "power=99\noverdrive=on\n"
NOTES_COMMITTED = "Engine log\n"
NOTES_STAGED = "Engine log\nDay 4: overdrive test planned\n"
LOOK = r"git diff\b"

BRIEFING = """
Last night's experiment in `engine.cfg` overheated the engine. It was never staged or committed;
scrap it and go back to the committed settings. Your notes in `notes.txt` are staged for the next
commit: keep them.

The mission is done when you have looked at the experiment with `git diff`, `engine.cfg` is back to
its committed version, and `notes.txt` is still staged.
"""

HINTS = [
    "`git diff` shows the lines in the working folder that are not staged: the experiment.",
    "`git restore engine.cfg` replaces the file with its version in the staging area, which is the committed one.",
    "Every line of the mission, in order:\n\n    $ git diff\n    $ git restore engine.cfg",
]

DEBRIEF = """
`git restore engine.cfg` copied the file's version from the staging area over the one in the
working folder. The experiment's lines were never staged or committed, so no copy of them existed
anywhere: Git cannot give them back, and no command will.

`notes.txt` was safe all along: what is staged or committed is inside Git's flight recorder. Before
you scrap a file, `git diff` shows exactly what you are about to lose.

Commands to keep:

    $ git diff                 # what is in the working folder and not staged
    $ git restore engine.cfg   # scrap it: back to the staged version
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOOKED = "`git diff` shows the experiment: the lines that are in the working folder and nowhere else."
NOT_LOOKED = "Look at what you would lose first: `git diff`."
NOT_SCRAPPED = "`engine.cfg` still holds the experiment. Scrap it: `git restore engine.cfg`."
NOTES_LOST = "Your staged notes are gone: they were in no commit. Start the mission again."
NOTES_UNSTAGED = "`notes.txt` is no longer staged. Stage it again: `git add notes.txt`."
SCRAPPED = "`engine.cfg` is back to its committed settings, and your notes are still staged."
GONE = (
    "The experiment's lines are gone for good: they were never staged or committed, so Git has no copy of them. "
    "Git keeps what was staged or committed; these lines were neither."
)

REACTIONS = [
    kit.ReactionRule(line=r"git (restore|checkout)\b(?!.*--staged( |$))", mood="warn", text=GONE, event="file-changed", moment="search-beam"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You scrap the experiment with `git restore engine.cfg`. Could Git give its lines back afterwards?",
    options=("Yes, from the last commit", "No: they were never saved in Git"),
    reveal="No. The last commit holds the old settings, not the experiment: its lines were never staged or committed, so Git never had a copy.",
)


def watch_look(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git diff`` worked.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused).
    state : kit.State
        The level's state (unused).
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    looked = kit.typed(typed, LOOK, "ok")
    return kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)


def watch_scrap(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``engine.cfg`` is its committed version and the notes are still staged.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the blob id of the staged notes.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; lost once the staged notes are gone.
    """
    snap = kit.snapshot(lab.project)
    files = {file["path"]: file for file in snap["files"]}
    notes = files.get(NOTES)
    notes_staged = notes is not None and notes["index"] == state["notes"]
    notes_kept = notes is not None and state["notes"] in (notes["index"], notes["folder"], notes["head"])
    engine = lab.project / ENGINE
    scrapped = engine.is_file() and engine.read_text() == ENGINE_COMMITTED
    message = SCRAPPED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif not notes_kept:
        message = NOTES_LOST
    elif not scrapped:
        message = NOT_SCRAPPED
    elif not notes_staged:
        message = NOTES_UNSTAGED
    return kit.Verdict(message == SCRAPPED, message, lost=message == NOTES_LOST)


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="look", text="Look at the experiment you are about to scrap.", command="git diff", watch=watch_look),
    kit.WatchStep(id="scrap", text="Scrap the experiment, and keep your staged notes.", command=f"git restore {ENGINE}", watch=watch_scrap),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Commit the engine settings and the notes, then stage a change to the notes and leave an experiment in the engine.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``notes``: the blob id of the staged notes.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    (lab.project / ENGINE).write_text(ENGINE_COMMITTED)
    (lab.project / NOTES).write_text(NOTES_COMMITTED)
    kit.git(lab.project, "add", ENGINE, NOTES)
    kit.git(lab.project, "commit", "-q", "-m", "Set the engine", when="2026-07-01T09:00:00+00:00")
    (lab.project / NOTES).write_text(NOTES_STAGED)
    kit.git(lab.project, "add", NOTES)
    (lab.project / ENGINE).write_text(ENGINE_EXPERIMENT)
    return {"notes": kit.git(lab.project, "hash-object", NOTES).strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the engine is scrapped, the notes staged, and ``git diff`` was typed.

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
        The scrap's verdict (it says when the work is lost) unless the look is missing.
    """
    scrapped = watch_scrap(lab, state, typed)
    looked = watch_look(lab, state, typed)
    return looked if scrapped.solved and not looked.solved else scrapped


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
    return GUESS.options[0]


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "guess": guess,
    "look": kit.typing("git diff"),
    "scrap": kit.typing(f"git restore {ENGINE}"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
