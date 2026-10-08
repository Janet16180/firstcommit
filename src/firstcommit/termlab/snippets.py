"""Test support: run the shell snippets that lessons and cards make claims about."""

import os
import signal
import subprocess
from collections.abc import Mapping
from pathlib import Path

SKIP_STATUS = 77  # automake convention: "this test cannot run here"


def run(code: str, cwd: Path, env: Mapping[str, str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
    """
    Run a snippet in bash, without startup files or input, in a given folder and environment.

    The snippet gets its own session, so a stray ``kill 0`` cannot reach the caller, and
    its whole process group is killed if it runs out of time.

    Parameters
    ----------
    code : str
        Bash code. One that cannot test its claim on this machine exits `SKIP_STATUS`.
    cwd : Path
        Folder to run it in.
    env : Mapping[str, str]
        The snippet's whole environment; nothing is inherited from the caller.
    timeout : float
        Seconds the snippet may run.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The snippet's exit status, stdout and stderr.

    Raises
    ------
    subprocess.TimeoutExpired
        If the snippet runs longer than `timeout`; its process group is killed first.
    """
    proc = subprocess.Popen(
        ["bash", "--noprofile", "--norc", "-c", code],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)
