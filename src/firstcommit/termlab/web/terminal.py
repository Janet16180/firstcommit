"""
Embedded terminal: a WebSocket (RFC 6455) bridged to the player's shell on a pseudo-terminal.

Protocol
--------
Endpoint: ``GET /api/terminal`` upgraded to a WebSocket (see `firstcommit.termlab.web.shell`).
A page cannot add headers to a WebSocket request, so it passes the access
token as a second subprotocol, next to the game's own (`TerminalSettings`)::

    new WebSocket("ws://" + location.host + "/api/terminal", [protocol, "t." + token])

The server requires the game's protocol and exactly one ``t.`` entry (the
token compared in constant time) and answers ``Sec-WebSocket-Protocol:
<protocol>``. The ``Origin`` header is mandatory and must name this server
(``http://localhost:PORT`` or ``http://127.0.0.1:PORT``); browsers always send
it. A refused upgrade gets a plain HTTP 403 (or 400 for a malformed
handshake), which browsers report as an ``error`` followed by ``close`` code
1006.

Each connection gets its own interactive shell (the command the game's settings
name, else ``$SHELL``, else ``/bin/bash``) with the environment and in the folder
the game's settings give, on an 80x24 terminal.

- Binary frames carry raw bytes both ways: keystrokes in, terminal output out.
  Output chunks may split a UTF-8 character; xterm.js's ``write(Uint8Array)``
  copes with that. Set ``socket.binaryType = "arraybuffer"`` and send input as
  ``new TextEncoder().encode(data)``.
- Text frames carry JSON control messages. The only one is
  ``{"type": "resize", "cols": N, "rows": M}`` with whole numbers from 1 to
  1000. Anything else in a text frame is ignored.
- Ping is answered with pong. Fragmented messages are accepted; a message may
  be at most 1 MiB.
- Input the foreground program does not read within a second (a huge paste
  into ``sleep``) is dropped, so the connection always stays responsive; the
  server then prints a yellow ``[<notice prefix>: N bytes of pasted input
  were dropped ...]`` line in the terminal output. A Ctrl-C still gets through:
  the queued input is discarded first (silently), as the kernel itself does
  when it reads a Ctrl-C.
- The server pings every 15 seconds (browsers answer by themselves) and drops
  a connection it has heard nothing from for 45 seconds.

Close codes sent by the server:

- 1000 "the shell exited": the player typed ``exit`` (or the shell died).
- 1013 "too many terminals open ...": at most ``max_terminals`` at once per server.
- 1002 / 1007 / 1009: the client broke the protocol (an invalid close code
  included) / sent text, or a close reason, that is not UTF-8 / sent a
  message over 1 MiB.
- 1011 "cannot start a shell: ...": the shell could not be started.

When the connection closes for any reason, the shell's process group gets
SIGHUP; an interactive shell passes it on to its jobs. After `GRACE` seconds
the shell's process group (not its jobs, which have their own) gets SIGKILL,
and the shell is reaped. As in a real terminal, a job that ignores SIGHUP
(``nohup``) keeps running.
"""

import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
import select
import signal
import socket
import struct
import subprocess
import termios
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from email.message import Message
from io import BufferedIOBase, BufferedReader, RawIOBase
from pathlib import Path
from typing import Any

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TOKEN_PREFIX = "t."
# An HTTP token (RFC 9110, section 5.6.2): what a subprotocol name may be.
HTTP_TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+")
MAX_MESSAGE = 1 << 20
MAX_CONTROL = 256
MAX_SIZE = 1000
DEFAULT_SIZE = (80, 24)
GRACE = 1.0
CLOSE_TIMEOUT = 2.0
POLL_INTERVAL = 0.1
WRITE_WAIT = 1.0
PING_INTERVAL = 15.0
IDLE_TIMEOUT = 45.0
READ_SIZE = 65536
DROPPED_NOTICE = "\r\n\x1b[33m[{}: {} bytes of pasted input were dropped: the program was not reading them]\x1b[0m\r\n"

