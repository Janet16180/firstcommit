import base64
import contextlib
import dataclasses
import io
import json
import math
import os
import random
import re
import select
import signal
import socket
import struct
import subprocess
import termios
import threading
import time
import tty
from collections.abc import Callable, Iterator
from email.message import Message
from pathlib import Path
from typing import Any, BinaryIO, NamedTuple

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from firstcommit.termlab.web import shell, terminal
from termlab_helpers import MARKER, SETTINGS, TERMINAL, Site, fetch, held_open, make_opener, wait_for

TIMEOUT = 10
SECOND = "/api/terminal/second"
# The sample handshake of RFC 6455, section 1.3.
KEY = "dGhlIHNhbXBsZSBub25jZQ=="
ACCEPT = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
MASK = b"\x37\xfa\x21\x3d"


def read_proc(pid: int, name: str) -> bytes | None:
    """
    Read a file under /proc/PID.

    Parameters
    ----------
    pid : int
        Process id.
    name : str
        Path relative to /proc/PID, e.g. ``"environ"``.

    Returns
    -------
    bytes | None
        File contents, or None if the process is gone or the file is not readable.
    """
    try:
        return (Path("/proc") / str(pid) / name).read_bytes()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None


def pids() -> list[int]:
    """
    List the processes visible in /proc.

    Returns
    -------
    list[int]
        Sorted process ids.
    """
    return sorted(int(entry.name) for entry in Path("/proc").iterdir() if entry.name.isdigit())


def stat_fields(pid: int) -> list[str]:
    """
    Split /proc/PID/stat into fields, coping with spaces and parentheses in the command name.

    Parameters
    ----------
    pid : int
        Process id.

    Returns
    -------
    list[str]
        Fields numbered as in proc(5) minus one: index 0 is the pid, 1 the comm,
        2 the state, 3 the ppid. Empty if the process is gone.
    """
    raw = (read_proc(pid, "stat") or b"").decode(errors="replace")
    if not raw:
        return []
    head, _, tail = raw.rpartition(")")
    pid_text, _, comm = head.partition(" (")
    return [pid_text, comm, *tail.split()]


def proc_state(pid: int) -> str | None:
    """
    Get a process's one-letter scheduler state.

    Parameters
    ----------
    pid : int
        Process id.

    Returns
    -------
    str | None
        ``R``, ``S``, ``Z``..., or None if the process is gone.
    """
    fields = stat_fields(pid)
    return fields[2] if fields else None


def is_alive(pid: int) -> bool:
    """
    Tell whether a process exists and is not a zombie.

    Parameters
    ----------
    pid : int
        Process id.

    Returns
    -------
    bool
        False for vanished, zombie (Z) and dead (X) processes.
    """
    return proc_state(pid) not in (None, "Z", "X")


class Connection(NamedTuple):
    """A client socket after the upgrade request, and the server's answer."""

    sock: socket.socket
    reader: BinaryIO
    status: int
    headers: dict[str, str]


def shells() -> list[int]:
    """
    List this process's children started for a terminal, in any state (zombies included).

    Returns
    -------
    list[int]
        Pids of ``setsid`` processes and the shells they became.
    """
    found = []
    for pid in pids():
        fields = stat_fields(pid)
        if fields and int(fields[3]) == os.getpid() and fields[1] in {"setsid", "bash"}:
            found.append(pid)
    return found


def foreground(shell: int) -> str:
    """
    Name the terminal's foreground job.

    Parameters
    ----------
    shell : int
        Pid of the terminal's shell.

    Returns
    -------
    str
        Command name of the foreground process group's leader; empty if it just exited.
    """
    # Field 8 of /proc/PID/stat, tpgid: the terminal's foreground process group.
    leader = stat_fields(int(stat_fields(shell)[7]))
    return leader[1] if leader else ""


def upgrade(port: int, headers: dict[str, str], path: str = shell.TERMINAL_PATH) -> Connection:
    """
    Connect and send a WebSocket upgrade request for a terminal.

    Parameters
    ----------
    port : int
        Server port on 127.0.0.1.
    headers : dict[str, str]
        Request headers.
    path : str
        The terminal's path.

    Returns
    -------
    Connection
        The socket, a reader on it, the response status and its headers (names lowercased).
    """
    sock = socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT)
    lines = [f"GET {path} HTTP/1.1", *(f"{name}: {value}" for name, value in headers.items()), "", ""]
    sock.sendall("\r\n".join(lines).encode())
    reader = sock.makefile("rb")
    status = int(reader.readline().split()[1])
    response = {}
    line = reader.readline()
    while line.strip():
        name, _, value = line.decode().partition(":")
        response[name.strip().lower()] = value.strip()
        line = reader.readline()
    return Connection(sock, reader, status, response)


def frame(first_byte: int, payload: bytes, masked: bool = True) -> bytes:
    """
    Encode a client frame, valid or not.

    Parameters
    ----------
    first_byte : int
        FIN, reserved bits and opcode.
    payload : bytes
        Payload.
    masked : bool
        Whether to mask it, as clients must.

    Returns
    -------
    bytes
        The frame.
    """
    length = len(payload)
    mask_bit = 0x80 if masked else 0
    if length < 126:
        header = struct.pack("!BB", first_byte, mask_bit | length)
    elif length < 1 << 16:
        header = struct.pack("!BBH", first_byte, mask_bit | 126, length)
    else:
        header = struct.pack("!BBQ", first_byte, mask_bit | 127, length)
    if not masked:
        return header + payload
    return header + MASK + bytes(byte ^ MASK[index % 4] for index, byte in enumerate(payload))


def send(conn: Connection, opcode: int, payload: bytes, fin: bool = True) -> None:
    """
    Send a valid, masked client frame.

    Parameters
    ----------
    conn : Connection
        Open terminal.
    opcode : int
        Frame type.
    payload : bytes
        Payload.
    fin : bool
        Whether this is the last frame of its message.
    """
    conn.sock.sendall(frame((0x80 if fin else 0) | opcode, payload))


