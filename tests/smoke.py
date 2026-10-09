"""
The smoke flow of DESIGN.md section 3, shared by each runtime's smoke test.

`play_the_template_level` plays the template level (`TEMPLATE_LEVEL`, the Orbit level "Plant the
flag") as a player does in the page: through the game's API and the page's terminal, so the same flow runs against ``firstcommit serve`` on this
machine (``tests/test_smoke.py``) and in the Docker image (``tests/test_docker.py``).
"""

import base64
import http.client
import json
import os
import re
import select
import socket
import struct
import time
from typing import Any

from firstcommit.web import routes

TOKEN_HEADER = routes.SETTINGS.token_header
LINK = re.compile(r"http://localhost:(?P<port>\d+)/#token=(?P<token>[A-Za-z0-9_-]+)")
PROMPT = r"\$ $"
TEMPLATE_LEVEL = "liftoff-flag"


def call(port: int, method: str, path: str, token: str | None, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    """
    Call the game's API as the page does in the browser: through localhost, with the key in its header.

    Parameters
    ----------
    port : int
        The server's port.
    method : str
        ``GET`` or ``POST``.
    path : str
        The path, with its query.
    token : str | None
        The key from the printed link, or None to leave it out.
    body : dict[str, Any] | None
        The JSON body of a POST.

    Returns
    -------
    tuple[int, Any]
        The HTTP status, and the decoded reply when it is JSON (else None).
    """
    headers = {"Host": f"localhost:{port}"}
    if token is not None:
        headers[TOKEN_HEADER] = token
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()
        headers.update({"Content-Type": "application/json", "Origin": f"http://localhost:{port}"})
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    connection.request(method, path, body=payload, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    connection.close()
    reply = None
    if response.getheader("Content-Type", "").startswith("application/json"):
        reply = json.loads(raw)
    return response.status, reply


def play_the_template_level(port: int, token: str) -> dict[str, Any]:
    """
    Play the smoke flow of DESIGN.md section 3: the template level, through the page's API and terminal.

    Open the level and start it; for each quest step, type its command into the page's terminal
    and report the step as the page does (its goals read the typed lines); then check the level
    as the page's polling does.

    Parameters
    ----------
    port : int
        The server's port.
    token : str
        The key from the printed link.

    Returns
    -------
    dict[str, Any]
        The last check's reply (`firstcommit.game.CheckResult`).
    """
    status, level = call(port, "GET", f"/api/level?id={TEMPLATE_LEVEL}", token)
    assert status == 200, level
    status, active = call(port, "POST", "/api/start", token, {"level": TEMPLATE_LEVEL})
    assert status == 200, active
    status, _ = call(port, "GET", "/api/observe", token)
    assert status == 200
    page = open_page_terminal(port, token)
    type_and_expect(page, "", PROMPT)
    typed = []
    for step in level["steps"]:
        typed.append(step["command"])
        type_and_expect(page, typed[-1] + "\r", PROMPT)
        status, result = call(port, "POST", "/api/step", token, {"answer": None})
        assert status == 200 and result["correct"], (step["id"], result)
    page.close()
    status, observed = call(port, "GET", "/api/observe", token)
    assert status == 200, observed
    assert observed["commands"] == [{"line": line, "status": 0} for line in typed]
    status, checked = call(port, "POST", "/api/check", token, {"answer": None, "auto": True})
    assert status == 200, checked
    return dict(checked)


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


def type_and_expect(page: socket.socket, keys: str, expected: str, timeout: float = 15) -> str:
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

    Returns
    -------
    str
        The output read after typing, up to the match.

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
    return output


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


def read_until(leader: int, pattern: re.Pattern[str], timeout: float) -> re.Match[str]:
    """
    Read a terminal or a pipe until its output matches a pattern.

    Parameters
    ----------
    leader : int
        The controlling end of the terminal, or the reading end of the pipe.
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
        If the output ends or the time runs out first; the message holds the output.
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
    Read what a terminal or a pipe has printed.

    Parameters
    ----------
    leader : int
        The controlling end of the terminal, or the reading end of the pipe.

    Returns
    -------
    bytes
        The output, or nothing once every writer has closed it.
    """
    try:
        return os.read(leader, 65536)
    except OSError:
        # Linux reports a terminal whose other end is closed as EIO.
        return b""


def free_port() -> int:
    """
    Ask the OS for a local port nothing listens on.

    Returns
    -------
    int
        The port; it stays free until something binds it, which the caller does at once.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
    return port
