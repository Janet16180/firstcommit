"""
The Docker runtime: ``deploy/docker/run`` and the image it builds.

Tests marked ``docker`` build or run containers; they skip when Docker or its daemon is not
available. Every image tag, container and volume they create is named after this pytest run
(`RUN_NAME`) and removed afterwards, and every port they use is one the OS picked, so several runs
can share the machine. One plays the smoke flow of DESIGN.md section 3 (``tests/smoke.py``, also
run on this machine by ``tests/test_smoke.py``) on the player image. The other tests check the
script's messages with a fake ``docker``.
"""

import ast
import json
import os
import pty
import re
import secrets
import shlex
import shutil
import subprocess
import time
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import pytest

from smoke import (
    LINK,
    PROMPT,
    TEMPLATE_LEVEL,
    call,
    free_port,
    open_page_terminal,
    play_the_template_level,
    read_until,
    type_and_expect,
)

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "deploy" / "docker" / "run"
DOCKERFILE = ROOT / "deploy" / "docker" / "Dockerfile"
GAME_HOME = "/home/player/.firstcommit"
INPUTS_LABEL = "firstcommit.inputs"
BUILT_LABEL = "firstcommit.built"
MAX_AGE = timedelta(days=30)
RUN_NAME = f"firstcommit-test-{secrets.token_hex(3)}"


def volume_of(name: str) -> str:
    """
    Give the name of the volume ``deploy/docker/run`` keeps the game home in.

    Parameters
    ----------
    name : str
        The value of ``FIRSTCOMMIT_DOCKER_NAME``.

    Returns
    -------
    str
        The volume's name.
    """
    return f"{name}-home"


def run_script(
    *args: str,
    name: str,
    script: Path = RUN,
    path: str | None = None,
    today: date | None = None,
    stdin: str = "",
    timeout: float = 60,
) -> subprocess.CompletedProcess[str]:
    """
    Run ``deploy/docker/run`` to completion, with its own docker names.

    Parameters
    ----------
    *args : str
        The script's arguments.
    name : str
        The value of ``FIRSTCOMMIT_DOCKER_NAME``.
    script : Path
        The script to run (a copy, for the tests that change sources).
    path : str | None
        ``PATH`` for the script, or None to keep this process's.
    today : date | None
        The day the script takes as today (``FIRSTCOMMIT_DOCKER_TODAY``), or None for the real one.
    stdin : str
        What the script reads.
    timeout : float
        Seconds before the test fails.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The finished script, with its output.
    """
    env = {**os.environ, "FIRSTCOMMIT_DOCKER_NAME": name}
    if path is not None:
        env["PATH"] = path
    if today is not None:
        env["FIRSTCOMMIT_DOCKER_TODAY"] = today.isoformat()
    return subprocess.run(
        [str(script), *args], env=env, input=stdin, capture_output=True, text=True, timeout=timeout, check=False
    )


def docker(*args: str, timeout: float = 60) -> subprocess.CompletedProcess[str]:
    """
    Run a docker command to completion.

    Parameters
    ----------
    *args : str
        The arguments after ``docker``.
    timeout : float
        Seconds before the test fails.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The finished command, with its output; the caller checks the status.
    """
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout, check=False)


def in_image(image: str, script: str, *options: str) -> str:
    """
    Run a shell script in a throwaway container of the image.

    Parameters
    ----------
    image : str
        The image's name.
    script : str
        The ``sh -c`` script.
    *options : str
        More ``docker run`` options, such as ``--env`` or ``--volume``.

    Returns
    -------
    str
        The script's standard output, stripped.
    """
    result = docker("run", "--rm", *options, image, "sh", "-c", script)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def label(image: str, key: str) -> str:
    """
    Give one of the labels ``deploy/docker/run`` puts on the image.

    Parameters
    ----------
    image : str
        The image's name.
    key : str
        The label: ``firstcommit.inputs``, the hash of the sources, or ``firstcommit.built``, the build day.

    Returns
    -------
    str
        The label's value.
    """
    result = docker("image", "inspect", "--format", f'{{{{ index .Config.Labels "{key}" }}}}', image)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def docker_that_records_builds(folder: Path) -> tuple[str, Path]:
    """
    Make a ``docker`` command that writes down each build instead of running it, and runs every other command.

    Parameters
    ----------
    folder : Path
        Where to put it and its record.

    Returns
    -------
    tuple[str, Path]
        A ``PATH`` that finds it first, and the file that receives one line of arguments per build.
    """
    real = shutil.which("docker")
    assert real is not None
    record = folder / "builds"
    command = folder / "docker"
    command.write_text(
        f'#!/bin/sh\nif [ "$1" = build ]; then echo "$*" >> {shlex.quote(str(record))}; exit 0; fi\n'
        f'exec {shlex.quote(real)} "$@"\n'
    )
    command.chmod(0o755)
    return f"{folder}:{os.environ['PATH']}", record


