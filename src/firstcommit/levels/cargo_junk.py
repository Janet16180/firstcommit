"""
Junk bay: the simulator floods the working folder; a ``.gitignore`` keeps its output out of ``git status`` and ``git add .``.

Wave 2, cargo 2-5 (docs/drafts/chapters-5-9.md), a situation. Setup commits the navigation and
changes it since. The simulator's run is a level event: it runs after the page's first look, so
the page animates the crates pouring into the working folder. The first goal reads the lines
typed (a ``git status`` that worked); the second asks git which file ignores the simulator's
output (``git check-ignore --verbose --no-index``), so only a ``.gitignore`` counts, not
``.git/info/exclude``, which never reaches the crew; the third reads the staging area: the rule
and the navigation staged as they are, and no output staged. Output in a commit is lost for this
play: the level says so and offers to start again.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Junk bay"
DIFFICULTY = 2
XP = 150
COMMAND = ".gitignore"
PAR = 3
CARD = kit.CommandCard(
    command=".gitignore",
    text="A file of names and patterns Git ignores: `git status` stops listing them and `git add .` skips them. The files stay on your disk.",
)
SCENE = [
    kit.SceneFrame(art="conveyor", text="The jump simulator ran all night, and it writes a pile of output files every time it runs."),
    kit.SceneFrame(art="zones", text="Generated files stay on your disk, but they never belong in a commit."),
]

NAV = "nav.cfg"
FIRST = "heading=Moon\n"
CHANGED = "heading=Mars\n"
OUTPUT = "sim-output"
RUNS = 120
IGNORE_FILE = ".gitignore"
PROBE = f"{OUTPUT}/run-001.log"
STATUS = r"git status\b"

BRIEFING = """
The jump simulator ran overnight and filled `sim-output/` with output files, one per run. They
are made again on every run, so they never belong in a commit. Your real work is the new heading
in `nav.cfg`.

The mission is done when you have looked with `git status`, a `.gitignore` file tells Git to
ignore `sim-output/`, and both `.gitignore` and `nav.cfg` are staged, with nothing from
`sim-output/`.
"""

HINTS = [
    "A file named `.gitignore` lists what Git ignores, one name or pattern per line: `sim-output/` ignores the whole folder.",
    'Write it from the terminal: `echo "sim-output/" > .gitignore`, then stage the rule and your change.',
    'Every line of the mission, in order:\n\n    $ git status\n    $ echo "sim-output/" > .gitignore\n    $ git add .gitignore nav.cfg',
]

DEBRIEF = """
`.gitignore` told Git to ignore everything in `sim-output/`. The files are still on your disk;
`git status` stopped listing them, and `git add .` skips them, so they cannot ride into a commit
by accident.

You staged `.gitignore` too. Once it is in a commit, everyone who works on the project gets the
same rule, so nobody's simulator output reaches the mothership. Build folders, logs and
downloaded dependencies get the same treatment on real projects.

Commands to keep:

    $ echo "sim-output/" > .gitignore   # ignore a folder of generated files
    $ git add .gitignore                # share the rule with the crew
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
LOOKED = "`git status` lists `sim-output/` as untracked, next to your change in `nav.cfg`."
NOT_LOOKED = "Look first: `git status` shows what the simulator left in the working folder."
NOT_IGNORED = 'Git does not ignore `sim-output/` yet. Write its name in a file called `.gitignore`: `echo "sim-output/" > .gitignore`.'
IGNORED = "`.gitignore` names `sim-output/`: Git ignores the simulator's output."
JUNK_ABOARD = "Files from `sim-output/` are staged. `git restore --staged sim-output` takes them out of the staging area; the files stay on your disk."
NOT_STAGED = "Stage the rule and your change: `git add .gitignore nav.cfg`. Now that the output is ignored, `git add .` works too."
JUNK_COMMITTED = (
    "Files from `sim-output/` are in a commit now, so they are in this repository's history. Taking a commit back "
    "comes in a later chapter: start the mission again."
)
STAGED = "`.gitignore` and `nav.cfg` are staged, and nothing from `sim-output/` is."
WHY_IGNORE = (
    "Everything in `sim-output/` is generated, and it is listed as untracked. A `git add .` now would take every file into the "
    "next commit, and every copy of the project would download them, forever. A `.gitignore` keeps them out."
)
JUNK_STAGED = (
    "That staged the simulator's output too: every file of `sim-output/`. "
    "`git restore --staged sim-output` takes it out of the staging area, files kept; then tell Git to ignore it."
)
IGNORE_FIELD = "`.gitignore` is in place: Git ignores the files it names. They are still on your disk; `git status` and `git add .` skip them."
REGENERATED = "The simulator makes those files again on its next run. Ask Git to ignore them instead: then they can stay on your disk."

