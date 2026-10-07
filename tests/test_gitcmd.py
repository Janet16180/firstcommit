import http.server
import os
import subprocess
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from firstcommit import gitcmd, save

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
        "GIT_CONFIG_GLOBAL": str(tmp_path / save.GITCONFIG_FILE),
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



def players_personal_git_files(home: Path) -> None:
    """
    Give a player's home an ignore file and an attributes file in git's default places.

    Parameters
    ----------
    home : Path
        The player's home folder.
    """
    personal = home / ".config" / "git"
    personal.mkdir(parents=True)
    (personal / "ignore").write_text("*.txt\n")
    (personal / "attributes").write_text("*.txt -text\n")


def test_a_players_personal_ignore_and_attributes_files_never_reach_a_lab(game_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (game_home / "gitconfig").write_text(gitcmd.BASE_CONFIG)
    player_home = tmp_path / "player"
    players_personal_git_files(player_home)
    monkeypatch.setenv("HOME", str(player_home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", str(repo))
    (repo / "notes.txt").write_text("hello\n")
    assert gitcmd.output(repo, "status", "--porcelain", "--ignored") == "?? notes.txt\n"
    assert gitcmd.output(repo, "check-attr", "text", "notes.txt") == "notes.txt: text: unspecified\n"

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


def test_the_games_git_never_opens_the_players_editor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", "-b", "main", str(repo))
    script, marker = program_that_leaves_a_mark(tmp_path)
    monkeypatch.setenv("EDITOR", str(script))
    monkeypatch.setenv("VISUAL", str(script))
    gitcmd.run(repo, "commit", "--allow-empty")
    assert not marker.exists()


class AsksForAPassword(http.server.BaseHTTPRequestHandler):
    """Answer every request as a server that wants a user name and a password."""

    def do_GET(self) -> None:
        """Refuse the request until it carries credentials."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="lab"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Keep the test output quiet."""


@pytest.fixture
def password_server() -> Iterator[str]:
    """
    Serve a repository address on localhost that asks for a password.

    Yields
    ------
    str
        The address.
    """
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), AsksForAPassword)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/project.git"
    server.shutdown()
    thread.join()


def test_the_games_git_never_asks_for_a_password(tmp_path: Path, password_server: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSH_ASKPASS", raising=False)
    result = gitcmd.run(tmp_path, "ls-remote", password_server)
    assert result.returncode != 0
    assert "terminal prompts disabled" in result.stderr


@pytest.mark.parametrize("email_variable", [{}, {"EMAIL": "sam@example.com"}], ids=["no EMAIL", "EMAIL set"])
def test_a_commit_with_a_name_but_no_email_stops_instead_of_guessing_one(game_home: Path, tmp_path: Path, email_variable: dict[str, str]) -> None:
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", str(repo))
    gitcmd.output(repo, "config", "user.name", "Sam Lee")
    shell = gitcmd.shell_environment({"PATH": os.environ["PATH"], "HOME": str(tmp_path), **email_variable}, game_home)
    result = subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "First"], cwd=repo, env=shell, capture_output=True, text=True, check=False)
    assert result.returncode == 128
    assert "fatal: no email was given and auto-detection is disabled" in result.stderr


@pytest.mark.parametrize(
    ("printed", "shown"),
    [
        ("counting 1\rcounting 2\rdone\n", "doneting 2\n"),
        ("counting 3\r          \rdone\n", "done\n"),
        ("a  \r\nkept  \n", "a\nkept  \n"),
        ("Rebasing (1/1)\r" + " " * 79 + "\rSuccessfully rebased.\n", "Successfully rebased.\n"),
    ],
)
def test_carriage_returns_leave_what_a_terminal_shows(printed: str, shown: str) -> None:
    assert gitcmd.as_on_terminal(printed) == shown


@given(st.text(alphabet=st.characters(blacklist_characters="\r")))
def test_output_without_carriage_returns_is_shown_as_printed(printed: str) -> None:
    assert gitcmd.as_on_terminal(printed) == printed


