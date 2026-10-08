import os
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from termlab.web import terminal

from firstcommit import commands, gitcmd, save

Typist = Callable[..., bytes]


def logging_shell(folder: Path) -> list[str]:
    """
    Write the game's startup file in a folder and give the command of a shell that uses it.

    Parameters
    ----------
    folder : Path
        Where the startup file, the log (``commands.log``) and the history go.

    Returns
    -------
    list[str]
        The game's shell command (`firstcommit.commands.shell`), with the folder as its quiet home.
    """
    startup = folder / "bashrc"
    startup.write_text(commands.startup(folder / "commands.log", folder / "history"))
    (folder / ".hushlogin").touch()
    return commands.shell(startup, folder)


def project(folder: Path) -> Path:
    """
    Make the folder a shell starts in.

    Parameters
    ----------
    folder : Path
        Its parent.

    Returns
    -------
    Path
        ``<folder>/project``, created.
    """
    path = folder / "project"
    path.mkdir()
    return path


def test_each_command_line_typed_is_logged_with_its_exit_status(typist: Typist, tmp_path: Path) -> None:
    typist(
        logging_shell(tmp_path),
        terminal.player_env(os.environ),
        project(tmp_path),
        [
            (b"true\n", b"$ "),
            (b"false\n", b"$ "),
            (b"git --version >/dev/null && false\n", b"$ "),
            (b"sh -c 'echo $((40 + 2)); exec sleep 30'\n", b"42\r\n"),
            (b"\x03", b"$ "),
        ],
    )
    typed, end = commands.since(tmp_path / "commands.log", 0)
    assert typed == [
        {"line": "true", "status": 0},
        {"line": "false", "status": 1},
        {"line": "git --version >/dev/null && false", "status": 1},
        {"line": "sh -c 'echo $((40 + 2)); exec sleep 30'", "status": 130},
    ]
    assert end == (tmp_path / "commands.log").stat().st_size


def test_empty_lines_and_lines_dropped_at_the_prompt_are_not_logged_but_a_repeat_is(typist: Typist, tmp_path: Path) -> None:
    typist(
        logging_shell(tmp_path),
        {**terminal.player_env(os.environ), "HISTCONTROL": "ignoreboth", "HISTIGNORE": "true"},
        project(tmp_path),
        # The half-typed line is dropped with Ctrl-U, not Ctrl-C: on a busy machine bash sometimes
        # leaves a Ctrl-C unhandled until the next key, and the test then waited for a prompt that
        # never came. Either way the line never reaches the history, which is what is tested here.
        [(b"\n", b"$ "), (b"true\n", b"$ "), (b"\n", b"$ "), (b"half typed", b"half typed"), (b"\x15\n", b"$ "), (b"   \n", b"$ "), (b"true\n", b"$ ")],
    )
    assert commands.since(tmp_path / "commands.log", 0)[0] == [{"line": "true", "status": 0}, {"line": "true", "status": 0}]


def test_a_new_shell_does_not_log_the_history_it_reads_back(typist: Typist, tmp_path: Path) -> None:
    shell, env, folder = logging_shell(tmp_path), terminal.player_env(os.environ), project(tmp_path)
    typist(shell, env, folder, [(b"echo one\n", b"$ ")])
    typist(shell, env, folder, [(b"echo two\n", b"$ ")])
    assert commands.since(tmp_path / "commands.log", 0)[0] == [{"line": "echo one", "status": 0}, {"line": "echo two", "status": 0}]
    assert "echo one" in (tmp_path / "history").read_text()


def test_the_prompt_shows_the_folder_and_never_the_user_or_the_machine(typist: Typist, tmp_path: Path) -> None:
    env = {**terminal.player_env(os.environ), "PS1": "user@host:\\w\\$ "}
    shown = typist(logging_shell(tmp_path), env, project(tmp_path), [])
    assert shown.endswith(b"project $ ")
    assert shown.count(b"$ ") == 1 and b"@" not in shown


@pytest.mark.skipif(not commands.COMPLETION.exists(), reason="bash-completion is not installed")
def test_tab_completes_git_commands_where_bash_completion_is_installed(typist: Typist, tmp_path: Path) -> None:
    typist(logging_shell(tmp_path), terminal.player_env(os.environ), project(tmp_path), [(b"git chec\t", b"git checkout "), (b"\x15", b"")])


def test_the_shell_opens_without_the_systems_login_notices_and_on_the_players_own_home(typist: Typist, tmp_path: Path) -> None:
    shown = typist(logging_shell(tmp_path), terminal.player_env(os.environ), project(tmp_path), [(b'echo "home=$HOME player=${FIRSTCOMMIT_PLAYER_HOME-unset}"\n', b"$ ")])
    assert b"sudo" not in shown
    assert b"home=/" in shown and f"home={tmp_path} ".encode() not in shown and b"player=unset" in shown


def test_a_shell_can_have_a_prompt_of_its_own_and_print_one_line_before_it(typist: Typist, tmp_path: Path) -> None:
    startup = tmp_path / "bashrc"
    startup.write_text(commands.startup(tmp_path / "commands.log", tmp_path / "history", prompt=commands.ALEX_PROMPT, banner="Try: it's `git status`"))
    (tmp_path / ".hushlogin").touch()
    shown = typist(commands.shell(startup, tmp_path), terminal.player_env(os.environ), project(tmp_path), [])
    assert shown.startswith(b"Try: it's `git status`\r\n")
    assert shown.endswith(b"\x1b[32malex: project\x1b[0m $ ")


