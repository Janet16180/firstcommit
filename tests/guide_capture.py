"""
Capture what real git prints for the field guide's cards and its conflict, and write guide-git.js.

Every transcript comes from git itself, run with the game's settings (`gitcmd.BASE_CONFIG`, no
pager, no editor, no colours) and fixed dates, so the hashes are the same on every run. The
branch and merge cards' commands run on a terminal of their own, as in the game's terminal: git
then names branches in ``git log``, and ``ls`` prints in columns; what is kept is what the screen
shows (`shown`). The one change to what git printed: the temporary folder's path is written as
``/home/you``.
``test_guide_capture.py`` regenerates it and checks the page's copy is the same, byte for byte.
To regenerate after a change to git or to the story:

    uv run python tests/guide_capture.py

The conflict is the "Markers decoded" prototype's: a 7-line launch checklist where you aim for
the Moon on ``main`` and Alex for Jupiter on ``alex-route``.
"""

import fcntl
import json
import os
import pty
import re
import shutil
import struct
import subprocess
import tempfile
import termios
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any

from firstcommit import commands, gitcmd
from firstcommit.records import Keep

STATIC = Path(__file__).resolve().parents[1] / "src" / "firstcommit" / "web" / "static"
TARGET = STATIC / "guide-git.js"
YOU = gitcmd.Person("You", "you@station.space")
ALEX = gitcmd.Person("Alex", "alex@station.space")
START = 1760000000
SHOWN_HOME = "/home/you"
CARDS = 1780300800
"""When the branch and merge cards' story starts (2026-06-01): each of its commits has a fixed minute after it."""
TERMINAL = {"TERM": "xterm-256color", "COLUMNS": "80", "LINES": "24"}
"""The terminal the cards' commands run on: 80 columns, as a narrow game terminal."""
CLEAR_LINE = "\x1b[K"

CHECKLIST = """LAUNCH CHECKLIST
1. Seal the hatch
2. Fuel tanks: half
3. Shields: on
4. Course: Mars
5. Music: off
6. Snack: crackers
7. Wave goodbye to base
"""


def shown(raw: str) -> str:
    """
    Give what a terminal's output leaves on screen.

    A carriage return goes back to the start of the line, ESC [K clears the rest of it (git's
    "Waiting for your editor" hint goes that way), and the terminal's carriage return and line feed pairs become plain line feeds.

    Parameters
    ----------
    raw : str
        What the terminal received.

    Returns
    -------
    str
        The lines as the screen shows them.

    Raises
    ------
    ValueError
        If any other escape sequence is left: the screen would show something else.
    """
    lines = []
    for line in raw.replace("\r\n", "\n").split("\n"):
        screen = ""
        for part in line.split("\r"):
            clear = part.startswith(CLEAR_LINE)
            part = part.removeprefix(CLEAR_LINE)
            screen = part if clear else part + screen[len(part) :]
        if "\x1b" in screen:
            raise ValueError(f"an escape sequence is left in {screen!r}")
        lines.append(screen)
    return "\n".join(lines)


