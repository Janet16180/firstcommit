import random
import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from firstcommit import cards
from firstcommit.save import CardEntry

TODAY = date(2026, 10, 6)

DECK = '''
notes = """
The three areas.
"""

[[card]]
id = "basics-staging-area"
kind = "choice"
level = 1
prompt = "What does `git add` change?"
correct = "The staging area"
wrong = ["The last commit", "The remote"]
explain = "It stages."
source = "git-add(1)"

[[card]]
id = "basics-hello-blob"
kind = "predict"
level = 2
prompt = "What does the last command print?"
code = "printf 'hello\\\\n' | git hash-object --stdin"
correct = "ce013625030ba8dba906f756967f9e9ca394464a"
wrong = ["ce01362", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", "none"]
explain = "A blob hash depends only on the content."
source = "git-hash-object(1)"
verify = "true"

[[card]]
id = "basics-default-branch"
kind = "text"
level = 3
prompt = "Which branch does the game start you on?"
accept = ["main", "the main branch"]
placeholder = "a branch name"
explain = "The game's configuration sets it."
source = "git-init(1)"
'''


def write_deck(folder: Path, text: str, chapter: str = "basics") -> Path:
    """
    Write a deck file for a chapter.

    Parameters
    ----------
    folder : Path
        Folder to write it in.
    text : str
        TOML text.
    chapter : str
        Chapter id, the file's name.

    Returns
    -------
    Path
        The deck file.
    """
    path = folder / f"{chapter}.toml"
    path.write_text(text)
    return path


def card(card_id: str = "basics-x", kind: cards.CardKind = "choice", level: int = 1) -> cards.Card:
    """
    Make a valid card of a kind, for schedule and judging tests.

    Parameters
    ----------
    card_id : str
        The card's id.
    kind : cards.CardKind
        Its kind.
    level : int
        Its level.

    Returns
    -------
    cards.Card
        A card with a right answer ``"right"`` and three distractors (text cards accept ``"Main Branch"``).
    """
    if kind == "text":
        return cards.Card(card_id, "basics", kind, level, "Prompt?", "Why.", "src", accept=("Main Branch", "main"))
    return cards.Card(card_id, "basics", kind, level, "Prompt?", "Why.", "src", correct="right", wrong=("wrong", "worse", "worst"))


def test_a_deck_file_loads_into_cards_of_its_chapter(tmp_path: Path) -> None:
    deck = cards.load_deck(write_deck(tmp_path, DECK))
    assert deck.chapter == "basics"
    assert deck.notes == "The three areas.\n"
    assert [(entry.id, entry.kind, entry.level, entry.chapter) for entry in deck.cards] == [
        ("basics-staging-area", "choice", 1, "basics"),
        ("basics-hello-blob", "predict", 2, "basics"),
        ("basics-default-branch", "text", 3, "basics"),
    ]
    choice, predict, text = deck.cards
    assert choice.wrong == ("The last commit", "The remote")
    assert predict.code == "printf 'hello\\n' | git hash-object --stdin"
    assert predict.verify == "true"
    assert text.accept == ("main", "the main branch")
    assert text.placeholder == "a branch name"


def test_a_chapter_without_a_deck_file_has_an_empty_deck(tmp_path: Path) -> None:
    assert cards.deck("toolbox", tmp_path) == cards.Deck("toolbox", "", ())


