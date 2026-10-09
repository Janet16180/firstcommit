"""
Recorder for the Merge tools mission: build the level's repository with fixed identities and
dates in a temporary HOME, then type each scene's lines in a real interactive bash on a pty and
save the exact terminal output.

Run: python3 record.py <worktree src folder> <out folder>
Never touches the user's HOME, ~/.gitconfig or ~/.bash_history: HOME is a new temporary folder,
GIT_CONFIG_NOSYSTEM=1 and HISTFILE=/dev/null.
"""

import os
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SRC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
TOOL = Path(__file__).resolve().parent / "tool.py"
sys.path.insert(0, str(SRC))

from firstcommit import markers  # noqa: E402

PROMPT = "project $ "
HEAD_LINES = "Launch plan\nWindow: {window}\nPilot: Cadet\nDestination: Base 7\nCargo:\n- water\n- fuel cells\n"
START = HEAD_LINES.format(window="06:00")
OURS = HEAD_LINES.format(window="07:00") + "- oxygen\n"
THEIRS = HEAD_LINES.format(window="05:30") + "- spare antenna\n"
GAME_CONFIG = (
    "[init]\n\tdefaultBranch = main\n[core]\n\tpager = cat\n\teditor = true\n\texcludesFile =\n\tattributesFile =\n"
    "[user]\n\tname = Cadet\n\temail = cadet@example.com\n\tuseConfigOnly = true\n[color]\n\tui = never\n"
)
TOOL_SETTINGS = {
    "merge.tool": "firstcommit",
    "mergetool.firstcommit.cmd": f"python3 '{TOOL}' \"$MERGED\"",
    "mergetool.firstcommit.trustExitCode": "true",
    "mergetool.keepBackup": "false",
    "mergetool.prompt": "false",
    "mergetool.writeToTemp": "true",
}
PLAIN_TOOL = {
    "merge.tool": "firstcommit",
    "mergetool.firstcommit.cmd": f"python3 '{TOOL}' \"$MERGED\"",
    "mergetool.firstcommit.trustExitCode": "true",
}


def environment(home: Path, settings: dict[str, str]) -> dict[str, str]:
    env = {
        "HOME": str(home),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "TERM": "xterm-256color",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "HISTFILE": "/dev/null",
        "TMPDIR": str(home / "tmp"),
        "FIRSTCOMMIT_SRC": str(SRC),
        "GIT_AUTHOR_DATE": "2026-06-04T09:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-06-04T09:00:00+00:00",
        "GIT_CONFIG_COUNT": str(len(settings) + 2),
        "GIT_CONFIG_KEY_0": "core.editor",
        "GIT_CONFIG_VALUE_0": "true",
        "GIT_CONFIG_KEY_1": "core.pager",
        "GIT_CONFIG_VALUE_1": "cat",
    }
    for index, (key, value) in enumerate(settings.items(), start=2):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    return env


