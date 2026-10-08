"""
What Rama says about a line the player typed: one shared set of rules, written as data, plus a level's own.

A rule reads three things: the typed line, how it ended (its exit status) and what changed in the
player's repository (the event kinds of `firstcommit.changes`, whether a repository is there
afterwards, and whether anything is staged then). The first rule that fits a line speaks for it; the game puts a level's rules before
the shared `RULES`, so a level can say something more precise. A line no rule fits gets no
reaction. Lines read in one observation share that observation's changes.

The texts follow AUTHORING.md: they never quote git's messages, and they scope what they claim
to the command the rule matches. Their Spanish is `firstcommit.reactions_es`, read into `SPANISH`.
"""

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Literal

from firstcommit import reactions_es
from firstcommit.records import Command, Mood

Outcome = Literal["any", "ok", "failed", "unknown-command"]
"""How a line must have ended: any way, with status 0, with any other status, or with bash's 127 for a command it does not know."""

UNKNOWN_COMMAND_STATUS = 127
NEEDS_REPOSITORY = r"git (status|add|commit|log|restore|branch|switch|push|pull|fetch|remote)\b"
"""The git commands a beginner meets that fail in a folder without a repository."""
GIT_COMMANDS: tuple[str, ...] = (
    "add", "am", "annotate", "apply", "archive", "bisect", "blame", "branch", "bugreport", "bundle",
    "cat-file", "check-attr", "check-ignore", "check-mailmap", "check-ref-format", "checkout",
    "checkout--worker", "checkout-index", "cherry", "cherry-pick", "clean", "clone", "column",
    "commit", "commit-graph", "commit-tree", "config", "count-objects", "credential",
    "credential-cache", "credential-cache--daemon", "credential-store", "daemon", "describe",
    "diagnose", "diff", "diff-files", "diff-index", "diff-tree", "difftool", "difftool--helper",
    "fast-export", "fast-import", "fetch", "fetch-pack", "filter-branch", "fmt-merge-msg",
    "for-each-ref", "for-each-repo", "format-patch", "fsck", "fsck-objects", "fsmonitor--daemon",
    "gc", "get-tar-commit-id", "grep", "hash-object", "help", "hook", "http-backend", "http-fetch",
    "http-push", "imap-send", "index-pack", "init", "init-db", "instaweb", "interpret-trailers",
    "log", "ls-files", "ls-remote", "ls-tree", "mailinfo", "mailsplit", "maintenance", "merge",
    "merge-base", "merge-file", "merge-index", "merge-octopus", "merge-one-file", "merge-ours",
    "merge-recursive", "merge-recursive-ours", "merge-recursive-theirs", "merge-resolve",
    "merge-subtree", "merge-tree", "mergetool", "mktag", "mktree", "multi-pack-index", "mv",
    "name-rev", "notes", "pack-objects", "pack-redundant", "pack-refs", "patch-id", "pickaxe",
    "prune", "prune-packed", "pull", "push", "quiltimport", "range-diff", "read-tree", "rebase",
    "receive-pack", "reflog", "remote", "remote-ext", "remote-fd", "remote-ftp", "remote-ftps",
    "remote-http", "remote-https", "repack", "replace", "request-pull", "rerere", "reset",
    "restore", "rev-list", "rev-parse", "revert", "rm", "send-pack", "sh-i18n--envsubst", "shell",
    "shortlog", "show", "show-branch", "show-index", "show-ref", "sparse-checkout", "stage",
    "stash", "status", "stripspace", "submodule", "submodule--helper", "subtree", "switch",
    "symbolic-ref", "tag", "unpack-file", "unpack-objects", "update-index", "update-ref",
    "update-server-info", "upload-archive", "upload-archive--writer", "upload-pack", "var",
    "verify-commit", "verify-pack", "verify-tag", "version", "web--browse", "whatchanged",
    "worktree", "write-tree",
)
"""The commands git 2.43 knows, as ``git --list-cmds=main`` lists them in the game's image."""
OPTIONAL_COMMANDS: tuple[str, ...] = (
    "archimport", "citool", "cvsexportcommit", "cvsimport", "cvsserver", "gui", "gui--askpass", "lfs", "p4", "send-email", "svn",
)
"""Commands a machine may have besides: git's own that git(1) lists but Ubuntu installs apart (git-gui, git-svn, git-email, git-cvs...), and git-lfs."""
MISSPELLED_COMMAND = rf"git (?!(?:{'|'.join(re.escape(name) for name in GIT_COMMANDS + OPTIONAL_COMMANDS)})(?: |$))[a-z][\w-]*(?: |$)"
"""A ``git`` line whose first word after ``git`` is a name git does not know (not an option)."""
BARE_COMMIT = r"git commit(?!.* (?:-[a-zA-Z]*[mFCc]|--message|--file|--reuse-message|--reedit-message|--no-edit|--amend|--fixup|--squash|--allow-empty-message))( |$)"
"""A ``git commit`` that brings no message of its own, so git asks the editor for one."""
LIST_HIDDEN = r"ls( \S+)* (-[^-\s]*[aA]\S*|--all|--almost-all)( |$)"
"""An ``ls`` that lists hidden names too (``-a``, ``-A``, ``-la``...), such as ``.git``."""


