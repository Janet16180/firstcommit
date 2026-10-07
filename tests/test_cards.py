import random
import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from firstcommit import cards, score
from firstcommit.save import CardEntry

TODAY = date(2026, 10, 6)

DECK = '''
notes = """
The three areas.
"""

[[card]]
id = "cargo-staging-area"
kind = "choice"
level = 1
prompt = "What does `git add` change?"
correct = "The staging area"
wrong = ["The last commit", "The remote"]
explain = "It stages."
source = "git-add(1)"

[[card]]
id = "cargo-hello-blob"
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
id = "cargo-default-branch"
kind = "text"
level = 3
prompt = "Which branch does the game start you on?"
accept = ["main", "the main branch"]
placeholder = "a branch name"
explain = "The game's configuration sets it."
source = "git-init(1)"
'''


SPANISH_DECK = '''
notes = """
Las tres zonas.
"""

[[card]]
id = "cargo-staging-area"
prompt = "¿Qué cambia `git add`?"
correct = "El área de preparación"
wrong = ["El último commit", "El remoto"]
explain = "Prepara."

[[card]]
id = "cargo-hello-blob"
prompt = "¿Qué imprime el último comando?"
explain = "El hash de un blob solo depende del contenido."

[[card]]
id = "cargo-default-branch"
prompt = "¿En qué rama te pone el juego al empezar?"
accept = ["main", "la rama main"]
placeholder = "un nombre de rama"
explain = "Lo fija la configuración del juego."
'''


def write_deck(folder: Path, text: str, chapter: str = "cargo") -> Path:
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


def card(card_id: str = "cargo-x", kind: cards.CardKind = "choice", level: int = 1) -> cards.Card:
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
        return cards.Card(card_id, "cargo", kind, level, "Prompt?", "Why.", "src", accept=("Main Branch", "main"))
    return cards.Card(card_id, "cargo", kind, level, "Prompt?", "Why.", "src", correct="right", wrong=("wrong", "worse", "worst"))


def test_a_deck_file_loads_into_cards_of_its_chapter(tmp_path: Path) -> None:
    deck = cards.load_deck(write_deck(tmp_path, DECK))
    assert deck.chapter == "cargo"
    assert deck.notes == "The three areas.\n"
    assert [(entry.id, entry.kind, entry.level, entry.chapter) for entry in deck.cards] == [
        ("cargo-staging-area", "choice", 1, "cargo"),
        ("cargo-hello-blob", "predict", 2, "cargo"),
        ("cargo-default-branch", "text", 3, "cargo"),
    ]
    choice, predict, text = deck.cards
    assert choice.wrong == ("The last commit", "The remote")
    assert predict.code == "printf 'hello\\n' | git hash-object --stdin"
    assert predict.verify == "true"
    assert text.accept == ("main", "the main branch")
    assert text.placeholder == "a branch name"


def test_a_chapters_deck_is_read_from_the_deck_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    assert cards.deck("cargo", "en") == cards.load_deck(tmp_path / "cargo.toml")


def test_a_chapter_without_a_deck_file_has_an_empty_deck(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    assert cards.deck("toolbox", "en") == cards.deck("toolbox", "es") == cards.Deck("toolbox", "", ())


def test_an_unknown_chapter_has_no_deck() -> None:
    with pytest.raises(KeyError):
        cards.deck("nonsense", "en")


def test_a_card_is_found_by_its_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    assert cards.find("cargo-hello-blob", "en").kind == "predict"


@pytest.mark.parametrize("card_id", ["cargo-nothing", "nowhere-card", "cargo", ""])
def test_an_unknown_card_id_is_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, card_id: str) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    with pytest.raises(KeyError):
        cards.find(card_id, "en")


def test_a_spanish_deck_shows_its_texts_and_keeps_the_english_options_as_the_values_judged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    (tmp_path / "cargo.es.toml").write_text(SPANISH_DECK)
    deck = cards.deck("cargo", "es")
    choice, predict, text = deck.cards
    assert deck.notes == "Las tres zonas.\n"
    assert (choice.prompt, choice.explain, choice.correct) == ("¿Qué cambia `git add`?", "Prepara.", "The staging area")
    assert dict(choice.shown) == {"The staging area": "El área de preparación", "The last commit": "El último commit", "The remote": "El remoto"}
    assert cards.judge(choice, "The staging area") and not cards.judge(choice, "El área de preparación")
    assert (predict.prompt, predict.correct, dict(predict.shown), predict.code) == ("¿Qué imprime el último comando?", cards.find("cargo-hello-blob", "en").correct, {}, cards.find("cargo-hello-blob", "en").code)
    assert (text.accept, text.placeholder) == (("main", "la rama main"), "un nombre de rama")
    assert cards.judge(text, "La rama MAIN") and cards.answer(text) == "main"
    assert cards.find("cargo-staging-area", "es") == choice