OP_CONTINUATION, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA
OPCODES = {OP_CONTINUATION, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG}

CLOSE_NORMAL = 1000
CLOSE_PROTOCOL_ERROR = 1002
CLOSE_INVALID_DATA = 1007
CLOSE_TOO_BIG = 1009
CLOSE_INTERNAL_ERROR = 1011
CLOSE_TRY_AGAIN_LATER = 1013

# Variables describing the terminal the server runs in, wrong inside the page's terminal.
HOST_TERMINAL = {
    "COLUMNS",
    "LINES",
    "OLDPWD",
    "STY",
    "TERM_PROGRAM",
    "TERM_PROGRAM_VERSION",
    "TERM_SESSION_ID",
    "TMUX",
    "TMUX_PANE",
    "VTE_VERSION",
    "WINDOW",
    "WINDOWID",
    "WT_PROFILE_ID",
    "WT_SESSION",
}


@dataclass(frozen=True)
class TerminalSettings:
    """
    A game's choices for the page's terminal.

    The environment, the start folder and the shell's command are built again
    for each new terminal, so they follow the server's environment and the
    game's state.

    Attributes
    ----------
    protocol : str
        The WebSocket subprotocol the page offers next to its ``t.<token>``
        entry and the server selects, e.g. the game's name. An HTTP token
        that does not start with ``t.``.
    notice_prefix : str
        Name at the start of the notices the server prints into the
        terminal, as in ``[name: 12 bytes of pasted input were dropped ...]``.
    environment : Callable[[], Mapping[str, str]]
        Builds a new shell's environment, usually with `player_env`.
    start_folder : Callable[[], Path]
        Gives the folder a new shell starts in, e.g. ``Path.home``.
    max_terminals : int
        Terminals open at once per server; a whole number, at least 1.
        Another one is accepted and closed at once with code 1013.
    shell : Callable[[], Sequence[str]] | None
        Gives the command a new terminal runs, program and arguments, such as
        ``["bash", "--noprofile", "--rcfile", startup_file, "-i"]``: an
        interactive shell, found on the environment's ``PATH``. None runs
        ``$SHELL -i`` (`shell_path`).

    Raises
    ------
    ValueError
        If the protocol is not a name the page can offer, or the limit is not
        a whole number of at least 1.
    """

    protocol: str
    notice_prefix: str
    environment: Callable[[], Mapping[str, str]]
    start_folder: Callable[[], Path]
    max_terminals: int = 3
    shell: Callable[[], Sequence[str]] | None = None

    def __post_init__(self) -> None:
        """Check the settings once, when the game makes them."""
        if not HTTP_TOKEN.fullmatch(self.protocol) or self.protocol.startswith(TOKEN_PREFIX):
            raise ValueError(f"the terminal protocol must be an HTTP token not starting with {TOKEN_PREFIX!r}: {self.protocol!r}")
        if type(self.max_terminals) is not int or self.max_terminals < 1:
            raise ValueError(f"allow at least one terminal, as a whole number, not {self.max_terminals!r}")


class ProtocolError(Exception):
    """A client frame that breaks RFC 6455 (or our limits); ends the connection."""

    def __init__(self, code: int, reason: str) -> None:
        """
        Remember how to close the connection.

        Parameters
        ----------
        code : int
            Close code to send.
        reason : str
            Close reason to send.
        """
        super().__init__(reason)
        self.code = code
        self.reason = reason


