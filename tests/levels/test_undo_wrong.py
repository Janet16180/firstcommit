from firstcommit import kit
from firstcommit.levels import undo_wrong as level
from level_helpers import reaction, started, typed_in, watch

FIX = ["git branch rescue", "git reset --hard origin/main", "git log --oneline"]


def test_two_commits_sit_on_main_and_not_on_the_mothership() -> None:
    lab, state = started(level)
    assert kit.git(lab.project, "rev-list", "--count", "origin/main..main").strip() == "2"
    assert kit.git(lab.github, "rev-parse", "main").strip() == state["origin"]


def test_a_branch_a_reset_and_a_look_at_the_history_solve_the_level_and_the_commits_stay_on_rescue() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *FIX)
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.LOGGED)
    assert kit.git(lab.project, "log", "--oneline").strip().count("\n") == 0
    assert kit.git(lab.project, "rev-parse", "rescue").strip() == state["tip"]
    assert kit.git(lab.project, "rev-parse", "main").strip() == state["origin"]
    assert not (lab.project / level.SURVEY).exists()


def test_a_reset_first_leaves_ghosts_and_a_label_on_the_old_tip_brings_them_back() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git reset --hard origin/main")
    assert [ghost["hash"] for ghost in kit.ghosts(lab.project)][0] == state["tip"]
    assert watch(level, "rescue").watch(lab, state, typed).message == level.GHOSTS
    rule = reaction(level, typed[0], {"branch-moved"}, True, False)
    assert rule is not None and (rule.mood, rule.text) == ("info", level.MOVED_BACK)
    typed += typed_in(lab, "git branch rescue HEAD@{1}", "git log --oneline")
    assert level.check(lab, state, None, typed).solved
    assert kit.ghosts(lab.project) == []


def test_until_main_is_back_the_goal_says_how() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch rescue")
    assert watch(level, "rescue").watch(lab, state, typed) == kit.Verdict(True, level.LABELLED)
    assert watch(level, "reset").watch(lab, state, typed).message == level.NOT_RESET


def test_pushing_the_two_commits_to_the_mothership_is_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.SHARED)


def test_every_prediction_passes_with_the_reveal() -> None:
    for option in level.GUESS.options:
        assert kit.choose(level.GUESS, option) == kit.Verdict(True, level.GUESS.reveal)


def test_a_history_read_before_the_reset_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch rescue", "git log --oneline", "git reset --hard origin/main")
    assert level.check(lab, state, None, typed).message == level.NOT_LOGGED
