import shutil
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from firstcommit import gitcmd, kit
from firstcommit.levels import basics_first_commit as level

HOSTILE = [
    "",
    " ",
    "\x00",
    "\n\n",
    "a" * 100_000,
    "MAIN",
    "\N{FULLWIDTH LATIN SMALL LETTER M}ain",
    "main\x00",
    "$(rm -rf ~)",
    "../../..",
    "HEAD",
    "-n",
    "\N{KELVIN SIGN}",
]


@pytest.fixture
def lab(game_home: Path) -> kit.Lab:
    """
    Give a fresh lab, set up by the level, in a game home that starts like the game's.

    Parameters
    ----------
    game_home : Path
        The test's game home.

    Returns
    -------
    kit.Lab
        The lab, after `level.setup`.
    """
    (game_home / "gitconfig").write_text(gitcmd.BASE_CONFIG)
    root = game_home / "labs" / "basics-first-commit"
    root.mkdir(parents=True)
    lab = kit.Lab(root)
    level.setup(lab)
    return lab


@pytest.fixture
def played(lab: kit.Lab) -> kit.Lab:
    """
    Give a lab where the player has done every quest step.

    Parameters
    ----------
    lab : kit.Lab
        A fresh lab.

    Returns
    -------
    kit.Lab
        The same lab, after the quest.
    """
    play_until(lab, None)
    return lab


def play_until(lab: kit.Lab, stop: str | None) -> None:
    """
    Do the player's part of every quest step before one.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    stop : str | None
        The id of the step to stop before, or None to play the whole quest.
    """
    for quest_step in level.QUEST:
        if quest_step.id == stop:
            return
        level.QUEST_ACTIONS[quest_step.id](lab, {})


def git(lab: kit.Lab, *args: str) -> str:
    """
    Run a git command in the project folder as the player would.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    *args : str
        Arguments after ``git``.

    Returns
    -------
    str
        Standard output.
    """
    return kit.git(lab.project, *args, author=level.PLAYER)


def watch(lab: kit.Lab, step_id: str) -> kit.Verdict:
    """
    Run a watch step's check.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    step_id : str
        The step's id.

    Returns
    -------
    kit.Verdict
        Its verdict.
    """
    check = next(quest_step.watch for quest_step in level.QUEST if quest_step.id == step_id)
    assert check is not None
    return check(lab, {})


def answer(lab: kit.Lab, step_id: str, text: str) -> kit.Verdict:
    """
    Answer an answer step's question.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    step_id : str
        The step's id.
    text : str
        The answer.

    Returns
    -------
    kit.Verdict
        Its verdict.
    """
    check = next(quest_step.check for quest_step in level.QUEST if quest_step.id == step_id)
    assert check is not None
    return check(lab, {}, text)


def check(lab: kit.Lab) -> kit.Verdict:
    """
    Check the level against the lab, as the page does while the player works.

    Parameters
    ----------
    lab : kit.Lab
        The lab.

    Returns
    -------
    kit.Verdict
        The level's verdict.
    """
    return level.check(lab, {}, None)


def append(lab: kit.Lab, name: str, text: str) -> None:
    """
    Add a line to a file in the project folder, creating it if needed.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    name : str
        The file's name.
    text : str
        The line, without its newline.
    """
    with (lab.project / name).open("a") as file:
        file.write(text + "\n")


def test_setup_leaves_an_empty_folder_with_no_repository(lab: kit.Lab) -> None:
    assert list(lab.project.iterdir()) == []
    assert not kit.snapshot(lab.project)["exists"]


def test_the_level_starts_unsolved_and_says_to_create_a_repository(lab: kit.Lab) -> None:
    verdict = check(lab)
    assert not verdict.solved
    assert "git init" in verdict.message


def test_the_quest_alternates_watch_steps_and_two_questions() -> None:
    kinds = {quest_step.id: "watch" if quest_step.watch else "question" for quest_step in level.QUEST}
    assert kinds == {
        "init": "watch",
        "status": "question",
        "file": "watch",
        "stage": "watch",
        "name": "watch",
        "email": "watch",
        "commit": "watch",
        "hash": "question",
    }


def test_the_quest_leads_to_a_solved_level(played: kit.Lab) -> None:
    verdict = check(played)
    assert verdict.solved
    assert verdict.message == level.SOLVED


def test_plain_git_init_starts_on_main_with_the_games_starting_settings(lab: kit.Lab) -> None:
    level.init_repository(lab, {})
    assert kit.snapshot(lab.project)["branch"] == "main"
    assert watch(lab, "init").solved


