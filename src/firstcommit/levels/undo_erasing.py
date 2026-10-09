"""
Deleting isn't erasing: a commit that removes a file is a new commit without it, and the commit before still holds the file.

Time travel 8-3 (docs/drafts/past/8-3-script.md), guided, with a prediction. Setup builds the
playground: *Plot the route* and *Add the crew list*, then your *Add the airlock keys* (the
password Stowaway kept out of a commit) and *Remove the keys*, both pushed, and Alex pulled. The
goals read the lines typed: the history, ``git show HEAD:keys.txt`` (git's fatal answer is the
expected one), ``git show HEAD~1:keys.txt`` (the commit resolved with git, so any name of it
counts), ``git log --oneline keys.txt`` (failing on purpose: the file is not in the folder) and
``git log --oneline -- keys.txt``. The level's question asks for the password to change, kept as
digests. Reading changes nothing, so nothing can be lost.
"""

from collections.abc import Callable

from firstcommit import kit

TITLE = "Deleting isn't erasing"
DIFFICULTY = 2
XP = 150
COMMAND = "git show HEAD~1:<file>"
PAR = 5
CARD = kit.CommandCard(
    command="git show HEAD~1:<file>",
    text="Prints the file as the commit before `HEAD` recorded it, even when a later commit removed it.",
)
SCENE = [
    kit.SceneFrame(art="conveyor", text="Back in the staging area (the cargo dock), you kept a password out of a commit with `git restore --staged`."),
    kit.SceneFrame(art="chain", text="Last night one got in: `keys.txt`, with the airlock password. You removed it in the next commit and pushed both, and Alex has pulled."),
]

KEYS = "keys.txt"
KEYS_TEXT = "airlock password: orion-7\n"
KEYS_ADDED = "Add the airlock keys"
HISTORY = [("route.txt", "Route: Moon\n", "Plot the route"), ("crew.txt", "Crew: Ana, Alex\n", "Add the crew list")]
"""The playground's history before the keys: each file, its text and the commit's message."""
PICTURES = kit.pictures("chain", mothership=True, alex=True, past=KEYS, quiet=["guess", "head", "before", "try", "trail"])
LOG = r"git log\b"
LOG_KEYS = r"git log\b.* (\./)?keys\.txt$"
LOG_KEYS_DASHED = r"git log\b.* -- (\./)?keys\.txt$"

BRIEFING = """
Last night a commit took the airlock keys by mistake, so you removed them in the next commit. Both
went up to the remote (the mothership), and Alex has pulled. The captain asks: is the airlock
password safe?

The mission is done when you have read the history, looked for `keys.txt` in the newest commit
and in the one before, found every commit that touched it, and named the password to change.
"""
QUESTION = "The captain will change the airlock password now, and needs to know which one leaked. What is the password to change?"
PLACEHOLDER = "the password"

HINTS = [
    "`git show HEAD:keys.txt` reads the file in the newest commit; `HEAD~1` is the commit before it.",
    "For a file that is no longer in your folder, put `--` before its name: `git log --oneline -- keys.txt`.",
    "Every line of the mission, in order; then answer orion-7:\n\n"
    "    $ git log --oneline\n    $ git show HEAD:keys.txt\n    $ git show HEAD~1:keys.txt\n    $ git log --oneline keys.txt\n    $ git log --oneline -- keys.txt",
]

DEBRIEF = """
Removing `keys.txt` made a new commit without it; the commit before still holds the file as it
was. `git show HEAD~1:keys.txt` read it, and `git log -- keys.txt` found every commit that touched
it. Once a secret is committed and pushed, it is leaked: change the secret. The real fix comes
before the commit, as in Stowaway: keep it out of the staging area.

Commands to keep:

    $ git show HEAD~1:keys.txt            # a file as the commit before HEAD recorded it
    $ git log --oneline -- keys.txt       # every commit that touched a file, even a deleted one
"""

LOGGED = "*Remove the keys* on top; *Add the airlock keys* just below. Both are on the mothership and at Alex's station: look at the pins."
NOT_LOGGED = "Read the history first: `git log --oneline`."
NOT_IN_HEAD = "Right, as expected: `HEAD` is the newest commit, today's files, and it has no `keys.txt`. That part of the fix worked."
NOT_HEAD = "Look for `keys.txt` in the newest commit: `git show HEAD:keys.txt`."
FOUND = (
    "`HEAD~1` means one commit before `HEAD`: here, *Add the airlock keys*. There is the password, exactly as it was committed.\n\n"
    "The mothership has this commit, and so does Alex: see the pins. Anyone who clones the project later gets it too, and can type the same line."
)
NOT_FOUND = "Look in the commit before the newest one: `git show HEAD~1:keys.txt`."
DASHES = "A file that is no longer in your folder needs `--` before its name, as git's last line says."
NOT_TRIED = "List the commits that touched the keys: `git log --oneline keys.txt`."
TRAIL = (
    "Two commits touched `keys.txt`: the one that added it and the one that removed it.\n\n"
    "So a later commit cannot remove what an earlier commit recorded. The password reached the mothership: treat it as "
    "leaked, and change it. Rewriting history can hide it from future copies, but not from anyone who already pulled it, so "
    "you still change the password. That is why, in Stowaway, the keys never went into a commit at all.\n\n"
    "Now answer the captain in the answer box: which password leaked?"
)
NOT_TRAIL = "Put `--` before the file's name: `git log --oneline -- keys.txt`."
RIGHT = "Right: `orion-7` leaked. The captain changes it now, and the old one opens nothing."
WRONG = "That is not what `keys.txt` held. Read it again with `git show HEAD~1:keys.txt`."
TOO_FAR = "Two commits back is before the keys were added: that commit has no `keys.txt`. Try one back."

