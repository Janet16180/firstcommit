from firstcommit import kit
from firstcommit.levels import names_chart as level
from level_helpers import reaction, started, typed_in

SOLUTION = ("git switch main", "git branch -d fuel-test", "git branch release", "git switch bright-lights", "git switch -c lights-v2")


def test_the_charts_names_cover_every_branch_but_fuel_test_and_add_release_and_lights_v2() -> None:
    lab, state = started(level)
    have = set(kit.git(lab.project, "branch", "--format=%(refname:short)").split())
    assert have - set(level.TARGET["names"]) == {"fuel-test"}
    assert set(level.TARGET["names"]) - have == {"release", "lights-v2"}


def test_taking_off_the_name_head_is_on_fails_and_rama_says_to_move_head_first() -> None:
    lab, state = started(level)
    line = typed_in(lab, "git branch -d fuel-test")[-1]
    assert line["status"] != 0
    rule = reaction(level, line, set(), True, False, branch="fuel-test")
    assert rule is not None and rule.text == level.USED_BY_WORKTREE


def test_the_hints_lines_match_the_chart_with_no_commit_changed() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *SOLUTION)
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.MATCHED)
    assert sorted(kit.git(lab.project, "rev-list", "--all").split()) == sorted(state["commits"])


def test_lights_v2_made_from_main_lands_on_the_wrong_side_line() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch main", "git branch -d fuel-test", "git branch release", "git switch -c lights-v2")
    assert level.check(lab, state, None, typed).message == level.WRONG_SIDE


def test_head_left_on_another_name_does_not_match() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *SOLUTION, "git switch main")
    assert level.check(lab, state, None, typed).message == level.NOT_MATCHED


def test_a_new_commit_is_lost() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git commit -q --allow-empty -m extra")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.COMMITS_CHANGED)
