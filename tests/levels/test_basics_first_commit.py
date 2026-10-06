import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from firstcommit import kit
from firstcommit.levels import basics_first_commit as level

PLAYER = kit.Person("Sam Lee", "sam@example.com")
HOSTILE = [
    "",
    " ",
    "\x00",
    "\n\n",
    "a" * 100_000,
    "MAIN",
    "ｍａｉｎ",
    "main\x00",
    "$(rm -rf ~)",
    "../../..",
    "HEAD",
    "-n",
    "K",
]


@pytest.fixture
def lab(game_home: Path) -> kit.Lab:
    """
    Give a fresh lab where the game keeps labs, set up by the level.

    Parameters
    ----------
    game_home : Path
        The test's game home.

    Returns
    -------
    kit.Lab
        The lab, after `level.setup`.
    """
    root = game_home / "labs" / "basics-first-commit"
    root.mkdir(parents=True)
    lab = kit.Lab(root)
    level.setup(lab)
    return lab


@pytest.fixture
def played(lab: kit.Lab) -> kit.Lab:
    """
    Give a lab where the player has done every quest action.

    Parameters
    ----------
    lab : kit.Lab
        A fresh lab.

    Returns
    -------
    kit.Lab
        The same lab, after the quest.
    """
    play_all(lab)
    return lab


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
    return kit.git(lab.project, *args, author=PLAYER)


def init(lab: kit.Lab) -> None:
    """Create the repository, as the quest asks."""
    git(lab, "init", "-b", "main")


def write_readme(lab: kit.Lab) -> None:
    """Create the quest's file."""
    (lab.project / "README.md").write_text("# My project\n")


def stage(lab: kit.Lab) -> None:
    """Stage the quest's file."""
    git(lab, "add", "README.md")


def set_name(lab: kit.Lab) -> None:
    """Set the player's name in the game's global settings."""
    git(lab, "config", "--global", "user.name", PLAYER.name)


def set_email(lab: kit.Lab) -> None:
    """Set the player's email in the game's global settings."""
    git(lab, "config", "--global", "user.email", PLAYER.email)


def commit(lab: kit.Lab) -> None:
    """Commit what is staged."""
    git(lab, "commit", "-m", "Add the README")


PLAYTHROUGH: list[tuple[str, Callable[[kit.Lab], None]]] = [
    ("init", init),
    ("file", write_readme),
    ("stage", stage),
    ("name", set_name),
    ("email", set_email),
    ("commit", commit),
]


def step(step_id: str) -> kit.Step:
    """
    Find a quest step by id.

    Parameters
    ----------
    step_id : str
        The step's id.

    Returns
    -------
    kit.Step
        The step.
    """
    return next(candidate for candidate in level.QUEST if candidate.id == step_id)


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
    check = step(step_id).watch
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
    check = step(step_id).check
    assert check is not None
    return check(lab, {}, text)


def play_until(lab: kit.Lab, step_id: str) -> None:
    """
    Do every quest action that comes before a step.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    step_id : str
        The step to stop before.
    """
    for done_id, action in PLAYTHROUGH:
        if done_id == step_id:
            return
        action(lab)


def play_all(lab: kit.Lab) -> None:
    """
    Do every quest action.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    """
    for _, action in PLAYTHROUGH:
        action(lab)


def head(lab: kit.Lab) -> str:
    """
    Give the full hash of the project's last commit.

    Parameters
    ----------
    lab : kit.Lab
        The lab.

    Returns
    -------
    str
        The hash.
    """
    return git(lab, "rev-parse", "HEAD").strip()


def test_setup_leaves_an_empty_folder_with_no_repository(lab: kit.Lab) -> None:
    assert list(lab.project.iterdir()) == []
    assert not kit.snapshot(lab.project)["exists"]


def test_the_level_starts_unsolved_and_says_to_create_a_repository(lab: kit.Lab) -> None:
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "git init -b main" in verdict.message


def test_every_quest_step_is_a_watch_or_a_question() -> None:
    kinds = {quest_step.id: (quest_step.watch is not None, quest_step.check is not None) for quest_step in level.QUEST}
    assert kinds == {
        "init": (True, False),
        "status": (False, True),
        "file": (True, False),
        "stage": (True, False),
        "name": (True, False),
        "email": (True, False),
        "commit": (True, False),
        "hash": (False, True),
    }


