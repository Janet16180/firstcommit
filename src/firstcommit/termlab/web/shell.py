"""
A secure local web server for a game's page: its files, its JSON routes and the in-page terminal.

The server listens on 127.0.0.1 only. The page and its static files are
public: they hold no secrets. Every ``/api/*`` request must carry a random
token in the game's token header. The link printed at startup hands the
token to the page in its fragment (``/#token=...``), which browsers never send
to a server. There is no cookie on purpose: cookies ignore ports, so one would
also be sent to every other service on localhost.

Requests whose Host header is not localhost are refused (DNS rebinding), and
POSTs from another origin too. The terminal's WebSocket (see
`firstcommit.termlab.web.terminal`) carries the token as a subprotocol, since a page cannot
add headers to it, and must name this server in its Origin header.

The game brings its routes as a table ``{(method, path): route}``: ``GET``
routes get the query (the first value of each name), ``POST`` routes the JSON
body (an empty dict if it is missing, oversized, not JSON or not an object),
and each returns a status and a JSON-serializable dict.
"""

import errno
import hmac
import json
import math
import os
import re
import secrets
import socket
import socketserver
import sys
import threading
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BufferedReader
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import parse_qs, urlsplit

from . import terminal

Route = Callable[[dict[str, Any]], tuple[HTTPStatus, dict[str, Any]]]

SHARED_STATIC = Path(__file__).parent / "static"
TERMINAL_PATH = "/api/terminal"
LOCAL_HOSTS = {"localhost", "127.0.0.1"}
METHODS = {"GET", "POST"}
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
}
# A Content-Length the server reads: 1 to 10 ASCII digits. str.isdigit() lets "²" through, which
# int() rejects, and int() refuses more than 4300 digits.
LENGTH = re.compile(r"[0-9]{1,10}")
# One source in a Content-Security-Policy directive: visible ASCII (0x21-0x7E) without "," and ";",
# which would end the source list or the directive.
CSP_SOURCE = re.compile(r"[\x21-\x2b\x2d-\x3a\x3c-\x7e]+")
# A path a terminal can have: under /api/, with no query, fragment or other character a request
# line would change.
TERMINAL_PATHS = re.compile(r"/api/[A-Za-z0-9/_-]+")


@dataclass(frozen=True)
class ShellSettings:
    """
    A game's choices for its web server.

    Attributes
    ----------
    name : str
        The game's name, sent in the ``Server`` header; an HTTP token.
    command : str
        The command that starts the server, e.g. ``game serve``. Messages name
        it: the refusal of a request without the key, and the hint for a busy port.
    token_header : str
        The header the page sends the access key in, e.g. ``X-Game-Token``.
    style_sources : tuple[str, ...]
        Stylesheet sources allowed besides the page's own files and inline
        styles, e.g. ``https://fonts.googleapis.com``.
    font_sources : tuple[str, ...]
        The whole ``font-src`` list, e.g. ``https://fonts.gstatic.com``; at least one.
    max_body : int
        Largest request body read, in bytes; a larger one is not read. A
        whole number, at least 1, as is `max_threads`.
    max_threads : int
        Connections are turned away while the process runs this many threads,
        so a trickle of slow clients cannot pile up handler threads. The
        default leaves room for the main and serving threads, 3 terminals (2
        threads each) and the page's polls.
    request_timeout : float
        Seconds a client may take to send its request; positive and finite.

    Raises
    ------
    ValueError
        If a name or a source would break its header, or a limit is out of range.
    """

    name: str
    command: str
    token_header: str
    style_sources: tuple[str, ...] = ()
    font_sources: tuple[str, ...] = ("'self'",)
    max_body: int = 64 * 1024
    max_threads: int = 32
    request_timeout: float = 30

    def __post_init__(self) -> None:
        """Check the settings once, when the game makes them."""
        for value in (self.name, self.token_header):
            if not terminal.HTTP_TOKEN.fullmatch(value):
                raise ValueError(f"the server name and token header must be HTTP tokens: {value!r}")
        sources = (*self.style_sources, *self.font_sources)
        if not self.font_sources or not all(CSP_SOURCE.fullmatch(source) for source in sources):
            raise ValueError(f"each style and font source must be one CSP source, with at least one font source: {sources!r}")
        counts = (self.max_body, self.max_threads)
        if any(type(count) is not int or count < 1 for count in counts) or not (
            math.isfinite(self.request_timeout) and self.request_timeout > 0
        ):
            raise ValueError("the body and thread limits must be whole numbers of at least 1, the request timeout positive and finite")


