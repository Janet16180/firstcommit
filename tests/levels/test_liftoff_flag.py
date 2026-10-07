from firstcommit import kit, reactions, runner
from firstcommit.levels import liftoff_flag as level


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


def watches() -> list[kit.WatchStep]:
    """
    Give the level's goals, which are all watch steps.

    Returns
    -------
    list[kit.WatchStep]
        The goals, in order.
    """
    steps = [step for step in level.QUEST if isinstance(step, kit.WatchStep)]
    assert len(steps) == len(level.QUEST)
    return steps


def test_the_level_is_solved_by_init_then_ls_a_then_git_status() -> None:
    lab, state = started()
    typed = typed_in(lab, "git init", "ls -a", "git status")
    assert [line["status"] for line in typed] == [0, 0, 0]
    assert level.check(lab, state, None, typed).solved
    assert kit.snapshot(lab.project)["branch"] == "main"


def test_git_status_before_init_fails_and_does_not_count() -> None:
    lab, state = started()
    typed = typed_in(lab, "git status", "git init", "ls -a")
    assert typed[0]["status"] == 128
    assert not watches()[2].watch(lab, state, typed).solved
    assert reactions.react(typed[0], (), False, reactions.RULES) is not None
    typed += typed_in(lab, "git status")
    assert level.check(lab, state, None, typed).solved


def test_ls_a_before_init_shows_no_git_folder_so_it_does_not_count() -> None:
    lab, state = started()
    typed = typed_in(lab, "ls -a", "git init", "git status")
    assert watches()[0].watch(lab, state, typed).solved
    assert not watches()[1].watch(lab, state, typed).solved
    assert not level.check(lab, state, None, typed).solved


def test_a_plain_ls_does_not_show_the_hidden_folder() -> None:
    lab, state = started()
    typed = typed_in(lab, "git init", "ls")
    assert not watches()[1].watch(lab, state, typed).solved
    assert watches()[1].watch(lab, state, typed + typed_in(lab, "ls -la")).solved


def test_a_misspelled_init_makes_no_repository() -> None:
    lab, state = started()
    typed = typed_in(lab, "git int")
    assert typed[0]["status"] != 0
    assert not watches()[0].watch(lab, state, typed).solved


def test_init_twice_is_harmless_and_still_solves_the_level() -> None:
    lab, state = started()
    typed = typed_in(lab, "git init", "git init", "ls -a", "git status")
    assert typed[1]["status"] == 0
    assert level.check(lab, state, None, typed).solved
