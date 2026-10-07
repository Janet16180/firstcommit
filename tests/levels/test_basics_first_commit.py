import re
import shutil
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from firstcommit import demos, gitcmd, kit, reactions
from firstcommit.levels import basics_first_commit as level

CODE_SPAN = re.compile(r"`[^`]*`")
SENTENCE_END = re.compile(r"[.!?](?=\s|$)")
LESSON_CHANGES = [
    ("history", set[str]()),
    ("init", {"repository"}),
    ("file", {"working folder"}),
    ("nothing-staged", set[str]()),
    ("add", {"staging area"}),
    ("commit", {"commits"}),
    ("edit", {"working folder"}),
    ("add-again", {"staging area"}),
    ("second-commit", {"commits"}),
]
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
        level.QUEST_ACTIONS[quest_step.id](lab, {}, [])


def sentences(text: str) -> int:
    """
    Count the sentences of a text's prose, leaving out its verbatim lines and code spans.

    A paragraph that ends with a colon, before the command it introduces, counts as a sentence.

    Parameters
    ----------
    text : str
        Text in the game's layout (AUTHORING.md section 6).

    Returns
    -------
    int
        How many sentences end in it.
    """
    count = 0
    for paragraph in text.strip().split("\n\n"):
        prose = " ".join(
            line for line in paragraph.splitlines() if line.strip() and not line.startswith((" ", "\t", "$ "))
        )
        prose = CODE_SPAN.sub("code", prose).strip()
        count += len(SENTENCE_END.findall(prose)) + prose.endswith(":")
    return count


def versions(snap: kit.Snapshot, area: level.Area) -> dict[str, str]:
    """
    Give the content id of every file one place holds.

    Parameters
    ----------
    snap : kit.Snapshot
        The repository.
    area : level.Area
        The place: ``"folder"``, ``"index"`` or ``"head"``.

    Returns
    -------
    dict[str, str]
        Each path the place holds, with its blob id.
    """
    return {entry["path"]: blob for entry in snap["files"] if (blob := entry[area]) is not None}


def changed_places(before: kit.Snapshot, after: kit.Snapshot) -> set[str]:
    """
    Name the places of the picture that changed between two snapshots.

    Parameters
    ----------
    before : kit.Snapshot
        The repository before a slide's commands.
    after : kit.Snapshot
        The repository after them.

    Returns
    -------
    set[str]
        Some of "repository" (it appeared or went), "working folder", "staging area" and
        "commits".
    """
    changes = {
        "repository": before["exists"] != after["exists"],
        "working folder": versions(before, "folder") != versions(after, "folder"),
        "staging area": versions(before, "index") != versions(after, "index"),
        "commits": len(before["commits"]) != len(after["commits"]),
    }
    return {place for place, changed in changes.items() if changed}


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
    step = next(quest_step for quest_step in level.QUEST if quest_step.id == step_id)
    assert isinstance(step, kit.WatchStep)
    return step.watch(lab, {}, [])


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
    step = next(quest_step for quest_step in level.QUEST if quest_step.id == step_id)
    assert isinstance(step, kit.AnswerStep)
    return step.check(lab, {}, text)


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
    return level.check(lab, {}, None, [])


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
    kinds = {
        quest_step.id: "watch" if isinstance(quest_step, kit.WatchStep) else "question" for quest_step in level.QUEST
    }
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


def test_the_quest_sets_the_identity_before_there_is_anything_to_commit() -> None:
    ids = [quest_step.id for quest_step in level.QUEST]
    assert ids.index("name") < ids.index("file")
    assert ids.index("email") < ids.index("file")


def test_the_quest_leads_to_a_solved_level(played: kit.Lab) -> None:
    verdict = check(played)
    assert verdict.solved
    assert verdict.message == level.SOLVED


def test_the_reference_solution_plays_every_quest_step_identity_included(lab: kit.Lab) -> None:
    assert level.solve(lab, {}, []) is None
    assert git(lab, "config", "--global", "user.name").strip() == level.PLAYER.name
    assert git(lab, "config", "--global", "user.email").strip() == level.PLAYER.email
    assert check(lab).solved


def test_plain_git_init_starts_on_main_with_the_games_starting_settings(lab: kit.Lab) -> None:
    level.init_repository(lab, {}, [])
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
    assert "capital" in verdict.message
    assert "case-sensitive" not in verdict.message


def test_the_whole_status_line_gets_a_nudge_to_type_only_the_branch(lab: kit.Lab) -> None:
    play_until(lab, "status")
    verdict = answer(lab, "status", "On branch main")
    assert not verdict.solved
    assert "only" in verdict.message
    assert "not the branch" not in verdict.message


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