def receive(conn: Connection) -> tuple[int, bytes]:
    """
    Read one server frame.

    Parameters
    ----------
    conn : Connection
        Open terminal.

    Returns
    -------
    tuple[int, bytes]
        Opcode and payload.
    """
    first, second = conn.reader.read(2)
    length = second & 0x7F
    if length == 126:
        (length,) = struct.unpack("!H", conn.reader.read(2))
    elif length == 127:
        (length,) = struct.unpack("!Q", conn.reader.read(8))
    assert first & 0x80, "server frames are final"
    assert not second & 0x80, "server frames are unmasked"
    return first & 0x0F, conn.reader.read(length)


def output_until(conn: Connection, pattern: bytes) -> re.Match[bytes]:
    """
    Collect the terminal's output until a pattern shows up.

    Parameters
    ----------
    conn : Connection
        Open terminal.
    pattern : bytes
        Regular expression; make it match only command output, not the echoed command line.

    Returns
    -------
    re.Match[bytes]
        The match, against everything received so far.
    """
    output = b""
    match = None
    while match is None:
        opcode, payload = receive(conn)
        assert opcode != terminal.OP_CLOSE, f"closed early: {payload!r}, output so far {output!r}"
        output += payload if opcode == terminal.OP_BINARY else b""
        match = re.search(pattern, output)
    return match


def close_frame(conn: Connection) -> tuple[int, str]:
    """
    Skip output until the server's close frame.

    Parameters
    ----------
    conn : Connection
        Open terminal.

    Returns
    -------
    tuple[int, str]
        Close code and reason.
    """
    opcode, payload = receive(conn)
    while opcode != terminal.OP_CLOSE:
        opcode, payload = receive(conn)
    return struct.unpack("!H", payload[:2])[0], payload[2:].decode()


def hang_up(conn: Connection) -> tuple[int, str]:
    """
    Close the connection properly and wait until the server has finished with it.

    Parameters
    ----------
    conn : Connection
        Open terminal.

    Returns
    -------
    tuple[int, str]
        The server's close code and reason.
    """
    send(conn, terminal.OP_CLOSE, struct.pack("!H", 1000))
    answer = close_frame(conn)
    assert conn.reader.read() == b""
    return answer