@given(st.text())
def test_what_a_terminal_shows_has_no_carriage_return_and_as_many_lines(printed: str) -> None:
    shown = gitcmd.as_on_terminal(printed)
    assert "\r" not in shown
    assert shown.count("\n") == printed.count("\n")


def clone_behind_with_a_change_in_the_way(folder: Path) -> Path:
    """
    Make a clone that is one commit behind its remote and has changed, without committing, the file that commit changes.

    Parameters
    ----------
    folder : Path
        An empty folder; the game's git configuration must exist.

    Returns
    -------
    Path
        The clone, where ``git pull`` has to refuse the fast-forward.
    """
    github, alex, mine = folder / "github.git", folder / "alex", folder / "mine"
    gitcmd.output(folder, "init", "-q", "--bare", str(github))
    gitcmd.output(folder, "clone", "-q", str(github), str(alex))
    (alex / "notes.txt").write_text("one\n")
    gitcmd.output(alex, "add", "notes.txt")
    gitcmd.output(alex, "commit", "-q", "-m", "Add notes")
    gitcmd.output(alex, "push", "-q", "origin", "main")
    gitcmd.output(folder, "clone", "-q", str(github), str(mine))
    (alex / "notes.txt").write_text("two\n")
    gitcmd.output(alex, "commit", "-q", "-am", "Change notes")
    gitcmd.output(alex, "push", "-q", "origin", "main")
    (mine / "notes.txt").write_text("mine\n")
    return mine


def test_a_command_on_a_terminal_shows_its_lines_in_the_order_a_terminal_does(game_home: Path, tmp_path: Path) -> None:
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    mine = clone_behind_with_a_change_in_the_way(tmp_path)
    shell = {**gitcmd.shell_environment(os.environ, game_home), "LC_ALL": "C"}
    piped = subprocess.run(["git", "pull"], cwd=mine, env=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False).stdout
    assert piped.index("Aborting") < piped.index("Updating")
    status, shown = gitcmd.run_on_terminal(mine, "pull")
    assert status != 0
    assert shown.index("Updating") < shown.index("error: Your local changes") < shown.index("Aborting")


def diverged(folder: Path) -> Path:
    """
    Make a repository whose branch ``topic`` and ``main`` each have a commit the other lacks, with Alex as its configured identity.

    Parameters
    ----------
    folder : Path
        Where to make it.

    Returns
    -------
    Path
        The repository, on ``topic``.
    """
    repo = folder / "repo"
    gitcmd.output(folder, "init", "-q", "-b", "main", str(repo))
    gitcmd.output(repo, "config", "user.name", ALEX.name)
    gitcmd.output(repo, "config", "user.email", ALEX.email)
    gitcmd.output(repo, "commit", "-q", "--allow-empty", "-m", "one")
    gitcmd.output(repo, "switch", "-q", "-c", "topic")
    gitcmd.output(repo, "commit", "-q", "--allow-empty", "-m", "two")
    gitcmd.output(repo, "switch", "-q", "main")
    gitcmd.output(repo, "commit", "-q", "--allow-empty", "-m", "three")
    gitcmd.output(repo, "switch", "-q", "topic")
    return repo


def test_a_command_on_a_terminal_shows_what_stays_on_the_screen_without_escapes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TERM", "xterm-256color")
    repo = diverged(tmp_path)
    assert gitcmd.run_on_terminal(repo, "rebase", "main") == (0, "Successfully rebased and updated refs/heads/topic.\n")


