from firstcommit import kit, runner
from firstcommit.levels import vault_inspection as level
from level_helpers import arrived, reaction, started, typed_in, watch


def test_the_challenge_starts_with_the_patch_the_keys_and_the_log_staged_once_the_page_has_looked() -> None:
    lab, _ = started(level)
    assert kit.untracked(kit.snapshot(lab.project)) == ["debug.log", "keys.txt"]
    lab, _ = arrived(level)
    assert kit.staged(kit.snapshot(lab.project)) == ["debug.log", "keys.txt", "reactor.cfg"]
    assert runner.load(level).challenge


def test_unstaging_both_stowaways_then_committing_solves_it_with_one_command_or_two() -> None:
    for unstage in (["git restore --staged keys.txt debug.log"], ["git rm --cached -q keys.txt", "git restore --staged debug.log"]):
        lab, state = arrived(level)
        typed = typed_in(lab, *unstage, 'git commit -m "Lower the reactor limit"')
        assert level.check(lab, state, None, typed).solved, unstage
        assert kit.untracked(kit.snapshot(lab.project)) == ["debug.log", "keys.txt"]


def test_the_goals_tick_in_any_order() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git restore --staged debug.log")
    assert watch(level, "log").watch(lab, state, typed).solved
    assert not watch(level, "keys").watch(lab, state, typed).solved
    assert not watch(level, "reactor").watch(lab, state, typed).solved


def test_committing_at_once_seals_the_password_and_the_challenge_is_lost() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, 'git commit -m "Patch"')
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost) == (False, True)
    assert verdict.message in (level.KEYS_SEALED, level.LOG_SEALED)


def test_deleting_the_keys_while_they_are_staged_is_said_and_unstaging_them_then_loses_them() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "rm keys.txt")
    verdict = watch(level, "keys").watch(lab, state, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, False, level.KEYS_DELETED)
    typed += typed_in(lab, "git restore --staged keys.txt")
    verdict = watch(level, "keys").watch(lab, state, typed)
    assert (verdict.lost, verdict.message) == (True, level.KEYS_LOST)


def test_a_deleted_debug_log_is_asked_back_but_is_no_lost_work() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git restore --staged debug.log", "rm debug.log")
    verdict = watch(level, "log").watch(lab, state, typed)
    assert (verdict.solved, verdict.lost) == (False, False)


def test_staging_everything_again_is_a_danger_rama_still_names_in_the_challenge() -> None:
    rule = reaction(level, {"line": "git add .", "status": 0}, {"file-staged"}, True, True)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.EVERYTHING_STAGED)


def test_the_patch_in_the_folder_but_in_no_commit_is_not_saved() -> None:
    lab, state = arrived(level)
    assert watch(level, "reactor").watch(lab, state, []).message == level.REACTOR_NOT_SAVED
