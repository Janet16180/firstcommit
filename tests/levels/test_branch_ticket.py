from firstcommit import kit
from firstcommit.levels import branch_ticket as level
from level_helpers import arrived, reaction, started, typed_in

SEND = 'git switch -c fix-lights && git commit -am "Fix the hall lights" && git push -u origin fix-lights'


def test_alex_pushes_to_main_once_the_page_has_looked_and_your_fix_waits_uncommitted() -> None:
    lab, state = started(level)
    assert level.check(lab, state, None, []).message == level.NOT_UP
    lab, state = arrived(level)
    assert kit.git(lab.github, "log", "-1", "--format=%an", "main").strip() == "Alex"
    assert kit.git(lab.project, "status", "--porcelain").strip() == "M lights.cfg"


def test_the_goals_pass_in_either_order() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git pull")
    assert level.check(lab, state, None, typed).message == level.NOT_UP
    typed += typed_in(lab, SEND)
    assert [line["status"] for line in typed] == [0, 0]
    assert level.check(lab, state, None, typed).solved


def test_the_fix_committed_on_main_is_named_and_the_level_offers_to_start_again() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, 'git commit -am "Fix the hall lights"')
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.MINE_ON_MAIN)


def test_the_fix_pushed_to_the_mothership_main_skipped_review() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, 'git commit -am "Fix the hall lights"', "git pull --no-rebase", "git push")
    assert [line["status"] for line in typed] == [0, 0, 0]
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.MAIN_TOUCHED)


def test_the_fix_thrown_away_before_any_commit_is_lost() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git restore lights.cfg")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.FIX_LOST)


def test_the_fix_in_the_stash_is_not_lost() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git stash")
    assert not level.check(lab, state, None, typed).lost
    typed += typed_in(lab, "git switch -c fix-lights", "git stash pop", 'git commit -am "Fix the hall lights"', "git push -u origin fix-lights")
    typed += typed_in(lab, "git switch main", "git pull")
    assert level.check(lab, state, None, typed).solved


def test_a_forced_push_to_main_drops_alexs_commit_and_rama_warns() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git push --force origin main")
    rule = reaction(level, typed[0], {"push-received"}, True, False)
    assert rule is not None and (rule.mood, rule.text) == ("err", level.FORCED)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.ALEX_DROPPED)
