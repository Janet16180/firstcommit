import itertools
import json
import textwrap
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
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
