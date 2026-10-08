from firstcommit import kit
from firstcommit.levels import mothership_launch as level
from level_helpers import reaction, started, typed_in, watch

PATH = ["git push -u origin main", 'echo "Stop: Phobos" >> route.txt', "git push", 'git commit -am "Add the Phobos stop"', "git push"]


def test_the_level_starts_with_origin_set_and_an_empty_mothership() -> None:
    lab, _ = started(level)
    assert kit.git(lab.project, "remote", "get-url", "origin").strip() == "../github/project.git"
    assert kit.snapshot(lab.github)["refs"] == []


def test_the_whole_launch_solves_the_level_and_the_mothership_matches() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *PATH)
    assert [line["status"] for line in typed] == [0, 0, 0, 0, 0]
    assert level.check(lab, state, None, typed).solved
    assert kit.git(lab.project, "rev-parse", "main").strip() == kit.git(lab.github, "rev-parse", "main").strip()


def test_a_plain_first_push_stops_and_rama_names_the_first_push() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push")
    assert typed[0]["status"] == 128
    rule = reaction(level, typed[0], set(), True, False)
    assert rule is not None and rule.text == level.NO_UPSTREAM
    assert watch(level, "launch").watch(lab, state, typed).message == level.NOT_LAUNCHED


def test_a_push_without_upstream_is_asked_to_set_one() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push origin main")
    assert watch(level, "launch").watch(lab, state, typed).message == level.NO_UPSTREAM_SET


def test_the_push_with_the_edit_in_no_commit_sends_nothing_new() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *PATH[:3])
    assert watch(level, "fizzle").watch(lab, state, typed).solved
    assert kit.git(lab.github, "show", "main:route.txt") == "Route: Earth, Moon, Mars\n"
    assert not watch(level, "send").watch(lab, state, typed).solved


def test_committing_and_pushing_before_the_empty_push_skips_the_lesson_and_the_quest_waits() -> None:
    lab, state = started(level)
    typed = typed_in(lab, PATH[0], PATH[1], PATH[3])
    assert watch(level, "fizzle").watch(lab, state, typed).message == level.NOT_FIZZLED


def test_the_prediction_passes_with_any_option() -> None:
    assert all(kit.choose(level.GUESS, option).solved for option in level.GUESS.options)