@pytest.mark.parametrize("step_id", [step_id for step_id, _ in PLAYTHROUGH])
def test_a_watch_step_passes_only_once_the_player_has_done_it(lab: kit.Lab, step_id: str) -> None:
    play_until(lab, step_id)
    before = watch(lab, step_id)
    dict(PLAYTHROUGH)[step_id](lab)
    after = watch(lab, step_id)
    assert not before.solved
    assert before.message
    assert after.solved


def test_the_status_question_has_no_answer_before_the_repository_exists(lab: kit.Lab) -> None:
    verdict = answer(lab, "status", "main")
    assert not verdict.solved
    assert "git init" in verdict.message


def test_the_status_question_wants_the_branch_git_status_names(lab: kit.Lab) -> None:
    init(lab)
    assert answer(lab, "status", "main").solved
    assert answer(lab, "status", "  main\n").solved
    assert not answer(lab, "status", "master").solved
    assert not answer(lab, "status", "").solved


def test_a_branch_name_in_the_wrong_case_gets_a_hint_about_case(lab: kit.Lab) -> None:
    init(lab)
    verdict = answer(lab, "status", "Main")
    assert not verdict.solved
    assert "case" in verdict.message


def test_the_hash_question_has_no_answer_before_the_commit(lab: kit.Lab) -> None:
    play_until(lab, "commit")
    verdict = answer(lab, "hash", "abcd")
    assert not verdict.solved
    assert "git commit" in verdict.message


def test_the_hash_question_accepts_the_players_commit_short_or_whole(lab: kit.Lab) -> None:
    play_all(lab)
    full = head(lab)
    assert answer(lab, "hash", full[:7]).solved
    assert answer(lab, "hash", full).solved
    assert answer(lab, "hash", f" {full[:7].upper()} ").solved


def test_the_hash_question_refuses_hashes_of_objects_that_are_not_commits(lab: kit.Lab) -> None:
    play_all(lab)
    blob = git(lab, "rev-parse", "HEAD:README.md").strip()
    tree = git(lab, "rev-parse", "HEAD^{tree}").strip()
    assert not answer(lab, "hash", blob[:7]).solved
    assert not answer(lab, "hash", tree).solved


def test_typing_the_commit_message_instead_of_the_hash_gets_a_nudge(lab: kit.Lab) -> None:
    play_all(lab)
    verdict = answer(lab, "hash", "Add the README")
    assert not verdict.solved
    assert "message" in verdict.message
    assert head(lab)[:4] not in verdict.message


@pytest.mark.parametrize(
    ("step_id", "key", "example"), [("name", "user.name", "Your Name"), ("email", "user.email", "you@example.com")]
)
def test_the_identity_steps_refuse_the_example_values(lab: kit.Lab, step_id: str, key: str, example: str) -> None:
    git(lab, "config", "--global", key, example)
    verdict = watch(lab, step_id)
    assert not verdict.solved
    assert "example" in verdict.message


def test_an_identity_set_without_global_also_counts(lab: kit.Lab) -> None:
    init(lab)
    git(lab, "config", "user.name", PLAYER.name)
    git(lab, "config", "user.email", PLAYER.email)
    assert watch(lab, "name").solved
    assert watch(lab, "email").solved


def test_the_quest_leads_to_a_solved_level(lab: kit.Lab) -> None:
    play_all(lab)
    verdict = level.check(lab, {}, None)
    assert verdict.solved
    assert verdict.message == level.SOLVED


def test_solve_solves_the_level_and_passes_every_step(lab: kit.Lab) -> None:
    assert level.solve(lab, {}) is None
    assert level.check(lab, {}, None).solved
    for step_id, _ in PLAYTHROUGH:
        assert watch(lab, step_id).solved, step_id
    assert answer(lab, "status", "main").solved
    assert answer(lab, "hash", head(lab)[:7]).solved


def test_committing_before_staging_leaves_the_level_unsolved(lab: kit.Lab) -> None:
    init(lab)
    write_readme(lab)
    assert kit.git_run(lab.project, "commit", "-m", "Add the README", author=PLAYER).returncode != 0
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "staging area" in verdict.message


def test_staging_without_committing_leaves_the_level_unsolved(lab: kit.Lab) -> None:
    init(lab)
    write_readme(lab)
    stage(lab)
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "git commit" in verdict.message


def test_a_commit_without_the_readme_does_not_solve_the_level(lab: kit.Lab) -> None:
    init(lab)
    (lab.project / "notes.txt").write_text("notes\n")
    git(lab, "add", "notes.txt")
    git(lab, "commit", "-m", "Add notes")
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "README.md" in verdict.message


