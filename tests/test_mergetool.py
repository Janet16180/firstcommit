import contextlib
import io
import os
import pty
import select
import signal
import termios
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from firstcommit import game, gitcmd, markers, mergetool, runner, save
from firstcommit.termlab import store

CONFLICTED = b"Launch plan\n<<<<<<< HEAD\nWindow: 07:00\n=======\nWindow: 05:30\n>>>>>>> scout\nPilot: Cadet\n"
ANSWERED = b"Launch plan\nWindow: 05:30\nPilot: Cadet\n"


@pytest.fixture
def conflicted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Make the file in conflict, named as git names it: from the top of the working folder, the current folder."""
    monkeypatch.chdir(tmp_path)
    path = Path("launch.txt")
    path.write_bytes(CONFLICTED)
    return path


def later(seconds: float, action: object) -> threading.Timer:
    timer = threading.Timer(seconds, action)  # type: ignore[arg-type]
    timer.start()
    return timer


@pytest.fixture
def terminal() -> Iterator[tuple[int, int]]:
    leader, follower = pty.openpty()
    yield leader, follower
    for fd in (leader, follower):
        with contextlib.suppress(OSError):
            os.close(fd)


def drain(leader: int) -> str:
    """Read everything the terminal shows so far."""
    shown = b""
    while select.select([leader], [], [], 0.1)[0]:
        shown += os.read(leader, 65536)
    return shown.decode()


def test_the_title_names_the_tool_and_the_file_without_control_characters() -> None:
    assert mergetool.title("launch.txt") == "firstcommit-mergetool launch.txt"
    assert mergetool.title("a\x07b\x1b]0;evil\nc.txt") == "firstcommit-mergetool ab]0;evilc.txt"


def test_a_file_is_answered_once_it_is_a_plain_file_with_no_conflict_block(conflicted: Path, tmp_path: Path) -> None:
    assert not mergetool.answered(conflicted)
    conflicted.write_bytes(ANSWERED)
    assert mergetool.answered(conflicted)
    link = tmp_path / "link.txt"
    link.symlink_to(conflicted)
    assert not mergetool.answered(link)
    assert not mergetool.answered(tmp_path / "missing.txt")


def test_waiting_ends_answered_once_the_blocks_are_written_away(conflicted: Path) -> None:
    timer = later(0.1, lambda: conflicted.write_bytes(markers.resolve(CONFLICTED, ["theirs"])))
    assert mergetool.wait(conflicted, None, lambda: None, poll=0.01) == "answered"
    timer.join()


def test_waiting_ends_cancelled_on_a_ctrl_c_and_ignores_other_keys(conflicted: Path) -> None:
    keys, sent = os.pipe()
    os.write(sent, b"ls -l\r")
    timer = later(0.1, lambda: os.write(sent, b"\x03"))
    assert mergetool.wait(conflicted, keys, lambda: None, poll=0.01) == "cancelled"
    timer.join()
    os.close(keys)
    os.close(sent)


@pytest.mark.parametrize("change", ["delete", "folder", "symlink"])
def test_waiting_ends_gone_when_the_file_stops_being_a_plain_file(conflicted: Path, tmp_path: Path, change: str) -> None:
    def act() -> None:
        conflicted.unlink()
        if change == "folder":
            conflicted.mkdir()
        elif change == "symlink":
            (tmp_path / "elsewhere.txt").write_bytes(ANSWERED)
            conflicted.symlink_to(tmp_path / "elsewhere.txt")

    timer = later(0.05, act)
    assert mergetool.wait(conflicted, None, lambda: None, poll=0.01) == "gone"
    timer.join()


def test_waiting_sends_the_title_again_every_so_often(conflicted: Path) -> None:
    sent: list[float] = []
    timer = later(0.25, lambda: conflicted.write_bytes(ANSWERED))
    mergetool.wait(conflicted, None, lambda: sent.append(time.monotonic()), poll=0.01, every=0.05)
    timer.join()
    assert len(sent) >= 3


def test_a_file_already_answered_is_handed_back_to_git_at_once(conflicted: Path) -> None:
    conflicted.write_bytes(ANSWERED)
    out = io.StringIO()
    assert mergetool.run(conflicted, "en", io.StringIO(), out) == 0
    assert out.getvalue() == "launch.txt has no conflict markers left: Git stages it as it is.\n"


def test_without_a_terminal_the_tool_prints_its_two_lines_sets_no_title_and_waits_for_the_file(conflicted: Path) -> None:
    out = io.StringIO()
    timer = later(0.15, lambda: conflicted.write_bytes(ANSWERED))
    assert mergetool.run(conflicted, "en", io.StringIO(), out) == 0
    timer.join()
    assert out.getvalue() == (
        "Waiting for the merge panel: pick a side for each conflict in launch.txt, then Write.\n"
        "To stop without changing the file: Cancel in the panel, or Ctrl-C here.\n"
    )


def test_the_tool_says_so_and_fails_when_the_file_is_gone(conflicted: Path) -> None:
    out = io.StringIO()
    timer = later(0.2, conflicted.unlink)
    assert mergetool.run(conflicted, "en", io.StringIO(), out) == 1
    timer.join()
    assert out.getvalue().endswith("launch.txt is gone from the working folder.\n")


def test_the_tool_speaks_spanish_to_a_spanish_player(conflicted: Path) -> None:
    out = io.StringIO()
    timer = later(0.2, lambda: conflicted.write_bytes(ANSWERED))
    mergetool.run(conflicted, "es", io.StringIO(), out)
    timer.join()
    assert out.getvalue().startswith("Esperando el panel de merge: elige un lado para cada conflicto en launch.txt, y luego Escribir.\n")


def test_on_a_terminal_the_tool_titles_it_takes_ctrl_c_as_a_key_and_gives_the_terminal_back_as_it_was(conflicted: Path, terminal: tuple[int, int]) -> None:
    leader, follower = terminal
    before = termios.tcgetattr(follower)
    with open(follower, closefd=False) as stdin, open(follower, "w", closefd=False) as stdout:
        timer = later(0.15, lambda: os.write(leader, b"ls\r\x03"))
        status = mergetool.run(conflicted, "en", stdin, stdout)
        timer.join()
    shown = drain(leader)
    assert status == 1
    assert shown.startswith("\x1b]0;firstcommit-mergetool launch.txt\x07Waiting for the merge panel")
    assert shown.endswith("\x1b]0;\x07")
    assert "ls" not in shown
    assert termios.tcgetattr(follower) == before


def test_keys_typed_while_the_tool_waits_never_reach_the_shell_after_it(conflicted: Path, terminal: tuple[int, int]) -> None:
    leader, follower = terminal
    with open(follower, closefd=False) as stdin, open(follower, "w", closefd=False) as stdout:
        def type_then_answer() -> None:
            os.write(leader, b"rm -rf x\r")
            time.sleep(0.05)
            conflicted.write_bytes(ANSWERED)

        timer = later(0.1, type_then_answer)
        assert mergetool.run(conflicted, "en", stdin, stdout) == 0
        timer.join()
    os.write(leader, b"after\r")
    time.sleep(0.05)
    assert os.read(follower, 1024) == b"after\n"


def lab_in_conflict(game_home: Path) -> Path:
    """Build a repository paused in a merge with `launch.txt` in conflict, as a level builds one."""
    project = game_home / "labs" / "tool" / "project"
    project.mkdir(parents=True)
    gitcmd.ensure_config()

    def commit(text: str, message: str) -> None:
        (project / "launch.txt").write_text(text)
        gitcmd.output(project, "add", "launch.txt")
        gitcmd.output(project, "commit", "-q", "-m", message, when="2026-06-01T09:00:00+00:00")

    gitcmd.output(project, "init", "-q")
    commit("Window: 06:00\n", "Write the launch plan")
    gitcmd.output(project, "switch", "-q", "-c", "scout")
    commit("Window: 05:30\n", "Launch at 05:30")
    gitcmd.output(project, "switch", "-q", "main")
    commit("Window: 07:00\n", "Launch at 07:00")
    gitcmd.run(project, "merge", "--no-edit", "scout")
    return project


class Shell:
    """`git mergetool` run on a terminal of its own, with the game shell's environment, as the player types it."""

    def __init__(self, project: Path) -> None:
        env = {**game.shell_environment(os.environ), "HOME": str(save.home()), "HISTFILE": "/dev/null", "TERM": "xterm"}
        self.pid, self.leader = pty.fork()
        if self.pid == 0:
            os.chdir(project)
            os.execvpe("bash", ["bash", "--norc", "--noprofile", "-c", "git mergetool"], env)
        self.shown = ""

    def until(self, text: str, seconds: float = 20.0) -> None:
        """Read the terminal until it shows `text`."""
        deadline = time.monotonic() + seconds
        while text not in self.shown and time.monotonic() < deadline:
            if select.select([self.leader], [], [], 0.1)[0]:
                try:
                    self.shown += os.read(self.leader, 65536).decode()
                except OSError:
                    break
        assert text in self.shown, self.shown

    def status(self) -> int:
        """Read the rest, wait for the line to end, and give its exit status."""
        while select.select([self.leader], [], [], 0.2)[0]:
            try:
                chunk = os.read(self.leader, 65536)
            except OSError:
                break
            if not chunk:
                break
            self.shown += chunk.decode()
        _, raw = os.waitpid(self.pid, 0)
        os.close(self.leader)
        return os.waitstatus_to_exitcode(raw)


