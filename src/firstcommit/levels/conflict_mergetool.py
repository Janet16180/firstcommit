"""
Merge tools: ``git mergetool`` opens a merge tool on the file in conflict, and adds the answer itself.

Wave 2, conflict 7-4 (docs/drafts/mergetool/, approved 2026-10-08), guided. Setup makes a
repository where ``main`` moved the launch to 07:00 and packed oxygen while Alex, on ``scout``,
moved it to 05:30 and packed a spare antenna, the commit's message saying the launch window
closes early. The merge stops with two conflicts in ``launch.txt`` that need different answers
(Alex's time, both cargo lines), so keeping one side of the whole file cannot answer it. The
game's merge tool (`firstcommit.mergetool`) opens the page's merge panel; the goals read end
states, so an answer written by hand passes too. The goals: the merge paused; ``launch.txt``
added with the right answer; ``git status`` typed after it (looking is the lesson: the tool
added the file); and ``main``'s last commit holding the answer with ``scout`` in its history.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Merge tools"
DIFFICULTY = 2
XP = 180
COMMAND = "git mergetool"
PAR = 4
VIEW = "sides"
CARD = kit.CommandCard(
    command="git mergetool",
    text="Opens the merge tool that `merge.tool` names on each file in conflict, one after the other. When the tool reports success, Git adds the file to the staging area. In the game it opens the game's own merge panel.",
)
SCENE = [
    kit.SceneFrame(art="collision", text="Two crews changed the launch plan, and it cracked in two places."),
    kit.SceneFrame(art="collision", text="You know the terminal way. Today Git opens a tool for you: one click per conflict."),
]

LAUNCH = "launch.txt"
SCOUT = "scout"
ALEX = kit.Person("Alex", "alex@example.com")
PLAN = "Launch plan\nWindow: {window}\nPilot: Cadet\nDestination: Base 7\nCargo:\n- water\n- fuel cells\n"
START = PLAN.format(window="06:00")
OURS = PLAN.format(window="07:00") + "- oxygen\n"
THEIRS = PLAN.format(window="05:30") + "- spare antenna\n"
CARGO = ("- oxygen", "- spare antenna")
MARKER = "<<<<<<<"
MERGE = f"git merge --no-edit {SCOUT}"
PICKS: dict[str, tuple[kit.Keep, ...]] = {LAUNCH: ("theirs", "both")}
"""The merge panel's clicks the last hint asks for: Alex's launch time, then both cargo lines."""
AGAIN = "To answer again: `git merge --abort`, then `git merge --no-edit scout` and `git mergetool`."

BRIEFING = """
You moved the launch to 07:00 and packed oxygen, on `main`. Alex, on `scout`, moved it to 05:30
and packed a spare antenna: the launch window closes early. Bring `scout` into `main`, and answer
both conflicts with a merge tool: Alex's launch time, and both cargo lines.

The mission is done when `main`'s last commit holds `scout`'s work, launches at 05:30 and packs
both the oxygen and the spare antenna, with no conflict markers.
"""

HINTS = [
    "`git merge --no-edit scout` stops with two conflicts in `launch.txt`. Then `git mergetool` opens the game's merge panel.",
    "In the panel, keep Alex's launch time and Both cargo lines, then press Write. The tool adds `launch.txt` itself, so the next lines are `git status` and `git commit --no-edit`.",
    "Every line of the mission, in order. In the panel, pick Alex's, then Both, then press Write:\n\n    $ git merge --no-edit scout\n    $ git mergetool\n    $ git status\n    $ git commit --no-edit",
]

DEBRIEF = """
`git mergetool` opened a merge tool on the file in conflict: here, the game's panel. You answered
each conflict on its own, Write saved the file, and when the tool finished, Git added `launch.txt`
to the staging area (the cargo dock) itself. `git commit --no-edit` finished the merge, as in 7-3.
`git restore --theirs` could not have done it: it keeps one side for the whole file.

Real tools differ. The panel is a training tool: one click per conflict, made to learn with. At
work, people answer conflicts in their editor's merge view or in a merge tool. In VS Code you
usually open its merge editor from the conflicted file or from the Source Control view; it can
also be set as git's merge tool. A tool such as Meld is what `git mergetool` opens once you set
your own: `git config merge.tool meld`. Real tools show more of the file and let you write an
answer line by line, for when neither side alone is right.

