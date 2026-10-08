from pathlib import Path

import pytest

from firstcommit import gitcmd, pulls
from firstcommit.records import PullRequest
from repo_helpers import shell

ROBIN = gitcmd.Person("Robin Park", "robin@example.com")
WHEN = "2026-09-01T09:00:00+00:00"


def hub(tmp_path: Path, branches: str = "") -> Path:
    """
    Make a bare stand-in GitHub with ``main`` and, from a clone, the branches the code pushes.

    Parameters
    ----------
    tmp_path : Path
        An empty folder.
    branches : str
        Bash code run in the clone after ``main``'s first commit is pushed.

    Returns
    -------
    Path
        The bare repository.
    """
    shell(tmp_path, "git init -q --bare hub.git && git clone -q hub.git clone 2>/dev/null")
    shell(tmp_path / "clone", "echo base > a.txt && echo d > d.txt && git add . && git commit -q -m base && git push -q origin HEAD:main 2>/dev/null\n" + branches)
    return tmp_path / "hub.git"


FIX = "git switch -q -c fix && echo fix >> a.txt && git commit -q -am 'Fix a' && git push -q origin fix 2>/dev/null"
CLASH = "git switch -q -c clash origin/main && echo clash >> a.txt && git commit -q -am 'Clash a' && git push -q origin clash 2>/dev/null"


def opened(github: Path) -> list[PullRequest]:
    """
    Open pull request 1 from ``fix`` into ``main``.

    Parameters
    ----------
    github : Path
        The stand-in GitHub, with a ``fix`` branch.

    Returns
    -------
    list[PullRequest]
        The one pull request.
    """
    return pulls.open_pull(github, [], head="fix", base="main", title="Fix a", author="you")


def test_opening_a_pull_request_numbers_it_records_it_open_and_mirrors_its_head(tmp_path: Path) -> None:
    github = hub(tmp_path, FIX)
    [pull] = opened(github)
    assert pull == {"number": 1, "title": "Fix a", "author": "you", "head": "fix", "base": "main", "state": "open", "reviews": [], "merge_commit": None}
    assert shell(github, "git rev-parse refs/pull/1/head") == shell(github, "git rev-parse fix")


def test_a_second_pull_request_gets_the_next_number(tmp_path: Path) -> None:
    github = hub(tmp_path, f"{FIX}\n{CLASH}")
    both = pulls.open_pull(github, opened(github), head="clash", base="main", title="Clash", author="alex")
    assert [pull["number"] for pull in both] == [1, 2]


@pytest.mark.parametrize(("head", "base"), [("nope", "main"), ("fix", "nope"), ("main", "main"), ("fix", "main")])
def test_a_pull_request_needs_two_different_branches_and_none_already_open_for_them(tmp_path: Path, head: str, base: str) -> None:
    github = hub(tmp_path, FIX)
    existing = opened(github) if (head, base) == ("fix", "main") else []
    with pytest.raises(ValueError, match="branch|already"):
        pulls.open_pull(github, existing, head=head, base=base, title="T", author="you")


def test_a_branch_that_merges_cleanly_is_mergeable_and_one_that_clashes_names_the_file(tmp_path: Path) -> None:
    github = hub(tmp_path, f"{FIX}\n{CLASH}")
    assert pulls.mergeability(github, "main", "fix") == (True, [])
    assert pulls.mergeability(github, "fix", "clash") == (False, ["a.txt"])


def test_merging_makes_a_commit_with_two_parents_on_the_base_and_records_it(tmp_path: Path) -> None:
    github = hub(tmp_path, FIX)
    main = shell(github, "git rev-parse main").strip()
    fix = shell(github, "git rev-parse fix").strip()
    [merged] = pulls.merge(github, opened(github), 1, ROBIN, WHEN)
    tip = shell(github, "git rev-parse main").strip()
    assert (merged["state"], merged["merge_commit"]) == ("merged", tip)
    assert shell(github, "git log -1 --format=%P main").split() == [main, fix]
    assert shell(github, "git log -1 --format=%s main").strip() == "Merge pull request #1 from moonbase/fix"
    assert shell(github, "git show main:a.txt") == "base\nfix\n"


def test_a_pull_request_that_conflicts_with_its_base_is_not_merged(tmp_path: Path) -> None:
    github = hub(tmp_path, f"{FIX}\n{CLASH}")
    shell(tmp_path / "clone", "git push -q origin clash:main 2>/dev/null")
    main = shell(github, "git rev-parse main")
    with pytest.raises(ValueError, match="conflict"):
        pulls.merge(github, opened(github), 1, ROBIN, WHEN)
    assert shell(github, "git rev-parse main") == main


def test_only_an_open_pull_request_can_be_reviewed_or_merged(tmp_path: Path) -> None:
    github = hub(tmp_path, FIX)
    merged = pulls.merge(github, opened(github), 1, ROBIN, WHEN)
    with pytest.raises(ValueError, match="not open"):
        pulls.merge(github, merged, 1, ROBIN, WHEN)
    with pytest.raises(ValueError, match="not open"):
        pulls.review(merged, 1, reviewer="Robin", verdict="approved", body="", commit="")
    with pytest.raises(KeyError):
        pulls.review(merged, 7, reviewer="Robin", verdict="approved", body="", commit="")


def test_a_review_is_kept_with_the_commit_it_saw_and_turns_outdated_when_the_branch_moves(tmp_path: Path) -> None:
    github = hub(tmp_path, FIX)
    seen = shell(github, "git rev-parse fix").strip()
    reviewed = pulls.review(opened(github), 1, reviewer="Robin", verdict="changes-requested", body="Name the file.", commit=seen)
    assert reviewed[0]["reviews"] == [{"reviewer": "Robin", "verdict": "changes-requested", "body": "Name the file.", "commit": seen}]
    [view] = pulls.board(github, reviewed)
    assert view["reviews"][0]["outdated"] is False
    shell(tmp_path / "clone", "git switch -q fix && echo more >> a.txt && git commit -q -am more && git push -q origin fix 2>/dev/null")
    pulls.mirror(github, reviewed)
    [view] = pulls.board(github, reviewed)
    assert view["reviews"][0]["outdated"] is True
    assert shell(github, "git rev-parse refs/pull/1/head") == shell(github, "git rev-parse fix")


def test_the_board_shows_a_pull_requests_commits_files_and_mergeability(tmp_path: Path) -> None:
    github = hub(tmp_path, FIX)
    [view] = pulls.board(github, opened(github))
    assert (view["number"], view["state"], view["mergeable"], view["conflicts"], view["files"]) == (1, "open", True, [], ["a.txt"])
    assert [commit["subject"] for commit in view["commits"]] == ["Fix a"]
    assert view["head_commit"] == shell(github, "git rev-parse fix").strip()


def test_a_merged_pull_request_keeps_its_commits_on_the_board_after_its_branch_is_deleted(tmp_path: Path) -> None:
    github = hub(tmp_path, FIX)
    merged = pulls.merge(github, opened(github), 1, ROBIN, WHEN)
    shell(github, "git update-ref -d refs/heads/fix")
    [view] = pulls.board(github, merged)
    assert (view["state"], view["mergeable"], [commit["subject"] for commit in view["commits"]]) == ("merged", True, ["Fix a"])
