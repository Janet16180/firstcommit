import hashlib
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from firstcommit import repomap
from repo_helpers import ALEX, WHEN, entry, shell

HELLO = "ce013625030ba8dba906f756967f9e9ca394464a"
NOTHING: repomap.Snapshot = {
    "exists": False,
    "bare": False,
    "head": None,
    "branch": None,
    "commits": [],
    "refs": [],
    "files": [],
    "operation": None,
    "stash": 0,
    "truncated": False,
}


def blob_id(data: bytes) -> str:
    """
    Compute a blob's SHA-1 object id the way git defines it, independently of git.

    Parameters
    ----------
    data : bytes
        The blob's content.

    Returns
    -------
    str
        Its object id.
    """
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def new_repo(tmp_path: Path, code: str = "") -> Path:
    """
    Create a repository on branch ``main`` in ``tmp_path/project`` and run code in it.

    Parameters
    ----------
    tmp_path : Path
        The test's folder.
    code : str
        Bash code to run in the new repository.

    Returns
    -------
    Path
        The repository's folder.
    """
    repo = tmp_path / "project"
    shell(tmp_path, "git init -q -b main project")
    if code:
        shell(repo, code)
    return repo


def rev(repo: Path, name: str) -> str:
    """
    Resolve a name to a full object id.

    Parameters
    ----------
    repo : Path
        The repository.
    name : str
        Anything ``git rev-parse`` accepts.

    Returns
    -------
    str
        The object id.
    """
    return shell(repo, f"git rev-parse {name}").strip()


def areas(snap: repomap.Snapshot, path: str) -> tuple[str | None, str | None, str | None]:
    """
    Give a path's blob ids in the three areas.

    Parameters
    ----------
    snap : repomap.Snapshot
        The snapshot.
    path : str
        A path it lists.

    Returns
    -------
    tuple[str | None, str | None, str | None]
        The ids in HEAD, the staging area and the working folder.
    """
    file = entry(snap, path)
    return file["head"], file["index"], file["folder"]


def test_a_missing_folder_holds_no_repository(tmp_path: Path) -> None:
    assert repomap.snapshot(tmp_path / "missing") == NOTHING


def test_an_empty_folder_holds_no_repository(tmp_path: Path) -> None:
    assert repomap.snapshot(tmp_path) == NOTHING


def test_a_file_where_the_folder_should_be_holds_no_repository(tmp_path: Path) -> None:
    (tmp_path / "project").write_text("not a folder\n")
    assert repomap.snapshot(tmp_path / "project") == NOTHING


def test_a_new_repository_is_on_its_branch_before_its_first_commit(tmp_path: Path) -> None:
    snap = repomap.snapshot(new_repo(tmp_path))
    assert snap == {**NOTHING, "exists": True, "branch": "main"}


def test_a_commit_puts_the_same_blob_in_head_the_staging_area_and_the_folder(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "printf 'hello\\n' > hello.txt && git add hello.txt && git commit -q -m 'Say hello'")
    snap = repomap.snapshot(repo)
    head = rev(repo, "HEAD")
    assert snap["head"] == head
    assert snap["branch"] == "main"
    assert snap["commits"] == [
        {
            "hash": head,
            "short": head[:7],
            "parents": [],
            "subject": "Say hello",
            "author": ALEX.name,
            "time": int(datetime.fromisoformat(WHEN).timestamp()),
        }
    ]
    assert snap["refs"] == [{"name": "main", "kind": "branch", "target": head}]
    assert snap["files"] == [
        {"path": "hello.txt", "head": HELLO, "index": HELLO, "folder": HELLO, "ignored": False, "conflicted": False}
    ]


def test_each_area_shows_untracked_staged_changed_and_deleted_files(tmp_path: Path) -> None:
    repo = new_repo(
        tmp_path,
        "echo one > changed.txt && echo one > deleted.txt && echo one > staged.txt && git add . && git commit -q -m one\n"
        "echo two > changed.txt && rm deleted.txt && echo two > staged.txt && git add staged.txt\n"
        "echo new > added.txt && git add added.txt && echo new > untracked.txt\n",
    )
    snap = repomap.snapshot(repo)
    one, two, new = blob_id(b"one\n"), blob_id(b"two\n"), blob_id(b"new\n")
    assert [file["path"] for file in snap["files"]] == ["added.txt", "changed.txt", "deleted.txt", "staged.txt", "untracked.txt"]
    assert areas(snap, "added.txt") == (None, new, new)
    assert areas(snap, "changed.txt") == (one, one, two)
    assert areas(snap, "deleted.txt") == (one, one, None)
    assert areas(snap, "staged.txt") == (one, two, two)
    assert areas(snap, "untracked.txt") == (None, None, new)


