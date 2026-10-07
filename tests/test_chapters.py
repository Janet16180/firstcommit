from firstcommit.chapters import BLURBS, CHAPTERS


def test_every_chapter_has_one_short_line_of_blurb_and_nothing_else_has_one() -> None:
    assert list(BLURBS) == list(CHAPTERS)
    assert all(blurb.strip() and "\n" not in blurb and len(blurb) <= 80 for blurb in BLURBS.values())
