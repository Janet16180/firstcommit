from firstcommit import game, kit, runner
from firstcommit.levels import conflict_mergetool as level
from level_helpers import command_shape, reaction, started, typed_in, watch

MERGE = "git merge --no-edit scout"


def merged_with_panel(picks: tuple[kit.Keep, ...]) -> tuple[kit.Lab, kit.State, list[kit.Command]]:
    """Start the level, merge, and answer the conflicts in the merge panel with `picks`."""
    lab, state = started(level)
    typed = typed_in(lab, MERGE)
    typed.append(kit.type_line(lab.project, "git mergetool", {level.LAUNCH: picks}))
    return lab, state, typed


def test_the_merge_stops_with_two_conflicts_that_need_different_answers() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE)
    assert typed[0]["status"] == 1
    assert (lab.project / level.LAUNCH).read_text().count(level.MARKER) == 2
    assert watch(level, "merge").watch(lab, state, typed).message == level.CONFLICT
    assert watch(level, "answer").watch(lab, state, typed).message == level.NOT_ANSWERED


def test_the_panels_picks_answer_the_file_and_git_mergetool_adds_it_with_no_backup_left() -> None:
    lab, state, typed = merged_with_panel(level.PICKS[level.LAUNCH])
    assert typed[-1]["status"] == 0
    assert watch(level, "answer").watch(lab, state, typed).message == level.ANSWERED
    assert sorted(entry.name for entry in lab.project.iterdir()) == [".git", level.LAUNCH]
    assert watch(level, "status").watch(lab, state, typed).message == level.NOT_LOOKED
    typed += typed_in(lab, "git status")
    assert watch(level, "status").watch(lab, state, typed).message == level.LOOKED
    typed += typed_in(lab, "git commit --no-edit")
    assert level.check(lab, state, None, typed).message == level.DONE


def test_keeping_your_time_is_named_with_the_way_to_answer_again() -> None:
    lab, state, typed = merged_with_panel(("yours", "both"))
    assert watch(level, "answer").watch(lab, state, typed).message == level.LATE
    typed += typed_in(lab, "git merge --abort", MERGE)
    typed.append(kit.type_line(lab.project, "git mergetool", level.PICKS))
    assert watch(level, "answer").watch(lab, state, typed).message == level.ANSWERED


def test_keeping_one_cargo_line_is_named() -> None:
    lab, state, typed = merged_with_panel(("theirs", "theirs"))
    assert watch(level, "answer").watch(lab, state, typed).message == level.ONE_CARGO


def test_the_cargo_lines_may_come_in_either_order_and_an_answer_written_by_hand_passes_too() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE)
    (lab.project / level.LAUNCH).write_text(level.PLAN.format(window="05:30") + "- spare antenna\n- oxygen\n")
    typed += typed_in(lab, "git add launch.txt", "git status", "git commit --no-edit")
    assert level.check(lab, state, None, typed).solved


def test_seven_three_s_way_keeps_one_side_of_the_whole_file_and_rama_says_why_it_cannot_answer_here() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "git restore --theirs launch.txt")
    assert "- oxygen" not in (lab.project / level.LAUNCH).read_text()
    rule = reaction(level, typed[1], {"file-changed"}, True, False)
    assert rule is not None and rule.text == level.ONE_SIDE
    typed.append(kit.type_line(lab.project, "git mergetool", level.PICKS))
    assert watch(level, "answer").watch(lab, state, typed).message == level.ONE_CARGO


def test_a_commit_while_the_file_is_in_conflict_fails_and_rama_says_to_answer_first() -> None:
    lab, _ = started(level)
    typed = typed_in(lab, MERGE, "git commit --no-edit")
    assert typed[1]["status"] == 128
    rule = reaction(level, typed[1], set(), True, False)
    assert rule is not None and rule.text == level.ANSWER_FIRST


def test_markers_added_by_hand_are_named_and_git_mergetool_then_has_nothing_to_answer() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "git add launch.txt")
    assert watch(level, "answer").watch(lab, state, typed).message == level.MARKERS
    assert typed_in(lab, "git mergetool") == [{"line": "git mergetool", "status": 0}]


def test_a_wrong_answer_committed_is_named() -> None:
    lab, state, typed = merged_with_panel(("yours", "yours"))
    typed += typed_in(lab, "git status", "git commit --no-edit")
    assert level.check(lab, state, None, typed).message == level.WRONG_COMMITTED


def test_only_git_mergetool_is_new_the_other_lines_were_taught_before_in_the_map_order() -> None:
    catalogue = runner.catalogue()
    order = list(catalogue)
    before = order[: order.index("conflict-mergetool")]
    taught = {shape for level_id in before for shape in map(command_shape, game.SHOWN_LINE.findall(catalogue[level_id].texts["en"].hints[-1])) if shape}
    shown = {shape for shape in map(command_shape, game.SHOWN_LINE.findall(level.HINTS[-1])) if shape}
    assert shown - taught == {"mergetool"}


def test_it_comes_after_collision_and_docking_collision_becomes_the_fifth_mission() -> None:
    sector = [level_id for level_id in runner.catalogue() if level_id.startswith("conflict-")]
    assert sector == ["conflict-meet", "conflict-abort", "conflict-collision", "conflict-mergetool", "conflict-docking"]
