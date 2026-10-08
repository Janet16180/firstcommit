from firstcommit import kit
from firstcommit.levels import names_step as level
from level_helpers import started, typed_in, watch

COMMIT = 'git add dim.txt && git commit -m "Try dim lights"'
GRAPH = "git log --oneline --graph --all"


def test_switch_c_makes_the_name_on_mains_commit_and_moves_head_onto_it_without_a_commit() -> None:
    lab, state = started(level)
    main = kit.git(lab.project, "rev-parse", "main").strip()
    typed = typed_in(lab, "git switch -c dim-lights")
    assert (kit.snapshot(lab.project)["branch"], kit.git(lab.project, "rev-parse", "dim-lights").strip()) == ("dim-lights", main)
    assert watch(level, "make").watch(lab, state, typed).message == level.MADE


def test_two_commands_in_place_of_the_one_step_do_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch dim-lights", "git switch dim-lights")
    assert watch(level, "make").watch(lab, state, typed).message == level.NOT_MADE


def test_the_commit_grows_a_third_side_line_off_main() -> None:
    lab, state = started(level)
    typed_in(lab, "git switch -c dim-lights", COMMIT)
    tips = [kit.git(lab.project, "rev-parse", f"{branch}~1").strip() for branch in ("bright-lights", "quiet-engine", "dim-lights")]
    assert tips == [kit.git(lab.project, "rev-parse", "main").strip()] * 3


def test_dim_txt_committed_on_main_is_named_and_lost() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch -c dim-lights", "git switch main", COMMIT)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.DIM_ON_MAIN)


def test_the_newer_forms_count_for_the_older_ways_steps_too() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git checkout -b dim-lights", COMMIT, GRAPH, "git switch quiet-engine", "git switch -c night-watch", "git branch -v")
    assert level.check(lab, state, None, typed).solved
    assert kit.git(lab.project, "rev-parse", "night-watch").strip() == kit.git(lab.project, "rev-parse", "quiet-engine").strip()


def test_the_list_typed_before_night_watch_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch -c dim-lights", COMMIT, GRAPH, "git checkout quiet-engine", "git branch -v", "git checkout -b night-watch")
    assert level.check(lab, state, None, typed).message == level.NOT_LISTED
