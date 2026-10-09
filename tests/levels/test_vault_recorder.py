from firstcommit import kit
from firstcommit.levels import vault_recorder as level
from level_helpers import started, typed_in, watch


def answer_step() -> kit.AnswerStep:
    """
    Give the step that asks for the commit's hash.

    Returns
    -------
    kit.AnswerStep
        The step.
    """
    step = level.QUEST[1]
    assert isinstance(step, kit.AnswerStep)
    return step


def short(lab: kit.Lab, revision: str) -> str:
    """
    Give a commit's short hash, as `git log --oneline` shows it.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    revision : str
        The commit.

    Returns
    -------
    str
        Its short hash.
    """
    return kit.git(lab.project, "rev-parse", "--short", revision).strip()


def test_the_history_holds_seven_commits_and_only_two_touch_the_oxygen() -> None:
    lab, state = started(level)
    assert len(kit.snapshot(lab.project)["commits"]) == 7
    touching = kit.git(lab.project, "log", "--format=%H", "--", "oxygen.cfg").split()
    assert touching == [state["culprit"], state["first"]]
    assert kit.git(lab.project, "show", "-s", "--format=%s", state["culprit"]).strip() == level.CULPRIT_MESSAGE


def test_the_culprit_moves_between_plays() -> None:
    places = set()
    for _ in range(12):
        lab, state = started(level)
        places.add(kit.git(lab.project, "rev-list", "--count", state["culprit"]).strip())
    assert len(places) > 1


def test_the_hash_is_accepted_whole_or_abbreviated_in_any_case() -> None:
    lab, state = started(level)
    for typed in (state["culprit"], state["culprit"][:7].upper(), f"  {state['culprit'][:4]} "):
        assert answer_step().check(lab, state, typed).solved, typed


def test_the_first_commit_is_the_beginners_wrong_answer_and_is_explained() -> None:
    lab, state = started(level)
    verdict = answer_step().check(lab, state, short(lab, state["first"]))
    assert (verdict.solved, verdict.message) == (False, level.SET_UP)


def test_a_commit_that_only_names_the_oxygen_in_its_message_did_not_touch_the_file() -> None:
    lab, state = started(level)
    decoy = kit.git(lab.project, "log", "--format=%h", "--grep", "oxygen check").split()[0]
    verdict = answer_step().check(lab, state, decoy)
    assert (verdict.solved, verdict.message) == (False, level.OTHER_COMMIT)


def test_text_that_is_no_hash_and_a_hash_of_no_commit_are_told_apart() -> None:
    lab, state = started(level)
    assert answer_step().check(lab, state, "Night tweaks").message == level.NOT_A_HASH
    assert answer_step().check(lab, state, "--all").message == level.NOT_A_HASH
    unknown = next(prefix for prefix in ("0000000", "fffffff", "1234567") if not state["culprit"].startswith(prefix))
    assert answer_step().check(lab, state, unknown).message == level.NO_SUCH_COMMIT


def test_the_author_is_named_by_full_name_or_first_name_in_any_case() -> None:
    lab, state = started(level)
    author = kit.git(lab.project, "show", "-s", "--format=%an", state["culprit"]).strip()
    for typed in (author, author.upper(), f" {author.split()[0].lower()} "):
        assert level.check(lab, state, typed, []).solved, typed
    others = {"Robin Park", "Alex", "Sam Ortiz", "Kai Moreno"} - {author}
    assert not any(level.check(lab, state, name, []).solved for name in others)


def test_reading_the_history_of_the_file_shows_the_culprit_first() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git log oxygen.cfg")
    assert typed[0]["status"] == 0
    assert watch(level, "read").watch(lab, state, typed).solved
    assert kit.git(lab.project, "log", "-1", "--format=%H", "oxygen.cfg").strip() == state["culprit"]


def test_the_answer_is_read_from_the_lab_without_changing_it() -> None:
    lab, state = started(level)
    before = kit.git(lab.project, "status", "--porcelain=v2", "--branch") + kit.git(lab.project, "rev-parse", "HEAD")
    answer = level.ANSWER(lab, state)
    assert level.check(lab, state, answer, typed_in(lab, "git log", f"git log {level.OXYGEN}")).solved
    assert kit.git(lab.project, "status", "--porcelain=v2", "--branch") + kit.git(lab.project, "rev-parse", "HEAD") == before
