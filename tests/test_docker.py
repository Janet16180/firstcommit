"""
The Docker runtime: ``deploy/docker/run`` and the image it builds.

Tests marked ``docker`` build or run containers; they skip when Docker or its daemon is not
available. Every image tag, container and volume they create carries a random test name and is
removed afterwards. Some build the image around a stand-in game
(``tests/fixtures/docker_game_cli.py``), so playing is checked even before the game's own server
exists. The other tests check the script's messages with a fake ``docker``.
"""

import base64
import http.client
import os
import pty
import re
import secrets
import select
import shutil
import socket
import struct
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "deploy" / "docker" / "run"
TERMLAB_SRC = ROOT.parent / "termlab" / "src"
STAND_IN_CLI = ROOT / "tests" / "fixtures" / "docker_game_cli.py"
GAME_HOME = "/home/player/.firstcommit"
INPUTS_LABEL = "firstcommit.inputs"
TOKEN_HEADER = "X-FirstCommit-Token"
LINK = re.compile(r"http://localhost:(?P<port>\d+)/#token=(?P<token>[A-Za-z0-9_-]+)")
WAITS_FOR_INTEGRATION = pytest.mark.xfail(
    reason="waits for integration: the firstcommit command line and its serve command", strict=True
)


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
    *args: str, name: str, script: Path = RUN, path: str | None = None, stdin: str = "", timeout: float = 60
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


def inputs_label(image: str) -> str:
    """
    Give the hash of the sources an image was built from.

    Parameters
    ----------
    image : str
        The image's name.

    Returns
    -------
    str
        The image's ``firstcommit.inputs`` label.
    """
    result = docker("image", "inspect", "--format", f'{{{{ index .Config.Labels "{INPUTS_LABEL}" }}}}', image)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


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


def read_until(leader: int, pattern: re.Pattern[str], timeout: float) -> re.Match[str]:
    """
    Read a terminal until its output matches a pattern.

    Parameters
    ----------
    leader : int
        The controlling end of the terminal.
    pattern : re.Pattern[str]
        What to wait for.
    timeout : float
        Seconds before the test fails.

    Returns
    -------
    re.Match[str]
        The first match in everything read so far.

    Raises
    ------
    AssertionError
        If the terminal closes or the time runs out first; the message holds the output.
    """
    deadline = time.monotonic() + timeout
    seen = ""
    match = None
    closed = False
    while match is None and not closed and time.monotonic() < deadline:
        ready, _, _ = select.select([leader], [], [], 0.2)
        if not ready:
            continue
        chunk = read_terminal(leader)
        closed = chunk == b""
        seen += chunk.decode(errors="replace")
        match = pattern.search(seen)
    if match is None:
        raise AssertionError(f"no {pattern.pattern!r} in the terminal's output:\n{seen}")
    return match


def read_terminal(leader: int) -> bytes:
    """
    Read what a terminal has printed.

    Parameters
    ----------
    leader : int
        The controlling end of the terminal.

    Returns
    -------
    bytes
        The output, or nothing once every process on the terminal has closed it.
    """
    try:
        return os.read(leader, 65536)
    except OSError:
        # Linux reports a terminal whose other end is closed as EIO.
        return b""


def free_port() -> int:
    """
    Pick a port in the range these tests may use that nothing listens on.

    Returns
    -------
    int
        A port between 8851 and 8899.
    """
    free = [port for port in range(8851, 8900) if not listening(port)]
    if not free:
        raise RuntimeError("every port from 8851 to 8899 is in use")
    return free[0]


def listening(port: int) -> bool:
    """
    Tell whether something accepts connections on a local port.

    Parameters
    ----------
    port : int
        The port on 127.0.0.1.

    Returns
    -------
    bool
        True if a connection succeeds.
    """
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


def get(port: int, path: str, headers: dict[str, str]) -> int:
    """
    Send a GET to the game's server as the player's browser would, through localhost.

    Parameters
    ----------
    port : int
        The server's port.
    path : str
        The path to request.
    headers : dict[str, str]
        Headers besides ``Host``.

    Returns
    -------
    int
        The HTTP status.
    """
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    connection.request("GET", path, headers={"Host": f"localhost:{port}", **headers})
    status = connection.getresponse().status
    connection.close()
    return status


