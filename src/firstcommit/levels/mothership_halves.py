"""
Two halves of a ship: you and Alex each finish your own part at the same time, and Git puts the pieces together.

Wave 1b, mothership 4-2b (the user's playtest decisions in docs/drafts/chapters-3-7.md), guided.
Setup builds the playground with the ship's frame on the mothership: you own ``nav.cfg``, Alex
owns ``engine.cfg``. Alex has already committed the engines, and your navigation is edited but
not committed. The goals: your half committed, then pushed; once it is pushed, a level event
has Alex push too (Alex's push needs a pull first, which joins the two halves in a merge
commit); and your ``main`` holding Alex's work, with both halves, after a pull. That pull plays
the launch moment.
"""

from collections.abc import Callable
from pathlib import Path

from firstcommit import kit

TITLE = "Two halves of a ship"
DIFFICULTY = 2
XP = 150
COMMAND = "git pull"
PAR = 3
CARD = kit.CommandCard(
    command="git pull",
    text="Brings the remote's new commits into your branch: a fetch, then a merge (or only a slide of your label when you have nothing new).",
)
SCENE = [
    kit.SceneFrame(art="orbit", text="The ship is half built. You finish the navigation; Alex, at another station, finishes the engines."),
    kit.SceneFrame(art="pull", text="Each of you sends a half to the mothership, and each brings the other's back."),
]

NAV = "nav.cfg"
ENGINE = "engine.cfg"
FRAME = {NAV: "heading=unset\n", ENGINE: "thrust=unset\n"}
YOUR_HALF = "heading=Mars\n"
ALEX_HALF = "thrust=full\n"
ROBIN = kit.Person("Robin Park", "robin@example.com")
ALEX = kit.Person("Alex", "alex@example.com")

BRIEFING = """
The ship's frame is on the mothership. You own the navigation in `nav.cfg`, and your edit is
ready but not committed. Alex owns the engines in `engine.cfg`, and is finishing them right now
at another station.

The mission is done when your navigation is committed and on the mothership, and your `main`
holds Alex's engines too: the whole ship.
"""

HINTS = [
    "Your half travels as a commit: commit `nav.cfg`, then push.",
    "Once Alex has pushed, `git pull` brings their half into your `main`.",
    'Every line of the mission, in order:\n\n    $ git commit -am "Set the navigation"\n    $ git push\n    $ git pull',
]

DEBRIEF = """
You and Alex worked at the same time, each on a different file. Your push reached the mothership
first, so Alex's push was refused until Alex pulled; that pull joined the two halves in a merge
commit with no conflict, because the changes touched different files. Your `git pull` then
brought that merge into your `main`, and both stations hold the whole ship.

That is Git's point for a team: two people, at the same time, on different parts, and Git puts
the pieces together.

Commands to keep:

    $ git commit -am "Set the navigation"   # your half, in a commit
    $ git push                              # up to the mothership
    $ git pull                              # and the other half back
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NOT_COMMITTED = 'Your navigation is not in a commit yet: `git commit -am "Set the navigation"`.'
COMMITTED = "Your navigation is in a commit, ready to travel."
NOT_PUSHED = "The mothership does not have your navigation yet: `git push`."
PUSHED = "The mothership has your navigation."
WAITING = "Alex is still finishing the engines. Wait a moment for their push."
NOT_PULLED = "Your `main` does not hold Alex's engines yet: `git pull`."
WHOLE = "Your `main` holds the whole ship: your navigation and Alex's engines."
TWO_HALVES = (
    "The whole ship is in your station: your navigation and Alex's engines. Two people worked at the same time on "
    "different parts, and Git put the pieces together."
)

REACTIONS = [
    kit.ReactionRule(line=r"git pull\b", mood="ok", text=TWO_HALVES, outcome="ok", event="branch-moved", moment="launch"),
]


def alex_pushes(lab: kit.Lab, state: kit.State) -> None:
    """
    Have Alex pull your half in, which joins the two halves in a merge commit, and push, with the playground's buttons.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    """
    for button in ("pull-no-rebase", "push"):
        kit.press(lab, "alex", button)


EVENTS = [kit.LevelEvent(id="alex-pushes", run=alex_pushes, goal="push")]


def _file(folder: Path, ref: str, name: str) -> str:
    """
    Read a file as a branch's last commit holds it.

    Parameters
    ----------
    folder : Path
        The repository.
    ref : str
        The branch's full name.
    name : str
        The file.

    Returns
    -------
    str
        Its content, or empty when there is none.
    """
    return kit.git_run(folder, "show", f"{ref}:{name}").stdout


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds your navigation.

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
    committed = _file(lab.project, "refs/heads/main", NAV) == YOUR_HALF
    message = COMMITTED if committed else NOT_COMMITTED
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    return kit.Verdict(message == COMMITTED, message)


def watch_push(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``main`` holds your navigation.

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
        The step's verdict; your commit comes first.
    """
    committed = watch_commit(lab, state, typed)
    pushed = _file(lab.github, "refs/heads/main", NAV) == YOUR_HALF
    verdict = kit.Verdict(pushed, PUSHED if pushed else NOT_PUSHED)
    return verdict if committed.solved or pushed else committed


def watch_pull(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds Alex's engines and your navigation.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: Alex's commit.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict; your push comes first.
    """
    pushed = watch_push(lab, state, typed)
    alex_waiting = kit.git_run(lab.teammate, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip() == state["alex"]
    whole = _file(lab.project, "refs/heads/main", NAV) == YOUR_HALF and _file(lab.project, "refs/heads/main", ENGINE) == ALEX_HALF
    message = WHOLE if whole else NOT_PULLED
    if alex_waiting and not whole:
        message = WAITING
    verdict = kit.Verdict(message == WHOLE, message)
    return verdict if pushed.solved else pushed


QUEST: list[kit.Step] = [
    kit.WatchStep(id="commit", text="Commit your half of the ship.", command='git commit -am "Set the navigation"', watch=watch_commit),
    kit.WatchStep(id="push", text="Send your half to the mothership.", command="git push", watch=watch_push),
    kit.WatchStep(id="pull", text="Bring Alex's half into your `main`.", command="git pull", watch=watch_pull),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground with the ship's frame, Alex's engines committed in Alex's clone, and your navigation edited.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``alex``: Alex's commit of the engines, not pushed yet.
    """
    kit.setup_playground(lab)
    for name, text in FRAME.items():
        (lab.project / name).write_text(text)
    kit.git(lab.project, "add", *FRAME)
    kit.git(lab.project, "commit", "-q", "-m", "Lay down the ship's frame", author=ROBIN, when="2026-06-20T09:00:00+00:00")
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    (lab.teammate / ENGINE).write_text(ALEX_HALF)
    kit.git(lab.teammate, "commit", "-q", "-am", "Set the engines", author=ALEX, when="2026-06-21T09:00:00+00:00")
    (lab.project / NAV).write_text(YOUR_HALF)
    return {"alex": kit.git(lab.teammate, "rev-parse", "HEAD").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once your ``main`` holds the whole ship; the quest keeps your push first.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    answer : str | None
        Ignored: the level reads the repositories.
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
    Play the level like a player: every quest step's action, in order, with Alex's push after yours.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state.
    typed : list[kit.Command]
        The lines typed so far; each line typed here is added.

    Returns
    -------
    str | None
        None: the level reads the repositories.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
        for event in EVENTS:
            if event.goal == quest_step.id:
                event.run(lab, state)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "commit": kit.typing('git commit -am "Set the navigation"'),
    "push": kit.typing("git push"),
    "pull": kit.typing("git pull"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
