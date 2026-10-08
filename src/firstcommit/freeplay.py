"""
The free playground: its starting points, and the lab it is played in.

Free play has no goals: the player picks a starting point, and the playground builds it in its own
lab, ``<home>/playground``, apart from the levels' labs, so a level started meanwhile leaves it as it
was and a playground start leaves the level's lab alone. Every start is built with fixed dates, so
it is the same commits, with the same hashes, every time. A start with a mothership is the
two-person playground (`firstcommit.playground.setup`) plus the start's own commits: GitHub is
``origin`` at ``../github.com/moonbase/project.git``, your clone is the lab's project and Alex's its
teammate folder, and the files are ``README.md``, ``notes.txt``, ``route.txt`` and ``crew.txt``.
The field guide's "Try it" commands rely on these names.
"""

from collections.abc import Callable
from dataclasses import dataclass

from firstcommit import gitcmd, playground, save
from firstcommit.gitcmd import PLAYER
from firstcommit.lab import Lab
from firstcommit.records import Language, PlaygroundView, StartId
from firstcommit.termlab import sandbox

ALEX = playground.ALEX
CHECKLIST = "checklist.txt"
CHECKLIST_TEXT = (
    "LAUNCH CHECKLIST\n1. Seal the hatch\n2. Fuel tanks: full\n3. Check the radio\n4. Course: Mars\n"
    "5. Music: off\n6. Shields: off\n7. Gloves on\n8. Snack: crackers\n9. Wave goodbye to base\n"
)
"""The launch checklist of the Conflict start, as you both had it before either changed it."""
YOUR_CHECKLIST = CHECKLIST_TEXT.replace("Shields: off", "Shields: on").replace("Course: Mars", "Course: the Moon")
ALEX_CHECKLIST = (
    CHECKLIST_TEXT.replace("Fuel tanks: full", "Fuel tanks: half").replace("Course: Mars", "Course: Jupiter").replace("Snack: crackers", "Snack: space noodles")
)


@dataclass(frozen=True)
class Start:
    """
    One starting point of the free playground.

    Attributes
    ----------
    title : dict[Language, str]
        Its name in the picker and the header.
    blurb : dict[Language, str]
        One line on the picker's card saying what it holds.
    banner : dict[Language, str]
        The one suggestion your terminal prints first; the only guidance free play gives.
    view : PlaygroundView
        The view it opens on; never ``graph``.
    mothership : bool
        Whether it has a stand-in GitHub, and so Alex: without one there is no Alex to show.
    alex : bool
        Whether Alex's terminal is shown at first: only in the starts about two people.
    uses : tuple[str, ...]
        The chapters whose commands it uses, by id, named in the picker; none locks it.
    setup : Callable[[Lab], None]
        Builds it in an empty lab.
    """

    title: dict[Language, str]
    blurb: dict[Language, str]
    banner: dict[Language, str]
    view: PlaygroundView
    mothership: bool
    alex: bool
    uses: tuple[str, ...]
    setup: Callable[[Lab], None]


def _commit(folder: str, lab: Lab, files: dict[str, str], message: str, when: str, author: gitcmd.Person = PLAYER) -> None:
    """
    Write files in a clone and commit them, on a fixed date.

    Parameters
    ----------
    folder : str
        ``"project"`` for yours, ``"teammate"`` for Alex's.
    lab : Lab
        The playground's lab.
    files : dict[str, str]
        Each file's new text, by name.
    message : str
        The commit's message.
    when : str
        Its date, as ISO 8601.
    author : gitcmd.Person
        Its author and committer.
    """
    clone = lab.project if folder == "project" else lab.teammate
    for name, text in files.items():
        (clone / name).write_text(text)
    gitcmd.output(clone, "add", *files)
    gitcmd.output(clone, "commit", "--quiet", "-m", message, author=author, when=when)


def _empty(lab: Lab) -> None:
    """
    Build Empty folder: ``README.md`` and ``notes.txt`` in your folder, with no repository and no mothership.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    lab.project.mkdir()
    for name, line in playground.FIRST_LINES.items():
        (lab.project / name).write_text(line + "\n")


def _shared(lab: Lab) -> None:
    """
    Build the history every start with a mothership shares: three commits on ``main``, pushed, and Alex's clone up to date.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    playground.setup(lab)
    _commit("project", lab, {"route.txt": "Route: Moon\n"}, "Plot the route", "2026-06-01T09:00:00+00:00")
    _commit("project", lab, {"crew.txt": "Crew: Ana, Alex\n"}, "Add the crew list", "2026-06-02T09:00:00+00:00")
    gitcmd.output(lab.project, "push", "--quiet")
    gitcmd.output(lab.teammate, "pull", "--quiet")


