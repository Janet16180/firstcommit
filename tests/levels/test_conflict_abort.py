from firstcommit import kit
from firstcommit.levels import conflict_abort as level
from level_helpers import arrived, reaction, started, typed_in


def test_the_pull_stops_once_the_page_has_looked_with_both_files_in_conflict() -> None:
    lab, state = started(level)
    assert level.check(lab, state, None, []).message == level.WAITING
    lab, state = arrived(level)
    snap = kit.snapshot(lab.project)
    assert snap["operation"] == "merge"
    assert sorted(kit.conflicted(snap)) == sorted(level.FILES)


def test_abort_puts_main_and_both_files_back_and_keeps_the_note() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git merge --abort")
    assert [line["status"] for line in typed] == [0, 0]
    assert (lab.project / level.TODO).read_text() == level.TODO_NOTE
    assert level.check(lab, state, None, typed).solved


def test_a_hard_reset_ends_the_merge_but_throws_the_note_away() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git reset --hard")
    rule = reaction(level, typed[0], set(), True, False)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.RESET)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.NOTE_LOST)


def test_finishing_the_merge_instead_is_named_and_the_level_offers_to_start_again() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git restore --theirs README.md notes.txt", "git add README.md notes.txt", "git commit --no-edit")
    assert typed[-1]["status"] == 0
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.MERGED)


def test_the_merge_still_paused_is_named() -> None:
    lab, state = arrived(level)
    assert level.check(lab, state, None, typed_in(lab, "git status")).message == level.STILL_PAUSED
