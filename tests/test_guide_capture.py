"""The field guide shows what real git prints: its guide-git.js is what tests/guide_capture.py makes today."""

from pathlib import Path

import pytest

import guide_capture


@pytest.mark.slow
def test_the_guide_shows_what_git_prints_today() -> None:
    assert guide_capture.TARGET.read_text() == guide_capture.generate(), "run: uv run python tests/guide_capture.py"


def test_a_terminal_line_ends_in_a_newline_as_it_reads_on_screen() -> None:
    assert guide_capture.shown("Switched to branch 'scout'\r\n") == "Switched to branch 'scout'\n"


def test_a_line_git_overwrites_is_kept_as_the_terminal_leaves_it() -> None:
    raw = "hint: Waiting for your editor to close the file... \r\x1b[KMerge made by the 'ort' strategy.\r\n"
    assert guide_capture.shown(raw) == "Merge made by the 'ort' strategy.\n"


def test_a_carriage_return_writes_over_the_start_of_the_line_only() -> None:
    assert guide_capture.shown("12345\rab\r\n") == "ab345\n"


def test_any_other_escape_sequence_is_an_error() -> None:
    with pytest.raises(ValueError, match="escape"):
        guide_capture.shown("\x1b[31mred\x1b[m\r\n")


def test_a_terminal_step_runs_on_a_terminal_and_keeps_what_it_printed(tmp_path: Path) -> None:
    story = guide_capture.Story(work=tmp_path, here=tmp_path)
    story.step("tty", "test -t 1 && echo on a terminal", terminal=True)
    story.step("pipe", "test -t 1 || echo not on a terminal")
    assert story.runs == {
        "tty": [{"command": "test -t 1 && echo on a terminal", "output": "on a terminal\n"}],
        "pipe": [{"command": "test -t 1 || echo not on a terminal", "output": "not on a terminal\n"}],
    }