def _changes(lab: Lab) -> None:
    """
    Build Uncommitted changes: a branch ``bright-lights`` with a commit of its own, and you on ``main`` with ``notes.txt`` edited.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    _shared(lab)
    gitcmd.output(lab.project, "switch", "--quiet", "-c", "bright-lights")
    _commit("project", lab, {"lights.txt": "lights=bright\n"}, "Try bright lights", "2026-06-05T09:00:00+00:00")
    gitcmd.output(lab.project, "switch", "--quiet", "main")
    with (lab.project / "notes.txt").open("a") as notes:
        notes.write("Fuel: 80%\n")


def _branches(lab: Lab) -> None:
    """
    Build Two branches: ``bright-lights`` and ``quiet-engine``, each one commit off ``main``'s, and you on ``main``.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    _shared(lab)
    experiments = [
        ("bright-lights", "lights.txt", "lights=bright\n", "Try bright lights"),
        ("quiet-engine", "engine.txt", "engine=quiet\n", "Try a quiet engine"),
    ]
    for day, (branch, name, text, message) in enumerate(experiments, start=5):
        gitcmd.output(lab.project, "switch", "--quiet", "-c", branch, "main")
        _commit("project", lab, {name: text}, message, f"2026-06-0{day}T09:00:00+00:00")
    gitcmd.output(lab.project, "switch", "--quiet", "main")


def _alex_ahead(lab: Lab) -> None:
    """
    Build Alex is ahead: Alex pushed two commits that you have not fetched.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    _shared(lab)
    _commit("teammate", lab, {"route.txt": "Route: Moon, Phobos\n"}, "Fix the route", "2026-06-04T09:00:00+00:00", ALEX)
    _commit("teammate", lab, {"notes.txt": "Notes\nFuel: 80%\n"}, "Note the fuel level", "2026-06-05T09:00:00+00:00", ALEX)
    gitcmd.output(lab.teammate, "push", "--quiet")


def _both(lab: Lab) -> None:
    """
    Build Both committed: Alex pushed a change to ``route.txt``, you committed one to ``notes.txt`` and fetched, so the two have diverged.

    A ``git pull --no-rebase`` or ``git merge origin/main`` then makes a merge commit, with no
    conflict: the two commits change different files.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    _shared(lab)
    _commit("teammate", lab, {"route.txt": "Route: Moon, Phobos\n"}, "Fix the route", "2026-06-04T09:00:00+00:00", ALEX)
    gitcmd.output(lab.teammate, "push", "--quiet")
    _commit("project", lab, {"notes.txt": "Notes\nFuel: 80%\n"}, "Note the fuel level", "2026-06-04T10:00:00+00:00")
    gitcmd.output(lab.project, "fetch", "--quiet")


