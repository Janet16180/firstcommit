from firstcommit import kit, reactions
from firstcommit.levels import cargo_stowaway as level
from level_helpers import arrived, reaction, started, typed_in, watch


def test_the_night_shifts_add_stages_the_keys_once_the_page_has_looked() -> None:
    lab, _ = started(level)
    snap = kit.snapshot(lab.project)
    assert (len(snap["commits"]), kit.staged(snap), kit.untracked(snap)) == (1, [], ["keys.txt"])
    assert kit.unstaged(snap) == ["engine.cfg", "route.txt"]
    lab, _ = arrived(level)
    assert kit.staged(kit.snapshot(lab.project)) == ["engine.cfg", "keys.txt", "route.txt"]


def test_looking_then_restoring_the_keys_from_the_staging_area_solves_the_level() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git restore --staged keys.txt")
    assert level.check(lab, state, None, typed).solved
    snap = kit.snapshot(lab.project)
    assert (kit.staged(snap), kit.untracked(snap)) == (["engine.cfg", "route.txt"], ["keys.txt"])


def test_rm_cached_takes_the_keys_out_too() -> None:
    lab, state = arrived(level)
    assert level.check(lab, state, None, typed_in(lab, "git status", "git rm --cached keys.txt")).solved


def test_the_level_waits_for_a_look_with_git_status() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git restore --staged keys.txt")
    assert watch(level, "unstage").watch(lab, state, typed).solved
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_LOOKED)


def test_the_keys_on_the_dock_are_named_as_the_thing_to_fix() -> None:
    lab, state = arrived(level)
    verdict = watch(level, "unstage").watch(lab, state, typed_in(lab, "git status"))
    assert (verdict.solved, verdict.message) == (False, level.KEYS_ABOARD)


def test_git_rm_refuses_and_rama_says_why_and_what_keeps_the_file() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git rm keys.txt")
    assert typed[0]["status"] == 1 and (lab.project / "keys.txt").exists()
    rule = reaction(level, typed[0], set(), True, True)
    assert rule is not None and rule.text == level.RM_REFUSED


def test_deleting_the_file_leaves_it_staged_and_restoring_it_from_the_staging_area_brings_it_back() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "rm keys.txt")
    rule = reaction(level, typed[1], {"file-deleted"}, True, True)
    assert rule is not None and rule.text == level.DELETED
    verdict = watch(level, "unstage").watch(lab, state, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, False, level.DELETED)
    typed += typed_in(lab, "git restore keys.txt", "git restore --staged keys.txt")
    assert level.check(lab, state, None, typed).solved


def test_deleting_the_file_then_unstaging_it_loses_it_for_good() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "rm keys.txt", "git restore --staged keys.txt")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.KEYS_LOST)


def test_unstaging_everything_takes_the_engine_and_route_out_too_and_adding_them_again_solves_it() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git restore --staged .")
    verdict = watch(level, "unstage").watch(lab, state, typed)
    assert (verdict.solved, verdict.message) == (False, level.CARGO_UNSTAGED)
    rule = reaction(level, typed[1], {"file-unstaged"}, True, False)
    assert rule is not None and rule.text == reactions.UNSTAGED
    assert level.check(lab, state, None, typed + typed_in(lab, "git add engine.cfg route.txt")).solved


def test_keys_in_a_commit_are_said_and_the_level_offers_to_start_again() -> None:
    lab, state = arrived(level)
    kit.git(lab.project, "commit", "-q", "-m", "Night cargo")
    verdict = level.check(lab, state, None, typed_in(lab, "git status"))
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.KEYS_COMMITTED)


def test_looking_at_the_staged_keys_explains_why_secrets_stay_out_with_the_leak_moment() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status")
    rule = reaction(level, typed[0], set(), True, True)
    assert rule is not None and (rule.mood, rule.text, rule.moment) == ("warn", level.WHY_SECRETS, "secret-leak")
