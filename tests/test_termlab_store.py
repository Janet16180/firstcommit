import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from firstcommit.termlab import store

HOLD_LOCK = """
import sys
from pathlib import Path
from firstcommit.termlab import store

with store.lock(Path(sys.argv[1])):
    print("held", flush=True)
    sys.stdin.read()
"""


def lock_holder(home: Path) -> list[str]:
    """
    Build the command for a child process that takes the lock on `home`, prints ``held`` and waits for its stdin to close.

    Parameters
    ----------
    home : Path
        Home directory to lock.

    Returns
    -------
    list[str]
        The command.
    """
    return [sys.executable, "-c", HOLD_LOCK, str(home)]


# The first tests are Ring Zero's, with its settings, so the port is proven unchanged.
def test_home_defaults_to_a_dot_directory_in_the_users_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RING0_HOME", raising=False)
    assert store.home("RING0_HOME", "~/.ring0") == Path.home() / ".ring0"


def test_home_expands_a_tilde(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RING0_HOME", "~/games/ring0")
    assert store.home("RING0_HOME", "~/.ring0") == Path.home() / "games" / "ring0"


@pytest.mark.parametrize("value", ["", "relative/home", "./ring0", "~no-such-user-ring0/home"])
def test_home_must_be_an_absolute_path(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("RING0_HOME", value)
    with pytest.raises(ValueError, match="RING0_HOME must be an absolute path"):
        store.home("RING0_HOME", "~/.ring0")


def test_home_reads_the_variable_and_default_it_is_given(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BASICS_HOME", raising=False)
    assert store.home("BASICS_HOME", "~/.basics") == Path.home() / ".basics"
    monkeypatch.setenv("BASICS_HOME", "/srv/basics")
    assert store.home("BASICS_HOME", "~/.basics") == Path("/srv/basics")


def test_a_relative_home_is_refused_in_the_name_of_its_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASICS_HOME", "basics")
    with pytest.raises(ValueError, match="BASICS_HOME must be an absolute path"):
        store.home("BASICS_HOME", "~/.basics")


def test_read_json_returns_none_for_a_missing_file(tmp_path: Path) -> None:
    assert store.read_json(tmp_path / "missing.json") is None


def test_read_json_raises_on_a_damaged_file(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_text('{"xp": ')
    with pytest.raises(ValueError):
        store.read_json(path)


@pytest.mark.parametrize("content", ["[1, 2]", "null", '"text"', "0"])
def test_read_json_refuses_a_file_that_holds_no_object(tmp_path: Path, content: str) -> None:
    path = tmp_path / "save.json"
    path.write_text(content)
    with pytest.raises(ValueError, match="save.json does not hold a JSON object"):
        store.read_json(path)


def test_write_json_then_read_json_gives_the_same_object(tmp_path: Path) -> None:
    data = {"xp": 150, "missions": {"fds-fifo": {"hints": 1}}, "cards": {}}
    store.write_json(tmp_path / "save.json", data)
    assert store.read_json(tmp_path / "save.json") == data


def test_write_json_writes_sorted_keys_one_per_line(tmp_path: Path) -> None:
    store.write_json(tmp_path / "save.json", {"b": 2, "a": 1})
    assert (tmp_path / "save.json").read_text() == '{\n  "a": 1,\n  "b": 2\n}'


def test_write_json_creates_missing_folders(tmp_path: Path) -> None:
    path = tmp_path / "new" / "home" / "save.json"
    store.write_json(path, {"xp": 1})
    assert store.read_json(path) == {"xp": 1}


def test_write_json_replaces_the_file_and_leaves_nothing_else_behind(tmp_path: Path) -> None:
    store.write_json(tmp_path / "save.json", {"xp": 1})
    store.write_json(tmp_path / "save.json", {"xp": 2})
    assert [path.name for path in tmp_path.iterdir()] == ["save.json"]
    assert store.read_json(tmp_path / "save.json") == {"xp": 2}


def test_write_json_keeps_the_old_file_when_the_data_cannot_be_saved(tmp_path: Path) -> None:
    store.write_json(tmp_path / "save.json", {"xp": 1})
    with pytest.raises(TypeError):
        store.write_json(tmp_path / "save.json", {"xp": {1, 2}})
    assert store.read_json(tmp_path / "save.json") == {"xp": 1}


def test_write_json_syncs_the_new_file_before_the_replace_and_the_folder_after_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "save.json"
    store.write_json(path, {"xp": 1})
    events: list[tuple[str, Any]] = []
    real_fsync, real_replace = os.fsync, os.replace

    def fsync(fd: int) -> None:
        synced = Path(os.readlink(f"/proc/self/fd/{fd}"))
        events.append(("sync", "folder" if synced == tmp_path.resolve() else json.loads(synced.read_text())))
        real_fsync(fd)

    def replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        events.append(("replace", Path(target)))
        real_replace(source, target)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "replace", replace)
    store.write_json(path, {"xp": 2})
    assert events == [("sync", {"xp": 2}), ("replace", path), ("sync", "folder")]


def test_replace_bytes_writes_the_new_bytes_and_leaves_nothing_else_behind(tmp_path: Path) -> None:
    path = tmp_path / "launch.txt"
    path.write_bytes(b"<<<<<<< HEAD\nold\n")
    store.replace_bytes(path, b"new\n")
    assert path.read_bytes() == b"new\n"
    assert [entry.name for entry in tmp_path.iterdir()] == ["launch.txt"]


def test_replace_bytes_keeps_the_files_permission_bits(tmp_path: Path) -> None:
    path = tmp_path / "run.sh"
    path.write_bytes(b"old\n")
    path.chmod(0o751)
    store.replace_bytes(path, b"new\n")
    assert path.stat().st_mode & 0o7777 == 0o751


def test_replace_bytes_swaps_the_file_whole_so_a_reader_never_sees_half_of_it(tmp_path: Path) -> None:
    path = tmp_path / "big.txt"
    old, new = b"a" * 400_000, b"b" * 400_000
    path.write_bytes(old)
    seen: set[bytes] = set()
    stop = threading.Event()

    def read() -> None:
        while not stop.is_set():
            seen.add(path.read_bytes())

    reader = threading.Thread(target=read)
    reader.start()
    try:
        for _ in range(10):
            store.replace_bytes(path, new)
            store.replace_bytes(path, old)
    finally:
        stop.set()
        reader.join()
    assert seen <= {old, new}


def test_replace_bytes_syncs_the_new_file_before_the_replace_and_the_folder_after_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "launch.txt"
    path.write_bytes(b"old\n")
    events: list[tuple[str, Any]] = []
    real_fsync, real_replace = os.fsync, os.replace

    def fsync(fd: int) -> None:
        synced = Path(os.readlink(f"/proc/self/fd/{fd}"))
        events.append(("sync", "folder" if synced == tmp_path.resolve() else synced.read_bytes()))
        real_fsync(fd)

    def replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        events.append(("replace", Path(target)))
        real_replace(source, target)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "replace", replace)
    store.replace_bytes(path, b"new\n")
    assert events == [("sync", b"new\n"), ("replace", path), ("sync", "folder")]


def test_replace_bytes_leaves_the_old_file_and_no_temporary_one_when_the_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "launch.txt"
    path.write_bytes(b"old\n")

    def refuse(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        raise PermissionError("refused")

    monkeypatch.setattr(os, "replace", refuse)
    with pytest.raises(PermissionError):
        store.replace_bytes(path, b"new\n")
    assert path.read_bytes() == b"old\n"
    assert [entry.name for entry in tmp_path.iterdir()] == ["launch.txt"]


def test_replace_bytes_replaces_a_symbolic_link_itself_and_never_writes_through_it(tmp_path: Path) -> None:
    target = tmp_path / "outside.txt"
    target.write_bytes(b"keep\n")
    link = tmp_path / "launch.txt"
    link.symlink_to(target)
    store.replace_bytes(link, b"new\n")
    assert target.read_bytes() == b"keep\n"
    assert not link.is_symlink() and link.read_bytes() == b"new\n"


def test_lock_creates_a_missing_home(tmp_path: Path) -> None:
    home = tmp_path / "new" / "home"
    with store.lock(home):
        assert home.is_dir()


def test_the_lock_is_held_across_processes(tmp_path: Path) -> None:
    acquired = threading.Event()

    def take_lock() -> None:
        with store.lock(tmp_path):
            acquired.set()

    with subprocess.Popen(lock_holder(tmp_path), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as holder:
        assert holder.stdin is not None and holder.stdout is not None
        assert holder.stdout.readline() == "held\n"
        waiter = threading.Thread(target=take_lock, daemon=True)
        waiter.start()
        acquired_while_held = acquired.wait(0.5)
        holder.stdin.close()
    waiter.join(10)
    assert not acquired_while_held
    assert acquired.is_set()


def test_the_lock_is_released_when_the_block_ends(tmp_path: Path) -> None:
    with store.lock(tmp_path):
        pass
    result = subprocess.run(lock_holder(tmp_path), input="", capture_output=True, text=True, timeout=10)
    assert result.stdout == "held\n"
