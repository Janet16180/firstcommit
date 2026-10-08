from typing import get_args

from firstcommit import runner
from firstcommit.chapters import BLURBS, CHAPTERS, PLAY_ORDER
from firstcommit.records import Language


def test_every_chapter_has_one_short_line_of_blurb_and_nothing_else_has_one() -> None:
    assert list(BLURBS) == list(CHAPTERS)
    assert all(blurb.strip() and "\n" not in blurb and len(blurb) <= 80 for texts in BLURBS.values() for blurb in texts.values())


def test_every_chapter_has_its_name_and_blurb_in_every_language() -> None:
    languages = set(get_args(Language))
    assert all(set(texts) == languages and all(text.strip() for text in texts.values()) for texts in [*CHAPTERS.values(), *BLURBS.values()])


def test_the_play_order_lists_every_level_of_the_game_once_chapter_by_chapter() -> None:
    assert list(runner.catalogue()) == list(PLAY_ORDER)
    chapters = [level_id.split("-", 1)[0] for level_id in PLAY_ORDER]
    assert chapters == sorted(chapters, key=list(CHAPTERS).index)


def test_name_tags_comes_after_the_mothership_whose_new_recruit_comes_just_before_base_7() -> None:
    assert list(CHAPTERS)[3:8] == ["mothership", "names", "branch", "conflict", "undo"]
    assert (CHAPTERS["names"]["en"], CHAPTERS["names"]["es"]) == ("Name tags", "Etiquetas")
    assert PLAY_ORDER[PLAY_ORDER.index("mothership-base7") - 1] == "mothership-recruit"
