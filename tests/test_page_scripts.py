"""Run the node tests of the page scripts (tests/js), and keep their sample records true to `firstcommit.game`."""

import json
import shutil
import subprocess
import types
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints, is_typeddict

import pytest

from firstcommit import game
from firstcommit.repomap import Snapshot

JS_TESTS = Path(__file__).parent / "js"
RECORDS = JS_TESTS / "records.json"
NODE = shutil.which("node")
RECORD_TYPES: dict[str, Any] = {
    "status": game.Status,
    "level": game.LevelView,
    "lesson": game.LessonView,
    "active": game.ActiveView,
    "step": game.StepResult,
    "check_unsolved": game.CheckResult,
    "check_solved": game.CheckResult,
    "hint": game.HintView,
    "observation": game.Observation,
    "cards": list[game.CardView],
    "card_result": game.CardResult,
    "notes": game.Notes,
    "snapshots": dict[str, Snapshot],
}


def mismatches(value: Any, kind: Any, where: str) -> list[str]:
    """
    Compare a JSON value with a type of the API contract, field by field.

    Parameters
    ----------
    value : Any
        Decoded JSON.
    kind : Any
        A TypedDict, a union, ``list[...]``, ``dict[str, ...]``, a Literal, None or a plain type.

    where : str
        Path of the value, for the messages.

    Returns
    -------
    list[str]
        One message per difference; empty when the value fits the type exactly.
    """
    origin = get_origin(kind)
    problems: list[str] = []
    if is_typeddict(kind):
        hints = get_type_hints(kind)
        if not isinstance(value, dict) or set(value) != set(hints):
            problems = [f"{where}: fields {sorted(value) if isinstance(value, dict) else value!r}, expected {sorted(hints)}"]
        else:
            problems = [problem for key, hint in hints.items() for problem in mismatches(value[key], hint, f"{where}.{key}")]
    elif origin in (Union, types.UnionType):
        tries = [mismatches(value, option, where) for option in get_args(kind)]
        problems = [] if [] in tries else min(tries, key=len)
    elif origin is list:
        problems = [f"{where}: not a list"] if not isinstance(value, list) else []
        problems += [problem for index, item in enumerate(value if isinstance(value, list) else []) for problem in mismatches(item, get_args(kind)[0], f"{where}[{index}]")]
    elif origin is dict:
        problems = [f"{where}: not an object"] if not isinstance(value, dict) else []
        problems += [problem for key, item in (value.items() if isinstance(value, dict) else []) for problem in mismatches(item, get_args(kind)[1], f"{where}.{key}")]
    elif origin is Literal:
        problems = [] if value in get_args(kind) else [f"{where}: {value!r} is not one of {get_args(kind)}"]
    elif kind is type(None):
        problems = [] if value is None else [f"{where}: {value!r} is not null"]
    elif kind is int:
        problems = [] if isinstance(value, int) and not isinstance(value, bool) else [f"{where}: {value!r} is not an integer"]
    else:
        problems = [] if isinstance(value, kind) else [f"{where}: {value!r} is not a {kind.__name__}"]
    return problems


@pytest.mark.slow
@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_the_page_scripts_pass_their_node_tests() -> None:
    assert NODE is not None
    # Node 21+ reads --test arguments as files or globs, not directories, so list the files for every version.
    test_files = [str(path) for path in sorted(JS_TESTS.glob("*.test.js"))]
    result = subprocess.run([NODE, "--test", *test_files], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_page_tests_sample_records_have_exactly_the_fields_of_the_games_records() -> None:
    records = json.loads(RECORDS.read_text())
    assert set(records) == set(RECORD_TYPES)
    problems = [problem for name, kind in RECORD_TYPES.items() for problem in mismatches(records[name], kind, name)]
    assert problems == []


def test_a_record_with_a_missing_or_extra_field_is_caught() -> None:
    hint = {"hint": [], "used": 1, "total": 3, "cost": 10}
    assert mismatches(hint, game.HintView, "hint") == []
    assert mismatches({**hint, "extra": 1}, game.HintView, "hint") != []
    assert mismatches({**hint, "used": True}, game.HintView, "hint") != []
    assert mismatches({**hint, "hint": [{"kind": "para", "spans": [{"text": "a"}]}]}, game.HintView, "hint") != []