def remove_docker_objects(name: str) -> None:
    """
    Remove the container, volume and image tag a test created under one name.

    Parameters
    ----------
    name : str
        The test's ``FIRSTCOMMIT_DOCKER_NAME``.
    """
    docker("container", "rm", "--force", name)
    docker("volume", "rm", volume_of(name))
    docker("image", "rm", name, f"{name}:test")


def spawn_in_terminal(command: list[str], env: dict[str, str]) -> tuple[subprocess.Popen[bytes], int]:
    """
    Start a command on a new pseudo-terminal, as a player would in their terminal.

    Parameters
    ----------
    command : list[str]
        The command and its arguments.
    env : dict[str, str]
        Its environment.

    Returns
    -------
    tuple[subprocess.Popen[bytes], int]
        The process and the terminal's controlling end, to read its output and type into it.
    """
    leader, follower = pty.openpty()
    process = subprocess.Popen(
        command, stdin=follower, stdout=follower, stderr=follower, env=env, start_new_session=True
    )
    os.close(follower)
    return process, leader


def check_the_page_terminal(port: int, token: str) -> None:
    """
    Check the shell in the page: no privileges, the game's git isolation, and the tools a beginner uses.

    Parameters
    ----------
    port : int
        The server's port.
    token : str
        The key from the printed link.
    """
    page = open_page_terminal(port, token)
    type_and_expect(page, "", PROMPT)
    type_and_expect(
        page,
        "awk '/CapBnd|NoNewPrivs/' /proc/self/status; echo \"uid=$(id -u)\"\r",
        r"CapBnd:\s+0{16}\s+NoNewPrivs:\s+1\s+uid=[1-9]",
    )
    type_and_expect(
        page,
        'echo "config=$GIT_CONFIG_GLOBAL nosystem=$GIT_CONFIG_NOSYSTEM ceiling=$GIT_CEILING_DIRECTORIES"\r',
        rf"config={GAME_HOME}/\S+ nosystem=1 ceiling={GAME_HOME}/[^:\s]+(:{GAME_HOME}/[^:\s]+)*\r",
    )
    type_and_expect(page, "git help commit | head -n 1\r", r"GIT-COMMIT\(1\)")
    type_and_expect(page, "git chec\t", "git checkout")
    identity = "git -c user.name=Player -c user.email=player@example.com"
    bare = type_and_expect(page, f"\x15cd /tmp && git init -q demo && cd demo && {identity} commit --allow-empty; echo status=$?\r", r"(?s)status=1.*\$ $")
    assert "nano" not in bare.lower()
    type_and_expect(page, f'{identity} commit -q --allow-empty -m "My first commit"\r', PROMPT)
    type_and_expect(page, "git log -1 --format=subject:%s\r", "subject:My first commit")
    page.close()


def fake_docker(folder: Path, message: str) -> str:
    """
    Make a ``docker`` command that fails as Docker does when it cannot reach its daemon.

    Parameters
    ----------
    folder : Path
        Where to put it.
    message : str
        What it prints to standard error.

    Returns
    -------
    str
        A ``PATH`` that finds it before any real ``docker``.
    """
    command = folder / "docker"
    command.write_text(f"#!/bin/sh\necho '{message}' >&2\nexit 1\n")
    command.chmod(0o755)
    return f"{folder}:/usr/bin:/bin"


@pytest.fixture(scope="session")
def docker_ready() -> None:
    """Skip the test unless the docker command exists and its daemon answers."""
    if shutil.which("docker") is None or docker("info").returncode != 0:
        pytest.skip("Docker or its daemon is not available")


@pytest.fixture(scope="session")
def image(docker_ready: None) -> Iterator[str]:
    """
    Build the image from this checkout under a test name, as a player's first run does.

    Parameters
    ----------
    docker_ready : None
        Skips when Docker is not available.

    Yields
    ------
    str
        The test name, used for the image, its container and its volume.
    """
    name = RUN_NAME
    built = run_script("build", name=name, timeout=900)
    assert built.returncode == 0, built.stdout + built.stderr
    yield name
    remove_docker_objects(name)