def git(env: dict[str, str], cwd: Path, *args: str, who: tuple[str, str] = ("Cadet", "cadet@example.com"), day: int = 1) -> None:
    when = f"2026-06-{day:02}T09:00:00+00:00"
    run_env = {**env, "GIT_AUTHOR_NAME": who[0], "GIT_AUTHOR_EMAIL": who[1], "GIT_COMMITTER_NAME": who[0],
               "GIT_COMMITTER_EMAIL": who[1], "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(["git", *args], cwd=cwd, env=run_env, check=True, capture_output=True)


def build(env: dict[str, str], root: Path) -> Path:
    project = root / "project"
    subprocess.run(["git", "init", "-q", str(project)], env=env, check=True)

    def commit(text: str, message: str, day: int, who: tuple[str, str] = ("Cadet", "cadet@example.com")) -> None:
        (project / "launch.txt").write_text(text)
        git(env, project, "add", "launch.txt", who=who, day=day)
        git(env, project, "commit", "-q", "-m", message, who=who, day=day)

    commit(START, "Write the launch plan", 1)
    git(env, project, "switch", "-q", "-c", "scout")
    commit(THEIRS, "The window closes early: launch at 05:30, and pack a spare antenna", 2, ("Alex", "alex@example.com"))
    git(env, project, "switch", "-q", "main")
    commit(OURS, "Launch at 07:00 and pack oxygen", 3)
    return project


class Session:
    def __init__(self, env: dict[str, str], cwd: Path) -> None:
        self.cwd = cwd
        self.titles: list[str] = []
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(cwd)
            os.execve("/bin/bash", ["bash", "--norc", "--noprofile", "-i"], {**env, "PS1": PROMPT})
        self.transcript = ""
        self.read_until_prompt()
        self.transcript = ""

    def read(self, timeout: float) -> str:
        chunks = []
        ready, _, _ = select.select([self.fd], [], [], timeout)
        while ready:
            try:
                data = os.read(self.fd, 4096)
            except OSError:
                break
            if not data:
                break
            chunks.append(data.decode("utf-8", "replace"))
            ready, _, _ = select.select([self.fd], [], [], 0.05)
        return "".join(chunks)

    def clean(self, text: str) -> str:
        for found in re.findall(r"\x1b\]0;([^\x07]*)\x07", text):
            self.titles.append(found)
        text = re.sub(r"\x1b\]0;[^\x07]*\x07", "", text)
        text = re.sub(r"\x1b\[\?2004[hl]", "", text)
        return text.replace("\r\n", "\n").replace("\r", "")

    def read_until_prompt(self, on_output=None, limit: float = 20.0) -> str:
        got = ""
        end = time.time() + limit
        while time.time() < end:
            got += self.clean(self.read(0.2))
            try:
                acted = on_output is not None and on_output(got)
            except HungUp:
                self.transcript += got
                raise
            if acted:
                on_output = None
            if got.endswith(PROMPT):
                break
        self.transcript += got
        return got

    def typed_so_far(self) -> str:
        return self.transcript

    def type(self, line: str, on_output=None) -> str:
        os.write(self.fd, (line + "\n").encode())
        return self.read_until_prompt(on_output)

    def close(self) -> None:
        os.write(self.fd, b"exit\n")
        time.sleep(0.2)
        os.close(self.fd)
        os.waitpid(self.pid, 0)


def atomic_write(path: Path, data: bytes) -> None:
    """Write as plan.md proposes: a temporary file in the same folder, then os.replace."""
    handle = tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False)
    with handle:
        handle.write(data)
    os.chmod(handle.name, path.stat().st_mode & 0o777)
    os.replace(handle.name, path)


class HungUp(Exception):
    """The terminal was closed while a line ran."""


def hangup(session, project, notes):
    def act(got: str) -> bool:
        if "Waiting for the merge panel" not in got:
            return False
        time.sleep(0.4)
        os.close(session.fd)
        raise HungUp

    return act


def panel_write(project: Path, choices: list[str], listing: list[str]):
    """Play the panel's Write once the tool waits: rewrite the blocks with markers.resolve."""

    def act(got: str) -> bool:
        if "Waiting for the merge panel" not in got:
            return False
        time.sleep(0.4)
        listing.append(" ".join(sorted(os.listdir(project))))
        path = project / "launch.txt"
        atomic_write(path, markers.resolve(path.read_bytes(), choices))
        return True

    return act


def ctrl_c(session: "Session", listing: list[str], project: Path, cue: str = "Waiting for the merge panel"):
    def act(got: str) -> bool:
        if cue not in got:
            return False
        time.sleep(0.4)
        listing.append(" ".join(sorted(os.listdir(project))))
        os.write(session.fd, b"\x03")
        return True

    return act


def scene(name: str, settings: dict[str, str], lines) -> None:
    home = Path(tempfile.mkdtemp(prefix="mt-home-"))
    root = Path(tempfile.mkdtemp(prefix="mt-lab-"))
    try:
        (home / ".gitconfig").write_text(GAME_CONFIG)
        (home / "tmp").mkdir()
        env = environment(home, settings)
        project = build(env, root)
        session = Session(env, project)
        notes: list[str] = []
        text = PROMPT
        for line, action in lines:
            hook = action(session, project, notes) if action else None
            try:
                session.type(line, hook)
            except HungUp:
                os.waitpid(session.pid, 0)
                time.sleep(1.0)
                notes.append("after the hang-up, left in TMPDIR: " + " ".join(sorted(str(p.relative_to(home / "tmp")) for p in (home / "tmp").rglob("*"))))
                text += session.transcript + "\n[the terminal closes; a new one opens]\n" + PROMPT
                session = Session(env, project)
        session.close()
        text += session.transcript if text.endswith(PROMPT) and not session.transcript.startswith(PROMPT) else session.transcript
        (OUT / f"{name}.txt").write_text(text)
        notes.append("left in TMPDIR: " + " ".join(sorted(str(p.relative_to(home / "tmp")) for p in (home / "tmp").rglob("*"))))
        extra = [f"title: {title!r}" for title in session.titles] + [f"folder while the tool waited: {entry}" for entry in notes]
        (OUT / f"{name}.notes.txt").write_text("\n".join(extra) + "\n")
        print(f"== {name}\n{text}\n-- {extra}\n")
    finally:
        shutil.rmtree(home)
        shutil.rmtree(root)


