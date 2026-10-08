from pathlib import Path

from firstcommit import kit
from firstcommit.levels import names_tags as level
from level_helpers import reaction, started, typed_in, watch

COMMIT = 'git commit -am "Note the fuel level"'


def tip(path: Path, ref: str) -> str:
    """
    Give the commit a ref points at.

    Parameters
    ----------
    path : Path
        The repository.
    ref : str
        The ref.

    Returns
    -------
    str
        Its hash.
    """
    return kit.git(path, "rev-parse", ref).strip()


def test_main_and_the_bookmark_share_the_newest_of_three_commits_and_test_run_names_the_first() -> None:
    lab, state = started(level)
    assert kit.git(lab.project, "log", "--format=%s", "main").splitlines() == ["Add the crew list", "Plot the route", "Start the project"]
    assert tip(lab.project, "origin/main") == tip(lab.project, "main") == tip(lab.github, "main")
    assert tip(lab.project, "test-run") == tip(lab.project, "main~2")
    assert kit.git(lab.project, "status", "--porcelain").strip() == "M notes.txt"


def test_a_commit_moves_only_main_and_the_bookmark_waits_for_the_mothership() -> None:
    lab, state = started(level)
    before = {ref: tip(lab.project, ref) for ref in ("test-run", "origin/main")}
    typed_in(lab, COMMIT)
    assert {ref: tip(lab.project, ref) for ref in before} == before
    assert tip(lab.project, "main~1") == before["origin/main"]


def test_alex_pushes_a_fix_inside_your_push_so_the_mothership_moves_on_and_your_bookmark_stays() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git branch -v", COMMIT, "git log --oneline", "git push")
    assert watch(level, "push").watch(lab, state, typed).message == level.PUSHED
    assert kit.git(lab.github, "log", "-1", "--format=%an %s", "main").strip() == "Alex Fix the route"
    assert tip(lab.project, "origin/main") == tip(lab.project, "main") == tip(lab.github, "main~1")
    assert watch(level, "fetch").watch(lab, state, typed).message == level.NOT_FETCHED


def test_a_fetch_brings_the_bookmark_up_and_status_says_main_is_one_behind() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git branch -v", COMMIT, "git log --oneline", "git push", "git fetch")
    assert tip(lab.project, "origin/main") == tip(lab.github, "main") != tip(lab.project, "main")
    assert not (lab.project / "route.txt").read_text().endswith("Phobos\n")
    typed += typed_in(lab, "git status")
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.STATUS_READ)


def test_a_pull_instead_of_the_fetch_passes_the_last_two_goals_too() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git branch -v", COMMIT, "git log --oneline", "git push", "git pull", "git status")
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.STATUS_PULLED)


def test_a_status_read_before_the_fetch_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git branch -v", COMMIT, "git log --oneline", "git push", "git status", "git fetch")
    assert level.check(lab, state, None, typed).message == level.NOT_STATUS


def test_rama_reads_git_branch_v_aloud() -> None:
    lab, state = started(level)
    for line in ("git branch -v", "git branch -vv", "git branch --verbose"):
        rule = reaction(level, typed_in(lab, line)[-1], set(), True, False)
        assert rule is not None and rule.text == level.LISTS_NAMES, line
    assert reaction(level, typed_in(lab, "git branch -d test-run")[-1], set(), True, False) is None
