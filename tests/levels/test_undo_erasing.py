import pytest

from firstcommit import kit
from firstcommit.levels import undo_erasing as level
from level_helpers import reaction, started, typed_in, watch

LINES = ["git log --oneline", "git show HEAD:keys.txt", "git show HEAD~1:keys.txt", "git log --oneline keys.txt", "git log --oneline -- keys.txt"]


def test_the_keys_were_added_then_removed_and_both_commits_are_on_the_mothership_and_at_alexs() -> None:
    lab, state = started(level)
    assert kit.git(lab.project, "log", "--format=%s").splitlines() == ["Remove the keys", level.KEYS_ADDED, "Add the crew list", "Plot the route", "Start the project"]
    head = kit.git(lab.project, "rev-parse", "HEAD").strip()
    assert kit.git(lab.github, "rev-parse", "main").strip() == head
    assert kit.git(lab.teammate, "rev-parse", "HEAD").strip() == head
    assert not (lab.project / level.KEYS).exists()
    assert kit.in_history(lab.github, level.KEYS)


def test_the_newest_commit_has_no_keys_and_the_one_before_still_holds_the_password() -> None:
    lab, state = started(level)
    head, before = typed_in(lab, "git show HEAD:keys.txt", "git show HEAD~1:keys.txt")
    assert (head["status"], before["status"]) == (128, 0)
    assert kit.git(lab.project, "show", "HEAD~1:keys.txt") == level.KEYS_TEXT


def test_a_log_of_a_file_no_longer_in_the_folder_needs_the_two_dashes() -> None:
    lab, state = started(level)
    bare, dashed = typed_in(lab, "git log --oneline keys.txt", "git log --oneline -- keys.txt")
    assert (bare["status"], dashed["status"]) == (128, 0)
    assert kit.git(lab.project, "log", "--format=%s", "--", level.KEYS).splitlines() == ["Remove the keys", level.KEYS_ADDED]


def test_every_goal_reads_the_lines_typed_and_the_password_solves_the_level() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *LINES)
    assert watch(level, "log").watch(lab, state, typed) == kit.Verdict(True, level.LOGGED)
    assert watch(level, "head").watch(lab, state, typed) == kit.Verdict(True, level.NOT_IN_HEAD)
    assert watch(level, "before").watch(lab, state, typed) == kit.Verdict(True, level.FOUND)
    assert watch(level, "try").watch(lab, state, typed) == kit.Verdict(True, level.DASHES)
    assert watch(level, "trail").watch(lab, state, typed) == kit.Verdict(True, level.TRAIL)
    assert level.check(lab, state, "orion-7", typed) == kit.Verdict(True, level.RIGHT)


@pytest.mark.parametrize("answer", ["orion-7", "ORION-7", " Orion-7 ", "airlock password: orion-7", "Airlock  Password:  ORION-7"])
def test_the_password_is_accepted_alone_or_as_the_whole_line_in_any_case(answer: str) -> None:
    lab, state = started(level)
    assert level.check(lab, state, answer, []).solved


@pytest.mark.parametrize("answer", ["orion", "orion7", "airlock password", "keys.txt", "f3a8bc6"])
def test_anything_else_points_back_to_the_file(answer: str) -> None:
    lab, state = started(level)
    assert level.check(lab, state, answer, []) == kit.Verdict(False, level.WRONG)


def test_the_password_is_kept_as_a_digest_only() -> None:
    lab, state = started(level)
    assert "orion" not in str(state)


def test_the_commit_read_may_be_named_by_its_hash() -> None:
    lab, state = started(level)
    added = kit.git(lab.project, "rev-parse", "--short", "HEAD~1").strip()
    assert watch(level, "before").watch(lab, state, typed_in(lab, f"git show {added}:keys.txt")).solved


def test_reading_another_commit_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git show HEAD~2:keys.txt", "git show HEAD:crew.txt")
    assert watch(level, "head").watch(lab, state, typed) == kit.Verdict(False, level.NOT_HEAD)
    assert watch(level, "before").watch(lab, state, typed) == kit.Verdict(False, level.NOT_FOUND)


def test_two_commits_back_is_before_the_keys_and_rama_says_so() -> None:
    lab, state = started(level)
    [line] = typed_in(lab, "git show HEAD~2:keys.txt")
    assert line["status"] == 128
    rule = reaction(level, line, set(), True, False)
    assert rule is not None and rule.text == level.TOO_FAR


def test_the_dashed_log_alone_also_finds_the_trail() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline -- keys.txt")
    assert watch(level, "try").watch(lab, state, typed).solved
    assert watch(level, "trail").watch(lab, state, typed).solved
    assert not watch(level, "trail").watch(lab, state, typed_in(lab, "git log --oneline keys.txt")).solved


def test_the_answer_is_read_from_the_lab_without_changing_it() -> None:
    lab, state = started(level)
    before = kit.git(lab.project, "status", "--porcelain=v2", "--branch")
    assert level.ANSWER(lab, state) == "orion-7"
    assert kit.git(lab.project, "status", "--porcelain=v2", "--branch") == before
