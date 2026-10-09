import os
import subprocess
import time
from pathlib import Path

import pytest

from firstcommit.termlab import snippets

ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C"}


def is_alive(pid: int) -> bool:
    """
    Tell whether a process is still running; one that has exited but not been reaped counts as gone.

    Parameters
    ----------
    pid : int
        Process id.

    Returns
    -------
    bool
        True if the process exists and is not a zombie.
    """
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return False
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


def test_run_returns_the_exit_status_and_both_outputs(tmp_path: Path) -> None:
    result = snippets.run("echo out; echo err >&2; exit 3", tmp_path, ENV)
    assert (result.returncode, result.stdout, result.stderr) == (3, "out\n", "err\n")


def test_a_snippet_that_cannot_test_its_claim_here_exits_the_skip_status(tmp_path: Path) -> None:
    result = snippets.run(f'echo "no user namespaces here"; exit {snippets.SKIP_STATUS}', tmp_path, ENV)
    assert snippets.SKIP_STATUS == 77
    assert result.returncode == snippets.SKIP_STATUS
    assert result.stdout == "no user namespaces here\n"


def test_the_snippet_runs_in_the_folder_it_is_given(tmp_path: Path) -> None:
    assert snippets.run("pwd", tmp_path, ENV).stdout == f"{tmp_path.resolve()}\n"


def test_the_snippet_sees_exactly_the_environment_it_is_given(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CALLER_ONLY", "leaked")
    result = snippets.run('echo "$GREETING ${CALLER_ONLY-unset}"', tmp_path, {**ENV, "GREETING": "hello"})
    assert result.stdout == "hello unset\n"


def test_the_snippet_leads_its_own_session(tmp_path: Path) -> None:
    # Field 6 of /proc/<pid>/stat is the session id; bash's name holds no space to shift it.
    result = snippets.run("echo $$ $(cut -d' ' -f6 /proc/$$/stat)", tmp_path, ENV)
    pid, session = result.stdout.split()
    assert pid == session
    assert int(session) != os.getsid(0)


def test_a_snippet_that_runs_out_of_time_is_killed_with_the_children_it_started(tmp_path: Path) -> None:
    with pytest.raises(subprocess.TimeoutExpired):
        snippets.run("sleep 60 >/dev/null 2>&1 & echo $! > child.pid; wait", tmp_path, ENV, timeout=1)
    child = int((tmp_path / "child.pid").read_text())
    deadline = time.monotonic() + 5
    while is_alive(child) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not is_alive(child)
