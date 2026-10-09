from firstcommit import kit
from firstcommit.levels import names_experiments as level
from level_helpers import reaction, started, typed_in, watch

COMMIT = 'git add engine.txt && git commit -m "Try a quiet engine"'


def test_bright_lights_was_made_yesterday_and_engine_txt_waits_untracked_on_main() -> None:
    lab, state = started(level)
    assert kit.snapshot(lab.project)["branch"] == "main"
    assert kit.git(lab.project, "log", "-1", "--format=%s", "bright-lights").strip() == "Try bright lights"
    assert kit.git(lab.project, "status", "--porcelain").strip() == "?? engine.txt"


def test_a_second_name_and_a_switch_leave_the_folder_as_it_was() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch quiet-engine", "git switch quiet-engine")
    assert watch(level, "switch").watch(lab, state, typed).message == level.ON_QUIET
    assert (lab.project / "engine.txt").exists() and not (lab.project / "lights.txt").exists()


def test_the_commit_forks_the_chain_and_main_stays() -> None:
    lab, state = started(level)
    typed_in(lab, "git branch quiet-engine", "git switch quiet-engine", COMMIT)
    parents = {kit.git(lab.project, "rev-parse", f"{branch}~1").strip() for branch in ("quiet-engine", "bright-lights")}
    assert parents == {state["main"]} and kit.git(lab.project, "rev-parse", "main").strip() == state["main"]


def test_switching_to_bright_lights_swaps_the_two_files_and_the_tree_ends_the_mission() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch quiet-engine", "git switch quiet-engine", COMMIT, "git switch bright-lights")
    assert (lab.project / "lights.txt").exists() and not (lab.project / "engine.txt").exists()
    assert level.check(lab, state, None, typed).message == level.NOT_DRAWN
    typed += typed_in(lab, "git log --oneline --graph --all")
    assert level.check(lab, state, None, typed).solved


def test_a_commit_while_still_on_main_is_lost() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git branch quiet-engine", COMMIT)
    verdict = level.check(lab, state, None, typed)
    assert (verdict.lost, verdict.message) == (True, level.MAIN_MOVED)


def test_the_older_forms_play_the_level_too_and_rama_names_checkout_as_one() -> None:
    lab, state = started(level)
    typed = typed_in(lab, "git checkout -b quiet-engine", COMMIT, "git checkout bright-lights", "git log --oneline --graph --all")
    assert level.check(lab, state, None, typed).solved
    rule = reaction(level, typed[2], {"branch-switched"}, True, False)
    assert rule is not None and rule.text == level.OLDER_FORM_WORKS
