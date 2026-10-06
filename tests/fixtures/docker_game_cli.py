"""
A stand-in for ``firstcommit.cli`` that the Docker tests build into an image.

It serves ``GET /api/status`` and the page's terminal through termlab, as the game does, so the
tests can check the container around a real server without waiting for the game's own routes.
"""

import argparse
import os
from http import HTTPStatus
from pathlib import Path
from typing import Any

from termlab.web import shell, terminal

TOKEN_HEADER = "X-FirstCommit-Token"


def status(query: dict[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    """
    Answer the status route.

    Parameters
    ----------
    query : dict[str, Any]
        The request's query (unused).

    Returns
    -------
    tuple[HTTPStatus, dict[str, Any]]
        200 and an empty object.
    """
    return HTTPStatus.OK, {}


def main(argv: list[str] | None = None) -> int:
    """
    Run ``firstcommit serve [--port N]``.

    Parameters
    ----------
    argv : list[str] | None
        Arguments after the program name, or None for ``sys.argv``.

    Returns
    -------
    int
        The server's exit status.
    """
    parser = argparse.ArgumentParser(prog="firstcommit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve").add_argument("--port", type=int, default=8820)
    args = parser.parse_args(argv)
    page_terminal = terminal.TerminalSettings(
        protocol="firstcommit",
        notice_prefix="firstcommit",
        environment=lambda: terminal.player_env(os.environ),
        start_folder=Path.home,
    )
    settings = shell.ShellSettings(name="firstcommit", command="firstcommit serve", token_header=TOKEN_HEADER)
    return shell.serve(
        args.port,
        routes={("GET", "/api/status"): status},
        static_dir=Path(__file__).parent / "web" / "static",
        terminal=page_terminal,
        settings=settings,
        banner="  First Commit (stand-in for the Docker tests)",
    )
