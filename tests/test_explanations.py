import json
from pathlib import Path
from typing import Any

import pytest

from firstcommit import explanations, markup, records

TABLE = Path(__file__).parent.parent / "docs" / "drafts" / "playground-errors.json"
CASES: dict[str, Any] = json.loads(TABLE.read_text())
PRESSED: dict[str, Any] = {key: case for key, case in CASES.items() if case["button"] != "terminal"}
"""Every recorded press; the commands typed in the terminal earn no explanation."""
TABLE_FILES = ("README.md", "notes.txt", "todo.txt", "you.txt", "alex.txt")
CATALOGUE = frozenset(
    [
        "init",
        "clone",
        "status",
        "commit",
        "push",
        "fetch",
        "pull",
        "pull-no-rebase",
        "merge-abort",
        *(f"{kind}:{name}" for kind in ("edit", "delete", "add", "keep-ours", "keep-theirs") for name in TABLE_FILES),
    ]
)
"""Every button of the one-person playgrounds the table was recorded in, by id."""
TWO_PEOPLE_CATALOGUE = frozenset(button for button in CATALOGUE if button.partition(":")[0] not in ("init", "clone", "delete"))
"""The buttons of the two-person playground the table was recorded in."""
REWORDED = {"records its author's name and email": "records who made it: a name and an email"}
"""Words the game changed after the table was recorded: git names the committer, not the author, when a merge commit has no identity."""
OWN_FILES = {"you": "you.txt", "alex": "alex.txt"}
"""The file each person's edit and add acted on in the two-person playground the table was recorded in, whose ids named no file."""


def recorded_press(case: dict[str, Any]) -> records.Press:
    """
    Give a recorded case's press as the game records it, with its button's id.

    Parameters
    ----------
    case : dict[str, Any]
        A case of the table.

    Returns
    -------
    records.Press
        The press.
    """
    button = case["button"]
    if case["merged"] and button in ("edit", "add"):
        button = f"{button}:{OWN_FILES[case['who']]}"
    return {"person": case["who"], "button": button, "command": case["line"], "status": case["status"], "output": case["stdout"] + case["stderr"]}


def recorded_facts(case: dict[str, Any]) -> records.Facts:
    """
    Give the facts a recorded case was explained from.

    Parameters
    ----------
    case : dict[str, Any]
        A case of the table.

    Returns
    -------
    records.Facts
        GitHub before the press (None where there was none), the folder and the configuration.
    """
    github = case["before"]["github"]
    return {"github": github if github["exists"] else None, "folder": case["folder"], "config": case["config"]}


def explained(case: dict[str, Any], buttons: frozenset[str] | None = None) -> explanations.Explanation:
    """
    Explain a recorded case.

    Parameters
    ----------
    case : dict[str, Any]
        A case of the table.
    buttons : frozenset[str] | None
        The playground's buttons, or None for those of the playground it was recorded in.

    Returns
    -------
    explanations.Explanation
        What `explanations.explain` gives for it.
    """
    place = "project" if case["who"] == "you" else "teammate"
    recorded_in = TWO_PEOPLE_CATALOGUE if case["before"]["teammate"]["exists"] else CATALOGUE
    found = explanations.explain(recorded_press(case), case["before"][place], case["after"][place], recorded_facts(case), recorded_in if buttons is None else buttons)
    return found


@pytest.mark.parametrize("key", list(PRESSED))
def test_every_recorded_press_gets_its_recorded_explanation_and_fix(key: str) -> None:
    case = PRESSED[key]
    expected = case["explanation"]
    text = expected["text"]
    for old, new in REWORDED.items():
        text = text.replace(old, new)
    assert explained(case) == {
        "tag": expected["tag"],
        "file": expected["file"],
        "text": text,
        "fix": case["fix"]["button"],
        "fix_line": case["fix"]["line"],
    }


def test_the_table_covers_every_explanation_but_the_one_that_adds_nothing() -> None:
    told = {case["explanation"]["tag"] for case in PRESSED.values()}
    assert set(explanations.EXPLANATIONS) - told == {"E0"}


def test_a_fix_the_playground_has_no_button_for_is_left_out() -> None:
    e1 = next(case for case in PRESSED.values() if case["explanation"]["tag"] == "E1")
    assert explained(e1)["fix"] == "init"
    assert explained(e1, CATALOGUE - {"init"})["fix"] == ""
    e5 = next(case for case in PRESSED.values() if case["explanation"]["tag"] == "E5")
    assert explained(e5, CATALOGUE - {f"edit:{e5['explanation']['file']}"})["fix"] == ""


def test_an_explanation_writes_its_file_as_code_in_the_games_markup() -> None:
    e12 = next(case for case in PRESSED.values() if case["explanation"]["tag"] == "E12")
    found = explained(e12)
    [paragraph] = markup.parse(found["text"])
    assert paragraph["kind"] == "para"
    assert {"text": found["file"], "code": True} in paragraph["spans"]


def test_a_refusal_no_rule_explains_adds_nothing_to_gits_own_message() -> None:
    status = next(case for case in PRESSED.values() if case["button"] == "status")
    failed = {**status, "status": 1}
    assert explained(failed)["tag"] == "E0"
    assert (explained(failed)["fix"], explained(failed)["fix_line"]) == ("", "")
