"""
Record "Share a file with Alex" on real git, for the figure in theme-time-share.js.

Run it from the repository::

    uv run python tools/demo/share.py share.json

It builds one lab in a temporary folder, laid out as a level's (`firstcommit.lab.Lab`): a bare
practice copy that stands in for GitHub, your clone of it (the lab's project) and Alex's (the
lab's teammate), each reaching GitHub by a relative path as AUTHORING section 3.2 asks. You
commit the README and push it, Alex clones, then every step of `WALK` runs as the person it
belongs to, Robin Park or Alex Kim, in the lessons' own fixed environment
(`firstcommit.demos.environment`: fixed dates, the C locale, the game's starting configuration
and nothing else from the shell that runs it).
A command written with a leading ``! `` must fail, as in a lesson; any other must succeed.
After each step it snapshots all three repositories with `firstcommit.repomap` and lists what
changed in each with `firstcommit.changes`, the same events the game's feed shows. It writes the
steps to the given file as JSON: ``[{id, actor, commands, transcript, before, after, events}]``,
the observations being ``{you, github, alex}``. `LABELS` names each step for a demo's buttons.

Three steps check themselves:

- Alex's ``git pull`` is recorded in two halves. A copy of Alex's clone runs ``git fetch`` (the
  drawing between the halves), then ``git merge --ff-only origin/main``, and the copy must end
  exactly where Alex's real ``git pull`` did.
- The refused push must leave all three repositories exactly as they were.
- Your plain ``git pull`` on diverged branches must fail and end exactly where a ``git fetch``
  in a copy of your clone ends: it fetched, and changed nothing else.

Git prints the practice copy's URL in push and pull output and writes it into the merge commit's
message, so with a relative URL nothing recorded names the temporary folder: every hash and every
line of output is the same on every run with the same git, and nothing is rewritten after
recording. The folder is removed at the end.
"""

import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, NamedTuple, TypedDict

from firstcommit import changes, demos, gitcmd, repomap
from firstcommit.changes import Event
from firstcommit.lab import Lab
from firstcommit.repomap import Snapshot

PEOPLE = {"you": gitcmd.Person("Robin Park", "robin@example.com"), "alex": gitcmd.Person("Alex Kim", "alex@example.com")}

Check = Literal["", "halves", "unchanged", "fetch-only"]
"""What a step must show besides its commands' exit statuses (see the module's description)."""


class Walk(NamedTuple):
    """One step of the walk: its id, who runs it, the commands as typed, and its own check."""

    id: str
    actor: str
    commands: list[str]
    check: Check = ""


WALK = [
    Walk("create", "you", ["echo 'Meeting at 10.' > notes.txt"]),
    Walk("add", "you", ["git add notes.txt"]),
    Walk("commit", "you", ["git commit -m 'Add the meeting notes'"]),
    Walk("push", "you", ["git push"]),
    Walk("pull", "alex", ["git pull"], "halves"),
    Walk("alex-commit", "alex", ["echo 'Bring the slides.' >> notes.txt", "git commit -am 'Ask for the slides'"]),
    Walk("alex-push", "alex", ["git push"]),
    Walk("you-commit", "you", ["echo 'Start here.' >> README.md", "git commit -am 'Say where to start'"]),
    Walk("refused", "you", ["! git push"], "unchanged"),
    Walk("pull-stops", "you", ["! git pull"], "fetch-only"),
    Walk("pull-merge", "you", ["git pull --no-rebase --no-edit"]),
    Walk("push-again", "you", ["git push"]),
]
HALVES = ("pull-fetch", "pull-merge-half")
"""The ids of the two steps a ``halves`` step is recorded as."""

LABELS = {
    "create": "You: new file",
    "add": "You: add",
    "commit": "You: commit",
    "push": "You: push",
    "pull-fetch": "Alex: pull, fetch half",
    "pull-merge-half": "Alex: pull, merge half",
    "alex-commit": "Alex: edit, commit",
    "alex-push": "Alex: push",
    "you-commit": "You: edit, commit",
    "refused": "You: push (refused)",
    "pull-stops": "You: pull (stops)",
    "pull-merge": "You: pull --no-rebase",
    "push-again": "You: push",
}
"""Each recorded step's name on a demo's button, in the walk's order."""


