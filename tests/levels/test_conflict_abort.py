from firstcommit import kit
from firstcommit.levels import conflict_abort as level
from level_helpers import arrived, reaction, typed_in, watch


def paused() -> tuple[kit.Lab, kit.State, list[kit.Command]]:
    """
    Open the level and pull as the player does, so the merge stops with both files in conflict.

    Returns
    -------
    tuple[kit.Lab, kit.State, list[kit.Command]]
        The lab, the level's state and the lines typed.
    """
    lab, state = arrived(level)
    typed = typed_in(lab, "git pull --no-rebase")
    return lab, state, typed


def test_nothing_pulls_by_itself_and_the_level_asks_for_the_pull_first() -> None:
    lab, state = arrived(level)
    assert kit.snapshot(lab.project)["operation"] is None
    assert watch(level, "pull").watch(lab, state, []).message == level.NOT_PULLED
    assert level.check(lab, state, None, []).message == level.NOT_PULLED


def test_your_pull_stops_with_both_files_in_conflict() -> None:
    lab, state, typed = paused()
    assert typed[0]["status"] == 1
    snap = kit.snapshot(lab.project)
    assert snap["operation"] == "merge"
    assert sorted(kit.conflicted(snap)) == sorted(level.FILES)
    assert watch(level, "pull").watch(lab, state, typed).solved


def test_a_plain_pull_is_refused_and_the_level_says_how_to_join_the_histories() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git pull")
    assert typed[0]["status"] == 128
    assert kit.snapshot(lab.project)["operation"] is None
    verdict = watch(level, "pull").watch(lab, state, typed)
    assert (verdict.solved, verdict.message) == (False, level.HOW_TO_JOIN)


def test_a_pull_with_rebase_is_refused_because_of_the_note_and_the_level_says_why() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git pull --rebase")
    assert typed[0]["status"] == 128
    assert kit.snapshot(lab.project)["operation"] is None
    assert watch(level, "pull").watch(lab, state, typed).message == level.REBASE_REFUSED
    typed += typed_in(lab, "git pull --no-rebase")
    assert watch(level, "pull").watch(lab, state, typed).solved


def test_a_fetch_and_an_abort_with_no_merge_started_do_not_count() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git fetch", "git status", "git merge --abort")
    assert level.check(lab, state, None, typed).message == level.NOT_PULLED


def test_a_merge_of_the_bookmark_counts_as_the_pull() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git fetch", "git merge origin/main")
    assert watch(level, "pull").watch(lab, state, typed).solved


def test_status_counts_only_once_the_pull_stopped() -> None:
    lab, state = arrived(level)
    early = typed_in(lab, "git status")
    assert watch(level, "status").watch(lab, state, early).message == level.NOT_PULLED
    lab, state, typed = paused()
    typed += typed_in(lab, "git status")
    assert watch(level, "status").watch(lab, state, typed).message == level.LOOKED


def test_abort_puts_main_and_both_files_back_and_keeps_the_note() -> None:
    lab, state, typed = paused()
    typed += typed_in(lab, "git status", "git merge --abort")
    assert [line["status"] for line in typed] == [1, 0, 0]
    assert (lab.project / level.TODO).read_text() == level.TODO_NOTE
    assert level.check(lab, state, None, typed).solved


def test_a_hard_reset_ends_the_merge_but_throws_the_note_away() -> None:
    lab, state, typed = paused()
    reset = typed_in(lab, "git reset --hard")
    rule = reaction(level, reset[0], set(), True, False)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.RESET)
    verdict = level.check(lab, state, None, typed + reset)
    assert (verdict.lost, verdict.message) == (True, level.NOTE_LOST)


def test_finishing_the_merge_instead_is_named_and_the_level_offers_to_start_again() -> None:
    lab, state, typed = paused()
    typed += typed_in(lab, "git restore --theirs README.md notes.txt", "git add README.md notes.txt", "git commit --no-edit")
    assert typed[-1]["status"] == 0
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.MERGED)


def test_the_merge_still_paused_is_named() -> None:
    lab, state, typed = paused()
    assert level.check(lab, state, None, typed + typed_in(lab, "git status")).message == level.STILL_PAUSED


def test_the_briefing_carries_alexs_note_on_why_to_call_the_merge_off() -> None:
    assert "Alex, on the comms" in level.BRIEFING and "Call the merge off" in level.BRIEFING
