import re
from collections.abc import Collection

import pytest

from firstcommit import markup, reactions
from firstcommit.reactions import ReactionRule
from firstcommit.records import Command


def said(line: str, status: int = 0, kinds: Collection[str] = (), repository: bool = True, rules: tuple[ReactionRule, ...] = reactions.RULES) -> str | None:
    """
    Give the mood and text of the rule that speaks for one typed line, or None.

    Parameters
    ----------
    line : str
        The typed line.
    status : int
        Its exit status.
    kinds : Collection[str]
        The event kinds of what changed.
    repository : bool
        Whether the player's folder holds a repository after it.
    rules : tuple[ReactionRule, ...]
        The rules to read, the shared ones by default.

    Returns
    -------
    str | None
        ``"<mood>: <text>"``, or None when no rule fits.
    """
    command: Command = {"line": line, "status": status}
    rule = reactions.react(command, kinds, repository, rules)
    return None if rule is None else f"{rule.mood}: {rule.text}"


QUIET = ReactionRule(line=r"git status\b", mood="info", text="Quiet.")
LOUD = ReactionRule(line=r"git status\b", mood="warn", text="Loud.")


def test_the_first_rule_that_fits_speaks_for_the_line() -> None:
    assert said("git status", rules=(QUIET, LOUD)) == "info: Quiet."
    assert said("git status", rules=(LOUD, QUIET)) == "warn: Loud."


def test_a_line_no_rule_fits_gets_no_reaction() -> None:
    assert said("git status", rules=()) is None
    assert said("git log", rules=(QUIET,)) is None


def test_a_rule_reads_the_line_from_its_start_with_spaces_made_single() -> None:
    assert said("   git    status  --short", rules=(QUIET,)) == "info: Quiet."
    assert said("echo git status", rules=(QUIET,)) is None
    assert said("git statusx", rules=(QUIET,)) is None


@pytest.mark.parametrize(
    ("outcome", "fits"),
    [("any", {0, 1, 127, 128, 130}), ("ok", {0}), ("failed", {1, 127, 128, 130}), ("unknown-command", {127})],
)
def test_a_rule_may_ask_how_the_line_ended(outcome: reactions.Outcome, fits: set[int]) -> None:
    rule = ReactionRule(line=r"x", mood="info", text="Seen.", outcome=outcome)
    assert {status for status in (0, 1, 127, 128, 130) if said("x", status, rules=(rule,))} == fits


def test_a_rule_may_ask_for_one_kind_of_change() -> None:
    rule = ReactionRule(line=r"git add\b", mood="ok", text="Staged.", event="file-staged")
    assert said("git add a", kinds={"file-created", "file-staged"}, rules=(rule,)) == "ok: Staged."
    assert said("git add a", kinds={"file-created"}, rules=(rule,)) is None


def test_a_rule_may_ask_whether_a_repository_is_there_after_the_line() -> None:
    there = ReactionRule(line=r"ls\b", mood="info", text="There.", repository=True)
    gone = ReactionRule(line=r"ls\b", mood="info", text="Gone.", repository=False)
    assert said("ls", repository=True, rules=(gone, there)) == "info: There."
    assert said("ls", repository=False, rules=(there, gone)) == "info: Gone."


def test_every_shared_rule_is_a_valid_pattern_with_text_the_page_can_show() -> None:
    for rule in reactions.RULES:
        re.compile(rule.line)
        assert rule.text.strip() and markup.parse(rule.text), rule


def test_a_new_repository_is_greeted_and_a_second_init_is_called_safe() -> None:
    assert said("git init", kinds={"repository-created"}) == f"ok: {reactions.NEW_REPOSITORY}"
    assert said("git init", repository=True) == f"info: {reactions.INIT_AGAIN}"


def test_a_git_command_that_fails_where_no_repository_is_says_so() -> None:
    for line in ("git status", "git add notes.txt", "git log --oneline"):
        assert said(line, 128, repository=False) == f"err: {reactions.NO_REPOSITORY}", line
    assert said("git status", 0, repository=False) != f"err: {reactions.NO_REPOSITORY}"


def test_deleting_the_repository_is_a_warning_whatever_did_it() -> None:
    assert said("rm -rf .git", kinds={"repository-removed"}, repository=False) == f"warn: {reactions.REPOSITORY_GONE}"


def test_staging_and_committing_are_told_apart_from_lines_that_changed_nothing() -> None:
    assert said("git add notes.txt", kinds={"file-staged"}) == f"ok: {reactions.STAGED}"
    assert said("git add notes.txt") == f"info: {reactions.NOTHING_NEW}"
    assert said("git add") == f"info: {reactions.ADD_WHAT}"
    assert said("git add nope.txt", 128) == f"err: {reactions.NOT_STAGED}"
    assert said('git commit -m "Add notes"', kinds={"commit-created", "file-staged"}) == f"ok: {reactions.COMMITTED}"
    assert said('git commit -m "Add notes"', 1) == f"err: {reactions.NOT_COMMITTED}"


def test_unstaging_is_told_apart_from_restoring_the_working_folder() -> None:
    assert said("git restore --staged notes.txt", kinds={"file-unstaged"}) == f"ok: {reactions.UNSTAGED}"
    assert said("git restore notes.txt", kinds={"file-changed"}) == f"warn: {reactions.RESTORED}"


def test_ls_explains_hidden_files_once_a_repository_is_there() -> None:
    for line in ("ls -a", "ls -la", "ls -al", "ls --all", "ls -l -a ."):
        assert said(line) == f"info: {reactions.HIDDEN_GIT}", line
    assert said("ls") == f"info: {reactions.LS_IN_REPOSITORY}"
    assert said("ls", repository=False) == f"info: {reactions.LS_NO_REPOSITORY}"


def test_a_mistyped_git_gets_a_nudge_and_any_other_unknown_command_a_plain_error() -> None:
    assert said("gti status", 127) == f"info: {reactions.DID_YOU_MEAN_GIT}"
    assert said("lss", 127) == f"err: {reactions.UNKNOWN_COMMAND}"


def test_files_made_or_changed_by_the_shell_are_explained_in_a_repository() -> None:
    assert said("touch notes.txt", kinds={"file-created"}) == f"info: {reactions.NEW_FILE}"
    assert said('echo "more" >> notes.txt', kinds={"file-changed"}) == f"warn: {reactions.CHANGED_FILE}"
    assert said("touch notes.txt", kinds={"file-created"}, repository=False) is None


def test_reading_the_status_or_the_history_is_explained() -> None:
    assert said("git status --short") == f"info: {reactions.STATUS}"
    assert said("git log --oneline") == f"info: {reactions.LOG}"


def test_a_typed_line_matches_a_pattern_from_its_start_and_an_outcome() -> None:
    failed: Command = {"line": "  git   status ", "status": 128}
    assert reactions.matches(failed, r"git status\b", "any")
    assert reactions.matches(failed, r"git status\b", "failed")
    assert not reactions.matches(failed, r"git status\b", "ok")
    assert not reactions.matches(failed, r"status\b", "any")
