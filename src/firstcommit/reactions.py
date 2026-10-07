"""
What Rama says about a line the player typed: one shared set of rules, written as data, plus a level's own.

A rule reads three things: the typed line, how it ended (its exit status) and what changed in the
player's repository (the event kinds of `firstcommit.changes`, and whether a repository is there
afterwards). The first rule that fits a line speaks for it; the game puts a level's rules before
the shared `RULES`, so a level can say something more precise. A line no rule fits gets no
reaction. Lines read in one observation share that observation's changes.

The texts follow AUTHORING.md: they never quote git's messages, and they scope what they claim
to the command the rule matches.
"""

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Literal

from firstcommit.records import Command, Mood

Outcome = Literal["any", "ok", "failed", "unknown-command"]
"""How a line must have ended: any way, with status 0, with any other status, or with bash's 127 for a command it does not know."""

UNKNOWN_COMMAND_STATUS = 127
NEEDS_REPOSITORY = r"git (status|add|commit|log|restore|branch|switch|push|pull|fetch|remote)\b"
"""The git commands a beginner meets that fail in a folder without a repository."""


@dataclass(frozen=True)
class ReactionRule:
    r"""
    One thing Rama may say about a typed line, and when.

    ``line`` is a regular expression matched at the start of the typed line, its runs of spaces
    made single (so ``git status\b`` fits ``git  status --short``). ``outcome`` is how the
    line must have ended. ``event`` is an event kind that must be among the changes, or empty
    for none. ``repository`` says whether the player's folder must hold a repository afterwards
    (True or False), or None for either. ``text`` is markup, as every game text.
    """

    line: str
    mood: Mood
    text: str
    outcome: Outcome = "any"
    event: str = ""
    repository: bool | None = None


NEW_REPOSITORY = "A new repository: Git made the hidden `.git` folder, where it keeps this project's history. `ls -a` shows it."
INIT_AGAIN = "This folder already was a repository. Running `git init` in it again is safe: it overwrites nothing."
REPOSITORY_GONE = "The repository is gone, and its history with it: Git kept all of it in the `.git` folder."
NO_REPOSITORY = "Git found no repository here. Git works only in a folder it knows, and `git init` makes this folder one."
STATUS = "`git status` lists what is staged for your next commit, what changed in the working folder since, and the files Git does not track yet."
UNSTAGED = "Out of the staging area: your next commit will not take that change."
RESTORED = "`git restore` replaced the file in the working folder: the changes it had there that you had not staged are gone."
STAGED = "Staged: your next commit will take the file as it is now. Change it again, and you stage it again."
NOTHING_NEW = "Nothing new to stage: the staging area already matched."
ADD_WHAT = "`git add` needs to know what to stage: a file name, or `.` for everything in this folder and the folders inside it."
NOT_STAGED = "Nothing was staged. Read Git's message: a name it does not find is the usual cause. `ls` lists the folder, and Tab completes names."
COMMITTED = "Committed: a new closed box in your repository, with its own hash and your message. `git log --oneline` lists it."
NOT_COMMITTED = "No commit was made. Read Git's message: an empty staging area, or no name and email set yet, are the usual causes."
LOG = "Your history, newest commit first. Each commit records its author, its date and its message, and Git names it by its hash."
HIDDEN_GIT = "See `.git`? That hidden folder is the repository: Git keeps the whole history in it. A plain `ls` hides names that start with a dot."
LS_IN_REPOSITORY = "`ls` lists the working folder. To see which of these files Git tracks, and which changed, ask `git status`."
LS_NO_REPOSITORY = "Plain files in a plain folder: Git keeps no history of them yet."
DID_YOU_MEAN_GIT = "Did you mean `git`? It happens to every crew."
UNKNOWN_COMMAND = "The shell knows no command by that name. Check its spelling: Tab completes command names too."
NEW_FILE = "A new file in the working folder. Git does not track it yet: `git status` lists it as untracked until you `git add` it."
CHANGED_FILE = "You changed a file in the working folder. What is staged stays as it was until you `git add` the file again."

RULES: tuple[ReactionRule, ...] = (
    ReactionRule(line=r"", mood="warn", text=REPOSITORY_GONE, event="repository-removed"),
    ReactionRule(line=r"git init\b", mood="ok", text=NEW_REPOSITORY, event="repository-created"),
    ReactionRule(line=r"git init( -\S+)*$", mood="info", text=INIT_AGAIN, outcome="ok", repository=True),
    ReactionRule(line=NEEDS_REPOSITORY, mood="err", text=NO_REPOSITORY, outcome="failed", repository=False),
    ReactionRule(line=r"git status\b", mood="info", text=STATUS, outcome="ok"),
    ReactionRule(line=r"git restore\b.* --staged\b", mood="ok", text=UNSTAGED, event="file-unstaged"),
    ReactionRule(line=r"git restore\b", mood="warn", text=RESTORED, event="file-changed"),
    ReactionRule(line=r"git add$", mood="info", text=ADD_WHAT),
    ReactionRule(line=r"git add\b", mood="ok", text=STAGED, event="file-staged"),
    ReactionRule(line=r"git add\b", mood="info", text=NOTHING_NEW, outcome="ok"),
    ReactionRule(line=r"git add\b", mood="err", text=NOT_STAGED, outcome="failed", repository=True),
    ReactionRule(line=r"git commit\b", mood="ok", text=COMMITTED, event="commit-created"),
    ReactionRule(line=r"git commit\b", mood="err", text=NOT_COMMITTED, outcome="failed", repository=True),
    ReactionRule(line=r"git log\b", mood="info", text=LOG, outcome="ok"),
    ReactionRule(line=r"ls( \S+)* (-[^-\s]*a\S*|--all)( |$)", mood="info", text=HIDDEN_GIT, outcome="ok", repository=True),
    ReactionRule(line=r"ls\b", mood="info", text=LS_IN_REPOSITORY, outcome="ok", repository=True),
    ReactionRule(line=r"ls\b", mood="info", text=LS_NO_REPOSITORY, outcome="ok", repository=False),
    ReactionRule(line=r"(gti|gi|gt|got|tig|igt)\b", mood="info", text=DID_YOU_MEAN_GIT, outcome="unknown-command"),
    ReactionRule(line=r"", mood="err", text=UNKNOWN_COMMAND, outcome="unknown-command"),
    ReactionRule(line=r"(echo|printf|touch|cat|cp)\b", mood="info", text=NEW_FILE, event="file-created", repository=True),
    ReactionRule(line=r"(echo|printf|cat|sed)\b", mood="warn", text=CHANGED_FILE, event="file-changed", repository=True),
)
"""The rules every level shares, in the order they are tried."""


def react(command: Command, kinds: Collection[str], repository: bool, rules: Sequence[ReactionRule]) -> ReactionRule | None:
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
    rules : Sequence[ReactionRule]
        The rules to try, in order: a level's own first, then `RULES`.

    Returns
    -------
    ReactionRule | None
        The first rule that fits, or None.
    """
    return next((rule for rule in rules if _fits(rule, command, kinds, repository)), None)


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
    return re.match(pattern, " ".join(command["line"].split())) is not None and ended[outcome]


def _fits(rule: ReactionRule, command: Command, kinds: Collection[str], repository: bool) -> bool:
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

    Returns
    -------
    bool
        True when the line, its outcome, the change and the repository all fit.
    """
    return (
        matches(command, rule.line, rule.outcome)
        and (not rule.event or rule.event in kinds)
        and (rule.repository is None or rule.repository == repository)
    )
