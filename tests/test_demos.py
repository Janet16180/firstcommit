import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from termlab import snippets

from firstcommit import demos, gitcmd, kit, save

HELLO = "ce013625030ba8dba906f756967f9e9ca394464a"


def lesson(*runs: str) -> list[kit.Slide]:
    """
    Build a lesson whose slides run the given lines.

    Parameters
    ----------
    *runs : str
        Each slide's ``run`` lines.

    Returns
    -------
    list[kit.Slide]
        Slides named ``s0``, ``s1``...
    """
    return [kit.Slide(id=f"s{index}", title=f"Slide {index}", text="Text.", run=run) for index, run in enumerate(runs)]


def run_in(tmp_path: Path, code: str) -> subprocess.CompletedProcess[str]:
    """
    Run bash code in an empty folder with the lesson environment, as the card tests do.

    Parameters
    ----------
    tmp_path : Path
        The test's folder.
    code : str
        Bash code.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Its result.
    """
    env = demos.environment(tmp_path / "home")
    work = tmp_path / "work"
    work.mkdir()
    return snippets.run(code, work, env)


def test_the_environment_is_complete_and_inherits_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "elsewhere"))
    env = demos.environment(tmp_path / "home")
    assert env == {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(tmp_path / "home"),
        "LC_ALL": "C",
        "TERM": "dumb",
        "TZ": "UTC",
        "GIT_CONFIG_GLOBAL": str(tmp_path / "home" / ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": str(tmp_path),
        "GIT_MERGE_AUTOEDIT": "yes",
        "GIT_AUTHOR_NAME": demos.AUTHOR.name,
        "GIT_AUTHOR_EMAIL": demos.AUTHOR.email,
        "GIT_AUTHOR_DATE": demos.DATE,
        "GIT_COMMITTER_NAME": demos.AUTHOR.name,
        "GIT_COMMITTER_EMAIL": demos.AUTHOR.email,
        "GIT_COMMITTER_DATE": demos.DATE,
    }
    assert (tmp_path / "home" / ".gitconfig").read_text() == gitcmd.BASE_CONFIG + "[log]\n\tdecorate = short\n"
    assert demos.AUTHOR.email.endswith("@example.com")


def test_the_environment_gives_git_a_fixed_identity_date_and_default_branch(tmp_path: Path) -> None:
    result = run_in(tmp_path, "git var GIT_AUTHOR_IDENT && git var GIT_COMMITTER_IDENT && git config --global init.defaultBranch")
    assert result.stdout == f"{demos.AUTHOR.name} <{demos.AUTHOR.email}> 1768467600 +0000\n" * 2 + "main\n"


def test_the_environment_never_finds_a_repository_above_its_folder(tmp_path: Path) -> None:
    gitcmd.output(tmp_path, "init", "-q")
    inside = tmp_path / "lesson"
    inside.mkdir()
    result = run_in(inside, "git rev-parse --git-dir")
    assert result.returncode != 0


def test_the_environment_refuses_a_home_that_already_exists(tmp_path: Path) -> None:
    with pytest.raises(FileExistsError):
        demos.environment(tmp_path)


def test_the_blob_of_hello_is_shown_as_git_prints_it() -> None:
    [frame] = demos.frames(lesson("printf 'hello\\n' > hello.txt\ngit hash-object hello.txt"))
    assert frame["transcript"] == [
        {"command": "printf 'hello\\n' > hello.txt", "output": ""},
        {"command": "git hash-object hello.txt", "output": HELLO + "\n"},
    ]


def test_each_slide_shows_only_its_own_commands() -> None:
    first, second = demos.frames(lesson("echo one", "echo two\necho three"))
    assert first["transcript"] == [{"command": "echo one", "output": "one\n"}]
    assert second["transcript"] == [{"command": "echo two", "output": "two\n"}, {"command": "echo three", "output": "three\n"}]


def test_output_and_errors_are_shown_together_in_order() -> None:
    [frame] = demos.frames(lesson("echo out; echo err >&2; echo out again"))
    assert frame["transcript"][0]["output"] == "out\nerr\nout again\n"


def test_blank_lines_and_surrounding_spaces_are_dropped() -> None:
    [frame] = demos.frames(lesson("\n    echo one\n\n    echo two   \n"))
    assert [line["command"] for line in frame["transcript"]] == ["echo one", "echo two"]


def test_the_shell_keeps_its_folder_variables_and_status_between_lines_and_slides() -> None:
    first, second = demos.frames(lesson("mkdir demo\ncd demo\nname=hello", "echo $name\npwd\n! false\necho $?"))
    assert [line["output"] for line in second["transcript"]] == ["hello\n", "/home/you/project/demo\n", "", "1\n"]


def test_new_files_get_the_same_permissions_whatever_the_games_umask() -> None:
    previous = os.umask(0o077)
    try:
        [frame] = demos.frames(lesson("umask"))
    finally:
        os.umask(previous)
    assert frame["transcript"][0]["output"] == "0022\n"


def test_the_lesson_runs_in_a_project_folder_inside_home_shown_as_home_you() -> None:
    [frame] = demos.frames(lesson("pwd\necho $HOME\ngit init"))
    outputs = [line["output"] for line in frame["transcript"]]
    assert outputs == ["/home/you/project\n", "/home/you\n", "Initialized empty Git repository in /home/you/project/.git/\n"]


def test_each_frame_maps_the_repository_after_its_own_slide() -> None:
    empty, created, committed = demos.frames(lesson("", "git init -q", "echo hi > a.txt\ngit add a.txt\ngit commit -q -m 'Add a'"))
    assert not empty["map"]["exists"]
    assert created["map"]["exists"]
    assert created["map"]["commits"] == []
    assert [commit["subject"] for commit in committed["map"]["commits"]] == ["Add a"]
    assert committed["map"]["commits"][0]["author"] == demos.AUTHOR.name


def test_the_map_follows_the_shells_current_folder() -> None:
    inside, outside = demos.frames(lesson("git init -q demo\ncd demo", "cd .."))
    assert inside["map"]["exists"]
    assert not outside["map"]["exists"]


def test_from_a_subfolder_the_map_shows_the_repository_the_shell_is_in() -> None:
    top, below = demos.frames(lesson("git init -q\ngit commit -q --allow-empty -m one", "mkdir docs\ncd docs"))
    assert below["map"] == top["map"]
    assert below["objects"] == top["objects"]


def test_the_log_shows_where_head_and_branches_are_as_on_a_terminal() -> None:
    [frame] = demos.frames(lesson("git init -q\ngit commit -q --allow-empty -m First\ngit log --oneline"))
    short = frame["map"]["commits"][0]["short"]
    assert frame["transcript"][-1]["output"] == f"{short} (HEAD -> main) First\n"


def test_a_merge_that_opens_an_editor_on_a_terminal_must_say_how_to_skip_it() -> None:
    setup = "git init -q\ngit commit -q --allow-empty -m one\ngit switch -q -c topic\ngit commit -q --allow-empty -m two\ngit switch -q main\ngit commit -q --allow-empty -m three"
    with pytest.raises(RuntimeError, match="git merge topic"):
        demos.frames(lesson(setup, "git merge topic"))
    _, merged = demos.frames(lesson(setup, "git merge --no-edit topic"))
    assert merged["map"]["commits"][0]["subject"] == "Merge branch 'topic'"


def test_carriage_returns_show_what_stays_on_a_terminal() -> None:
    [frame] = demos.frames(lesson("printf 'counting 1\\rcounting 2\\rdone\\n'\nprintf 'counting 3\\r          \\rdone\\n'\nprintf 'a  \\r\\nkept  \\n'"))
    assert [line["output"] for line in frame["transcript"]] == ["doneting 2\n", "done\n", "a\nkept  \n"]


def test_a_rebase_shows_its_last_line_only_as_on_a_terminal() -> None:
    runs = "git init -q\ngit commit -q --allow-empty -m one\ngit switch -q -c topic\ngit commit -q --allow-empty -m two\ngit switch -q main\ngit commit -q --allow-empty -m three\ngit switch -q topic\ngit rebase main"
    [frame] = demos.frames(lesson(runs))
    assert frame["transcript"][-1]["output"] == "Successfully rebased and updated refs/heads/topic.\n"


def test_objects_list_the_repository_of_the_frame() -> None:
    before, after = demos.frames(lesson("git init -q\nprintf 'hello\\n' > hello.txt", "git add hello.txt"))
    assert before["objects"] == []
    assert after["objects"] == [{"hash": HELLO, "type": "blob", "size": 6}]


def test_a_line_that_fails_unexpectedly_names_the_slide_and_the_command() -> None:
    with pytest.raises(RuntimeError, match=r"s1.*git commit -m nothing"):
        demos.frames(lesson("git init -q", "git commit -m nothing"))


def test_a_line_marked_to_fail_may_fail_and_shows_its_output() -> None:
    [frame] = demos.frames(lesson("git init -q\n! git commit -q -m nothing"))
    line = frame["transcript"][1]
    assert line["command"] == "git commit -q -m nothing"
    assert line["output"] != ""


def test_a_line_marked_to_fail_that_succeeds_is_a_bug() -> None:
    with pytest.raises(RuntimeError, match=r"s0.*echo fine"):
        demos.frames(lesson("! echo fine"))


def test_a_line_that_ends_the_shell_is_a_bug() -> None:
    with pytest.raises(RuntimeError, match=r"s0.*exit 0"):
        demos.frames(lesson("echo before\nexit 0\necho after"))


def test_a_command_split_over_lines_is_a_bug() -> None:
    with pytest.raises(RuntimeError, match=r"s0.*if true; then"):
        demos.frames(lesson("if true; then\necho yes\nfi"))


def test_a_slide_that_leaves_the_lesson_folder_is_a_bug() -> None:
    with pytest.raises(RuntimeError, match=r"s0.*outside"):
        demos.frames(lesson("cd /"))


def test_the_lesson_folder_is_removed_afterwards(game_home: Path) -> None:
    demos.frames(lesson("git init -q\necho cleaned up > a.txt"))
    with pytest.raises(RuntimeError):
        demos.frames(lesson("echo cleaned up after a failure\nfalse"))
    leftovers = list(game_home.rglob("*"))
    assert leftovers == [game_home / "lessons"]


def test_a_game_home_inside_a_repository_never_shows_that_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gitcmd.output(tmp_path, "init", "-q")
    home = tmp_path / "home"
    monkeypatch.setenv("FIRSTCOMMIT_HOME", str(home))
    outside, inside = demos.frames(lesson("echo no repository here yet", "git init -q demo\ncd demo"))
    assert not outside["map"]["exists"]
    assert outside["objects"] == []
    assert inside["map"]["exists"]
    assert sorted(path.name for path in tmp_path.iterdir()) == [".git", "home"]
    assert list(home.rglob("*")) == [home / save.LESSONS_FOLDER]


def test_a_lessons_folder_that_is_a_link_elsewhere_is_refused_before_anything_runs(game_home: Path, tmp_path: Path) -> None:
    victim = tmp_path / "victim"
    victim.mkdir()
    (game_home / save.LESSONS_FOLDER).symlink_to(victim)
    with pytest.raises(ValueError, match="must be a folder inside the game home"):
        demos.frames(lesson("echo never run elsewhere"))
    assert list(victim.iterdir()) == []


def test_a_lessons_folder_that_is_a_link_inside_the_home_is_refused_too(game_home: Path) -> None:
    (game_home / "elsewhere").mkdir()
    (game_home / save.LESSONS_FOLDER).symlink_to(game_home / "elsewhere")
    with pytest.raises(ValueError, match="must be a folder inside the game home"):
        demos.frames(lesson("echo never run through a link"))
    assert list((game_home / "elsewhere").iterdir()) == []


def test_asking_twice_for_a_lesson_runs_it_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    real_run: Callable[..., subprocess.CompletedProcess[str]] = snippets.run

    def counting_run(code: str, cwd: Path, env: dict[str, str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
        calls.append(code)
        return real_run(code, cwd, env, timeout)

    monkeypatch.setattr(snippets, "run", counting_run)
    slides = lesson("echo cached once")
    first = demos.frames(slides)
    first[0]["transcript"].clear()
    second = demos.frames(list(slides))
    assert len(calls) == 1
    assert second[0]["transcript"] == [{"command": "echo cached once", "output": "cached once\n"}]


FRESH_PROCESS = """
import json, sys
from firstcommit import demos, kit
runs = json.load(sys.stdin)
print(json.dumps(demos.frames([kit.Slide(id=f"s{n}", title="t", text="t", run=run) for n, run in enumerate(runs)])))
"""


@pytest.mark.slow
def test_a_lesson_gives_the_same_frames_every_time(game_home: Path) -> None:
    runs = ["git init", "printf 'hello\\n' > hello.txt\ngit add hello.txt\ngit commit -m 'Say hello'", "git switch -c topic\ngit log --oneline --all"]
    here = demos.frames(lesson(*runs))
    elsewhere = subprocess.run([sys.executable, "-c", FRESH_PROCESS], input=json.dumps(runs), capture_output=True, text=True, check=True)
    assert json.loads(elsewhere.stdout) == here
