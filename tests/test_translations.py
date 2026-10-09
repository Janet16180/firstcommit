"""
Every text in Spanish keeps the shape of its English: the same placeholders, code spans, commands and paragraph and bullet counts.

A translation may reorder a sentence, so code spans are compared as a sorted list; a verbatim
block keeps its commands and may translate the comments after ``#``.
"""

import importlib.util
import re
from typing import Any

import pytest

import sample_levels
from firstcommit import cards, game, markup, reactions, reactions_es, runner
from firstcommit.chapters import BLURBS, CHAPTERS
from firstcommit.markup import Block, Span

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
# A str.format field: one brace, a name, one brace, not part of a {{placeholder}}.
FORMAT_FIELD = re.compile(r"(?<!\{)\{(\w+)\}(?!\})")

NEVER = {
    "confirmación": "commit",
    "confirmar": "commit (hacer un commit)",
    "empujar": "push (hacer push)",
    "empuja": "push (haz push)",
    "jalar": "pull (hacer pull)",
    "fusión": "merge",
    "fusionar": "merge (hacer merge)",
    "rama": "branch (el branch)",
    "ramas": "branch (los branches)",
    "área de preparación": "staging area (el staging area)",
    "preparado": "staging area (está en el staging area)",
    "preparados": "staging area (están en el staging area)",
    "preparar": "staging area (agregar al staging area)",
    "prepara": "staging area (agrega al staging area)",
    "índice": "staging area",
    "bifurcación": "branch",
    "registro de cambios": "log",
    "clonación": "clone",
    "ordenador": "computadora",
    "pulsa": "presiona",
    "añade": "agrega",
    "añadir": "agregar",
    "añades": "agregas",
    "vosotros": "ustedes",
    "directorio de trabajo": "carpeta de trabajo",
    "historial": "historia",
    "el carpeta": "la carpeta",
    "has preguntado": "le preguntaste (simple past)",
    "ha creado": "creó (simple past)",
    "se ha negado": "se negó (simple past)",
    "ha desaparecido": "desapareció (simple past)",
}
"""Spanish forms never written, each with what docs/i18n-glossary.md says instead."""

LEVELS = [*runner.catalogue().values(), *runner.discover(sample_levels).values()]
SPANISH_DECKS = sorted(path.name.removesuffix(".es.toml") for path in cards.DECKS.glob("*.es.toml"))


def spans(block: Block) -> list[Span]:
    """
    List the spans of a block.

    Parameters
    ----------
    block : Block
        A parsed block.

    Returns
    -------
    list[Span]
        A paragraph's spans, or every bullet's in order; none for a verbatim block.
    """
    found: list[Span] = []
    if block["kind"] == "para":
        found = block["spans"]
    elif block["kind"] == "bullets":
        found = [span for item in block["items"] for span in item]
    return found


def shape(text: str) -> dict[str, Any]:
    """
    Describe what a translation of a text must keep.

    Parameters
    ----------
    text : str
        Game markup.

    Returns
    -------
    dict[str, Any]
        Its blocks' kinds with each list's bullet count, its verbatim blocks without their
        comments, its code spans sorted, and its placeholders and format fields sorted.
    """
    blocks = markup.parse(text)
    return {
        "blocks": [(block["kind"], len(block["items"]) if block["kind"] == "bullets" else 0) for block in blocks],
        "verbatim": [[line.split("#")[0].rstrip() for line in block["text"].splitlines()] for block in blocks if block["kind"] == "code"],
        "code": sorted(span["text"] for block in blocks for span in spans(block) if span["code"]),
        "placeholders": sorted(PLACEHOLDER.findall(text) + FORMAT_FIELD.findall(text)),
    }


def assert_same_shape(pairs: list[tuple[str, str]]) -> None:
    """
    Check that each Spanish text keeps the shape of its English one, and is written.

    Parameters
    ----------
    pairs : list[tuple[str, str]]
        English and Spanish texts.
    """
    for english, spanish in pairs:
        assert bool(spanish.strip()) == bool(english.strip()), f"{english!r} has no Spanish"
        assert shape(spanish) == shape(english), f"\n{english}\n{spanish}"


def level_pairs(level: runner.Level) -> list[tuple[str, str]]:
    """
    Pair every English text of a level with its Spanish.

    Parameters
    ----------
    level : runner.Level
        The level.

    Returns
    -------
    list[tuple[str, str]]
        Title, briefing, question, placeholder, hints, debrief, card, scene, each step's texts
        and options, and each message.
    """
    english, spanish = level.texts["en"], level.texts["es"]
    pairs = [
        (english.title, spanish.title),
        (english.briefing, spanish.briefing),
        (english.question, spanish.question),
        (english.placeholder, spanish.placeholder),
        (english.debrief, spanish.debrief),
        (english.card, spanish.card),
        *zip(english.hints, spanish.hints, strict=True),
        *zip(english.scene, spanish.scene, strict=True),
        *spanish.messages.items(),
    ]
    for step_id, step in english.steps.items():
        other = spanish.steps[step_id]
        pairs += [(getattr(step, name), getattr(other, name)) for name in ("text", "more", "question", "placeholder", "reveal")]
        pairs += list(zip(step.options, other.options, strict=True))
    return pairs