@pytest.fixture(autouse=True)
def plain_shell(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """
    Use bash with an empty home, so the player's own shell setup stays out of the tests.

    Afterwards, check that every shell a test started was stopped and reaped.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        To set SHELL and HOME.
    tmp_path : Path
        The test's own folder, used as HOME.

    Yields
    ------
    None
        Control returns to the test.
    """
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TESTGAME_HOME", str(tmp_path))
    yield
    wait_for(lambda: not shells(), timeout=5, what="the terminals' shells to be reaped")


@pytest.fixture
def pty_pair() -> Iterator[tuple[int, int]]:
    """
    Open a pseudo-terminal whose master end does not block, as the server opens it; close both ends afterwards.

    Yields
    ------
    tuple[int, int]
        Master and slave file descriptors.
    """
    master, slave = os.openpty()
    os.set_blocking(master, False)
    yield master, slave
    os.close(master)
    os.close(slave)


@pytest.fixture
def connect(site: Site) -> Iterator[Callable[..., Connection]]:
    """
    Open terminals with a valid handshake, or one with some headers changed; close them all afterwards.

    Parameters
    ----------
    site : Site
        The running server, unless a call names another one.

    Yields
    ------
    Callable[..., Connection]
        Takes an optional dict of header changes (None removes a header), an optional server and
        an optional terminal path.
    """
    opened: list[Connection] = []

    def open_terminal(
        changes: dict[str, str | None] | None = None, to: Site = site, path: str = shell.TERMINAL_PATH
    ) -> Connection:
        valid = {
            "Host": f"127.0.0.1:{to.port}",
            "Origin": f"http://127.0.0.1:{to.port}",
            "Sec-WebSocket-Protocol": f"testgame, t.{to.token}",
            "Upgrade": "websocket",
            "Connection": "keep-alive, Upgrade",
            "Sec-WebSocket-Key": KEY,
            "Sec-WebSocket-Version": "13",
        }
        merged = {**valid, **(changes or {})}
        conn = upgrade(to.port, {name: value for name, value in merged.items() if value is not None}, path)
        opened.append(conn)
        return conn

    yield open_terminal
    for conn in opened:
        conn.reader.close()
        conn.sock.close()


def test_round_trip_through_the_shell(connect: Callable[..., Connection]) -> None:
    conn = connect()
    assert conn.status == 101
    assert conn.headers["sec-websocket-accept"] == ACCEPT
    assert conn.headers["sec-websocket-protocol"] == "testgame"
    send(conn, terminal.OP_BINARY, b"echo lab-$((6*7)) shell=$$\n")
    match = output_until(conn, rb"lab-42 shell=(\d+)")
    assert b"no job control" not in match.string
    shell = int(match.group(1))
    assert is_alive(shell)
    assert hang_up(conn) == (1000, "")
    assert proc_state(shell) is None


def test_bad_handshakes_are_refused(connect: Callable[..., Connection], site: Site) -> None:
    port, token = site.port, site.token
    refused = [
        ({"Sec-WebSocket-Protocol": None}, 403),
        ({"Sec-WebSocket-Protocol": "testgame"}, 403),
        ({"Sec-WebSocket-Protocol": "testgame, t.wrong"}, 403),
        ({"Sec-WebSocket-Protocol": f"testgame, t.{token[:-1]}"}, 403),
        ({"Sec-WebSocket-Protocol": f"t.{token}"}, 403),
        ({"Sec-WebSocket-Protocol": f"testgame, t.wrong, t.{token}"}, 403),
        ({"Sec-WebSocket-Protocol": f"testgame, t.{token}, t.{token}"}, 403),
        ({"Sec-WebSocket-Protocol": f"testgame, {token}"}, 403),
        ({"Sec-WebSocket-Protocol": None, "Cookie": f"testgame_token={token}"}, 403),
        ({"Sec-WebSocket-Protocol": None, SETTINGS.token_header: token}, 403),
        ({"Origin": None}, 403),
        ({"Origin": "http://evil.example"}, 403),
        ({"Origin": f"http://localhost:{port + 1}"}, 403),
        ({"Origin": "null"}, 403),
        ({"Origin": f"https://127.0.0.1:{port}"}, 403),
        ({"Origin": f"http://127.0.0.1:{port}/"}, 403),
        ({"Host": f"evil.example:{port}"}, 403),
        ({"Host": f"evil.example:{port}", "Origin": f"http://evil.example:{port}"}, 403),
        ({"Upgrade": None}, 400),
        ({"Connection": "keep-alive"}, 400),
        ({"Sec-WebSocket-Version": "8"}, 400),
        ({"Sec-WebSocket-Key": "c2hvcnQ="}, 400),
        ({"Sec-WebSocket-Key": "not base64!"}, 400),
    ]
    for changes, status in refused:
        conn = connect(changes)
        assert conn.status == status, changes
        assert "sec-websocket-accept" not in conn.headers
    assert shells() == []

    for changes in [{"Origin": f"http://localhost:{port}", "Host": f"localhost:{port}"}, {"Sec-WebSocket-Protocol": f"t.{token},testgame"}]:
        conn = connect(changes)
        assert conn.status == 101, changes
        assert conn.headers["sec-websocket-protocol"] == "testgame"
        assert not any(token in value for value in conn.headers.values())
        hang_up(conn)


def test_resize_sets_the_terminal_size_and_garbage_is_ignored(connect: Callable[..., Connection]) -> None:
    conn = connect()
    garbage = [
        b"not json",
        b"[" * 5000,
        b"[1, 2]",
        json.dumps({"type": "other"}).encode(),
        json.dumps({"type": "resize", "cols": 0, "rows": 10}).encode(),
        json.dumps({"type": "resize", "cols": 100, "rows": 1001}).encode(),
        json.dumps({"type": "resize", "cols": True, "rows": 10}).encode(),
        json.dumps({"type": "resize", "cols": "100", "rows": "31"}).encode(),
        json.dumps({"type": "resize", "cols": 2.5, "rows": 3}).encode(),
        json.dumps({"type": "resize", "cols": 100}).encode(),
    ]
    for payload in garbage:
        send(conn, terminal.OP_TEXT, payload)
    send(conn, terminal.OP_BINARY, b"stty size; echo size-$((1+1))\n")
    assert output_until(conn, rb"(\d+ \d+)\r\nsize-2").group(1) == b"24 80"

    send(conn, terminal.OP_TEXT, json.dumps({"type": "resize", "cols": 100, "rows": 31}).encode())
    send(conn, terminal.OP_BINARY, b"stty size; echo size-$((2+1))\n")
    assert output_until(conn, rb"(\d+ \d+)\r\nsize-3").group(1) == b"31 100"
    hang_up(conn)


def test_the_shell_gets_a_clean_environment(
    connect: Callable[..., Connection], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(MARKER, "/nonexistent/lab")
    monkeypatch.setenv("TMUX", "/tmp/tmux-sock,1,0")
    conn = connect()
    send(conn, terminal.OP_BINARY, b'echo "ENV:$((1+1)):$$:${TESTGAME_LAB-unset}:${TMUX-unset}:$TESTGAME_HOME:$TERM:$PWD:END"\n')
    match = output_until(conn, rb"ENV:2:(\d+):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):END")
    shell, lab, tmux, home, term, cwd = (group.decode() for group in match.groups())
    assert (lab, tmux) == ("unset", "unset")
    assert home == str(tmp_path)
    assert term == "xterm-256color"
    assert cwd == str(tmp_path)
    assert MARKER.encode() not in (read_proc(int(shell), "environ") or b"")
    hang_up(conn)


def test_dropping_the_connection_hangs_up_the_shell_and_its_jobs(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"sleep 300 & echo JOB:$$:$!:$((1+1))\n")
    shell, job = (int(pid) for pid in output_until(conn, rb"JOB:(\d+):(\d+):2").groups())
    assert is_alive(job)
    conn.reader.close()
    conn.sock.close()
    wait_for(lambda: proc_state(shell) is None and not is_alive(job), what="the shell and its job to go")


def test_exiting_the_shell_closes_the_connection(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"echo shell=$$; exit\n")
    shell = int(output_until(conn, rb"shell=(\d+)").group(1))
    assert close_frame(conn) == (1000, "the shell exited")
    send(conn, terminal.OP_CLOSE, struct.pack("!H", 1000))
    assert conn.reader.read() == b""
    assert proc_state(shell) is None


def test_exiting_closes_even_while_a_leftover_job_keeps_printing(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"(for i in $(seq 200); do echo spam; sleep 0.05; done) & echo job=$!\n")
    job = int(output_until(conn, rb"job=(\d+)").group(1))
    try:
        output_until(conn, rb"spam")
        send(conn, terminal.OP_BINARY, b"exit\n")
        assert close_frame(conn) == (1000, "the shell exited")
        send(conn, terminal.OP_CLOSE, struct.pack("!H", 1000))
        assert conn.reader.read() == b""
    finally:
        os.kill(job, signal.SIGTERM)


def test_fragmented_messages_and_pings(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"echo frag-", fin=False)
    send(conn, terminal.OP_PING, b"are you there")
    send(conn, terminal.OP_CONTINUATION, b"$((40+2))\n")
    opcode, payload = receive(conn)
    while opcode != terminal.OP_PONG:
        opcode, payload = receive(conn)
    assert payload == b"are you there"
    output_until(conn, rb"frag-42")
    hang_up(conn)


def test_too_many_terminals_are_turned_away(connect: Callable[..., Connection]) -> None:
    open_ones = [connect() for _ in range(TERMINAL.max_terminals)]
    assert [conn.status for conn in open_ones] == [101] * TERMINAL.max_terminals

    extra = connect()
    assert extra.status == 101
    code, reason = close_frame(extra)
    assert code == 1013
    assert f"too many terminals open (at most {TERMINAL.max_terminals})" in reason
    send(extra, terminal.OP_CLOSE, struct.pack("!H", 1000))
    assert extra.reader.read() == b""

    hang_up(open_ones.pop())
    replacement = connect()
    send(replacement, terminal.OP_BINARY, b"echo again-$((6*7))\n")
    output_until(replacement, rb"again-42")
    for conn in [*open_ones, replacement]:
        hang_up(conn)


def test_each_terminal_path_starts_the_shell_its_own_settings_give(
    connect: Callable[..., Connection], start_site: Callable[..., Site]
) -> None:
    second = dataclasses.replace(TERMINAL, environment=lambda: {**TERMINAL.environment(), "WHICH": "second"})
    site = start_site(more_terminals={SECOND: second})
    first, other = connect(to=site), connect(to=site, path=SECOND)
    assert (first.status, other.status) == (101, 101)
    send(first, terminal.OP_BINARY, b"echo which-${WHICH:-first}\n")
    send(other, terminal.OP_BINARY, b"echo which-${WHICH:-first}\n")
    output_until(first, rb"which-first")
    output_until(other, rb"which-second")
    hang_up(first)
    hang_up(other)


def test_the_terminals_of_every_path_share_one_limit(
    connect: Callable[..., Connection], start_site: Callable[..., Site]
) -> None:
    one = dataclasses.replace(TERMINAL, max_terminals=1)
    site = start_site(terminal=one, more_terminals={SECOND: one})
    first = connect(to=site)
    extra = connect(to=site, path=SECOND)
    assert close_frame(extra)[0] == 1013
    send(extra, terminal.OP_CLOSE, struct.pack("!H", 1000))

    hang_up(first)
    replacement = connect(to=site, path=SECOND)
    send(replacement, terminal.OP_BINARY, b"echo again-$((6*7))\n")
    output_until(replacement, rb"again-42")
    hang_up(replacement)


def test_a_turned_away_client_that_keeps_pinging_is_dropped_after_one_deadline(
    connect: Callable[..., Connection], start_site: Callable[..., Site], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(terminal, "CLOSE_TIMEOUT", 1.0)
    site = start_site(terminal=dataclasses.replace(TERMINAL, max_terminals=1))
    first = connect(to=site)
    extra = connect(to=site)
    assert close_frame(extra)[0] == 1013
    # It never answers the close frame, but pings often enough to beat any per-read timeout.
    assert held_open(extra.sock, frame(0x89, b"still here")) < 2.0
    hang_up(first)


def test_malformed_frames_close_the_connection_without_crashing_the_server(
    connect: Callable[..., Connection], site: Site, capsys: pytest.CaptureFixture[str]
) -> None:
    cases = [
        (frame(0x82, b"hi", masked=False), 1002),
        (frame(0xC2, b"hi"), 1002),
        (frame(0x83, b"hi"), 1002),
        (frame(0x89, b"p" * 200), 1002),
        (frame(0x09, b"ping"), 1002),
        (frame(0x88, b"\x03"), 1002),
        (frame(0x81, b"\xff\xfe"), 1007),
        *((frame(0x88, struct.pack("!H", code)), 1002) for code in [0, 999, 1004, 1005, 1006, 1015, 2000, 2999, 5000]),
        (frame(0x88, struct.pack("!H", 1000) + b"bye \xff"), 1007),
        (frame(0x01, b"caf\xc3") + frame(0x80, b"\xa9 ok") + frame(0x81, b"\xc3"), 1007),
        (frame(0x80, b"x"), 1002),
        (frame(0x02, b"x") + frame(0x82, b"y"), 1002),
        (struct.pack("!BBQ", 0x82, 0x80 | 127, 1 << 40) + MASK, 1009),
        (frame(0x02, b"a" * (600 * 1024)) + frame(0x80, b"b" * (600 * 1024)), 1009),
    ]
    for raw, code in cases:
        conn = connect()
        conn.sock.sendall(raw)
        assert close_frame(conn)[0] == code, raw[:4]
        # Wait for the server to finish the session and free its slot. It may reset
        # the connection instead of closing it, since part of the bad frame is never read.
        with contextlib.suppress(ConnectionResetError):
            conn.reader.read()

    truncated = connect()
    truncated.sock.sendall(frame(0x82, b"hello")[:-2])
    truncated.reader.close()
    truncated.sock.close()

    wait_for(lambda: not shells(), what="the shells to be reaped")
    assert fetch(make_opener(site.token), f"{site.url}/api/status")[0] == 200
    assert "Traceback" not in capsys.readouterr().err


def test_a_paste_nobody_reads_does_not_block_the_connection(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"echo shell=$$\n")
    shell = int(output_until(conn, rb"shell=(\d+)").group(1))
    send(conn, terminal.OP_BINARY, b"sleep 30\n")
    wait_for(lambda: foreground(shell) == "sleep", what="sleep to take the foreground")

    # Lines fill the terminal's input buffer after about 20 KB; sleep never reads them.
    send(conn, terminal.OP_BINARY, (b"x" * 99 + b"\n") * 3000)
    send(conn, terminal.OP_PING, b"still there?")
    opcode, payload = receive(conn)
    while opcode != terminal.OP_PONG:
        opcode, payload = receive(conn)
    assert payload == b"still there?"

    # Ctrl-C does not fit in the full queue either; it must still stop sleep.
    send(conn, terminal.OP_BINARY, b"\x03")
    wait_for(lambda: foreground(shell) == "bash", what="Ctrl-C to give the prompt back")
    send(conn, terminal.OP_BINARY, b"echo back-$((6*7))\n")
    output_until(conn, rb"back-42")
    assert hang_up(conn) == (1000, "")


def test_valid_close_codes_get_a_normal_close(connect: Callable[..., Connection]) -> None:
    for code in [1000, 1001, 1003, 1007, 1014, 3000, 4999]:
        conn = connect()
        send(conn, terminal.OP_CLOSE, struct.pack("!H", code) + "au revoir, caf\u00e9".encode())
        assert close_frame(conn) == (1000, ""), code
        assert conn.reader.read() == b""
    conn = connect()
    send(conn, terminal.OP_CLOSE, b"")
    assert close_frame(conn) == (1000, "")


def test_input_gets_one_deadline_per_message_even_if_the_reader_trickles(
    pty_pair: tuple[int, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(terminal, "WRITE_WAIT", 0.5)
    master, slave = pty_pair
    tty.setraw(slave)
    stop = threading.Event()

    def read_steadily() -> None:
        while not stop.wait(0.1):
            if select.select([slave], [], [], 0)[0]:
                os.read(slave, 4096)

    reader = threading.Thread(target=read_steadily)
    reader.start()
    try:
        began = time.monotonic()
        terminal.write_input(master, slave, b"x" * 300_000)
        assert time.monotonic() - began < 1.5
    finally:
        stop.set()
        reader.join()


def test_ctrl_c_counts_as_an_interrupt_only_when_the_terminal_says_so(pty_pair: tuple[int, int]) -> None:
    master, slave = pty_pair
    data = b"pasted\x03more\x03tail"
    assert terminal.last_interrupt(master, data) == 11
    assert terminal.last_interrupt(master, b"no interrupt here") is None
    cooked = termios.tcgetattr(slave)
    for flags in [cooked[3] & ~termios.ISIG, cooked[3] | termios.NOFLSH]:
        termios.tcsetattr(slave, termios.TCSANOW, cooked[:3] + [flags] + cooked[4:])
        assert terminal.last_interrupt(master, data) is None


def test_input_discarded_for_ctrl_c_does_not_count_as_dropped(pty_pair: tuple[int, int]) -> None:
    master, slave = pty_pair
    assert terminal.write_input(master, slave, b"typed ahead\x03") == 0


def test_output_that_is_not_ready_yet_is_not_the_end_of_the_shell(
    pty_pair: tuple[int, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    master, _ = pty_pair
    shell = subprocess.Popen(["sleep", "30"])
    server_end, client_end = socket.socketpair()
    channel = terminal.Channel(server_end, server_end.makefile("wb"))
    # Every poll reports the terminal readable, but there is never anything to read. A real terminal
    # does that only in a short race, which no client can trigger, so this patches select itself.
    monkeypatch.setattr(select, "select", lambda read, write, error, timeout: (read, write, error))
    pump = threading.Thread(target=terminal.forward_output, args=(channel, shell, master))
    pump.start()
    try:
        time.sleep(0.5)
        assert not channel.closed
    finally:
        channel.finished.set()
        pump.join()
        shell.kill()
        shell.wait()
        server_end.close()
        client_end.close()


def test_an_idle_terminal_outlives_the_request_timeout(
    start_site: Callable[..., Site], connect: Callable[..., Connection], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(terminal, "IDLE_TIMEOUT", 5.0)
    settings = dataclasses.replace(SETTINGS, request_timeout=0.5)
    conn = connect(to=start_site(settings=settings))
    send(conn, terminal.OP_BINARY, b"echo shell=$$\n")
    output_until(conn, rb"shell=\d+")
    time.sleep(4 * settings.request_timeout)
    send(conn, terminal.OP_BINARY, b"echo still-$((6*7))\n")
    output_until(conn, rb"still-42")
    assert hang_up(conn) == (1000, "")


def test_dropped_input_is_announced_with_its_size(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"echo shell=$$\n")
    shell = int(output_until(conn, rb"shell=(\d+)").group(1))
    send(conn, terminal.OP_BINARY, b"sleep 2; wc -c; echo counted-$((1+1))\n")
    wait_for(lambda: foreground(shell) == "sleep", what="sleep to take the foreground")

    paste = (b"x" * 99 + b"\n") * 3000
    send(conn, terminal.OP_BINARY, paste)
    dropped = int(output_until(conn, rb"\[testgame: (\d+) bytes of pasted input were dropped").group(1))
    # Once sleep is over, wc counts exactly the bytes the terminal took. They may end in the
    # middle of a line, so a newline goes before the Ctrl-D that ends wc's input; wc counts it too.
    wait_for(lambda: foreground(shell) == "wc", what="wc to start reading")
    send(conn, terminal.OP_BINARY, b"\n\x04")
    taken = int(output_until(conn, rb"(\d+)\r\ncounted-2").group(1)) - 1
    assert 0 < dropped < len(paste)
    assert taken + dropped == len(paste)
    assert hang_up(conn) == (1000, "")


def test_a_paste_the_program_reads_is_not_announced(connect: Callable[..., Connection]) -> None:
    conn = connect()
    send(conn, terminal.OP_BINARY, b"echo shell=$$\n")
    shell = int(output_until(conn, rb"shell=(\d+)").group(1))
    send(conn, terminal.OP_BINARY, b"cat > pasted.txt\n")
    wait_for(lambda: foreground(shell) == "cat", what="cat to take the foreground")

    paste = (b"y" * 99 + b"\n") * 2000
    send(conn, terminal.OP_BINARY, paste)
    send(conn, terminal.OP_BINARY, b"\x04")
    wait_for(lambda: foreground(shell) == "bash", what="cat to finish")
    send(conn, terminal.OP_BINARY, b"wc -c < pasted.txt; echo size-$((1+1))\n")
    match = output_until(conn, rb"(\d+)\r\nsize-2")
    assert int(match.group(1)) == len(paste)
    assert b"[testgame:" not in match.string
    assert hang_up(conn) == (1000, "")


def test_pings_keep_a_live_client_and_silence_drops_it(
    connect: Callable[..., Connection], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(terminal, "PING_INTERVAL", 0.2)
    monkeypatch.setattr(terminal, "IDLE_TIMEOUT", 1.0)

    live = connect()
    pings = 0
    while pings < 10:
        opcode, payload = receive(live)
        if opcode == terminal.OP_PING:
            send(live, terminal.OP_PONG, payload)
            pings += 1
    send(live, terminal.OP_BINARY, b"echo alive-$((6*7))\n")
    output_until(live, rb"alive-42")
    hang_up(live)

    silent = connect()
    send(silent, terminal.OP_BINARY, b"echo shell=$$\n")
    shell = int(output_until(silent, rb"shell=(\d+)").group(1))
    wait_for(lambda: proc_state(shell) is None, timeout=5, what="the silent client's shell to be stopped")


def test_a_shell_that_cannot_start_is_reported(connect: Callable[..., Connection], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/nonexistent")
    conn = connect()
    assert conn.status == 101
    code, reason = close_frame(conn)
    assert code == 1011
    assert reason.startswith("cannot start a shell")


def headers_of(fields: dict[str, str]) -> Message:
    """
    Build request headers as the server's handler sees them.

    Parameters
    ----------
    fields : dict[str, str]
        Header names and values; a value holding commas stands for a repeated header.

    Returns
    -------
    Message
        The headers.
    """
    headers = Message()
    for name, value in fields.items():
        headers[name] = value
    return headers


def test_a_game_that_cannot_prepare_the_shell_gets_close_code_1011(
    connect: Callable[..., Connection], start_site: Callable[..., Site], capsys: pytest.CaptureFixture[str]
) -> None:
    def no_home() -> Path:
        # What Path.home() raises when HOME is unset and the user has no passwd entry.
        raise RuntimeError("Could not determine home directory.")

    def no_environment() -> dict[str, str]:
        raise KeyError("PATH")

    def no_shell() -> list[str]:
        raise LookupError("no shell for this game")

    cases = [(dataclasses.replace(TERMINAL, start_folder=no_home, max_terminals=1), "Could not determine home directory.")]
    cases += [(dataclasses.replace(TERMINAL, environment=no_environment, max_terminals=1), "'PATH'")]
    cases += [(dataclasses.replace(TERMINAL, shell=no_shell, max_terminals=1), "no shell for this game")]
    for failing, error in cases:
        site = start_site(terminal=failing)
        # Twice: the first attempt must free the only slot, or the second would get 1013.
        for _ in range(2):
            conn = connect(to=site)
            assert conn.status == 101
            assert close_frame(conn) == (1011, f"cannot start a shell: {error}")
            with contextlib.suppress(ConnectionResetError):
                conn.reader.read()
    # The page is told, and the error still reaches the server's log, once per attempt.
    assert capsys.readouterr().err.count("Traceback") == 6


def test_close_reasons_are_cut_to_123_bytes_of_whole_characters() -> None:
    server_end, client_end = socket.socketpair()
    with server_end, client_end, server_end.makefile("wb") as writer:
        # 2-byte characters: the 123rd byte would be the first half of one.
        terminal.Channel(server_end, writer).close(1011, "\u00e9" * 100)
        writer.flush()
        first, length = client_end.recv(2)
        reason = client_end.recv(length)[2:]
    assert first == 0x88
    assert reason.decode() == "\u00e9" * 61


def test_a_close_reason_that_is_not_valid_unicode_is_still_sent() -> None:
    server_end, client_end = socket.socketpair()
    with server_end, client_end, server_end.makefile("wb") as writer:
        # A path decoded with surrogateescape can put a lone surrogate into a game's error text.
        terminal.Channel(server_end, writer).close(1011, "bad home \udcff")
        writer.flush()
        first, length = client_end.recv(2)
        reason = client_end.recv(length)[2:]
    assert first == 0x88
    assert reason.decode().startswith("bad home ")


def test_accept_key_matches_the_rfc_example() -> None:
    headers = headers_of({"Upgrade": "websocket", "Connection": "Upgrade", "Sec-WebSocket-Key": KEY, "Sec-WebSocket-Version": "13"})
    assert terminal.handshake_key(headers) == KEY
    assert f"Sec-WebSocket-Accept: {ACCEPT}\r\n".encode() in terminal.accept_response(KEY, "testgame")
    assert b"Sec-WebSocket-Protocol: testgame\r\n" in terminal.accept_response(KEY, "testgame")
    assert len(base64.b64decode(KEY)) == 16


def test_the_offered_key_needs_the_games_protocol_and_exactly_one_key() -> None:
    cases = [
        ("testgame, t.abc", "abc"),
        ("t.abc,testgame", "abc"),
        ("testgame, t.", ""),
        ("other, t.abc", None),
        ("testgame2, t.abc", None),
        ("testgame, t.abc, t.abc", None),
        ("testgame, abc", None),
        ("", None),
    ]
    for offered, key in cases:
        assert terminal.offered_key(headers_of({"Sec-WebSocket-Protocol": offered}), "testgame") == key, offered
    repeated = Message()
    repeated["Sec-WebSocket-Protocol"] = "testgame"
    repeated["Sec-WebSocket-Protocol"] = "t.abc"
    assert terminal.offered_key(repeated, "testgame") == "abc"
    assert terminal.offered_key(repeated, "other") is None


def test_player_env_leaves_out_the_host_terminal_and_the_dropped_names() -> None:
    base = {
        "PATH": "/usr/bin",
        "HOME": "/home/player",
        "PWD": "/srv/elsewhere",
        "TERM": "screen",
        "TMUX": "/tmp/tmux-1000/default,1,0",
        "COLUMNS": "80",
        MARKER: "/home/player/lab",
        "TESTGAME_HOME": "/home/player/.testgame",
    }
    expected = {
        "PATH": "/usr/bin",
        "HOME": "/home/player",
        "PWD": "/home/player",
        "TERM": "xterm-256color",
        "TESTGAME_HOME": "/home/player/.testgame",
    }
    assert terminal.player_env(base, drop={MARKER}) == expected
    assert terminal.player_env(base)[MARKER] == "/home/player/lab"
    assert base["TERM"] == "screen"


def test_player_env_without_a_home_uses_the_users_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for base in [{"PATH": "/usr/bin"}, {"PATH": "/usr/bin", "HOME": ""}]:
        env = terminal.player_env(base)
        assert (env["HOME"], env["PWD"]) == (str(tmp_path), str(tmp_path)), base


def test_a_terminal_starts_in_its_start_folder(
    connect: Callable[..., Connection], start_site: Callable[..., Site], tmp_path: Path
) -> None:
    lab = tmp_path / "lab"
    lab.mkdir()
    site = start_site(terminal=dataclasses.replace(TERMINAL, start_folder=lambda: lab))
    conn = connect(to=site)
    send(conn, terminal.OP_BINARY, b'echo "DIR:$((1+1)):$PWD:$(pwd -P):$HOME:END"\n')
    match = output_until(conn, rb"DIR:2:([^:]*):([^:]*):([^:]*):END")
    assert [group.decode() for group in match.groups()] == [str(lab), str(lab.resolve()), str(tmp_path)]
    hang_up(conn)



def test_a_game_can_choose_the_shell_each_terminal_runs(
    connect: Callable[..., Connection], start_site: Callable[..., Site], tmp_path: Path
) -> None:
    startup = tmp_path / "startup"
    startup.write_text("PS1='chosen-$((6*7))> '\n")
    calls: list[int] = []

    def chosen() -> list[str]:
        calls.append(1)
        return ["bash", "--noprofile", "--rcfile", str(startup), "-i"]

    site = start_site(terminal=dataclasses.replace(TERMINAL, shell=chosen))
    for _ in range(2):
        conn = connect(to=site)
        output_until(conn, rb"chosen-42> ")
        hang_up(conn)
    assert len(calls) == 2

def test_the_number_of_terminals_is_a_setting(
    connect: Callable[..., Connection], start_site: Callable[..., Site]
) -> None:
    site = start_site(terminal=dataclasses.replace(TERMINAL, max_terminals=1))
    first = connect(to=site)
    extra = connect(to=site)
    assert close_frame(extra) == (1013, "too many terminals open (at most 1); close one and try again")
    send(extra, terminal.OP_CLOSE, struct.pack("!H", 1000))
    assert extra.reader.read() == b""
    send(first, terminal.OP_BINARY, b"echo first-$((6*7))\n")
    output_until(first, rb"first-42")
    hang_up(first)


def test_terminal_settings_refuse_a_protocol_a_page_cannot_offer() -> None:
    for protocol in ["", "two words", "a,b", "t.key", "caf\u00e9", "line\r\nbreak"]:
        with pytest.raises(ValueError, match="protocol"):
            dataclasses.replace(TERMINAL, protocol=protocol)


def test_terminal_settings_refuse_a_limit_that_is_not_a_positive_whole_number() -> None:
    # A float limit would make BoundedSemaphore grant every request: 1.5, inf and nan remove the cap.
    limits: list[Any] = [0, -1, 1.5, math.inf, math.nan, True, "3"]
    for limit in limits:
        with pytest.raises(ValueError, match="terminal"):
            dataclasses.replace(TERMINAL, max_terminals=limit)
    assert dataclasses.replace(TERMINAL, max_terminals=1).max_terminals == 1


DATA_OPCODES = [terminal.OP_CONTINUATION, terminal.OP_TEXT, terminal.OP_BINARY]
CONTROL_OPCODES = [terminal.OP_CLOSE, terminal.OP_PING, terminal.OP_PONG]
# Sizes where the frame length changes encoding (7, 16 or 64 bits), and the message limit.
EDGE_SIZES = [0, 125, 126, 127, 65535, 65536, terminal.MAX_MESSAGE]


def sized(size: int, seed: int) -> bytes:
    """
    Make reproducible bytes of a given size.

    Parameters
    ----------
    size : int
        Length.
    seed : int
        Picks the content.

    Returns
    -------
    bytes
        Pseudo-random bytes.
    """
    return random.Random(seed).randbytes(size)


def oracle() -> Any:
    """
    Import the websockets library's sans-I/O frames module, or skip where it is not installed.

    Returns
    -------
    Any
        ``websockets.frames``.
    """
    return pytest.importorskip("websockets.frames")


def oracle_parse(data: bytes, mask: bool) -> Any:
    """
    Parse one complete frame with the websockets library.

    Parameters
    ----------
    data : bytes
        The frame.
    mask : bool
        True to read it as a server reads client frames, False as a client reads server frames.

    Returns
    -------
    Any
        The library's ``Frame``.

    Raises
    ------
    websockets.exceptions.ProtocolError
        For a frame the library refuses; ``PayloadTooBig`` for one over `terminal.MAX_MESSAGE`.
    """
    streams = pytest.importorskip("websockets.streams")
    reader = streams.StreamReader()
    reader.feed_data(data)
    reader.feed_eof()
    parser = oracle().Frame.parse(reader.read_exact, mask=mask, max_size=terminal.MAX_MESSAGE)
    with pytest.raises(StopIteration) as done:
        next(parser)
    return done.value.value


def edge_sizes(test: Callable[..., None]) -> Callable[..., None]:
    """
    Make a property test try every size in `EDGE_SIZES`, whatever it generates.

    Parameters
    ----------
    test : Callable[..., None]
        A property test that takes ``size`` and ``seed``.

    Returns
    -------
    Callable[..., None]
        The test with an explicit example per edge size.
    """
    for size in EDGE_SIZES:
        test = example(size=size, seed=size)(test)
    return test


SIZES = st.sampled_from(EDGE_SIZES) | st.integers(0, terminal.MAX_MESSAGE)


@settings(max_examples=40, deadline=None)
@edge_sizes
@given(size=SIZES, seed=st.integers(0, 2**32 - 1))
def test_server_frames_are_read_by_the_websockets_library_as_sent(size: int, seed: int) -> None:
    payload = sized(size, seed)
    for opcode in [terminal.OP_TEXT, terminal.OP_BINARY, *CONTROL_OPCODES]:
        sent = payload[:125] if opcode in CONTROL_OPCODES else payload
        parsed = oracle_parse(terminal.encode_frame(opcode, sent), mask=False)
        assert (parsed.fin, parsed.opcode, parsed.data) == (True, opcode, sent)


@settings(max_examples=40, deadline=None)
@edge_sizes
@given(size=SIZES, seed=st.integers(0, 2**32 - 1))
def test_client_frames_from_the_websockets_library_are_read_as_sent(size: int, seed: int) -> None:
    frames = oracle()
    payload = sized(size, seed)
    for opcode, fin in [(code, fin) for code in DATA_OPCODES for fin in (True, False)] + [(code, True) for code in CONTROL_OPCODES]:
        sent = payload[:125] if opcode in CONTROL_OPCODES else payload
        raw = frames.Frame(frames.Opcode(opcode), sent, fin).serialize(mask=True)
        assert terminal.read_frame(io.BytesIO(raw)) == (fin, opcode, sent)


def client_header(first: int, masked: bool, length: int) -> bytes:
    """
    Encode a client frame's header with the shortest length encoding, as RFC 6455 requires.

    Parameters
    ----------
    first : int
        FIN, reserved bits and opcode.
    masked : bool
        Whether the mask bit is set; the mask itself is `MASK`.
    length : int
        Payload length.

    Returns
    -------
    bytes
        The header, mask included when `masked`.
    """
    mask_bit = 0x80 if masked else 0
    if length < 126:
        header = struct.pack("!BB", first, mask_bit | length)
    elif length < 1 << 16:
        header = struct.pack("!BBH", first, mask_bit | 126, length)
    else:
        header = struct.pack("!BBQ", first, mask_bit | 127, length)
    return header + (MASK if masked else b"")


@settings(max_examples=400)
@given(first=st.integers(0, 255), masked=st.booleans(), length=st.integers(0, 300), seed=st.integers(0, 2**32 - 1))
def test_frame_headers_are_refused_exactly_when_the_websockets_library_refuses_them(
    first: int, masked: bool, length: int, seed: int
) -> None:
    exceptions = pytest.importorskip("websockets.exceptions")
    raw = client_header(first, masked, length) + sized(length, seed)
    try:
        oracle_parse(raw, mask=True)
        expected = None
    except exceptions.ProtocolError:
        expected = terminal.CLOSE_PROTOCOL_ERROR
    try:
        terminal.read_frame(io.BytesIO(raw))
        refused = None
    except terminal.ProtocolError as error:
        refused = error.code
    assert refused == expected


@settings(max_examples=100, deadline=None)
@example(length=terminal.MAX_MESSAGE, opcode=terminal.OP_BINARY)
@example(length=terminal.MAX_MESSAGE + 1, opcode=terminal.OP_BINARY)
@example(length=2**64 - 1, opcode=terminal.OP_CONTINUATION)
@given(
    length=st.integers(terminal.MAX_MESSAGE - 2, terminal.MAX_MESSAGE + 2) | st.integers(126, 4 * terminal.MAX_MESSAGE) | st.integers(126, 2**64 - 1),
    opcode=st.sampled_from(DATA_OPCODES),
)
def test_frames_over_the_limit_are_refused_before_their_payload_as_the_websockets_library_does(length: int, opcode: int) -> None:
    exceptions = pytest.importorskip("websockets.exceptions")
    # Only the header is sent: a parser that waited for the payload would reach the end of the data.
    header = client_header(0x80 | opcode, True, length)
    with pytest.raises((exceptions.PayloadTooBig, EOFError)) as theirs:
        oracle_parse(header, mask=True)
    with pytest.raises((terminal.ProtocolError, EOFError)) as ours:
        terminal.read_frame(io.BytesIO(header))
    too_big = length > terminal.MAX_MESSAGE
    refusal = ours.value.code if isinstance(ours.value, terminal.ProtocolError) else None
    assert isinstance(theirs.value, exceptions.PayloadTooBig) == too_big
    assert refusal == (terminal.CLOSE_TOO_BIG if too_big else None)


@settings(max_examples=300)
@given(
    payload=st.binary(max_size=3)
    | st.builds(
        lambda code, reason: struct.pack("!H", code) + reason,
        st.integers(0, 65535) | st.sampled_from([999, 1000, 1003, 1004, 1006, 1007, 1014, 1015, 2999, 3000, 4999, 5000]),
        st.text(max_size=40).map(str.encode) | st.binary(max_size=40),
    )
)
def test_close_payloads_are_accepted_exactly_when_the_websockets_library_accepts_them(payload: bytes) -> None:
    exceptions = pytest.importorskip("websockets.exceptions")
    try:
        oracle().Close.parse(payload)
        accepted = True
    except (exceptions.ProtocolError, UnicodeDecodeError):
        accepted = False
    try:
        terminal.check_close(payload)
        valid = True
    except terminal.ProtocolError:
        valid = False
    assert valid == accepted


@settings(max_examples=100, deadline=None)
@given(
    parts=st.lists(
        st.tuples(st.just(terminal.OP_TEXT), st.text(max_size=300).map(str.encode), st.integers(1, 4))
        | st.tuples(st.just(terminal.OP_BINARY), st.binary(max_size=300), st.integers(1, 4)),
        max_size=5,
    ),
    data=st.data(),
)
def test_fragmented_messages_are_reassembled_around_the_pings_between_their_frames(
    parts: list[tuple[int, bytes, int]], data: st.DataObject
) -> None:
    frames = oracle()
    stream = b""
    expected: list[tuple[int, bytes]] = []
    for opcode, message, pieces in parts:
        # Cuts may fall inside a UTF-8 character: only the whole text message must be UTF-8.
        cuts = sorted(data.draw(st.lists(st.integers(0, len(message)), min_size=pieces - 1, max_size=pieces - 1)))
        fragments = [message[start:end] for start, end in zip([0, *cuts], [*cuts, len(message)], strict=True)]
        for index, fragment in enumerate(fragments):
            first = frames.Opcode(opcode if index == 0 else terminal.OP_CONTINUATION)
            stream += frames.Frame(first, fragment, index == len(fragments) - 1).serialize(mask=True)
            if index < len(fragments) - 1:
                stream += frames.Frame(frames.Opcode.PING, b"%d" % index).serialize(mask=True)
                expected.append((terminal.OP_PING, b"%d" % index))
        expected.append((opcode, message))
    assert list(terminal.messages(io.BytesIO(stream))) == expected