@dataclass(frozen=True)
class ReactionRule:
    r"""
    One thing Rama may say about a typed line, and when.

    ``line`` is a regular expression matched at the start of the typed line, its runs of spaces
    made single (so ``git status\b`` fits ``git  status --short``). ``outcome`` is how the
    line must have ended. ``event`` is an event kind that must be among the changes, or empty
    for none. ``repository`` says whether the player's folder must hold a repository afterwards
    (True or False), or None for either; ``staged``, likewise, whether its staging area must then
    differ from the last commit. ``text`` is markup, as every game text.
    """

    line: str
    mood: Mood
    text: str
    outcome: Outcome = "any"
    event: str = ""
    repository: bool | None = None
    staged: bool | None = None


NEW_REPOSITORY = "A new repository: Git made the hidden `.git` folder, where it keeps this project's history. `ls -a` shows it."
NOT_A_GIT_COMMAND = "Git knows no command by that name. Check its spelling: `git help -a` lists every command Git has."
INIT_AGAIN = "This folder already was a repository. Running `git init` in it again is safe: it overwrites nothing."
REPOSITORY_GONE = "The repository is gone, and its history with it: Git kept all of it in the `.git` folder."
NO_REPOSITORY = "Git found no repository here. This command works only inside a repository, and `git init` makes this folder one."
STATUS = "`git status` lists what is staged for your next commit, what changed in the working folder since, and the files Git does not track yet."
UNSTAGED = "Out of the staging area: your next commit will not take that change."
RESTORED = "`git restore` replaced the file in the working folder: the changes it had there that you had not staged are gone."
STAGED = "Staged: your next commit will take the file as it is now. Change it again, and you stage it again."
NOTHING_NEW = "Nothing new to stage: the staging area already matched."
ADD_WHAT = "`git add` needs to know what to stage: a file name, or `.` for everything in this folder and the folders inside it."
NOT_STAGED = "Nothing was staged. Read Git's message: a name it does not find is the usual cause. `ls` lists the folder, and Tab completes names."
COMMITTED = "Committed: a new capsule sealed in your vault, with its own hash and your message. `git log --oneline` lists it."
NO_MESSAGE = (
    "No commit was made: every commit needs a message, and in the game no editor opens to write one. "
    'Give it on the line: `git commit -m "Add the map"`.'
)
NOT_COMMITTED = "No commit was made. Read Git's message: nothing new in the staging area, or no name and email set yet, are the usual causes."
LOG = "Your history, newest commit first. Each commit records its author, its date and its message, and Git names it by its hash."
HIDDEN_GIT = "See `.git`? That hidden folder is the repository: Git keeps the whole history in it. A plain `ls` hides names that start with a dot."
LS_IN_REPOSITORY = "`ls` lists the working folder. To see which of these files changed, and which Git does not track yet, ask `git status`."
LS_NO_REPOSITORY = "Plain files in a plain folder: Git keeps no history of them yet."
DID_YOU_MEAN_GIT = "Did you mean `git`? It happens to every crew."
UNKNOWN_COMMAND = "The shell knows no command by that name. Check its spelling: Tab completes command names too."
NEW_FILE = "A new file in the working folder. Git does not track it yet: `git status` lists it as untracked until you `git add` it."
CHANGED_FILE = "You changed a file in the working folder. What is staged stays as it was until you `git add` the file again."

RULES: tuple[ReactionRule, ...] = (
    ReactionRule(line=r"", mood="warn", text=REPOSITORY_GONE, event="repository-removed"),
    ReactionRule(line=r"git init\b", mood="ok", text=NEW_REPOSITORY, event="repository-created"),
    ReactionRule(line=r"git init( -\S+)*$", mood="info", text=INIT_AGAIN, outcome="ok", repository=True),
    ReactionRule(line=MISSPELLED_COMMAND, mood="err", text=NOT_A_GIT_COMMAND, outcome="failed"),
    ReactionRule(line=NEEDS_REPOSITORY, mood="err", text=NO_REPOSITORY, outcome="failed", repository=False),
    ReactionRule(line=r"git status\b", mood="info", text=STATUS, outcome="ok"),
    ReactionRule(line=r"git (restore\b.* --staged|rm\b.* --cached)\b", mood="ok", text=UNSTAGED, event="file-unstaged"),
    ReactionRule(line=r"git restore\b", mood="warn", text=RESTORED, event="file-changed"),
    ReactionRule(line=r"git add$", mood="info", text=ADD_WHAT),
    ReactionRule(line=r"git add\b", mood="ok", text=STAGED, event="file-staged"),
    ReactionRule(line=r"git add\b", mood="info", text=NOTHING_NEW, outcome="ok"),
    ReactionRule(line=r"git add\b", mood="err", text=NOT_STAGED, outcome="failed", repository=True),
    ReactionRule(line=r"git commit\b", mood="ok", text=COMMITTED, event="commit-created"),
    ReactionRule(line=BARE_COMMIT, mood="err", text=NO_MESSAGE, outcome="failed", repository=True, staged=True),
    ReactionRule(line=r"git commit\b", mood="err", text=NOT_COMMITTED, outcome="failed", repository=True),
    ReactionRule(line=r"git log\b", mood="info", text=LOG, outcome="ok"),
    ReactionRule(line=LIST_HIDDEN, mood="info", text=HIDDEN_GIT, outcome="ok", repository=True),
    ReactionRule(line=r"ls\b", mood="info", text=LS_IN_REPOSITORY, outcome="ok", repository=True),
    ReactionRule(line=r"ls\b", mood="info", text=LS_NO_REPOSITORY, outcome="ok", repository=False),
    ReactionRule(line=r"(gti|gi|gt|got|tig|igt)\b", mood="info", text=DID_YOU_MEAN_GIT, outcome="unknown-command"),
    ReactionRule(line=r"", mood="err", text=UNKNOWN_COMMAND, outcome="unknown-command"),
    ReactionRule(line=r"(echo|printf|touch|cat|cp)\b", mood="info", text=NEW_FILE, event="file-created", repository=True),
    ReactionRule(line=r"(echo|printf|cat|sed)\b", mood="warn", text=CHANGED_FILE, event="file-changed", repository=True),
)
"""The rules every level shares, in the order they are tried."""

