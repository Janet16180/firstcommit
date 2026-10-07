from firstcommit import kit, reactions, runner
from firstcommit.levels import cargo_first as level


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


def stage_step() -> kit.WatchStep:
    """
    Give the level's first goal.

    Returns
    -------
    kit.WatchStep
        The goal that watches the staging area.
    """
    step = level.QUEST[0]
    assert isinstance(step, kit.WatchStep)
    return step


def rules() -> tuple[kit.ReactionRule, ...]:
    """
    Give the reaction rules the game tries for this level.

    Returns
    -------
    tuple[kit.ReactionRule, ...]
        The level's own, then the shared ones.
    """
    return (*runner.load(level).reactions, *reactions.RULES)


def test_the_level_starts_in_a_new_repository_with_two_untracked_files() -> None:
    lab, _ = started()
    snap = kit.snapshot(lab.project)
    assert (snap["exists"], snap["branch"], snap["commits"]) == (True, "main", [])
    assert kit.untracked(snap) == ["journal.txt", "map.txt"]


def test_the_level_is_solved_by_staging_the_map_then_git_status() -> None:
    lab, state = started()
    typed = typed_in(lab, "git add map.txt", "git status")
    assert level.check(lab, state, None, typed).solved
    assert kit.staged(kit.snapshot(lab.project)) == ["map.txt"]


def test_git_status_before_staging_does_not_count() -> None:
    lab, state = started()
    typed = typed_in(lab, "git status", "git add map.txt")
    assert stage_step().watch(lab, state, typed).solved
    assert not level.check(lab, state, None, typed).solved
    assert level.check(lab, state, None, typed + typed_in(lab, "git status")).solved


def test_a_misspelled_name_stages_nothing_and_gets_the_shared_nudge() -> None:
    lab, state = started()
    typed = typed_in(lab, "git add mapa.txt")
    assert typed[0]["status"] == 128
    verdict = stage_step().watch(lab, state, typed)
    assert not verdict.solved and "git add map.txt" in verdict.message
    rule = reactions.react(typed[0], (), True, rules())
    assert rule is not None and rule.text == reactions.NOT_STAGED


def test_staging_everything_stages_the_journal_too_and_the_way_back_before_a_commit_is_rm_cached() -> None:
    lab, state = started()
    typed = typed_in(lab, "git add .")
    assert kit.staged(kit.snapshot(lab.project)) == ["journal.txt", "map.txt"]
    verdict = stage_step().watch(lab, state, typed)
    assert not verdict.solved and "git rm --cached journal.txt" in verdict.message
    rule = reactions.react(typed[0], {"file-staged"}, True, rules())
    assert rule is not None and rule.mood == "warn" and rule.text == level.EVERYTHING_STAGED
    typed += typed_in(lab, "git rm --cached journal.txt", "git status")
    assert kit.untracked(kit.snapshot(lab.project)) == ["journal.txt"]
    assert level.check(lab, state, None, typed).solved


def test_staging_one_file_gets_the_shared_reaction_not_the_warning() -> None:
    rule = reactions.react({"line": "git add map.txt", "status": 0}, {"file-staged"}, True, rules())
    assert rule is not None and rule.text == reactions.STAGED


def test_a_deleted_repository_is_told_and_never_solved() -> None:
    lab, state = started()
    typed = typed_in(lab, "rm -rf .git", "git add map.txt", "git status")
    verdict = stage_step().watch(lab, state, typed)
    assert not verdict.solved and verdict.message == level.NO_REPOSITORY
    assert not level.check(lab, state, None, typed).solved


def test_restore_staged_fails_before_the_first_commit_and_the_level_says_what_works_instead() -> None:
    lab, state = started()
    typed = typed_in(lab, "git add .", "git restore --staged journal.txt")
    assert typed[1]["status"] == 128
    assert kit.staged(kit.snapshot(lab.project)) == ["journal.txt", "map.txt"]
    rule = reactions.react(typed[1], (), True, rules())
    assert rule is not None and rule.text == level.NOTHING_TO_RESTORE