class DeadlineReader(RawIOBase):
    """
    The reading side of a socket, where all reads together must end by a deadline.

    A client that sends a byte now and then stretches a per-read timeout without
    end; here each read waits only for the time left. Wrap it in
    ``io.BufferedReader`` to read lines and frames.
    """

    def __init__(self, connection: socket.socket, deadline: float | None) -> None:
        """
        Read from a socket.

        Parameters
        ----------
        connection : socket.socket
            The client's socket; its own timeout is restored after each read.
        deadline : float | None
            The `time.monotonic` value by which reading must be done; None, or
            setting the attribute to None later, lifts the limit.
        """
        super().__init__()
        self.connection = connection
        self.deadline = deadline

    def readable(self) -> bool:
        """
        Tell the io module that this stream can be read.

        Returns
        -------
        bool
            True.
        """
        return True

    def readinto(self, buffer: Any) -> int:
        """
        Receive what the client sent, waiting no later than the deadline.

        Parameters
        ----------
        buffer : Any
            Writable buffer to fill.

        Returns
        -------
        int
            Bytes received; 0 when the client closed the connection.

        Raises
        ------
        TimeoutError
            If the deadline passed, or passes while waiting.
        """
        timeout = self.connection.gettimeout()
        if self.deadline is not None:
            left = self.deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError("the client took too long to send its data")
            self.connection.settimeout(left)
        try:
            received = self.connection.recv_into(buffer)
        finally:
            self.connection.settimeout(timeout)
        return received


class Channel:
    """The server's sending half of a WebSocket, shared by the input and output threads."""

    def __init__(self, connection: socket.socket, wfile: BufferedIOBase) -> None:
        """
        Wrap a connection whose handshake is done.

        Parameters
        ----------
        connection : socket.socket
            The client's socket.
        wfile : BufferedIOBase
            Unbuffered writer on that socket.
        """
        self.connection = connection
        self.wfile = wfile
        self.lock = threading.Lock()
        self.closed = False
        self.finished = threading.Event()

    def send(self, opcode: int, payload: bytes) -> None:
        """
        Send one frame, unless a close frame was already sent or the connection broke.

        Parameters
        ----------
        opcode : int
            Frame type.
        payload : bytes
            Frame payload.
        """
        with self.lock:
            if self.closed:
                return
            self.closed = opcode == OP_CLOSE
            try:
                self.wfile.write(encode_frame(opcode, payload))
            except OSError:
                self.closed = True

    def close(self, code: int, reason: str) -> None:
        """
        Start the closing handshake.

        Parameters
        ----------
        code : int
            Close code.
        reason : str
            Short explanation, shown to the page; cut to the whole characters
            that fit in 123 bytes of UTF-8. Characters UTF-8 cannot encode (lone
            surrogates) become "?".
        """
        encoded = reason.encode(errors="replace")[:123]
        self.send(OP_CLOSE, struct.pack("!H", code) + encoded.decode(errors="ignore").encode())


def handshake_key(headers: Message) -> str | None:
    """
    Validate a WebSocket upgrade request.

    Parameters
    ----------
    headers : Message
        Request headers.

    Returns
    -------
    str | None
        The ``Sec-WebSocket-Key``, or None if this is not a valid version 13 upgrade.
    """
    upgrade = {token.strip().lower() for token in headers.get("Upgrade", "").split(",")}
    connection = {token.strip().lower() for token in headers.get("Connection", "").split(",")}
    key = headers.get("Sec-WebSocket-Key", "")
    try:
        nonce = base64.b64decode(key, validate=True)
    except ValueError:
        nonce = b""
    valid = "websocket" in upgrade and "upgrade" in connection and headers.get("Sec-WebSocket-Version") == "13"
    return key if valid and len(nonce) == 16 else None


def offered_key(headers: Message, protocol: str) -> str | None:
    """
    Find the access key a client sent as a subprotocol next to the game's one.

    Parameters
    ----------
    headers : Message
        Request headers; ``Sec-WebSocket-Protocol`` may be repeated.
    protocol : str
        The game's subprotocol.

    Returns
    -------
    str | None
        The value of the ``t.<key>`` entry; None unless `protocol` and exactly
        one such entry are offered, so a client cannot try several keys at once.
    """
    offered = [name.strip() for value in headers.get_all("Sec-WebSocket-Protocol", []) for name in value.split(",")]
    keys = [name.removeprefix(TOKEN_PREFIX) for name in offered if name.startswith(TOKEN_PREFIX)]
    return keys[0] if protocol in offered and len(keys) == 1 else None