def on_terminal(command: str, here: Path, environment: dict[str, str]) -> str:
    """
    Run bash code on a terminal of its own, 80 columns wide, and give everything it wrote.

    Parameters
    ----------
    command : str
        Bash code.
    here : Path
        Where it runs.
    environment : dict[str, str]
        Its variables.

    Returns
    -------
    str
        What the terminal received, standard output and standard error in the order written.
    """
    main, side = pty.openpty()
    fcntl.ioctl(side, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    process = subprocess.Popen(["bash", "-c", command], cwd=here, env={**environment, **TERMINAL}, stdin=side, stdout=side, stderr=side, start_new_session=True)
    os.close(side)
    chunks = []
    while True:
        try:
            chunk = os.read(main, 4096)
        except OSError:  # EIO: the terminal's other end closed
            break
        if not chunk:
            break
        chunks.append(chunk)
    process.wait()
    os.close(main)
    return b"".join(chunks).decode()


@dataclass
class Story:
    """
    A run of commands in one temporary folder, each recorded with what it printed.

    Every command runs one minute after the one before, as the person `who`, in `here`.
    """

    work: Path
    here: Path
    who: gitcmd.Person = YOU
    tick: int = START
    runs: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def environment(self) -> dict[str, str]:
        """
        Give the environment of the next command: the game's git settings, `who` and the next minute.

        Returns
        -------
        dict[str, str]
            The variables to run it with.
        """
        self.tick += 60
        when = f"@{self.tick} +0000"
        return {
            "PATH": os.environ["PATH"],
            "HOME": str(self.work),
            "HISTFILE": "/dev/null",
            "LC_ALL": "C",
            "GIT_CONFIG_GLOBAL": str(self.work / ".gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            **gitcmd.config_entries({**gitcmd.PLAYER_SETTINGS, "color.ui": "never"}),
            "GIT_AUTHOR_NAME": self.who.name,
            "GIT_AUTHOR_EMAIL": self.who.email,
            "GIT_COMMITTER_NAME": self.who.name,
            "GIT_COMMITTER_EMAIL": self.who.email,
            "GIT_AUTHOR_DATE": when,
            "GIT_COMMITTER_DATE": when,
        }

    def quiet(self, command: str) -> str:
        """
        Run a setup command no card shows, and give what it printed.

        Parameters
        ----------
        command : str
            Bash code.

        Returns
        -------
        str
            Its standard output.

        Raises
        ------
        subprocess.CalledProcessError
            If it fails: the story is wrong.
        """
        return subprocess.run(["bash", "-c", command], cwd=self.here, env=self.environment(), capture_output=True, text=True, check=True).stdout

    def step(self, name: str, command: str, picks: Mapping[str, Sequence[Keep]] | None = None, terminal: bool = False) -> None:
        """
        Run a command a card shows, and add it with everything it printed to the transcript `name`.

        Standard output and standard error are kept in the order git wrote them. A command that
        fails is kept too: what git says then is part of the lesson.

        Parameters
        ----------
        name : str
            The transcript, a key of GuideGit.runs.
        command : str
            Bash code, as the player would type it.
        picks : Mapping[str, Sequence[Keep]] | None
            For ``git mergetool``, the merge panel's clicks, written while the game's tool waits
            (`firstcommit.commands.run_with_panel`); the tool's game home is the work folder's.
        terminal : bool
            Run it on a terminal, and keep what the screen shows.
        """
        argv = ["bash", "-c", command]
        if picks:
            printed = commands.run_with_panel(argv, self.here, {**self.environment(), "FIRSTCOMMIT_HOME": str(self.work / ".firstcommit")}, picks)[1]
        elif terminal:
            printed = shown(on_terminal(command, self.here, self.environment()))
        else:
            printed = subprocess.run(argv, cwd=self.here, env=self.environment(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False).stdout
        self.runs.setdefault(name, []).append({"command": command, "output": printed.replace(str(self.work), SHOWN_HOME)})

    def at(self, minute: int) -> None:
        """
        Set the clock so the next command runs `minute` minutes into the cards' story.

        Parameters
        ----------
        minute : int
            Minutes after `CARDS`.
        """
        self.tick = CARDS + (minute - 1) * 60


def edit(path: Path, old: str, new: str) -> None:
    """
    Replace one line of a file.

    Parameters
    ----------
    path : Path
        The file.
    old : str
        The line as it is.
    new : str
        The line it becomes.
    """
    path.write_text(path.read_text().replace(f"{old}\n", f"{new}\n"))


def ship(story: Story) -> None:
    """
    Play your ship's story: one repository from git init to a reset, with a mothership and Alex.

    Parameters
    ----------
    story : Story
        The story, in its work folder.
    """
    story.quiet("git init -q --bare mothership.git && mkdir ship")
    story.here = story.work / "ship"
    for part in (desk, names, branches, crew):
        part(story)


def desk(story: Story) -> None:
    """
    Play the desk: a repository made, files staged, committed, restored and ignored.

    Parameters
    ----------
    story : Story
        The story, in the ship.
    """
    step, quiet = story.step, story.quiet
    star_map = story.here / "map.txt"

    step("init", "git init")
    star_map.write_text("Star map: Mars, Jupiter\n")
    step("ls", "ls")
    step("ls", "ls -a")
    step("status-new", "git status")
    step("add", "git add map.txt")
    step("add", "git status")
    step("commit", 'git commit -m "Add the star map"')

    star_map.write_text("Star map: Mars, Jupiter, Saturn\n")
    step("diff", "git diff")
    step("diff", "git add map.txt")
    step("diff", "git diff --staged")
    step("commit-2", 'git commit -m "Add Saturn"')
    step("log", "git log")

    (story.here / "fuel.txt").write_text("fuel: full\n")
    star_map.write_text("Star map: Mars, Jupiter, Saturn, Uranus\n")
    quiet("git add fuel.txt")
    step("status", "git status")
    quiet('git commit -q -m "Fill the tanks" fuel.txt')

    star_map.write_text("Star map: Mars, Saturn\n")
    step("restore", "git restore map.txt")
    step("restore", "git status")

    star_map.write_text("Star map: Mars, Jupiter, Saturn, Neptune\n")
    quiet("git add map.txt")
    step("restore-staged", "git restore --staged map.txt")
    step("restore-staged", "git status")
    quiet("git restore map.txt")

    (story.here / "notes.txt").write_text("secret\n")
    quiet("git add notes.txt")
    step("rm-cached", "git rm --cached notes.txt")
    step("rm-cached", "git status")
    (story.here / "notes.txt").unlink()

    quiet("mkdir sim-output && touch sim-output/run1.log")
    step("gitignore", "git status --short")
    step("gitignore", 'echo "sim-output/" > .gitignore')
    step("gitignore", "git status --short")
    quiet('git add .gitignore && git commit -q -m "Ignore the simulator output"')


def names(story: Story) -> None:
    """
    Play the names: the mothership named and pushed to, then names put on commits and taken off.

    Parameters
    ----------
    story : Story
        The story, in the ship.
    """
    step, quiet = story.step, story.quiet

    step("remote-add", "git remote add origin ../mothership.git")
    step("remote-add", "git remote -v")
    step("push-first", "git push -u origin main")

    quiet("git branch test-run")
    quiet("git branch")
    step("branch-v", "git branch -v")
    step("branch-v", "git branch -r")
    first = quiet("git rev-parse --short HEAD~3").strip()
    step("branch-at", "git log --oneline")
    step("branch-at", f"git branch first-route {first}")
    step("branch-at", "git branch -v")
    quiet("git branch -d test-run")
    quiet("git branch -d first-route")


def branches(story: Story) -> None:
    """
    Play the branches: a new course switched to, drawn, sent up and merged; the cards' own transcripts come from `cards`.

    Parameters
    ----------
    story : Story
        The story, in the ship.
    """
    step, quiet = story.step, story.quiet
    star_map = story.here / "map.txt"

    quiet("git switch -c scout")
    (story.here / "probe.txt").write_text("probe: ready\n")
    quiet('git add probe.txt && git commit -q -m "Ready the probe"')
    quiet("git switch main")
    quiet("ls")
    star_map.write_text("Star map: Mars, Jupiter, Saturn, Pluto\n")
    quiet('git commit -q -am "Add Pluto"')
    quiet("git log --oneline --graph --all")
    quiet("git checkout scout")
    quiet("git checkout -b night-watch")
    quiet("git switch -q main")
    step("push-branch", "git push -u origin scout")
    quiet("git merge scout")
    quiet("git log --graph --oneline")
    step("push", "git push")


def crew(story: Story) -> None:
    """
    Play the crew: Alex's commits fetched and pulled, a refused push, then the undos and a clone.

    Parameters
    ----------
    story : Story
        The story, in the ship.
    """
    step, quiet = story.step, story.quiet
    work = story.work
    star_map = work / "ship" / "map.txt"
    alex(story, "snack.txt", "snack: noodles\n", "Pack the snacks")
    story.here = work / "ship"
    step("fetch", "git fetch")
    step("fetch", "git status")
    step("pull", "git pull")

    alex(story, "music.txt", "music: on\n", "Turn the music on")
    story.here = work / "ship"
    (story.here / "lights.txt").write_text("lights: dim\n")
    quiet('git add lights.txt && git commit -q -m "Dim the lights"')
    step("pull-no-rebase", "git push")
    step("pull-no-rebase", "git pull --no-rebase")
    step("pull-no-rebase", "git log --oneline --graph -4")

    (story.here / "radio.txt").write_text("radio: loud\n")
    quiet('git add radio.txt && git commit -q -m "Turn the radio up"')
    step("revert", "git revert HEAD")
    step("revert", "git log --oneline -3")

    star_map.write_text("Star map: Mars, Jupiter, Saturn, Pluto, Eris\n")
    quiet('git commit -q -am "Add Eris"')
    star_map.write_text("Star map: Mars, Jupiter, Saturn, Pluto, Eris, Ceres\n")
    step("reset", "git status --short")
    step("reset", "git reset --hard HEAD~1")
    step("reset", "git status --short")

    story.here = work
    step("clone", "git clone mothership.git crew")
    step("clone", "ls crew")


def alex(story: Story, name: str, text: str, message: str) -> None:
    """
    Have Alex add one file in Alex's own clone and push it to the mothership.

    Parameters
    ----------
    story : Story
        The story; it is left in Alex's clone, as you.
    name : str
        The file Alex adds.
    text : str
        Its text.
    message : str
        Alex's commit message.
    """
    clone = story.work / "alex"
    story.here = story.work
    if not clone.exists():
        story.quiet("git clone -q mothership.git alex")
    story.here = clone
    story.who = ALEX
    story.quiet("git pull -q --no-rebase")
    (clone / name).write_text(text)
    story.quiet(f'git add {name} && git commit -q -m "{message}" && git push -q')
    story.who = YOU


def move_log(story: Story) -> None:
    """
    Make a short move log in a small repository of its own: two commits, then a reset.

    Parameters
    ----------
    story : Story
        The story, in its work folder.
    """
    story.here = story.work
    story.quiet("mkdir log && git -C log init -q")
    story.here = story.work / "log"
    story.quiet('echo one > a.txt && git add a.txt && git commit -q -m "First course"')
    story.quiet('echo two >> a.txt && git commit -q -am "Second course"')
    story.quiet("git reset -q --hard HEAD~1")
    story.step("reflog", "git reflog")


def resolve(story: Story, name: str, keep: list[str]) -> dict[str, str]:
    """
    Resolve the conflict in a copy of the checklist: `keep` replaces the whole conflict block.

    Parameters
    ----------
    story : Story
        The story; its `here` is the conflicted checklist.
    name : str
        The way out: "yours", "theirs" or "both".
    keep : list[str]
        The lines kept, in order.

    Returns
    -------
    dict[str, str]
        The clean file ("resolved") and the merge commit's "hash parent parent" ("head").
    """
    copy = story.work / name
    shutil.copytree(story.here, copy)
    story.here = copy
    checklist = copy / "checklist.txt"
    block = re.compile(r"^<{7} .*?^>{7} [^\n]*\n", re.MULTILINE | re.DOTALL)
    checklist.write_text(block.sub("".join(f"{line}\n" for line in keep), checklist.read_text()))
    story.step(f"conflict-add-{name}", "git add checklist.txt")
    story.step(f"conflict-add-{name}", "git status")
    story.step(f"conflict-commit-{name}", "git commit --no-edit")
    story.step(f"conflict-commit-{name}", "git log --graph --oneline")
    return {"resolved": checklist.read_text(), "head": story.quiet("git log -1 --format='%h %p'").strip()}


def conflict(story: Story) -> dict[str, Any]:
    """
    Build the checklist's real merge conflict and resolve it three ways.

    Parameters
    ----------
    story : Story
        The story, in its work folder.

    Returns
    -------
    dict[str, Any]
        The file's three stages, the file with markers, the three commits' short hashes, and for
        each way out the clean file and the merge commit.
    """
    work = story.work
    story.here = work
    story.quiet("mkdir checklist && git -C checklist init -q")
    folder = work / "checklist"
    story.here = folder
    checklist = folder / "checklist.txt"
    checklist.write_text(CHECKLIST)
    story.quiet('git add checklist.txt && git commit -q -m "Write the launch checklist" && git switch -q -c alex-route')
    edit(checklist, "4. Course: Mars", "4. Course: Jupiter")
    edit(checklist, "6. Snack: crackers", "6. Snack: space noodles")
    story.who = ALEX
    story.quiet('git commit -q -am "Head for Jupiter, pack noodles"')
    story.who = YOU
    story.quiet("git switch -q main")
    edit(checklist, "2. Fuel tanks: half", "2. Fuel tanks: full")
    edit(checklist, "4. Course: Mars", "4. Course: the Moon")
    story.quiet('git commit -q -am "Fill the tanks, aim for the Moon"')

    for name, lines in (
        ("merge-abort", ["git merge alex-route", "git merge --abort", "git status"]),
        ("restore-theirs", ["git merge alex-route", "git restore --theirs checklist.txt", "cat checklist.txt"]),
        ("mergetool", ["git merge alex-route", "git mergetool", "git status"]),
    ):
        story.here = folder
        copy = work / name
        shutil.copytree(folder, copy)
        story.here = copy
        for line in lines:
            story.step(name, line, {"checklist.txt": ["yours"]} if line == "git mergetool" else None)

    story.here = folder
    story.step("conflict-merge", "git merge alex-route")
    story.step("conflict-status", "git status")
    data: dict[str, Any] = {
        "base": story.quiet("git show :1:checklist.txt"),
        "ours": story.quiet("git show :2:checklist.txt"),
        "theirs": story.quiet("git show :3:checklist.txt"),
        "markers": checklist.read_text(),
        "yourCommit": story.quiet("git rev-parse --short main").strip(),
        "alexCommit": story.quiet("git rev-parse --short alex-route").strip(),
        "baseCommit": story.quiet("git rev-parse --short $(git merge-base main alex-route)").strip(),
    }
    ways = {"yours": ["4. Course: the Moon"], "theirs": ["4. Course: Jupiter"], "both": ["4. Course: the Moon", "4. Course: Jupiter"]}
    resolved: dict[str, str] = {}
    head: dict[str, str] = {}
    for name, keep in ways.items():
        story.here = folder
        made = resolve(story, name, keep)
        resolved[name], head[name] = made["resolved"], made["head"]
    return {**data, "resolved": resolved, "head": head}


def scene(story: Story, moves: int) -> None:
    """
    Start a fresh repository for one of the cards' scenes, `moves` steps into their one story, in ``project``, the folder the game's terminal opens in.

    Every scene is rebuilt from the start with the same minutes, so a commit has the same hash on
    every card that shows it. The steps: 1 *Start the project* and 2 *Plot the route* on
    ``main``; 3 ``scout`` with *Ready the probe*, back on ``main``; 4 *Fill the tanks* on ``main``.

    Parameters
    ----------
    story : Story
        The story; it is left in the scene's folder.
    moves : int
        How many steps to play, 2 to 4.
    """
    story.here = story.work / "project"
    shutil.rmtree(story.here, ignore_errors=True)
    story.here.mkdir()
    commits = [
        ("notes.txt", "Notes\n", "Start the project"),
        ("route.txt", "Route: Moon\n", "Plot the route"),
        ("probe.txt", "probe=ready\n", "Ready the probe"),
        ("fuel.txt", "fuel=full\n", "Fill the tanks"),
    ]
    story.quiet("git init -q")
    for minute, (file, text, message) in enumerate(commits[:moves], start=1):
        if minute == 3:
            story.quiet("git switch -q -c scout")
        (story.here / file).write_text(text)
        story.at(minute)
        story.quiet(f'git add {file} && git commit -q -m "{message}"')
        if minute == 3:
            story.quiet("git switch -q main")


def naming(story: Story) -> None:
    """
    Play the cards that put names on and move HEAD: git branch, git switch, git switch -c and the older checkouts.

    Parameters
    ----------
    story : Story
        The story.
    """
    step = partial(story.step, terminal=True)
    scene(story, 2)
    step("branch", "git branch scout")
    step("branch", "git branch")
    step("branch", "git log --oneline")

    scene(story, 3)
    step("switch", "ls")
    step("switch", "git switch scout")
    step("switch", "ls")
    step("switch", "git log --oneline --all")
    step("switch", "git switch main")
    step("switch", "ls")

    scene(story, 3)
    (story.here / "notes.txt").write_text("Notes\nFuel: 80%\n")
    step("switch-carry", "git switch scout")
    step("switch-carry", "git status --short")

    scene(story, 2)
    story.quiet("git switch -q -c scout")
    (story.here / "route.txt").write_text("Route: Mars\n")
    story.at(3)
    story.quiet('git commit -q -am "Head for Mars" && git switch -q main')
    (story.here / "route.txt").write_text("Route: Moon, Phobos\n")
    step("switch-refused", "git switch scout")

    scene(story, 2)
    step("switch-c", "git switch -c lights")
    step("switch-c", "git log --oneline")
    step("switch-missing", "git switch lights-on")
    scene(story, 2)
    step("checkout-b", "git checkout -b lights")
    scene(story, 3)
    step("checkout", "git checkout scout")


def deleting(story: Story) -> None:
    """
    Play git branch -d: a name taken off after a merge, and git's two refusals.

    Parameters
    ----------
    story : Story
        The story.
    """
    step = partial(story.step, terminal=True)
    scene(story, 3)
    story.at(4)
    story.quiet("git merge -q scout")
    step("branch-d", "git branch -d scout")
    step("branch-d", "git log --oneline --all")
    scene(story, 4)
    step("branch-d-refused", "git branch -d scout")
    scene(story, 3)
    story.quiet("git switch -q scout")
    step("branch-d-here", "git branch -d scout")


def merging(story: Story) -> str:
    """
    Play the merges, a fast-forward and a merge commit, the graph before and after, and give the merge's message.

    Parameters
    ----------
    story : Story
        The story.

    Returns
    -------
    str
        The text git hands the editor for ``git merge scout``, comments included.
    """
    step = partial(story.step, terminal=True)
    scene(story, 3)
    story.at(4)
    step("merge-ff", "git merge scout")
    step("merge-ff", "git log --oneline --graph --all")

    scene(story, 4)
    step("log-graph", "git log --oneline --graph --all")
    step("log-graph-head", "git log --oneline --graph")

    scene(story, 4)
    story.at(5)
    step("merge", "git merge scout")
    step("merge", "git log --oneline --graph --all")
    step("log-graph-merged", "git log --oneline --graph --all")

    scene(story, 4)
    story.at(5)
    step("merge-no-edit", "git merge --no-edit scout")
    step("merge-no-edit", "git log --oneline -1")

    scene(story, 4)
    editor = story.work / "editor.sh"
    editor.write_text(f'#!/bin/sh\ncp "$1" "{story.work}/message.txt"\n')
    editor.chmod(0o755)
    story.at(5)
    story.quiet(f"GIT_MERGE_AUTOEDIT=yes GIT_EDITOR={editor} git merge -q scout")
    return (story.work / "message.txt").read_text()


def capture(work: Path) -> dict[str, Any]:
    """
    Run the whole story in an empty folder and give everything git printed.

    Parameters
    ----------
    work : Path
        An empty folder; the story's repositories are made in it.

    Returns
    -------
    dict[str, Any]
        ``version`` (git's), ``runs`` (each transcript, [{command, output}], by name),
        ``conflict`` and ``mergeMessage`` (what git asks the editor to confirm for a merge).
    """
    (work / ".gitconfig").write_text(gitcmd.BASE_CONFIG)
    story = Story(work=work, here=work)
    ship(story)
    move_log(story)
    found = conflict(story)
    naming(story)
    deleting(story)
    message = merging(story)
    version = story.quiet("git --version").strip()
    return {"version": version, "runs": dict(sorted(story.runs.items())), "conflict": found, "mergeMessage": message}


def page(data: dict[str, Any]) -> str:
    """
    Write the page's data module from a capture.

    Parameters
    ----------
    data : dict[str, Any]
        What `capture` gave.

    Returns
    -------
    str
        The text of guide-git.js.
    """
    return f'''"use strict";

/*
 * GENERATED by tests/guide_capture.py from {data["version"]}: do not edit by hand. Regenerate
 * with `uv run python tests/guide_capture.py`; test_guide_capture.py checks this file matches.
 * What real git printed, for the field guide's command cards and its conflict, with the game's
 * git settings and fixed dates, so the hashes are the same on every run. runs[name] is a
 * transcript, [{{command, output}}]; conflict is one real merge conflict (the launch checklist):
 * the file's three stages, the file with markers, and for each way to resolve it (yours, theirs,
 * both) the clean file and the merge commit's "hash parent parent"; mergeMessage is the text git
 * hands the editor for a merge commit. The branch and merge cards' transcripts were run on a
 * terminal, as the game's is, and keep what its screen showed. Data only. Defines one global,
 * GuideGit.
 */

/* exported GuideGit */

const GuideGit = Object.freeze({json.dumps(data, indent=2, ensure_ascii=False)});
'''


def generate() -> str:
    """
    Capture the story in a fresh temporary folder and give the text of guide-git.js.

    Returns
    -------
    str
        The text of guide-git.js.
    """
    with tempfile.TemporaryDirectory() as folder:
        return page(capture(Path(folder)))


if __name__ == "__main__":
    TARGET.write_text(generate())
    print(f"wrote {TARGET}")