def write(choices):
    return lambda session, project, notes: panel_write(project, choices, notes)


def cancel(session, project, notes):
    return ctrl_c(session, notes, project)


def edit_by_hand(text: str):
    def act(session, project, notes):
        (project / "launch.txt").write_text(text)
        return None

    return act


def typing_then_write(keys: str, choices):
    def act(session, project, notes):
        inner = panel_write(project, choices, notes)

        def both(got: str) -> bool:
            if "Waiting for the merge panel" not in got:
                return False
            os.write(session.fd, keys.encode())
            time.sleep(0.3)
            return inner(got)

        return both

    return act


def half_by_hand(choices):
    def act(session, project, notes):
        path = project / "launch.txt"
        path.write_text(path.read_text().replace("<<<<<<< HEAD\nWindow: 07:00\n=======\nWindow: 05:30\n>>>>>>> scout\n", "Window: 05:30\n"))
        notes.append("before the tool: " + path.read_text().replace("\n", " | "))
        return panel_write(project, choices, notes)

    return act


def delete_while_waiting(session, project, notes):
    def act(got: str) -> bool:
        if "Waiting for the merge panel" not in got:
            return False
        time.sleep(0.4)
        (project / "launch.txt").unlink()
        return True

    return act


RESOLVED = HEAD_LINES.format(window="05:30") + "- oxygen\n- spare antenna\n"

OUT.mkdir(parents=True, exist_ok=True)
scene("1-mission", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", write(["theirs", "both"])),
    ("git status", None),
    ("git commit --no-edit", None),
    ("git log --oneline --graph", None),
    ("cat launch.txt", None),
])
scene("2-before-merge", TOOL_SETTINGS, [
    ("git mergetool", None),
    ("echo $?", None),
])
scene("3-cancel", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", cancel),
    ("echo $?", None),
    ("git status", None),
    ("cat launch.txt", None),
])
scene("4-after-commit", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", write(["theirs", "both"])),
    ("git commit --no-edit", None),
    ("git mergetool", None),
])
scene("5-markers-added", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git add launch.txt", None),
    ("git mergetool", None),
    ("git status", None),
])
scene("6-cleaned-by-hand", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", edit_by_hand(RESOLVED)),
    ("git status --short", None),
])
scene("7-git-defaults", PLAIN_TOOL, [
    ("git merge --no-edit scout", None),
    ("git mergetool", write(["theirs", "both"])),
    ("ls", None),
    ("git status --short", None),
])
scene("8-conflict-file", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("cat launch.txt", None),
    ("git log --oneline --all", None),
])
scene("9-typing-while-waiting", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", typing_then_write("ls -l\n", ["theirs", "both"])),
    ("git status --short", None),
])
scene("10-one-block-left", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", half_by_hand(["both"])),
    ("cat launch.txt", None),
])
scene("11-ctrl-c-any-tool", {**TOOL_SETTINGS, "mergetool.firstcommit.cmd": "sleep 30"}, [
    ("git merge --no-edit scout", None),
    ("git mergetool", lambda session, project, notes: ctrl_c(session, notes, project, "{remote}: modified file")),
    ("echo $?", None),
    ("git status --short", None),
])
scene("13-file-deleted", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", delete_while_waiting),
    ("echo $?", None),
    ("git status --short", None),
])
scene("14-twice", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", cancel),
    ("git mergetool", write(["theirs", "both"])),
    ("git add launch.txt", None),
    ("git commit --no-edit", None),
])
scene("12-cancel-defaults", PLAIN_TOOL, [
    ("git merge --no-edit scout", None),
    ("git mergetool", cancel),
    ("ls", None),
])
scene("15-restore-theirs", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git restore --theirs launch.txt", None),
    ("cat launch.txt", None),
])
scene("16-wrong-pick", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", write(["yours", "both"])),
    ("git merge --abort", None),
    ("git merge --no-edit scout", None),
])
scene("17-git-guesses", {}, [
    ("git merge --no-edit scout", None),
    ("git mergetool", lambda session, project, notes: ctrl_c(session, notes, project, "Hit return to start merge resolution tool")),
])
scene("18-hangup", TOOL_SETTINGS, [
    ("git merge --no-edit scout", None),
    ("git mergetool", hangup),
    ("git status --short", None),
    ("cat launch.txt", None),
])
