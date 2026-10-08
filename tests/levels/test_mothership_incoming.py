from firstcommit import kit
from firstcommit.levels import mothership_incoming as level
from level_helpers import arrived, started, typed_in, watch


def test_alex_pushes_once_the_page_has_looked_and_your_origin_main_stays_behind() -> None:
    lab, state = started(level)
    assert kit.git(lab.github, "rev-parse", "main").strip() == state["start"]
    lab, state = arrived(level)
    alex = kit.git(lab.github, "rev-parse", "main").strip()
    assert alex != state["start"] and kit.git(lab.github, "log", "-1", "--format=%an", "main").strip() == "Alex"
    assert kit.git(lab.project, "rev-parse", "origin/main").strip() == state["start"]


def test_nothing_counts_before_alex_has_pushed() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git status", "git fetch", "git status", "git pull")
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.message) == (False, level.WAITING)
    assert watch(level, "status").watch(lab, state, typed).message == level.WAITING


def test_status_fetch_status_pull_solves_the_level_with_alexs_line_in_the_notes() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git fetch", "git status", "git pull")
    assert [line["status"] for line in typed] == [0, 0, 0, 0]
    assert level.check(lab, state, None, typed).solved
    assert "Alex" in (lab.project / "notes.txt").read_text()


def test_status_before_the_fetch_says_up_to_date_and_after_it_behind() -> None:
    lab, _ = arrived(level)
    assert "up to date" in kit.git(lab.project, "status")
    kit.git(lab.project, "fetch", "-q")
    assert "behind 'origin/main' by 1 commit" in kit.git(lab.project, "status")


def test_a_status_before_the_fetch_does_not_count_as_the_second_look() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git fetch")
    verdict = watch(level, "again").watch(lab, state, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_AGAIN)


def test_pulling_first_is_safe_and_meets_the_fetch_and_the_pull_goals() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git pull")
    assert watch(level, "fetch").watch(lab, state, typed).solved
    assert level.check(lab, state, None, typed).solved


def test_the_prediction_passes_with_any_option() -> None:
    assert all(kit.choose(level.GUESS, option).solved for option in level.GUESS.options)
