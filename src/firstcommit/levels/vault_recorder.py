"""
Flight recorder: read the history to find the commit that changed the oxygen setting, and who made it.

Wave 1, vault 3-3 (docs/drafts/chapters-3-7.md), a situation solved by typed answers. Setup
builds six commits by four people; one of them, at a random place and by a random author, turns
the oxygen down. The first goal reads the lines typed (a ``git log`` that worked: looking is the
lesson); the second checks the hash the player found, and says what a wrong commit changed; the
level's question asks for the author. Commit messages do not give the culprit away, and one
message names the oxygen without touching its file, so only the history of the file tells.
"""

import random
import re
from collections.abc import Callable

from firstcommit import kit

TITLE = "Flight recorder"
DIFFICULTY = 2
XP = 150
COMMAND = "git log <file>"
PAR = 3
CARD = kit.CommandCard(
    command="git log <file>",
    text="Lists the commits that changed the file, newest first, each with its hash, author, date and message.",
)
SCENE = [
    kit.SceneFrame(art="alarm", text="Alarm: the oxygen level in the base is low. Someone changed the setting, some days ago."),
    kit.SceneFrame(art="chain", text="Every commit is an entry in the base's flight recorder: who changed what, and when. Git keeps them all."),
]

PEOPLE = [kit.Person("Robin Park", "robin@example.com"), kit.Person("Alex", "alex@example.com"), kit.Person("Sam Ortiz", "sam@example.com"), kit.Person("Kai Moreno", "kai@example.com")]
OXYGEN = "oxygen.cfg"
GOOD = "O2=21\n"
LOW = ("O2=17\n", "O2=16\n", "O2=18\n")
HISTORY = [
    ("Set up the base", {OXYGEN: GOOD, "crew.txt": "Robin\n", "route.txt": "Route: Earth, Moon\n"}),
    ("Add the night crew", {"crew.txt": "Robin\nAlex\n"}),
    ("Extend the route to Mars", {"route.txt": "Route: Earth, Moon, Mars\n"}),
    ("Note the oxygen check in the log", {"log.txt": "Day 4: oxygen check planned.\n"}),
    ("Add Sam and Kai to the crew", {"crew.txt": "Robin\nAlex\nSam\nKai\n"}),
    ("Write the day 6 log", {"log.txt": "Day 4: oxygen check planned.\nDay 6: quiet night.\n"}),
]
"""The base's history before the culprit is slipped in: each message and the files it writes."""
CULPRIT_MESSAGE = "Night tweaks"
LOG = r"git log\b"
HASH = re.compile(r"[0-9a-f]{4,64}")

BRIEFING = """
The oxygen alarm is ringing. `oxygen.cfg` was right when the base was set up, and since then one
commit changed it. Find that commit in the history, and who made it.

The mission is done when you have read the history with `git log`, typed the hash of the commit
that changed `oxygen.cfg`, and named its author.
"""
QUESTION = "Who made the commit that changed `oxygen.cfg`?"
PLACEHOLDER = "a name"

HINTS = [
    "`git log` lists every commit, newest first, with its hash, author, date and message.",
    "Give `git log` the file's name: `git log oxygen.cfg` lists only the commits that changed it.",
    "The newest commit `git log oxygen.cfg` lists is the one you want: its `commit` line holds the hash, its `Author` line the name.",
]

DEBRIEF = """
`git log oxygen.cfg` showed only the commits that changed the file: the one that set up the base,
and the one that turned the oxygen down. Each commit records its author, its date and its
message, so the history tells who changed what, and when.

A message can say little ("Night tweaks") or mislead; the changes themselves never do.

Commands to keep:

    $ git log              # every commit, newest first
    $ git log oxygen.cfg   # only the commits that changed this file
"""

NO_REPOSITORY = "This folder is no longer a repository: `.git` is gone. Leave the level and start it again to get it back."
READ = "That is the base's history, newest commit first: each one with its hash, author, date and message."
NOT_READ = "Read the history: type `git log`."
FOUND = "That is the commit that turned the oxygen down."
NOT_A_HASH = "Type the commit's hash as `git log` shows it, at least its first 4 characters."
NO_SUCH_COMMIT = "No commit of this base starts with those characters. Copy the hash from a `commit` line of `git log`."
SET_UP = "That commit created `oxygen.cfg` with the right setting, when the base was set up. The one you want changed the file later."
OTHER_COMMIT = "That commit did not touch `oxygen.cfg`. `git log oxygen.cfg` lists only the commits that changed it."
RIGHT_AUTHOR = "Right: that is who turned the oxygen down."
WRONG_AUTHOR = "That is not the author of that commit. Its `Author` line in `git log oxygen.cfg` names them."


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
    read = kit.typed(typed, LOG, "ok")
    return kit.Verdict(read, READ if read else NOT_READ)