@pytest.fixture
def unused_name(docker_ready: None) -> Iterator[str]:
    """
    Give a docker name no test has used, and remove whatever a test made under it.

    Parameters
    ----------
    docker_ready : None
        Skips when Docker is not available.

    Yields
    ------
    str
        The name.
    """
    name = f"{RUN_NAME}-{secrets.token_hex(2)}"
    yield name
    remove_docker_objects(name)


@pytest.fixture
def copied_checkout(tmp_path: Path) -> Path:
    """
    Copy what the image is built from into a game folder.

    Parameters
    ----------
    tmp_path : Path
        The test's temporary folder.

    Returns
    -------
    Path
        The copy of the game's folder.
    """
    game = tmp_path / "firstcommit"
    skip_caches = shutil.ignore_patterns("__pycache__")
    shutil.copytree(ROOT / "deploy" / "docker", game / "deploy" / "docker")
    shutil.copytree(ROOT / "src" / "firstcommit", game / "src" / "firstcommit", ignore=skip_caches)
    shutil.copy2(ROOT / ".dockerignore", game / ".dockerignore")
    return game


def test_run_says_how_to_install_docker_when_it_is_missing(tmp_path: Path) -> None:
    for tool in ("bash", "dirname"):
        (tmp_path / tool).symlink_to(shutil.which(tool) or tool)

    result = run_script("play", name="unused", path=str(tmp_path))

    assert result.returncode == 1
    assert "Docker is not installed" in result.stderr
    assert "docs.docker.com/engine/install/ubuntu" in result.stderr


def test_run_says_how_to_start_docker_when_its_service_is_stopped(tmp_path: Path) -> None:
    path = fake_docker(tmp_path, "Cannot connect to the Docker daemon at unix:///var/run/docker.sock.")

    result = run_script("play", name="unused", path=path)

    assert result.returncode == 1
    assert "sudo service docker start" in result.stderr


def test_run_says_how_to_join_the_docker_group_when_access_is_denied(tmp_path: Path) -> None:
    path = fake_docker(tmp_path, "permission denied while trying to connect to the Docker daemon socket")

    result = run_script("play", name="unused", path=path)

    assert result.returncode == 1
    assert "usermod -aG docker" in result.stderr




def test_run_shows_its_commands_and_refuses_an_unknown_one() -> None:
    shown = run_script("help", name="unused")
    refused = run_script("start", name="unused")

    assert shown.returncode == 0
    assert all(
        command in shown.stdout for command in ("play", "shell", "build", "update", "reset", "test", "FIRSTCOMMIT_PORT")
    )
    assert refused.returncode == 2
    assert "Usage" in refused.stderr


@pytest.mark.docker
@pytest.mark.slow
def test_the_image_has_the_git_the_levels_are_checked_against(image: str) -> None:
    assert in_image(image, "git --version").startswith("git version 2.43.")


@pytest.mark.docker
@pytest.mark.slow
def test_the_image_has_python_3_12(image: str) -> None:
    assert in_image(image, "python3 --version").startswith("Python 3.12.")


@pytest.mark.docker
@pytest.mark.slow
def test_git_opens_nano_to_edit_a_commit_message(image: str) -> None:
    editor = in_image(image, 'readlink -f "$(command -v "$(git var GIT_EDITOR)")"', "--env", "TERM=xterm-256color")

    assert editor == "/usr/bin/nano"


@pytest.mark.docker
@pytest.mark.slow
def test_the_image_has_vim_for_the_playgrounds_editor_way_and_vi_opens_it(image: str) -> None:
    programs = in_image(image, 'readlink -f "$(command -v vim)" "$(command -v vi)"; vim --version | head -n 1')

    assert programs.splitlines()[:2] == ["/usr/bin/vim.basic", "/usr/bin/vim.basic"]
    assert programs.splitlines()[2].startswith("VIM - Vi IMproved 9.1")


@pytest.mark.docker
@pytest.mark.slow
def test_vim_keeps_the_title_the_games_shell_gives_it_and_says_insert_while_in_insert_mode(image: str) -> None:
    keys = "(sleep 2; printf ix; sleep 1; printf '\\033'; sleep 1; printf ':wq\\r')"
    titles = "import re, sys; print(re.findall(r'\\x1b]2;([^\\x07]*)\\x07', sys.stdin.buffer.read().decode()))"
    script = f'cd /tmp && echo line > a.txt && {keys} | script -qfc "vim a.txt" /dev/null | python3 -c "{titles}" && cat a.txt'
    shown = in_image(image, script, "--env", "TERM=xterm-256color", "--env", "FIRSTCOMMIT_TITLE=firstcommit-editor vim a.txt")
    seen, written = shown.splitlines()
    assert ast.literal_eval(seen) == ["firstcommit-editor vim a.txt", "firstcommit-editor vim a.txt insert", "firstcommit-editor vim a.txt", ""]
    assert written == "xline"