def test_ignored_files_are_listed_and_marked_ignored(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "printf '*.log\\nbuild/\\n' > .gitignore && mkdir build && echo x > build/app.o && echo y > debug.log")
    snap = repomap.snapshot(repo)
    assert entry(snap, "build/app.o") == {"path": "build/app.o", "head": None, "index": None, "folder": blob_id(b"x\n"), "ignored": True, "conflicted": False}
    assert entry(snap, "debug.log")["ignored"]
    assert not entry(snap, ".gitignore")["ignored"]


def test_a_tracked_file_that_matches_an_ignore_rule_is_not_ignored(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo x > kept.log && git add kept.log && git commit -q -m log && echo '*.log' > .gitignore")
    assert not entry(repomap.snapshot(repo), "kept.log")["ignored"]


def test_a_detached_head_names_no_branch(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "git commit -q --allow-empty -m one && git commit -q --allow-empty -m two && git switch -q --detach HEAD~1")
    snap = repomap.snapshot(repo)
    assert snap["branch"] is None
    assert snap["head"] == rev(repo, "main~1")


def test_commits_from_every_branch_and_a_detached_head_are_listed_children_first(tmp_path: Path) -> None:
    repo = new_repo(
        tmp_path,
        "git commit -q --allow-empty -m base && git switch -q -c feature && git commit -q --allow-empty -m feature-work\n"
        "git switch -q main && git commit -q --allow-empty -m main-work && git merge -q --no-edit feature\n"
        "echo wip > wip.txt && git add wip.txt && git stash -q\n"
        "git switch -q --detach HEAD && git commit -q --allow-empty -m detached-work\n",
    )
    snap = repomap.snapshot(repo)
    subjects = {commit["subject"] for commit in snap["commits"]}
    assert subjects == {"base", "feature-work", "main-work", "Merge branch 'feature'", "detached-work"}
    position = {commit["hash"]: index for index, commit in enumerate(snap["commits"])}
    for commit in snap["commits"]:
        assert all(position[parent] > position[commit["hash"]] for parent in commit["parents"])
    merge = next(commit for commit in snap["commits"] if commit["subject"].startswith("Merge"))
    assert merge["parents"] == [rev(repo, "main~1"), rev(repo, "feature")]
    assert snap["commits"][0]["subject"] == "detached-work"


def test_refs_list_branches_remote_tracking_branches_and_tags_peeled_to_their_commit(tmp_path: Path) -> None:
    origin = new_repo(tmp_path, "git commit -q --allow-empty -m one && git tag v1 && git tag -a v2 -m 'Release 2'")
    shell(tmp_path, "git clone -q project clone")
    clone = tmp_path / "clone"
    shell(clone, "git branch topic")
    commit = rev(origin, "HEAD")
    assert repomap.snapshot(clone)["refs"] == [
        {"name": "main", "kind": "branch", "target": commit},
        {"name": "topic", "kind": "branch", "target": commit},
        {"name": "origin/main", "kind": "remote", "target": commit},
        {"name": "v1", "kind": "tag", "target": commit},
        {"name": "v2", "kind": "tag", "target": commit},
    ]


def test_a_merge_conflict_flags_the_path_and_shows_the_merge_in_progress(tmp_path: Path) -> None:
    repo = new_repo(
        tmp_path,
        "echo base > a.txt && git add a.txt && git commit -q -m base && git switch -q -c feature\n"
        "echo theirs > a.txt && git commit -q -am theirs && git switch -q main && echo ours > a.txt && git commit -q -am ours\n"
        "git merge -q feature >/dev/null || true\n",
    )
    snap = repomap.snapshot(repo)
    assert snap["operation"] == "merge"
    assert snap["branch"] == "main"
    conflicted = entry(snap, "a.txt")
    assert conflicted["conflicted"]
    assert conflicted["index"] is None
    assert conflicted["head"] == blob_id(b"ours\n")
    assert conflicted["folder"] == blob_id((repo / "a.txt").read_bytes())


def conflicting_branches(tmp_path: Path) -> Path:
    """
    Build a repository whose ``main`` and ``feature`` change the same line of ``a.txt``.

    Parameters
    ----------
    tmp_path : Path
        The test's folder.

    Returns
    -------
    Path
        The repository, on ``main``.
    """
    return new_repo(
        tmp_path,
        "echo 1 > a.txt && git add a.txt && git commit -q -m one && git switch -q -c feature\n"
        "echo feature > a.txt && git commit -q -am feature && git switch -q main && echo 2 > a.txt && git commit -q -am two\n",
    )


@pytest.mark.parametrize(
    ("command", "operation"),
    [
        ("git switch -q feature && git rebase -q main", "rebase"),
        ("git cherry-pick feature", "cherry-pick"),
        ("git revert --no-edit HEAD~1", "revert"),
        ("git bisect start", "bisect"),
    ],
)
def test_an_operation_in_progress_is_named(tmp_path: Path, command: str, operation: str) -> None:
    repo = conflicting_branches(tmp_path)
    shell(repo, f"{command} >/dev/null 2>&1 || true")
    assert repomap.snapshot(repo)["operation"] == operation


def test_the_stash_is_counted_and_its_commits_stay_off_the_map(tmp_path: Path) -> None:
    repo = new_repo(
        tmp_path,
        "echo 1 > a.txt && git add a.txt && git commit -q -m one\n"
        "echo 2 > a.txt && git stash -q && echo 3 > a.txt && git stash -q\n",
    )
    snap = repomap.snapshot(repo)
    assert snap["stash"] == 2
    assert [commit["subject"] for commit in snap["commits"]] == ["one"]
    assert [ref["name"] for ref in snap["refs"]] == ["main"]


def test_a_bare_repository_has_refs_and_commits_but_no_files(tmp_path: Path) -> None:
    new_repo(tmp_path, "echo 1 > a.txt && git add a.txt && git commit -q -m one")
    shell(tmp_path, "git clone -q --bare project github.git")
    snap = repomap.snapshot(tmp_path / "github.git")
    assert snap["bare"]
    assert snap["exists"]
    assert snap["branch"] == "main"
    assert snap["head"] == rev(tmp_path / "project", "HEAD")
    assert [commit["subject"] for commit in snap["commits"]] == ["one"]
    assert snap["files"] == []


def test_odd_file_names_keep_their_blob_ids(tmp_path: Path) -> None:
    repo = new_repo(tmp_path)
    names = [b"with space.txt", b"caf\xe9.txt", b"new\nline.txt", b"tab\there", b'"quoted".txt', b"back\\slash", "ünï.txt".encode(), b"HEAD"]
    for name in names:
        (repo / os.fsdecode(name)).write_bytes(name)
    shell(repo, "git add -A && git commit -q -m odd")
    snap = repomap.snapshot(repo)
    for name in names:
        assert areas(snap, name.decode("utf-8", errors="replace")) == (blob_id(name), blob_id(name), blob_id(name))
    assert snap["commits"][0]["subject"] == "odd"


def test_a_symlink_has_the_blob_id_git_stores_for_the_link_itself(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo text > target.txt && ln -s target.txt link && ln -s nowhere dangling && git add -A && git commit -q -m links")
    (repo / "untracked-link").symlink_to("target.txt")
    snap = repomap.snapshot(repo)
    assert entry(snap, "link")["folder"] == entry(snap, "link")["head"] == blob_id(b"target.txt")
    assert entry(snap, "dangling")["folder"] == entry(snap, "dangling")["index"] == blob_id(b"nowhere")
    assert entry(snap, "untracked-link")["folder"] == blob_id(b"target.txt")


def test_a_link_deleted_while_it_is_read_has_no_folder_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = new_repo(tmp_path, "echo a > a.txt && ln -s a.txt link")

    def vanished(path: bytes) -> bytes:
        raise FileNotFoundError(path)

    monkeypatch.setattr(os, "readlink", vanished)
    snap = repomap.snapshot(repo)
    assert entry(snap, "link")["folder"] is None
    assert entry(snap, "a.txt")["folder"] == blob_id(b"a\n")


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read any file")
def test_a_file_git_cannot_read_has_no_folder_id_and_the_others_still_do(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo a > a.txt && echo b > b.txt && echo c > c.txt && git add . && git commit -q -m abc && chmod 000 b.txt")
    snap = repomap.snapshot(repo)
    assert entry(snap, "a.txt")["folder"] == blob_id(b"a\n")
    assert entry(snap, "b.txt")["folder"] is None
    assert entry(snap, "c.txt")["folder"] == blob_id(b"c\n")


def test_a_large_binary_file_gets_its_blob_id(tmp_path: Path) -> None:
    repo = new_repo(tmp_path)
    data = os.urandom(5 * 1024 * 1024)
    (repo / "big.bin").write_bytes(data)
    assert entry(repomap.snapshot(repo), "big.bin")["folder"] == blob_id(data)


def test_a_file_replaced_by_a_folder_is_missing_from_the_folder(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo a > a && git add a && git commit -q -m a && rm a && mkdir a && echo b > a/b")
    snap = repomap.snapshot(repo)
    assert entry(snap, "a")["folder"] is None
    assert entry(snap, "a/b")["folder"] == blob_id(b"b\n")


def test_a_tracked_file_replaced_by_a_named_pipe_has_no_folder_id(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo a > a && git add a && git commit -q -m a && rm a && mkfifo a")
    assert entry(repomap.snapshot(repo), "a")["folder"] is None


def test_a_file_named_like_a_commit_hides_no_history(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "git commit -q --allow-empty -m one && touch $(git rev-parse HEAD)")
    assert [commit["subject"] for commit in repomap.snapshot(repo)["commits"]] == ["one"]


def test_a_nested_repository_is_left_out_of_the_files(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo a > a.txt && git init -q inner && echo b > inner/b.txt")
    assert [file["path"] for file in repomap.snapshot(repo)["files"]] == ["a.txt"]


def test_a_nested_repository_added_as_a_submodule_is_left_out_of_the_files(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "git init -q inner && git -C inner commit -q --allow-empty -m inner && git add inner && git commit -q -m outer")
    snap = repomap.snapshot(repo)
    assert snap["files"] == []
    assert [commit["subject"] for commit in snap["commits"]] == ["outer"]


def test_a_repository_one_folder_too_high_is_not_the_folders_own(tmp_path: Path) -> None:
    shell(tmp_path, "git init -q -b main && mkdir project")
    assert repomap.snapshot(tmp_path / "project") == NOTHING
    assert repomap.objects(tmp_path / "project") == []


def test_a_subfolder_of_a_repository_holds_no_repository_of_its_own(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "mkdir docs && echo a > docs/a.txt && git add . && git commit -q -m one")
    assert repomap.snapshot(repo / "docs") == NOTHING


def test_the_git_folder_itself_holds_no_repository_of_its_own(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "git commit -q --allow-empty -m one")
    assert repomap.snapshot(repo / ".git") == NOTHING


def test_a_folder_inside_a_bare_repository_holds_no_repository_of_its_own(tmp_path: Path) -> None:
    shell(tmp_path, "git init -q --bare github.git")
    assert repomap.snapshot(tmp_path / "github.git" / "refs") == NOTHING


def test_a_link_to_a_repository_shows_that_repository(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "git commit -q --allow-empty -m one")
    (tmp_path / "link").symlink_to(repo)
    assert repomap.snapshot(tmp_path / "link") == repomap.snapshot(repo)


@pytest.mark.parametrize("part", ["HEAD", "objects", "refs"])
def test_a_git_folder_missing_a_vital_part_holds_no_repository(tmp_path: Path, part: str) -> None:
    repo = new_repo(tmp_path, f"git commit -q --allow-empty -m one && rm -r .git/{part}")
    assert repomap.snapshot(repo) == NOTHING


def test_an_empty_git_folder_holds_no_repository(tmp_path: Path) -> None:
    (tmp_path / "project" / ".git").mkdir(parents=True)
    assert repomap.snapshot(tmp_path / "project") == NOTHING


def test_a_deleted_index_shows_committed_files_as_staged_for_deletion_and_untracked(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo a > a.txt && git add a.txt && git commit -q -m one && rm .git/index")
    assert entry(repomap.snapshot(repo), "a.txt") == {
        "path": "a.txt",
        "head": blob_id(b"a\n"),
        "index": None,
        "folder": blob_id(b"a\n"),
        "ignored": False,
        "conflicted": False,
    }


def test_a_missing_commit_object_leaves_what_git_cannot_read_empty(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo a > a.txt && git add a.txt && git commit -q -m one")
    head = rev(repo, "HEAD")
    (repo / ".git" / "objects" / head[:2] / head[2:]).unlink()
    snap = repomap.snapshot(repo)
    assert snap["exists"]
    assert snap["branch"] == "main"
    assert snap["commits"] == []
    assert entry(snap, "a.txt")["head"] is None
    assert entry(snap, "a.txt")["index"] == blob_id(b"a\n")


def test_a_snapshot_changes_nothing_in_the_repository(tmp_path: Path) -> None:
    repo = new_repo(
        tmp_path,
        "echo a > a.txt && echo b > b.txt && git add . && git commit -q -m one\n"
        "touch -d '2000-01-01' .git/index && echo changed > a.txt && touch b.txt && echo new > c.txt\n",
    )

    def state() -> dict[str, tuple[int, bytes]]:
        return {str(path): (path.stat().st_mtime_ns, path.read_bytes()) for path in (repo / ".git").rglob("*") if path.is_file()}

    before = state()
    repomap.snapshot(repo)
    assert state() == before


def test_commits_beyond_the_limit_are_cut_newest_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(repomap, "MAX_COMMITS", 2)
    repo = new_repo(tmp_path, "for n in 1 2 3; do git commit -q --allow-empty -m $n; done")
    snap = repomap.snapshot(repo)
    assert [commit["subject"] for commit in snap["commits"]] == ["3", "2"]
    assert snap["truncated"]


def test_files_beyond_the_limit_are_cut_ignored_files_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(repomap, "MAX_FILES", 3)
    repo = new_repo(tmp_path, "echo '*.log' > .gitignore && echo x > a.log && echo x > b.txt && echo x > c.txt")
    snap = repomap.snapshot(repo)
    assert [file["path"] for file in snap["files"]] == [".gitignore", "b.txt", "c.txt"]
    assert snap["truncated"]


def test_a_repository_within_the_limits_is_not_truncated(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "echo x > a.txt && git add . && git commit -q -m one")
    assert not repomap.snapshot(repo)["truncated"]


file_names = st.binary(min_size=1, max_size=12).filter(lambda name: b"/" not in name and b"\0" not in name and name.lower() not in {b".", b"..", b".git"})


@pytest.mark.slow
@settings(max_examples=40, deadline=None)
@given(name=file_names, content=st.binary(max_size=64))
def test_any_file_name_shows_with_the_blob_id_git_would_store(name: bytes, content: bytes) -> None:
    with tempfile.TemporaryDirectory() as folder:
        repo = new_repo(Path(folder))
        (repo / os.fsdecode(name)).write_bytes(content)
        snap = repomap.snapshot(repo)
    assert entry(snap, name.decode("utf-8", errors="replace"))["folder"] == blob_id(content)


def test_objects_lists_every_object_with_its_type_and_size_sorted_by_hash(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "printf 'hello\\n' > hello.txt && git add hello.txt && git commit -q -m 'Say hello' && echo loose | git hash-object -w --stdin >/dev/null")
    found = repomap.objects(repo)
    assert [obj["hash"] for obj in found] == sorted(obj["hash"] for obj in found)
    assert {(obj["hash"], obj["type"]) for obj in found} == {
        (HELLO, "blob"),
        (blob_id(b"loose\n"), "blob"),
        (rev(repo, "HEAD^{tree}"), "tree"),
        (rev(repo, "HEAD"), "commit"),
    }
    assert next(obj for obj in found if obj["hash"] == HELLO)["size"] == 6


def test_objects_lists_annotated_tags(tmp_path: Path) -> None:
    repo = new_repo(tmp_path, "git commit -q --allow-empty -m one && git tag -a v1 -m 'Release 1'")
    assert {obj["type"] for obj in repomap.objects(repo)} == {"commit", "tree", "tag"}


def test_objects_of_a_folder_without_a_repository_is_empty(tmp_path: Path) -> None:
    assert repomap.objects(tmp_path / "missing") == []
    assert repomap.objects(tmp_path) == []
