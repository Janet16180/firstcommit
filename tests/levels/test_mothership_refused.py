import pytest

from firstcommit import kit
from firstcommit.levels import mothership_refused as level
from level_helpers import arrived, reaction, started, typed_in, watch


def test_alex_pushes_once_the_page_has_looked_and_your_commit_is_not_on_the_mothership() -> None:
    lab, state = started(level)
    assert watch(level, "push").watch(lab, state, []).message == level.WAITING
    lab, state = arrived(level)
    assert kit.git(lab.github, "log", "-1", "--format=%an", "main").strip() == "Alex"
    assert kit.git(lab.project, "log", "-1", "--format=%an %s").strip() == "Cadet Add the route"


@pytest.mark.parametrize("pull", ["git pull --no-rebase", "git pull --rebase"])
def test_a_refused_push_then_either_pull_then_a_push_solves_the_level(pull: str) -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git push", pull, "git push")
    assert [line["status"] for line in typed] == [1, 0, 0]
    assert level.check(lab, state, None, typed).solved


def test_a_plain_pull_stops_and_rama_names_the_two_answers() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git push", "git pull")
    assert typed[1]["status"] == 128
    rule = reaction(level, typed[1], set(), True, False)
    assert rule is not None and rule.text == level.CHOOSE
    assert watch(level, "pull").watch(lab, state, typed).message == level.NOT_JOINED


def test_the_refused_push_changes_nothing_on_either_side() -> None:
    lab, state = arrived(level)
    mine, theirs = kit.git(lab.project, "rev-parse", "main"), kit.git(lab.github, "rev-parse", "main")
    typed = typed_in(lab, "git push")
    assert watch(level, "push").watch(lab, state, typed).solved
    assert (kit.git(lab.project, "rev-parse", "main"), kit.git(lab.github, "rev-parse", "main")) == (mine, theirs)


def test_a_forced_push_drops_alexs_commit_and_the_level_offers_to_start_again() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git push --force")
    assert typed[0]["status"] == 0
    rule = reaction(level, typed[0], {"push-received"}, True, False)
    assert rule is not None and (rule.mood, rule.text) == ("err", level.FORCED)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.ALEX_DROPPED)


def test_nothing_names_no_rebase_before_the_plain_pull_has_stopped() -> None:
    assert watch(level, "push").text == "Try to send your commit up."
    assert watch(level, "pull").command == "git pull"
    lab, state = arrived(level)
    typed = typed_in(lab, "git push")
    assert "--no-rebase" not in watch(level, "pull").watch(lab, state, typed).message
