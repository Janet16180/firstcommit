from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from firstcommit import kit

FULL = "ce013625030ba8dba906f756967f9e9ca394464a"


def test_a_lab_keeps_the_project_and_the_stand_in_github_under_its_root(tmp_path: Path) -> None:
    lab = kit.Lab(tmp_path)
    assert lab.project == tmp_path / "project"
    assert lab.github == tmp_path / "github" / "project.git"


def test_parse_int_reads_plain_digits() -> None:
    assert kit.parse_int(" 42 ") == 42


def test_parse_int_refuses_what_is_not_a_small_ascii_number() -> None:
    for text in [None, "", "-1", "²", "٣", "1.0", "0x10", "9" * 11, "word " + "9" * 5000]:
        assert kit.parse_int(text) is None


@given(st.text())
def test_parse_int_never_raises(text: str) -> None:
    kit.parse_int(text)


def test_a_hash_can_be_typed_whole_or_abbreviated_in_any_case() -> None:
    assert kit.is_hash_of(FULL, FULL)
    assert kit.is_hash_of(" CE01362 ", FULL)
    assert kit.is_hash_of("ce01", FULL)


def test_a_hash_answer_must_be_a_long_enough_hex_prefix() -> None:
    for text in [None, "", "ce0", "e013625", "ce01362g", "ce 01362", FULL + "0"]:
        assert not kit.is_hash_of(text, FULL)


@given(st.text())
def test_is_hash_of_never_raises(text: str) -> None:
    kit.is_hash_of(text, FULL)


def test_a_digest_matches_only_its_own_answer() -> None:
    stored = kit.digest("main")
    assert kit.answer_is(" main ", stored)
    assert not kit.answer_is("master", stored)
    assert not kit.answer_is(None, stored)