The game also hides two things git does on its own. It keeps the file as it was, markers and all,
as `launch.txt.orig` after each answer, until you delete it. And when no tool is set, it picks one
it finds and asks "Hit return to start merge resolution tool" before opening it.

The terminal way from 7-3 works everywhere, with or without a tool, and so does
`git merge --abort`.

Commands to keep:

    $ git mergetool   # open the merge tool on each file in conflict; it adds each answer
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_STARTED = "Bring `scout` in: `git merge --no-edit scout`."
CONFLICT = "The merge stopped: `launch.txt` has two conflicts."
NOT_ANSWERED = "Answer both conflicts: `git mergetool` opens the merge panel. Keep Alex's launch time and both cargo lines."
MARKERS = f"`launch.txt` is in the staging area with conflict markers still in it. {AGAIN}"
LATE = f"`launch.txt` launches at 07:00, after the window closes. {AGAIN}"
ONE_CARGO = f"Only one cargo line made it into `launch.txt`; the trip needs both. {AGAIN}"
OTHER = f"`launch.txt` should launch at 05:30 and pack both the oxygen and the spare antenna. {AGAIN}"
ANSWERED = "`launch.txt` launches at 05:30 and packs both, with no markers."
NOT_LOOKED = "See what the tool did: `git status`."
LOOKED = "`launch.txt` is in the staging area (the cargo dock): the tool added it for you."
NOT_COMMITTED = "Finish the merge: `git commit --no-edit`."
WRONG_COMMITTED = "`main`'s last commit does not launch at 05:30 with both cargo lines. Leave the mission and start it again, and pick Alex's time and Both."
DONE = "`main`'s last commit holds `scout`'s work, launches at 05:30 and packs both."
ANSWER_FIRST = "Git cannot commit while a file is in conflict. Answer it first: `git mergetool`."
ONE_SIDE = f"That keeps one side of the whole file, so a line of the other side went too. Here each conflict needs its own answer. {AGAIN}"

REACTIONS = [
    kit.ReactionRule(line=r"git commit\b", mood="err", text=ANSWER_FIRST, outcome="failed", repository=True),
    kit.ReactionRule(line=r"git restore (--ours|--theirs)\b", mood="warn", text=ONE_SIDE, outcome="ok", repository=True),
]


def _merging(lab: kit.Lab) -> bool:
    """
    Tell whether the merge of ``scout`` has started: paused, or finished into ``main``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    bool
        True while a merge is paused, or once ``main`` holds ``scout``.
    """
    paused = kit.snapshot(lab.project)["operation"] == "merge"
    return paused or _joined(lab)


def _joined(lab: kit.Lab) -> bool:
    """
    Tell whether ``main`` holds ``scout`` and no merge is paused.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    bool
        True once the merge is committed.
    """
    scout = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"refs/heads/{SCOUT}").stdout.strip()
    paused = kit.snapshot(lab.project)["operation"] == "merge"
    return bool(scout) and not paused and kit.is_ancestor(lab.project, scout, "refs/heads/main")


def _kind(text: str | None) -> str:
    """
    Name what a version of the launch plan says.

    Parameters
    ----------
    text : str | None
        The version's content, or None when there is none.

    Returns
    -------
    str
        ``"right"`` for Alex's time and both cargo lines (in either order, trailing blank space
        ignored), ``"markers"`` for a version that still holds conflict markers, ``"late"`` for
        your 07:00, ``"one cargo"`` for 05:30 without both cargo lines, ``"other"`` for anything else.
    """
    lines = [line.rstrip() for line in (text or "").rstrip().splitlines()]
    head = PLAN.format(window="05:30").splitlines()
    kind = "other"
    if text is not None and MARKER in text:
        kind = "markers"
    elif lines[: len(head)] == head and sorted(lines[len(head) :]) == sorted(CARGO):
        kind = "right"
    elif "Window: 07:00" in lines:
        kind = "late"
    elif "Window: 05:30" in lines:
        kind = "one cargo"
    return kind


