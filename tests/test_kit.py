import typing

import pytest
from hypothesis import given
from hypothesis import strategies as st

from firstcommit import kit, lab, markup, playground, repomap

FULL = "ce013625030ba8dba906f756967f9e9ca394464a"


def test_a_level_gets_its_lab_from_the_toolkit() -> None:
    assert kit.Lab is lab.Lab


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


def test_levels_can_name_every_part_of_a_snapshot() -> None:
    assert {"Snapshot", "FileEntry", "Commit", "Ref"} <= set(kit.__all__)


def test_an_answer_step_cannot_be_built_without_its_question_and_check() -> None:
    with pytest.raises(TypeError):
        kit.AnswerStep(id="a", text="t", question="Which branch?")  # type: ignore[call-arg]


def test_a_watch_step_cannot_be_built_without_its_watch() -> None:
    with pytest.raises(TypeError):
        kit.WatchStep(id="w", text="t")  # type: ignore[call-arg]


def test_every_step_kind_is_a_step_and_nothing_else_is() -> None:
    def never(lab: kit.Lab, state: kit.State, answer_or_typed: object = "") -> kit.Verdict:
        return kit.Verdict(False, "")

    steps = [
        kit.AnswerStep(id="a", text="t", question="q", check=never),
        kit.WatchStep(id="w", text="t", watch=never),
        kit.ReadStep(id="r", text="t"),
    ]
    assert all(isinstance(step, kit.Step) for step in steps)
    assert not isinstance(kit.Slide(id="s", title="t", text="x"), kit.Step)


def test_a_level_writes_a_name_the_player_chose_with_the_text_parsers_own_code_helper() -> None:
    assert kit.code is markup.code


def test_kit_hands_out_the_status_lists_every_level_asks_for() -> None:
    for name in ["untracked", "nested", "staged", "unstaged", "mode_changed", "conflicted"]:
        assert name in kit.__all__
        assert getattr(kit, name) is getattr(repomap, name)


def test_a_level_sets_up_the_playground_and_presses_its_buttons_through_the_toolkit() -> None:
    assert kit.setup_playground is playground.setup
    assert kit.press is playground.press
    assert {"setup_playground", "press"} <= set(kit.__all__)


def test_a_level_writes_its_scene_card_and_reactions_with_the_toolkit() -> None:
    frame = kit.SceneFrame(art="flag", text="`git init` plants the flag.")
    card = kit.CommandCard(command="git init", text="Makes the current folder a repository.")
    rule = kit.ReactionRule(line=r"git init\b", mood="ok", text="Flag planted.")
    assert (frame.art, card.command, rule.mood) == ("flag", "git init", "ok")
    assert set(typing.get_args(kit.Art)) >= {"space", "timeline", "terminal", "planet", "flag", "zones", "conveyor"}


TYPED: list[kit.Command] = [
    {"line": "git status", "status": 128},
    {"line": "git init", "status": 0},
    {"line": "ls -a", "status": 0},
    {"line": "git init again", "status": 129},
    {"line": "git status", "status": 0},
]


def test_a_level_asks_whether_a_line_was_typed_and_how_it_ended() -> None:
    assert kit.typed(TYPED, r"ls -a\b", "ok")
    assert kit.typed(TYPED, r"git status\b")
    assert not kit.typed(TYPED, r"git add\b")
    assert not kit.typed(TYPED[:1], r"git status\b", "ok")


def test_a_level_reads_the_lines_typed_after_the_last_one_that_worked() -> None:
    assert kit.after(TYPED, r"git init\b") == TYPED[2:]
    assert kit.after(TYPED, r"git add\b") == TYPED
    assert kit.after(TYPED, r"git status\b") == []