def spanish_texts() -> list[str]:
    """
    Gather every Spanish text the game shows.

    Returns
    -------
    list[str]
        The levels', the shared reactions', the game's own, the chapters', the card levels' and
        every Spanish deck's texts.
    """
    found = [*reactions.SPANISH.values(), *game.SPANISH.values(), *cards.LEVEL_NAMES["es"].values()]
    found += [texts["es"] for texts in [*CHAPTERS.values(), *BLURBS.values()]]
    for level in LEVELS:
        found += [spanish for _, spanish in level_pairs(level)]
    for chapter in SPANISH_DECKS:
        deck = cards.deck(chapter, "es")
        found.append(deck.notes)
        for card in deck.cards:
            found += [card.prompt, card.explain, card.placeholder, *card.shown.values(), *card.accept]
    return found


def prose(text: str) -> str:
    """
    Keep a text's prose: its code spans and verbatim lines dropped, lower-cased.

    Parameters
    ----------
    text : str
        Game markup.

    Returns
    -------
    str
        The words a translation chose; "Rama", capitalized, is the ship's computer and is left out.
    """
    words = " ".join(span["text"] for block in markup.parse(text) for span in spans(block) if not span["code"])
    return re.sub(r"\bRama\b", "", words).lower()


def test_no_spanish_text_uses_a_form_the_glossary_rules_out() -> None:
    found = {
        (word, text[:60])
        for text in spanish_texts()
        for word in NEVER
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", prose(text))
    }
    assert not found, "\n".join(f"{word!r} (use {NEVER[word]}) in {text!r}" for word, text in sorted(found))


def test_the_shape_of_a_text_is_its_blocks_code_and_placeholders() -> None:
    english = "Stage `a.txt` on `{{branch}}`, step {step}:\n\n- one\n- two\n\n    $ git add a.txt   # stage it"
    spanish = "En `{{branch}}`, paso {step}, prepara `a.txt`:\n\n- uno\n- dos\n\n    $ git add a.txt   # prepáralo"
    assert shape(spanish) == shape(english)
    assert shape("Prepara `b.txt`.") != shape("Stage `a.txt`.")
    assert shape("- uno") != shape("- one\n- two")
    assert shape("Uno.\n\nDos.") != shape("One. Two.")


def test_the_shared_reactions_have_every_text_in_spanish_with_the_same_shape() -> None:
    assert {rule.text for rule in reactions.RULES} <= set(reactions.SPANISH)
    english = {name: value for name, value in vars(reactions).items() if name.isupper() and isinstance(value, str) and value in reactions.SPANISH}
    assert set(english) == {name for name in vars(reactions_es) if name.isupper()}
    assert_same_shape(list(reactions.SPANISH.items()))


def test_the_games_own_messages_have_the_same_shape_in_spanish() -> None:
    assert_same_shape(list(game.SPANISH.items()))


def test_the_chapters_names_and_blurbs_have_the_same_shape_in_spanish() -> None:
    assert_same_shape([(texts["en"], texts["es"]) for texts in [*CHAPTERS.values(), *BLURBS.values()]])


@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_a_levels_spanish_texts_have_the_shape_of_its_english_ones(level: runner.Level) -> None:
    assert_same_shape(level_pairs(level))


def test_every_level_and_every_deck_of_the_game_has_its_spanish() -> None:
    for level in runner.catalogue().values():
        assert importlib.util.find_spec(f"firstcommit.levels.{level.id.replace('-', '_')}_es") is not None, level.id
    english_decks = sorted(path.stem for path in cards.DECKS.glob("*.toml") if not path.name.endswith(".es.toml"))
    assert english_decks == SPANISH_DECKS


@pytest.mark.parametrize("chapter", SPANISH_DECKS)
def test_a_spanish_deck_has_the_shape_of_its_english_deck(chapter: str) -> None:
    english, spanish = cards.deck(chapter, "en"), cards.deck(chapter, "es")
    pairs = [(english.notes, spanish.notes)]
    for card, other in zip(english.cards, spanish.cards, strict=True):
        pairs += [(card.prompt, other.prompt), (card.explain, other.explain), (card.placeholder, other.placeholder), *other.shown.items()]
    assert_same_shape(pairs)
