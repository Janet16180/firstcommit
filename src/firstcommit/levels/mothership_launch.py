"""
Launch: ``git push`` copies commits to the mothership, and only commits.

Wave 1, mothership 4-2 (docs/drafts/chapters-3-7.md), guided, with a prediction. Setup picks up
where Make contact ended: two commits, ``origin`` naming the empty stand-in GitHub. The goals:
the first push with ``-u`` (GitHub's ``main`` equals yours, ``origin/main`` its upstream); a
prediction; an edit to the route; a push with the edit in no commit (typed after the edit: the
mothership gets nothing new); the edit committed; a plain push that sends it. The goals read
GitHub and the repository, and the lines typed only where the empty push is the lesson.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Launch"
DIFFICULTY = 1
XP = 120
COMMAND = "git push"
PAR = 6
CARD = kit.CommandCard(
    command="git push -u origin main",
    text="Sends the commits of `main` to `origin` and makes `origin/main` its upstream, so a plain `git push` knows where to go afterwards.",
)
SCENE = [
    kit.SceneFrame(art="rocket", text="A push sends your capsules up to the mothership."),
    kit.SceneFrame(art="rocket", text="Only capsules fly. An edit that is in no capsule stays on the ground."),
]

ROUTE = "route.txt"
FILES = {ROUTE: "Route: Earth, Moon, Mars\n", "journal.txt": "Day 1: landed without trouble.\n"}
STOP = "Stop: Phobos"
EDIT = rf"(echo|printf)\b.*>> *{ROUTE}"
PUSH = r"git push\b"

BRIEFING = """
Your base knows the mothership as `origin`, and the mothership is still empty. Launch your two
capsules, then find out what a push sends when your work is not in a capsule.

The mission is done when the mothership's `main` holds your commits, an edit to `route.txt` went
up only once it was committed, and you pushed it with a plain `git push`.
"""

HINTS = [
    "The first push of a branch names where it goes: `git push -u origin main`.",
    'Commit the edit before you push it: `git commit -am "Add the Phobos stop"`, then `git push`.',
]

DEBRIEF = """
`git push -u origin main` sent your two commits to the mothership and made `origin/main` the
upstream of your `main`. The push with the edit sent nothing new, because the edit was in no
commit. Once committed, a plain `git push` sent it up.

Commands to keep:

    $ git push -u origin main   # the first push of main
    $ git push                  # send new commits to the upstream
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
NO_UPSTREAM = "That push stopped: `main` has no upstream yet. The first push names it: `git push -u origin main`."
LAUNCHED = "The mothership's `main` holds your commits, and `origin/main` is the upstream of your `main`."
NOT_LAUNCHED = "Launch your commits: `git push -u origin main`."
NO_UPSTREAM_SET = "The mothership has your commits, but `main` has no upstream yet: `git push -u origin main` sets it."
EDITED = "`route.txt` has a new line, in no commit yet."
NOT_EDITED = f'Add a stop to the route: `echo "{STOP}" >> {ROUTE}`.'
FIZZLED = "The push sent nothing new: the edit is in no commit, so there was nothing to send."
NOT_FIZZLED = "Now push, with the edit still in no commit: `git push`."
COMMITTED_EDIT = "The edit is in a commit now, ahead of `origin/main`."
EDIT_NOT_COMMITTED = 'Commit the edit: `git commit -am "Add the Phobos stop"`.'
SENT = "The mothership's `main` holds the edit's commit."
NOT_SENT = "Send the new commit up: `git push`."

REACTIONS = [kit.ReactionRule(line=r"git push$", mood="info", text=NO_UPSTREAM, outcome="failed", repository=True)]

GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You edit `route.txt` and push without committing. What does the mothership receive?",
    options=("The edited `route.txt`", "Nothing new"),
    reveal="Nothing new: a push sends commits, and the edit is in none. Commit it first.",
)


