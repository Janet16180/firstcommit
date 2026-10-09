from firstcommit import kit
from firstcommit.levels import conflict_collision as level
from level_helpers import reaction, started, typed_in, watch

MERGE = "git merge --no-edit scout"


def test_the_merge_stops_with_both_sides_between_markers() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE)
    assert typed[0]["status"] == 1
    text = (lab.project / level.DOCKING).read_text()
    assert level.OURS in text and level.THEIRS in text and level.MARKER in text
    assert watch(level, "merge").watch(lab, state, typed).message == level.CONFLICT


def test_a_commit_while_the_file_is_in_conflict_fails_and_rama_says_to_answer_first() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "git commit --no-edit")
    assert typed[1]["status"] == 128
    rule = reaction(level, typed[1], set(), True, False)
    assert rule is not None and rule.text == level.ANSWER_FIRST


def test_restore_theirs_keeps_bay_4_but_the_conflict_stays_until_add() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "cat docking.txt", "git restore --theirs docking.txt")
    assert (lab.project / level.DOCKING).read_text() == level.THEIRS
    assert kit.conflicted(kit.snapshot(lab.project)) == [level.DOCKING]
    assert watch(level, "add").watch(lab, state, typed).message == level.NOT_ADDED
    rule = reaction(level, typed[2], {"file-changed"}, True, False)
    assert rule is not None and rule.text == level.SIDE


def test_keeping_bay_3_is_named() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "cat docking.txt", "git restore --ours docking.txt")
    assert watch(level, "choose").watch(lab, state, typed).message == level.BAY_3


def test_writing_bay_4_by_hand_works_as_well() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "cat docking.txt", 'echo "Dock at bay 4" > docking.txt', "git add docking.txt", "git commit --no-edit")
    assert level.check(lab, state, None, typed).solved


def test_markers_committed_are_named_and_a_new_commit_fixes_them() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "cat docking.txt", "git add docking.txt", "git commit --no-edit")
    assert typed[-1]["status"] == 0
    assert level.check(lab, state, None, typed).message == level.NOT_BAY_4_COMMITTED
    typed += typed_in(lab, "git restore --source=scout docking.txt", "git add docking.txt", 'git commit -m "Dock at bay 4"')
    assert level.check(lab, state, None, typed).solved


def test_bay_3_committed_is_named() -> None:
    lab, state = started(level)
    typed = typed_in(lab, MERGE, "cat docking.txt", "git restore --ours docking.txt", "git add docking.txt", "git commit --no-edit")
    assert level.check(lab, state, None, typed).message == level.BAY_3_COMMITTED


def test_the_two_sides_are_yours_and_alexs_named_by_person() -> None:
    lab, _ = started(level)
    typed_in(lab, MERGE)
    [conflict] = kit.conflicts(lab.project)
    assert (conflict["you"]["author"], conflict["them"]["author"], conflict["them"]["label"]) == (kit.PLAYER.name, "Alex", "scout")
    assert "Alex" in level.BRIEFING and "*ours*" in level.DEBRIEF and "*theirs*" in level.DEBRIEF
