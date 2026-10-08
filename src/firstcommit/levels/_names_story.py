"""
The Name tags sector's one continuing story, rebuilt by each level's setup up to where it starts.

Each level starts where the last one ended (docs/drafts/sector5/plan.md), with the same commits:
every commit here has a fixed date, as GitHub's first one has (`kit.setup_playground`), so a
commit has the same hash in every level that holds it. The commits the player makes in a level
are rebuilt the same way for the levels after it. A helper module, not a level: its name starts
with ``_``.
"""

from firstcommit import kit

ROUTE = "route.txt"
CREW = "crew.txt"
NOTES = "notes.txt"
OLD_NAME = "test-run"
FIRST_ROUTE = "first-route"
NOTES_WITH_FUEL = "Notes\nFuel: 80%\n"
"""``notes.txt`` once the fuel level is noted: GitHub's first line, then the note."""
FUEL_MESSAGE = "Note the fuel level"
ALEX_FIX = [
    "git pull -q",
    "printf 'Route: Moon, Phobos\\n' > route.txt",
    'GIT_AUTHOR_DATE=2026-06-04T09:00:00+00:00 GIT_COMMITTER_DATE=2026-06-04T09:00:00+00:00 git commit -q -am "Fix the route"',
    "git push -q",
]
"""Alex's lines in Alex's clone when the fuel note reaches the mothership: pull it, fix the route, push."""


def _commit(lab: kit.Lab, name: str, text: str, message: str, day: int) -> None:
    """
    Write one file in your clone and commit it as the player, on a fixed day of June 2026.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    name : str
        The file.
    text : str
        Its whole content.
    message : str
        The commit's message.
    day : int
        The day of June 2026.
    """
    (lab.project / name).write_text(text)
    kit.git(lab.project, "add", name)
    kit.git(lab.project, "commit", "-q", "-m", message, author=kit.PLAYER, when=f"2026-06-{day:02}T09:00:00+00:00")


def name_tags(lab: kit.Lab) -> None:
    """
    Build 5-1's start: three commits on ``main``, pushed, ``test-run`` on the first, and the fuel level noted but not committed.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.
    """
    kit.setup_playground(lab)
    _commit(lab, ROUTE, "Route: Moon\n", "Plot the route", 1)
    _commit(lab, CREW, "Crew: Ana, Alex\n", "Add the crew list", 2)
    kit.git(lab.project, "push", "-q")
    kit.git(lab.teammate, "pull", "-q")
    kit.git(lab.project, "branch", OLD_NAME, "main~2")
    (lab.project / NOTES).write_text(NOTES_WITH_FUEL)


def any_commit(lab: kit.Lab) -> None:
    """
    Build 5-2's start: 5-1's end, then the ``git pull`` it ended on, so ``main`` is on Alex's route fix.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.
    """
    name_tags(lab)
    _commit(lab, NOTES, NOTES_WITH_FUEL, FUEL_MESSAGE, 3)
    kit.git(lab.project, "push", "-q")
    for line in ALEX_FIX:
        kit.type_line(lab.teammate, line)
    kit.git(lab.project, "pull", "-q")


def experiments(lab: kit.Lab) -> None:
    """
    Build 5-3's start: 5-2's end, with ``bright-lights`` made yesterday with its commit, and ``engine.txt`` waiting in the folder, on ``main``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.
    """
    any_commit(lab)
    kit.git(lab.project, "branch", "-d", OLD_NAME)
    kit.git(lab.project, "branch", FIRST_ROUTE, "main~3")
    kit.git(lab.project, "switch", "-q", "-c", "bright-lights")
    _commit(lab, "lights.txt", "lights=bright\n", "Try bright lights", 5)
    kit.git(lab.project, "switch", "-q", "main")
    (lab.project / "engine.txt").write_text("engine=quiet\n")


def one_step(lab: kit.Lab) -> None:
    """
    Build 5-4's start: 5-3's end (``quiet-engine`` with its commit), back on ``main`` with ``dim.txt`` waiting in the folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.
    """
    experiments(lab)
    kit.git(lab.project, "switch", "-q", "-c", "quiet-engine")
    _commit(lab, "engine.txt", "engine=quiet\n", "Try a quiet engine", 6)
    kit.git(lab.project, "switch", "-q", "main")
    (lab.project / "dim.txt").write_text("lights=dim\n")
