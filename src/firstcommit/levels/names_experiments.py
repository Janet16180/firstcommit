"""
A second course: a branch is a label on a commit, and switching rewrites the working folder.

Wave 2, branch 5-2 (docs/drafts/chapters-3-7.md), guided, with a prediction. Setup makes a
repository with three commits on ``main``. The prediction breaks the myth that a branch copies
the folder. The goals read the repository: a branch ``scout``; ``HEAD`` on it; a commit on
``scout`` holding ``probe.txt`` that ``main`` does not have; back on ``main`` with ``probe.txt``
gone from the folder; and, read from the lines typed, an ``ls`` after that switch (looking is
the lesson).
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "A second course"
DIFFICULTY = 2
XP = 150
COMMAND = "git branch"
PAR = 5
VIEW = "history"
CARD = kit.CommandCard(
    command="git branch <name>",
    text="Makes a new branch: a label on the commit you are on. No file is copied, and you stay on the branch you were on.",
)
SCENE = [
    kit.SceneFrame(art="fork", text="The base wants to try a new course without touching `main`."),
    kit.SceneFrame(art="fork", text="A branch is a label on a capsule. `HEAD` is the label you ride: your next capsule moves it on."),
]

BRANCH = "scout"
PROBE = "probe.txt"
PROBE_LINE = "Probe: launched"
FILES = {"route.txt": "Route: Earth, Moon\n", "crew.txt": "Robin\nAlex\n", "log.txt": "Day 1: all quiet.\n"}
BACK = kit.switching("main")
LIST = r"ls\b"

BRIEFING = """
The base's `main` holds three commits. The captain wants a probe tried on a second course, and
`main` left as it is.

The mission is done when a branch `scout` holds a commit with `probe.txt` that `main` does not
have, you are back on `main`, and you have looked at the folder there with `ls`.
"""

HINTS = [
    "`git branch scout` makes the label; `git switch scout` moves you onto it.",
    'On `scout`, write the file and commit it: `echo "Probe: launched" > probe.txt && git add probe.txt && git commit -m "Launch the probe"`.',
    "`git switch main` takes you back; `ls` shows what the folder holds there.",
    'Every line of the mission, in order:\n\n    $ git branch scout\n    $ git switch scout\n    $ echo "Probe: launched" > probe.txt && git add probe.txt && git commit -m "Launch the probe"\n    $ git switch main\n    $ ls',
]

DEBRIEF = """
`git branch scout` wrote one new label on the commit you were on: no file was copied. `git switch
scout` moved `HEAD` onto that label, and your commit moved `scout` on, while `main` stayed where it
was.

Back on `main`, Git rewrote the working folder to match `main`'s last commit, so `probe.txt` left
it. Nothing was lost: the probe is in `scout`'s commit, and `git switch scout` brings it back.

At work, every task gets its own branch, so `main` stays as the team agreed it.

Commands to keep:

    $ git branch scout   # a new label on the commit you are on
    $ git switch scout   # move onto it; the folder follows
    $ git switch main    # and back
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NO_BRANCH = "There is no branch `scout` yet. Make it: `git branch scout`."
MADE = "`scout` is a second label on the commit `main` is on. The folder did not change."
NOT_ON = "You are not on `scout`. Move onto it: `git switch scout`."
ON = "You are on `scout`: your next commit moves its label on."
NOT_COMMITTED = 'Commit the probe on `scout`: `echo "Probe: launched" > probe.txt && git add probe.txt && git commit -m "Launch the probe"`.'
COMMITTED = "`scout` moved on to the probe's commit; `main` stayed where it was."
PROBE_ON_MAIN = "`main` holds `probe.txt` too: that commit went onto `main`. Start the mission again, and commit the probe on `scout`."
NOT_BACK = "Go back to `main`: `git switch main`."
STILL_THERE = "`probe.txt` is still in the folder, outside any commit of `main`. Remove it with `rm probe.txt`: `scout` keeps its copy."
BACK_ON_MAIN = "You are on `main`, and `probe.txt` left the folder: it lives in `scout`'s commit."
LOOKED = "`ls` shows `main`'s files only. `git switch scout` would bring the probe back."
NOT_LOOKED = "Look at the folder: `ls`."

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You are about to make a branch `scout`. What will the folder hold afterwards?",
    options=("The same files, once", "A second copy of the files, for scout"),
    reveal="The same files, once. A branch is a label on a commit: `git branch scout` writes a new label and copies no file.",
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
        Its hash, or empty when there is no such branch.
    """
    return kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()


def _holds_probe(lab: kit.Lab, ref: str) -> bool:
    """
    Tell whether a branch's last commit holds the probe.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    ref : str
        The branch's full name.

    Returns
    -------
    bool
        True when its tree has ``probe.txt``.
    """
    return kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{ref}:{PROBE}").returncode == 0


def watch_branch(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the branch ``scout`` exists.

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
    message = MADE
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    elif not _tip(lab, f"refs/heads/{BRANCH}"):
        message = NO_BRANCH
    return kit.Verdict(message == MADE, message)


def watch_switch(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``HEAD`` is on ``scout``.

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
        The step's verdict; the branch comes first.
    """
    made = watch_branch(lab, state, typed)
    on = kit.snapshot(lab.project)["branch"] == BRANCH
    verdict = kit.Verdict(on, ON if on else NOT_ON)
    return verdict if made.solved else made