def security_headers(settings: ShellSettings) -> dict[str, str]:
    """
    List the headers every response carries.

    Parameters
    ----------
    settings : ShellSettings
        The style and font sources the page may load.

    Returns
    -------
    dict[str, str]
        No sniffing, no framing, no referrer, and a Content-Security-Policy that
        allows only the page's own scripts and connections.
    """
    styles = " ".join(("'self'", "'unsafe-inline'", *settings.style_sources))
    fonts = " ".join(settings.font_sources)
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Content-Security-Policy": (
            f"default-src 'self'; script-src 'self'; style-src {styles}; font-src {fonts}; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        ),
    }


@dataclass(frozen=True)
class ServerState:
    """
    What every request handler of one server shares.

    Attributes
    ----------
    token : str
        Secret every API request must present.
    routes : Mapping[tuple[str, str], Route]
        The game's JSON routes.
    static_dir : Path
        The page's files, served next to `SHARED_STATIC`.
    terminals : Mapping[str, terminal.TerminalSettings]
        The page's terminals, by path; empty serves none.
    settings : ShellSettings
        The game's names and limits.
    headers : dict[str, str]
        The security headers, from `security_headers`.
    slots : threading.BoundedSemaphore
        One slot per terminal that may be open, on any path.
    """

    token: str
    routes: Mapping[tuple[str, str], Route]
    static_dir: Path
    terminals: Mapping[str, terminal.TerminalSettings]
    settings: ShellSettings
    headers: dict[str, str]
    slots: threading.BoundedSemaphore


def same_secret(sent: str, token: str) -> bool:
    """
    Compare a secret sent by the client with the token, in constant time.

    Both are compared as UTF-8 bytes: `hmac.compare_digest` raises TypeError
    for strings with non-ASCII characters, which any client can send.

    Parameters
    ----------
    sent : str
        Value from the token header or the terminal's subprotocol.
    token : str
        The server's token.

    Returns
    -------
    bool
        True if they are equal.
    """
    return hmac.compare_digest(sent.encode(), token.encode())


def file_names(folder: Path) -> dict[str, Path]:
    """
    List the files directly in a folder.

    Parameters
    ----------
    folder : Path
        A static folder.

    Returns
    -------
    dict[str, Path]
        Each file's name and path; subfolders are left out.
    """
    return {entry.name: entry for entry in folder.iterdir() if entry.is_file()}


def content_length(value: str | None) -> int:
    """
    Read a request's Content-Length.

    Parameters
    ----------
    value : str | None
        The header, if any; surrounding whitespace is ignored.

    Returns
    -------
    int
        The length, or 0 if the header is missing or not 1 to 10 ASCII digits.
    """
    if value is None or not LENGTH.fullmatch(value.strip()):
        return 0
    return int(value.strip())


