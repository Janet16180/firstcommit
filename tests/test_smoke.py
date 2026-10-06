"""The smoke flow of DESIGN.md section 3 where the tests run: the real ``firstcommit serve``, played through the page."""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from smoke import LINK, TEMPLATE_LEVEL, call, free_port, play_the_template_level, read_until


@pytest.mark.slow
def test_the_template_level_played_through_the_page_is_saved(game_home: Path, tmp_path: Path) -> None:
    port = free_port()
    player_home = tmp_path / "player"
    player_home.mkdir()
    # A fresh account: bash without the developer's own shell setup, and a home of its own.
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(player_home),
        "SHELL": "/bin/bash",
        "LANG": "C.UTF-8",
        "FIRSTCOMMIT_HOME": str(game_home),
        "PYTHONUNBUFFERED": "1",
    }
    command = [str(Path(sys.executable).parent / "firstcommit"), "serve", "--port", str(port)]
    server = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        assert server.stdout is not None
        link = read_until(server.stdout.fileno(), LINK, timeout=30)
        assert call(port, "GET", "/api/status", None)[0] == 403
        checked = play_the_template_level(port, link["token"])
        assert checked["solved"], checked

        server.send_signal(signal.SIGINT)

        assert server.wait(timeout=30) == 0
    finally:
        server.kill()
    progress = json.loads((game_home / "progress.json").read_text())
    assert progress["levels"][TEMPLATE_LEVEL]["xp"] > 0
