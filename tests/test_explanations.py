import json
from pathlib import Path
from typing import Any

import pytest

from firstcommit import explanations, gitcmd, markup, playground, records, repomap, save
from firstcommit.lab import Lab
from playground_helpers import clone, conflicted_lab, new_lab, presses

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
"""Every button of the playgrounds the table was recorded in, by id."""
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


def explained(case: dict[str, Any], buttons: frozenset[str] = CATALOGUE) -> explanations.Explanation:
    """
    Explain a recorded case.

    Parameters
    ----------
    case : dict[str, Any]
        A case of the table.
    buttons : frozenset[str]
        The playground's buttons.

    Returns
    -------
    explanations.Explanation
        What `explanations.explain` gives for it.
    """
    place = "project" if case["who"] == "you" else "teammate"
    return explanations.explain(recorded_press(case), case["before"][place], case["after"][place], recorded_facts(case), buttons)


@pytest.mark.parametrize("key", list(PRESSED))
def test_every_recorded_press_gets_its_recorded_explanation_and_fix(key: str) -> None:
    case = PRESSED[key]
    expected = case["explanation"]
    assert explained(case) == {
        "tag": expected["tag"],
        "file": expected["file"],
        "text": expected["text"],
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


def explain_press(lab: Lab, person: records.Who, button: str) -> explanations.Explanation:
    """
    Press a playground button on real git and explain it, as the game does.

    Parameters
    ----------
    lab : Lab
        A playground lab.
    person : records.Who
        Who presses.
    button : str
        The button's id.

    Returns
    -------
    explanations.Explanation
        The explanation of that press.
    """
    before = {"github": repomap.snapshot(lab.github), "you": repomap.snapshot(lab.project), "alex": repomap.snapshot(lab.teammate)}
    facts = playground.facts(lab, person, before[person], before["github"])
    press = playground.press(lab, person, button)
    return explanations.explain(press, before[person], repomap.snapshot(clone(lab, person)), facts, playground.BUTTON_IDS)


def test_a_commit_refused_for_a_conflict_says_so_even_without_an_identity() -> None:
    with new_lab() as lab:
        conflicted_lab(lab)
        gitcmd.output(save.home(), "config", "--global", "--unset", "user.email")
        found = explain_press(lab, "you", "commit")
        assert (found["tag"], found["file"]) == ("E35", "notes.txt")


def test_a_push_with_nothing_to_send_names_uncommitted_work_only_in_the_button_files() -> None:
    with new_lab() as lab:
        (lab.project / "other.txt").write_text("not a button file\n")
        assert explain_press(lab, "you", "push")["tag"] == "E17"
        presses(lab, "you", "edit:notes.txt")
        assert explain_press(lab, "you", "push")["tag"] == "E18"
