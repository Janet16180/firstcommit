import os
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import pytest

import firstcommit.web
from firstcommit import cli, game, gitcmd, markup, runner, save


@pytest.fixture
def served(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """
    Stand in for the web routes module, recording the ports it is asked to serve on.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest's patcher.

    Returns
    -------
    list[int]
        The ports `serve` was called with.
    """
    ports: list[int] = []
    routes = types.ModuleType("firstcommit.web.routes")

    def serve(port: int) -> int:
        ports.append(port)
        return 7

    routes.serve = serve  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "firstcommit.web.routes", routes)
    monkeypatch.setattr(firstcommit.web, "routes", routes, raising=False)
    return ports


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str]:
    """
    Run the command line and capture what it prints.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Pytest's output capture.
    *argv : str
        Arguments after the program name.

    Returns
    -------
    tuple[int, str]
        The exit status, and standard output and error together.
    """
    status = cli.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out + captured.err


def test_no_command_serves_the_page_on_the_default_port(served: list[int]) -> None:
    assert cli.main([]) == 7
    assert served == [8820]


def test_serve_takes_a_port(served: list[int]) -> None:
    assert cli.main(["serve", "--port", "8851"]) == 7
    assert served == [8851]


@pytest.mark.parametrize("port", ["0", "65536", "-1", "http", ""])
def test_serve_refuses_a_port_out_of_range(served: list[int], port: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        cli.main(["serve", "--port", port])
    assert raised.value.code == 2
    assert "port" in capsys.readouterr().err
    assert served == []


def test_a_relative_game_home_stops_any_command_before_it_starts(served: list[int], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", "relative/home")
    for argv in (["serve"], ["status"], ["shell"]):
        status, printed = run(capsys, *argv)
        assert (status, "FIRSTCOMMIT_HOME" in printed) == (2, True)
    assert served == []


def test_the_shell_starts_in_the_lab_with_the_games_git_settings(sample_level: runner.Level, game_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(args: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, **options})
        return subprocess.CompletedProcess(args, 3)

    game.start(sample_level.id)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("SHELL", "/bin/sh")
    monkeypatch.setenv("TMUX", "/tmp/tmux-1/default")
    monkeypatch.setenv("GIT_DIR", "/somewhere/else/.git")
    monkeypatch.setenv("EDITOR", "nano")
    status, printed = run(capsys, "shell")
    lab = str(game_home / "labs" / "basics-sample" / "project")
    (call,) = calls
    assert (status, call["args"], call["cwd"]) == (3, ["/bin/sh"], lab)
    assert {key: call["env"][key] for key in gitcmd.isolation(game_home)} == gitcmd.isolation(game_home)
    assert (call["env"]["PWD"], call["env"]["EDITOR"], "TMUX" in call["env"], "GIT_DIR" in call["env"]) == (lab, "nano", False, False)
    assert "exit" in printed


def test_the_shell_is_bash_when_no_shell_is_set(sample_level: runner.Level, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.delenv("SHELL", raising=False)
    run(capsys, "shell")
    assert calls == [["/bin/bash"]]


def test_status_shows_xp_rank_the_level_in_progress_and_cards_due(sample_level: runner.Level, sample_decks: Path, capsys: pytest.CaptureFixture[str]) -> None:
    game.start(sample_level.id)
    status, printed = run(capsys, "status")
    assert status == 0
    for expected in ("0 XP", "Untracked", "next: Staged at 150 XP", "Say hello", "step 1 of 3", "hints 0 of 3", "Cards to review: 0"):
        assert expected in printed


def test_check_without_a_level_says_so(sample_level: runner.Level, capsys: pytest.CaptureFixture[str]) -> None:
    status, printed = run(capsys, "check")
    assert (status, "No level is in progress" in printed) == (1, True)


def test_an_unsolved_check_explains_and_counts_an_attempt(sample_level: runner.Level, capsys: pytest.CaptureFixture[str]) -> None:
    game.start(sample_level.id)
    status, printed = run(capsys, "check", "some answer")
    assert (status, "`hello.txt` is not in a commit yet." in printed) == (1, True)
    active = save.load_active()
    assert active is not None and active["attempts"] == 1


def test_a_solved_check_shows_the_payout_and_the_debrief(sample_level: runner.Level, capsys: pytest.CaptureFixture[str]) -> None:
    game.start(sample_level.id)
    active = save.load_active()
    assert active is not None
    sample_level.solve(runner.lab_of(sample_level.id), active["state"])
    status, printed = run(capsys, "check")
    assert status == 0
    for expected in ("Solved", "+100 XP", "`hello.txt` is now in a commit on `trunk`."):
        assert expected in printed


def test_a_hint_shows_its_text_and_its_cost(sample_level: runner.Level, capsys: pytest.CaptureFixture[str]) -> None:
    game.start(sample_level.id)
    status, printed = run(capsys, "hint")
    assert status == 0
    assert "Hint 1 of 3" in printed and "15 XP" in printed and sample_level.hints[0] in printed


def test_reset_needs_yes(sample_level: runner.Level, capsys: pytest.CaptureFixture[str]) -> None:
    save.write_progress({**save.new_progress(), "xp": 40})
    status, printed = run(capsys, "reset")
    assert (status, "--yes" in printed, save.load_progress()["xp"]) == (1, True, 40)
    status, printed = run(capsys, "reset", "--yes")
    assert (status, save.load_progress()["xp"]) == (0, 0)


def test_a_damaged_save_is_named_with_the_way_out(sample_level: runner.Level, game_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (game_home / "progress.json").write_text('{"xp": "lots"}')
    status, printed = run(capsys, "status")
    assert status == 1
    assert "progress.json" in printed and "reset --yes" in printed


def test_the_doctor_prints_one_line_per_check(capsys: pytest.CaptureFixture[str]) -> None:
    status, printed = run(capsys, "doctor")
    lines = printed.strip().splitlines()
    assert status == 0
    assert [line.split()[:2] for line in lines] == [["ok", "git"], ["ok", "python"], ["ok", "home"]]


def test_the_doctor_fails_when_a_check_fails(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("FIRSTCOMMIT_HOME", "relative")
    status, printed = run(capsys, "doctor")
    assert status == 1
    assert printed.strip().splitlines()[-1].startswith("FAIL home")


def test_text_is_rendered_as_wrapped_paragraphs_code_and_bullets() -> None:
    text = "A " + "word " * 30 + "end.\n\n    $ git status\n      indented\n\n- `one`\n- two"
    rendered = cli.render(markup.parse(text))
    assert all(len(line) <= cli.WIDTH for line in rendered.splitlines())
    assert "    $ git status\n      indented" in rendered
    assert "  - `one`\n  - two" in rendered


def test_control_characters_never_reach_the_players_terminal() -> None:
    blocks: list[markup.Block] = [
        {"kind": "para", "spans": [{"text": "esc\x1b]0;PWNED\x07title", "code": True}, {"text": " is untracked\x9b.", "code": False}]},
        {"kind": "code", "text": "line one\x1b[2K\nline two\x7f"},
        {"kind": "bullets", "items": [[{"text": "bell\x07", "code": False}]]},
    ]
    rendered = cli.render(blocks)
    assert not any(ord(char) < 0x20 and char != "\n" or 0x7F <= ord(char) <= 0x9F for char in rendered)
    assert "`esc\\033]0;PWNED\\atitle` is untracked\\302\\233." in rendered
    assert "    line one\\033[2K\n    line two\\177" in rendered
    assert "  - bell\\a" in rendered


def test_the_module_runs_as_a_program(game_home: Path) -> None:
    env = {**os.environ, "FIRSTCOMMIT_HOME": str(game_home)}
    result = subprocess.run([sys.executable, "-m", "firstcommit", "status"], capture_output=True, text=True, env=env, check=False)
    assert (result.returncode, "0 XP" in result.stdout) == (0, True), result.stderr