def test_without_a_spanish_deck_file_the_spanish_deck_is_the_english_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    assert cards.deck("cargo", "es") == cards.deck("cargo", "en")


def spanish_with(old: str, new: str) -> str:
    """
    Change the Spanish test deck once.

    Parameters
    ----------
    old : str
        Text in `SPANISH_DECK`, which must be there.
    new : str
        Its replacement.

    Returns
    -------
    str
        The changed deck.
    """
    assert old in SPANISH_DECK
    return SPANISH_DECK.replace(old, new, 1)


BROKEN_SPANISH_DECKS = [
    (spanish_with('id = "cargo-hello-blob"', 'id = "cargo-other"'), r"cargo-other.*not a card of cargo\.toml"),
    (spanish_with('[[card]]\nid = "cargo-hello-blob"', '[[card]]\nid = "cargo-staging-area"'), r"cargo-staging-area.*twice"),
    (SPANISH_DECK.split("[[card]]\nid = \"cargo-default-branch\"")[0], r"cargo-default-branch.*no Spanish card"),
    (spanish_with('wrong = ["El último commit", "El remoto"]', 'wrong = ["El último commit"]'), r"cargo-staging-area.*`wrong` must hold 2"),
    (spanish_with('wrong = ["El último commit", "El remoto"]', 'wrong = ["El último commit", "El área de preparación"]'), r"cargo-staging-area.*the same text twice"),
    (spanish_with('correct = "El área de preparación"\n', ""), r"cargo-staging-area.*`correct` is missing"),
    (spanish_with('explain = "Prepara."', 'explain = ""'), r"cargo-staging-area.*`explain` must be text"),
    (spanish_with('explain = "El hash', 'correct = "x"\nexplain = "El hash'), r"cargo-hello-blob.*`correct` is not a field"),
    (spanish_with('accept = ["main", "la rama main"]', "accept = []"), r"cargo-default-branch.*`accept`"),
    (spanish_with('placeholder = "un nombre de rama"\n', ""), r"cargo-default-branch.*`placeholder` is missing"),
    (spanish_with('notes = """\nLas tres zonas.\n"""', ""), r"`notes` is missing"),
    ("source = 'x'\n" + SPANISH_DECK, r"`source` is not a key"),
]


@pytest.mark.parametrize(("text", "problem"), BROKEN_SPANISH_DECKS)
def test_a_spanish_deck_must_translate_every_card_of_its_english_deck_and_only_those(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str, problem: str) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    (tmp_path / "cargo.es.toml").write_text(text)
    with pytest.raises(ValueError, match=rf"cargo\.es\.toml.*{problem}"):
        cards.deck("cargo", "es")


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


VALID_CHOICE = """id = "cargo-one"
kind = "choice"
level = 1
prompt = "P?"
correct = "right"
wrong = ["wrong", "worse"]
explain = "E."
source = "S"
"""

BROKEN = {
    "an id outside its chapter": (VALID_CHOICE.replace('"cargo-one"', '"hash-one"'), "cargo-"),
    "an id that is only the chapter": (VALID_CHOICE.replace('"cargo-one"', '"cargo-"'), "cargo-"),
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
    "a text card that accepts nothing": ('id = "cargo-t"\nkind = "text"\nlevel = 1\nprompt = "P?"\naccept = []\nexplain = "E."\nsource = "S"\n', "accept"),
    "an empty verify snippet": (VALID_CHOICE + 'verify = ""\n', "verify"),
    "a placeholder with backticks": ('id = "cargo-t"\nkind = "text"\nlevel = 1\nprompt = "P?"\naccept = ["main"]\nplaceholder = "a `branch`"\nexplain = "E."\nsource = "S"\n', "placeholder"),
}


@pytest.mark.parametrize("case", BROKEN.values(), ids=list(BROKEN))
def test_a_broken_card_is_refused_with_the_file_the_card_and_the_field(tmp_path: Path, case: tuple[str, str]) -> None:
    text, field = case
    with pytest.raises(ValueError, match=rf"cargo\.toml.*card 1.*{re.escape(field)}"):
        cards.load_deck(write_deck(tmp_path, deck_with(text)))


def test_two_cards_may_not_share_an_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"cargo-one.*twice"):
        cards.load_deck(write_deck(tmp_path, deck_with(VALID_CHOICE) + deck_with(VALID_CHOICE)))


@pytest.mark.parametrize(("text", "problem"), [("[[card\n", "TOML"), ("notes = 3\n", "notes"), ("title = 'x'\n", "title"), ("card = 3\n", "card")])
def test_a_broken_deck_file_is_refused_with_its_name(tmp_path: Path, text: str, problem: str) -> None:
    with pytest.raises(ValueError, match=rf"cargo\.toml.*{problem}"):
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