def _conflict(lab: Lab) -> None:
    """
    Build Conflict: you and Alex changed the course line of ``checklist.txt``; Alex pushed first, and your pull stopped on it.

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    _shared(lab)
    _commit("project", lab, {CHECKLIST: CHECKLIST_TEXT}, "Add the launch checklist", "2026-06-03T09:00:00+00:00")
    gitcmd.output(lab.project, "push", "--quiet")
    gitcmd.output(lab.teammate, "pull", "--quiet")
    _commit("teammate", lab, {CHECKLIST: ALEX_CHECKLIST}, "Head for Jupiter", "2026-06-04T09:00:00+00:00", ALEX)
    gitcmd.output(lab.teammate, "push", "--quiet")
    _commit("project", lab, {CHECKLIST: YOUR_CHECKLIST}, "Head for the Moon", "2026-06-04T10:00:00+00:00")
    gitcmd.run(lab.project, "pull", "--no-rebase", "--no-edit")


def _lost(lab: Lab) -> None:
    """
    Build Something lost: two commits on ``thrusters``, then back on ``main`` and the branch deleted.

    The move log keeps them: ``HEAD@{1}`` is "Test the right thruster".

    Parameters
    ----------
    lab : Lab
        An empty lab.
    """
    _shared(lab)
    gitcmd.output(lab.project, "switch", "--quiet", "-c", "thrusters")
    tests = [("left=on\n", "Test the left thruster"), ("left=on\nright=on\n", "Test the right thruster")]
    for day, (text, message) in enumerate(tests, start=5):
        _commit("project", lab, {"thrusters.txt": text}, message, f"2026-06-0{day}T09:00:00+00:00")
    gitcmd.output(lab.project, "switch", "--quiet", "main")
    gitcmd.output(lab.project, "branch", "--quiet", "-D", "thrusters")


STARTS: dict[StartId, Start] = {
    "empty": Start(
        title={"en": "Empty folder", "es": "Carpeta vacía"},
        blurb={"en": "Two files and no repository yet.", "es": "Dos archivos y todavía ningún repositorio."},
        banner={"en": "No repository here yet. Try: git init", "es": "Aquí todavía no hay repositorio. Prueba: git init"},
        view="desk",
        mothership=False,
        alex=False,
        uses=(),
        setup=_empty,
    ),
    "changes": Start(
        title={"en": "Uncommitted changes", "es": "Cambios sin commit"},
        blurb={"en": "notes.txt edited on main, and a branch to switch to.", "es": "notes.txt editado en main, y un branch al que cambiar."},
        banner={
            "en": "notes.txt is edited and not committed. Try: git status",
            "es": "notes.txt está editado y sin commit. Prueba: git status",
        },
        view="desk",
        mothership=True,
        alex=False,
        uses=("branch", "undo"),
        setup=_changes,
    ),
    "branches": Start(
        title={"en": "Two branches", "es": "Dos branches"},
        blurb={"en": "Two experiments forked off main.", "es": "Dos experimentos que salen de main."},
        banner={
            "en": "Try: git switch bright-lights, then pick another view.",
            "es": "Prueba: git switch bright-lights, y luego elige otra vista.",
        },
        view="chain",
        mothership=True,
        alex=False,
        uses=("names",),
        setup=_branches,
    ),
    "alex-ahead": Start(
        title={"en": "Alex is ahead", "es": "Alex va adelante"},
        blurb={"en": "Alex pushed two commits you have not fetched.", "es": "Alex hizo push de dos commits que todavía no trajiste."},
        banner={
            "en": "Alex sent two commits. Try: git status, then git fetch.",
            "es": "Alex envió dos commits. Prueba: git status, y luego git fetch.",
        },
        view="history",
        mothership=True,
        alex=True,
        uses=("mothership",),
        setup=_alex_ahead,
    ),
    "both": Start(
        title={"en": "Both committed", "es": "Los dos hicieron commit"},
        blurb={"en": "You and Alex each committed a different file: a merge with no conflict.", "es": "Tú y Alex hicieron commit de archivos distintos: un merge sin conflicto."},
        banner={
            "en": "You and Alex each made a commit. Try: git status, then git pull --no-rebase.",
            "es": "Tú y Alex hicieron un commit cada uno. Prueba: git status, y luego git pull --no-rebase.",
        },
        view="history",
        mothership=True,
        alex=False,
        uses=("conflict",),
        setup=_both,
    ),
    "conflict": Start(
        title={"en": "Conflict", "es": "Conflicto"},
        blurb={"en": "You and Alex changed the same line, and your pull stopped on it.", "es": "Tú y Alex cambiaron la misma línea, y tu pull se detuvo ahí."},
        banner={
            "en": "Your pull stopped on a conflict in checklist.txt. Try: git status",
            "es": "Tu pull se detuvo en un conflicto en checklist.txt. Prueba: git status",
        },
        view="conflict",
        mothership=True,
        alex=True,
        uses=("conflict",),
        setup=_conflict,
    ),
    "lost": Start(
        title={"en": "Something lost", "es": "Algo perdido"},
        blurb={"en": "A branch with two commits, deleted.", "es": "Un branch con dos commits, borrado."},
        banner={
            "en": "A branch was deleted. Try: git log --oneline --all, then git reflog",
            "es": "Se borró un branch. Prueba: git log --oneline --all, y luego git reflog",
        },
        view="movelog",
        mothership=True,
        alex=False,
        uses=("undo",),
        setup=_lost,
    ),
}
"""The starting points, in the picker's order."""


def lab() -> Lab:
    """
    Give the free playground's lab.

    Returns
    -------
    Lab
        ``<home>/playground``; it may not exist.
    """
    return Lab(save.home() / save.PLAYGROUND_FOLDER)


def build(start: StartId) -> Lab:
    """
    Build the free playground afresh from a starting point, replacing whatever its lab held.

    The game's git configuration is made ready first (`firstcommit.gitcmd.ensure_config`). If the
    start's setup fails, the lab is removed and the error raised again.

    Parameters
    ----------
    start : StartId
        The starting point.

    Returns
    -------
    Lab
        The playground's lab, as the start begins.
    """
    built = lab()
    remove()
    gitcmd.ensure_config()
    built.root.mkdir(parents=True)
    try:
        STARTS[start].setup(built)
    except BaseException:
        remove()
        raise
    return built


def remove() -> None:
    """Remove the free playground's lab, if any, even one whose folders a player locked."""
    sandbox.remove_tree(lab().root, save.home())
