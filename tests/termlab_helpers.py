"""Helpers for the tests of termlab's web server shell and terminal: test settings, a site to run, and HTTP calls to it."""

import os
import select
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from email.message import Message
from http import HTTPStatus
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import parse_qs, urlsplit

from firstcommit.termlab.web import shell, terminal

HTTP_TIMEOUT = 60
MARKER = "TESTGAME_LAB"
TERMINAL = terminal.TerminalSettings(
    protocol="testgame",
    notice_prefix="testgame",
    environment=lambda: terminal.player_env(os.environ, drop={MARKER}),
    start_folder=Path.home,
)
# The style and font sources of a page that uses Google Fonts.
SETTINGS = shell.ShellSettings(
    name="testgame",
    command="testgame serve",
    token_header="X-Testgame-Token",
    style_sources=("https://fonts.googleapis.com",),
    font_sources=("https://fonts.gstatic.com",),
)


def wait_for(condition: Callable[[], bool], timeout: float = 5.0, what: str = "the condition") -> None:
    """
    Poll until a condition holds.

    Parameters
    ----------
    condition : Callable[[], bool]
        Function checked every 20 ms.
    timeout : float
        Seconds to wait before giving up.
    what : str
        Description used in the error message.

    Raises
    ------
    TimeoutError
        If the condition is still false after `timeout` seconds.
    """
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise TimeoutError(f"timed out waiting for {what}")
        time.sleep(0.02)


def held_open(sock: socket.socket, drip: bytes, every: float = 0.3, limit: float = 10.0) -> float:
    """
    Keep sending a little data, as a slow client does, until the server closes the connection.

    Parameters
    ----------
    sock : socket.socket
        A connection to the server.
    drip : bytes
        Sent whenever the server has been quiet for `every` seconds; what the server sends is read and dropped.
    every : float
        Seconds between drips.
    limit : float
        Seconds after which the test fails.

    Returns
    -------
    float
        Seconds from the call until the server closed the connection.
    """
    began = time.monotonic()
    while time.monotonic() - began < limit:
        ready, _, _ = select.select([sock], [], [], every)
        try:
            if ready and sock.recv(65536) == b"":
                return time.monotonic() - began
            if not ready:
                sock.sendall(drip)
        except (ConnectionResetError, BrokenPipeError):
            return time.monotonic() - began
    raise AssertionError(f"the server still held the connection after {limit} s")


class Site(NamedTuple):
    """A web server running in this process on 127.0.0.1."""

    url: str
    port: int
    token: str


Response = tuple[int, Message, bytes]


def token_of(link: str) -> str:
    """
    Read the access token from the link the server prints.

    Parameters
    ----------
    link : str
        ``http://localhost:PORT/#token=TOKEN``.

    Returns
    -------
    str
        The token.
    """
    return parse_qs(urlsplit(link).fragment)["token"][0]


def make_opener(token: str | None = None) -> urllib.request.OpenerDirector:
    """
    Build a urllib opener that talks to the server directly, never through a proxy.

    Parameters
    ----------
    token : str | None
        Access token to send in the token header of every request, as the page
        does; None sends none.

    Returns
    -------
    urllib.request.OpenerDirector
        The opener.
    """
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    if token is not None:
        opener.addheaders.append((SETTINGS.token_header, token))
    return opener


def fetch(
    opener: urllib.request.OpenerDirector, url: str, data: bytes | None = None, headers: dict[str, str] | None = None
) -> Response:
    """
    Send a GET (no data) or POST request and return the response, whatever its status.

    Parameters
    ----------
    opener : urllib.request.OpenerDirector
        Opener to send it with.
    url : str
        Full URL; the path is sent as written, without normalization.
    data : bytes | None
        POST body; None sends a GET.
    headers : dict[str, str] | None
        Extra request headers, e.g. ``Host``, ``Origin`` or ``Cookie``.

    Returns
    -------
    Response
        Status code, headers and body.
    """
    request = urllib.request.Request(url, data=data, headers=headers or {}, method="GET" if data is None else "POST")
    try:
        response = opener.open(request, timeout=HTTP_TIMEOUT)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def dummy_routes(calls: list[dict[str, Any]]) -> dict[tuple[str, str], shell.Route]:
    """
    Build a route table that stands in for a game's API.

    Parameters
    ----------
    calls : list[dict[str, Any]]
        Receives each body that ``POST /api/echo`` gets, so a test can tell whether a route ran.

    Returns
    -------
    dict[tuple[str, str], shell.Route]
        ``GET /api/status``, ``GET`` and ``POST /api/echo`` (which reply with what they got) and ``POST /api/abort``.
    """

    def echo_body(body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
        calls.append(dict(body))
        return HTTPStatus.OK, {"body": dict(body)}

    return {
        ("GET", "/api/status"): lambda params: (HTTPStatus.OK, {"status": "ok"}),
        ("GET", "/api/echo"): lambda params: (HTTPStatus.OK, {"query": dict(params)}),
        ("POST", "/api/echo"): echo_body,
        ("POST", "/api/abort"): lambda body: (HTTPStatus.OK, {"aborted": None}),
    }
