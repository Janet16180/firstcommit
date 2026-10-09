import pytest

from firstcommit import kit
from firstcommit.levels import vault_past as level
from level_helpers import reaction, started, typed_in, watch


def test_six_commits_four_of_them_change_the_fuel_log_and_the_phobos_one_has_the_hash_the_text_names() -> None:
    lab, state = started(level)
    assert kit.git(lab.project, "log", "--format=%s").splitlines() == [message for message, _, _ in reversed(level.FUEL_LOG)]
    assert kit.git(lab.project, "log", "--format=%s", "--", level.FUEL).splitlines() == [
        "Log the fuel tonight",
        level.PHOBOS,
        "Log the fuel after the Moon",
        "Set up the base",
    ]
    phobos = kit.git(lab.project, "log", "--format=%H", "--grep", "Phobos").strip()
    assert phobos.startswith(level.PHOBOS_HASH)
    assert state["phobos"] == phobos
    assert (lab.project / level.FUEL).read_text() == "fuel: 40%\n"


def test_reading_the_phobos_commit_and_its_fuel_log_then_answering_60_solves_the_level() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log fuel.txt", "git show ccf9485", "git show ccf9485:fuel.txt")
    assert [line["status"] for line in typed] == [0, 0, 0]
    assert watch(level, "log").watch(lab, state, typed) == kit.Verdict(True, level.LOGGED)
    assert watch(level, "show").watch(lab, state, typed) == kit.Verdict(True, level.SHOWN)
    assert watch(level, "file").watch(lab, state, typed) == kit.Verdict(True, level.READ)
    assert kit.git(lab.project, "show", f"{level.PHOBOS_HASH}:{level.FUEL}") == "fuel: 60%\n"
    assert level.check(lab, state, "60%", typed) == kit.Verdict(True, level.RIGHT)


@pytest.mark.parametrize("answer", ["60%", "60", " 60 % ", "fuel: 60%", "FUEL: 60%"])
def test_the_reading_is_accepted_with_or_without_its_percent_sign(answer: str) -> None:
    lab, state = started(level)
    assert level.check(lab, state, answer, []).solved


@pytest.mark.parametrize("answer", ["40%", "75", "fuel: 90%"])
def test_a_reading_from_another_stop_points_to_the_phobos_message(answer: str) -> None:
    lab, state = started(level)
    assert level.check(lab, state, answer, []) == kit.Verdict(False, level.OTHER_STOP)


@pytest.mark.parametrize("answer", ["sixty", "61%", "ccf9485", "-60"])
def test_anything_else_asks_for_the_reading_as_git_printed_it(answer: str) -> None:
    lab, state = started(level)
    assert level.check(lab, state, answer, []) == kit.Verdict(False, level.NOT_A_READING)


def test_a_log_of_the_whole_history_is_not_the_fuel_logs_history() -> None:
    lab, state = started(level)
    assert watch(level, "log").watch(lab, state, typed_in(lab, "git log")) == kit.Verdict(False, level.NOT_LOGGED)
    assert watch(level, "log").watch(lab, state, typed_in(lab, "git log --oneline -- fuel.txt")).solved


def test_showing_another_commit_or_the_file_in_another_commit_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git show HEAD", "git show HEAD:fuel.txt")
    assert watch(level, "show").watch(lab, state, typed) == kit.Verdict(False, level.NOT_SHOWN)
    assert watch(level, "file").watch(lab, state, typed) == kit.Verdict(False, level.NOT_READ)


def test_the_phobos_commit_may_be_named_any_way_git_reads_it() -> None:
    lab, state = started(level)
    typed = typed_in(lab, f"git show {state['phobos']}", "git show HEAD~1:fuel.txt")
    assert watch(level, "show").watch(lab, state, typed).solved
    assert watch(level, "file").watch(lab, state, typed).solved


def test_reading_the_past_leaves_the_folder_as_it_was() -> None:
    lab, state = started(level)
    before = kit.git(lab.project, "status", "--porcelain=v2", "--branch")
    typed_in(lab, "git show ccf9485", "git show ccf9485:fuel.txt")
    assert kit.git(lab.project, "status", "--porcelain=v2", "--branch") == before
    assert (lab.project / level.FUEL).read_text() == "fuel: 40%\n"


def test_a_space_instead_of_a_colon_shows_the_change_and_rama_says_what_the_colon_does() -> None:
    lab, state = started(level)
    [line] = typed_in(lab, "git show ccf9485 fuel.txt")
    assert line["status"] == 0
    rule = reaction(level, line, set(), True, False, remote=False)
    assert rule is not None and rule.text == level.SPACE_NOT_COLON


def test_the_answer_is_read_from_the_lab_without_changing_it() -> None:
    lab, state = started(level)
    assert level.ANSWER(lab, state) == "60%"
