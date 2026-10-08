import pytest

from firstcommit import kit
from firstcommit.levels import mothership_contact as level
from level_helpers import reaction, started, typed_in, watch


def test_the_level_starts_with_two_commits_no_remote_and_an_empty_mothership() -> None:
    lab, _ = started(level)
    assert len(kit.snapshot(lab.project)["commits"]) == 2
    assert kit.git(lab.project, "remote").strip() == ""
    assert kit.snapshot(lab.github)["refs"] == []


def test_adding_origin_then_listing_solves_the_level_and_nothing_travels() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git remote add origin ../github/project.git", "git remote -v")
    assert [line["status"] for line in typed] == [0, 0]
    assert level.check(lab, state, None, typed).solved
    assert kit.snapshot(lab.github)["refs"] == []


def test_listing_before_adding_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git remote -v", "git remote add origin ../github/project.git")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_LISTED)


def test_an_https_address_gets_a_warning_and_set_url_fixes_it() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git remote add origin https://github.com/base/project.git")
    rule = reaction(level, typed[0], set(), True, False)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.HTTPS_URL)
    assert watch(level, "remote").watch(lab, state, typed).message == level.WRONG_URL
    typed += typed_in(lab, "git remote add origin ../github/project.git")
    assert typed[-1]["status"] == 3
    rule = reaction(level, typed[-1], set(), True, False)
    assert rule is not None and rule.text == level.REMOTE_EXISTS
    typed += typed_in(lab, "git remote set-url origin ../github/project.git", "git remote -v")
    assert level.check(lab, state, None, typed).solved


def test_another_name_is_asked_to_be_origin() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git remote add mothership ../github/project.git")
    assert watch(level, "remote").watch(lab, state, typed).message == level.OTHER_NAME


def test_without_a_remote_the_goal_says_how_to_add_one() -> None:
    lab, state = started(level)
    assert watch(level, "remote").watch(lab, state, []).message == level.NO_REMOTE


def test_the_prediction_passes_with_any_option() -> None:
    assert all(kit.choose(level.GUESS, option).solved for option in level.GUESS.options)


@pytest.mark.parametrize("url", ["../github/project.git/", "./../github/project.git", "{github}", "file://{github}"])
def test_any_address_that_reaches_the_mothership_makes_contact(url: str) -> None:
    lab, state = started(level)
    typed_in(lab, f"git remote add origin {url.format(github=lab.github)}")
    assert watch(level, "remote").watch(lab, state, []).message == level.CONTACT