def accept_response(key: str, protocol: str) -> bytes:
    """
    Build the response that completes the handshake and selects the game's subprotocol.

    Parameters
    ----------
    key : str
        The client's ``Sec-WebSocket-Key``.
    protocol : str
        The game's subprotocol.

    Returns
    -------
    bytes
        The ``101 Switching Protocols`` response.
    """
    accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        f"Sec-WebSocket-Protocol: {protocol}\r\n\r\n"
    ).encode()


def encode_frame(opcode: int, payload: bytes) -> bytes:
    """
    Encode a complete, unmasked server frame.

    Parameters
    ----------
    opcode : int
        Frame type.
    payload : bytes
        Frame payload.

    Returns
    -------
    bytes
        The frame.
    """
    length = len(payload)
    if length < 126:
        header = struct.pack("!BB", 0x80 | opcode, length)
    elif length < 1 << 16:
        header = struct.pack("!BBH", 0x80 | opcode, 126, length)
    else:
        header = struct.pack("!BBQ", 0x80 | opcode, 127, length)
    return header + payload


def read_exactly(rfile: BufferedIOBase, size: int) -> bytes:
    """
    Read a fixed number of bytes from the client.

    Parameters
    ----------
    rfile : BufferedIOBase
        Buffered reader on the socket.
    size : int
        Bytes to read.

    Returns
    -------
    bytes
        Exactly `size` bytes.

    Raises
    ------
    EOFError
        If the connection ends first.
    """
    data = rfile.read(size)
    if len(data) < size:
        raise EOFError("the connection closed in the middle of a frame")
    return data