@settings(deadline=None)
@given(st.none() | st.builds(lambda box: CardEntry(box=box, due="2026-01-01"), st.integers(0, 5)), st.booleans(), st.dates())
def test_a_rescheduled_card_is_due_after_its_box_interval(entry: CardEntry | None, correct: bool, today: date) -> None:
    after = cards.reschedule(entry, correct, today)
    assert 0 <= after["box"] < len(cards.INTERVALS)
    assert date.fromisoformat(after["due"]) == today + timedelta(days=cards.INTERVALS[after["box"]])


def test_cards_due_for_review_come_first_oldest_first_then_new_cards_easiest_first() -> None:
    deck = [card("cargo-a-new", level=3), card("cargo-b-later"), card("cargo-c-due-recent"), card("cargo-d-new", level=1), card("cargo-e-due-old")]
    entries: dict[str, CardEntry] = {
        "cargo-b-later": {"box": 3, "due": "2026-10-10"},
        "cargo-c-due-recent": {"box": 1, "due": "2026-10-06"},
        "cargo-e-due-old": {"box": 2, "due": "2026-10-01"},
    }
    picked = cards.pick(deck, entries, TODAY, limit=10, rng=random.Random(1))
    assert [entry.id for entry in picked] == ["cargo-e-due-old", "cargo-c-due-recent", "cargo-d-new", "cargo-a-new"]


def test_picking_stops_at_the_limit() -> None:
    deck = [card(f"cargo-{number}") for number in range(5)]
    assert len(cards.pick(deck, {}, TODAY, limit=3, rng=random.Random(1))) == 3
    assert cards.pick(deck, {}, TODAY, limit=0, rng=random.Random(1)) == []


@settings(deadline=None)
@given(st.lists(st.tuples(st.integers(1, 3), st.none() | st.integers(-40, 40)), max_size=12), st.integers(0, 15), st.randoms())
def test_picked_cards_are_distinct_new_or_due_and_as_many_as_allowed(specs: list[tuple[int, int | None]], limit: int, rng: random.Random) -> None:
    deck = [card(f"cargo-{number}", level=level) for number, (level, _) in enumerate(specs)]
    entries: dict[str, CardEntry] = {
        f"cargo-{number}": {"box": 1, "due": (TODAY + timedelta(days=offset)).isoformat()}
        for number, (_, offset) in enumerate(specs)
        if offset is not None
    }
    picked = cards.pick(deck, entries, TODAY, limit, rng)
    eligible = [entry for entry in deck if cards.is_due(entries.get(entry.id), TODAY)]
    assert len({entry.id for entry in picked}) == len(picked) == min(limit, len(eligible))
    assert all(cards.is_due(entries.get(entry.id), TODAY) for entry in picked)


@settings(deadline=None)
@given(st.lists(st.tuples(st.integers(1, 3), st.none() | st.integers(-40, 0)), max_size=12), st.randoms())
def test_due_cards_come_oldest_first_then_new_cards_easiest_first(specs: list[tuple[int, int | None]], rng: random.Random) -> None:
    deck = [card(f"cargo-{number:02}", level=level) for number, (level, _) in enumerate(specs)]
    entries: dict[str, CardEntry] = {
        f"cargo-{number:02}": {"box": 1, "due": (TODAY + timedelta(days=offset)).isoformat()}
        for number, (_, offset) in enumerate(specs)
        if offset is not None
    }
    picked = cards.pick(deck, entries, TODAY, len(deck), rng)
    seen = [entries[entry.id]["due"] for entry in picked if entry.id in entries]
    new = [entry.level for entry in picked if entry.id not in entries]
    assert [entry.id in entries for entry in picked] == [True] * len(seen) + [False] * len(new)
    assert seen == sorted(seen)
    assert new == sorted(new)


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


@settings(deadline=None)
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


def test_every_card_level_has_one_name() -> None:
    assert set(cards.LEVEL_NAMES) == set(cards.LEVELS)
    assert len(set(cards.LEVEL_NAMES.values())) == len(cards.LEVEL_NAMES)
    assert all(name.strip() for name in cards.LEVEL_NAMES.values())


def test_every_card_level_pays_xp() -> None:
    assert set(cards.LEVELS) == set(score.CARD_XP)
    assert all(score.card_score(level, correct=True, pays=True, streak=0).xp > 0 for level in cards.LEVELS)


def test_a_deck_is_read_once_per_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "DECKS", tmp_path)
    write_deck(tmp_path, DECK)
    assert cards.deck("cargo", "en") is cards.deck("cargo", "en")


def test_decks_from_another_folder_are_never_mixed_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, prompt in (("one", "First?"), ("two", "Second?")):
        folder = tmp_path / name
        folder.mkdir()
        write_deck(folder, deck_with(VALID_CHOICE.replace('"P?"', f'"{prompt}"')))
        monkeypatch.setattr(cards, "DECKS", folder)
        assert cards.deck("cargo", "en").cards[0].prompt == prompt