def test_an_unknown_chapter_has_no_deck(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        cards.deck("nonsense", tmp_path)


def test_a_deck_file_must_be_named_after_a_chapter(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"nonsense\.toml.*chapter"):
        cards.load_deck(write_deck(tmp_path, DECK, chapter="nonsense"))


def deck_with(card_text: str) -> str:
    """
    Make a deck holding one card written as TOML key lines.

    Parameters
    ----------
    card_text : str
        The card's lines, without the ``[[card]]`` header.

    Returns
    -------
    str
        The deck's TOML text.
    """
    return "[[card]]\n" + card_text


VALID_CHOICE = """id = "basics-one"
kind = "choice"
level = 1
prompt = "P?"
correct = "right"
wrong = ["wrong", "worse"]
explain = "E."
source = "S"
"""

BROKEN = {
    "an id outside its chapter": (VALID_CHOICE.replace('"basics-one"', '"hash-one"'), "basics-"),
    "an id that is only the chapter": (VALID_CHOICE.replace('"basics-one"', '"basics-"'), "basics-"),
    "an unknown kind": (VALID_CHOICE.replace('"choice"', '"essay"'), "kind"),
    "a level above 3": (VALID_CHOICE.replace("level = 1", "level = 4"), "level"),
    "a level that is not a number": (VALID_CHOICE.replace("level = 1", "level = true"), "level"),
    "a missing explanation": (VALID_CHOICE.replace('explain = "E."\n', ""), "explain"),
    "an empty prompt": (VALID_CHOICE.replace('"P?"', '""'), "prompt"),
    "an unknown field": (VALID_CHOICE + 'hint = "x"\n', "hint"),
    "one distractor": (VALID_CHOICE.replace('["wrong", "worse"]', '["wrong"]'), "wrong"),
    "six distractors": (VALID_CHOICE.replace('["wrong", "worse"]', '["a", "b", "c", "d", "e", "f"]'), "wrong"),
    "a distractor equal to the answer": (VALID_CHOICE.replace('["wrong", "worse"]', '["wrong", "right"]'), "wrong"),
    "the same distractor twice": (VALID_CHOICE.replace('["wrong", "worse"]', '["wrong", "wrong"]'), "wrong"),
    "a distractor that is not text": (VALID_CHOICE.replace('["wrong", "worse"]', '["wrong", 3]'), "wrong"),
    "a predict card without code": (VALID_CHOICE.replace('"choice"', '"predict"'), "code"),
    "a text card with a right option": (VALID_CHOICE.replace('"choice"', '"text"'), "correct"),
    "a text card that accepts nothing": ('id = "basics-t"\nkind = "text"\nlevel = 1\nprompt = "P?"\naccept = []\nexplain = "E."\nsource = "S"\n', "accept"),
    "an empty verify snippet": (VALID_CHOICE + 'verify = ""\n', "verify"),
}


@pytest.mark.parametrize("case", BROKEN.values(), ids=list(BROKEN))
def test_a_broken_card_is_refused_with_the_file_the_card_and_the_field(tmp_path: Path, case: tuple[str, str]) -> None:
    text, field = case
    with pytest.raises(ValueError, match=rf"basics\.toml.*card 1.*{re.escape(field)}"):
        cards.load_deck(write_deck(tmp_path, deck_with(text)))


def test_two_cards_may_not_share_an_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"basics-one.*twice"):
        cards.load_deck(write_deck(tmp_path, deck_with(VALID_CHOICE) + deck_with(VALID_CHOICE)))


@pytest.mark.parametrize(("text", "problem"), [("[[card\n", "TOML"), ("notes = 3\n", "notes"), ("title = 'x'\n", "title"), ("card = 3\n", "card")])
def test_a_broken_deck_file_is_refused_with_its_name(tmp_path: Path, text: str, problem: str) -> None:
    with pytest.raises(ValueError, match=rf"basics\.toml.*{problem}"):
        cards.load_deck(write_deck(tmp_path, text))


def test_a_new_card_is_due() -> None:
    assert cards.is_due(None, TODAY)


def test_a_card_is_due_on_its_due_date_and_after() -> None:
    entry: CardEntry = {"box": 2, "due": TODAY.isoformat()}
    assert cards.is_due(entry, TODAY)
    assert cards.is_due(entry, TODAY + timedelta(days=4))
    assert not cards.is_due(entry, TODAY - timedelta(days=1))


def test_the_leitner_intervals_are_the_documented_ones() -> None:
    assert cards.INTERVALS == (0, 1, 3, 7, 16, 35)


def test_each_right_answer_moves_a_card_up_a_box_and_spaces_it_further_out() -> None:
    entry = None
    dues = []
    for _ in range(7):
        entry = cards.reschedule(entry, correct=True, today=TODAY)
        dues.append((entry["box"], (date.fromisoformat(entry["due"]) - TODAY).days))
    assert dues == [(1, 1), (2, 3), (3, 7), (4, 16), (5, 35), (5, 35), (5, 35)]


def test_a_wrong_answer_sends_a_card_back_to_the_first_box_due_today() -> None:
    assert cards.reschedule({"box": 4, "due": "2026-01-01"}, correct=False, today=TODAY) == {"box": 0, "due": TODAY.isoformat()}