def open_page_terminal(port: int, token: str) -> socket.socket:
    """
    Open the page's terminal as the browser does: a WebSocket that carries the key as a subprotocol.

    Parameters
    ----------
    port : int
        The server's port.
    token : str
        The key from the printed link.

    Returns
    -------
    socket.socket
        The open connection, past the handshake.
    """
    page = socket.create_connection(("127.0.0.1", port), timeout=10)
    key = base64.b64encode(os.urandom(16)).decode()
    page.sendall(
        (
            "GET /api/terminal HTTP/1.1\r\n"
            f"Host: localhost:{port}\r\nOrigin: http://localhost:{port}\r\n"
            f"Sec-WebSocket-Protocol: firstcommit, t.{token}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode()
    )
    reply = b""
    while not reply.endswith(b"\r\n\r\n"):
        reply += page.recv(1)
    assert reply.startswith(b"HTTP/1.1 101"), reply
    return page


def type_and_expect(page: socket.socket, keys: str, expected: str, timeout: float = 15) -> None:
    """
    Type keys into the page's terminal and wait until its output shows what they should cause.

    Parameters
    ----------
    page : socket.socket
        The terminal's open WebSocket.
    keys : str
        What to type, control characters included.
    expected : str
        A regular expression the output that follows must match.
    timeout : float
        Seconds before the test fails.

    Raises
    ------
    AssertionError
        If the output does not match in time; the message holds the output.
    """
    payload = keys.encode()
    mask = os.urandom(4)
    size = bytes([0x80 | len(payload)]) if len(payload) < 126 else bytes([0x80 | 126]) + struct.pack("!H", len(payload))
    page.sendall(bytes([0x82]) + size + mask + bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload)))
    deadline = time.monotonic() + timeout
    pending = b""
    output = ""
    while re.search(expected, output) is None and time.monotonic() < deadline:
        if select.select([page], [], [], 0.2)[0]:
            pending += page.recv(65536)
        shown, pending = terminal_output(pending)
        output += shown
    assert re.search(expected, output), f"no {expected!r} in the page terminal's output:\n{output}"


def terminal_output(frames: bytes) -> tuple[str, bytes]:
    """
    Take the terminal output out of the complete WebSocket frames a server sent.

    Parameters
    ----------
    frames : bytes
        Bytes received so far; a frame may be cut at the end.

    Returns
    -------
    tuple[str, bytes]
        The text of the complete binary frames, and the bytes of the cut frame, if any.
    """
    output = b""
    while len(frames) >= 2:
        size, start = frames[1] & 0x7F, 2
        if size == 126:
            size, start = struct.unpack("!H", frames[2:4])[0], 4
        if len(frames) < start + size:
            break
        if frames[0] & 0x0F == 0x2:
            output += frames[start : start + size]
        frames = frames[start + size :]
    return output.decode(errors="replace"), frames


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
    name = f"firstcommit-test-{secrets.token_hex(4)}"
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
    name = f"firstcommit-test-{secrets.token_hex(4)}"
    yield name
    remove_docker_objects(name)


@pytest.fixture
def stand_in_image(copied_checkout: Path, unused_name: str) -> str:
    """
    Build, under an unused name, an image whose game is a termlab server that does not need the game's routes.

    Parameters
    ----------
    copied_checkout : Path
        A copy of the game's folder, whose command line is replaced.
    unused_name : str
        The name to build under; removed afterwards.

    Returns
    -------
    str
        The name.
    """
    package = copied_checkout / "src" / "firstcommit"
    shutil.copy2(STAND_IN_CLI, package / "cli.py")
    (package / "web" / "static").mkdir(parents=True, exist_ok=True)
    built = run_script("build", name=unused_name, script=copied_checkout / "deploy" / "docker" / "run", timeout=600)
    assert built.returncode == 0, built.stdout + built.stderr
    return unused_name


