"""
Record "Share a file with Alex" on real git, for the figure in theme-time-share.js.

Run it from the repository::

    uv run python tools/demo/share.py share.json

It builds one lab in a temporary folder: a bare practice copy that stands in for GitHub
(``github/project.git``) and two clones of it, ``you`` and ``alex``. You commit the README and
push it, Alex clones, then every step of the walk runs as the person it belongs to (Robin Park
or Alex Kim, fixed dates, no global or system configuration, ``init.defaultBranch=main``). After
each step it snapshots all three repositories with `firstcommit.repomap` and lists what changed
in each with `firstcommit.changes`, the same events the game's feed shows. It writes the steps
to the given file as JSON: ``[{id, actor, commands, transcript, before, after, events}]``, the
observations being ``{you, github, alex}``.

Two steps check themselves:

- Alex's ``git pull`` is recorded in two halves. A copy of Alex's clone runs ``git fetch`` (the
  drawing between the halves), then ``git merge --ff-only origin/main``, and the copy must end
  exactly where Alex's real ``git pull`` did.
- The refused push must fail and leave all three repositories exactly as they were.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, TypedDict

from firstcommit import changes, repomap
from firstcommit.changes import Event
from firstcommit.repomap import Snapshot

DATE = "2026-01-15T09:00:00+00:00"
BASE = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "init.defaultBranch",
    "GIT_CONFIG_VALUE_0": "main",
    "GIT_AUTHOR_DATE": DATE,
    "GIT_COMMITTER_DATE": DATE,
    "LC_ALL": "C",
}
PEOPLE = {
    "you": {"GIT_AUTHOR_NAME": "Robin Park", "GIT_AUTHOR_EMAIL": "robin@example.com", "GIT_COMMITTER_NAME": "Robin Park", "GIT_COMMITTER_EMAIL": "robin@example.com"},
    "alex": {"GIT_AUTHOR_NAME": "Alex Kim", "GIT_AUTHOR_EMAIL": "alex@example.com", "GIT_COMMITTER_NAME": "Alex Kim", "GIT_COMMITTER_EMAIL": "alex@example.com"},
}
SHOWN_LAB = "/home/you/lab"

# Each step: its id, who runs it, the commands, and whether git must refuse it.
STEPS = [
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


class Line(TypedDict):
    """One command a step ran: as typed, what it printed (output and errors) and its exit status."""

    command: str
    output: str
    status: int


Observation = dict[str, Snapshot]
"""The three repositories at one moment: ``{you, github, alex}``."""


class Step(TypedDict):
    """One recorded step: who ran what, git's words, the three repositories around it and each one's events."""

    id: str
    actor: str
    commands: list[str]
    transcript: list[Line]
    before: Observation
    after: Observation
    events: dict[str, list[Event]]


def run(cwd: Path, person: str, command: str, must_fail: bool = False) -> Line:
    """
    Run one shell command as one person, and check it succeeds, or fails when it must.

    Parameters
    ----------
    cwd : Path
        Where to run it.
    person : str
        ``"you"`` or ``"alex"``: whose name and email git records.
    command : str
        A bash command line.
    must_fail : bool
        Whether git must refuse it.

    Returns
    -------
    Line
        The command, what it printed and its exit status.

    Raises
    ------
    RuntimeError
        If the command succeeds when it must fail, or fails when it must succeed.
    """
    done = subprocess.run(["bash", "-c", command], cwd=cwd, env={**BASE, **PEOPLE[person]}, capture_output=True, text=True)
    if (done.returncode != 0) != must_fail:
        raise RuntimeError(f"{command!r} in {cwd.name}: exit {done.returncode}\n{done.stdout}{done.stderr}")
    return {"command": command, "output": done.stdout + done.stderr, "status": done.returncode}


def observe(lab: Path, alex: str = "alex") -> Observation:
    """
    Snapshot your clone, GitHub and Alex's clone.

    Parameters
    ----------
    lab : Path
        The lab folder.
    alex : str
        The folder of Alex's clone: a copy, for the pull's halfway state.

    Returns
    -------
    Observation
        The three snapshots.
    """
    return {"you": repomap.snapshot(lab / "you"), "github": repomap.snapshot(lab / "github" / "project.git"), "alex": repomap.snapshot(lab / alex)}


def step(name: str, actor: str, commands: list[str], before: Observation, after: Observation, transcript: list[Line]) -> Step:
    """
    Make one step's record, with the feed events of each repository.

    Parameters
    ----------
    name : str
        The step's id.
    actor : str
        Who ran it: ``"you"`` or ``"alex"``.
    commands : list[str]
        What they typed.
    before : Observation
        The three repositories before the step.
    after : Observation
        The three repositories after it.
    transcript : list[Line]
        What git printed, command by command.

    Returns
    -------
    Step
        The step.
    """
    events = {key: changes.describe(before[key], after[key]) for key in ("you", "github", "alex")}
    return {"id": name, "actor": actor, "commands": commands, "transcript": transcript, "before": before, "after": after, "events": events}


def same(one: Any, other: Any) -> bool:
    """
    Tell whether two snapshots, or two observations, are equal field for field.

    Parameters
    ----------
    one : Any
        JSON-shaped data.
    other : Any
        JSON-shaped data.

    Returns
    -------
    bool
        True when they are equal.
    """
    return json.dumps(one, sort_keys=True) == json.dumps(other, sort_keys=True)


def record_sharing() -> list[Step]:
    """
    Record you sharing a file with Alex through GitHub, then a refused push and its fix.

    Returns
    -------
    list[Step]
        One step per entry of `STEPS`; Alex's ``git pull`` is two steps, ``pull-fetch`` and
        ``pull-merge-half``.

    Raises
    ------
    RuntimeError
        If a command does not end as expected, the pull's two halves do not end where
        ``git pull`` does, or the refused push changes anything.
    """
    root = Path(tempfile.mkdtemp(prefix="fc-share-"))
    steps: list[Step] = []
    try:
        subprocess.run(["git", "init", "-q", "--bare", "github/project.git"], cwd=root, env=BASE, check=True)
        run(root, "you", "git clone -q github/project.git you 2>/dev/null")
        for command in ["echo '# Team handbook' > README.md", "git add README.md", "git commit -qm 'Add the README'", "git push -q"]:
            run(root / "you", "you", command)
        run(root, "alex", "git clone -q github/project.git alex")
        before = observe(root)
        for name, actor, commands, must_fail in STEPS:
            if name == "pull":
                shutil.copytree(root / "alex", root / "alex-fetched", symlinks=True)
                fetched = [run(root / "alex-fetched", "alex", "git fetch")]
                halfway = observe(root, "alex-fetched")
                transcript = [run(root / "alex", actor, command) for command in commands]
                after = observe(root)
                run(root / "alex-fetched", "alex", "git merge -q --ff-only origin/main")
                if not same(observe(root, "alex-fetched")["alex"], after["alex"]):
                    raise RuntimeError("fetch + merge did not end where git pull did")
                steps.append(step("pull-fetch", actor, commands, before, halfway, fetched))
                steps.append(step("pull-merge-half", actor, commands, halfway, after, transcript))
            else:
                last = len(commands) - 1
                transcript = [run(root / actor, actor, command, must_fail and index == last) for index, command in enumerate(commands)]
                after = observe(root)
                if must_fail and not same(after, before):
                    raise RuntimeError(f"{name}: a refused command changed something")
                steps.append(step(name, actor, commands, before, after, transcript))
            before = after
    finally:
        shutil.rmtree(root)
    # git prints the lab's random temporary path; show it as a home folder instead.
    shown: list[Step] = json.loads(json.dumps(steps).replace(str(root), SHOWN_LAB))
    return shown


def main() -> None:
    """Record the walk and write it to the file named on the command line, as JSON."""
    Path(sys.argv[1]).write_text(json.dumps(record_sharing()) + "\n")


if __name__ == "__main__":
    main()
