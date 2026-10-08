from firstcommit import kit
from firstcommit.levels import names_experiments as level
from level_helpers import started, typed_in, watch

PROBE = f'echo "{level.PROBE_LINE}" > {level.PROBE} && git add {level.PROBE} && git commit -m "Launch the probe"'


def test_a_branch_copies_no_file_and_points_at_the_commit_main_is_on() -> None:
    lab, state = started(level)
    before = sorted(path.name for path in lab.project.iterdir())
    typed_in(lab, "git branch scout")
    assert sorted(path.name for path in lab.project.iterdir()) == before
    assert kit.git(lab.project, "rev-parse", "scout") == kit.git(lab.project, "rev-parse", "main")
    assert watch(level, "branch").watch(lab, state, []).message == level.MADE


def test_switch_c_makes_the_branch_and_moves_onto_it_at_once() -> None:
    lab, state = started(level)
    typed_in(lab, "git switch -c scout")
    assert watch(level, "switch").watch(lab, state, []).message == level.ON


def test_the_probe_leaves_the_folder_on_main_and_comes_back_on_scout() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch -c scout", PROBE, "git switch main", "ls")
    assert not (lab.project / level.PROBE).exists()
    assert level.check(lab, state, None, typed).solved
    typed_in(lab, "git switch scout")
    assert (lab.project / level.PROBE).read_text() == f"{level.PROBE_LINE}\n"


def test_the_probe_committed_on_main_is_named_and_the_level_offers_to_start_again() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch scout", PROBE)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.PROBE_ON_MAIN)


def test_an_ls_typed_before_going_back_to_main_does_not_count() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git switch -c scout", PROBE, "ls", "git switch main")
    assert level.check(lab, state, None, typed).message == level.NOT_LOOKED
