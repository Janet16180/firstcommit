from firstcommit import kit
from firstcommit.levels import mothership_halves as level
from level_helpers import reached, reaction, started, typed_in, watch


def test_alex_has_the_engines_committed_and_your_navigation_waits_uncommitted() -> None:
    lab, state = started(level)
    assert kit.git(lab.teammate, "log", "-1", "--format=%an %s").strip() == "Alex Set the engines"
    assert kit.git(lab.project, "status", "--porcelain").strip() == "M nav.cfg"
    assert kit.git(lab.github, "rev-parse", "main") != kit.git(lab.teammate, "rev-parse", "main")


def test_alex_pushes_once_your_half_is_up_joining_both_halves_in_a_merge_and_your_pull_brings_the_whole_ship() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -am "Set the navigation"', "git push")
    assert watch(level, "pull").watch(lab, state, typed).message == level.WAITING
    reached(level, lab, state, "push")
    assert len(kit.git(lab.github, "log", "-1", "--format=%P", "main").split()) == 2
    typed += typed_in(lab, "git pull")
    assert level.check(lab, state, None, typed).solved
    assert ((lab.project / level.NAV).read_text(), (lab.project / level.ENGINE).read_text()) == (level.YOUR_HALF, level.ALEX_HALF)


def test_the_pull_that_brings_the_other_half_plays_the_launch_moment() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -am "Set the navigation"', "git push")
    reached(level, lab, state, "push")
    typed += typed_in(lab, "git pull")
    rule = reaction(level, typed[-1], {"branch-moved"}, True, False)
    assert rule is not None and (rule.text, rule.moment) == (level.TWO_HALVES, "launch")
    quiet = reaction(level, typed[-1], set(), True, False)
    assert quiet is None or quiet.moment is None
