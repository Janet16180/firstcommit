"""
Base 7: the boss of the mothership chapter. From a plain folder to the mothership, the debris left out.

Wave 1, mothership 4-5 (docs/drafts/chapters-3-7.md), a challenge combining liftoff (init),
cargo (staging by name), vault (commit) and mothership (remote, push). A meteorite destroyed
Base 7's computer: setup leaves its files in a plain folder, the meteorite's debris among them,
next to an empty stand-in GitHub. The goals are end states read from the repositories only, met
in any order: the folder is a repository; a commit holds the blueprint and the reactor settings
and no commit holds the debris; ``origin`` names the mothership; the mothership's ``main`` equals
yours. Debris sealed in a commit, here or on the mothership, is lost for this play.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Base 7"
DIFFICULTY = 3
XP = 300
COMMAND = "liftoff to mothership"
PAR = 6
CHALLENGE = True
CARD = kit.CommandCard(
    command="git status",
    text="Says what is staged, what changed in the working folder, and how your branch stands against its upstream. Ask it before every commit and push.",
)
SCENE = [
    kit.SceneFrame(art="meteor", text="Meteorite strike on Base 7. Its computer is gone, and its history with it."),
    kit.SceneFrame(art="alarm", text="The files survived on a backup drive, with debris from the crash. Rebuild the base and get it to the remote (the mothership)."),
]

CARGO = {"blueprint.txt": "Base 7: three domes and a landing pad\n", "reactor.cfg": "core=stable\nlimit=80\n"}
DEBRIS = "crash-dump.bin"
DEBRIS_BYTES = bytes(range(256)) * 16

BRIEFING = """
A meteorite destroyed Base 7's computer. Its files survived in this folder, and so did
`crash-dump.bin`, debris from the crash. The mothership waits, empty, at `../github.com/moonbase/project.git`.

The mission is done when the folder is a repository, a capsule holds `blueprint.txt` and
`reactor.cfg` and no capsule holds the debris, `origin` names the mothership, and the mothership's
`main` is the same as yours.
"""

HINTS = [
    "This is every chapter so far, in order: lift-off, the staging area (the cargo dock), your repository (the vault) and the remote (the mothership).",
    "A repository first; then choose the cargo by name, seal it, name the mothership and launch.",
    'Every line of the mission, in order:\n\n    $ git init\n    $ git add blueprint.txt reactor.cfg\n    $ git commit -m "Rebuild Base 7"\n    $ git remote add origin ../github.com/moonbase/project.git\n    $ git push -u origin main',
]

DEBRIEF = """
Base 7 is a repository again, its blueprint and reactor settings sealed in a capsule, and the
mothership holds the same history. The debris never left the working folder.

That is the whole loop you will use at work: `git init` (or a clone), `git add` by name,
`git commit`, `git remote add`, `git push -u`. The next chapters add branches, merges and undo.
"""

NO_REPOSITORY = "Base 7's folder is not a repository yet."
REPOSITORY = "Base 7's folder is a repository."
SEALED = "A capsule holds the blueprint and the reactor settings, and no capsule holds the debris."
NOT_SEALED = "No capsule holds both `blueprint.txt` and `reactor.cfg` yet."
DEBRIS_SEALED = "`crash-dump.bin` is sealed in a capsule. Taking a commit back comes in a later chapter: start the mission again."
CONTACT = "`origin` names the mothership."
NO_CONTACT = "Your repository does not know the mothership as `origin` at `../github.com/moonbase/project.git` yet."
LAUNCHED = "The mothership's `main` is the same as yours."
NOT_LAUNCHED = "The mothership's `main` is not the same as yours yet."
DEBRIS_LAUNCHED = "The debris is on the mothership, in a capsule of its `main`. Start the mission again."


def _exists(lab: kit.Lab) -> bool:
    """
    Tell whether Base 7's folder holds a repository.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    bool
        True once ``git init`` made it one.
    """
    return kit.snapshot(lab.project)["exists"]


def watch_repository(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the folder is a repository.

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
        The goal's verdict.
    """
    exists = _exists(lab)
    return kit.Verdict(exists, REPOSITORY if exists else NO_REPOSITORY)


def watch_capsule(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the last commit holds the blueprint and the reactor settings, and no commit the debris.

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
        The goal's verdict; lost once the debris is in a commit.
    """
    sealed = kit.in_history(lab.project, DEBRIS)
    holds = all(kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"HEAD:{name}").returncode == 0 for name in CARGO)
    message = SEALED if holds else NOT_SEALED
    if not _exists(lab):
        message = NO_REPOSITORY
    elif sealed:
        message = DEBRIS_SEALED
    return kit.Verdict(message == SEALED, message, lost=sealed)


def watch_contact(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``origin`` names the lab's GitHub.

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
        The goal's verdict.
    """
    url = kit.git_run(lab.project, "remote", "get-url", "origin").stdout.strip() if _exists(lab) else ""
    contact = kit.reaches_github(lab, lab.project, url)
    return kit.Verdict(contact, CONTACT if contact else NO_CONTACT)


def watch_launch(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the mothership's ``main`` is your ``main``, and the debris is in none of its commits.

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
        The goal's verdict; lost once the debris is on the mothership.
    """
    mine = kit.git_run(lab.project, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    theirs = kit.git_run(lab.github, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    debris = kit.in_history(lab.github, DEBRIS)
    message = LAUNCHED if mine and mine == theirs else NOT_LAUNCHED
    if debris:
        message = DEBRIS_LAUNCHED
    return kit.Verdict(message == LAUNCHED, message, lost=debris)


QUEST: list[kit.Step] = [
    kit.WatchStep(id="repository", text="Base 7's folder is a repository.", watch=watch_repository),
    kit.WatchStep(id="capsule", text="A capsule holds `blueprint.txt` and `reactor.cfg`; no capsule holds the debris.", watch=watch_capsule),
    kit.WatchStep(id="contact", text="`origin` names the mothership.", watch=watch_contact),
    kit.WatchStep(id="launch", text="The mothership's `main` is the same as yours.", watch=watch_launch),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Leave Base 7's files and the debris in a plain folder, next to an empty stand-in GitHub.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the goals read the repositories.
    """
    kit.setup_github(lab)
    lab.project.mkdir()
    for name, text in CARGO.items():
        (lab.project / name).write_text(text)
    (lab.project / DEBRIS).write_bytes(DEBRIS_BYTES)
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once every goal holds; else the first that does not, lost ones first.

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
        The verdict.
    """
    verdicts = [step.watch(lab, state, typed) for step in QUEST if isinstance(step, kit.WatchStep)]
    unmet = sorted((verdict for verdict in verdicts if not verdict.solved), key=lambda verdict: not verdict.lost)
    return unmet[0] if unmet else verdicts[-1]


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the boss like a player: every goal's action, in order (AUTHORING section 3.6).

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
        None: the level reads the repositories.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return None


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "repository": kit.typing("git init"),
    "capsule": kit.typing(f"git add {' '.join(CARGO)} && git commit -m 'Rebuild Base 7'"),
    "contact": kit.typing("git remote add origin ../github.com/moonbase/project.git"),
    "launch": kit.typing("git push -u origin main"),
}
"""The player's part of each goal, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
