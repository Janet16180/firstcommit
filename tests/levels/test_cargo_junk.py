from firstcommit import kit, reactions
from firstcommit.levels import cargo_junk as level
from level_helpers import arrived, reaction, started, typed_in, watch

IGNORE = 'echo "sim-output/" > .gitignore'


def test_the_simulator_floods_the_working_folder_once_the_page_has_looked() -> None:
    lab, _ = started(level)
    snap = kit.snapshot(lab.project)
    assert (len(snap["commits"]), kit.unstaged(snap), kit.untracked(snap)) == (1, ["nav.cfg"], [])
    lab, _ = arrived(level)
    junk = [path for path in kit.untracked(kit.snapshot(lab.project)) if path.startswith("sim-output/")]
    assert len(junk) == level.RUNS


def test_looking_ignoring_the_output_and_staging_the_rule_and_the_change_solves_the_level() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", IGNORE, "git add .gitignore nav.cfg")
    assert level.check(lab, state, None, typed) == kit.Verdict(True, level.STAGED)
    snap = kit.snapshot(lab.project)
    assert kit.staged(snap) == [".gitignore", "nav.cfg"]
    assert all(file["ignored"] for file in snap["files"] if file["path"].startswith("sim-output/"))
    assert (lab.project / "sim-output" / "run-001.log").exists()


def test_once_the_output_is_ignored_git_add_dot_stages_only_the_rule_and_the_change() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "echo sim-output > .gitignore", "git add .")
    assert level.check(lab, state, None, typed).solved
    assert kit.staged(kit.snapshot(lab.project)) == [".gitignore", "nav.cfg"]


def test_the_level_waits_for_a_look_with_git_status() -> None:
    lab, state = arrived(level)
    verdict = level.check(lab, state, None, typed_in(lab, IGNORE, "git add .gitignore nav.cfg"))
    assert (verdict.solved, verdict.message) == (False, level.NOT_LOOKED)


def test_until_gitignore_names_the_output_the_ignore_goal_says_how() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status")
    assert watch(level, "ignore").watch(lab, state, typed).message == level.NOT_IGNORED
    typed += typed_in(lab, "mkdir -p .git/info && echo sim-output/ >> .git/info/exclude")
    assert watch(level, "ignore").watch(lab, state, typed).message == level.NOT_IGNORED


def test_deleting_the_output_does_not_ignore_it_and_rama_says_the_simulator_makes_it_again() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "rm -r sim-output")
    rule = reaction(level, typed[0], {"file-deleted"}, True, False)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.REGENERATED)
    assert watch(level, "ignore").watch(lab, state, typed).message == level.NOT_IGNORED


def test_git_status_before_the_output_is_ignored_warns_with_the_junk_flood() -> None:
    lab, _ = arrived(level)
    typed = typed_in(lab, "git status")
    rule = reaction(level, typed[0], set(), True, False, ignored=False)
    assert rule is not None and (rule.mood, rule.text, rule.moment) == ("warn", level.WHY_IGNORE, "junk-flood")
    rule = reaction(level, typed[0], set(), True, False, ignored=True)
    assert rule is not None and rule.text == reactions.STATUS


def test_writing_the_rule_raises_the_ignore_field() -> None:
    lab, _ = arrived(level)
    typed = typed_in(lab, IGNORE)
    rule = reaction(level, typed[0], {"file-created", "file-ignored"}, True, False, ignored=True)
    assert rule is not None and (rule.mood, rule.text) == ("ok", level.IGNORE_FIELD)


def test_git_add_dot_before_the_rule_stages_the_output_and_unstaging_it_recovers() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git add .")
    rule = reaction(level, typed[1], {"file-staged"}, True, True, ignored=False)
    assert rule is not None and (rule.mood, rule.text) == ("warn", level.JUNK_STAGED)
    typed += typed_in(lab, IGNORE)
    verdict = watch(level, "stage").watch(lab, state, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, False, level.JUNK_ABOARD)
    typed += typed_in(lab, "git restore --staged sim-output", "git add .gitignore")
    assert level.check(lab, state, None, typed).solved


def test_the_rule_written_but_not_staged_is_named() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", IGNORE, "git add nav.cfg")
    verdict = watch(level, "stage").watch(lab, state, typed)
    assert (verdict.solved, verdict.message) == (False, level.NOT_STAGED)


def test_the_output_in_a_commit_is_said_and_the_level_offers_to_start_again() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", "git add .", 'git commit -q -m "Everything"')
    verdict = level.check(lab, state, None, typed)
    assert (verdict.solved, verdict.lost, verdict.message) == (False, True, level.JUNK_COMMITTED)


def test_committing_the_rule_and_the_change_still_solves_the_level() -> None:
    lab, state = arrived(level)
    typed = typed_in(lab, "git status", IGNORE, "git add .", 'git commit -q -m "Ignore the simulator"')
    assert level.check(lab, state, None, typed).solved
