"""
Edits come along: an uncommitted edit is on no branch; switching carries it, and git refuses only to overwrite it.

Wave 2, branch 5-4 (docs/drafts/chapters-5-9.md), guided, with a prediction. Setup makes a
repository whose ``main`` and ``scout`` hold the same ``lights.cfg`` and different routes, and
leaves ``lights.cfg`` edited, not committed, on ``main``. The goals: on ``scout`` with the lights
edit still in the working folder; a switch that failed after the route was edited too (git
refuses, since ``route.txt`` differs on the other branch); and both edits in a commit on
``scout``, ``main`` untouched. The lights edit thrown away, or a commit on ``main``, is lost for
this play: the level says so and offers to start again.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Edits come along"
DIFFICULTY = 2
XP = 150
COMMAND = "git switch"
PAR = 4
VIEW = "history"
CARD = kit.CommandCard(
    command="git switch <branch>",
    text="Moves you onto another branch and rewrites the working folder to match it. Edits you have not committed come along; Git refuses only when the switch would overwrite one.",
)
SCENE = [
    kit.SceneFrame(art="fork", text="Two courses, `main` and `scout`. Your new lights setting sits in the working folder, not committed."),
    kit.SceneFrame(art="fork", text="A commit belongs to a branch. An edit you have not committed belongs to no branch yet."),
]

BRANCH = "scout"
LIGHTS = "lights.cfg"
ROUTE = "route.txt"
LIGHTS_FIRST = "lights=dim\n"
LIGHTS_EDITED = "lights=bright\n"
ROUTE_MAIN = "Route: Earth, Moon\n"
ROUTE_SCOUT = "Route: Earth, Moon, Mars\n"
SWITCH = r"git (switch|checkout)\b(?!.* (-c|-C|-b|-B|--create|--force-create)\b)"

BRIEFING = """
You are on `main`, and you changed the lights setting in `lights.cfg` without committing it. The
survey team needs you on `scout`, a branch with a longer route.

The mission is done when you are on `scout` with your lights edit, Git has refused a switch that
would overwrite an edit, and both your edits are in a commit on `scout`, with `main` unchanged.
"""

HINTS = [
    "`git switch scout` moves you; `git status` there shows whether your edit came along.",
    'Edit the route on `scout` with `echo "Stop at Phobos" >> route.txt`, then try `git switch main`: `route.txt` is different on `main`.',
    'Every line of the mission, in order:\n\n    $ git switch scout\n    $ echo "Stop at Phobos" >> route.txt\n    $ git switch main\n    $ git commit -am "Note the survey route"',
]

DEBRIEF = """
Your lights edit came with you to `scout`: an edit you have not committed is on no branch. It
stays in the working folder while you switch, because `lights.cfg` is the same on both branches
and the switch has nothing to overwrite.

Your route note was different. `route.txt` differs between `scout` and `main`, so going back to
`main` would have replaced your edit, and Git refused instead. It refuses only to protect an
edit, and the edit stayed where it was.

`git commit -am` put both edits in a commit on `scout`: now they belong to that branch, and
`main` never saw them. At work, commit (or throw away) your edits before you switch to someone
else's branch.

Commands to keep:

    $ git switch scout                        # move to a branch; uncommitted edits come along
    $ git commit -am "Note the survey route"  # commit them on the branch you are on
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_ON_SCOUT = "Switch to `scout`: `git switch scout`."
CARRIED = "You are on `scout`, and your lights edit came with you, still not committed."
LIGHTS_GONE = "Your lights edit is gone: it was in no commit, so nothing kept a copy. Start the mission again."
NOT_REFUSED = 'Edit the route on `scout` (`echo "Stop at Phobos" >> route.txt`), then try `git switch main`.'
REFUSED = "Git refused the switch: `route.txt` is different on the other branch, and switching would have overwritten your edit."
NOT_KEPT = 'Your edits are still on no branch. Commit both on `scout`: `git commit -am "Note the survey route"`.'
MAIN_TOUCHED = (
    "`main` has a new commit, so the edits went to the wrong branch. Taking a commit back comes in a later "
    "chapter: start the mission again."
)
KEPT = "Both edits are in a commit on `scout`, and `main` did not change."
SWITCH_REFUSED = (
    "Git refused to switch: you have an edit that is not committed, and the other branch has a different version of "
    'that file, so switching would overwrite it. Two ways out: commit it here, `git commit -am "Note the survey route"`, '
    "or throw the edit away, `git restore route.txt`."
)

REACTIONS = [
    kit.ReactionRule(line=SWITCH, mood="err", text=SWITCH_REFUSED, outcome="failed", repository=True),
]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You switch to `scout` with `lights.cfg` edited and not committed. Where does your edit go?",
    options=("It stays behind on main", "It comes with you", "Git deletes it"),
    reveal="It comes with you: an edit you have not committed belongs to no branch, so it stays in the working folder while you switch.",
)


