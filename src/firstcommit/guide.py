"""
The map guide's figures, as tiny lessons.

The time-travel map guide (``web/static/theme-time-guide.js``) opens each section with a small
figure: a tiny repository before and after one command, drawn by the map renderer. Each figure
here is that repository as a two-slide lesson that `firstcommit.demos` runs like any other, so
every hash, label and file in the picture is what git really made. The first slide builds the
repository; the second runs the change the section is about. A frame is read from the shell's
folder, so a change may ``cd`` to the repository its figure draws (the practice copy, for the
archive).
"""

from dataclasses import dataclass

from firstcommit.kit import Slide


@dataclass(frozen=True)
class Figure:
    """
    One guide figure: the section it illustrates, the lines that build its repository, and the change.

    ``section`` is the id of a section of the guide; ``setup`` and ``change`` are a lesson's
    ``run`` lines (`firstcommit.kit.Slide`), run in an empty folder in that order.
    """

    section: str
    setup: str
    change: str


def _commit(name: str, text: str, subject: str) -> str:
    """
    Give the lines that write a file and commit it.

    Parameters
    ----------
    name : str
        The file's name.
    text : str
        Its one line of content.
    subject : str
        The commit's message.

    Returns
    -------
    str
        Three ``run`` lines, ending in a newline.
    """
    return f"echo '{text}' > {name}\ngit add {name}\ngit commit -q -m '{subject}'\n"


_README = _commit("README.md", "# Handbook", "Add the README")
_RULES = _commit("rules.md", "Be kind.", "Add the rules")
_IDEA = _commit("idea.md", "Maybe a FAQ?", "Sketch an idea")
_PRACTICE_COPY = "git init -q --bare ../github/project.git\ngit clone -q ../github/project.git .\n"

FIGURES: tuple[Figure, ...] = (
    Figure(
        "commit", "git init -q\necho '# Handbook' > README.md\ngit add README.md\n", "git commit -m 'Add the README'"
    ),
    Figure(
        "parents",
        "git init -q\n" + _README + "echo 'Be kind.' > rules.md\ngit add rules.md\n",
        "git commit -m 'Add the rules'",
    ),
    Figure(
        "branch",
        "git init -q\n" + _README + _RULES + "git switch -q -c idea\necho 'Maybe a FAQ?' > idea.md\ngit add idea.md\n",
        "git commit -m 'Sketch an idea'",
    ),
    Figure(
        "now",
        "git init -q\n" + _README + "git switch -q -c idea\n" + _IDEA + "git switch -q main\n" + _RULES,
        "git switch idea",
    ),
    Figure(
        "detached",
        "git init -q\n"
        + _README
        + _RULES
        + "git switch -q --detach HEAD~1\necho 'Just trying' > try.md\ngit add try.md\n",
        "git commit -m 'Try something'",
    ),
    Figure(
        "merge",
        "git init -q\n" + _README + "git switch -q -c idea\n" + _IDEA + "git switch -q main\n" + _RULES,
        "git merge --no-edit idea",
    ),
    Figure(
        "tag",
        "git init -q\n" + _README + "git tag v1\necho 'Be kind.' > rules.md\ngit add rules.md\n",
        "git commit -m 'Add the rules'",
    ),
    Figure(
        "archive",
        _PRACTICE_COPY + _README + "git push -q\n" + _RULES + "cd ../github/project.git\n",
        "cd ../../project\ngit push\ncd ../github/project.git",
    ),
    Figure(
        "seen",
        _PRACTICE_COPY
        + _README
        + "git push -q\ngit clone -q ../github/project.git ../teammate\ncd ../teammate\n"
        + _RULES
        + "git push -q\ncd ../project\n",
        "git fetch",
    ),
)
"""The guide's figures, in the order of its sections."""


def lesson(figure: Figure) -> list[Slide]:
    """
    Turn a figure into the two-slide lesson `firstcommit.demos.frames` runs.

    Parameters
    ----------
    figure : Figure
        One of `FIGURES`.

    Returns
    -------
    list[Slide]
        ``<section>-before`` builds the repository, ``<section>-after`` runs the change; the
        frames of the two are the figure's drawings before and after.
    """
    return [
        Slide(id=f"{figure.section}-before", title=figure.section, text="", run=figure.setup),
        Slide(id=f"{figure.section}-after", title=figure.section, text="", run=figure.change),
    ]