REACTIONS = [kit.ReactionRule(line=r"git show HEAD~2:(\./)?keys\.txt$", mood="info", text=TOO_FAR, outcome="failed")]


def _read(lab: kit.Lab, typed: kit.Typed, outcome: kit.Outcome) -> list[str]:
    """
    Give the commits the player read ``keys.txt`` in with ``git show <rev>:keys.txt``, as git resolves them now.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    typed : kit.Typed
        The lines typed since the level started.
    outcome : kit.Outcome
        How the line must have ended.

    Returns
    -------
    list[str]
        Their full hashes, empty for a name git does not know.
    """
    revs = kit.shown_revs(list(typed), KEYS, outcome)
    return [kit.git_run(lab.project, "rev-parse", "--verify", "-q", f"{rev}^{{commit}}").stdout.strip() for rev in revs]


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` worked.

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
    logged = kit.typed(typed, LOG, "ok")
    return kit.Verdict(logged, LOGGED if logged else NOT_LOGGED)


def watch_head(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the player looked for ``keys.txt`` in the newest commit, which git answers has none.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the hash of the commit that removed the keys.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    looked = state["removed"] in _read(lab, typed, "failed")
    return kit.Verdict(looked, NOT_IN_HEAD if looked else NOT_HEAD)


def watch_before(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the player read ``keys.txt`` in the commit that added it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the hash of the commit that added the keys.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    found = state["added"] in _read(lab, typed, "ok")
    return kit.Verdict(found, FOUND if found else NOT_FOUND)


def watch_try(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once the player asked ``git log`` for ``keys.txt``, with or without ``--``.

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
    tried = kit.typed(typed, LOG_KEYS)
    return kit.Verdict(tried, DASHES if tried else NOT_TRIED)


def watch_trail(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git log -- keys.txt`` worked.

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
    found = kit.typed(typed, LOG_KEYS_DASHED, "ok")
    return kit.Verdict(found, TRAIL if found else NOT_TRAIL)


GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="`keys.txt` is gone from your folder and from the newest commit. Can anyone with this history still read the password?",
    options=("Yes", "No"),
    reveal="Yes. Removing the file made a new commit without it. The commit before was not changed: it still holds `keys.txt` as it was. Look.",
)

QUEST: list[kit.Step] = [
    kit.WatchStep(id="log", text="Read the history.", command="git log --oneline", watch=watch_log),
    GUESS,
    kit.WatchStep(id="head", text="Look for the keys in the newest commit.", command="git show HEAD:keys.txt", watch=watch_head, look=("HEAD",)),
    kit.WatchStep(id="before", text="Look in the commit before it.", command="git show HEAD~1:keys.txt", watch=watch_before, look=(KEYS_ADDED,)),
    kit.WatchStep(id="try", text="List the commits that touched the keys.", command="git log --oneline keys.txt", watch=watch_try),
    kit.WatchStep(id="trail", text="Tell git that `keys.txt` is a file.", command="git log --oneline -- keys.txt", watch=watch_trail),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the playground with the route and the crew list, then the keys added and removed, pushed and pulled by Alex.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``added`` and ``removed``: the hashes of the commits that added and removed the keys;
        ``password``: the digests of the answers accepted, lower-cased.
    """
    kit.setup_playground(lab)
    for day, (name, text, message) in enumerate(HISTORY, start=1):
        (lab.project / name).write_text(text)
        kit.git(lab.project, "add", name)
        kit.git(lab.project, "commit", "-q", "-m", message, author=kit.PLAYER, when=f"2026-06-0{day}T09:00:00+00:00")
    (lab.project / KEYS).write_text(KEYS_TEXT)
    kit.git(lab.project, "add", KEYS)
    kit.git(lab.project, "commit", "-q", "-m", KEYS_ADDED, author=kit.PLAYER, when="2026-07-02T21:00:00+00:00")
    kit.git(lab.project, "rm", "-q", KEYS)
    kit.git(lab.project, "commit", "-q", "-m", "Remove the keys", author=kit.PLAYER, when="2026-07-02T21:05:00+00:00")
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    line = KEYS_TEXT.strip()
    return {
        "added": kit.git(lab.project, "rev-parse", "HEAD~1").strip(),
        "removed": kit.git(lab.project, "rev-parse", "HEAD").strip(),
        "password": [kit.digest(line), kit.digest(line.split(": ")[1])],
    }


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved when the player names the password that leaked, alone or as the whole line, in any case.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused: the answer is checked against the state).
    state : kit.State
        The level's state.
    answer : str | None
        What the player typed, or None.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        Whether the password is right.
    """
    right = answer is not None and kit.digest(" ".join(answer.lower().split())) in state["password"]
    return kit.Verdict(right, RIGHT if right else WRONG)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order, then read the password.

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
        The password, as the commit before ``HEAD`` recorded it.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return read_password(lab, state)


def read_password(lab: kit.Lab, state: kit.State) -> str:
    """
    Read the answer from the lab, changing nothing: the password in the commit that added the keys.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the hash of the commit that added the keys.

    Returns
    -------
    str
        The password, such as ``orion-7``.
    """
    return kit.git(lab.project, "show", f"{state['added']}:{KEYS}").strip().split(": ")[-1]


ANSWER = read_password
"""How dev mode reads the answer to the question (`firstcommit.runner.Answer`)."""

QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "log": kit.typing("git log --oneline"),
    "guess": kit.picking(GUESS.options[0]),
    "head": kit.typing("git show HEAD:keys.txt"),
    "before": kit.typing("git show HEAD~1:keys.txt"),
    "try": kit.typing("git log --oneline keys.txt"),
    "trail": kit.typing("git log --oneline -- keys.txt"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