class Handler(BaseHTTPRequestHandler):
    """Serves the page, its static files, the game's JSON routes and the terminal."""

    def __init__(
        self, request: socket.socket, client_address: tuple[str, int], server: socketserver.BaseServer, *, state: ServerState
    ) -> None:
        """
        Handle one connection.

        Parameters
        ----------
        request : socket.socket
            The client's socket.
        client_address : tuple[str, int]
            Its address.
        server : socketserver.BaseServer
            The server that accepted it.
        state : ServerState
            What the server's handlers share.
        """
        self.state = state
        self.server_version = state.settings.name
        super().__init__(request, client_address, server)

    def setup(self) -> None:
        """Give the client the request timeout, counted from now, to send its whole request in."""
        super().setup()
        self.connection.settimeout(self.state.settings.request_timeout)
        self.rfile.close()
        self.reader = terminal.DeadlineReader(self.connection, time.monotonic() + self.state.settings.request_timeout)
        self.rfile = BufferedReader(self.reader)

    def log_message(self, format: str, *args: Any) -> None:
        """Stay quiet: a page may poll several times a second."""

    def do_GET(self) -> None:
        """Handle GET requests."""
        self.route("GET")

    def do_POST(self) -> None:
        """Handle POST requests."""
        self.route("POST")

    def route(self, method: str) -> None:
        """
        Authorize the request and dispatch it.

        Parameters
        ----------
        method : str
            ``GET`` or ``POST``.
        """
        url = urlsplit(self.path)
        query = {key: values[0] for key, values in parse_qs(url.query).items()}
        if not self.from_localhost():
            self.send(HTTPStatus.FORBIDDEN, b"unknown host", "text/plain")
            return
        if method == "GET" and not url.path.startswith("/api/"):
            self.send_static(url.path)
            return
        if method == "GET" and url.path in self.state.terminals:
            self.open_terminal(self.state.terminals[url.path])
            return
        if not same_secret(self.headers.get(self.state.settings.token_header, ""), self.state.token):
            self.refuse_key()
            return
        if method == "POST" and not self.same_origin():
            self.send(HTTPStatus.FORBIDDEN, b"cross-origin request", "text/plain")
            return

        handler = self.state.routes.get((method, url.path))
        if handler is None:
            self.send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            return
        status, payload = handler(query if method == "GET" else self.read_json())
        self.send(status, json.dumps(payload).encode(), "application/json")

    def from_localhost(self) -> bool:
        """
        Tell whether the Host header names this machine.

        Returns
        -------
        bool
            True for localhost and 127.0.0.1; False for other or malformed hosts.
        """
        host = self.headers.get("Host", "")
        try:
            hostname = urlsplit(f"//{host}").hostname
        except ValueError:
            hostname = None
        return hostname in LOCAL_HOSTS

    def same_origin(self) -> bool:
        """
        Tell whether a POST comes from this page (or from a tool that sends no Origin).

        The port counts: a page served by another program on localhost is
        same-site, but it is not this page.

        Returns
        -------
        bool
            False if an Origin header names another origin than this server.
        """
        origin = self.headers.get("Origin")
        return origin is None or origin in self.own_origins()

    def own_origins(self) -> set[str]:
        """
        List the origins this server's page can have.

        Returns
        -------
        set[str]
            ``http://localhost:PORT`` and ``http://127.0.0.1:PORT``.
        """
        port = self.connection.getsockname()[1]
        return {f"http://{name}:{port}" for name in LOCAL_HOSTS}

    def refuse_key(self) -> None:
        """Refuse a request without the right key, and say where the key comes from."""
        message = f"Open the link printed by `{self.state.settings.command}`: it carries the access key."
        self.send(HTTPStatus.FORBIDDEN, message.encode(), "text/plain; charset=utf-8")

    def open_terminal(self, settings: terminal.TerminalSettings) -> None:
        """
        Upgrade the request to a WebSocket bridged to a shell (see `firstcommit.termlab.web.terminal`).

        The token comes as a ``t.<token>`` subprotocol next to the game's one.
        Unlike the API, the Origin header is mandatory: browsers always send
        it on WebSocket upgrades, so this blocks cross-site WebSocket hijacking.

        Parameters
        ----------
        settings : terminal.TerminalSettings
            The settings of the terminal the request asked for.
        """
        if self.headers.get("Origin") not in self.own_origins():
            self.send(HTTPStatus.FORBIDDEN, b"cross-origin request", "text/plain")
            return
        offered = terminal.offered_key(self.headers, settings.protocol)
        if offered is None or not same_secret(offered, self.state.token):
            self.refuse_key()
            return
        key = terminal.handshake_key(self.headers)
        if key is None:
            self.send(HTTPStatus.BAD_REQUEST, b"expected a WebSocket handshake", "text/plain")
            return
        accept = terminal.accept_response(key, settings.protocol)
        if not self.state.slots.acquire(blocking=False):
            self.wfile.write(accept)
            terminal.turn_away(self.connection, self.wfile, settings.max_terminals)
            return
        # The terminal outlives the request: from here on, its own idle timeout applies.
        self.reader.deadline = None
        try:
            self.wfile.write(accept)
            terminal.run(self.connection, self.rfile, self.wfile, settings)
        finally:
            self.state.slots.release()

    def read_json(self) -> dict[str, Any]:
        """
        Parse the request body as a JSON object.

        Returns
        -------
        dict[str, Any]
            The object, or an empty dict if the body is empty, oversized, not
            JSON or not an object. Oversized or malformed lengths are not read.
        """
        length = content_length(self.headers.get("Content-Length"))
        raw = self.rfile.read(length) if 0 < length <= self.state.settings.max_body else b"{}"
        try:
            body = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            body = {}
        return body if isinstance(body, dict) else {}

    def send_static(self, path: str) -> None:
        """
        Serve the page or one of its files; only names that exist in the game's or the shared static folder.

        A shared file wins over a page file of the same name, even one added after startup.

        Parameters
        ----------
        path : str
            Request path.
        """
        name = "index.html" if path in ("", "/") else path.removeprefix("/static/")
        target = {**file_names(self.state.static_dir), **file_names(SHARED_STATIC)}.get(name)
        if target is None:
            self.send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            return
        self.send(HTTPStatus.OK, target.read_bytes(), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))

    def send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        """
        Send a complete response.

        Parameters
        ----------
        status : HTTPStatus
            Status code.
        body : bytes
            Response body.
        content_type : str
            Value of the Content-Type header.
        """
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        """Add the security headers to every response, the standard library's error pages included."""
        for name, value in self.state.headers.items():
            self.send_header(name, value)
        super().end_headers()


