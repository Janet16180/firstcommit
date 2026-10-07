from pathlib import Path

from firstcommit import game, kit, markup, reactions, runner, save
from firstcommit.levels import liftoff_aboard as level


def started() -> tuple[kit.Lab, kit.State]:
    """
    Start the level's lab, as the game does.

    Returns
    -------
    tuple[kit.Lab, kit.State]
        The lab and the level's state.
    """
    entry = runner.load(level)
    state = runner.start_lab(entry)
    return runner.lab_of(entry.id), state


def typed_in(lab: kit.Lab, *lines: str) -> list[kit.Command]:
    """
    Type lines in the lab's project folder, as the player would.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    *lines : str
        The lines, in order.

    Returns
    -------
    list[kit.Command]
        Each line with its real exit status.
    """
    return [kit.type_line(lab.project, line) for line in lines]


def test_the_folder_holds_the_two_files_and_no_repository() -> None:
    lab, _ = started()
    assert sorted(path.name for path in lab.project.iterdir()) == ["journal.txt", "map.txt"]
    assert kit.snapshot(lab.project)["exists"] is False


def test_git_status_fails_in_the_folder_because_it_is_not_a_repository() -> None:
    lab, _ = started()
    assert typed_in(lab, "git status") == [{"line": "git status", "status": 128}]


def test_the_level_is_solved_by_ls_then_the_failed_git_status() -> None:
    lab, state = started()
    typed = typed_in(lab, "ls", "git status")
    assert level.check(lab, state, None, typed).solved
    assert kit.snapshot(lab.project)["exists"] is False


def test_git_status_typed_before_ls_still_counts_once_ls_is_typed() -> None:
    lab, state = started()
    typed = typed_in(lab, "git status")
    first, second = level.QUEST
    assert isinstance(first, kit.WatchStep) and isinstance(second, kit.WatchStep)
    assert not first.watch(lab, state, typed).solved
    assert not level.check(lab, state, None, typed).solved
    typed += typed_in(lab, "ls")
    assert first.watch(lab, state, typed).solved and level.check(lab, state, None, typed).solved


def test_an_ls_that_failed_does_not_count() -> None:
    lab, state = started()
    typed = typed_in(lab, "ls nothing-here", "git status")
    assert typed[0]["status"] != 0
    assert not level.check(lab, state, None, typed).solved


def test_the_failed_git_status_gets_the_levels_own_lesson_and_not_the_shared_one() -> None:
    rules = (*runner.load(level).reactions, *reactions.RULES)
    rule = reactions.react({"line": "git status", "status": 128}, (), False, rules)
    assert rule is not None and rule.text == level.NO_REPOSITORY_YET
    assert reactions.react({"line": "git status", "status": 0}, (), True, rules) is not None


def test_the_step_messages_tell_what_git_status_said() -> None:
    lab, state = started()
    second = level.QUEST[1]
    assert isinstance(second, kit.WatchStep)
    assert second.watch(lab, state, typed_in(lab, "ls", "git status")).message == level.REFUSED
    kit.git(lab.project, "init", "-q")
    assert second.watch(lab, state, typed_in(lab, "git status")).message == level.ANSWERED


def test_the_level_plays_through_the_game_from_the_typed_log_to_three_stars(game_home: Path) -> None:
    entry = runner.load(level)
    game.start(entry.id)
    game.observe()
    lab = runner.lab_of(entry.id)
    log = game_home / save.COMMANDS_FILE
    for number, command in enumerate(typed_in(lab, "ls", "git status"), start=1):
        with log.open("ab") as handle:
            handle.write(f"{number}\t{command['status']}\t{command['line']}\0".encode())
        assert game.quest_step(None)["correct"] is True
    observed = game.observe()
    assert [reaction["text"] for reaction in observed["reactions"]] == [markup.parse(reactions.LS_NO_REPOSITORY), markup.parse(level.NO_REPOSITORY_YET)]
    result = game.check(None, auto=True)
    assert (result["solved"], result["stars"], result["new_card"] is not None) == (True, 3, True)


def test_a_git_status_typed_before_ls_is_told_as_the_goal_already_met_when_its_turn_comes() -> None:
    lab, state = started()
    typed = typed_in(lab, "git status", "ls")
    first, second = level.QUEST
    assert isinstance(first, kit.WatchStep) and isinstance(second, kit.WatchStep)
    assert first.watch(lab, state, typed).solved
    verdict = second.watch(lab, state, typed)
    assert verdict.solved and verdict.message.startswith("You asked Git earlier")
    assert second.watch(lab, state, typed_in(lab, "ls", "git status")).message.startswith("You asked Git:")