def test_a_command_on_a_terminal_never_prints_colours(game_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TERM", "xterm-256color")
    save.ensure_gitconfig(gitcmd.BASE_CONFIG + "[color]\n\tui = always\n")
    repo = diverged(tmp_path)
    status, shown = gitcmd.run_on_terminal(repo, "log", "--oneline", "--decorate", "-1")
    assert (status, shown) == (0, f"{gitcmd.output(repo, 'rev-parse', '--short', 'HEAD').strip()} (HEAD -> topic) two\n")


def test_a_command_on_a_terminal_never_opens_a_pager_or_an_editor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = diverged(tmp_path)
    script, marker = program_that_leaves_a_mark(tmp_path)
    gitcmd.output(repo, "config", "core.pager", str(script))
    gitcmd.output(repo, "config", "core.editor", str(script))
    monkeypatch.setenv("EDITOR", str(script))
    monkeypatch.setenv("VISUAL", str(script))
    monkeypatch.setenv("PAGER", str(script))
    assert gitcmd.run_on_terminal(repo, "log", "--oneline")[0] == 0
    status, shown = gitcmd.run_on_terminal(repo, "commit", "--allow-empty")
    assert (status, shown) == (1, "Aborting commit due to empty commit message.\n")
    assert not marker.exists()


def test_a_command_on_a_terminal_never_waits_for_a_password(tmp_path: Path, password_server: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSH_ASKPASS", raising=False)
    status, shown = gitcmd.run_on_terminal(tmp_path, "ls-remote", password_server)
    assert status != 0
    assert "terminal prompts disabled" in shown


def test_a_command_on_a_terminal_reads_no_answer_to_its_own_questions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitcmd, "TIMEOUT", 5.0)
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", str(repo))
    (repo / "notes.txt").write_text("one\n")
    gitcmd.output(repo, "add", "notes.txt")
    (repo / "notes.txt").write_text("two\n")
    status, shown = gitcmd.run_on_terminal(repo, "add", "-p")
    assert status == 0 and "Stage this hunk" in shown
    assert gitcmd.output(repo, "diff", "--name-only") == "notes.txt\n"



def test_a_command_on_a_terminal_never_runs_the_repositorys_hooks(tmp_path: Path) -> None:
    repo = diverged(tmp_path)
    script, marker = program_that_leaves_a_mark(tmp_path)
    (repo / ".git" / "hooks" / "pre-commit").write_text(script.read_text())
    (repo / ".git" / "hooks" / "pre-commit").chmod(0o755)
    assert gitcmd.run_on_terminal(repo, "commit", "-q", "--allow-empty", "-m", "x") == (0, "")
    assert not marker.exists()

def test_a_command_on_a_terminal_commits_as_the_configured_identity_whatever_the_environment_says(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ["GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"]:
        monkeypatch.setenv(variable, "Intruder")
    for variable in ["GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "EMAIL"]:
        monkeypatch.setenv(variable, "intruder@example.com")
    repo = tmp_path / "repo"
    gitcmd.output(tmp_path, "init", "-q", str(repo))
    gitcmd.output(repo, "config", "user.name", "Alex Kim")
    gitcmd.output(repo, "config", "user.email", "alex@example.com")
    assert gitcmd.run_on_terminal(repo, "commit", "-q", "--allow-empty", "-m", "First") == (0, "")
    assert gitcmd.output(repo, "log", "-1", "--format=%an <%ae>, %cn <%ce>") == "Alex Kim <alex@example.com>, Alex Kim <alex@example.com>\n"


def test_a_command_on_a_terminal_is_kept_to_the_games_configuration_and_labs(game_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gitcmd.output(game_home, "init", "-q")
    monkeypatch.setenv("GIT_DIR", str(game_home / ".git"))
    lab = game_home / "labs" / "some-level"
    lab.mkdir(parents=True)
    status, shown = gitcmd.run_on_terminal(lab, "rev-parse", "--git-dir")
    assert status == 128 and "not a git repository" in shown


def test_a_command_on_a_terminal_in_a_missing_folder_gives_gits_own_failure(tmp_path: Path) -> None:
    status, shown = gitcmd.run_on_terminal(tmp_path / "gone", "status")
    assert status == 128 and "cannot change to" in shown



def test_a_command_on_a_terminal_runs_in_the_c_locale_so_its_words_can_be_read_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    assert gitcmd.run_on_terminal(tmp_path, "-c", "alias.locale=!printf %s \"$LC_ALL\"", "locale") == (0, "C")


def test_a_command_on_a_terminal_keeps_each_line_as_printed(tmp_path: Path) -> None:
    assert gitcmd.run_on_terminal(tmp_path, "-c", "alias.say=!printf 'kept  \\n'", "say") == (0, "kept  \n")

def ended(pid: int) -> bool:
    """
    Tell whether a process has ended: it is gone, or a zombie waiting to be reaped.

    Parameters
    ----------
    pid : int
        The process id.

    Returns
    -------
    bool
        True once the process runs no more.
    """
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except FileNotFoundError:
        state = "Z"
    return state == "Z"


@pytest.mark.slow
def test_a_command_on_a_terminal_that_runs_too_long_is_stopped_with_everything_it_started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitcmd, "TIMEOUT", 1.0)
    pid_file = tmp_path / "sleeper.pid"
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        gitcmd.run_on_terminal(tmp_path, "-c", f"alias.wait=!echo $$ > {pid_file}; exec sleep 60", "wait")
    assert time.monotonic() - started < 10
    pid = int(pid_file.read_text())
    deadline = time.monotonic() + 5
    while not ended(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert ended(pid)


def players_line(folder: Path, line: str, editor: str) -> int:
    """
    Run a line in the player's shell environment, with an editor of the player's own set.

    Parameters
    ----------
    folder : Path
        Where to run it.
    line : str
        The command line.
    editor : str
        The player's ``EDITOR`` and ``VISUAL``.

    Returns
    -------
    int
        The line's exit status.
    """
    env = {**gitcmd.shell_environment(os.environ, save.home()), "HOME": str(save.home()), "EDITOR": editor, "VISUAL": editor}
    return subprocess.run(["bash", "--norc", "-c", line], cwd=folder, env=env, capture_output=True, stdin=subprocess.DEVNULL, timeout=30, check=False).returncode


def test_in_the_players_shell_a_bare_commit_stops_instead_of_opening_any_editor(game_home: Path) -> None:
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    project = game_home / "labs" / "editor" / "project"
    project.mkdir(parents=True)
    trap = game_home / "editor-ran"
    setup = 'git init -q && git config user.name Robin && git config user.email robin@example.com && echo a > map.txt && git add map.txt'
    assert players_line(project, setup, f"touch {trap};false") == 0
    assert players_line(project, "git commit", f"touch {trap};false") == 1
    assert not trap.exists()
    assert gitcmd.run(project, "rev-parse", "-q", "--verify", "HEAD").returncode != 0


def test_in_the_players_shell_merge_revert_and_commit_no_edit_keep_gits_message(game_home: Path) -> None:
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    project = game_home / "labs" / "editor" / "project"
    project.mkdir(parents=True)
    lines = [
        "git init -q && git config user.name Robin && git config user.email robin@example.com",
        "echo a > map.txt && git add map.txt && git commit -q -m 'Add the map'",
        "git switch -q -c other && echo b > b.txt && git add b.txt && git commit -q -m 'Add b' && git switch -q main",
        "echo c > c.txt && git add c.txt && git commit -q -m 'Add c'",
        "git merge -q other",
        "git revert HEAD~1",
        "git switch -q -c side HEAD~1 && echo x > map.txt && git commit -q -am Side && git switch -q main",
        "echo y > map.txt && git commit -q -am Main",
    ]
    assert [players_line(project, line, "false") for line in lines] == [0] * len(lines)
    assert players_line(project, "git merge side", "false") == 1
    assert players_line(project, "echo z > map.txt && git add map.txt && git commit --no-edit", "false") == 0
    subjects = gitcmd.output(project, "log", "--format=%s").splitlines()
    assert subjects[0] == "Merge branch 'side'"
    assert {"Merge branch 'other'", 'Revert "Add c"'} <= set(subjects)
