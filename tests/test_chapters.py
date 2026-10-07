from typing import get_args

from firstcommit.chapters import BLURBS, CHAPTERS
from firstcommit.records import Language


def test_every_chapter_has_one_short_line_of_blurb_and_nothing_else_has_one() -> None:
    assert list(BLURBS) == list(CHAPTERS)
    assert all(blurb.strip() and "\n" not in blurb and len(blurb) <= 80 for texts in BLURBS.values() for blurb in texts.values())


def test_every_chapter_has_its_name_and_blurb_in_every_language() -> None:
    languages = set(get_args(Language))
    assert all(set(texts) == languages and all(text.strip() for text in texts.values()) for texts in [*CHAPTERS.values(), *BLURBS.values()])