def names_the_commit(lab: kit.Lab, state: kit.State, answer: str) -> kit.Verdict:
    """
    Pass for the culprit's hash, whole or abbreviated; else say what the commit named did.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state: the culprit's hash and the first commit's.
    answer : str
        What the player typed.

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    typed = answer.strip().lower()
    message = FOUND
    if not kit.snapshot(lab.project)["exists"]:
        message = NO_REPOSITORY
    elif kit.is_hash_of(typed, state["culprit"]):
        message = FOUND
    elif not _is_hash(typed):
        message = NOT_A_HASH
    elif kit.is_hash_of(typed, state["first"]):
        message = SET_UP
    elif not _is_commit(lab, typed):
        message = NO_SUCH_COMMIT
    else:
        message = OTHER_COMMIT
    return kit.Verdict(message == FOUND, message)


def _is_hash(text: str) -> bool:
    """
    Tell whether a text could be a hash git accepts.

    Parameters
    ----------
    text : str
        The player's answer, stripped and lower-cased.

    Returns
    -------
    bool
        True for 4 to 64 hexadecimal characters.
    """
    return HASH.fullmatch(text) is not None


def _is_commit(lab: kit.Lab, prefix: str) -> bool:
    """
    Tell whether a hash, whole or abbreviated, names one commit of the project.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    prefix : str
        Hexadecimal characters only (`_is_hash`), so git never reads them as an option.

    Returns
    -------
    bool
        True when git resolves them to a commit.
    """
    return kit.git_run(lab.project, "rev-parse", "--verify", "-q", f"{prefix}^{{commit}}").returncode == 0


QUEST: list[kit.Step] = [
    kit.WatchStep(id="read", text="Read the base's history.", command="git log", watch=watch_log),
    kit.AnswerStep(
        id="commit",
        text="Find the commit that changed `oxygen.cfg`.",
        question="What is its hash?",
        placeholder="a hash, such as 3f9a2c1",
        check=names_the_commit,
        command="git log oxygen.cfg",
    ),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Build the base's history with the culprit at a random place, by a random author, with a random low setting.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``culprit`` and ``first``: the culprit's and the first commit's hashes; ``author``: the
        digests of the culprit author's full name and first name, lower-cased.
    """
    rng = random.Random()
    place = rng.randrange(2, len(HISTORY))
    author = rng.choice(PEOPLE)
    history = [(message, files, PEOPLE[number % len(PEOPLE)]) for number, (message, files) in enumerate(HISTORY)]
    history.insert(place, (CULPRIT_MESSAGE, {OXYGEN: rng.choice(LOW)}, author))
    kit.git(lab.root, "init", "-q", str(lab.project))
    hashes = []
    for day, (message, files, person) in enumerate(history, start=1):
        for name, text in files.items():
            (lab.project / name).write_text(text)
        kit.git(lab.project, "add", *files)
        kit.git(lab.project, "commit", "-q", "-m", message, author=person, when=f"2026-04-{day:02}T21:30:00+00:00")
        hashes.append(kit.git(lab.project, "rev-parse", "HEAD").strip())
    names = [author.name.lower(), author.name.split()[0].lower()]
    return {"culprit": hashes[place], "first": hashes[0], "author": [kit.digest(name) for name in names]}


def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict:
    """
    Solved when the player names the culprit's author, full name or first name, in any case.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab (unused: the answer is checked against the state).
    state : kit.State
        The level's state.
    answer : str | None
        The name the player typed, or None.
    typed : kit.Typed
        The lines typed since the level started (unused).

    Returns
    -------
    kit.Verdict
        Whether the name is right.
    """
    right = answer is not None and kit.digest(" ".join(answer.lower().split())) in state["author"]
    return kit.Verdict(right, RIGHT_AUTHOR if right else WRONG_AUTHOR)


def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Play the level like a player: read the history, find the commit, then read its author.

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
        The author's name, read from the history.
    """
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state, typed)
    return kit.git(lab.project, "log", "-1", "--format=%an", "--", OXYGEN).strip()


def read_history(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Type ``git log`` in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    typed.append(kit.type_line(lab.project, "git log"))
    return None


def find_commit(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    """
    Read the newest commit that changed ``oxygen.cfg``, as ``git log oxygen.cfg`` lists it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    typed : list[kit.Command]
        The lines typed so far; the line is added.

    Returns
    -------
    str | None
        Its short hash, as the player would copy it.
    """
    typed.append(kit.type_line(lab.project, f"git log {OXYGEN}"))
    return kit.git(lab.project, "log", "-1", "--format=%h", "--", OXYGEN).strip()


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State, list[kit.Command]], str | None]] = {"read": read_history, "commit": find_commit}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
