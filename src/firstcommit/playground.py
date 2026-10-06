"""
The two-person playground: you and Alex share one remote, and each of you has the same buttons.

GitHub is the lab's bare repository; your clone is the lab's project, where the player's
terminal opens, and Alex's is the lab's teammate folder. Every button is one fixed command, run
for real in the clone of the person who pressed it, so what the figure draws afterwards is what
git did, and the player can type the same command in the terminal and get the same result.

A press runs as the player's terminal would run it (the game's shell environment, the clone's
own hooks and settings), but without a terminal: git opens no editor, pager or progress meter,
and prints no colours. Where a terminal would open the editor for a merge commit, git keeps the
message it suggests, as when the player saves and closes the editor unchanged. Git speaks
English (``LC_ALL=C``) so that its words can be read back.
"""

import os
import shlex
from pathlib import Path

from termlab import snippets

from firstcommit import gitcmd, save
from firstcommit.kit import Lab
from firstcommit.records import FILE_MODE, Button, Press, Who

PEOPLE: dict[Who, gitcmd.Person] = {
    "you": gitcmd.Person("You", "you@example.com"),
    "alex": gitcmd.Person("Alex", "alex@example.com"),
}
"""Each clone's own identity, set in its ``.git/config``, so typed commits and pressed ones agree."""

FILES: dict[Who, str] = {"you": "you.txt", "alex": "alex.txt"}
"""The file each person's Edit button changes: one each, so no pull ever has to merge one file."""

LINES: dict[Who, str] = {"you": "A line from you.", "alex": "A line from Alex."}

BUTTONS: dict[Button, dict[Who, str]] = {
    "edit": {person: f"echo {shlex.quote(LINES[person])} >> {FILES[person]}" for person in PEOPLE},
    "add": {person: f"git add {FILES[person]}" for person in PEOPLE},
    "commit": {person: f"git commit -m {shlex.quote(f'Add a line to {FILES[person]}')}" for person in PEOPLE},
    "push": {person: "git push" for person in PEOPLE},
    "fetch": {person: "git fetch" for person in PEOPLE},
    "pull": {person: "git pull" for person in PEOPLE},
    "pull-no-rebase": {person: "git pull --no-rebase" for person in PEOPLE},
    "status": {person: "git status" for person in PEOPLE},
}
"""
Each button's command, by person: one line of bash the player could type.

``pull`` is git's own ``git pull``: on branches that have diverged, git 2.27 and later refuse
until the player chooses how to reconcile them (``pull.rebase``). ``pull-no-rebase`` merges
without that choice, for a step that has to merge before the player has made it.
"""

README = "# Shared notes\n\nYou and Alex both work on this project.\n"


def setup(lab: Lab) -> None:
    """
    Create the playground: GitHub with one commit, and a clone of it for each person.

    Parameters
    ----------
    lab : Lab
        The lab; its root exists, and its GitHub, project and teammate folders do not.

    Raises
    ------
    FileExistsError
        If the teammate's folder already exists.
    subprocess.CalledProcessError
        If git fails, for example because GitHub or the project already exists.
    """
    lab.github.parent.mkdir(exist_ok=True)
    gitcmd.output(lab.github.parent, "init", "--quiet", "--bare", "--initial-branch=main", lab.github.name)
    blob = gitcmd.output(lab.github, "hash-object", "-w", "--stdin", stdin=README).strip()
    tree = gitcmd.output(lab.github, "mktree", stdin=f"{FILE_MODE} blob {blob}\tREADME.md\n").strip()
    commit = gitcmd.output(lab.github, "commit-tree", tree, "-m", "Add the README").strip()
    gitcmd.output(lab.github, "update-ref", "refs/heads/main", commit)
    lab.teammate.parent.mkdir()
    for person, identity in PEOPLE.items():
        folder = _clone(lab, person)
        gitcmd.output(folder.parent, "clone", "--quiet", str(lab.github), folder.name)
        gitcmd.output(folder, "config", "user.name", identity.name)
        gitcmd.output(folder, "config", "user.email", identity.email)


def press(lab: Lab, person: Who, button: Button) -> Press:
    """
    Run one person's button in their clone, whatever state the player left it in.

    Parameters
    ----------
    lab : Lab
        The lab, set up by `setup`; the player may have changed or removed anything since.
    person : Who
        Who pressed.
    button : Button
        Which button.

    Returns
    -------
    Press
        The command and what it printed. A command that fails, or a clone that is gone, is
        reported with its non-zero status, as a terminal would show it.

    Raises
    ------
    KeyError
        If ``person`` or ``button`` is not one of the playground's.
    subprocess.TimeoutExpired
        If the command runs longer than `firstcommit.gitcmd.TIMEOUT` seconds.
    """
    command = BUTTONS[button][person]
    script = f"exec 2>&1\ncd -- {shlex.quote(str(_clone(lab, person)))} || exit\n{command}\n"
    env = {**gitcmd.shell_environment(os.environ, save.home()), "LC_ALL": "C"}
    result = snippets.run(script, Path("/"), env, timeout=gitcmd.TIMEOUT)
    return {"person": person, "button": button, "command": command, "status": result.returncode, "output": result.stdout}


def _clone(lab: Lab, person: Who) -> Path:
    """
    Find a person's clone in the lab.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : Who
        Who.

    Returns
    -------
    Path
        Your clone is the lab's project, where the player's terminal opens; Alex's is the
        lab's teammate folder.
    """
    return {"you": lab.project, "alex": lab.teammate}[person]
