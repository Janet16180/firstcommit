"""
Scrap the workshop: ``git restore`` replaces a file in the working folder, and lines never staged or committed are gone.

Time travel 8-1 (docs/drafts/sector8/8-1-script.md), guided, with a prediction. Setup makes a
repository with the engine settings committed, then an experiment in ``engine.cfg`` that was
never staged, and a change to ``notes.txt`` that is staged. The prediction breaks the myth that
Git keeps every version of a file. The goals: ``git diff`` typed (look at what will be lost);
``engine.cfg`` back to its committed version, with the staged notes kept; and ``git status`` read
after it. The notes thrown away are lost for this play. The desk draws ``engine.cfg``'s lines, and
its "Git has a copy" outline round the staging area and the commits appears with the reveal.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Scrap the workshop"
DIFFICULTY = 1
XP = 120
COMMAND = "git restore"
PAR = 2
PICTURES = kit.pictures("desk", kept="guess", lines=["engine.cfg"])
CARD = kit.CommandCard(
    command="git restore <file>",
    text="Replaces a file in the working folder with Git's copy: the staged one if there is one, else the committed one. Lines you never staged or committed are gone for good.",
)
SCENE = [
    kit.SceneFrame(art="zones", text="Last night's experiment overheated the engine. In `engine.cfg`, one line changed and one line was added: the two red lines."),
]

ENGINE = "engine.cfg"
NOTES = "notes.txt"
ENGINE_COMMITTED = "power=80\n"
ENGINE_EXPERIMENT = "power=99\noverdrive=on\n"
NOTES_COMMITTED = "Engine log\n"
NOTES_STAGED = "Engine log\nDay 4: overdrive test planned\n"
LOOK = r"git diff\b"
RESTORE = rf"git (restore|checkout)\b(?!.*--staged( |$)).* {ENGINE}( |$)"
STATUS = r"git status\b"

BRIEFING = """
Last night's experiment in `engine.cfg`, in your working folder (the workshop), overheated the
engine. Scrap it and go back to the committed settings. Your notes in `notes.txt` are staged for
the next commit: keep them.

The mission is done when you have looked at the experiment with `git diff`, `engine.cfg` is back to
its committed version, and `git status` shows `notes.txt` still staged.
"""

HINTS = [
    "`git diff` shows the lines in the working folder that are not staged: the experiment.",
    "`git restore engine.cfg` copies Git's copy of the file over yours. `engine.cfg` was never staged, so Git's copy is the committed one.",
    "Every line of the mission, in order:\n\n    $ git diff\n    $ git restore engine.cfg\n    $ git status",
]

DEBRIEF = """
`git restore engine.cfg` copied Git's copy over your file: the staged copy when there is one,
otherwise the committed one. `engine.cfg` was never staged, so it got the committed `power=80`. The
experiment's lines were never staged or committed, so Git had no copy of them, and no command can
bring them back.

`notes.txt` was safe all along: it was inside "Git has a copy". Before you scrap a file, `git diff`
shows exactly what you are about to lose.

In sector 2, `git restore --staged` took a file out of the staging area and kept your folder's copy
as it was. Without `--staged`, `git restore` replaces your folder's copy: that is the one that can
lose work.

Commands to keep:

    $ git diff                 # what is in the working folder and not staged
    $ git restore engine.cfg   # scrap it: back to Git's copy
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOOKED = "`git diff` shows what is in your working folder and not staged. `-` is the line Git has, `+` the lines only you have. Look before they go."
NOT_LOOKED = "Look at what you would lose first: `git diff`."
NOT_SCRAPPED = "`engine.cfg` still holds the experiment. Scrap it: `git restore engine.cfg`."
NOTES_LOST = "Your staged notes are gone: they were in no commit. Start the mission again."
NOTES_UNSTAGED = "`notes.txt` is no longer staged. Stage it again: `git add notes.txt`."
SCRAPPED = "`git restore` copied Git's copy of `engine.cfg`, `power=80`, over yours. The two red lines are gone for good. `git restore` printed nothing: most git commands are quiet when they work."
STATUS_READ = "Your notes are still staged, ready for the next commit. `git restore` changed only the file you named."
NOT_STATUS = "Check your notes are still staged: `git status`."
GONE = "The experiment's lines are gone for good: Git had no copy of them."

REACTIONS = [
    kit.ReactionRule(line=r"git (restore|checkout)\b(?!.*--staged( |$))", mood="warn", text=GONE, event="file-changed"),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You scrap the experiment with `git restore engine.cfg`. Tomorrow you want it back. Can Git give you the two red lines?",
    options=("Yes, Git keeps every version of a file", "No, they are gone for good"),
    reveal="No. Git keeps only what you staged or committed. The dashed line shows it: the staging area and your commits are inside. The red lines exist only in your working folder, so Git never had a copy.",
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


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git status`` worked after the engine was scrapped, the notes still staged.

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
        The step's verdict; the scrap comes first.
    """
    scrapped = watch_scrap(lab, state, typed)
    read = kit.typed(kit.after(typed, RESTORE), STATUS, "ok")
    verdict = kit.Verdict(read, STATUS_READ if read else NOT_STATUS)
    return verdict if scrapped.solved else scrapped


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="look", text="Look at the experiment.", command="git diff", watch=watch_look),
    kit.WatchStep(id="scrap", text="Scrap it.", command=f"git restore {ENGINE}", watch=watch_scrap),
    kit.WatchStep(id="status", text="Check your notes are still staged.", command="git status", watch=watch_status),
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
    Solved once ``git status`` was read after the scrap, with ``git diff`` typed; lost once the staged notes are gone.

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
        The last goal's verdict (the scrap's says when the work is lost) unless the look is missing.
    """
    read = watch_status(lab, state, typed)
    looked = watch_look(lab, state, typed)
    return looked if read.solved and not looked.solved else read


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
    "guess": kit.picking(GUESS.options[0]),
    "look": kit.typing("git diff"),
    "scrap": kit.typing(f"git restore {ENGINE}"),
    "status": kit.typing("git status"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
