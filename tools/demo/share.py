"""
Record "Share a file with Alex" on real git, for the figure in theme-time-share.js.

Run it from the repository::

    uv run python tools/demo/share.py share.json

It builds one lab in the fixed folder `LAB`: a bare practice copy that stands in for GitHub
(``github/project.git``) and two clones of it, ``you`` and ``alex``. You commit the README and
push it, Alex clones, then every step of the walk runs as the person it belongs to, Robin Park or
Alex Kim, in the lessons' own fixed environment (`firstcommit.demos.environment`: fixed dates,
the C locale, the game's starting configuration and nothing else from the shell that runs it).
After each step it snapshots all three repositories with `firstcommit.repomap` and lists what changed
in each with `firstcommit.changes`, the same events the game's feed shows. It writes the steps
to the given file as JSON: ``[{id, actor, commands, transcript, before, after, events}]``, the
observations being ``{you, github, alex}``.

Two steps check themselves:

- Alex's ``git pull`` is recorded in two halves. A copy of Alex's clone runs ``git fetch`` (the
  drawing between the halves), then ``git merge --ff-only origin/main``, and the copy must end
  exactly where Alex's real ``git pull`` did.
- The refused push must fail and leave all three repositories exactly as they were.

The lab is always the same folder because git writes the practice copy's path into the merge
message of ``git pull``, so the merge commit's hash depends on it. Every hash and every line of
output is therefore the same on every run with the same git, and nothing is rewritten after
recording. The lab is removed at the end; the recorder refuses to start if the folder exists.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

from firstcommit import changes, demos, gitcmd, repomap
from firstcommit.changes import Event
from firstcommit.repomap import Snapshot

LAB = Path("/tmp/firstcommit-share")
"""The lab's folder, also its home: git prints this path, and writes it into the merge commit."""
PEOPLE = {"you": gitcmd.Person("Robin Park", "robin@example.com"), "alex": gitcmd.Person("Alex Kim", "alex@example.com")}

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


def as_person(environment: dict[str, str], person: str) -> dict[str, str]:
    """
    Give the lab's environment with one person as git's author and committer.

    Parameters
    ----------
    environment : dict[str, str]
        The lab's whole environment.
    person : str
        ``"you"`` or ``"alex"``.

    Returns
    -------
    dict[str, str]
        The same environment, with that person's name and email.
    """
    name, email = PEOPLE[person].name, PEOPLE[person].email
    return {**environment, "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}


def run(cwd: Path, environment: dict[str, str], person: str, command: str, must_fail: bool = False) -> Line:
    """
    Run one shell command as one person, and check it succeeds, or fails when it must.

    Parameters
    ----------
    cwd : Path
        Where to run it.
    environment : dict[str, str]
        The lab's whole environment.
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
    done = subprocess.run(["bash", "-c", command], cwd=cwd, env=as_person(environment, person), capture_output=True, text=True)
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
    FileExistsError
        If `LAB` exists already.
    RuntimeError
        If a command does not end as expected, the pull's two halves do not end where
        ``git pull`` does, or the refused push changes anything.
    """
    environment = demos.environment(LAB)
    steps: list[Step] = []
    try:
        run(LAB, environment, "you", "git init -q --bare github/project.git")
        run(LAB, environment, "you", "git clone -q github/project.git you 2>/dev/null")
        for command in ["echo '# Team handbook' > README.md", "git add README.md", "git commit -qm 'Add the README'", "git push -q"]:
            run(LAB / "you", environment, "you", command)
        run(LAB, environment, "alex", "git clone -q github/project.git alex")
        before = observe(LAB)
        for name, actor, commands, must_fail in STEPS:
            if name == "pull":
                shutil.copytree(LAB / "alex", LAB / "alex-fetched", symlinks=True)
                fetched = [run(LAB / "alex-fetched", environment, "alex", "git fetch")]
                halfway = observe(LAB, "alex-fetched")
                transcript = [run(LAB / "alex", environment, actor, command) for command in commands]
                after = observe(LAB)
                run(LAB / "alex-fetched", environment, "alex", "git merge -q --ff-only origin/main")
                if not same(observe(LAB, "alex-fetched")["alex"], after["alex"]):
                    raise RuntimeError("fetch + merge did not end where git pull did")
                steps.append(step("pull-fetch", actor, commands, before, halfway, fetched))
                steps.append(step("pull-merge-half", actor, commands, halfway, after, transcript))
            else:
                last = len(commands) - 1
                transcript = [run(LAB / actor, environment, actor, command, must_fail and index == last) for index, command in enumerate(commands)]
                after = observe(LAB)
                if must_fail and not same(after, before):
                    raise RuntimeError(f"{name}: a refused command changed something")
                steps.append(step(name, actor, commands, before, after, transcript))
            before = after
    finally:
        shutil.rmtree(LAB)
    return steps


def main() -> None:
    """Record the walk and write it to the file named on the command line, as JSON."""
    Path(sys.argv[1]).write_text(json.dumps(record_sharing()) + "\n")


if __name__ == "__main__":
    main()
