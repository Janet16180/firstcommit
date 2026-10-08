import re

from firstcommit import kit, runner
from firstcommit.levels import vault_look as level
from level_helpers import arrived, reaction, started, typed_in, watch


def answer_step() -> kit.AnswerStep:
    """
    Give the step that asks for the file that changed by accident.

    Returns
    -------
    kit.AnswerStep
        The step.
    """
    step = level.QUEST[1]
    assert isinstance(step, kit.AnswerStep)
    return step


def test_the_overnight_edits_arrive_once_the_page_has_looked() -> None:
    lab, state = started(level)
    assert kit.unstaged(kit.snapshot(lab.project)) == []
    assert watch(level, "diff").watch(lab, state, []).message == level.WAITING
    lab, _ = arrived(level)
    assert kit.unstaged(kit.snapshot(lab.project)) == ["engine.cfg", "route.txt"]


def test_diff_stage_the_route_check_and_commit_solves_the_level() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git diff", "git add route.txt", "git diff --staged", 'git commit -m "Add the Phobos stop"')
    assert [line["status"] for line in typed] == [0, 0, 0, 0]
    assert level.check(lab, state, None, typed).solved
    assert kit.unstaged(kit.snapshot(lab.project)) == ["engine.cfg"]


def test_the_accidental_change_is_named_by_its_file_and_the_route_is_told_apart() -> None:
    lab, state = arrived(level)
    assert all(answer_step().check(lab, state, name).solved for name in ("engine.cfg", " Engine.cfg ", "`engine.cfg`", "engine"))
    assert answer_step().check(lab, state, "route.txt").message == level.ROUTE_IS_MEANT
    assert answer_step().check(lab, state, "power=99999").message == level.NOT_A_FILE


def test_staging_everything_takes_the_accidental_change_too_and_restore_staged_takes_it_back_out() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git add .")
    rule = reaction(level, typed[0], {"file-staged"}, True, True)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.EVERYTHING_STAGED)
    assert watch(level, "stage").watch(lab, state, typed).message == level.ACCIDENT_STAGED
    typed += typed_in(lab, "git restore --staged engine.cfg")
    assert typed[-1]["status"] == 0 and watch(level, "stage").watch(lab, state, typed).solved
    assert (lab.project / "engine.cfg").read_text() == "power=99999\n"


def test_a_staged_check_before_the_add_does_not_count() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git diff --staged", "git add route.txt")
    assert watch(level, "check").watch(lab, state, typed).message == level.NOT_CHECKED


def test_the_accidental_change_sealed_in_a_commit_is_said_and_the_level_offers_to_start_again() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git add .", 'git commit -m "Overnight"')
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.ACCIDENT_SEALED)


def test_a_plain_diff_after_staging_the_route_shows_only_the_engine() -> None:
    lab, _ = arrived(level)
    kit.git(lab.project, "add", "route.txt")
    assert kit.git(lab.project, "diff", "--name-only").split() == ["engine.cfg"]
    assert kit.git(lab.project, "diff", "--staged", "--name-only").split() == ["route.txt"]


def test_the_level_speaks_of_an_accidental_change_never_of_a_typo_in_either_language() -> None:
    entry = runner.load(level)
    english = entry.texts["en"]
    words = [english.briefing, english.debrief, *english.hints, *english.scene]
    words += [field for step in english.steps.values() for field in (step.text, step.question)]
    words += [step.text for step in level.QUEST] + [step.question for step in level.QUEST if isinstance(step, kit.AnswerStep)]
    words += [value for name, value in vars(level).items() if name.isupper() and isinstance(value, str)]
    spanish = entry.texts["es"]
    words += [spanish.briefing, spanish.debrief, *spanish.hints, *spanish.scene, *spanish.messages.values()]
    words += [field for step in spanish.steps.values() for field in (step.text, step.question)]
    found = [text for text in words if re.search(r"typo|errata", text, re.IGNORECASE)]
    assert not found
    assert "route.txt" in english.briefing and "route.txt" in spanish.briefing