def test_the_whole_log_line_gets_a_nudge_to_type_only_the_hash(played: kit.Lab) -> None:
    short = git(played, "rev-parse", "--short", "HEAD").strip()
    for line in [f"{short} Add the README", f"{short} (HEAD -> main) Add the README"]:
        verdict = answer(played, "hash", line)
        assert not verdict.solved
        assert "only" in verdict.message
        assert short not in verdict.message


def test_a_hash_start_shorter_than_git_accepts_is_not_called_wrong(played: kit.Lab) -> None:
    full = git(played, "rev-parse", "HEAD").strip()
    assert kit.git_run(played.project, "rev-parse", "--verify", "-q", full[:3]).returncode != 0
    verdict = answer(played, "hash", full[:3])
    assert not verdict.solved
    assert "4 characters" in verdict.message
    assert "not the start" not in verdict.message


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
    level.init_repository(lab, {}, [])
    git(lab, "config", "user.name", "Sam Lee")
    git(lab, "config", "user.email", "sam@example.com")
    assert watch(lab, "name").solved
    assert watch(lab, "email").solved


def test_a_readme_in_the_wrong_letter_case_gets_the_command_that_renames_it(lab: kit.Lab) -> None:
    level.init_repository(lab, {}, [])
    append(lab, "readme.md", "# My project")
    verdict = watch(lab, "file")
    assert not verdict.solved
    assert "`mv readme.md README.md`" in verdict.message
    git(lab, "add", "readme.md")
    assert "`git mv readme.md README.md`" in watch(lab, "file").message
    git(lab, "mv", "readme.md", "README.md")
    assert watch(lab, "file").solved
    assert watch(lab, "stage").solved


def test_a_readme_in_the_wrong_letter_case_is_named_as_the_player_wrote_it(lab: kit.Lab) -> None:
    level.init_repository(lab, {}, [])
    append(lab, "Readme.MD", "# My project")
    assert "`mv Readme.MD README.md`" in check(lab).message


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
    assert '`git commit -m "Add the README"`' in verdict.message


def test_a_commit_without_the_readme_does_not_solve_the_level(lab: kit.Lab) -> None:
    level.init_repository(lab, {}, [])
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


def test_a_change_unstaged_with_restore_is_not_said_to_follow_the_last_add(played: kit.Lab) -> None:
    append(played, "README.md", "More.")
    git(played, "add", "README.md")
    git(played, "restore", "--staged", "README.md")
    verdict = check(played)
    assert not verdict.solved
    assert "not staged" in verdict.message
    assert "git add`." not in verdict.message


def test_a_readme_deleted_from_the_folder_gets_the_command_that_brings_it_back(played: kit.Lab) -> None:
    (played.project / "README.md").unlink()
    assert kit.unstaged(kit.snapshot(played.project)) == ["README.md"]
    verdict = check(played)
    assert not verdict.solved
    assert "`git restore README.md`" in verdict.message
    git(played, "restore", "README.md")
    assert check(played).solved


def test_another_file_deleted_from_the_folder_is_named_as_a_deletion(played: kit.Lab) -> None:
    append(played, "notes.txt", "notes")
    git(played, "add", "notes.txt")
    git(played, "commit", "-m", "Add notes")
    (played.project / "notes.txt").unlink()
    verdict = check(played)
    assert not verdict.solved
    assert "`notes.txt` is deleted from the working folder" in verdict.message
    git(played, "add", "notes.txt")
    git(played, "commit", "-m", "Remove the notes")
    assert check(played).solved


def test_a_conflicted_file_keeps_the_level_unsolved(played: kit.Lab) -> None:
    git(played, "switch", "-c", "other")
    append(played, "README.md", "Theirs.")
    git(played, "commit", "-a", "-m", "Theirs")
    git(played, "switch", "main")
    append(played, "README.md", "Ours.")
    git(played, "commit", "-a", "-m", "Ours")
    assert kit.git_run(played.project, "merge", "other").returncode != 0
    assert kit.conflicted(kit.snapshot(played.project)) == ["README.md"]
    verdict = check(played)
    assert not verdict.solved
    assert "`README.md` is in conflict" in verdict.message


def test_a_repository_inside_the_project_folder_keeps_the_level_unsolved(played: kit.Lab) -> None:
    git(played, "init", "project")
    assert git(played, "status", "--porcelain").strip() == "?? project/"
    verdict = check(played)
    assert not verdict.solved
    assert "`project/` is a folder with its own repository" in verdict.message


def test_a_changed_file_mode_keeps_the_level_unsolved(played: kit.Lab) -> None:
    (played.project / "README.md").chmod(0o755)
    assert git(played, "status", "--porcelain").strip() == "M README.md"
    verdict = check(played)
    assert not verdict.solved
    assert "`git status` still lists `README.md`" in verdict.message
    git(played, "add", "README.md")
    assert not check(played).solved
    git(played, "commit", "-m", "Make the README executable")
    assert check(played).solved