def _blob_text(lab: kit.Lab, blob: str | None) -> str | None:
    """
    Read a blob's content.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    blob : str | None
        The blob's id, or None.

    Returns
    -------
    str | None
        Its content, or None without a blob.
    """
    return kit.git_run(lab.project, "cat-file", "blob", blob).stdout if blob else None


def watch_merge(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the merge of ``scout`` has started.

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
    message = CONFLICT if _merging(lab) else NOT_STARTED
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == CONFLICT, message)


def watch_answer(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``launch.txt`` is no longer in conflict and the staging area holds the right answer.

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
        The step's verdict; the merge comes first.
    """
    merging = watch_merge(lab, state, typed)
    entry = next((entry for entry in kit.snapshot(lab.project)["files"] if entry["path"] == LAUNCH), None)
    message = NOT_ANSWERED
    if entry is not None and not entry["conflicted"]:
        kind = _kind(_blob_text(lab, entry["index"]))
        message = {"right": ANSWERED, "markers": MARKERS, "late": LATE, "one cargo": ONE_CARGO}.get(kind, OTHER)
    verdict = kit.Verdict(message == ANSWERED, message)
    return verdict if merging.solved else merging


def watch_status(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git status`` worked after the answer was added (by the tool or by ``git add``), or once the merge is committed.

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
        The step's verdict; the answer comes first.
    """
    answered = watch_answer(lab, state, typed)
    looked = kit.typed(kit.after(typed, r"git (mergetool|add)\b"), r"git status\b", "ok") or _joined(lab)
    verdict = kit.Verdict(looked, LOOKED if looked else NOT_LOOKED)
    return verdict if answered.solved else answered


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``main``'s last commit holds ``scout`` in its history and the right launch plan.

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
        The step's verdict; the steps before come first while the merge is paused.
    """
    looked = watch_status(lab, state, typed)
    joined = _joined(lab)
    message = NOT_COMMITTED
    if joined:
        committed = kit.git_run(lab.project, "show", f"refs/heads/main:{LAUNCH}").stdout
        message = DONE if _kind(committed) == "right" else WRONG_COMMITTED
    verdict = kit.Verdict(message == DONE, message)
    return verdict if joined or looked.solved else looked


QUEST: list[kit.Step] = [
    kit.WatchStep(id="merge", text="Bring `scout` into `main`.", command=MERGE, watch=watch_merge),
    kit.WatchStep(
        id="answer",
        text="Open the merge tool, and answer each conflict. In the panel, keep Alex's launch time and both cargo lines, then press Write.",
        command="git mergetool",
        watch=watch_answer,
    ),
    kit.WatchStep(id="status", text="See what the tool did.", command="git status", watch=watch_status),
    kit.WatchStep(id="commit", text="Finish the merge.", command="git commit --no-edit", watch=watch_commit),
]


def _commit(lab: kit.Lab, text: str, message: str, day: int, author: kit.Person = kit.PLAYER) -> None:
    """
    Write the launch plan and commit it on the current branch.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    text : str
        The plan's new content.
    message : str
        The commit's message.
    day : int
        The day of June 2026 it is dated.
    author : kit.Person
        Who made it; you by default.
    """
    (lab.project / LAUNCH).write_text(text)
    kit.git(lab.project, "add", LAUNCH)
    kit.git(lab.project, "commit", "-q", "-m", message, author=author, when=f"2026-06-{day:02}T09:00:00+00:00")


def setup(lab: kit.Lab) -> kit.State:
    """
    Make ``main`` launch at 07:00 with oxygen and ``scout`` at 05:30 with a spare antenna, from a plan at 06:00.

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
    _commit(lab, START, "Write the launch plan", 1)
    kit.git(lab.project, "switch", "-q", "-c", SCOUT)
    _commit(lab, THEIRS, "The window closes early: launch at 05:30, and pack a spare antenna", 2, ALEX)
    kit.git(lab.project, "switch", "-q", "main")
    _commit(lab, OURS, "Launch at 07:00 and pack oxygen", 3)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the merge is committed with the right launch plan; the quest keeps the steps before it first.

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
    return watch_commit(lab, state, typed)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order, the panel's clicks included (AUTHORING section 3.6).

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
    "merge": kit.typing(MERGE),
    "answer": kit.typing("git mergetool", PICKS),
    "status": kit.typing("git status"),
    "commit": kit.typing("git commit --no-edit"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
