import hashlib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from firstcommit import freeplay, gitcmd, markers, records

CONFLICTED = (
    b"LAUNCH CHECKLIST\n"
    b"<<<<<<< HEAD\n"
    b"4. Course: the Moon\n"
    b"=======\n"
    b"4. Course: Jupiter\n"
    b">>>>>>> 94b6459d1e2f\n"
    b"5. Music: off\n"
    b"<<<<<<< HEAD\n"
    b"6. Shields: on\n"
    b"||||||| 0a8298c\n"
    b"6. Shields: off\n"
    b"=======\n"
    b">>>>>>> origin/main\n"
)


def test_a_file_reads_as_its_clean_lines_and_each_conflict_block_with_both_sides_and_their_labels() -> None:
    assert markers.parts(CONFLICTED) == [
        {"kind": "clean", "lines": ["LAUNCH CHECKLIST"]},
        {"kind": "block", "yours": ["4. Course: the Moon"], "theirs": ["4. Course: Jupiter"], "yours_label": "HEAD", "theirs_label": "94b6459d1e2f"},
        {"kind": "clean", "lines": ["5. Music: off"]},
        {"kind": "block", "yours": ["6. Shields: on"], "theirs": [], "yours_label": "HEAD", "theirs_label": "origin/main"},
    ]


def test_a_marked_file_names_its_path_and_the_hash_of_the_bytes_it_was_read_from() -> None:
    marked = markers.marked("checklist.txt", CONFLICTED)
    assert marked == {"path": "checklist.txt", "read": hashlib.sha256(CONFLICTED).hexdigest(), "parts": markers.parts(CONFLICTED)}


@pytest.mark.parametrize(
    ("choices", "written"),
    [
        (["yours", "yours"], b"LAUNCH CHECKLIST\n4. Course: the Moon\n5. Music: off\n6. Shields: on\n"),
        (["theirs", "theirs"], b"LAUNCH CHECKLIST\n4. Course: Jupiter\n5. Music: off\n"),
        (["both", "theirs"], b"LAUNCH CHECKLIST\n4. Course: the Moon\n4. Course: Jupiter\n5. Music: off\n"),
    ],
)
def test_resolving_writes_each_blocks_chosen_sides_yours_first_and_keeps_every_other_byte(choices: list[records.Keep], written: bytes) -> None:
    assert markers.resolve(CONFLICTED, choices) == written


def test_resolving_needs_one_choice_per_block() -> None:
    wrong: list[list[records.Keep]] = [[], ["yours"], ["yours", "yours", "yours"]]
    for choices in wrong:
        with pytest.raises(ValueError, match="2 conflict blocks"):
            markers.resolve(CONFLICTED, choices)


def test_line_endings_and_bytes_that_are_not_utf8_stay_as_they_were_and_read_as_replacements() -> None:
    data = b"caf\xe9\r\n<<<<<<< HEAD\r\nmine\r\n=======\r\ntheirs\r\n>>>>>>> side\r\nend"
    assert markers.resolve(data, ["theirs"]) == b"caf\xe9\r\ntheirs\r\nend"
    assert markers.parts(data)[0] == {"kind": "clean", "lines": ["caf�"]}


@pytest.mark.parametrize(
    "text",
    [
        b"<<<<<<< HEAD\nmine\n=======\ntheirs\n",
        b"<<<<<<< HEAD\nmine\n>>>>>>> side\n",
        b"<<<<<<<< HEAD\nmine\n=======\ntheirs\n>>>>>>> side\n",
        b"======= \n>>>>>>> side\n",
    ],
)
def test_lines_that_only_look_like_markers_are_plain_lines(text: bytes) -> None:
    assert markers.parts(text) == [{"kind": "clean", "lines": text.decode().splitlines()}]
    assert markers.resolve(text, []) == text


def test_a_start_marker_inside_an_open_block_starts_the_block_again() -> None:
    text = b"<<<<<<< old\nstray\n<<<<<<< HEAD\nmine\n=======\ntheirs\n>>>>>>> side\n"
    assert markers.resolve(text, ["yours"]) == b"<<<<<<< old\nstray\nmine\n"


@given(st.lists(st.sampled_from([b"line\n", b"<<<<<<< HEAD\n", b"=======\n", b">>>>>>> x\n", b"||||||| base\n", b"other"]), max_size=12))
def test_resolving_keeps_every_side_line_and_clean_line_and_drops_only_markers(lines: list[bytes]) -> None:
    data = b"".join(lines)
    blocks = [part for part in markers.parts(data) if part["kind"] == "block"]
    both = markers.resolve(data, ["both"] * len(blocks))
    clean_lines = sum(len(part["lines"]) for part in markers.parts(data) if part["kind"] == "clean")
    side_lines = sum(len(part["yours"]) + len(part["theirs"]) for part in blocks)
    assert len(both.splitlines()) == clean_lines + side_lines


def test_the_conflict_start_reads_as_git_wrote_it_and_resolves_to_a_file_git_accepts(game_home: Path) -> None:
    lab = freeplay.build("conflict")
    path = lab.project / freeplay.CHECKLIST
    data = path.read_bytes()
    blocks = [part for part in markers.parts(data) if part["kind"] == "block"]
    assert [(block["yours"], block["theirs"]) for block in blocks] == [(["4. Course: the Moon"], ["4. Course: Jupiter"])]
    path.write_bytes(markers.resolve(data, ["yours"]))
    gitcmd.output(lab.project, "add", freeplay.CHECKLIST)
    assert gitcmd.run(lab.project, "diff", "--cached", "--check").returncode == 0
    assert "4. Course: the Moon\n" in path.read_text()
