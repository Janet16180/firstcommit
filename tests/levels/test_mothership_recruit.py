from firstcommit import kit
from firstcommit.levels import mothership_recruit as level
from level_helpers import reaction, started, watch


def test_setup_leaves_only_the_outpost_on_the_mothership_with_five_to_eight_commits_by_three_people() -> None:
    lab, state = started(level)
    assert not lab.project.exists()
    assert sorted(path.name for path in lab.root.iterdir()) == ["github.com"]
    authors = kit.git(lab.github, "log", "--format=%an", "main").splitlines()
    assert level.FEWEST <= len(authors) <= len(level.HISTORY)
    assert set(authors) == {person.name for person in level.PEOPLE}


def test_the_clone_holds_every_commit_and_the_count_is_the_answer() -> None:
    lab, state = started(level)
    kit.type_line(lab.root, "git clone github.com/moonbase/project.git")
    commits = len(kit.git(lab.github, "log", "--oneline", "main").splitlines())
    assert len(kit.git(lab.project, "log", "--oneline").splitlines()) == commits
    step = next(step for step in level.QUEST if isinstance(step, kit.AnswerStep))
    assert step.check(lab, state, f" {commits} ").message == level.RIGHT_COUNT
    assert step.check(lab, state, str(commits + 1)).message == level.WRONG_COUNT
    assert step.check(lab, state, "five").message == level.NOT_A_NUMBER


def test_a_git_log_typed_before_going_into_the_clone_fails_and_the_step_waits() -> None:
    lab, state = started(level)
    typed = [kit.type_line(lab.root, "git clone github.com/moonbase/project.git"), kit.type_line(lab.root, "git log --oneline")]
    assert typed[1]["status"] == 128
    assert watch(level, "log").watch(lab, state, typed).message == level.NOT_READ
    rule = reaction(level, typed[1], set(), True, False)
    assert rule is not None and rule.text == level.OUTSIDE_THE_CLONE


def test_a_git_command_before_the_clone_gets_told_to_clone_not_to_init() -> None:
    lab, state = started(level)
    line = kit.type_line(lab.root, "git log")
    assert line["status"] == 128
    rule = reaction(level, line, set(), False, False)
    assert rule is not None and rule.text == level.NOT_CLONED_YET


def test_a_clone_in_another_folder_is_not_the_one_the_mission_asks_for() -> None:
    lab, state = started(level)
    kit.type_line(lab.root, "git clone github.com/moonbase/project.git outpost")
    assert watch(level, "clone").watch(lab, state, []).message == level.NOT_CLONED


def test_a_project_folder_that_is_not_a_clone_of_the_outpost_is_named() -> None:
    lab, state = started(level)
    kit.type_line(lab.root, "git init -q project")
    assert watch(level, "clone").watch(lab, state, []).message == level.NOT_A_CLONE
