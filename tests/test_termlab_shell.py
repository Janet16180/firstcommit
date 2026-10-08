import dataclasses
import io
import json
import math
import os
import re
import select
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from firstcommit.termlab.web import shell
from termlab_helpers import HTTP_TIMEOUT, SETTINGS, TERMINAL, Site, fetch, held_open, make_opener, token_of, wait_for

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
    "base-uri 'none'; form-action 'none'"
)


def get(opener: urllib.request.OpenerDirector, url: str) -> tuple[int, Any]:
    """
    GET an API route and decode its JSON reply.

    Parameters
    ----------
    opener : urllib.request.OpenerDirector
        Opener to send it with.
    url : str
        Full URL.

    Returns
    -------
    tuple[int, Any]
        Status code and decoded payload.
    """
    status, _, body = fetch(opener, url)
    return status, json.loads(body)


def post(opener: urllib.request.OpenerDirector, url: str, payload: Any) -> tuple[int, Any]:
    """
    POST a JSON payload to an API route and decode its JSON reply.

    Parameters
    ----------
    opener : urllib.request.OpenerDirector
        Opener to send it with.
    url : str
        Full URL.
    payload : Any
        JSON-serializable request body.

    Returns
    -------
    tuple[int, Any]
        Status code and decoded payload.
    """
    status, _, body = fetch(opener, url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return status, json.loads(body)


@pytest.fixture
def browser(site: Site) -> urllib.request.OpenerDirector:
    """
    Talk to the server the way the page does, with the token in a header.

    Parameters
    ----------
    site : Site
        The running server.

    Returns
    -------
    urllib.request.OpenerDirector
        Opener that sends the token header.
    """
    return make_opener(site.token)


def test_api_requests_without_the_token_are_refused(site: Site, calls: list[dict[str, Any]]) -> None:
    base, token = site.url, site.token
    client = make_opener()
    for path in ["/api/status", "/api/echo?x=1", "/api/no-such-route", f"/api/status?token={token}"]:
        status, _, body = fetch(client, base + path)
        assert status == 403, path
        assert body == b"Open the link printed by `testgame serve`: it carries the access key."
    status, _, _ = fetch(client, f"{base}/api/echo", json.dumps({"mission": "x"}).encode())
    assert status == 403
    assert calls == []
    assert fetch(make_opener(token), f"{base}/api/status")[0] == 200


def test_the_page_is_public_and_sets_no_cookie(site: Site) -> None:
    base, token = site.url, site.token
    for path in ["/", "/static/app.js", f"/?token={token}"]:
        status, headers, _ = fetch(make_opener(), base + path)
        assert status == 200, path
        assert "Set-Cookie" not in headers


def test_the_link_carries_the_token_in_its_fragment(static_dir: Path) -> None:
    httpd, link = shell.create_server(0, routes={}, static_dir=static_dir, terminal=None, settings=SETTINGS)
    httpd.server_close()
    parts = urlsplit(link)
    assert (parts.scheme, parts.hostname, parts.port, parts.path, parts.query) == ("http", "localhost", httpd.server_port, "/", "")
    assert re.fullmatch(r"token=[A-Za-z0-9_-]{24}", parts.fragment)


def test_wrong_tokens_and_cookies_are_refused(site: Site) -> None:
    base, token = site.url, site.token
    client = make_opener()
    for guess in ["wrong", token[:-1], token + "A", "", "\u00e9", f"t.{token}"]:
        status, _, _ = fetch(client, f"{base}/api/status", headers={SETTINGS.token_header: guess})
        assert status == 403, guess
    for headers in [{"Cookie": f"testgame_token={token}"}, {"Authorization": f"Bearer {token}"}]:
        status, _, _ = fetch(client, f"{base}/api/status", headers=headers)
        assert status == 403, headers
    status, _, _ = fetch(client, f"{base}/api/abort?token={token}", b"{}")
    assert status == 403


def test_foreign_hosts_are_refused_even_with_the_token(site: Site, browser: urllib.request.OpenerDirector) -> None:
    base, port = site.url, site.port
    for host in ["evil.example", f"evil.example:{port}", f"localhost.evil.example:{port}", f"127.0.0.1.nip.io:{port}", "[", ""]:
        for path in ["/api/status", "/"]:
            status, _, body = fetch(browser, base + path, headers={"Host": host})
            assert (status, body) == (403, b"unknown host"), (host, path)

    for host in [f"localhost:{port}", f"127.0.0.1:{port}"]:
        status, _, _ = fetch(browser, f"{base}/api/status", headers={"Host": host})
        assert status == 200, host


def test_cross_origin_posts_are_refused(
    site: Site, browser: urllib.request.OpenerDirector, calls: list[dict[str, Any]]
) -> None:
    base, port = site.url, site.port
    foreign = [
        "http://evil.example",
        f"http://evil.example:{port}",
        f"http://localhost.evil.example:{port}",
        f"http://localhost:{port + 1}",
        f"https://localhost:{port}",
        "null",
        "http://[",
    ]
    for origin in foreign:
        status, _, body = fetch(browser, f"{base}/api/abort", b"{}", {"Origin": origin})
        assert (status, body) == (403, b"cross-origin request"), origin

    status, _, _ = fetch(browser, f"{base}/api/echo", json.dumps({"mission": "x"}).encode(), {"Origin": "http://evil.example"})
    assert status == 403
    assert calls == []

    same = [{"Origin": f"http://127.0.0.1:{port}"}, {"Origin": f"http://localhost:{port}", "Host": f"localhost:{port}"}, {}]
    for headers in same:
        status, _, body = fetch(browser, f"{base}/api/abort", b"{}", headers)
        assert (status, json.loads(body)) == (200, {"aborted": None}), headers


def test_every_response_forbids_framing_and_referrers(site: Site, browser: urllib.request.OpenerDirector) -> None:
    base = site.url
    responses = [
        fetch(browser, f"{base}/"),
        fetch(browser, f"{base}/static/app.js"),
        fetch(browser, f"{base}/api/status"),
        fetch(browser, f"{base}/no-such-file"),
        fetch(make_opener(), f"{base}/api/status"),
        fetch(browser, f"{base}/api/status", headers={"Host": "evil.example"}),
    ]
    for status, headers, _ in responses:
        assert headers["Content-Security-Policy"] == CSP, status
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["Referrer-Policy"] == "no-referrer"
        assert headers["X-Content-Type-Options"] == "nosniff"


def test_unfinished_requests_time_out(start_site: Callable[..., Site]) -> None:
    site = start_site(settings=dataclasses.replace(SETTINGS, request_timeout=0.5))
    with socket.create_connection(("127.0.0.1", site.port), timeout=HTTP_TIMEOUT) as sock:
        sock.sendall(b"GET /api/status HTTP/1.1\r\nHost: 127.0.0.1\r\n")
        began = time.monotonic()
        assert sock.recv(1024) == b""
        assert time.monotonic() - began < 5


def test_a_request_head_sent_a_byte_at_a_time_gets_one_deadline_in_all(start_site: Callable[..., Site]) -> None:
    site = start_site(settings=dataclasses.replace(SETTINGS, request_timeout=1.0))
    with socket.create_connection(("127.0.0.1", site.port), timeout=HTTP_TIMEOUT) as sock:
        sock.sendall(b"G")
        assert held_open(sock, b"E") < 2.0


def test_a_body_sent_a_byte_at_a_time_gets_the_same_deadline_and_never_reaches_the_route(
    start_site: Callable[..., Site], calls: list[dict[str, Any]]
) -> None:
    site = start_site(settings=dataclasses.replace(SETTINGS, request_timeout=1.0))
    head = f"POST /api/echo HTTP/1.1\r\nHost: 127.0.0.1:{site.port}\r\n{SETTINGS.token_header}: {site.token}\r\n"
    with socket.create_connection(("127.0.0.1", site.port), timeout=HTTP_TIMEOUT) as sock:
        sock.sendall(f"{head}Content-Length: 1000\r\n\r\n{{".encode())
        assert held_open(sock, b" ") < 2.0
    assert calls == []


def raw_exchange(port: int, request: bytes) -> tuple[int, dict[str, str]]:
    """
    Send raw bytes to the server and read its whole answer.

    Parameters
    ----------
    port : int
        Server port on 127.0.0.1.
    request : bytes
        What to send, possibly not valid HTTP.

    Returns
    -------
    tuple[int, dict[str, str]]
        Status code and headers (names lowercased).
    """
    with socket.create_connection(("127.0.0.1", port), timeout=HTTP_TIMEOUT) as sock:
        sock.sendall(request)
        answer = b""
        chunk = sock.recv(65536)
        while chunk:
            answer += chunk
            chunk = sock.recv(65536)
    head = answer.split(b"\r\n\r\n", 1)[0].decode("latin-1").split("\r\n")
    headers = {name.strip().lower(): value.strip() for name, _, value in (line.partition(":") for line in head[1:])}
    return int(head[0].split()[1]), headers


def test_error_pages_of_the_standard_library_carry_the_security_headers(site: Site) -> None:
    port = site.port
    answers = [
        raw_exchange(port, f"OPTIONS / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n\r\n".encode()),
        raw_exchange(port, f"HEAD / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n\r\n".encode()),
        raw_exchange(port, b"GET / HTTP/1.1\r\n" + b"X-Filler: 1\r\n" * 101 + b"\r\n"),
        raw_exchange(port, b"GET /" + b"a" * (65537 - 5)),
    ]
    assert [status for status, _ in answers] == [501, 501, 431, 414]
    for status, headers in answers:
        assert headers["content-security-policy"] == CSP, status
        assert headers["x-frame-options"] == "DENY"
        assert headers["referrer-policy"] == "no-referrer"
        assert headers["x-content-type-options"] == "nosniff"


def test_a_content_length_too_long_for_int_still_gets_an_answer(site: Site) -> None:
    port, token = site.port, site.token
    request = (
        f"POST /api/abort HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n{SETTINGS.token_header}: {token}\r\n"
        f"Content-Length: {'9' * 5000}\r\n\r\n"
    )
    status, headers = raw_exchange(port, request.encode())
    assert (status, headers["content-type"]) == (200, "application/json")


def test_too_many_threads_turn_new_connections_away(start_site: Callable[..., Site]) -> None:
    # The cap counts every thread in the process: the ones running now, the server's own, and two handlers.
    idle = threading.active_count() + 1
    site = start_site(settings=dataclasses.replace(SETTINGS, max_threads=idle + 2))
    address = ("127.0.0.1", site.port)
    trickles = [socket.create_connection(address, timeout=HTTP_TIMEOUT) for _ in range(2)]
    for sock in trickles:
        sock.sendall(b"GET /api/status HTTP/1.1\r\n")
    wait_for(lambda: threading.active_count() == idle + 2, what="two handler threads")

    # Closed at once: a connection that was accepted would wait for its request instead.
    with socket.create_connection(address, timeout=2) as refused:
        assert refused.recv(1024) == b""

    for sock in trickles:
        sock.close()
    wait_for(lambda: threading.active_count() == idle, what="the handler threads to finish")
    status, _, _ = fetch(make_opener(site.token), f"{site.url}/api/status")
    assert status == 200


def test_the_page_and_its_files_are_served(
    site: Site, browser: urllib.request.OpenerDirector, static_dir: Path
) -> None:
    base = site.url
    cases = [("/", "index.html", "text/html"), ("/static/app.js", "app.js", "text/javascript"), ("/static/app.css", "app.css", "text/css")]
    for path, name, content_type in cases:
        status, headers, body = fetch(browser, base + path)
        assert status == 200, path
        assert headers["Content-Type"].startswith(content_type)
        assert body == (static_dir / name).read_bytes()


def test_a_page_font_is_served_as_woff2(site: Site, browser: urllib.request.OpenerDirector, static_dir: Path) -> None:
    (static_dir / "pixel.woff2").write_bytes(b"wOF2 not a real font")
    status, headers, body = fetch(browser, f"{site.url}/static/pixel.woff2")
    assert (status, headers["Content-Type"], body) == (200, "font/woff2", b"wOF2 not a real font")


def test_the_shared_files_are_served_next_to_the_pages_own(site: Site) -> None:
    cases = [("xterm.js", "text/javascript"), ("xterm.css", "text/css"), ("xterm-LICENSE.txt", "application/octet-stream")]
    for name, content_type in cases:
        status, headers, body = fetch(make_opener(), f"{site.url}/static/{name}")
        assert status == 200, name
        assert headers["Content-Type"].startswith(content_type)
        assert body == (shell.SHARED_STATIC / name).read_bytes()


def test_a_page_file_named_like_a_shared_one_is_refused(static_dir: Path) -> None:
    (static_dir / "xterm.js").write_text("// an old copy")
    with pytest.raises(ValueError, match="xterm.js"):
        shell.create_server(0, routes={}, static_dir=static_dir, terminal=None, settings=SETTINGS)


def test_a_page_file_added_after_startup_cannot_shadow_a_shared_one(site: Site, static_dir: Path) -> None:
    (static_dir / "terminal.js").write_text("// a stale copy")
    status, _, body = fetch(make_opener(), f"{site.url}/static/terminal.js")
    assert (status, body) == (200, (shell.SHARED_STATIC / "terminal.js").read_bytes())


def test_paths_outside_the_static_folder_are_never_served(
    site: Site, browser: urllib.request.OpenerDirector
) -> None:
    base = site.url
    paths = [
        "/static/../server.py",
        "/static/%2e%2e/server.py",
        "/static/%2E%2E%2Fserver.py",
        "/static/..%2fguides.py",
        "/static/..\\server.py",
        "/static/../shell.py",
        "/static/%2e%2e/terminal.py",
        "/static/..%2fshell.py",
        "/static/../__init__.py",
        "/static/../../../../../../etc/passwd",
        "/static//etc/passwd",
        "/static/%2fetc%2fpasswd",
        "/../../etc/passwd",
        "//etc/passwd",
        "/server.py",
        "/static/..",
        "/static/",
        "/api/no-such-route",
    ]
    for path in paths:
        status, _, body = fetch(browser, base + path)
        assert (status, body) == (404, b"not found"), path
    status, _, _ = fetch(browser, f"{base}/api/no-such-route", b"{}")
    assert status == 404


def test_body_size_is_validated_before_reading(site: Site, calls: list[dict[str, Any]]) -> None:
    for declared in ["-5", "abc", "\u00b2", str(SETTINGS.max_body + 1)]:
        request = (
            f"POST /api/echo HTTP/1.1\r\nHost: 127.0.0.1:{site.port}\r\n{SETTINGS.token_header}: {site.token}\r\n"
            f"Content-Length: {declared}\r\n\r\n"
        )
        # No body follows: a server that tried to read one would wait for it and never answer.
        status, _ = raw_exchange(site.port, request.encode("latin-1"))
        assert status == 200, declared
    assert calls == [{}] * 4


def test_get_routes_get_the_query_and_post_routes_the_json_body(
    site: Site, browser: urllib.request.OpenerDirector, calls: list[dict[str, Any]]
) -> None:
    base = site.url
    assert get(browser, f"{base}/api/echo?a=1&a=2&b=x%20y&c=") == (200, {"query": {"a": "1", "b": "x y"}})
    assert post(browser, f"{base}/api/echo", {"n": [1, 2], "s": "café"}) == (200, {"body": {"n": [1, 2], "s": "café"}})
    for raw in [b"not json", b"\xff\xfe\x00", b"", b"[1, 2]", b"null", b"[" * 50_000]:
        status, _, body = fetch(browser, f"{base}/api/echo", raw)
        assert (status, json.loads(body)) == (200, {"body": {}}), raw[:10]
    assert calls == [{"n": [1, 2], "s": "café"}] + [{}] * 6


def test_a_route_answers_only_its_own_method(site: Site, browser: urllib.request.OpenerDirector) -> None:
    assert fetch(browser, f"{site.url}/api/abort")[0::2] == (404, b"not found")
    assert fetch(browser, f"{site.url}/api/status", b"{}")[0::2] == (404, b"not found")


def test_a_rebound_name_is_refused_even_when_its_origin_names_this_server(
    site: Site, browser: urllib.request.OpenerDirector, calls: list[dict[str, Any]]
) -> None:
    # DNS rebinding: evil.example now resolves to 127.0.0.1, so its page is same-origin with itself.
    port = site.port
    for origin in [f"http://evil.example:{port}", f"http://localhost:{port}", f"http://127.0.0.1:{port}"]:
        headers = {"Host": f"evil.example:{port}", "Origin": origin}
        assert fetch(browser, f"{site.url}/api/echo", b"{}", headers)[0::2] == (403, b"unknown host"), origin
        assert fetch(browser, f"{site.url}/api/status", headers=headers)[0::2] == (403, b"unknown host"), origin
    assert calls == []


def test_without_a_terminal_its_path_is_an_ordinary_api_path(start_site: Callable[..., Site]) -> None:
    site = start_site(terminal=None)
    offer = {"Origin": f"http://127.0.0.1:{site.port}", "Sec-WebSocket-Protocol": f"testgame, t.{site.token}"}
    assert fetch(make_opener(), f"{site.url}/api/terminal", headers=offer)[0] == 403
    assert fetch(make_opener(site.token), f"{site.url}/api/terminal")[0::2] == (404, b"not found")


def test_the_server_header_names_the_game(site: Site) -> None:
    _, headers, _ = fetch(make_opener(), f"{site.url}/")
    assert headers["Server"].split()[0] == "testgame"


def test_by_default_the_page_loads_styles_and_fonts_only_from_itself(start_site: Callable[..., Site]) -> None:
    site = start_site(settings=shell.ShellSettings(name="testgame", command="testgame serve", token_header="X-Testgame-Token"))
    _, headers, _ = fetch(make_opener(), f"{site.url}/")
    assert headers["Content-Security-Policy"] == (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    )


def test_shell_settings_refuse_values_that_would_break_a_header() -> None:
    bad: list[dict[str, Any]] = [
        {"name": ""},
        {"name": "two words"},
        {"name": "game\r\nX-Injected: 1"},
        {"token_header": ""},
        {"token_header": "X-Token:"},
        {"style_sources": ("https://fonts.example; script-src *",)},
        {"style_sources": ("https://a.example https://b.example",)},
        {"font_sources": ("https://fonts.example,",)},
        {"font_sources": ()},
        # Anything but visible ASCII: http.server would send NUL and controls, and fail on U+0100.
        *({"font_sources": (f"https://fonts.example/{char}",)} for char in ["\x00", "\x01", "\x1f", "\x7f", "\u00e9", "\u0100"]),
        {"style_sources": ("https://fonts.example\tX",)},
    ]
    for change in bad:
        with pytest.raises(ValueError):
            dataclasses.replace(SETTINGS, **change)
    sources = ("'self'", "data:", "https://*.example.com:8443/fonts/", "'sha256-AbC+/=='", "'unsafe-hashes'")
    assert dataclasses.replace(SETTINGS, style_sources=sources, font_sources=sources).font_sources == sources


def test_shell_settings_refuse_limits_that_are_not_positive() -> None:
    # A float or infinite thread limit removes the cap, and NaN compares false with everything.
    bad: list[dict[str, Any]] = [
        *({name: value} for name in ["max_body", "max_threads"] for value in [0, -1, 1.5, math.inf, math.nan, True, "64"]),
        *({"request_timeout": value} for value in [0, -1, math.inf, -math.inf, math.nan]),
    ]
    for change in bad:
        with pytest.raises(ValueError, match="limits"):
            dataclasses.replace(SETTINGS, **change)
    good = dataclasses.replace(SETTINGS, max_body=1, max_threads=1, request_timeout=0.5)
    assert (good.max_body, good.max_threads, good.request_timeout) == (1, 1, 0.5)


def test_routes_that_could_never_be_reached_are_refused(static_dir: Path) -> None:
    def reply(body: Any) -> tuple[HTTPStatus, dict[str, Any]]:
        return HTTPStatus.OK, {}

    for key in [("PUT", "/api/x"), ("get", "/api/x"), ("GET", "/x"), ("POST", "api/x"), ("GET", "/api/terminal")]:
        with pytest.raises(ValueError, match="never"):
            shell.create_server(0, routes={key: reply}, static_dir=static_dir, terminal=TERMINAL, settings=SETTINGS)
    for key, terminal in [(("POST", "/api/terminal"), TERMINAL), (("GET", "/api/terminal"), None)]:
        httpd, _ = shell.create_server(0, routes={key: reply}, static_dir=static_dir, terminal=terminal, settings=SETTINGS)
        httpd.server_close()



def test_more_terminals_need_a_reachable_path_and_the_first_terminals_limit(static_dir: Path) -> None:
    def reply(body: Any) -> tuple[HTTPStatus, dict[str, Any]]:
        return HTTPStatus.OK, {}

    def create(first: Any, more: dict[str, Any], routes: dict[tuple[str, str], Any]) -> None:
        httpd, _ = shell.create_server(0, routes=routes, static_dir=static_dir, terminal=first, settings=SETTINGS, more_terminals=more)
        httpd.server_close()

    for path in ["/api/terminal", "/terminal/second", "/api/terminal/second?x", "/api/status"]:
        with pytest.raises(ValueError, match="never"):
            create(TERMINAL, {path: TERMINAL}, {("GET", "/api/status"): reply})
    other_limit = dataclasses.replace(TERMINAL, max_terminals=TERMINAL.max_terminals + 1)
    for first, second in [(None, TERMINAL), (TERMINAL, other_limit)]:
        with pytest.raises(ValueError, match="limit"):
            create(first, {"/api/terminal/second": second}, {})
    create(TERMINAL, {"/api/terminal/second": TERMINAL}, {("POST", "/api/terminal/second"): reply})


SERVE = """
import sys
from http import HTTPStatus
from pathlib import Path

from firstcommit.termlab.web import shell

settings = shell.ShellSettings(name="testgame", command="testgame serve", token_header="X-Testgame-Token")
routes = {("GET", "/api/status"): lambda params: (HTTPStatus.OK, {"status": "ok"})}
sys.exit(shell.serve(0, routes=routes, static_dir=Path(sys.argv[1]), terminal=None, settings=settings, banner="TESTGAME"))
"""


def read_until(fd: int, marker: bytes) -> bytes:
    """
    Read a child's output until a marker shows up.

    Parameters
    ----------
    fd : int
        Pipe or pseudo-terminal the child writes to.
    marker : bytes
        Text to wait for.

    Returns
    -------
    bytes
        Everything read, up to and including the chunk that completed the marker.
    """
    output = b""
    while marker not in output:
        ready, _, _ = select.select([fd], [], [], HTTP_TIMEOUT)
        chunk = os.read(fd, 4096) if ready else b""
        assert chunk, f"no {marker!r} in the output: {output!r}"
        output += chunk
    return output


def serve_in_child(static_dir: Path, tty: bool) -> tuple[bytes, bytes, int]:
    """
    Run `shell.serve` in a child process, open its link once it is printed, then press Ctrl-C.

    Parameters
    ----------
    static_dir : Path
        The page's files.
    tty : bool
        Whether the child writes to a terminal, rather than to a pipe.

    Returns
    -------
    tuple[bytes, bytes, int]
        Output up to the banner's last line, the output after Ctrl-C, and the exit status.
    """
    env = {name: value for name, value in os.environ.items() if name != "NO_COLOR"} | {"PYTHONUNBUFFERED": "1"}
    reader, writer = os.openpty() if tty else os.pipe()
    proc = subprocess.Popen([sys.executable, "-c", SERVE, str(static_dir)], stdout=writer, stderr=writer, env=env)
    os.close(writer)
    try:
        banner = read_until(reader, b"Ctrl-C stops the server.")
        link = re.search(rb"http://localhost:\d+/#token=[A-Za-z0-9_-]+", banner)
        assert link is not None, banner
        parts = urlsplit(link.group().decode())
        assert fetch(make_opener(token_of(link.group().decode())), f"http://127.0.0.1:{parts.port}/api/status")[0] == 200
        proc.send_signal(signal.SIGINT)
        farewell = read_until(reader, b"Your progress is saved.")
        status = proc.wait(timeout=HTTP_TIMEOUT)
    finally:
        proc.kill()
        proc.wait()
        os.close(reader)
    return banner, farewell, status


def test_serve_prints_a_working_link_and_stops_on_ctrl_c(static_dir: Path) -> None:
    banner, farewell, status = serve_in_child(static_dir, tty=False)
    lines = banner.decode().splitlines()
    assert lines[0] == "TESTGAME"
    assert lines[1:3] == ["  Open this link in your browser (Ctrl+click in most terminals):", ""]
    assert re.fullmatch(r"    http://localhost:\d+/#token=[A-Za-z0-9_-]{24}", lines[3])
    assert lines[4:] == [
        "",
        "  Listening on 127.0.0.1 only; the link carries an access key, valid until the server stops.",
        "  Keep this terminal open while you play; Ctrl-C stops the server.",
    ]
    assert farewell == b"\n  Server stopped. Your progress is saved.\n"
    assert status == 0


def test_serve_highlights_the_link_in_a_terminal(static_dir: Path) -> None:
    banner, _, status = serve_in_child(static_dir, tty=True)
    assert re.search(rb"\r\n    \x1b\[1mhttp://localhost:\d+/#token=[A-Za-z0-9_-]{24}\x1b\[0m\r\n", banner)
    assert b"\x1b[2m  Keep this terminal open while you play; Ctrl-C stops the server.\x1b[0m" in banner
    assert status == 0


def test_serve_reports_a_busy_port(static_dir: Path) -> None:
    out = io.StringIO()
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        port = blocker.getsockname()[1]
        status = shell.serve(port, routes={}, static_dir=static_dir, terminal=None, settings=SETTINGS, banner="TESTGAME", out=out)
    assert status == 1
    assert out.getvalue() == f"  Port {port} is already in use. Try another one: testgame serve --port {port + 1}\n"