class CappedServer(ThreadingHTTPServer):
    """A threading HTTP server that turns connections away while too many threads are running."""

    def __init__(self, port: int, state: ServerState) -> None:
        """
        Bind to 127.0.0.1.

        Parameters
        ----------
        port : int
            TCP port; 0 picks a free one.
        state : ServerState
            What the request handlers share.
        """
        self.max_threads = state.settings.max_threads
        super().__init__(("127.0.0.1", port), partial(Handler, state=state))

    def verify_request(self, request: Any, client_address: Any) -> bool:
        """
        Accept a connection only below the thread limit; socketserver closes the ones refused.

        Parameters
        ----------
        request : Any
            The client's socket.
        client_address : Any
            Its address.

        Returns
        -------
        bool
            Whether to handle the connection.
        """
        return threading.active_count() < self.max_threads


def unreachable_routes(routes: Mapping[tuple[str, str], Route], terminal_paths: Collection[str]) -> list[tuple[str, str]]:
    """
    Find the routes no request could ever reach.

    Parameters
    ----------
    routes : Mapping[tuple[str, str], Route]
        The game's route table.
    terminal_paths : Collection[str]
        The paths of the server's terminals, whose GET each terminal takes.

    Returns
    -------
    list[tuple[str, str]]
        Routes with another method than GET and POST, a path outside ``/api/``,
        or a GET on a terminal's path.
    """
    taken = {("GET", path) for path in terminal_paths}
    return [key for key in routes if key[0] not in METHODS or not key[1].startswith("/api/") or key in taken]


def server_terminals(
    first: terminal.TerminalSettings | None, more: Mapping[str, terminal.TerminalSettings]
) -> dict[str, terminal.TerminalSettings]:
    """
    Give each of a server's terminals its path, checking that every one can be reached.

    Parameters
    ----------
    first : terminal.TerminalSettings | None
        The terminal at `TERMINAL_PATH`, whose ``max_terminals`` is the server's limit; None serves none.
    more : Mapping[str, terminal.TerminalSettings]
        More terminals, by path; each names the same ``max_terminals`` as `first`.

    Returns
    -------
    dict[str, terminal.TerminalSettings]
        Every terminal, by path.

    Raises
    ------
    ValueError
        If a path could never be reached (`TERMINAL_PATH` itself, or not a plain path under
        ``/api/``), or more terminals come without `first` or name another limit.
    """
    unreachable = sorted(path for path in more if path == TERMINAL_PATH or not TERMINAL_PATHS.fullmatch(path))
    if unreachable:
        raise ValueError(f"these terminal paths could never be reached: {unreachable}")
    if more and (first is None or any(settings.max_terminals != first.max_terminals for settings in more.values())):
        raise ValueError(
            "more terminals share the first terminal's limit: serve a terminal at /api/terminal, and give each the same max_terminals"
        )
    return {TERMINAL_PATH: first, **more} if first is not None else {}