@pytest.mark.docker
@pytest.mark.slow
def test_git_help_shows_the_manual(image: str) -> None:
    manual = in_image(image, "git help commit 2>&1")

    assert "GIT-COMMIT(1)" in manual
    assert "minimized" not in manual


@pytest.mark.docker
@pytest.mark.slow
def test_the_game_runs_as_the_player_user_in_its_home(image: str) -> None:
    assert in_image(image, 'echo "$(id -un) $HOME $PWD"') == "player /home/player /home/player"


@pytest.mark.docker
@pytest.mark.slow
def test_the_game_shell_is_bash_even_when_started_through_docker_exec(image: str) -> None:
    assert in_image(image, 'echo "$SHELL"') == "/bin/bash"


@pytest.mark.docker
@pytest.mark.slow
def test_tab_completes_git_commands_in_an_interactive_shell(image: str) -> None:
    container = f"{image}-tab"
    process, terminal = spawn_in_terminal(
        ["docker", "run", "--rm", "-it", "--name", container, image, "bash"], dict(os.environ)
    )
    try:
        read_until(terminal, re.compile(r"\$ $"), timeout=30)
        os.write(terminal, b"git chec\t")
        read_until(terminal, re.compile("git checkout"), timeout=10)
        os.write(terminal, b"\x15exit\r")
        assert process.wait(timeout=30) == 0
    finally:
        process.kill()
        os.close(terminal)
        docker("container", "rm", "--force", container)


@pytest.mark.docker
@pytest.mark.slow
def test_the_launcher_never_imports_python_files_from_the_current_folder(image: str) -> None:
    plant = "mkdir -p /tmp/lab/firstcommit && cd /tmp/lab/firstcommit && touch __init__.py && echo 'print(\"planted\")' > __main__.py"

    output = in_image(image, f"{plant} && cd /tmp/lab && firstcommit --help 2>&1 || true")

    assert "planted" not in output


@pytest.mark.docker
@pytest.mark.slow
def test_the_game_home_is_kept_in_the_volume_between_two_containers(image: str) -> None:
    mount = f"{volume_of(image)}:{GAME_HOME}"

    in_image(image, "echo kept > ~/.firstcommit/probe", "--volume", mount)

    assert in_image(image, "cat ~/.firstcommit/probe", "--volume", mount) == "kept"


@pytest.mark.docker
@pytest.mark.slow
def test_build_reuses_the_image_of_a_checkout_with_the_same_sources(image: str, copied_checkout: Path) -> None:
    inputs = label(image, INPUTS_LABEL)

    result = run_script("build", name=image, script=copied_checkout / "deploy" / "docker" / "run")

    assert result.returncode == 0, result.stderr
    assert "Building" not in result.stdout
    assert label(image, INPUTS_LABEL) == inputs


@pytest.mark.docker
@pytest.mark.slow
def test_build_rebuilds_the_image_when_the_games_source_changes(image: str, copied_checkout: Path, unused_name: str) -> None:
    script = copied_checkout / "deploy" / "docker" / "run"
    store = copied_checkout / "src" / "firstcommit" / "termlab" / "store.py"
    store.write_text(store.read_text() + "\n# changed by a test\n")

    result = run_script("build", name=unused_name, script=script, timeout=600)

    assert result.returncode == 0, result.stderr
    assert "Building" in result.stdout
    assert label(unused_name, INPUTS_LABEL) != label(image, INPUTS_LABEL)
    assert in_image(unused_name, "tail -n 1 /opt/firstcommit/lib/firstcommit/termlab/store.py") == "# changed by a test"


@pytest.mark.docker
@pytest.mark.slow
def test_build_keeps_an_image_built_30_days_ago(image: str, tmp_path: Path) -> None:
    path, builds = docker_that_records_builds(tmp_path)
    built = date.fromisoformat(label(image, BUILT_LABEL))

    result = run_script("build", name=image, path=path, today=built + MAX_AGE)

    assert result.returncode == 0, result.stderr
    assert not builds.exists()


