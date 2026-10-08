from firstcommit import kit, reactions
from firstcommit.levels import vault_seal as level
from level_helpers import reaction, started, typed_in, watch


def test_the_level_starts_with_the_map_staged_the_journal_untracked_and_an_empty_mothership() -> None:
    lab, _ = started(level)
    snap = kit.snapshot(lab.project)
    assert (snap["commits"], kit.staged(snap), kit.untracked(snap)) == ([], ["map.txt"], ["journal.txt"])
    assert kit.snapshot(lab.github)["refs"] == []


def test_committing_then_reading_the_log_solves_the_level_as_the_cadet() -> None:
    lab, state = started(level)
    typed = typed_in(lab, 'git commit -m "Add the map"', "git log")
    assert [line["status"] for line in typed] == [0, 0]
    assert level.check(lab, state, None, typed).solved
    assert kit.git(lab.project, "log", "-1", "--format=%an %s").strip() == "Cadet Add the map"
    assert kit.untracked(kit.snapshot(lab.project)) == ["journal.txt"]
    assert kit.snapshot(lab.github)["refs"] == []


def test_a_bare_commit_makes_no_commit_and_rama_asks_for_a_message() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git commit")
    assert typed[0]["status"] == 1
    assert watch(level, "commit").watch(lab, state, typed).message == level.NO_COMMIT
    rule = reaction(level, typed[0], set(), True, True)
    assert rule is not None and rule.text == reactions.NO_MESSAGE


def test_a_log_before_the_commit_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log", 'git commit -m "Add the map"')
    assert typed[0]["status"] == 128
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_LOOKED)


def test_sealing_the_journal_too_is_said_and_the_level_offers_to_start_again() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git add .", 'git commit -m "Everything"', "git log")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.JOURNAL_SEALED)


def test_unstaging_the_map_and_committing_nothing_new_says_what_is_missing() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git rm --cached -q map.txt", "touch notes.txt", "git add notes.txt", 'git commit -m "Notes"')
    assert watch(level, "commit").watch(lab, state, typed).message == level.MAP_MISSING


def test_the_prediction_passes_with_any_option() -> None:
    assert all(kit.choose(level.GUESS, option).solved for option in level.GUESS.options)
