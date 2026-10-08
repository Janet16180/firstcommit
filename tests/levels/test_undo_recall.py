from firstcommit import kit
from firstcommit.levels import undo_recall as level
from level_helpers import reached, reaction, started, typed_in, watch

RECALL = ["git log --oneline", "git revert HEAD~1", "git push"]


def test_the_strobe_commit_is_on_the_mothership_and_at_alexs_with_a_good_commit_after_it() -> None:
    lab, state = started(level)
    assert kit.git(lab.github, "rev-parse", "main").strip() == state["main"]
    assert (lab.teammate / "lights.cfg").read_text() == level.STROBE
    assert kit.git(lab.project, "log", "-1", "--format=%s", "HEAD~1").strip() == level.BAD_MESSAGE


def test_reverting_the_strobe_commit_and_pushing_solves_the_level_and_keeps_the_history() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *RECALL)
    assert [line["status"] for line in typed] == [0, 0, 0]
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.PUSHED)
    assert (lab.project / "lights.cfg").read_text() == level.STEADY
    assert (lab.project / "route.txt").is_file()
    assert kit.is_ancestor(lab.project, state["main"], "main")


def test_once_the_revert_reaches_the_mothership_alex_pulls_it_and_alexs_lights_are_steady() -> None:
    lab, state = started(level)
    typed_in(lab, *RECALL)
    reached(level, lab, state, "push")
    assert (lab.teammate / "lights.cfg").read_text() == level.STEADY


def test_the_level_waits_for_a_look_at_the_history() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git revert HEAD~1", "git push")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_LOOKED)


def test_a_revert_not_pushed_yet_is_named() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git revert HEAD~1")
    assert watch(level, "revert").watch(lab, state, typed) == kit.Verdict(True, level.REVERTED)
    assert watch(level, "push").watch(lab, state, typed).message == level.NOT_PUSHED


def test_a_reset_on_main_warns_with_the_force_break_and_a_pull_brings_main_back() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git reset --hard HEAD~2")
    rule = reaction(level, typed[0], {"branch-moved"}, True, False, branch="main")
    assert rule is not None and (rule.mood, rule.text, rule.moment) == ("warn", level.RESET_SHARED, "force-break")
    assert watch(level, "revert").watch(lab, state, typed).message == level.BEHIND
    typed += typed_in(lab, "git pull", *RECALL)
    assert level.check(lab, state, None, typed).solved


def test_a_forced_push_that_drops_the_shared_commits_is_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git reset --hard HEAD~2", "git push --force")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.REWRITTEN)