@pytest.mark.parametrize("name", ["a`b.txt", "line\nbreak.txt", "- bullet.txt"])
def test_a_file_name_the_player_chose_is_shown_exactly(played: kit.Lab, name: str) -> None:
    append(played, name, "x")
    verdict = check(played)
    assert not verdict.solved
    assert kit.code(name) in verdict.message


def test_a_branch_name_the_player_chose_is_shown_exactly(played: kit.Lab) -> None:
    git(played, "switch", "-c", "draft`1")
    verdict = check(played)
    assert not verdict.solved
    assert kit.code("draft`1") in verdict.message


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
        level.QUEST_ACTIONS[step_id](lab, {}, [])
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
        level.QUEST_ACTIONS[step_id](lab, {}, [])
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


def test_git_init_project_inside_the_project_folder_gets_its_own_nudge(lab: kit.Lab) -> None:
    git(lab, "init", "project")
    verdict = watch(lab, "init")
    assert not verdict.solved
    assert "`git init project`" in verdict.message
    assert "`git init project`" in check(lab).message


def test_deleting_the_git_folder_unsolves_the_level(played: kit.Lab) -> None:
    shutil.rmtree(played.project / ".git")
    verdict = check(played)
    assert not verdict.solved
    assert "git init" in verdict.message


@pytest.mark.slow
def test_checks_never_change_the_repository(played: kit.Lab) -> None:
    append(played, "notes.txt", "notes")
    append(played, "README.md", "More.")
    index = played.project / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns, kit.snapshot(played.project))
    check(played)
    for quest_step in level.QUEST:
        if isinstance(quest_step, kit.WatchStep):
            quest_step.watch(played, {}, [])
        if isinstance(quest_step, kit.AnswerStep):
            quest_step.check(played, {}, "main")
    assert (index.read_bytes(), index.stat().st_mtime_ns, kit.snapshot(played.project)) == before


@pytest.mark.slow
def test_hostile_answers_never_pass_a_question_once_the_quest_is_done(played: kit.Lab) -> None:
    for text in HOSTILE:
        assert not answer(played, "status", text).solved
        assert not answer(played, "hash", text).solved
        assert level.check(played, {}, text, []).solved


@pytest.mark.slow
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(text=st.text())
def test_the_questions_answer_any_text_with_a_message(played: kit.Lab, text: str) -> None:
    for step_id in ["status", "hash"]:
        verdict = answer(played, step_id, text)
        assert verdict.message


def test_the_lesson_shows_one_change_per_slide_in_order() -> None:
    assert [slide.id for slide in level.LESSON] == [slide_id for slide_id, _ in LESSON_CHANGES]


def test_each_slide_changes_exactly_the_place_it_is_about() -> None:
    frames = demos.frames(level.LESSON)
    assert not frames[0]["map"]["exists"]
    for (slide_id, expected), before, after in zip(LESSON_CHANGES[1:], frames[:-1], frames[1:], strict=True):
        assert changed_places(before["map"], after["map"]) == expected, slide_id


def test_every_slide_draws_the_places_so_a_commit_is_one_picture_throughout() -> None:
    assert [slide.view for slide in level.LESSON] == ["places"] * len(level.LESSON)


def test_every_slide_reads_its_picture_in_at_most_three_short_sentences() -> None:
    for slide in level.LESSON:
        assert 1 <= sentences(slide.text) <= 3, slide.id


def test_every_quest_step_says_what_to_do_in_two_sentences_and_leaves_the_command_to_its_box() -> None:
    for quest_step in level.QUEST:
        assert 1 <= sentences(quest_step.text) <= 2, quest_step.id
        assert quest_step.command, quest_step.id
        assert not any(line.startswith((" ", "\t", "$ ")) for line in quest_step.text.splitlines() if line.strip()), (
            quest_step.id
        )


def test_gits_own_terms_and_the_details_are_folded_into_more() -> None:
    shown = " ".join(" ".join(item.text.split()) for item in [*level.LESSON, *level.QUEST])
    folded = " ".join(" ".join(item.more.split()) for item in [*level.LESSON, *level.QUEST])
    for term in ["working tree", "index", "init.defaultBranch"]:
        assert term not in shown, term
        assert term in folded, term
    assert all(item.more for item in [*level.LESSON, *level.QUEST])


@pytest.mark.parametrize("key", ["name", "email"])
def test_setting_the_identity_is_acknowledged_and_only_reading_it_is_not(key: str) -> None:
    rules = (*level.REACTIONS, *reactions.RULES)
    setting = reactions.react({"line": f'git config --global user.{key} "Robin Park"', "status": 0}, (), True, rules)
    reading = reactions.react({"line": f"git config --global user.{key}", "status": 0}, (), True, rules)
    assert setting is not None and key in setting.text
    assert reading is None