@pytest.mark.docker
@pytest.mark.slow
def test_build_refreshes_an_older_image_from_scratch_and_dates_it(image: str, tmp_path: Path) -> None:
    path, builds = docker_that_records_builds(tmp_path)
    today = date.fromisoformat(label(image, BUILT_LABEL)) + MAX_AGE + timedelta(days=1)

    result = run_script("build", name=image, path=path, today=today)

    assert result.returncode == 0, result.stderr
    assert "more than 30 days old" in result.stdout
    build = builds.read_text()
    assert "--pull" in build
    assert "--no-cache" in build
    assert f"{BUILT_LABEL}={today.isoformat()}" in build


@pytest.mark.docker
@pytest.mark.slow
def test_update_rebuilds_the_image_from_scratch_whatever_its_age(image: str, tmp_path: Path) -> None:
    path, builds = docker_that_records_builds(tmp_path)

    result = run_script("update", name=image, path=path, today=date.fromisoformat(label(image, BUILT_LABEL)))

    assert result.returncode == 0, result.stderr
    build = builds.read_text()
    assert "--pull" in build
    assert "--no-cache" in build


@pytest.mark.docker
@pytest.mark.slow
def test_reset_keeps_the_saved_game_unless_the_player_types_yes(unused_name: str) -> None:
    assert docker("volume", "create", volume_of(unused_name)).returncode == 0

    result = run_script("reset", name=unused_name, stdin="y\n")

    assert result.returncode == 0
    assert "Nothing was deleted" in result.stdout
    assert docker("volume", "inspect", volume_of(unused_name)).returncode == 0


@pytest.mark.docker
@pytest.mark.slow
def test_reset_deletes_the_saved_game_after_yes(unused_name: str) -> None:
    assert docker("volume", "create", volume_of(unused_name)).returncode == 0

    result = run_script("reset", name=unused_name, stdin="yes\n")

    assert result.returncode == 0
    assert docker("volume", "inspect", volume_of(unused_name)).returncode != 0


@pytest.mark.docker
@pytest.mark.slow
def test_the_whole_suite_passes_inside_the_container_where_only_the_docker_tests_skip(unused_name: str) -> None:
    result = run_script("test", name=unused_name, timeout=1800)

    skipped = [line for line in result.stdout.splitlines() if line.startswith("SKIPPED")]
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-4000:]
    assert skipped, "the container's pytest run lists no skip reasons"
    assert all("Docker or its daemon is not available" in line for line in skipped), skipped


@pytest.mark.docker
@pytest.mark.slow
def test_firstcommit_help_runs_as_the_player(image: str) -> None:
    assert "serve" in in_image(image, "firstcommit --help")


@pytest.mark.docker
@pytest.mark.slow
def test_playing_in_docker_runs_the_smoke_flow_unprivileged_and_keeps_the_save(image: str) -> None:
    port = free_port()
    env = {**os.environ, "FIRSTCOMMIT_DOCKER_NAME": image, "FIRSTCOMMIT_PORT": str(port), "PORT": "1"}
    process, terminal = spawn_in_terminal([str(RUN)], env)
    try:
        link = read_until(terminal, LINK, timeout=60)
        assert link["port"] == str(port)
        assert call(port, "GET", "/api/status", None)[0] == 403
        checked = play_the_template_level(port, link["token"])
        assert checked["solved"], checked
        check_the_page_terminal(port, link["token"])
        assert docker("exec", image, "date", "+%z").stdout.strip() == time.strftime("%z")

        os.write(terminal, b"\x03")

        assert process.wait(timeout=30) == 0
        assert docker("container", "inspect", image).returncode != 0
    finally:
        process.kill()
        os.close(terminal)
        docker("container", "rm", "--force", image)
    progress = json.loads(
        in_image(image, "cat ~/.firstcommit/progress.json", "--volume", f"{volume_of(image)}:{GAME_HOME}")
    )
    assert progress["levels"][TEMPLATE_LEVEL]["xp"] > 0


def test_run_dev_starts_the_game_in_dev_mode_and_play_alone_does_not(tmp_path: Path) -> None:
    log = tmp_path / "docker.log"
    command = tmp_path / "docker"
    command.write_text(f'#!/bin/sh\necho "$@" >> {log}\n[ "$1 $2" = "container inspect" ] && exit 1\nexit 0\n')
    command.chmod(0o755)
    path = f"{tmp_path}:/usr/bin:/bin"

    assert run_script("--dev", name="unused", path=path).returncode == 0
    assert run_script("play", name="unused", path=path).returncode == 0

    runs = [line for line in log.read_text().splitlines() if line.startswith("run ")]
    assert [run.endswith("firstcommit serve --dev") for run in runs] == [True, False]