@pytest.fixture
def copied_checkout(tmp_path: Path) -> Path:
    """
    Copy what the image is built from into a game folder with termlab next to it.

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
    shutil.copytree(TERMLAB_SRC / "termlab", tmp_path / "termlab" / "src" / "termlab", ignore=skip_caches)
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
    assert all(command in shown.stdout for command in ("play", "shell", "build", "reset", "test", "FIRSTCOMMIT_PORT"))
    assert refused.returncode == 2
    assert "Usage" in refused.stderr


@pytest.mark.docker
@pytest.mark.slow
def test_the_image_has_the_git_the_lessons_are_checked_against(image: str) -> None:
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
    label = inputs_label(image)

    result = run_script("build", name=image, script=copied_checkout / "deploy" / "docker" / "run")

    assert result.returncode == 0, result.stderr
    assert "Building" not in result.stdout
    assert inputs_label(image) == label


@pytest.mark.docker
@pytest.mark.slow
def test_build_rebuilds_the_image_when_termlab_changes(image: str, copied_checkout: Path, unused_name: str) -> None:
    script = copied_checkout / "deploy" / "docker" / "run"
    store = copied_checkout.parent / "termlab" / "src" / "termlab" / "store.py"
    store.write_text(store.read_text() + "\n# changed by a test\n")

    result = run_script("build", name=unused_name, script=script, timeout=600)

    assert result.returncode == 0, result.stderr
    assert "Building" in result.stdout
    assert inputs_label(unused_name) != inputs_label(image)
    assert in_image(unused_name, "tail -n 1 /opt/firstcommit/lib/termlab/store.py") == "# changed by a test"


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
def test_play_runs_the_game_without_privileges_and_its_terminal_still_works(
    stand_in_image: str, copied_checkout: Path
) -> None:
    port = free_port()
    env = {**os.environ, "FIRSTCOMMIT_DOCKER_NAME": stand_in_image, "FIRSTCOMMIT_PORT": str(port), "PORT": "1"}
    process, terminal = spawn_in_terminal([str(copied_checkout / "deploy" / "docker" / "run")], env)
    try:
        link = read_until(terminal, LINK, timeout=60)
        assert link["port"] == str(port)
        page = open_page_terminal(port, link["token"])
        type_and_expect(page, "awk '/CapBnd|NoNewPrivs/' /proc/self/status\r", r"CapBnd:\s+0{16}\s+NoNewPrivs:\s+1")
        type_and_expect(page, "git help commit | head -n 1\r", r"GIT-COMMIT\(1\)")
        type_and_expect(page, "git chec\t", "git checkout")
        type_and_expect(
            page,
            "\x15cd /tmp && git init -q demo && cd demo && git -c user.name=Player -c user.email=player@example.com commit --allow-empty\r",
            "GNU nano",
        )
        type_and_expect(page, "My first commit\x18", "Save modified buffer")
        type_and_expect(page, "y", "File Name to Write")
        type_and_expect(page, "\r", r"\$ $")
        type_and_expect(page, "git log -1 --format=subject:%s\r", "subject:My first commit")
        page.close()

        os.write(terminal, b"\x03")

        assert process.wait(timeout=30) == 0
        assert docker("container", "inspect", stand_in_image).returncode != 0
    finally:
        process.kill()
        os.close(terminal)
        docker("container", "rm", "--force", stand_in_image)


@pytest.mark.docker
@pytest.mark.slow
def test_the_whole_suite_passes_inside_the_container(unused_name: str) -> None:
    result = run_script("test", name=unused_name, timeout=1800)

    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-4000:]


@pytest.mark.docker
@pytest.mark.slow
def test_firstcommit_help_runs_as_the_player(image: str) -> None:
    assert "serve" in in_image(image, "firstcommit --help")


@pytest.mark.docker
@pytest.mark.slow
@WAITS_FOR_INTEGRATION
def test_play_serves_the_game_through_localhost_until_ctrl_c(image: str) -> None:
    port = free_port()
    env = {**os.environ, "FIRSTCOMMIT_DOCKER_NAME": image, "FIRSTCOMMIT_PORT": str(port)}
    process, terminal = spawn_in_terminal([str(RUN)], env)
    try:
        link = read_until(terminal, LINK, timeout=60)
        assert link["port"] == str(port)
        assert get(port, "/api/status", {TOKEN_HEADER: link["token"]}) == 200
        assert get(port, "/api/status", {}) == 403
        assert docker("exec", image, "date", "+%z").stdout.strip() == time.strftime("%z")

        os.write(terminal, b"\x03")

        assert process.wait(timeout=30) == 0
        assert docker("container", "inspect", image).returncode != 0
    finally:
        process.kill()
        os.close(terminal)
        docker("container", "rm", "--force", image)
