from firstcommit import kit, reactions
from firstcommit.levels import cargo_selective as level
from level_helpers import reaction, started, typed_in, watch


def test_the_level_starts_in_a_new_repository_with_three_untracked_files() -> None:
    lab, _ = started(level)
    snap = kit.snapshot(lab.project)
    assert (snap["exists"], snap["commits"]) == (True, [])
    assert kit.untracked(snap) == ["engine.cfg", "keys.txt", "route.txt"]


def test_naming_the_two_files_then_looking_solves_the_level() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git add engine.cfg route.txt", "git status")
    assert level.check(lab, state, None, typed).solved
    assert kit.staged(kit.snapshot(lab.project)) == ["engine.cfg", "route.txt"]


def test_one_file_at_a_time_works_too_and_the_look_must_come_after_the_last_add() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git add engine.cfg", "git status")
    verdict = watch(level, "stage").watch(lab, state, typed)
    assert not verdict.solved and verdict.message == level.ONE_MISSING
    typed += typed_in(lab, "git add route.txt")
    assert watch(level, "stage").watch(lab, state, typed).solved
    assert not level.check(lab, state, None, typed).solved
    assert level.check(lab, state, None, typed + typed_in(lab, "git status")).solved


def test_staging_everything_takes_the_keys_too_and_rm_cached_takes_them_back_out() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git add .")
    verdict = watch(level, "stage").watch(lab, state, typed)
    assert not verdict.solved and verdict.message == level.KEYS_STAGED
    rule = reaction(level, typed[0], {"file-staged"}, True, True)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.EVERYTHING_STAGED)
    typed += typed_in(lab, "git rm --cached keys.txt", "git status")
    snap = kit.snapshot(lab.project)
    assert kit.untracked(snap) == ["keys.txt"] and (lab.project / "keys.txt").exists()
    assert level.check(lab, state, None, typed).solved


def test_restore_staged_fails_before_the_first_commit_and_the_level_says_what_works() -> None:
    lab, _ = started(level)
    typed = typed_in(lab, "git add .", "git restore --staged keys.txt")
    assert typed[1]["status"] == 128
    rule = reaction(level, typed[1], set(), True, True)
    assert rule is not None and rule.text == level.NOTHING_TO_RESTORE


def test_naming_one_file_of_the_engine_and_route_gets_the_shared_reaction() -> None:
    rule = reaction(level, {"line": "git add engine.cfg route.txt", "status": 0}, {"file-staged"}, True, True)
    assert rule is not None and rule.text == reactions.STAGED


def test_keys_in_a_commit_are_said_and_the_level_offers_to_start_again() -> None:
    lab, state = started(level)
    kit.git(lab.project, "add", ".")
    kit.git(lab.project, "commit", "-q", "-m", "Load everything")
    verdict = level.check(lab, state, None, typed_in(lab, "git status"))
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.KEYS_COMMITTED)


def test_the_engine_and_route_may_be_committed_already_as_long_as_the_keys_stay_out() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git add engine.cfg route.txt")
    kit.git(lab.project, "commit", "-q", "-m", "Load the engine and the route")
    assert level.check(lab, state, None, typed + typed_in(lab, "git status")).solved


def test_a_deleted_repository_is_told_and_never_solved() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "rm -rf .git", "git status")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.NO_REPOSITORY)
