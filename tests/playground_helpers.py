"""Helpers shared by the tests that press the two-person playground's buttons on real git."""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import get_args

from firstcommit import gitcmd, playground, records, repomap, save
from firstcommit.lab import Lab

PEOPLE: tuple[records.Who, ...] = get_args(records.Who)
PLAYER = gitcmd.Person("Robin Park", "robin@example.com")
"""The player's identity, in the game's global configuration as the basics chapter sets it."""
NOTES = "notes.txt"
COMMIT_NOTES: tuple[str, ...] = ("edit:notes.txt", "add:notes.txt", "commit")
SHARE_NOTES: tuple[str, ...] = (*COMMIT_NOTES, "push")


@contextmanager
def new_lab(identity: bool = True) -> Iterator[Lab]:
    """
    Make a lab with the playground set up, in the game's labs folder, and remove it afterwards.

    Parameters
    ----------
    identity : bool
        Whether the game's global configuration holds the player's name and email.

    Yields
    ------
    Lab
        The lab: GitHub and both clones.
    """
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    for key, value in (("user.name", PLAYER.name), ("user.email", PLAYER.email)):
        gitcmd.output(save.home(), "config", "--global", *((key, value) if identity else ("--unset", key)))
    labs = save.home() / save.LABS_FOLDER
    labs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=labs) as root:
        lab = Lab(Path(root))
        playground.setup(lab)
        yield lab


def clone(lab: Lab, person: records.Who) -> Path:
    """
    Find a person's clone.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : records.Who
        Who.

    Returns
    -------
    Path
        Their working folder.
    """
    return lab.project if person == "you" else lab.teammate


def views(lab: Lab) -> dict[str, repomap.Snapshot]:
    """
    Snapshot GitHub and both clones.

    Parameters
    ----------
    lab : Lab
        The lab.

    Returns
    -------
    dict[str, repomap.Snapshot]
        The snapshots by ``"github"`` and by person.
    """
    return {"github": repomap.snapshot(lab.github), "you": repomap.snapshot(lab.project), "alex": repomap.snapshot(lab.teammate)}


def bar(lab: Lab, person: records.Who) -> dict[str, records.ButtonView]:
    """
    Give the buttons a person sees now.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : records.Who
        Whose bar.

    Returns
    -------
    dict[str, records.ButtonView]
        The buttons by id, in bar order.
    """
    snapshots: dict[records.Who, repomap.Snapshot] = {who: repomap.snapshot(clone(lab, who)) for who in PEOPLE}
    return {view["id"]: view for view in playground.buttons(lab, snapshots)[person]}


def target(snap: repomap.Snapshot, name: str = "main") -> str | None:
    """
    Find the commit a ref names.

    Parameters
    ----------
    snap : repomap.Snapshot
        The snapshot.
    name : str
        The ref, such as ``main`` or ``origin/main``.

    Returns
    -------
    str | None
        Its commit, or None when the snapshot has no such ref.
    """
    return next((ref["target"] for ref in snap["refs"] if ref["name"] == name), None)


def presses(lab: Lab, person: records.Who, *buttons: str) -> list[records.Press]:
    """
    Press one person's buttons in order.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : records.Who
        Who presses.
    *buttons : str
        The button ids.

    Returns
    -------
    list[records.Press]
        What each press reported.
    """
    return [playground.press(lab, person, button) for button in buttons]


def conflicted_lab(lab: Lab) -> records.Press:
    """
    Pause a merge on a conflict in ``notes.txt`` in your clone: both people append their line 2, Alex pushes first.

    Parameters
    ----------
    lab : Lab
        A fresh lab.

    Returns
    -------
    records.Press
        Your ``git pull --no-rebase --no-edit``, which stopped on the conflict.
    """
    presses(lab, "alex", *SHARE_NOTES)
    presses(lab, "you", *COMMIT_NOTES)
    [pull] = presses(lab, "you", "pull-no-rebase")
    return pull
