from firstcommit import kit
from firstcommit.levels import branch_switch as level
from level_helpers import reaction, started, typed_in, watch

NOTE = 'echo "Stop at Phobos" >> route.txt'
KEEP = 'git commit -am "Note the survey route"'


def test_the_level_starts_on_main_with_lights_edited_and_scout_holding_another_route() -> None:
    lab, state = started(level)
    snap = kit.snapshot(lab.project)
    assert (snap["branch"], kit.unstaged(snap), kit.staged(snap)) == ("main", ["lights.cfg"], [])
    assert kit.git(lab.project, "show", "main:lights.cfg") == kit.git(lab.project, "show", "scout:lights.cfg")
    assert kit.git(lab.project, "show", "main:route.txt") != kit.git(lab.project, "show", "scout:route.txt")
    assert kit.git(lab.project, "rev-parse", "main").strip() == state["main"]


def test_every_prediction_passes_with_the_same_reveal() -> None:
    for option in level.GUESS.options:
        assert kit.choose(level.GUESS, option) == kit.Verdict(True, level.GUESS.reveal)


def test_switching_to_scout_carries_the_lights_edit() -> None:
    lab, state = started(level)
    assert watch(level, "carry").watch(lab, state, []).message == level.NOT_ON_SCOUT
    typed = typed_in(lab, "git switch scout")
    assert watch(level, "carry").watch(lab, state, typed) == kit.Verdict(True, level.CARRIED)
    assert (lab.project / "lights.cfg").read_text() == level.LIGHTS_EDITED


def test_a_switch_that_would_overwrite_the_route_note_is_refused_and_rama_names_both_ways_out() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch scout", NOTE)
    assert watch(level, "refused").watch(lab, state, typed).message == level.NOT_REFUSED
    typed += typed_in(lab, "git switch main")
    assert typed[-1]["status"] == 1
    assert kit.snapshot(lab.project)["branch"] == "scout"
    assert watch(level, "refused").watch(lab, state, typed) == kit.Verdict(True, level.REFUSED)
    rule = reaction(level, typed[-1], set(), True, False)
    assert rule is not None and (rule.mood, rule.text) == ("err", level.SWITCH_REFUSED)
    assert "git commit -am" in rule.text and "git restore route.txt" in rule.text


def test_committing_both_edits_on_scout_solves_the_level_and_main_is_untouched() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch scout", NOTE, "git switch main", KEEP)
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.KEPT)
    assert kit.git(lab.project, "rev-parse", "main").strip() == state["main"]
    assert kit.git(lab.project, "show", "scout:lights.cfg") == level.LIGHTS_EDITED


def test_committing_only_the_route_asks_for_both_edits() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch scout", NOTE, "git switch main", 'git commit -m "Route" route.txt')
    assert watch(level, "keep").watch(lab, state, typed).message == level.NOT_KEPT


def test_a_commit_on_main_is_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -am "Lights"')
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.MAIN_TOUCHED)


def test_throwing_the_lights_edit_away_is_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git restore lights.cfg")
    verdict = watch(level, "carry").watch(lab, state, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.LIGHTS_GONE)
