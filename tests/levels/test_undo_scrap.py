from firstcommit import kit
from firstcommit.levels import undo_scrap as level
from level_helpers import reaction, started, typed_in, watch

RESTORE = "git restore engine.cfg"


def test_the_level_starts_with_the_engine_edited_and_the_notes_staged() -> None:
    lab, _ = started(level)
    snap = kit.snapshot(lab.project)
    assert (kit.unstaged(snap), kit.staged(snap)) == (["engine.cfg"], ["notes.txt"])


def test_looking_then_restoring_the_engine_solves_the_level_and_keeps_the_staged_notes() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git diff", RESTORE)
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.SCRAPPED)
    assert (lab.project / "engine.cfg").read_text() == level.ENGINE_COMMITTED
    assert kit.staged(kit.snapshot(lab.project)) == ["notes.txt"]


def test_the_level_waits_for_a_look_at_what_would_be_lost() -> None:
    lab, state = started(level)
    typed = typed_in(lab, RESTORE)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_LOOKED)


def test_restoring_the_engine_says_the_lines_are_gone_with_the_search_beam() -> None:
    lab, _ = started(level)
    typed = typed_in(lab, "git diff", RESTORE)
    rule = reaction(level, typed[1], {"file-changed"}, True, True)
    assert rule is not None and (rule.mood, rule.text, rule.moment) == ("warn", level.GONE, "search-beam")


def test_the_unsaved_lines_are_in_no_commit_and_no_stage_once_restored() -> None:
    lab, _ = started(level)
    typed_in(lab, RESTORE)
    found = kit.git_run(lab.project, "log", "--all", "-S", "overdrive", "--format=%H").stdout.strip()
    assert found == "" and "overdrive" not in kit.git(lab.project, "show", ":engine.cfg")


def test_the_staged_notes_thrown_away_are_lost_for_this_play() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git diff", "git restore --staged --worktree notes.txt engine.cfg")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.NOTES_LOST)


def test_until_the_engine_matches_its_commit_the_goal_says_how() -> None:
    lab, state = started(level)
    assert watch(level, "scrap").watch(lab, state, []).message == level.NOT_SCRAPPED


def test_every_prediction_passes_with_the_reveal() -> None:
    for option in level.GUESS.options:
        assert kit.choose(level.GUESS, option) == kit.Verdict(True, level.GUESS.reveal)
