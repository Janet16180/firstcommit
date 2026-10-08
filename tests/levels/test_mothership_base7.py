from firstcommit import kit, runner
from firstcommit.levels import mothership_base7 as level
from level_helpers import started, typed_in, watch

REBUILD = ["git init", "git add blueprint.txt reactor.cfg", 'git commit -m "Rebuild Base 7"', "git remote add origin ../github.com/moonbase/project.git", "git push -u origin main"]


def test_base_7_starts_as_a_plain_folder_with_the_debris_next_to_an_empty_mothership() -> None:
    lab, state = started(level)
    assert not kit.snapshot(lab.project)["exists"]
    assert sorted(path.name for path in lab.project.iterdir()) == ["blueprint.txt", "crash-dump.bin", "reactor.cfg"]
    assert kit.snapshot(lab.github)["refs"] == [] and runner.load(level).challenge
    assert level.check(lab, state, None, []).message == level.NO_REPOSITORY


def test_the_whole_loop_rebuilds_base_7_and_the_debris_stays_in_the_folder() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *REBUILD)
    assert [line["status"] for line in typed] == [0, 0, 0, 0, 0]
    assert level.check(lab, state, None, typed).solved
    assert kit.untracked(kit.snapshot(lab.project)) == ["crash-dump.bin"]


def test_deleting_the_debris_and_adding_everything_left_works_too() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git init", "rm crash-dump.bin", "git add .", 'git commit -m "Rebuild Base 7"', REBUILD[3], REBUILD[4])
    assert level.check(lab, state, None, typed).solved


def test_sealing_the_debris_is_lost_here_and_on_the_mothership() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git init", "git add .", 'git commit -m "Everything"')
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.DEBRIS_SEALED)
    typed += typed_in(lab, REBUILD[3], REBUILD[4])
    assert watch(level, "launch").watch(lab, state, typed).message == level.DEBRIS_LAUNCHED


def test_the_goals_tick_in_any_order() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git init", "git remote add origin ../github.com/moonbase/project.git")
    assert watch(level, "contact").watch(lab, state, typed).solved
    assert not watch(level, "capsule").watch(lab, state, typed).solved


def test_a_commit_pushed_then_a_new_local_commit_is_not_the_same_main() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *REBUILD, "echo more >> blueprint.txt", 'git commit -am "More"')
    assert watch(level, "launch").watch(lab, state, typed).message == level.NOT_LAUNCHED


def test_origin_by_the_mothership_s_absolute_path_counts() -> None:
    lab, state = started(level)
    typed_in(lab, "git init -q", f"git remote add origin {lab.github}/")
    assert level.watch_contact(lab, state, []).message == level.CONTACT


def test_the_scene_opens_on_the_meteorite_strike_then_the_challenge_alarm() -> None:
    assert [frame.art for frame in level.SCENE] == ["meteor", "alarm"]
