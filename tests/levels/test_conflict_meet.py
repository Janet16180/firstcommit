from firstcommit import kit
from firstcommit.levels import conflict_meet as level
from level_helpers import started, typed_in, watch


def test_main_and_alexs_scout_have_each_moved_on_since_they_parted() -> None:
    lab, state = started(level)
    base = kit.git(lab.project, "merge-base", "main", "scout").strip()
    assert base not in (kit.git(lab.project, "rev-parse", "main").strip(), state["scout"])
    assert kit.git(lab.project, "log", "-1", "--format=%an", "scout").strip() == "Alex"


def test_the_prediction_reveal_recalls_the_fast_forward_of_4_3() -> None:
    assert len(level.GUESS.options) == 3
    assert "Incoming transmission" in level.GUESS.reveal


def test_merging_scout_makes_one_commit_with_two_parents_that_keeps_both_changes_and_both_labels() -> None:
    lab, state = started(level)
    commits = int(kit.git(lab.project, "rev-list", "--count", "--all"))
    typed = typed_in(lab, "git merge --no-edit scout", "git log --oneline --graph")
    assert int(kit.git(lab.project, "rev-list", "--count", "--all")) == commits + 1
    assert len(kit.git(lab.project, "log", "-1", "--format=%P").split()) == 2
    assert (lab.project / "crew.txt").read_text() == "Robin\nAlex\n"
    assert (lab.project / "route.txt").read_text() == "Route: Earth, Moon, Mars\n"
    assert kit.git(lab.project, "rev-parse", "scout").strip() == state["scout"]
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.LOOKED)


def test_a_paused_merge_is_named_with_both_ways_on() -> None:
    lab, state = started(level)
    kit.git(lab.project, "merge", "--no-commit", "--no-ff", "scout")
    assert watch(level, "merge").watch(lab, state, []).message == level.PAUSED


def test_a_graph_drawn_before_the_merge_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline --graph", "git merge --no-edit scout")
    assert level.check(lab, state, None, typed).message == level.NOT_LOOKED