REACTIONS = [
    kit.ReactionRule(line=STATUS, mood="warn", text=WHY_IGNORE, outcome="ok", repository=True, ignored=False, moment="junk-flood"),
    kit.ReactionRule(line=r"git add( \S+)* (\.|-A|--all|\*|sim-output\S*)( |$)", mood="warn", text=JUNK_STAGED, event="file-staged", ignored=False, moment="junk-flood"),
    kit.ReactionRule(line=r"(echo|printf|cat|touch)\b.*\.gitignore", mood="ok", text=IGNORE_FIELD, event="file-ignored"),
    kit.ReactionRule(line=rf"rm\b.*{OUTPUT}", mood="warn", text=REGENERATED, event="file-deleted"),
]


def simulator_runs(lab: kit.Lab, state: kit.State) -> None:
    """
    Fill ``sim-output/`` with one output file per run, as the night's simulation did.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    folder = lab.project / OUTPUT
    folder.mkdir(exist_ok=True)
    for run in range(1, RUNS + 1):
        (folder / f"run-{run:03}.log").write_text(f"run {run}: jump simulated, drift {run % 7} km\n")


EVENTS = [kit.LevelEvent(id="simulator", run=simulator_runs)]


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git status`` worked.

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
    looked = kit.typed(typed, STATUS, "ok")
    return kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)


def watch_ignore(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``.gitignore`` makes Git ignore the simulator's output.

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
    exists = kit.snapshot(lab.project)["exists"]
    found = kit.git_run(lab.project, "check-ignore", "--verbose", "--no-index", PROBE).stdout if exists else ""
    by_gitignore = found.split(":", 1)[0] == IGNORE_FILE
    message = IGNORED if by_gitignore else NOT_IGNORED
    if not exists:
        message = NO_REPOSITORY
    return kit.Verdict(message == IGNORED, message)


def watch_stage(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the rule and the navigation are staged as they are, with no output staged.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the blob id of the changed navigation.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict, with the next thing to do; lost once output is in a commit.
    """
    snap = kit.snapshot(lab.project)
    files = {file["path"]: file for file in snap["files"]}
    rule = files.get(IGNORE_FILE)
    rule_staged = rule is not None and rule["index"] is not None and rule["index"] == rule["folder"]
    nav = files.get(NAV)
    nav_staged = nav is not None and nav["index"] == state["nav"]
    junk_staged = any(path.startswith(f"{OUTPUT}/") and file["index"] is not None for path, file in files.items())
    message = STAGED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif kit.in_history(lab.project, OUTPUT):
        message = JUNK_COMMITTED
    elif junk_staged:
        message = JUNK_ABOARD
    elif not rule_staged or not nav_staged:
        message = NOT_STAGED
    return kit.Verdict(message == STAGED, message, lost=message == JUNK_COMMITTED)


QUEST: list[kit.Step] = [
    kit.WatchStep(id="look", text="Find out what the simulator left in the working folder.", command="git status", watch=watch_status),
    kit.WatchStep(id="ignore", text="Tell Git to ignore `sim-output/`.", command='echo "sim-output/" > .gitignore', watch=watch_ignore),
    kit.WatchStep(id="stage", text="Stage the rule and your change, and nothing else.", command="git add .gitignore nav.cfg", watch=watch_stage),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with one commit of the navigation, changed since; the simulator's output comes with its event.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``nav``: the blob id of the changed navigation, as staging it stores it.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    (lab.project / NAV).write_text(FIRST)
    kit.git(lab.project, "add", NAV)
    kit.git(lab.project, "commit", "-q", "-m", "Set the heading", when="2026-03-01T22:00:00+00:00")
    (lab.project / NAV).write_text(CHANGED)
    return {"nav": kit.git(lab.project, "hash-object", NAV).strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the output is ignored by ``.gitignore``, the rule and the change staged, and ``git status`` was typed.

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
        The first unmet of the staging area's verdict (it says when the work is lost), the rule's
        and the look's; the staging area's when all are met, as it names the finished state.
    """
    staged = watch_stage(lab, state, typed)
    unmet = [verdict for verdict in (staged, watch_ignore(lab, state, typed), watch_status(lab, state, typed)) if not verdict.solved]
    return unmet[0] if unmet else staged


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order (AUTHORING section 3.6).

    Parameters
    ----------
    lab : kit.Lab
        The level's lab, after the simulator's event.
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
    "look": kit.typing("git status"),
    "ignore": kit.typing('echo "sim-output/" > .gitignore'),
    "stage": kit.typing(f"git add {IGNORE_FILE} {NAV}"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
