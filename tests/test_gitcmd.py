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
        "GIT_CEILING_DIRECTORIES": str(tmp_path / "labs"),
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
