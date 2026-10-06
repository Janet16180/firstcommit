import os
import subprocess
import time
from pathlib import Path

import pytest

from firstcommit import gitcmd

ALEX = gitcmd.Person("Alex Kim", "alex@example.com")
WHEN = "2026-01-15T09:00:00+00:00"


def test_game_git_ignores_the_players_global_config(game_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    player_home = tmp_path / "player"
    player_home.mkdir()
    (player_home / ".gitconfig").write_text("[alias]\n\tsecret = status\n[user]\n\tname = Player\n")
    monkeypatch.setenv("HOME", str(player_home))
    result = gitcmd.run(tmp_path, "config", "--get", "user.name")
    assert result.returncode == 1
    assert result.stdout == ""


def test_game_git_reads_the_games_own_global_config(game_home: Path, tmp_path: Path) -> None:
    (game_home / "gitconfig").write_text("[user]\n\tname = In The Game\n")
    assert gitcmd.output(tmp_path, "config", "--get", "user.name") == "In The Game\n"


def test_game_git_never_finds_a_repository_above_the_labs(game_home: Path) -> None:
    gitcmd.output(game_home, "init", "-q")
    lab = game_home / "labs" / "some-level"
    lab.mkdir(parents=True)
    result = gitcmd.run(lab, "rev-parse", "--git-dir")
    assert result.returncode != 0


def test_inherited_git_variables_cannot_redirect_a_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    elsewhere = tmp_path / "elsewhere"
    gitcmd.output(tmp_path, "init", "-q", str(elsewhere))
    monkeypatch.setenv("GIT_DIR", str(elsewhere / ".git"))
    project = tmp_path / "project"
    project.mkdir()
    assert gitcmd.run(project, "rev-parse", "--git-dir").returncode != 0


def test_commits_with_a_fixed_author_and_date_have_a_stable_hash(tmp_path: Path) -> None:
    hashes = []
    for name in ("one", "two"):
        repo = tmp_path / name
        gitcmd.output(tmp_path, "init", "-q", "-b", "main", str(repo))
        (repo / "hello.txt").write_text("hello\n")
        gitcmd.output(repo, "add", "hello.txt")
        gitcmd.output(repo, "commit", "-q", "-m", "Say hello", author=ALEX, when=WHEN)
        hashes.append(gitcmd.output(repo, "rev-parse", "HEAD"))
    assert hashes[0] == hashes[1]
    assert gitcmd.output(tmp_path / "one", "log", "-1", "--format=%an <%ae> %cn %aI") == "Alex Kim <alex@example.com> Alex Kim 2026-01-15T09:00:00+00:00\n"


def test_output_raises_when_git_fails(tmp_path: Path) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        gitcmd.output(tmp_path, "rev-parse", "HEAD")


def test_run_returns_the_failure_instead_of_raising(tmp_path: Path) -> None:
    result = gitcmd.run(tmp_path, "rev-parse", "HEAD")
    assert result.returncode != 0
    assert "not a git repository" in result.stderr


def test_isolation_names_the_games_config_and_labs(tmp_path: Path) -> None:
    assert gitcmd.isolation(tmp_path) == {
        "GIT_CONFIG_GLOBAL": str(tmp_path / "gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": f"{tmp_path / 'labs'}:{tmp_path / 'lessons'}",
    }


def test_game_git_never_rewrites_the_index_behind_the_players_back(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", "-b", "main", str(repo))
    (repo / "a.txt").write_text("a\n")
    gitcmd.output(repo, "add", "a.txt")
    index = repo / ".git" / "index"
    long_ago = time.time_ns() - 60 * 10**9
    os.utime(index, ns=(long_ago, long_ago))
    (repo / "a.txt").touch()
    gitcmd.output(repo, "status", "--porcelain=v2")
    assert index.stat().st_mtime_ns == long_ago


def test_the_players_shell_keeps_its_own_settings_but_loses_inherited_git_variables(tmp_path: Path) -> None:
    base = {"PATH": "/usr/bin", "EDITOR": "vim", "GIT_DIR": "/elsewhere/.git", "GIT_INDEX_FILE": "/x"}
    env = gitcmd.shell_environment(base, tmp_path)
    assert env == {"PATH": "/usr/bin", "EDITOR": "vim", **gitcmd.isolation(tmp_path)}


def test_game_commands_start_from_the_players_shell_environment(tmp_path: Path) -> None:
    base = {"PATH": "/usr/bin", "GIT_WORK_TREE": "/x"}
    env = gitcmd.environment(base, tmp_path, gitcmd.GAME, None)
    assert gitcmd.shell_environment(base, tmp_path).items() <= env.items()


def test_a_missing_folder_gives_gits_own_failure_instead_of_crashing(tmp_path: Path) -> None:
    result = gitcmd.run(tmp_path / "deleted-by-the-player", "status", "--porcelain=v2")
    assert result.returncode == 128
    assert "cannot change to" in result.stderr


def test_relative_paths_in_arguments_resolve_in_the_folder_given(tmp_path: Path) -> None:
    gitcmd.output(tmp_path, "init", "-q", "-b", "main", "inner")
    assert (tmp_path / "inner" / ".git").is_dir()


def test_game_git_never_finds_a_repository_above_a_lesson(game_home: Path) -> None:
    gitcmd.output(game_home, "init", "-q")
    lesson = game_home / "lessons" / "some-lesson"
    lesson.mkdir(parents=True)
    assert gitcmd.run(lesson, "rev-parse", "--git-dir").returncode != 0


def test_the_game_pages_like_git_does_when_less_is_unset(game_home: Path, tmp_path: Path) -> None:
    (game_home / "gitconfig").write_text(gitcmd.BASE_CONFIG)
    env = {**gitcmd.shell_environment({"PATH": os.environ["PATH"], "LESS": "-R"}, game_home), "HOME": str(tmp_path)}
    result = subprocess.run(["git", "var", "GIT_PAGER"], env=env, capture_output=True, text=True, check=True)
    assert result.stdout == "less -FRX\n"


def program_that_leaves_a_mark(folder: Path) -> tuple[Path, Path]:
    """
    Write a script that appends a line to a marker file each time it runs.

    Parameters
    ----------
    folder : Path
        Where to write the script; the marker goes next to it.

    Returns
    -------
    tuple[Path, Path]
        The script and its marker file.
    """
    marker = folder / "ran"
    script = folder / "program.sh"
    script.write_text(f"#!/bin/sh\necho ran >> {marker}\nexit 0\n")
    script.chmod(0o755)
    return script, marker


def test_the_games_git_never_runs_a_file_system_monitor_named_by_the_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", "-b", "main", str(repo))
    script, marker = program_that_leaves_a_mark(tmp_path)
    gitcmd.output(repo, "config", "core.fsmonitor", str(script))
    (repo / "a.txt").write_text("a\n")
    gitcmd.output(repo, "status", "--porcelain=v2")
    assert not marker.exists()


def test_the_games_git_never_runs_the_repositorys_hooks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", "-b", "main", str(repo))
    script, marker = program_that_leaves_a_mark(tmp_path)
    (repo / ".git" / "hooks" / "pre-commit").write_text(script.read_text())
    (repo / ".git" / "hooks" / "pre-commit").chmod(0o755)
    gitcmd.output(repo, "commit", "-q", "--allow-empty", "-m", "x")
    assert not marker.exists()


def test_the_games_git_never_runs_a_signature_program_to_show_a_log(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", "-b", "main", str(repo))
    gitcmd.output(repo, "commit", "-q", "--allow-empty", "-m", "x")
    tree = gitcmd.output(repo, "rev-parse", "HEAD^{tree}").strip()
    signed = (
        f"tree {tree}\nauthor A <a@example.com> 0 +0000\ncommitter A <a@example.com> 0 +0000\n"
        "gpgsig -----BEGIN PGP SIGNATURE-----\n \n -----END PGP SIGNATURE-----\n\nsigned\n"
    )
    commit = gitcmd.output(repo, "hash-object", "-t", "commit", "-w", "--stdin", stdin=signed).strip()
    gitcmd.output(repo, "update-ref", "refs/heads/main", commit)
    script, marker = program_that_leaves_a_mark(tmp_path)
    gitcmd.output(repo, "config", "log.showSignature", "true")
    gitcmd.output(repo, "config", "gpg.program", str(script))
    gitcmd.run(repo, "log", "-1")
    assert not marker.exists()


def test_the_players_shell_keeps_the_repositorys_own_settings(tmp_path: Path) -> None:
    assert "GIT_CONFIG_COUNT" not in gitcmd.shell_environment({"PATH": "/usr/bin"}, tmp_path)
