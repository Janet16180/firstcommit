"""Helpers shared by the tests that build real repositories and read them back."""

import os
from pathlib import Path

from firstcommit import gitcmd, repomap, save
from firstcommit.termlab import snippets

ALEX = gitcmd.Person("Alex Kim", "alex@example.com")
WHEN = "2026-01-15T09:00:00+00:00"


def shell(folder: Path, code: str) -> str:
    """
    Run bash code in a folder with the game's git environment, a fixed author and a fixed date.

    The code runs with ``set -e``, so a step that should fail needs ``|| true``.

    Parameters
    ----------
    folder : Path
        Folder to run in.
    code : str
        Bash code.

    Returns
    -------
    str
        Standard output.

    Raises
    ------
    AssertionError
        If the code fails (the test's setup is wrong).
    """
    env = gitcmd.environment(os.environ, save.home(), ALEX, WHEN)
    result = snippets.run("set -e\n" + code, folder, env)
    assert result.returncode == 0, f"{code}\n{result.stdout}{result.stderr}"
    return result.stdout


def entry(snap: repomap.Snapshot, path: str) -> repomap.FileEntry:
    """
    Find one path in a snapshot.

    Parameters
    ----------
    snap : repomap.Snapshot
        The snapshot.
    path : str
        The path to find.

    Returns
    -------
    repomap.FileEntry
        Its entry.

    Raises
    ------
    AssertionError
        If the snapshot does not list the path.
    """
    found = [file for file in snap["files"] if file["path"] == path]
    assert len(found) == 1, f"{path!r} in {[file['path'] for file in snap['files']]}"
    return found[0]