def test_git_mergetool_runs_the_games_tool_and_adds_the_file_the_panel_wrote(game_home: Path) -> None:
    project = lab_in_conflict(game_home)
    shell = Shell(project)
    shell.until("Waiting for the merge panel")
    assert "\x1b]0;firstcommit-mergetool launch.txt\x07" in shell.shown
    path = project / "launch.txt"
    store.replace_bytes(path, markers.resolve(path.read_bytes(), ["theirs"]))
    assert shell.status() == 0
    assert gitcmd.output(project, "status", "--porcelain").splitlines() == ["M  launch.txt"]
    assert path.read_text() == "Window: 05:30\n"
    assert sorted(entry.name for entry in project.iterdir()) == [".git", "launch.txt"]
    assert list((game_home / "tmp").iterdir()) == []


def test_ctrl_c_cancels_the_games_tool_and_git_puts_the_file_back(game_home: Path) -> None:
    project = lab_in_conflict(game_home)
    before = (project / "launch.txt").read_bytes()
    shell = Shell(project)
    shell.until("Ctrl-C here.")
    os.write(shell.leader, b"\x03")
    assert shell.status() == 1
    assert "merge of launch.txt failed" in shell.shown
    assert (project / "launch.txt").read_bytes() == before
    assert gitcmd.output(project, "status", "--porcelain").splitlines() == ["UU launch.txt"]
    assert list((game_home / "tmp").iterdir()) == []


