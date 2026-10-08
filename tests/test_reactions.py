import re
import subprocess
from collections.abc import Collection

import pytest

from firstcommit import markup, reactions, runner
from firstcommit.levels import mothership_halves
from firstcommit.reactions import ReactionRule
from firstcommit.records import Command


def said(
    line: str,
    status: int = 0,
    kinds: Collection[str] = (),
    repository: bool = True,
    rules: tuple[ReactionRule, ...] = reactions.RULES,
    staged: bool = False,
    remote: bool = True,
) -> str | None:
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
    staged : bool
        Whether the staging area differs from the last commit after it.
    remote : bool
        Whether the repository names a remote after it.

    Returns
    -------
    str | None
        ``"<mood>: <text>"``, or None when no rule fits.
    """
    command: Command = {"line": line, "status": status}
    rule = reactions.react(command, kinds, repository, staged, rules, remote=remote)
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
    assert said("git rm --cached notes.txt", kinds={"file-unstaged"}) == f"ok: {reactions.UNSTAGED}"
    assert said("git restore notes.txt", kinds={"file-changed"}) == f"warn: {reactions.RESTORED}"


def test_ls_explains_hidden_files_once_a_repository_is_there() -> None:
    for line in ("ls -a", "ls -la", "ls -al", "ls --all", "ls -l -a .", "ls -A", "ls --almost-all"):
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


@pytest.mark.parametrize("line", ["git log oxygen.cfg", "git log -- oxygen.cfg", "git log -p oxygen.cfg", "git log --oneline notes/day1.txt"])
def test_git_log_on_a_file_says_it_lists_only_the_commits_that_changed_it(line: str) -> None:
    assert said(line) == f"info: {reactions.LOG_FILE}"


@pytest.mark.parametrize("line", ["git log", "git log --oneline", "git log main", "git log origin/main", "git log HEAD~3..HEAD"])
def test_git_log_without_a_file_keeps_the_history_reaction(line: str) -> None:
    assert said(line) == f"info: {reactions.LOG}"


def test_a_typed_line_matches_a_pattern_from_its_start_and_an_outcome() -> None:
    failed: Command = {"line": "  git   status ", "status": 128}
    assert reactions.matches(failed, r"git status\b", "any")
    assert reactions.matches(failed, r"git status\b", "failed")
    assert not reactions.matches(failed, r"git status\b", "ok")
    assert not reactions.matches(failed, r"status\b", "any")


@pytest.mark.parametrize(
    "line",
    [
        "git --no-pager log --oneline",
        "git -C . log",
        "git -C project log",
        "git -c color.ui=never log",
        "git --git-dir=.git log",
        "git -p log",
        "cd project && git --no-pager log",
    ],
)
def test_options_before_the_subcommand_do_not_hide_it(line: str) -> None:
    assert reactions.matches({"line": line, "status": 0}, r"(cd project && )?git log\b", "ok")


@pytest.mark.parametrize("line", ["git --version", "git --help", "git --no-pager"])
def test_a_line_with_options_and_no_subcommand_keeps_them(line: str) -> None:
    assert reactions.matches({"line": line, "status": 0}, line, "ok")
    assert not reactions.matches({"line": line, "status": 0}, r"git$", "ok")


@pytest.mark.parametrize("line", ["git ad map.txt", "git stauts", "git comit -m 'Add the map'", "git int"])
def test_a_misspelled_git_command_points_at_its_spelling_and_the_list_of_commands(line: str) -> None:
    assert said(line, 1) == f"err: {reactions.NOT_A_GIT_COMMAND}"
    assert said(line, 1, repository=False) == f"err: {reactions.NOT_A_GIT_COMMAND}"


@pytest.mark.parametrize("name", reactions.GIT_COMMANDS + reactions.OPTIONAL_COMMANDS)
def test_a_real_git_command_that_fails_is_never_called_misspelled(name: str) -> None:
    for status in (1, 128, 129):
        assert said(f"git {name} --oops", status) != f"err: {reactions.NOT_A_GIT_COMMAND}"
        assert said(f"git {name}", status, repository=False) != f"err: {reactions.NOT_A_GIT_COMMAND}"


def test_git_alone_or_with_an_option_first_is_not_a_misspelled_command() -> None:
    for line in ("git", "git --versoin", "git -C .. status"):
        assert said(line, 1) != f"err: {reactions.NOT_A_GIT_COMMAND}"


def test_the_known_git_commands_include_the_ones_beginners_type() -> None:
    assert {"add", "commit", "status", "log", "init", "restore", "switch", "push", "pull", "help", "rm", "diff"} <= set(reactions.GIT_COMMANDS)


def test_every_command_this_machines_git_knows_is_in_the_known_list() -> None:
    listed = subprocess.run(["git", "--list-cmds=main"], capture_output=True, text=True, check=True).stdout.split()
    assert set(listed) <= {*reactions.GIT_COMMANDS, *reactions.OPTIONAL_COMMANDS}


def test_a_rule_may_ask_whether_something_is_staged_after_the_line() -> None:
    rule = ReactionRule(line=r"git commit\b", mood="err", text="Staged.", staged=True)
    assert said("git commit", 1, rules=(rule,), staged=True) == "err: Staged."
    assert said("git commit", 1, rules=(rule,), staged=False) is None


def test_a_bare_commit_that_stopped_with_changes_staged_teaches_the_message_option() -> None:
    assert said("git commit", 1, staged=True) == f"err: {reactions.NO_MESSAGE}"
    assert said("git commit -a", 1, staged=True) == f"err: {reactions.NO_MESSAGE}"


@pytest.mark.parametrize("line", ['git commit -m "Add the map"', 'git commit -am "Add the map"', "git commit --no-edit", "git commit --amend", "git commit -F notes.txt"])
def test_a_commit_that_brings_its_own_message_never_gets_the_message_lesson(line: str) -> None:
    assert said(line, 128, staged=True) == f"err: {reactions.NOT_COMMITTED}"


def test_a_bare_commit_with_nothing_staged_is_the_usual_failed_commit() -> None:
    assert said("git commit", 1, staged=False) == f"err: {reactions.NOT_COMMITTED}"


def test_a_failed_commit_never_blames_a_missing_name_and_email() -> None:
    assert "email" not in reactions.NOT_COMMITTED and "correo" not in reactions.SPANISH[reactions.NOT_COMMITTED]


@pytest.mark.parametrize(("line", "status"), [("git push", 128), ("git push -u origin main", 1)])
def test_a_push_from_a_repository_with_no_remote_says_to_name_one_first(line: str, status: int) -> None:
    assert said(line, status, remote=False) == f"err: {reactions.NO_REMOTE}"
    assert said(line, status, remote=True) != f"err: {reactions.NO_REMOTE}"


@pytest.mark.parametrize("line", ["git fetch", "git fetch origin", "git -C . fetch --all"])
def test_a_fetch_that_brought_commits_says_your_branches_did_not_move(line: str) -> None:
    assert said(line, kinds={"remote-updated"}) == f"ok: {reactions.FETCHED}"
    assert said(line) == f"info: {reactions.FETCHED_NOTHING}"


def test_a_pull_says_whether_it_fast_forwarded_or_made_a_merge_commit() -> None:
    assert said("git pull", kinds={"remote-updated", "branch-moved"}) == f"ok: {reactions.PULLED_FAST_FORWARD}"
    assert said("git pull origin main", kinds={"remote-updated", "merge-commit-created"}) == f"ok: {reactions.PULLED_MERGE}"
    assert said("git pull") == f"info: {reactions.PULLED_NOTHING}"


@pytest.mark.parametrize("line", ["git fetch", "git pull"])
def test_a_failed_fetch_or_pull_gets_no_pleased_reaction(line: str) -> None:
    assert said(line, 1, kinds={"remote-updated"}) is None


def test_a_levels_own_pull_reaction_comes_before_the_shared_one() -> None:
    rules = (*runner.catalogue()["mothership-halves"].reactions, *reactions.RULES)
    assert said("git pull", kinds={"remote-updated", "branch-moved"}, rules=rules) == f"ok: {mothership_halves.TWO_HALVES}"