def lights_lost(lab: kit.Lab, state: kit.State) -> bool:
    """
    Tell whether the lights edit is gone: not in the working folder and in no commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the blob id of the edited lights.

    Returns
    -------
    bool
        True when no copy of the edit is left.
    """
    in_folder = (lab.project / LIGHTS).is_file() and (lab.project / LIGHTS).read_text() == LIGHTS_EDITED
    committed = kit.git_run(lab.project, "log", "--all", "--format=%H", f"--find-object={state['lights']}").stdout.strip() != ""
    return not in_folder and not committed


def watch_carry(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once you are on ``scout`` with the lights edit still in the working folder.

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
        The step's verdict; lost once the lights edit is gone.
    """
    snap = kit.snapshot(lab.project)
    message = CARRIED
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif lights_lost(lab, state):
        message = LIGHTS_GONE
    elif snap["branch"] != BRANCH:
        message = NOT_ON_SCOUT
    return kit.Verdict(message == CARRIED, message, lost=message == LIGHTS_GONE)


def watch_refused(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a switch failed while ``route.txt`` held an edit that is not committed.

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
    snap = kit.snapshot(lab.project)
    edited = ROUTE in kit.unstaged(snap) or ROUTE in kit.staged(snap)
    refused = edited and kit.typed(typed, SWITCH, "failed")
    return kit.Verdict(refused, REFUSED if refused else NOT_REFUSED)


def watch_keep(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once both edits are in a commit on ``scout`` and ``main`` is where it started.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: ``main``'s commit and the blob ids of the edited lights and of
        ``scout``'s route before the level.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; lost once ``main`` moved or the lights edit is gone.
    """
    snap = kit.snapshot(lab.project)
    main = kit.git_run(lab.project, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip() if snap["exists"] else ""
    lights = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{BRANCH}:{LIGHTS}").stdout.strip() if snap["exists"] else ""
    route = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"{BRANCH}:{ROUTE}").stdout.strip() if snap["exists"] else ""
    message = KEPT
    if not snap["exists"]:
        message = NO_REPOSITORY
    elif main != state["main"]:
        message = MAIN_TOUCHED
    elif lights_lost(lab, state):
        message = LIGHTS_GONE
    elif lights != state["lights"] or route in ("", state["route"]):
        message = NOT_KEPT
    return kit.Verdict(message == KEPT, message, lost=message in (MAIN_TOUCHED, LIGHTS_GONE))


QUEST: list[kit.Step] = [
    GUESS,
    kit.WatchStep(id="carry", text="Move onto `scout`, and see what happens to your edit.", command=f"git switch {BRANCH}", watch=watch_carry),
    kit.WatchStep(
        id="refused",
        text="Edit the route on `scout`, then try to go back to `main`.",
        command="git switch main",
        watch=watch_refused,
    ),
    kit.WatchStep(id="keep", text="Keep both edits on `scout`: commit them there.", command='git commit -am "Note the survey route"', watch=watch_keep),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make ``main`` and ``scout`` with the same lights and different routes, and edit the lights on ``main``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``main``: its commit; ``lights``: the blob id of the edited lights; ``route``: the blob
        id of ``scout``'s route.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    (lab.project / LIGHTS).write_text(LIGHTS_FIRST)
    (lab.project / ROUTE).write_text(ROUTE_MAIN)
    kit.git(lab.project, "add", LIGHTS, ROUTE)
    kit.git(lab.project, "commit", "-q", "-m", "Set the lights and the route", when="2026-04-01T09:00:00+00:00")
    kit.git(lab.project, "switch", "-q", "-c", BRANCH)
    (lab.project / ROUTE).write_text(ROUTE_SCOUT)
    kit.git(lab.project, "commit", "-q", "-am", "Extend the survey to Mars", when="2026-04-02T09:00:00+00:00")
    kit.git(lab.project, "switch", "-q", "main")
    (lab.project / LIGHTS).write_text(LIGHTS_EDITED)
    return {
        "main": kit.git(lab.project, "rev-parse", "main").strip(),
        "lights": kit.git(lab.project, "hash-object", LIGHTS).strip(),
        "route": kit.git(lab.project, "rev-parse", f"{BRANCH}:{ROUTE}").strip(),
    }


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once both edits are committed on ``scout``, ``main`` untouched, after a refused switch.

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
        The commit's verdict (it says when the work is lost) unless no switch was refused.
    """
    kept = watch_keep(lab, state, typed)
    refused = kit.typed(typed, SWITCH, "failed")
    return kept if not kept.solved or refused else kit.Verdict(False, NOT_REFUSED)


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
    Pick the prediction most players make.

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


def note_and_switch(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type the route note, then ``git switch main``, each on its own line in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; both lines are added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    for line in ('echo "Stop at Phobos" >> route.txt', "git switch main"):
        typed.append(kit.type_line(lab.project, line))
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "guess": guess,
    "carry": kit.typing(f"git switch {BRANCH}"),
    "refused": note_and_switch,
    "keep": kit.typing('git commit -am "Note the survey route"'),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
