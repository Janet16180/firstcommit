from firstcommit import kit
from firstcommit.levels import undo_movelog as level
from level_helpers import reaction, started, typed_in, watch

SOLUTION = ("git log --oneline", "git reflog", "git branch survey HEAD@{1}", "git switch survey", "git reflog")


def test_main_is_back_on_origin_main_and_no_branch_leads_to_the_survey_commits() -> None:
    lab, state = started(level)
    assert kit.git(lab.project, "rev-parse", "main").strip() == state["origin"]
    assert [ghost["hash"] for ghost in kit.ghosts(lab.project)][0] == state["tip"]
    assert "Survey" not in kit.git(lab.project, "log", "--oneline")


def test_the_move_log_reads_clone_two_commits_and_the_reset_with_survey_day_2_one_move_back() -> None:
    lab, state = started(level)
    messages = kit.git(lab.project, "reflog", "--format=%gs").splitlines()
    assert [message.split(":")[0] for message in messages] == ["reset", "commit", "commit", "clone"]
    assert kit.git(lab.project, "rev-parse", "HEAD@{1}").strip() == state["tip"]


def test_the_hints_lines_bring_both_commits_back_on_survey_and_shift_the_numbers() -> None:
    lab, state = started(level)
    typed = typed_in(lab, *SOLUTION)
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.READ_AGAIN)
    assert kit.ghosts(lab.project) == []
    assert kit.git(lab.project, "rev-parse", "HEAD@{2}").strip() == state["tip"]


def test_the_wrong_line_names_start_the_project_and_rama_points_one_move_back() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git reflog", "git branch survey HEAD@{0}")
    assert watch(level, "name").watch(lab, state, typed).message == level.WRONG_LINE
    rule = reaction(level, typed[-1], set(), True, False)
    assert rule is not None and rule.text == level.WRONG_LINE_SAID


def test_the_hash_from_the_move_log_works_as_well_as_its_name() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log --oneline", "git reflog", f"git branch survey {state['tip'][:7]}", "git checkout survey", "git reflog")
    assert level.check(lab, state, None, typed).solved


def test_erasing_the_survey_commits_is_lost_and_rama_warns_first() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git reflog expire --expire=now --all", "git gc --prune=now -q")
    rule = reaction(level, typed[0], set(), True, False)
    assert rule is not None and rule.text == level.WIPE
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.ERASED)
