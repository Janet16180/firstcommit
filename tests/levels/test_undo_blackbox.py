from firstcommit import kit
from firstcommit.levels import undo_blackbox as level
from level_helpers import reaction, started, typed_in

RESCUE = ["git reflog", "git branch thrusters HEAD@{1}", "git push -u origin thrusters"]


def test_the_thrusters_branch_is_gone_and_its_commits_are_ghosts() -> None:
    lab, state = started(level)
    assert kit.git_run(lab.project, "rev-parse", "-q", "--verify", "refs/heads/thrusters").returncode == 1
    assert [ghost["hash"] for ghost in kit.ghosts(lab.project)][0] == state["tip"]
    assert level.check(lab, state, None, []).message == level.NOT_RESCUED


def test_the_reflog_then_a_label_and_a_push_solve_the_level() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *RESCUE)
    assert [line["status"] for line in typed] == [0, 0, 0]
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.LAUNCHED)
    assert kit.git(lab.github, "rev-parse", "thrusters").strip() == state["tip"]
    assert kit.git(lab.github, "rev-parse", "main").strip() == state["main"]


def test_the_goals_pass_in_either_order_once_both_are_met() -> None:
    lab, state = started(level)
    typed = typed_in(lab, f"git push origin {state['tip']}:refs/heads/thrusters")
    assert level.check(lab, state, None, typed).message == level.NOT_RESCUED
    typed += typed_in(lab, f"git branch thrusters {state['tip']}")
    assert level.check(lab, state, None, typed).solved


def test_a_label_on_only_the_first_commit_is_not_enough() -> None:
    lab, state = started(level)
    typed = typed_in(lab, f"git branch thrusters {state['tip']}~1")
    assert level.check(lab, state, None, typed).message == level.NOT_RESCUED


def test_the_rescued_commits_pushed_to_main_skip_review_and_are_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch thrusters HEAD@{1}", "git push origin thrusters:main")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.MAIN_TOUCHED)


def test_wiping_the_black_box_warns_and_erasing_the_commits_is_lost() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git reflog expire --expire=now --all", "git gc -q --prune=now")
    rule = reaction(level, typed[0], set(), True, False)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.WIPE)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.ERASED)
