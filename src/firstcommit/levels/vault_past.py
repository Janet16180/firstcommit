"""
Look into the past: ``git show <commit>:<file>`` prints a file exactly as a commit recorded it.

The time vault 3-4 (docs/drafts/past/3-4-script.md), guided, with a prediction. Setup builds six
commits by three people with fixed dates, so the hashes the text names are the lab's; ``fuel.txt``
changes in four of them (90%, 75%, 60%, 40%) and no message names a number. The goals read the
lines typed: the file's history (``git log fuel.txt``), the Phobos commit (``git show <hash>``)
and the file as it recorded it (``git show <hash>:fuel.txt``), each commit resolved with git, so
any name of it counts. The level's question asks what the gauge read then. Reading changes
nothing, so nothing can be lost.
"""

import re
from collections.abc import Callable

from firstcommit import kit

TITLE = "Look into the past"
DIFFICULTY = 1
XP = 100
COMMAND = "git show <commit>:<file>"
PAR = 3
PICTURES = kit.pictures("chain", past="fuel.txt", plain=True)
CARD = kit.CommandCard(
    command="git show <commit>:<file>",
    text="Prints the file exactly as that commit recorded it. Your working folder is not changed.",
)
SCENE = [
    kit.SceneFrame(art="capsule", text="The gauge says 40% tonight. The question is about a few days ago."),
    kit.SceneFrame(art="chain", text="Every commit in your repository (the vault) keeps every file as it was when the commit was made, so the answer is in there."),
]

ROBIN = kit.Person("Robin Park", "robin@example.com")
SAM = kit.Person("Sam Ortiz", "sam@example.com")
FUEL = "fuel.txt"
PHOBOS = "Log the fuel after Phobos"
PHOBOS_HASH = "ccf9485"
FUEL_LOG = [
    ("Set up the base", {FUEL: "fuel: 90%\n", "crew.txt": "Robin\n"}, ROBIN),
    ("Add Sam to the crew", {"crew.txt": "Robin\nSam\n"}, SAM),
    ("Log the fuel after the Moon", {FUEL: "fuel: 75%\n"}, ROBIN),
    ("Plan the route to Mars", {"route.txt": "Route: Moon, Mars\n"}, SAM),
    (PHOBOS, {FUEL: "fuel: 60%\n"}, kit.PLAYER),
    ("Log the fuel tonight", {FUEL: "fuel: 40%\n"}, SAM),
]
"""The base's history, oldest first: each message, the files it writes and its author."""
THEN = 60
OTHER_STOPS = (90, 75, 40)
LOG_FUEL = r"git log\b.* (\./)?fuel\.txt$"
SHOW = re.compile(r"git show ([^\s:-][^\s:]*)")

BRIEFING = """
Tonight the fuel gauge reads 40%. The captain wants to know what it read after the Phobos stop, a
few days ago. Nobody wrote it down, but the vault keeps every commit.

The mission is done when you have found the commits that changed `fuel.txt`, looked at the Phobos
commit, read `fuel.txt` as that commit recorded it, and answered the captain.
"""
QUESTION = "Answer the captain: what did the fuel gauge read after the Phobos stop?"
PLACEHOLDER = "a reading, such as 50%"

HINTS = [
    "`git log fuel.txt` lists only the commits that changed `fuel.txt`. The Phobos one says so in its message.",
    "Put the commit's hash, a colon and the file's name together: `git show <hash>:fuel.txt`. The first 7 characters of the hash are enough.",
    "Every line of the mission, in order; then answer 60%:\n\n    $ git log fuel.txt\n    $ git show ccf9485\n    $ git show ccf9485:fuel.txt",
]

DEBRIEF = """
Every commit keeps every file exactly as it was. `git log fuel.txt` found the commits that changed
the file, and `git show <hash>:fuel.txt` printed it as one of them recorded it, while your working
folder stayed as it was. The past is all still there.

In Time travel you will also bring an old version back into your folder.

Commands to keep:

    $ git log fuel.txt              # the commits that changed one file
    $ git show <hash>               # what a commit changed
    $ git show <hash>:fuel.txt      # the file as that commit recorded it
"""

LOGGED = (
    "`git log fuel.txt` skips the commits that did not touch `fuel.txt`: four of the six are left, newest first. "
    "The second is the Phobos stop. Copy the first 7 characters of its hash, the long code after `commit`: `ccf9485`."
)
NOT_LOGGED = "List only the commits that changed the fuel log: `git log fuel.txt`."
SHOWN = (
    "The change: `-` took out `75%`, `+` put in `60%`; the lines above them only say which file. That answers tonight's "
    "question, but only because the file is one line. For a whole file as it was, put a colon and the file's name after the hash."
)
NOT_SHOWN = "Look at the Phobos commit: `git show` and its hash, `ccf9485`."
READ = (
    "The fuel log exactly as the Phobos commit recorded it. Your folder still says 40%: reading the past changes nothing.\n\n"
    "Now answer the captain in the answer box: what did the gauge read after Phobos?"
)
NOT_READ = "Read the fuel log as the Phobos commit recorded it: `git show ccf9485:fuel.txt`."
RIGHT = "Right: 60% after Phobos. The captain has the answer, and the vault is just as it was."
OTHER_STOP = "That is what the gauge read at another stop. Find the commit whose message names Phobos."
NOT_A_READING = "Type the reading as `git show` printed it, such as `50%`."
SPACE_NOT_COLON = "With a space, git shows what that commit changed in `fuel.txt`. With a colon, the file itself as it was."

