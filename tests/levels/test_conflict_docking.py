import pytest

from firstcommit import kit
from firstcommit.levels import conflict_docking as level
from level_helpers import reached, reaction, started, typed_in

ANSWER = "git add docking.txt && git commit --no-edit"


def test_your_push_bounces_and_the_pull_stops_on_the_docking_line() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push", "git pull --no-rebase")
    assert [line["status"] for line in typed] == [1, 1]
    assert kit.conflicted(kit.snapshot(lab.project)) == [level.DOCKING]
    assert level.check(lab, state, None, typed).message == level.PAUSED


@pytest.mark.parametrize(("pull", "side"), [("git pull --no-rebase", "--theirs"), ("git pull --rebase", "--ours")])
def test_either_pull_answered_with_alexs_bay_then_alex_moves_again_and_one_more_pull_solves_it(pull: str, side: str) -> None:
    lab, state = started(level)
    finish = ANSWER if "no-rebase" in pull else "git add docking.txt && GIT_EDITOR=true git rebase --continue"
    typed = typed_in(lab, pull, f"git restore {side} docking.txt", finish)
    assert typed[-1]["status"] == 0
    assert level.check(lab, state, None, typed).message == level.NOT_SENT
    reached(level, lab, state, "joined")
    typed += typed_in(lab, "git push")
    assert typed[-1]["status"] == 1
    typed += typed_in(lab, "git pull --no-rebase --no-edit", "git push")
    assert level.check(lab, state, None, typed).solved


def test_bay_5_kept_is_named() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git pull --no-rebase", "git restore --ours docking.txt", ANSWER)
    assert level.check(lab, state, None, typed).message == level.NOT_BAY_4


def test_a_forced_push_drops_alexs_commit_and_rama_warns() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git push --force")
    rule = reaction(level, typed[0], {"push-received"}, True, False)
    assert rule is not None and (rule.mood, rule.text, rule.moment) == ("err", level.FORCED, "force-break")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.ALEX_DROPPED)


def test_resetting_to_the_mothership_throws_the_checklist_away() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git fetch", "git reset --hard origin/main")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.CHECKLIST_LOST)