def create_server(
    port: int,
    *,
    routes: Mapping[tuple[str, str], Route],
    static_dir: Path,
    terminal: terminal.TerminalSettings | None,
    settings: ShellSettings,
    more_terminals: Mapping[str, terminal.TerminalSettings] | None = None,
) -> tuple[ThreadingHTTPServer, str]:
    """
    Bind the web server to 127.0.0.1.

    Parameters
    ----------
    port : int
        TCP port; 0 picks a free one.
    routes : Mapping[tuple[str, str], Route]
        The game's JSON routes, keyed by method (``GET`` or ``POST``) and a path under ``/api/``.
    static_dir : Path
        The page's files: ``index.html`` is served at ``/``, every file at
        ``/static/<name>``, next to the files in `SHARED_STATIC` (the terminal,
        the token client and xterm.js).
    terminal : terminal.TerminalSettings | None
        The page's terminal at ``/api/terminal``; None serves none. Its
        ``max_terminals`` is the limit for the terminals of every path together.
    settings : ShellSettings
        The game's names and limits.
    more_terminals : Mapping[str, terminal.TerminalSettings] | None
        More terminals, by path (such as ``/api/terminal/second``), each with its own settings
        and the same ``max_terminals`` as `terminal`; None serves no more.

    Returns
    -------
    tuple[ThreadingHTTPServer, str]
        The server (not yet serving) and the link that opens the game, with
        the token in its fragment.

    Raises
    ------
    ValueError
        If a route or a terminal path could never be reached, more terminals name another limit,
        or a page file has the name of a shared one.
    OSError
        If the port cannot be bound, e.g. ``EADDRINUSE``.
    """
    terminals = server_terminals(terminal, more_terminals or {})
    unreachable = unreachable_routes(routes, terminals)
    if unreachable:
        raise ValueError(f"these routes could never be reached: {unreachable}")
    shadowing = sorted(file_names(static_dir).keys() & file_names(SHARED_STATIC).keys())
    if shadowing:
        raise ValueError(f"the page's static folder holds files named like shared ones; remove its copies: {shadowing}")
    slots = threading.BoundedSemaphore(terminal.max_terminals if terminal is not None else 0)
    state = ServerState(secrets.token_urlsafe(18), routes, static_dir, terminals, settings, security_headers(settings), slots)
    server = CappedServer(port, state)
    return server, f"http://localhost:{server.server_port}/#token={state.token}"


def paint(text: str, style: str, out: TextIO) -> str:
    """
    Wrap text in an ANSI style when it goes to a terminal and ``NO_COLOR`` is not set.

    Parameters
    ----------
    text : str
        Text to style.
    style : str
        SGR code, e.g. ``1`` for bold.
    out : TextIO
        Where the text goes.

    Returns
    -------
    str
        The styled text, or the text unchanged.
    """
    colored = out.isatty() and "NO_COLOR" not in os.environ
    return f"\033[{style}m{text}\033[0m" if colored else text


def serve(
    port: int,
    *,
    routes: Mapping[tuple[str, str], Route],
    static_dir: Path,
    terminal: terminal.TerminalSettings | None,
    settings: ShellSettings,
    banner: str,
    out: TextIO | None = None,
    more_terminals: Mapping[str, terminal.TerminalSettings] | None = None,
) -> int:
    """
    Serve the game on 127.0.0.1 until Ctrl-C: the body of a game's ``serve`` command.

    Parameters
    ----------
    port : int
        TCP port; 0 picks a free one.
    routes : Mapping[tuple[str, str], Route]
        As for `create_server`.
    static_dir : Path
        As for `create_server`.
    terminal : terminal.TerminalSettings | None
        As for `create_server`.
    settings : ShellSettings
        As for `create_server`.
    banner : str
        Printed first, as the game wants it shown.
    out : TextIO | None
        Where to print; None is standard output.
    more_terminals : Mapping[str, terminal.TerminalSettings] | None
        As for `create_server`.

    Returns
    -------
    int
        Exit status: 0 after Ctrl-C, 1 if the port is in use.

    Raises
    ------
    OSError
        If the port cannot be bound for another reason.
    """
    out = sys.stdout if out is None else out
    try:
        httpd, url = create_server(
            port, routes=routes, static_dir=static_dir, terminal=terminal, settings=settings, more_terminals=more_terminals
        )
    except OSError as error:
        if error.errno != errno.EADDRINUSE:
            raise
        print(f"  Port {port} is already in use. Try another one: {settings.command} --port {port + 1}", file=out)
        return 1
    print(banner, file=out)
    print("  Open this link in your browser (Ctrl+click in most terminals):", file=out)
    print(file=out)
    print("    " + paint(url, "1", out), file=out)
    print(file=out)
    print(paint("  Listening on 127.0.0.1 only; the link carries an access key, valid until the server stops.", "2", out), file=out)
    print(paint("  Keep this terminal open while you play; Ctrl-C stops the server.", "2", out), file=out)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped. Your progress is saved.", file=out)
    finally:
        httpd.server_close()
    return 0