class Line(TypedDict):
    """One command a step ran: as shown, what it printed (output and errors) and its exit status."""

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


def run(cwd: Path, environment: dict[str, str], person: str, command: str) -> Line:
    """
    Run one shell command as one person, and check it succeeds, or fails when it starts with ``! ``.

    Parameters
    ----------
    cwd : Path
        Where to run it.
    environment : dict[str, str]
        The lab's whole environment.
    person : str
        ``"you"`` or ``"alex"``: whose name and email git records.
    command : str
        A bash command line, with ``! `` in front when it must fail.

    Returns
    -------
    Line
        The command without its ``! ``, what it printed (output and errors, in the order
        printed) and its exit status.

    Raises
    ------
    RuntimeError
        If the command succeeds when it must fail, or fails when it must succeed.
    """
    shown = command.removeprefix(demos.MUST_FAIL)
    done = subprocess.run(["bash", "-c", shown], cwd=cwd, env=as_person(environment, person), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if (done.returncode != 0) != command.startswith(demos.MUST_FAIL):
        raise RuntimeError(f"{command!r} in {cwd.name}: exit {done.returncode}\n{done.stdout}")
    return {"command": shown, "output": done.stdout, "status": done.returncode}


def clone(lab: Lab, person: str) -> Path:
    """
    Give a person's clone in the lab.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : str
        ``"you"`` (the lab's project) or ``"alex"`` (the lab's teammate).

    Returns
    -------
    Path
        The clone's top folder.
    """
    return {"you": lab.project, "alex": lab.teammate}[person]


def observe(lab: Lab, stand_in: dict[str, Path] | None = None) -> Observation:
    """
    Snapshot your clone, GitHub and Alex's clone.

    Parameters
    ----------
    lab : Lab
        The lab.
    stand_in : dict[str, Path] | None
        Folders to snapshot instead of a person's clone: a copy, for a pull's halfway state.

    Returns
    -------
    Observation
        The three snapshots.
    """
    folders = {"you": lab.project, "github": lab.github, "alex": lab.teammate, **(stand_in or {})}
    return {who: repomap.snapshot(folder) for who, folder in folders.items()}


def record(name: str, walk: Walk, before: Observation, after: Observation, transcript: list[Line]) -> Step:
    """
    Make one step's record, with the feed events of each repository.

    Parameters
    ----------
    name : str
        The step's id.
    walk : Walk
        The step of the walk it records: who ran it and what they typed.
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
    events = {who: changes.describe(before[who], after[who]) for who in before}
    commands = [command.removeprefix(demos.MUST_FAIL) for command in walk.commands]
    return {"id": name, "actor": walk.actor, "commands": commands, "transcript": transcript, "before": before, "after": after, "events": events}


def same(one: object, other: object) -> bool:
    """
    Tell whether two snapshots, or two observations, are equal field for field.

    Parameters
    ----------
    one : object
        JSON-shaped data.
    other : object
        JSON-shaped data.

    Returns
    -------
    bool
        True when they are equal.
    """
    return json.dumps(one, sort_keys=True) == json.dumps(other, sort_keys=True)


def make_clone(lab: Lab, environment: dict[str, str], person: str) -> None:
    """
    Clone GitHub as a person's clone, and make the clone reach GitHub by its relative path.

    Parameters
    ----------
    lab : Lab
        The lab; GitHub exists, and the clone's parent folder.
    environment : dict[str, str]
        The lab's whole environment.
    person : str
        Whose clone to make.
    """
    place = clone(lab, person)
    command = f"git clone -q {shlex.quote(str(lab.github))} {place.name} 2>/dev/null && git -C {place.name} remote set-url origin {shlex.quote(lab.github_url(place))}"
    run(place.parent, environment, person, command)


def fetched_copy(lab: Lab, environment: dict[str, str], person: str) -> tuple[Path, Line]:
    """
    Copy a person's clone next to it, where GitHub's relative URL still leads, and run ``git fetch`` in the copy.

    Parameters
    ----------
    lab : Lab
        The lab.
    environment : dict[str, str]
        The lab's whole environment.
    person : str
        Whose clone to copy.

    Returns
    -------
    tuple[Path, Line]
        The copy, which the caller removes, and what ``git fetch`` printed there.
    """
    original = clone(lab, person)
    copy = original.with_name(f"{original.name}-fetched")
    shutil.copytree(original, copy, symlinks=True)
    return copy, run(copy, environment, person, "git fetch")


def in_halves(lab: Lab, walk: Walk, environment: dict[str, str], before: Observation) -> list[Step]:
    """
    Run a person's ``git pull`` and record it as its fetch half, then its merge half.

    Parameters
    ----------
    lab : Lab
        The lab.
    walk : Walk
        The pull.
    environment : dict[str, str]
        The lab's whole environment.
    before : Observation
        The three repositories before it.

    Returns
    -------
    list[Step]
        The two steps, named `HALVES`.

    Raises
    ------
    RuntimeError
        If ``git fetch`` then ``git merge --ff-only origin/main`` does not end where the pull did.
    """
    copy, fetched = fetched_copy(lab, environment, walk.actor)
    halfway = observe(lab, {walk.actor: copy})
    transcript = [run(clone(lab, walk.actor), environment, walk.actor, command) for command in walk.commands]
    after = observe(lab)
    run(copy, environment, walk.actor, "git merge -q --ff-only origin/main")
    if not same(repomap.snapshot(copy), after[walk.actor]):
        raise RuntimeError(f"{walk.id}: git fetch, then git merge, did not end where git pull did")
    shutil.rmtree(copy)
    return [record(HALVES[0], walk, before, halfway, [fetched]), record(HALVES[1], walk, halfway, after, transcript)]


def in_one(lab: Lab, walk: Walk, environment: dict[str, str], before: Observation) -> Step:
    """
    Run one step of the walk and record it, checking what its `Walk.check` asks.

    Parameters
    ----------
    lab : Lab
        The lab.
    walk : Walk
        The step.
    environment : dict[str, str]
        The lab's whole environment.
    before : Observation
        The three repositories before it.

    Returns
    -------
    Step
        The step.

    Raises
    ------
    RuntimeError
        If a refused step changed anything, or a fetch-only step did more than ``git fetch``.
    """
    copy = fetched_copy(lab, environment, walk.actor)[0] if walk.check == "fetch-only" else None
    transcript = [run(clone(lab, walk.actor), environment, walk.actor, command) for command in walk.commands]
    after = observe(lab)
    if walk.check == "unchanged" and not same(after, before):
        raise RuntimeError(f"{walk.id}: a refused command changed something")
    if copy and not same(repomap.snapshot(copy), after[walk.actor]):
        raise RuntimeError(f"{walk.id}: did not end where git fetch does")
    if copy:
        shutil.rmtree(copy)
    return record(walk.id, walk, before, after, transcript)


def record_sharing() -> list[Step]:
    """
    Record you sharing a file with Alex through GitHub, then a refused push and its fix.

    Returns
    -------
    list[Step]
        One step per entry of `WALK`, in order, except that Alex's ``git pull`` is two steps,
        `HALVES`.

    Raises
    ------
    RuntimeError
        If a command does not end as expected, or a step fails its own check.
    """
    folder = Path(tempfile.mkdtemp(prefix="fc-share-"))
    steps: list[Step] = []
    try:
        environment = demos.environment(folder / "home")
        lab = Lab(folder / "lab")
        lab.teammate.parent.mkdir(parents=True)
        run(lab.root, environment, "you", f"git init -q --bare {shlex.quote(str(lab.github))}")
        make_clone(lab, environment, "you")
        run(lab.project, environment, "you", "echo '# Team handbook' > README.md && git add README.md && git commit -qm 'Add the README' && git push -q")
        make_clone(lab, environment, "alex")
        before = observe(lab)
        for walk in WALK:
            steps.extend(in_halves(lab, walk, environment, before) if walk.check == "halves" else [in_one(lab, walk, environment, before)])
            before = steps[-1]["after"]
    finally:
        shutil.rmtree(folder)
    return steps


def main() -> None:
    """Record the walk and write it to the file named on the command line, as JSON."""
    Path(sys.argv[1]).write_text(json.dumps(record_sharing()) + "\n")


if __name__ == "__main__":
    main()
