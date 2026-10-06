"""
Real-git recordings for the four places demo (build.py).

Every drawing in the demo is a snapshot of a real repository, never hand-made: each recorder runs
git in a fresh lab under a temporary folder (a bare practice copy that stands in for GitHub, and
clones of it), snapshots the repositories with `firstcommit.repomap` after each command and lists
what changed with `firstcommit.changes`, the same events the game's feed shows. Git runs with no
global or system configuration, ``init.defaultBranch=main`` and fixed names and dates, so the
hashes are the same on every run, except for merge commits: their message names the lab's real
path (shown as /home/you/lab), which changes from run to run.

- `record_commands`: one command at a time (add, commit, push, fetch, pull, pull after a fetch,
  pull on diverged branches, clone), each in its own lab.
- `record_first_commits`: init, two new files, add, commit, edit, add, commit, remote, push, one
  lab, one step after another.
"""

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from firstcommit import changes, repomap

DATE = "2026-01-15T09:00:00+00:00"
"""Every commit's author and committer date."""
SHOWN_LAB = "/home/you/lab"
"""How a lab's temporary folder appears in git's output."""

_BASE = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": "/nonexistent",
    "LC_ALL": "C",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "init.defaultBranch",
    "GIT_CONFIG_VALUE_0": "main",
    "GIT_AUTHOR_DATE": DATE,
    "GIT_COMMITTER_DATE": DATE,
}
_YOU = {"GIT_AUTHOR_NAME": "Robin Park", "GIT_AUTHOR_EMAIL": "robin@example.com", "GIT_COMMITTER_NAME": "Robin Park", "GIT_COMMITTER_EMAIL": "robin@example.com"}

Step = dict[str, Any]
"""One recorded step: the observations before and after it, the feed events and the commands."""


@contextmanager
def _lab() -> Iterator[Path]:
    """
    Make an empty lab folder holding a bare practice copy, and remove it afterwards.

    Yields
    ------
    Path
        The lab: ``github/project.git`` is the practice copy.
    """
    root = Path(tempfile.mkdtemp(prefix="fc-demo-"))
    try:
        subprocess.run(["git", "init", "-q", "--bare", "github/project.git"], cwd=root, env=_BASE, check=True)
        yield root
    finally:
        shutil.rmtree(root)


def _run(folder: Path, command: str) -> None:
    """
    Run one shell command, with git recording Robin Park as its author, and check it succeeds.

    Parameters
    ----------
    folder : Path
        Where to run it.
    command : str
        A bash command line.

    Raises
    ------
    RuntimeError
        If the command fails.
    """
    done = subprocess.run(["bash", "-euc", command], cwd=folder, env={**_BASE, **_YOU}, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"{command!r} in {folder.name}: exit {done.returncode}\n{done.stdout}{done.stderr}")


def _shown(value: Any, lab: Path) -> Any:
    """
    Replace the lab's temporary path with `SHOWN_LAB` everywhere in a recording.

    Parameters
    ----------
    value : Any
        JSON-shaped data.
    lab : Path
        The lab folder.

    Returns
    -------
    Any
        The same data, with the path replaced.
    """
    return json.loads(json.dumps(value).replace(str(lab), SHOWN_LAB))


def _places(lab: Path) -> dict[str, Any]:
    """
    Observe one computer and GitHub, as the game does.

    Parameters
    ----------
    lab : Path
        A lab with a ``project`` folder.

    Returns
    -------
    dict[str, Any]
        ``{project, github}`` snapshots.
    """
    return {"project": repomap.snapshot(lab / "project"), "github": repomap.snapshot(lab / "github" / "project.git")}


def _feed(before: dict[str, Any], after: dict[str, Any]) -> list[Any]:
    """
    List the feed events of every repository of an observation, in order.

    Parameters
    ----------
    before : dict[str, Any]
        Snapshots by name.
    after : dict[str, Any]
        The same names, later.

    Returns
    -------
    list[Any]
        The events of each repository in turn.
    """
    return [event for key in before for event in changes.describe(before[key], after[key])]


_HANDBOOK = (
    "git clone -q github/project.git teammate 2>/dev/null; cd teammate; "
    "echo '# Team handbook' > README.md; git add README.md; git commit -qm 'Add the README'; "
    "echo 'Be kind.' > rules.md; git add rules.md; git commit -qm 'Add the rules'; git push -q origin main; cd ..; "
)
_CLONED = _HANDBOOK + "git clone -q github/project.git project; "
_TEAMMATE_PUSHES = "cd teammate; echo 'Ask early.' >> rules.md; git commit -qam 'Add a rule'; git push -q; cd ..; "
_COMMANDS = {
    "add": (_CLONED + "cd project; echo 'Start here.' >> README.md; echo 'draft' > notes.txt", "git add README.md"),
    "commit": (_CLONED + "cd project; echo 'Start here.' >> README.md; git add README.md", "git commit -m 'Say where to start'"),
    "push": (_CLONED + "cd project; echo 'Start here.' >> README.md; git commit -qam 'Say where to start'", "git push"),
    "fetch": (_CLONED + _TEAMMATE_PUSHES, "git fetch"),
    "pull": (_CLONED + _TEAMMATE_PUSHES, "git pull"),
    "pull-after-fetch": (_CLONED + _TEAMMATE_PUSHES + "cd project; git fetch -q", "git pull"),
    "pull-merge": (_CLONED + _TEAMMATE_PUSHES + "cd project; echo 'Start here.' >> README.md; git commit -qam 'Say where to start'", "git pull --no-rebase --no-edit"),
    "clone": (_HANDBOOK + "mkdir project", "git clone ../github/project.git ."),
}


def record_commands() -> dict[str, Step]:
    """
    Record each single command of the four places in its own lab.

    Returns
    -------
    dict[str, Step]
        By scenario name: ``{before, after, events, command}``, the observations being
        ``{project, github}``.
    """
    recorded: dict[str, Step] = {}
    for name, (setup, command) in _COMMANDS.items():
        with _lab() as lab:
            _run(lab, setup)
            before = _places(lab)
            _run(lab / "project", command)
            after = _places(lab)
            recorded[name] = _shown({"before": before, "after": after, "events": _feed(before, after), "command": command}, lab)
    return recorded


_FIRST_COMMITS = [
    ("init", ["git init"]),
    ("new files", ["echo '# Team handbook' > README.md", "echo 'Be kind.' > rules.md"]),
    ("add", ["git add README.md rules.md"]),
    ("commit", ["git commit -m 'Start the handbook'"]),
    ("modify", ["echo 'Ask early.' >> README.md"]),
    ("add again", ["git add README.md"]),
    ("commit again", ["git commit -m 'Say how to ask'"]),
    ("remote", ["git remote add origin ../github/project.git"]),
    ("push", ["git push -u origin main"]),
]


def record_first_commits() -> list[Step]:
    """
    Record a first project, from git init to the first push, one step after another.

    Returns
    -------
    list[Step]
        ``{name, commands, before, after, events}`` per step, the observations being
        ``{project, github}``.
    """
    steps: list[Step] = []
    with _lab() as lab:
        (lab / "project").mkdir()
        before = _places(lab)
        for name, commands in _FIRST_COMMITS:
            for command in commands:
                _run(lab / "project", command)
            after = _places(lab)
            steps.append({"name": name, "commands": commands, "before": before, "after": after, "events": _feed(before, after)})
            before = after
        return [_shown(step, lab) for step in steps]

