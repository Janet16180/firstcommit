from firstcommit import kit
from firstcommit.levels import conflict_meet as level
from level_helpers import started, typed_in, watch


def test_merging_beacon_first_makes_no_commit_and_only_slides_main() -> None:
    lab, state = started(level)
    commits = kit.git(lab.project, "rev-list", "--count", "--all")
    typed_in(lab, "git merge beacon")
    assert kit.git(lab.project, "rev-list", "--count", "--all") == commits
    assert kit.git(lab.project, "rev-parse", "main").strip() == state["beacon"]
    assert watch(level, "forward").watch(lab, state, []).message == level.FORWARDED


def test_merging_scout_makes_a_commit_with_two_parents_that_keeps_both_changes() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git merge beacon", "git merge --no-edit scout", "git log --oneline --graph")
    assert len(kit.git(lab.project, "log", "-1", "--format=%P").split()) == 2
    assert (lab.project / "crew.txt").read_text() == "Robin\nAlex\n"
    assert (lab.project / "route.txt").read_text() == "Route: Earth, Moon, Mars\n"
    assert level.check(lab, state, None, typed).solved


def test_merging_scout_first_brings_beacon_in_by_a_merge_commit_and_the_level_offers_to_start_again() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git merge --no-edit scout", "git merge --no-edit beacon")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.MERGED_BEACON)


def test_a_graph_drawn_before_the_merge_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git merge beacon", "git log --oneline --graph", "git merge --no-edit scout")
    assert level.check(lab, state, None, typed).message == level.NOT_LOOKED
