"""
The survey commits made on ``main`` by mistake, shared by 8-3 Wrong course and 8-4 The move log.

A helper module, not a level: its name starts with ``_``.
"""

from firstcommit import kit

SURVEY = "survey.txt"
DAYS = ("Crater A: 4 km wide\n", "Crater B: 9 km wide\n")
"""The survey's line for each day, one commit each."""


def survey(lab: kit.Lab) -> kit.State:
    """
    Build the playground and make two survey commits on your ``main``, not pushed.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        ``origin``: the mothership's ``main``; ``tip``: the survey's last commit.
    """
    kit.setup_playground(lab)
    origin = kit.git(lab.project, "rev-parse", "main").strip()
    for day, line in enumerate(DAYS, start=1):
        with (lab.project / SURVEY).open("a") as file:
            file.write(line)
        kit.git(lab.project, "add", SURVEY)
        kit.git(lab.project, "commit", "-q", "-m", f"Survey day {day}", author=kit.PLAYER, when=f"2026-07-2{day}T09:00:00+00:00")
    return {"origin": origin, "tip": kit.git(lab.project, "rev-parse", "main").strip()}