def test_the_startup_file_alone_keeps_the_home_it_is_given(typist: Typist, tmp_path: Path) -> None:
    startup = tmp_path / "bashrc"
    startup.write_text(commands.startup(tmp_path / "commands.log", tmp_path / "history"))
    shown = typist(["bash", "--noprofile", "--rcfile", str(startup), "-i"], terminal.player_env(os.environ), project(tmp_path), [(b'echo "home=$HOME"\n', b"$ ")])
    assert b"home=/" in shown


def test_exit_and_a_shell_started_without_the_startup_file_leave_the_log_whole(typist: Typist, tmp_path: Path) -> None:
    typist(
        logging_shell(tmp_path),
        terminal.player_env(os.environ),
        project(tmp_path),
        [(b"true\n", b"$ "), (b"exec bash --norc --noprofile\n", b"$ "), (b"PS1='$ '\n", b"$ "), (b"false\n", b"$ ")],
    )
    assert commands.since(tmp_path / "commands.log", 0)[0] == [{"line": "true", "status": 0}]


def record(number: int, status: int, line: str) -> bytes:
    """
    Write one record as the startup file's shell writes it.

    Parameters
    ----------
    number : int
        The command's history number.
    status : int
        Its exit status.
    line : str
        The line typed.

    Returns
    -------
    bytes
        The number, the status and the line, separated by tabs, then a NUL byte.
    """
    return f"{number}\t{status}\t{line}\0".encode()


def test_a_record_the_shell_is_still_writing_is_read_next_time(tmp_path: Path) -> None:
    log = tmp_path / "commands.log"
    log.write_bytes(record(1, 0, "git status") + b"2\t1\tgit pu")
    assert commands.since(log, 0) == ([{"line": "git status", "status": 0}], len(record(1, 0, "git status")))
    assert commands.end(log) == len(record(1, 0, "git status"))
    with log.open("ab") as handle:
        handle.write(b"sh\0")
    assert commands.since(log, len(record(1, 0, "git status"))) == ([{"line": "git push", "status": 1}], log.stat().st_size)


def test_a_missing_log_has_no_commands(tmp_path: Path) -> None:
    assert commands.since(tmp_path / "commands.log", 0) == ([], 0)
    assert commands.end(tmp_path / "commands.log") == 0


def test_a_log_shorter_than_the_offset_is_read_from_its_start(tmp_path: Path) -> None:
    log = tmp_path / "commands.log"
    log.write_bytes(record(1, 0, "ls"))
    assert commands.since(log, 1000) == ([{"line": "ls", "status": 0}], len(record(1, 0, "ls")))


def test_a_record_of_another_shape_is_skipped_and_bytes_that_are_not_utf8_are_replaced(tmp_path: Path) -> None:
    log = tmp_path / "commands.log"
    log.write_bytes(b"garbage\0" + b"3\tbad\tls\0" + b"4\t0\tcat caf\xe9.txt\0" + record(5, 2, "a\tb\nc"))
    assert commands.since(log, 0)[0] == [{"line": "cat caf�.txt", "status": 0}, {"line": "a\tb\nc", "status": 2}]


LINES = st.text(alphabet=st.characters(blacklist_characters="\0", blacklist_categories=["Cs"]))


@settings(deadline=None)
@given(st.lists(st.tuples(st.integers(0, 10**6), st.integers(0, 255), LINES)), st.lists(st.integers(0, 10**4)))
def test_records_written_in_any_pieces_read_back_whole_and_in_order(tmp_path_factory: pytest.TempPathFactory, logged: list[tuple[int, int, str]], cuts: list[int]) -> None:
    log = tmp_path_factory.mktemp("log") / "commands.log"
    data = b"".join(record(*entry) for entry in logged)
    pieces = sorted({0, len(data), *(cut % (len(data) + 1) for cut in cuts)})
    typed, offset = [], 0
    for start, stop in zip(pieces, pieces[1:], strict=False):
        with log.open("ab") as handle:
            handle.write(data[start:stop])
        new, offset = commands.since(log, offset)
        typed += new
    assert typed == [{"line": line, "status": status} for _, status, line in logged]
    assert offset == len(data)


def test_a_line_typed_for_a_level_runs_in_bash_and_comes_back_with_its_exit_status(game_home: Path) -> None:
    folder = game_home / "labs" / "some-level" / "project"
    folder.mkdir(parents=True)
    (folder / "map.txt").write_text("Earth, Moon, Mars\n")
    assert commands.type_line(folder, "ls  map.txt") == {"line": "ls  map.txt", "status": 0}
    assert commands.type_line(folder, "ls nothing.txt") == {"line": "ls nothing.txt", "status": 2}
    assert commands.type_line(folder, "git status") == {"line": "git status", "status": 128}
    assert commands.type_line(folder, "gti status") == {"line": "gti status", "status": 127}


def test_a_line_typed_for_a_level_uses_the_games_git_and_never_the_players_home(game_home: Path) -> None:
    folder = game_home / "project"
    folder.mkdir()
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    assert commands.type_line(folder, 'test "$GIT_CONFIG_GLOBAL" = "$HOME/gitconfig" && test "$HOME" = "$FIRSTCOMMIT_HOME"')["status"] == 0
    assert commands.type_line(folder, "git init -q && git symbolic-ref --short HEAD | grep -qx main")["status"] == 0