def read_frame(rfile: BufferedIOBase) -> tuple[bool, int, bytes]:
    """
    Read and unmask one client frame.

    Parameters
    ----------
    rfile : BufferedIOBase
        Buffered reader on the socket.

    Returns
    -------
    tuple[bool, int, bytes]
        FIN bit, opcode and payload.

    Raises
    ------
    ProtocolError
        For unmasked frames, reserved bits or opcodes, bad control frames and oversized frames.
    EOFError
        If the connection ends.
    """
    first, second = read_exactly(rfile, 2)
    fin = bool(first & 0x80)
    opcode = first & 0x0F
    length = second & 0x7F
    if first & 0x70 or opcode not in OPCODES:
        raise ProtocolError(CLOSE_PROTOCOL_ERROR, "reserved bits or opcode")
    if not second & 0x80:
        raise ProtocolError(CLOSE_PROTOCOL_ERROR, "client frames must be masked")
    if opcode >= OP_CLOSE and (length > 125 or not fin):
        raise ProtocolError(CLOSE_PROTOCOL_ERROR, "control frames must be short and unfragmented")
    if length == 126:
        (length,) = struct.unpack("!H", read_exactly(rfile, 2))
    elif length == 127:
        (length,) = struct.unpack("!Q", read_exactly(rfile, 8))
    if length > MAX_MESSAGE:
        raise ProtocolError(CLOSE_TOO_BIG, f"messages are limited to {MAX_MESSAGE} bytes")
    mask = read_exactly(rfile, 4)
    payload = read_exactly(rfile, length)
    # XOR with the 4-byte mask repeated over the payload, as one big integer operation.
    repeated = (mask * (length // 4 + 1))[:length]
    unmasked = (int.from_bytes(payload, "big") ^ int.from_bytes(repeated, "big")).to_bytes(length, "big")
    return fin, opcode, unmasked


def messages(rfile: BufferedIOBase) -> Iterator[tuple[int, bytes]]:
    """
    Read the client's messages, reassembling fragmented ones.

    Control frames, which may arrive between the fragments of a message, are
    yielded as soon as they arrive. Iteration ends when the connection does.

    Parameters
    ----------
    rfile : BufferedIOBase
        Buffered reader on the socket.

    Yields
    ------
    tuple[int, bytes]
        Opcode and payload of each control frame and complete data message.

    Raises
    ------
    ProtocolError
        For bad frames, misplaced continuation frames, oversized messages and
        text messages that are not UTF-8.
    """
    message_opcode = None
    parts: list[bytes] = []
    size = 0
    while True:
        try:
            fin, opcode, payload = read_frame(rfile)
        except (EOFError, OSError):
            return
        if opcode == OP_CLOSE:
            check_close(payload)
        if opcode >= OP_CLOSE:
            yield opcode, payload
            continue
        if opcode == OP_CONTINUATION and message_opcode is None:
            raise ProtocolError(CLOSE_PROTOCOL_ERROR, "continuation frame without a message to continue")
        if opcode != OP_CONTINUATION and message_opcode is not None:
            raise ProtocolError(CLOSE_PROTOCOL_ERROR, "new message before the previous one ended")
        if message_opcode is None:
            message_opcode = opcode
        size += len(payload)
        if size > MAX_MESSAGE:
            raise ProtocolError(CLOSE_TOO_BIG, f"messages are limited to {MAX_MESSAGE} bytes")
        parts.append(payload)
        if not fin:
            continue
        message = b"".join(parts)
        if message_opcode == OP_TEXT and not is_utf8(message):
            raise ProtocolError(CLOSE_INVALID_DATA, "text messages must be UTF-8")
        yield message_opcode, message
        message_opcode, parts, size = None, [], 0


def check_close(payload: bytes) -> None:
    """
    Validate a close frame's payload: empty, or a status code (RFC 6455, section 7.4) and a UTF-8 reason.

    Parameters
    ----------
    payload : bytes
        Payload of the client's close frame.

    Raises
    ------
    ProtocolError
        1002 for a 1-byte payload or a code that may not be sent, 1007 for a reason that is not UTF-8.
    """
    if not payload:
        return
    if len(payload) == 1:
        raise ProtocolError(CLOSE_PROTOCOL_ERROR, "a close payload starts with a 2-byte code")
    (code,) = struct.unpack("!H", payload[:2])
    if not (1000 <= code <= 1003 or 1007 <= code <= 1014 or 3000 <= code <= 4999):
        raise ProtocolError(CLOSE_PROTOCOL_ERROR, f"invalid close code {code}")
    if not is_utf8(payload[2:]):
        raise ProtocolError(CLOSE_INVALID_DATA, "close reasons must be UTF-8")


def is_utf8(data: bytes) -> bool:
    """
    Tell whether bytes are valid UTF-8.

    Parameters
    ----------
    data : bytes
        Bytes to check.

    Returns
    -------
    bool
        True if they decode.
    """
    valid = True
    try:
        data.decode()
    except UnicodeDecodeError:
        valid = False
    return valid


def resize(master: int, cols: int, rows: int) -> None:
    """
    Set the terminal size; the kernel sends SIGWINCH to the foreground job.

    Parameters
    ----------
    master : int
        Master side of the pseudo-terminal.
    cols : int
        Columns.
    rows : int
        Rows.
    """
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def apply_control(master: int, payload: bytes) -> None:
    """
    Apply a JSON control message from a text frame; anything else is ignored.

    Parameters
    ----------
    master : int
        Master side of the pseudo-terminal.
    payload : bytes
        Text frame payload.
    """
    if len(payload) > MAX_CONTROL:
        return
    try:
        message = json.loads(payload)
    except ValueError:
        return
    if not isinstance(message, dict) or message.get("type") != "resize":
        return
    cols, rows = message.get("cols"), message.get("rows")
    if type(cols) is not int or type(rows) is not int or not (1 <= cols <= MAX_SIZE and 1 <= rows <= MAX_SIZE):
        return
    resize(master, cols, rows)


def last_interrupt(master: int, data: bytes) -> int | None:
    """
    Find the last interrupt character (Ctrl-C) in some input, if the terminal turns it into SIGINT.

    Parameters
    ----------
    master : int
        Master side of the pseudo-terminal; its attributes are the terminal's.
    data : bytes
        Input about to be written.

    Returns
    -------
    int | None
        Position of the last interrupt character. None if there is none, if
        the foreground program reads Ctrl-C as a plain byte (ISIG off, as in
        an editor), or if it asked the kernel not to discard input on
        interrupts (NOFLSH).
    """
    attributes = termios.tcgetattr(master)
    lflag, interrupt = attributes[3], attributes[6][termios.VINTR]
    index = data.rfind(interrupt)
    enabled = bool(lflag & termios.ISIG) and not lflag & termios.NOFLSH and interrupt != b"\0"
    return index if enabled and index >= 0 else None


def write_input(master: int, slave: int, data: bytes) -> int:
    """
    Type bytes into the terminal.

    The terminal holds little unread input. What the foreground program has
    not taken within `WRITE_WAIT` seconds of the message arriving is dropped,
    so that a big paste into a program that reads slowly or not at all can
    never keep the server from reading the connection for long.

    On reading a Ctrl-C, the kernel discards the queued input and signals the
    foreground job, but it cannot read a Ctrl-C stuck behind a full queue. So
    the queue (and the input before the Ctrl-C) is discarded here first.

    Parameters
    ----------
    master : int
        Master side of the pseudo-terminal, in non-blocking mode.
    slave : int
        Slave side, to discard the queued input.
    data : bytes
        Keystrokes or pasted text.

    Returns
    -------
    int
        Bytes dropped because the program did not take them in time; input
        discarded for a Ctrl-C does not count, the kernel discards it too.
    """
    interrupt = last_interrupt(master, data)
    if interrupt is not None:
        termios.tcflush(slave, termios.TCIFLUSH)
    view = memoryview(data)[interrupt or 0:]
    deadline = time.monotonic() + WRITE_WAIT
    while view and time.monotonic() < deadline:
        try:
            view = view[os.write(master, view):]
        except BlockingIOError:
            select.select([], [master], [], max(0.0, deadline - time.monotonic()))
    return len(view)


def read_output(master: int) -> bytes:
    """
    Read what the terminal printed.

    Parameters
    ----------
    master : int
        Master side of the pseudo-terminal, in non-blocking mode.

    Returns
    -------
    bytes
        Output; empty if there is none right now. The server keeps the slave
        side open, so this never reports end of file: the shell's exit does.
    """
    try:
        output = os.read(master, READ_SIZE)
    except BlockingIOError:
        output = b""
    return output


def player_env(base: Mapping[str, str], drop: Iterable[str] = ()) -> dict[str, str]:
    """
    Build a shell's environment from the server's, as a new terminal window would have it.

    Variables that describe the server's own terminal are left out, and so
    are the `drop` names: a game drops, for example, the marker it uses to
    find and stop its lab's processes, so that cleanup never kills the
    player's shell. Everything else stays, such as a game's home variable,
    so the game's commands typed in the terminal use the same save.

    Parameters
    ----------
    base : Mapping[str, str]
        Usually ``os.environ``; it is not changed.
    drop : Iterable[str]
        Names to leave out as well.

    Returns
    -------
    dict[str, str]
        The environment, with ``HOME`` (the user's home if `base` has none),
        ``PWD`` naming it and ``TERM=xterm-256color``.
    """
    left_out = HOST_TERMINAL | set(drop)
    home = base.get("HOME") or os.path.expanduser("~")
    env = {key: value for key, value in base.items() if key not in left_out}
    env.update({"HOME": home, "PWD": home, "TERM": "xterm-256color"})
    return env


def shell_path(env: Mapping[str, str]) -> str:
    """
    Choose the shell to run.

    Parameters
    ----------
    env : Mapping[str, str]
        The shell's environment.

    Returns
    -------
    str
        ``$SHELL`` if it is an absolute path to an executable, otherwise ``/bin/bash``.
    """
    shell = env.get("SHELL", "")
    return shell if os.path.isabs(shell) and os.access(shell, os.X_OK) else "/bin/bash"


def start_shell(command: Sequence[str], env: Mapping[str, str], cwd: Path) -> tuple[subprocess.Popen[bytes], int, int]:
    """
    Start an interactive shell on a new pseudo-terminal.

    Parameters
    ----------
    command : Sequence[str]
        The shell's program and arguments, such as ``["/bin/bash", "-i"]``.
    env : Mapping[str, str]
        The shell's environment; its ``PATH`` also finds ``setsid``.
    cwd : Path
        The folder it starts in; ``PWD`` is set to name it.

    Returns
    -------
    tuple[subprocess.Popen[bytes], int, int]
        The shell process, the master side of its terminal (in non-blocking
        mode) and the slave side, which the server keeps open to flush it.

    Raises
    ------
    OSError
        If the terminal or the shell cannot be created.
    """
    master, slave = os.openpty()
    os.set_blocking(master, False)
    resize(master, *DEFAULT_SIZE)
    try:
        # setsid --ctty: a new session whose controlling terminal is the pty, which job control needs.
        # It runs in the child, so no Python code runs between fork and exec in this threaded server.
        proc = subprocess.Popen(
            ["setsid", "--ctty", *command],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=cwd,
            env={**env, "PWD": str(cwd)},
        )
    except OSError:
        os.close(master)
        os.close(slave)
        raise
    return proc, master, slave


def signal_group(proc: subprocess.Popen[bytes], signum: int) -> None:
    """
    Signal the shell's process group, while the shell is unreaped and its pid cannot be reused.

    Parameters
    ----------
    proc : subprocess.Popen[bytes]
        The shell, leader of its own session and process group.
    signum : int
        Signal to send.
    """
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signum)
        except ProcessLookupError:
            # No such group yet: the connection ended before setsid ran in the child.
            proc.send_signal(signum)


def stop_shell(proc: subprocess.Popen[bytes]) -> None:
    """
    Hang up the shell, kill it if it lingers, and reap it.

    Parameters
    ----------
    proc : subprocess.Popen[bytes]
        The shell.
    """
    signal_group(proc, signal.SIGHUP)
    try:
        proc.wait(timeout=GRACE)
    except subprocess.TimeoutExpired:
        signal_group(proc, signal.SIGKILL)
        proc.kill()
        proc.wait()


def forward_input(channel: Channel, rfile: BufferedIOBase, master: int, slave: int, notice_prefix: str) -> None:
    """
    Apply the client's messages to the terminal until the client closes or the connection drops.

    When input has to be dropped, a yellow line in the terminal says how much.

    Parameters
    ----------
    channel : Channel
        The connection.
    rfile : BufferedIOBase
        Buffered reader on the socket.
    master : int
        Master side of the pseudo-terminal.
    slave : int
        Slave side of the pseudo-terminal.
    notice_prefix : str
        Name at the start of that line.
    """
    try:
        for opcode, payload in messages(rfile):
            if opcode == OP_CLOSE:
                channel.close(CLOSE_NORMAL, "")
                return
            if opcode == OP_PING:
                channel.send(OP_PONG, payload)
            elif opcode == OP_BINARY:
                dropped = write_input(master, slave, payload)
                if dropped:
                    channel.send(OP_BINARY, DROPPED_NOTICE.format(notice_prefix, dropped).encode())
            elif opcode == OP_TEXT:
                apply_control(master, payload)
    except ProtocolError as error:
        channel.close(error.code, error.reason)


def send_ready_output(channel: Channel, master: int) -> None:
    """
    Wait briefly for terminal output and send what there is.

    Parameters
    ----------
    channel : Channel
        The connection.
    master : int
        Master side of the pseudo-terminal.
    """
    ready, _, _ = select.select([master], [], [], POLL_INTERVAL)
    data = read_output(master) if ready else b""
    if data:
        channel.send(OP_BINARY, data)


def forward_output(channel: Channel, proc: subprocess.Popen[bytes], master: int) -> None:
    """
    Send the terminal's output and regular pings to the client; close the connection when the shell exits.

    Parameters
    ----------
    channel : Channel
        The connection.
    proc : subprocess.Popen[bytes]
        The shell.
    master : int
        Master side of the pseudo-terminal.
    """
    next_ping = time.monotonic() + PING_INTERVAL
    while proc.poll() is None and not channel.finished.is_set():
        send_ready_output(channel, master)
        if time.monotonic() >= next_ping:
            channel.send(OP_PING, b"")
            next_ping = time.monotonic() + PING_INTERVAL
    if channel.finished.is_set():
        return
    # Like a terminal window, close when the shell exits, even if a job it left behind keeps printing.
    send_ready_output(channel, master)
    channel.close(CLOSE_NORMAL, "the shell exited")
    if not channel.finished.wait(CLOSE_TIMEOUT):
        # The client did not answer the close frame: wake the reader blocked on the socket.
        with contextlib.suppress(OSError):
            channel.connection.shutdown(socket.SHUT_RDWR)


def run(connection: socket.socket, rfile: BufferedIOBase, wfile: BufferedIOBase, settings: TerminalSettings) -> None:
    """
    Bridge an accepted WebSocket to a new shell until either side goes away.

    Parameters
    ----------
    connection : socket.socket
        The client's socket, handshake done.
    rfile : BufferedIOBase
        Buffered reader on the socket.
    wfile : BufferedIOBase
        Unbuffered writer on the socket.
    settings : TerminalSettings
        The shell's environment, start folder and command, built now, and the notice prefix.

    Raises
    ------
    Exception
        Whatever the game's ``environment``, ``start_folder`` or ``shell``
        raised, other than OSError, after the page got close code 1011.
    """
    channel = Channel(connection, wfile)
    # Reads time out when the client has been silent through several pings: a half-open connection.
    connection.settimeout(IDLE_TIMEOUT)
    try:
        env = settings.environment()
        command = settings.shell() if settings.shell is not None else [shell_path(env), "-i"]
        proc, master, slave = start_shell(command, env, settings.start_folder())
    except OSError as error:
        channel.close(CLOSE_INTERNAL_ERROR, f"cannot start a shell: {error.strerror}")
        return
    except Exception as error:
        # The game's environment or start folder failed: tell the page, which then stops retrying,
        # and let the server log the error.
        channel.close(CLOSE_INTERNAL_ERROR, f"cannot start a shell: {error}")
        raise
    pump = threading.Thread(target=forward_output, args=(channel, proc, master), daemon=True)
    pump.start()
    try:
        forward_input(channel, rfile, master, slave, settings.notice_prefix)
    finally:
        channel.finished.set()
        stop_shell(proc)
        pump.join()
        os.close(master)
        os.close(slave)


def turn_away(connection: socket.socket, wfile: BufferedIOBase, limit: int) -> None:
    """
    Close an accepted WebSocket at once because too many terminals are open.

    The client gets `CLOSE_TIMEOUT` seconds in all to answer the close frame,
    however often it sends something else. The socket is read afresh: a client
    sends nothing before it gets the handshake's answer.

    Parameters
    ----------
    connection : socket.socket
        The client's socket, handshake done.
    wfile : BufferedIOBase
        Unbuffered writer on the socket.
    limit : int
        How many terminals may be open, for the close reason.
    """
    Channel(connection, wfile).close(
        CLOSE_TRY_AGAIN_LATER, f"too many terminals open (at most {limit}); close one and try again"
    )
    reader = BufferedReader(DeadlineReader(connection, time.monotonic() + CLOSE_TIMEOUT))
    with reader, contextlib.suppress(ProtocolError):
        for opcode, _ in messages(reader):
            if opcode == OP_CLOSE:
                return