@given(st.none() | st.builds(lambda box: CardEntry(box=box, due="2026-01-01"), st.integers(0, 5)), st.booleans(), st.dates())
def test_a_rescheduled_card_is_due_after_its_box_interval(entry: CardEntry | None, correct: bool, today: date) -> None:
    after = cards.reschedule(entry, correct, today)
    assert 0 <= after["box"] < len(cards.INTERVALS)
    assert date.fromisoformat(after["due"]) == today + timedelta(days=cards.INTERVALS[after["box"]])


def test_cards_due_for_review_come_first_oldest_first_then_new_cards_easiest_first() -> None:
    deck = [card("basics-new-hard", level=3), card("basics-later"), card("basics-due-recent"), card("basics-new-easy"), card("basics-due-old")]
    entries: dict[str, CardEntry] = {
        "basics-later": {"box": 3, "due": "2026-10-10"},
        "basics-due-recent": {"box": 1, "due": "2026-10-06"},
        "basics-due-old": {"box": 2, "due": "2026-10-01"},
    }
    picked = cards.pick(deck, entries, TODAY, limit=10, rng=random.Random(1))
    assert [entry.id for entry in picked] == ["basics-due-old", "basics-due-recent", "basics-new-easy", "basics-new-hard"]


def test_picking_stops_at_the_limit() -> None:
    deck = [card(f"basics-{number}") for number in range(5)]
    assert len(cards.pick(deck, {}, TODAY, limit=3, rng=random.Random(1))) == 3
    assert cards.pick(deck, {}, TODAY, limit=0, rng=random.Random(1)) == []


@given(st.lists(st.tuples(st.integers(1, 3), st.none() | st.integers(-40, 40)), max_size=12), st.integers(0, 15), st.randoms())
def test_picked_cards_are_distinct_new_or_due_and_as_many_as_allowed(specs: list[tuple[int, int | None]], limit: int, rng: random.Random) -> None:
    deck = [card(f"basics-{number}", level=level) for number, (level, _) in enumerate(specs)]
    entries: dict[str, CardEntry] = {
        f"basics-{number}": {"box": 1, "due": (TODAY + timedelta(days=offset)).isoformat()}
        for number, (_, offset) in enumerate(specs)
        if offset is not None
    }
    picked = cards.pick(deck, entries, TODAY, limit, rng)
    eligible = [entry for entry in deck if cards.is_due(entries.get(entry.id), TODAY)]
    assert len({entry.id for entry in picked}) == len(picked) == min(limit, len(eligible))
    assert all(cards.is_due(entries.get(entry.id), TODAY) for entry in picked)


def test_choices_are_the_answer_and_the_distractors_shuffled() -> None:
    question = card()
    orders = {tuple(cards.choices(question, random.Random(seed))) for seed in range(30)}
    assert all(sorted(order) == sorted(["right", "wrong", "worse", "worst"]) for order in orders)
    assert len({order.index("right") for order in orders}) > 1


def test_a_text_card_has_no_choices() -> None:
    assert cards.choices(card(kind="text"), random.Random(1)) == []


def test_a_choice_card_accepts_exactly_its_right_option() -> None:
    question = card()
    assert cards.judge(question, "right")
    assert not cards.judge(question, "wrong")
    assert not cards.judge(question, " right")
    assert not cards.judge(question, "Right")


def test_a_text_card_accepts_any_listed_spelling_whatever_the_case_and_spacing() -> None:
    question = card(kind="text")
    assert cards.judge(question, "  main branch ")
    assert cards.judge(question, "MAIN")
    assert cards.judge(question, "main\tbranch")
    assert not cards.judge(question, "master")
    assert not cards.judge(question, "")


@given(st.sampled_from(["Main Branch", "main"]), st.randoms())
def test_a_text_answer_survives_any_change_of_case_or_whitespace(spelling: str, rng: random.Random) -> None:
    typed = "".join(letter.upper() if rng.random() < 0.5 else letter for letter in spelling).replace(" ", " \t " if rng.random() < 0.5 else " ")
    assert cards.judge(card(kind="text"), f" {typed}  ")


@given(st.sampled_from(cards.KINDS), st.text(max_size=6000))
def test_judging_any_reply_never_raises(kind: cards.CardKind, reply: str) -> None:
    cards.judge(card(kind=kind), reply)


def test_the_answer_shown_is_the_right_option_or_the_first_accepted_spelling() -> None:
    assert cards.answer(card()) == "right"
    assert cards.answer(card(kind="text")) == "Main Branch"