def _committed(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Tell whether ``scout`` holds the probe in a commit ``main`` lacks, whatever branch you are on.

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
        Passed once ``scout`` holds it and ``main`` does not; lost once ``main`` holds it too.
    """
    made = watch_branch(lab, state, typed)
    on_main = _holds_probe(lab, "refs/heads/main")
    committed = _holds_probe(lab, f"refs/heads/{BRANCH}")
    message = COMMITTED if committed else NOT_COMMITTED
    if on_main:
        message = PROBE_ON_MAIN
    verdict = kit.Verdict(message == COMMITTED, message, lost=on_main)
    return verdict if made.solved else made


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once you are on ``scout`` and it holds the probe in a commit ``main`` lacks.

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
        The step's verdict; being on ``scout`` comes first.
    """
    on = watch_switch(lab, state, typed)
    committed = _committed(lab, state, typed)
    return committed if on.solved or committed.lost else on


def watch_back(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once you are on ``main`` again, with the probe in ``scout`` and gone from the folder.

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
        The step's verdict; the probe's commit comes first.
    """
    committed = _committed(lab, state, typed)
    snap = kit.snapshot(lab.project)
    message = BACK_ON_MAIN
    if snap["branch"] != "main":
        message = NOT_BACK
    elif any(entry["path"] == PROBE and entry["folder"] is not None for entry in snap["files"]):
        message = STILL_THERE
    verdict = kit.Verdict(message == BACK_ON_MAIN, message)
    return verdict if committed.solved else committed


def watch_look(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once an ``ls`` worked after the last switch back to ``main``.

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
        The step's verdict; being back on ``main`` comes first.
    """
    back = watch_back(lab, state, typed)
    looked = kit.typed(kit.after(typed, BACK), LIST, "ok")
    verdict = kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)
    return verdict if back.solved else back


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="branch", text="Make a branch `scout`.", command=f"git branch {BRANCH}", watch=watch_branch),
    kit.WatchStep(id="switch", text="Move onto `scout`.", command=f"git switch {BRANCH}", watch=watch_switch),
    kit.WatchStep(
        id="commit",
        text="Commit a probe on `scout`.",
        command=f'echo "{PROBE_LINE}" > {PROBE} && git add {PROBE} && git commit -m "Launch the probe"',
        watch=watch_commit,
    ),
    kit.WatchStep(id="back", text="Go back to `main`.", command="git switch main", watch=watch_back),
    kit.WatchStep(id="look", text="Look at the folder on `main`.", command="ls", watch=watch_look),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with three commits on ``main``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the goals read the repository.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for day, (name, text) in enumerate(FILES.items(), start=1):
        (lab.project / name).write_text(text)
        kit.git(lab.project, "add", name)
        kit.git(lab.project, "commit", "-q", "-m", f"Add {name}", author=kit.PLAYER, when=f"2026-05-0{day}T09:00:00+00:00")
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once you looked at the folder back on ``main``; lost once ``main`` holds the probe.

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
    return watch_look(lab, state, typed)


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
    "branch": kit.typing(f"git branch {BRANCH}"),
    "switch": kit.typing(f"git switch {BRANCH}"),
    "commit": kit.typing(f'echo "{PROBE_LINE}" > {PROBE} && git add {PROBE} && git commit -m "Launch the probe"'),
    "back": kit.typing("git switch main"),
    "look": kit.typing("ls"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