def test_the_status_question_has_no_answer_before_the_repository_exists(lab: kit.Lab) -> None:
    verdict = answer(lab, "status", "main")
    assert not verdict.solved
    assert "git init" in verdict.message


def test_the_status_question_wants_the_branch_git_status_names(lab: kit.Lab) -> None:
    play_until(lab, "status")
    assert answer(lab, "status", "main").solved
    assert answer(lab, "status", "  main\n").solved
    assert not answer(lab, "status", "master").solved


def test_a_branch_name_in_the_wrong_case_gets_a_hint_about_case(lab: kit.Lab) -> None:
    play_until(lab, "status")
    verdict = answer(lab, "status", "Main")
    assert not verdict.solved
    assert "case" in verdict.message


def test_the_hash_question_has_no_answer_before_the_commit(lab: kit.Lab) -> None:
    play_until(lab, "commit")
    verdict = answer(lab, "hash", "abcd")
    assert not verdict.solved
    assert "git commit" in verdict.message


def test_the_hash_question_accepts_the_players_commit_short_or_whole(played: kit.Lab) -> None:
    full = git(played, "rev-parse", "HEAD").strip()
    assert answer(played, "hash", full[:7]).solved
    assert answer(played, "hash", full).solved
    assert answer(played, "hash", f" {full[:7].upper()} ").solved


def test_the_hash_question_refuses_hashes_of_objects_that_are_not_commits(played: kit.Lab) -> None:
    blob = git(played, "rev-parse", "HEAD:README.md").strip()
    tree = git(played, "rev-parse", "HEAD^{tree}").strip()
    assert not answer(played, "hash", blob[:7]).solved
    assert not answer(played, "hash", tree).solved


def test_typing_the_commit_message_instead_of_the_hash_gets_a_nudge_without_the_hash(played: kit.Lab) -> None:
    verdict = answer(played, "hash", "Add the README")
    assert not verdict.solved
    assert "message" in verdict.message
    assert git(played, "rev-parse", "--short=4", "HEAD").strip() not in verdict.message


IDENTITY = [
    ("name", "user.name", "Your Name", level.NAME_COMMAND),
    ("email", "user.email", "you@example.com", level.EMAIL_COMMAND),
]


@pytest.mark.parametrize(("step_id", "key", "example", "command"), IDENTITY)
def test_the_identity_steps_refuse_the_example_values(
    lab: kit.Lab, step_id: str, key: str, example: str, command: str
) -> None:
    git(lab, "config", "--global", key, example)
    verdict = watch(lab, step_id)
    assert not verdict.solved
    assert "example" in verdict.message
    assert f"`{command}`" in verdict.message


@pytest.mark.parametrize(("step_id", "key", "example", "command"), IDENTITY)
def test_a_missing_identity_gets_a_complete_command_to_set_it(
    lab: kit.Lab, step_id: str, key: str, example: str, command: str
) -> None:
    verdict = watch(lab, step_id)
    assert not verdict.solved
    assert f"`{command}`" in verdict.message
    assert command.endswith(example) or command.endswith(f'"{example}"')


def test_an_identity_set_without_global_also_counts(lab: kit.Lab) -> None:
    level.init_repository(lab, {})
    git(lab, "config", "user.name", "Sam Lee")
    git(lab, "config", "user.email", "sam@example.com")
    assert watch(lab, "name").solved
    assert watch(lab, "email").solved


def test_committing_before_staging_leaves_the_level_unsolved(lab: kit.Lab) -> None:
    play_until(lab, "stage")
    assert kit.git_run(lab.project, "commit", "-m", "Add the README", author=level.PLAYER).returncode != 0
    verdict = check(lab)
    assert not verdict.solved
    assert "staging area" in verdict.message


def test_staging_without_committing_leaves_the_level_unsolved(lab: kit.Lab) -> None:
    play_until(lab, "commit")
    verdict = check(lab)
    assert not verdict.solved
    assert "git commit" in verdict.message


def test_a_commit_without_the_readme_does_not_solve_the_level(lab: kit.Lab) -> None:
    level.init_repository(lab, {})
    append(lab, "notes.txt", "notes")
    git(lab, "add", "notes.txt")
    git(lab, "commit", "-m", "Add notes")
    verdict = check(lab)
    assert not verdict.solved
    assert "README.md" in verdict.message


def test_an_extra_untracked_file_keeps_the_level_unsolved_and_is_named(played: kit.Lab) -> None:
    append(played, "notes.txt", "notes")
    verdict = check(played)
    assert not verdict.solved
    assert "`notes.txt` is" in verdict.message
    assert "untracked" in verdict.message