def test_an_extra_untracked_file_keeps_the_level_unsolved_and_is_named(lab: kit.Lab) -> None:
    level.solve(lab, {})
    (lab.project / "notes.txt").write_text("notes\n")
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "`notes.txt` is" in verdict.message
    assert "untracked" in verdict.message


def test_several_untracked_files_are_named_with_a_plural_verb(lab: kit.Lab) -> None:
    level.solve(lab, {})
    for name in ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]:
        (lab.project / name).write_text("x\n")
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "`a.txt`, `b.txt`, `c.txt` and 2 more are" in verdict.message


def test_a_staged_change_that_is_not_committed_keeps_the_level_unsolved(lab: kit.Lab) -> None:
    level.solve(lab, {})
    with (lab.project / "README.md").open("a") as readme:
        readme.write("More.\n")
    stage(lab)
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "staged" in verdict.message


def test_an_edit_after_the_commit_keeps_the_level_unsolved(lab: kit.Lab) -> None:
    level.solve(lab, {})
    with (lab.project / "README.md").open("a") as readme:
        readme.write("More.\n")
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "changed" in verdict.message


def test_committing_the_extra_file_too_solves_the_level(lab: kit.Lab) -> None:
    level.solve(lab, {})
    (lab.project / "notes.txt").write_text("notes\n")
    git(lab, "add", "notes.txt")
    git(lab, "commit", "-m", "Add notes")
    assert level.check(lab, {}, None).solved


def test_an_ignored_file_does_not_keep_the_level_unsolved(lab: kit.Lab) -> None:
    level.solve(lab, {})
    (lab.project / ".gitignore").write_text("*.log\n")
    git(lab, "add", ".gitignore")
    git(lab, "commit", "-m", "Ignore logs")
    (lab.project / "debug.log").write_text("noise\n")
    assert level.check(lab, {}, None).solved


def test_a_repository_on_another_branch_gets_the_rename_command(lab: kit.Lab) -> None:
    git(lab, "init", "-b", "master")
    write_readme(lab)
    stage(lab)
    commit(lab)
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "git branch -m main" in verdict.message
    git(lab, "branch", "-m", "main")
    assert level.check(lab, {}, None).solved


def test_a_detached_head_does_not_solve_the_level(lab: kit.Lab) -> None:
    level.solve(lab, {})
    git(lab, "switch", "--detach")
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "git switch main" in verdict.message


def test_a_bare_repository_does_not_count(lab: kit.Lab) -> None:
    git(lab, "init", "--bare", "-b", "main")
    verdict = watch(lab, "init")
    assert not verdict.solved
    assert "bare" in verdict.message
    assert not level.check(lab, {}, None).solved


def test_deleting_the_git_folder_unsolves_the_level(lab: kit.Lab) -> None:
    level.solve(lab, {})
    shutil.rmtree(lab.project / ".git")
    verdict = level.check(lab, {}, None)
    assert not verdict.solved
    assert "git init" in verdict.message


def test_every_check_survives_a_deleted_project_folder(lab: kit.Lab) -> None:
    lab.project.rmdir()
    verdicts = [level.check(lab, {}, None)]
    verdicts += [watch(lab, quest_step.id) for quest_step in level.QUEST if quest_step.watch]
    verdicts += [answer(lab, quest_step.id, "main") for quest_step in level.QUEST if quest_step.check]
    assert not any(verdict.solved for verdict in verdicts)


def test_checking_never_changes_the_repository(lab: kit.Lab) -> None:
    play_all(lab)
    (lab.project / "notes.txt").write_text("notes\n")
    with (lab.project / "README.md").open("a") as readme:
        readme.write("More.\n")
    index = lab.project / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns, kit.snapshot(lab.project))
    level.check(lab, {}, None)
    for step_id, _ in PLAYTHROUGH:
        watch(lab, step_id)
    answer(lab, "status", "main")
    answer(lab, "hash", "abcd")
    assert (index.read_bytes(), index.stat().st_mtime_ns, kit.snapshot(lab.project)) == before


def test_hostile_answers_are_refused_without_crashing(played: kit.Lab) -> None:
    for text in HOSTILE:
        assert not answer(played, "status", text).solved
        assert not answer(played, "hash", text).solved
        assert level.check(played, {}, text).solved


@pytest.mark.slow
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(text=st.text())
def test_the_questions_never_crash_on_any_text(played: kit.Lab, text: str) -> None:
    for step_id in ["status", "hash"]:
        verdict = answer(played, step_id, text)
        assert isinstance(verdict.message, str)
        assert verdict.message
