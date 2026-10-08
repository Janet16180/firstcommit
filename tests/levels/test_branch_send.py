from firstcommit import kit
from firstcommit.levels import branch_send as level
from level_helpers import reaction, started, typed_in, watch


def test_a_plain_push_on_main_leaves_scout_here() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push")
    assert typed[0]["status"] == 0
    assert kit.git_run(lab.github, "rev-parse", "-q", "--verify", "refs/heads/scout").returncode == 1
    assert watch(level, "send").watch(lab, state, typed).message == level.NOT_SENT


def test_pushing_scout_by_name_from_main_sends_it_and_leaves_the_mothership_main_alone() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push", "git push -u origin scout", "git branch -r")
    assert kit.git(lab.github, "rev-parse", "scout") == kit.git(lab.project, "rev-parse", "scout")
    assert kit.git(lab.github, "rev-parse", "main").strip() == state["main"]
    assert kit.git(lab.project, "rev-parse", "--abbrev-ref", "scout@{upstream}").strip() == "origin/scout"
    assert level.check(lab, state, None, typed).solved


def test_a_plain_push_on_scout_fails_and_rama_names_the_branch_to_push() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch scout", "git push")
    assert typed[1]["status"] == 128
    rule = reaction(level, typed[1], set(), True, False)
    assert rule is not None and rule.text == level.NO_UPSTREAM


def test_a_survey_merged_and_pushed_to_main_is_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git merge scout", "git push")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.MAIN_MOVED)


def test_a_list_typed_before_the_push_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push", "git branch -r", "git push -u origin scout")
    assert level.check(lab, state, None, typed).message == level.NOT_LISTED