def _tips(lab: kit.Lab) -> tuple[str, str]:
    """
    Give your ``main`` and GitHub's.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.

    Returns
    -------
    tuple[str, str]
        Each commit's hash, empty where the branch does not exist.
    """
    mine = kit.git_run(lab.project, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    theirs = kit.git_run(lab.github, "rev-parse", "-q", "--verify", "refs/heads/main").stdout.strip()
    return mine, theirs


def watch_launch(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once GitHub's ``main`` holds setup's commits and ``origin/main`` is your ``main``'s upstream.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: setup's commit.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    exists = kit.snapshot(lab.project)["exists"]
    upstream = kit.git_run(lab.project, "rev-parse", "--abbrev-ref", "main@{upstream}").stdout.strip()
    message = LAUNCHED
    if not exists:
        message = NO_REPOSITORY
    elif not kit.is_ancestor(lab.github, state["start"], "refs/heads/main"):
        message = NOT_LAUNCHED
    elif upstream != "origin/main":
        message = NO_UPSTREAM_SET
    return kit.Verdict(message == LAUNCHED, message)


def watch_edit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``route.txt`` differs from setup's, in the folder or in a later commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the route's blob id in setup's commit.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict; the launch comes first.
    """
    launched = watch_launch(lab, state, typed)
    route = next((file for file in kit.snapshot(lab.project)["files"] if file["path"] == ROUTE), None)
    edited = route is not None and route["folder"] not in (None, state["route"])
    verdict = kit.Verdict(edited, EDITED if edited else NOT_EDITED)
    return verdict if launched.solved else launched


def watch_fizzle(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git push`` worked after the last line that wrote to the route.

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
        The step's verdict; the edit comes first.
    """
    edited = watch_edit(lab, state, typed)
    fizzled = kit.typed(typed, EDIT) and kit.typed(kit.after(typed, EDIT), PUSH, "ok")
    verdict = kit.Verdict(fizzled, FIZZLED if fizzled else NOT_FIZZLED)
    return verdict if edited.solved else edited


def watch_commit(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once your ``main`` holds a commit after setup's with the edited route.

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
        The step's verdict; the launch comes first.
    """
    launched = watch_launch(lab, state, typed)
    head = kit.git_run(lab.project, "rev-parse", "-q", "--verify", f"HEAD:{ROUTE}").stdout.strip()
    committed = head not in ("", state["route"])
    verdict = kit.Verdict(committed, COMMITTED_EDIT if committed else EDIT_NOT_COMMITTED)
    return verdict if launched.solved else launched


def watch_sent(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once GitHub's ``main`` holds the commit with the edit.

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
        The step's verdict; the commit comes first.
    """
    committed = watch_commit(lab, state, typed)
    route = kit.git_run(lab.github, "rev-parse", "-q", "--verify", f"refs/heads/main:{ROUTE}").stdout.strip()
    sent = route not in ("", state["route"])
    verdict = kit.Verdict(sent, SENT if sent else NOT_SENT)
    return verdict if committed.solved else committed


QUEST: list[kit.Step] = [
    kit.WatchStep(id="launch", text="Launch your commits to the mothership.", command="git push -u origin main", watch=watch_launch),
    GUESS,
    kit.WatchStep(id="edit", text="Add a stop to the route.", command=f'echo "{STOP}" >> {ROUTE}', watch=watch_edit),
    kit.WatchStep(id="fizzle", text="Push, with the edit in no commit.", command="git push", watch=watch_fizzle),
    kit.WatchStep(id="commit", text="Commit the edit.", command='git commit -am "Add the Phobos stop"', watch=watch_commit),
    kit.WatchStep(id="send", text="Send the new commit up.", command="git push", watch=watch_sent),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with two commits and ``origin`` naming an empty stand-in GitHub.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``start``: setup's last commit; ``route``: the route's blob id in it.
    """
    kit.setup_github(lab)
    kit.git(lab.root, "init", "-q", str(lab.project))
    for day, (name, text) in enumerate(FILES.items(), start=1):
        (lab.project / name).write_text(text)
        kit.git(lab.project, "add", name)
        kit.git(lab.project, "commit", "-q", "-m", f"Add {name}", when=f"2026-05-0{day}T09:00:00+00:00")
    kit.git(lab.project, "remote", "add", "origin", lab.github_url(lab.project))
    return {"start": kit.git(lab.project, "rev-parse", "HEAD").strip(), "route": kit.git(lab.project, "rev-parse", f"HEAD:{ROUTE}").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved once the edit's commit is on GitHub; the quest keeps the empty push in order.

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
    return watch_sent(lab, state, typed)


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
        None: the level reads the repositories.
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
    return GUESS.options[0]


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "launch": kit.typing("git push -u origin main"),
    "guess": guess,
    "edit": kit.typing(f'echo "{STOP}" >> {ROUTE}'),
    "fizzle": kit.typing("git push"),
    "commit": kit.typing('git commit -am "Add the Phobos stop"'),
    "send": kit.typing("git push"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
