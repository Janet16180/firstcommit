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
- `record_sharing`: you and Alex, two clones of one practice copy, sharing a file. Alex's
  ``git pull`` is recorded in two halves: a copy of Alex's clone runs ``git fetch`` (the drawing
  between the halves), then ``git merge --ff-only origin/main``, and the copy must end exactly
  where the real ``git pull`` did. The refused push must fail and change nothing.
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
_PEOPLE = {"you": ("Robin Park", "robin@example.com"), "alex": ("Alex Kim", "alex@example.com")}

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


def _run(folder: Path, command: str, person: str = "you", must_fail: bool = False) -> dict[str, Any]:
    """
    Run one shell command as one person, and check it succeeds (or fails, when it must).

    Parameters
    ----------
    folder : Path
        Where to run it.
    command : str
        A bash command line.
    person : str
        ``"you"`` or ``"alex"``: whose name and email git records.
    must_fail : bool
        Whether git must refuse it.

    Returns
    -------
    dict[str, Any]
        ``{command, output, status}``: the command, what it printed (output and errors) and its
        exit status.

    Raises
    ------
    RuntimeError
        If the command succeeds when it must fail, or fails when it must succeed.
    """
    name, email = _PEOPLE[person]
    people = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}
    done = subprocess.run(["bash", "-euc", command], cwd=folder, env={**_BASE, **people}, capture_output=True, text=True)
    if (done.returncode != 0) != must_fail:
        raise RuntimeError(f"{command!r} in {folder.name}: exit {done.returncode}\n{done.stdout}{done.stderr}")
    return {"command": command, "output": done.stdout + done.stderr, "status": done.returncode}


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


_SHARING = [
    ("create", "you", ["echo 'Meeting at 10.' > notes.txt"], False),
    ("add", "you", ["git add notes.txt"], False),
    ("commit", "you", ["git commit -m 'Add the meeting notes'"], False),
    ("push", "you", ["git push"], False),
    ("pull", "alex", ["git pull"], False),
    ("alex-shares", "alex", ["echo 'Bring the slides.' >> notes.txt", "git commit -am 'Ask for the slides'", "git push"], False),
    ("you-commit", "you", ["echo 'Start here.' >> README.md", "git commit -am 'Say where to start'"], False),
    ("refused", "you", ["git push"], True),
    ("pull-merge", "you", ["git pull --no-rebase --no-edit"], False),
    ("push-again", "you", ["git push"], False),
]


def _three(lab: Path, alex: str = "alex") -> dict[str, Any]:
    """
    Observe your clone, GitHub and Alex's clone.

    Parameters
    ----------
    lab : Path
        The sharing lab.
    alex : str
        The folder of Alex's clone (a copy, for the pull's halfway state).

    Returns
    -------
    dict[str, Any]
        ``{you, github, alex}`` snapshots.
    """
    return {"you": repomap.snapshot(lab / "you"), "github": repomap.snapshot(lab / "github" / "project.git"), "alex": repomap.snapshot(lab / alex)}


def _shared_step(name: str, actor: str, commands: list[str], before: dict[str, Any], after: dict[str, Any], transcript: list[dict[str, Any]]) -> Step:
    """
    Make one sharing step, with each repository's feed events.

    Parameters
    ----------
    name : str
        The step's id.
    actor : str
        Who ran it: ``"you"`` or ``"alex"``.
    commands : list[str]
        What they typed.
    before : dict[str, Any]
        The three snapshots before.
    after : dict[str, Any]
        The three snapshots after.
    transcript : list[dict[str, Any]]
        What git printed, command by command.

    Returns
    -------
    Step
        ``{id, actor, commands, transcript, before, after, events}``, events by repository.
    """
    events = {key: changes.describe(before[key], after[key]) for key in ("you", "github", "alex")}
    return {"id": name, "actor": actor, "commands": commands, "transcript": transcript, "before": before, "after": after, "events": events}


def _same(one: Any, other: Any) -> bool:
    """
    Tell whether two snapshots, or two observations, are identical.

    Parameters
    ----------
    one : Any
        JSON-shaped data.
    other : Any
        JSON-shaped data.

    Returns
    -------
    bool
        True when they are equal field for field.
    """
    return json.dumps(one, sort_keys=True) == json.dumps(other, sort_keys=True)


def record_sharing() -> list[Step]:
    """
    Record you sharing a file with Alex through GitHub, then a refused push and its fix.

    Returns
    -------
    list[Step]
        One step per entry of the sharing walk; Alex's ``git pull`` is two steps,
        ``pull-fetch`` and ``pull-merge-half``.

    Raises
    ------
    RuntimeError
        If the pull's two halves do not end where ``git pull`` does, or the refused push changes
        anything.
    """
    steps: list[Step] = []
    with _lab() as lab:
        _run(lab, "git clone -q github/project.git you 2>/dev/null")
        _run(lab / "you", "echo '# Team handbook' > README.md && git add README.md && git commit -qm 'Add the README' && git push -q")
        _run(lab, "git clone -q github/project.git alex", "alex")
        before = _three(lab)
        for name, actor, commands, must_fail in _SHARING:
            if name == "pull":
                shutil.copytree(lab / "alex", lab / "alex-fetched", symlinks=True)
                fetched = [_run(lab / "alex-fetched", "git fetch", "alex")]
                halfway = _three(lab, "alex-fetched")
                transcript = [_run(lab / "alex", command, actor) for command in commands]
                after = _three(lab)
                _run(lab / "alex-fetched", "git merge -q --ff-only origin/main", "alex")
                if not _same(_three(lab, "alex-fetched")["alex"], after["alex"]):
                    raise RuntimeError("git fetch, then git merge, did not end where git pull did")
                steps.append(_shared_step("pull-fetch", actor, commands, before, halfway, fetched))
                steps.append(_shared_step("pull-merge-half", actor, commands, halfway, after, transcript))
            else:
                last = len(commands) - 1
                transcript = [_run(lab / actor, command, actor, must_fail and index == last) for index, command in enumerate(commands)]
                after = _three(lab)
                if must_fail and not _same(after, before):
                    raise RuntimeError(f"{name}: the refused command changed something")
                steps.append(_shared_step(name, actor, commands, before, after, transcript))
            before = after
        return [_shown(step, lab) for step in steps]