def test_a_hang_up_ends_the_tool_and_git_leaves_the_conflict_and_its_copies_for_the_next_reset(game_home: Path) -> None:
    project = lab_in_conflict(game_home)
    before = (project / "launch.txt").read_bytes()
    shell = Shell(project)
    shell.until("Ctrl-C here.")
    os.killpg(shell.pid, signal.SIGHUP)
    shell.status()
    assert (project / "launch.txt").read_bytes() == before
    assert gitcmd.output(project, "status", "--porcelain").splitlines() == ["UU launch.txt"]
    assert [entry.name.startswith("git-mergetool-") for entry in (game_home / "tmp").iterdir()] == [True]
    runner.remove_labs()
    assert list((game_home / "tmp").iterdir()) == []


def test_git_mergetool_with_no_conflict_starts_no_tool(game_home: Path) -> None:
    project = lab_in_conflict(game_home)
    gitcmd.output(project, "merge", "--abort")
    shell = Shell(project)
    assert shell.status() == 0
    assert "No files need merging" in shell.shown
    assert "firstcommit-mergetool" not in shell.shown


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_tools_first_line_tells_which_file_it_waits_for_in_either_language(language: str) -> None:
    first = mergetool.WAITING[language].format(path="docs/launch plan.txt").splitlines()[0]  # type: ignore[index]
    assert mergetool.waiting_for(first) == "docs/launch plan.txt"
    assert mergetool.waiting_for(first + "\n") == "docs/launch plan.txt"
    assert mergetool.waiting_for("Normal merge conflict for 'launch.txt':") is None