def test_several_untracked_files_are_named_with_a_plural_verb(played: kit.Lab) -> None:
    for name in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]:
        append(played, name, "x")
    verdict = check(played)
    assert not verdict.solved
    assert "`a.txt`, `b.txt`, `c.txt` and 2 more are" in verdict.message


def test_a_staged_change_that_is_not_committed_keeps_the_level_unsolved(played: kit.Lab) -> None:
    append(played, "README.md", "More.")
    git(played, "add", "README.md")
    verdict = check(played)
    assert not verdict.solved
    assert "staged" in verdict.message


def test_an_edit_after_the_commit_keeps_the_level_unsolved(played: kit.Lab) -> None:
    append(played, "README.md", "More.")
    verdict = check(played)
    assert not verdict.solved
    assert "changed" in verdict.message


def test_committing_the_extra_file_too_solves_the_level(played: kit.Lab) -> None:
    append(played, "notes.txt", "notes")
    git(played, "add", "notes.txt")
    git(played, "commit", "-m", "Add notes")
    assert check(played).solved


def test_an_ignored_file_does_not_keep_the_level_unsolved(played: kit.Lab) -> None:
    append(played, ".gitignore", "*.log")
    git(played, "add", ".gitignore")
    git(played, "commit", "-m", "Ignore logs")
    append(played, "debug.log", "noise")
    assert check(played).solved


def test_a_repository_on_another_branch_gets_the_rename_command(lab: kit.Lab) -> None:
    git(lab, "init", "-b", "master")
    for step_id in ["file", "stage", "commit"]:
        level.QUEST_ACTIONS[step_id](lab, {})
    verdict = check(lab)
    assert not verdict.solved
    assert "git branch -m main" in verdict.message
    git(lab, "branch", "-m", "main")
    assert check(lab).solved


def test_another_branch_while_main_exists_gets_the_switch_command(played: kit.Lab) -> None:
    git(played, "switch", "-c", "draft")
    verdict = check(played)
    assert not verdict.solved
    assert "`git switch main`" in verdict.message
    git(played, "switch", "main")
    assert check(played).solved


def test_a_detached_head_does_not_solve_the_level(played: kit.Lab) -> None:
    git(played, "switch", "--detach")
    verdict = check(played)
    assert not verdict.solved
    assert "`git switch main`" in verdict.message


def test_a_detached_head_without_main_gets_the_command_that_creates_it(lab: kit.Lab) -> None:
    git(lab, "init", "-b", "master")
    for step_id in ["file", "stage", "commit"]:
        level.QUEST_ACTIONS[step_id](lab, {})
    git(lab, "switch", "--detach")
    verdict = check(lab)
    assert not verdict.solved
    assert "`git switch -c main`" in verdict.message
    git(lab, "switch", "-c", "main")
    assert check(lab).solved


def test_a_bare_repository_does_not_count(lab: kit.Lab) -> None:
    git(lab, "init", "--bare")
    verdict = watch(lab, "init")
    assert not verdict.solved
    assert "bare" in verdict.message
    assert not check(lab).solved


def test_a_repository_one_folder_too_high_gets_its_own_nudge(lab: kit.Lab) -> None:
    kit.git(lab.root, "init")
    verdict = watch(lab, "init")
    assert not verdict.solved
    assert "one folder too high" in verdict.message
    assert "one folder too high" in check(lab).message


def test_deleting_the_git_folder_unsolves_the_level(played: kit.Lab) -> None:
    shutil.rmtree(played.project / ".git")
    verdict = check(played)
    assert not verdict.solved
    assert "git init" in verdict.message


def test_checks_never_change_the_repository(played: kit.Lab) -> None:
    append(played, "notes.txt", "notes")
    append(played, "README.md", "More.")
    index = played.project / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns, kit.snapshot(played.project))
    check(played)
    for quest_step in level.QUEST:
        if quest_step.watch:
            quest_step.watch(played, {})
        if quest_step.check:
            quest_step.check(played, {}, "main")
    assert (index.read_bytes(), index.stat().st_mtime_ns, kit.snapshot(played.project)) == before


def test_hostile_answers_never_pass_a_question_once_the_quest_is_done(played: kit.Lab) -> None:
    for text in HOSTILE:
        assert not answer(played, "status", text).solved
        assert not answer(played, "hash", text).solved
        assert level.check(played, {}, text).solved


@pytest.mark.slow
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(text=st.text())
def test_the_questions_answer_any_text_with_a_message(played: kit.Lab, text: str) -> None:
    for step_id in ["status", "hash"]:
        verdict = answer(played, step_id, text)
        assert verdict.message