REACTIONS = [kit.ReactionRule(line=r"git show [^\s:-]\S* (\./)?fuel\.txt$", mood="info", text=SPACE_NOT_COLON, outcome="ok")]


def _names_phobos(lab: kit.Lab, state: kit.State, revs: list[str]) -> bool:
    """
    Tell whether any of the commits the player named is the Phobos commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the Phobos commit's hash.
    revs : list[str]
        Commits as typed, none starting with ``-``.

    Returns
    -------
    bool
        True when git resolves one of them to the Phobos commit.
    """
    resolved = [kit.git_run(lab.project, "rev-parse", "--verify", "-q", f"{rev}^{{commit}}").stdout.strip() for rev in revs]
    return state["phobos"] in resolved


def watch_log(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git log`` of ``fuel.txt`` worked.

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
    logged = kit.typed(typed, LOG_FUEL, "ok")
    return kit.Verdict(logged, LOGGED if logged else NOT_LOGGED)


def watch_show(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once a ``git show`` of the Phobos commit worked.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the Phobos commit's hash.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    shows = [SHOW.fullmatch(" ".join(command["line"].split())) for command in typed if command["status"] == 0]
    shown = _names_phobos(lab, state, [show.group(1) for show in shows if show is not None])
    return kit.Verdict(shown, SHOWN if shown else NOT_SHOWN)


def watch_file(lab: kit.Lab, state: kit.State, typed: kit.Typed) -> kit.Verdict:
    """
    Pass once ``git show <commit>:fuel.txt`` worked for the Phobos commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the Phobos commit's hash.
    typed : kit.Typed
        The lines typed since the level started.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    read = _names_phobos(lab, state, kit.shown_revs(list(typed), FUEL, "ok"))
    return kit.Verdict(read, READ if read else NOT_READ)


GUESS = kit.ChoiceStep(
    id="guess",
    text="Predict first.",
    question="You type `git show` and the Phobos commit's hash. What does it print?",
    options=("`fuel.txt` as it was then", "What that commit changed", "Every file in the project"),
    reveal=(
        "What that commit changed: its message, then the change itself, where a `-` line is what was taken out and a `+` "
        "line what was put in. To read a whole file as it was, the next step adds the file's name."
    ),
    look=(PHOBOS,),
)

QUEST: list[kit.Step] = [
    kit.WatchStep(id="log", text="Find the commits that changed the fuel log.", command="git log fuel.txt", watch=watch_log),
    GUESS,
    kit.WatchStep(id="show", text="Look at the Phobos commit.", command=f"git show {PHOBOS_HASH}", watch=watch_show, look=(PHOBOS,)),
    kit.WatchStep(id="file", text="Read the fuel log as it was then.", command=f"git show {PHOBOS_HASH}:{FUEL}", watch=watch_file, look=(PHOBOS,)),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the base's six commits, each with its author and a fixed date, so the hashes are the ones the text names.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``phobos``: the full hash of the commit that logged the fuel after Phobos.
    """
    kit.git(lab.root, "init", "-q", str(lab.project))
    for day, (message, files, person) in enumerate(FUEL_LOG, start=1):
        for name, text in files.items():
            (lab.project / name).write_text(text)
        kit.git(lab.project, "add", *files)
        kit.git(lab.project, "commit", "-q", "-m", message, author=person, when=f"2026-04-{day:02}T21:30:00+00:00")
    return {"phobos": kit.git(lab.project, "rev-parse", "HEAD~1").strip()}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved when the player types the reading after Phobos, 60, with or without ``%`` or ``fuel:``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused: the answer is checked by value).
    state : kit.State
        The level's state (unused).
    answer : str | None
        The reading the player typed, or None.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        Whether the reading is right; a reading of another stop is told apart.
    """
    reading = kit.parse_int(answer.lower().strip().removeprefix("fuel:").strip().removesuffix("%").strip()) if answer is not None else None
    message = NOT_A_READING
    if reading == THEN:
        message = RIGHT
    elif reading in OTHER_STOPS:
        message = OTHER_STOP
    return kit.Verdict(message == RIGHT, message)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: every quest step's action, in order, then read the reading.

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
        The reading after Phobos, as `git show` printed it.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return read_fuel(lab, state)


def read_fuel(lab: kit.Lab, state: kit.State) -> str:
    """
    Read the answer from the lab, changing nothing: ``fuel.txt`` as the Phobos commit recorded it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the Phobos commit's hash.

    Returns
    -------
    str
        The reading, such as ``60%``.
    """
    return kit.git(lab.project, "show", f"{state['phobos']}:{FUEL}").removeprefix("fuel:").strip()


ANSWER = read_fuel
"""How dev mode reads the answer to the question (`firstcommit.runner.Answer`)."""

QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {
    "log": kit.typing("git log fuel.txt"),
    "guess": kit.picking(GUESS.options[1]),
    "show": kit.typing(f"git show {PHOBOS_HASH}"),
    "file": kit.typing(f"git show {PHOBOS_HASH}:{FUEL}"),
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game reads it only in dev mode."""
