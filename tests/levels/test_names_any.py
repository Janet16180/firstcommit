from firstcommit import kit
from firstcommit.levels import _names_story as story
from firstcommit.levels import names_any as level
from level_helpers import reaction, started, typed_in, watch


def test_the_state_names_plot_the_routes_hash_for_the_hint() -> None:
    lab, state = started(level)
    assert kit.git(lab.project, "log", "-1", "--format=%s", state["route"]).strip() == "Plot the route"


def test_taking_test_run_off_keeps_its_commit_in_main_s_history() -> None:
    lab, state = started(level)
    first = kit.git(lab.project, "rev-parse", story.OLD_NAME).strip()
    typed = typed_in(lab, "git log --oneline", f"git branch -d {story.OLD_NAME}")
    assert watch(level, "delete").watch(lab, state, typed).message == level.DELETED
    assert kit.is_ancestor(lab.project, first, "main")


def test_a_name_on_plot_the_route_leaves_head_and_the_folder_where_they_were() -> None:
    lab, state = started(level)
    before = (kit.snapshot(lab.project)["branch"], (lab.project / story.ROUTE).read_text())
    typed = typed_in(lab, "git log --oneline", "git branch -d test-run", "git log --oneline", f"git branch first-route {state['route']}", "git log --oneline")
    assert (kit.snapshot(lab.project)["branch"], (lab.project / story.ROUTE).read_text()) == before
    assert level.check(lab, state, None, typed).solved


def test_a_name_on_another_commit_is_named_and_can_be_moved() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git branch -d test-run", "git log --oneline", "git branch first-route")
    assert watch(level, "name").watch(lab, state, typed).message == level.ELSEWHERE
    typed += typed_in(lab, "git branch -d first-route", f"git branch first-route {state['route']}", "git log --oneline")
    assert level.check(lab, state, None, typed).solved


def test_the_history_read_before_the_new_name_does_not_count_for_the_last_goal() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git branch -d test-run", "git log --oneline", f"git branch first-route {state['route']}")
    assert level.check(lab, state, None, typed).message == level.NOT_LOGGED_THIRD


def test_moving_onto_first_route_is_allowed_and_rama_says_how_to_come_back() -> None:
    lab, state = started(level)
    typed = typed_in(lab, f"git branch first-route {state['route']}", "git switch first-route")
    rule = reaction(level, typed[-1], {"branch-switched"}, True, False)
    assert rule is not None and rule.text == level.MOVED_ONTO
    assert not (lab.project / "crew.txt").exists()
