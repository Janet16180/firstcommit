import os
import subprocess

from firstcommit import gitcmd, kit, save
from firstcommit.levels import mothership_halves as level
from level_helpers import reaction, started, typed_in


def test_alex_has_the_engines_committed_and_your_navigation_waits_uncommitted() -> None:
    lab, state = started(level)
    assert kit.git(lab.teammate, "log", "-1", "--format=%an %s").strip() == "Alex Set the engines"
    assert kit.git(lab.project, "status", "--porcelain").strip() == "M nav.cfg"
    assert kit.git(lab.github, "rev-parse", "main") != kit.git(lab.teammate, "rev-parse", "main")


def test_your_push_has_alex_join_both_halves_in_a_merge_and_push_before_it_returns_so_the_hints_lines_typed_at_once_solve_it() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -am "Set the navigation"', "git push", "git pull")
    assert len(kit.git(lab.github, "log", "-1", "--format=%P", "main").split()) == 2
    assert level.check(lab, state, None, typed).solved
    assert ((lab.project / level.NAV).read_text(), (lab.project / level.ENGINE).read_text()) == (level.YOUR_HALF, level.ALEX_HALF)


def test_a_push_from_your_playground_button_has_alex_push_too() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -am "Set the navigation"')
    kit.press(lab, "you", "push")
    typed += typed_in(lab, "git pull")
    assert level.check(lab, state, None, typed).solved


def test_alex_works_silently_so_your_push_shows_only_your_own_lines() -> None:
    lab, state = started(level)
    typed_in(lab, 'git commit -am "Set the navigation"')
    env = {**gitcmd.shell_environment(os.environ, save.home()), "HOME": str(save.home())}
    pushed = subprocess.run(["git", "push"], cwd=lab.project, env=env, capture_output=True, text=True, check=True)
    assert "remote:" not in pushed.stdout + pushed.stderr


def test_a_push_without_your_navigation_leaves_alex_waiting_until_one_with_it() -> None:
    lab, state = started(level)
    (lab.project / level.NAV).write_text("heading=Venus\n")
    typed = typed_in(lab, 'git commit -am "Set a heading"', "git push")
    assert kit.git(lab.teammate, "rev-parse", "main").strip() == state["alex"]
    (lab.project / level.NAV).write_text(level.YOUR_HALF)
    typed += typed_in(lab, 'git commit -am "Set the navigation"', "git push", "git pull")
    assert level.check(lab, state, None, typed).solved


def test_the_pull_that_brings_the_other_half_plays_the_launch_moment() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -am "Set the navigation"', "git push", "git pull")
    rule = reaction(level, typed[-1], {"branch-moved"}, True, False)
    assert rule is not None and (rule.text, rule.moment) == (level.TWO_HALVES, "launch")
    quiet = reaction(level, typed[-1], set(), True, False)
    assert quiet is None or quiet.moment is None
