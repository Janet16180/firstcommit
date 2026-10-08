"""The field guide shows what real git prints: its guide-git.js is what tests/guide_capture.py makes today."""

import pytest

import guide_capture


@pytest.mark.slow
def test_the_guide_shows_what_git_prints_today() -> None:
    assert guide_capture.TARGET.read_text() == guide_capture.generate(), "run: uv run python tests/guide_capture.py"