SPANISH: dict[str, str] = {globals()[name]: text for name, text in vars(reactions_es).items() if name.isupper()}
"""Each shared text in Spanish, by its English text: the constant of `firstcommit.reactions_es` with the same name."""


def react(command: Command, kinds: Collection[str], repository: bool, staged: bool, rules: Sequence[ReactionRule]) -> ReactionRule | None:
    """
    Find the rule that speaks for one typed line.

    Parameters
    ----------
    command : Command
        The typed line and its exit status.
    kinds : Collection[str]
        The kinds of the events that tell what changed (`firstcommit.changes`).
    repository : bool
        Whether the player's folder holds a repository afterwards.
    staged : bool
        Whether its staging area then differs from the last commit (`firstcommit.repomap.staged`).
    rules : Sequence[ReactionRule]
        The rules to try, in order: a level's own first, then `RULES`.

    Returns
    -------
    ReactionRule | None
        The first rule that fits, or None.
    """
    return next((rule for rule in rules if _fits(rule, command, kinds, repository, staged)), None)


GLOBAL_OPTIONS = re.compile(
    r"(?:^|(?<=[;&|] ))git"
    # git's options before a subcommand: those that take a separate value, then flags (with an
    # optional =value), up to a word that is not an option.
    r"(?: (?:-[Cc] \S+|--(?:git-dir|work-tree|namespace|config-env) \S+|-[pP]|--[a-z][a-z-]*(?:=\S+)?))+"
    r"(?= [^-\s])"
)
"""Git's options typed before a subcommand, which `plain` leaves out."""


def matches(command: Command, pattern: str, outcome: Outcome) -> bool:
    """
    Tell whether a typed line starts as a pattern says and ended as asked.

    Parameters
    ----------
    command : Command
        The typed line and its exit status.
    pattern : str
        A regular expression matched at the start of the line, its runs of spaces made single.
    outcome : Outcome
        How the line must have ended.

    Returns
    -------
    bool
        True when both fit.
    """
    status = command["status"]
    ended = {
        "any": True,
        "ok": status == 0,
        "failed": status != 0,
        "unknown-command": status == UNKNOWN_COMMAND_STATUS,
    }
    return re.match(pattern, plain(command["line"])) is not None and ended[outcome]


def plain(line: str) -> str:
    """
    Give a typed line as patterns read it: runs of spaces made single, git's options before a subcommand left out.

    Parameters
    ----------
    line : str
        The line as typed.

    Returns
    -------
    str
        The line with each ``git`` that starts a command (at the start, or after ``;``, ``&`` or
        ``|``) followed straight by its subcommand: ``git --no-pager log`` and ``git -C . log``
        read as ``git log``. Options with no subcommand after them (``git --version``) stay.
    """
    return GLOBAL_OPTIONS.sub("git", " ".join(line.split()))


def _fits(rule: ReactionRule, command: Command, kinds: Collection[str], repository: bool, staged: bool) -> bool:
    """
    Tell whether a rule fits a typed line.

    Parameters
    ----------
    rule : ReactionRule
        The rule.
    command : Command
        The typed line and its exit status.
    kinds : Collection[str]
        The event kinds of what changed.
    repository : bool
        Whether a repository is there afterwards.
    staged : bool
        Whether anything is staged afterwards.

    Returns
    -------
    bool
        True when the line, its outcome, the change, the repository and the staging area all fit.
    """
    return (
        matches(command, rule.line, rule.outcome)
        and (not rule.event or rule.event in kinds)
        and (rule.repository is None or rule.repository == repository)
        and (rule.staged is None or rule.staged == staged)
    )
