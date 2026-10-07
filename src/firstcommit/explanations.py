"""
Why a playground press turned out as it did, in a sentence or two, with the fix next to it.

The explanation is chosen from facts, never from git's words (AUTHORING section 1, rule 4): the
exit status, the person's repository before and after the press, GitHub before it, and what
the person's folder and configuration held before it (`firstcommit.records.Facts`). The order
of the rules was set by real git 2.43: a missing remote or upstream comes first, then the
identity (git checks it before what is staged, though after unmerged files), then the two
histories. When no rule proves a
cause, ``E0`` adds nothing to git's own message: a wrong explanation is worse than none. Most
presses that work earn no explanation, since the figure shows what they did; a few successes
surprise beginners and get one anyway.

Each rule and sentence is checked against a recorded press of real git in the playground's
mistakes table (docs/drafts/playground-errors.md), by its tag. File names come only from the
playground's buttons and are written with `firstcommit.markup.code`.
"""

from collections.abc import Collection
from dataclasses import dataclass
from typing import TypedDict

from firstcommit.markup import code
from firstcommit.records import ConfigFacts, Facts, FolderFacts, Press, Snapshot
from firstcommit.repomap import conflicted, history, staged, unstaged, untracked

EXPLANATIONS = {
    "E0": "Git refused this command; its own message above says why.",
    "E1": "This folder is not a Git repository yet: it has no `.git` folder, so there is no staging area and no history for this command to use. Fix: press `git init` first.",
    "E2": "This clone's folder does not exist, so there is no repository here for the command to use. If nothing has been cloned yet, clone it first; if the folder was deleted in the terminal, start the playground again.",
    "E3": "`git init` made an empty repository here: a `.git` folder, with no commits yet. Files already in the folder stay as they are, untracked: Git does not track them until you `git add` them.",
    "E4": "This folder already was a repository. Running `git init` again is safe: it keeps every commit, the staging area and your files as they were. You need `git init` once per project.",
    "E5": "There is no file called {file} in this folder, and Git has no copy of one either, so there is nothing to add. Fix: create the file first, or check its name and the folder you are in.",
    "E6": "There is nothing to commit yet: the repository has no commits, the staging area is empty and the working folder has no files to add. Fix: create a file, `git add` it, then commit.",
    "E7": "A commit saves what is in the staging area, and nothing new is staged: your new files are untracked. Fix: `git add` a file, then commit.",
    "E8": "You changed a tracked file (an edit or a deletion), but the change is not staged, and a plain `git commit` saves only what is staged. Fix: `git add` the file, then commit.",
    "E9": "Nothing changed since your last commit: the staging area and the working folder match it, so there is nothing new to save. Fix: change a file and `git add` it first.",
    "E10": 'Every commit, a merge commit included, records who made it: a name and an email, and Git does not have both of yours yet. Fix: set what is missing, once, in the terminal: `git config --global user.name "Your Name"` and `git config --global user.email you@example.com`.',
    "E12": "Nothing changed: the staging area already holds this exact version of {file}. `git add` stores a new copy only after the file changes.",
    "E13": "The commit saved the version of {file} that you staged, not your later edit: that edit is still in the working folder, not staged. To save it too, `git add` it and commit again.",
    "E14": "Git staged the deletion of {file}: the next commit leaves it out of the project. Earlier commits keep their copy.",
    "E15": "You already have a copy: the `project` folder exists, and `git clone` only fills a folder that does not exist yet or is empty. You clone once; after that, `git pull` brings in new commits.",
    "E16": "GitHub's copy has no commits yet, so your clone has none either; Git warns, but the clone worked. Make a first commit and push it.",
    "E17": "Nothing to send: GitHub's `main` already has every commit of your `main`.",
    "E18": "Nothing was sent: `git push` sends commits, and your change is not committed yet, so GitHub's copy stayed as it was. Fix: `git add` and commit it, then push.",
    "E19": "There is nothing to push yet: your `main` has no commits, and a branch only exists from its first commit on. Fix: make a commit, then push.",
    "E20": "This repository has no remote, so `git push` does not know where to send your commits. A clone sets one up, called `origin`; in the terminal you can add it with `git remote add origin ../github/project.git`, then push once with `git push -u origin main`.",
    "E21": "Your `main` is not linked to a branch on GitHub yet (it has no upstream), so a plain `git push` does not know where to push it. Fix: once, in the terminal, `git push -u origin main`; after that a plain `git push` works.",
    "E22": "GitHub's `main` has a commit that your `main` does not contain: someone pushed since you last pulled. A plain `git push` only moves GitHub's branch forward, never drops commits from it, so Git refused and nothing changed. Fix: `git pull`, then push again.",
    "E23": "Your `main` has not moved yet: the merge is paused, so your `main` still lacks GitHub's commit, and GitHub refuses the push. Finish the merge (resolve, `git add`, commit), then push.",
    "E24": "Nothing new: GitHub has no commits that your repository lacks, so `git fetch` had nothing to download.",
    "E25": "This repository has no remote, so `git fetch` has nowhere to fetch from, and it did nothing. In the terminal you can add one with `git remote add origin ../github/project.git`.",
    "E26": "Already up to date: your `main` already has every commit of GitHub's `main`.",
    "E27": "This repository has no remote, so `git pull` has nowhere to pull from. In the terminal you can add one with `git remote add origin ../github/project.git`.",
    "E28": "GitHub's copy has no `main` yet (no commits at all), so there is nothing to pull. Someone has to push a first commit.",
    "E29": "Both sides have new commits: yours, and one on GitHub that you did not have. Git fetched it (see `origin/main`), then stopped, because you must choose how to combine them. Fix: press `git pull --no-rebase`, which merges them. Git's hint shows how to set a default; the game leaves it unset, so you choose each time (the rebase chapter shows the other way).",
    "E30": "Git fetched the new commit (see `origin/main`), then refused to merge it: it changes {file}, which you changed too without committing, and Git does not overwrite work you have not committed. Fix: `git add` and commit your change, then press `git pull --no-rebase`, which merges the two. If both sides changed the same lines, Git then asks you to resolve a conflict.",
    "E31": "Git fetched the new commit (see `origin/main`), then refused to merge it: it adds {file}, and an untracked {file} is already in your working folder, which Git does not overwrite. Fix: rename yours (or delete it if you do not need it), then pull again.",
    "E32": "Git merged GitHub's commits with yours in a merge commit: a commit with two parents that joins the two lines of history. GitHub does not have it yet: push it.",
    "E33": "Both sides changed the same part of {file}, so Git cannot combine them by itself. It wrote both versions into the file, between `<<<<<<<` and `>>>>>>>` markers, and paused the merge. Fix: keep one side (or edit the file in the terminal), `git add` it, then commit; or abort the merge.",
    "E34": "A merge is still in progress. Finish it (resolve, `git add`, commit) or abort it before you pull again.",
    "E35": "The merge is paused: {file} still has a conflict, so Git refuses to commit. Fix: keep one side or edit the file, `git add` it, then commit.",
    "E36": "The commit finished the merge: a merge commit with two parents, your last commit and the one from GitHub.",
    "E37": "Git now counts the conflict in {file} as resolved, with the file as it is. Commit to finish the merge.",
    "E38": "Git counts {file} as resolved, but the file still holds the conflict markers: `git add` takes the file exactly as it is, markers included. Before you commit, remove the marker lines (edit the file in the terminal), then `git add` it again.",
    "E39": "{file} now holds one side only, but Git still lists it as unmerged until you `git add` it.",
    "E40": "The merge is undone: your files and your `main` are back as they were before the pull. The fetched commit stays in your repository (`origin/main` still points to it), so you can merge it later.",
    "E41": "There is no merge in progress (it may have been finished or aborted in the terminal), so there is nothing to abort.",
    "E42": "Git found `.git/index.lock`, the file a Git command holds while it changes the staging area: a commit in the terminal may still be waiting for its message in the editor (`git commit -a` holds the file then), or a command stopped halfway and left it behind. Finish that commit first; if no Git command is running, delete the file in the terminal with `rm .git/index.lock`, then press again.",
    "E43": "Your repository and GitHub's were started separately: they have no commit in common, so Git will not combine them. The usual fix is to start again: rename your folder (from the lab folder: `mv project mine`), clone GitHub's project with `git clone`, copy your files from `mine` into the new `project`, then add, commit and push them.",
    "E44": "GitHub's `main` has a commit that your `main` does not contain, and you have commits GitHub lacks: both sides moved on. A plain `git push` only moves GitHub's branch forward, never drops commits from it, so Git refused and nothing changed. Fix: merge GitHub's commit into yours by pressing `git pull --no-rebase`, then push again.",
    "E45": "Your `main` is not linked to a branch on GitHub yet (it has no upstream), and GitHub has no commits, so there is nothing to pull. Push yours first, once, in the terminal: `git push -u origin main`. After that, `git pull` and `git push` work.",
    "E46": "Your `main` is not linked to a branch on GitHub (it has no upstream), so `git pull` does not know which branch to bring in. Fix, in the terminal: `git pull origin main` brings GitHub's `main` in, then `git push -u origin main` links yours to it, so a plain `git pull` and `git push` work.",
    "E47": "Git merged GitHub's commits with yours in a merge commit, as your `pull.rebase false` setting asks: a commit with two parents that joins the two lines of history. GitHub does not have the merge yet: push it.",
}
"""Each explanation, by tag, in the game's markup; ``{file}`` is the file the outcome is about, written as code."""

FIX_BUTTONS = {
    "E1": "init",
    "E2": "clone",
    "E5": "edit:{file}",
    "E7": "add:{file}",
    "E8": "add:{file}",
    "E13": "add:{file}",
    "E22": "pull",
    "E29": "pull-no-rebase",
    "E30": "add:{file}",
    "E34": "merge-abort",
    "E44": "pull-no-rebase",
}
"""The button an explanation offers as its fix, when one press fixes it and the playground has that button."""
FIX_LINES = {
    "E20": "git remote add origin ../github/project.git",
    "E21": "git push -u origin main",
    "E25": "git remote add origin ../github/project.git",
    "E27": "git remote add origin ../github/project.git",
    "E31": "mv {file} my-{file}",
    "E42": "rm .git/index.lock",
    "E45": "git push -u origin main",
    "E46": "git pull origin main",
}
"""The line an explanation offers to type in the terminal, when its fix is not a button."""
NAME_LINE = 'git config --global user.name "Your Name"'
EMAIL_LINE = "git config --global user.email you@example.com"
REMOTE_BUTTONS = ("push", "fetch", "pull", "pull-no-rebase")
PULLS = ("pull", "pull-no-rebase")


class Explanation(TypedDict):
    """
    What a press earned beyond git's own output.

    ``tag`` names the rule (``"E22"``), or is empty when the press needs no explanation;
    ``file`` is the button file it is about, or empty; ``text`` is the explanation in the
    game's markup, empty with the tag. ``fix`` is the id of a button that fixes it, and
    ``fix_line`` a line to type in the terminal instead; each is empty when there is none.
    """

    tag: str
    file: str
    text: str
    fix: str
    fix_line: str


@dataclass(frozen=True)
class _Found:
    """A rule that applies, by tag, and the button file it is about."""

    tag: str
    file: str = ""


def explain(press: Press, before: Snapshot, after: Snapshot, facts: Facts, buttons: Collection[str]) -> Explanation:
    """
    Explain what a playground press did, from facts about the state it was pressed in.

    Parameters
    ----------
    press : Press
        The press: its button id and exit status.
    before : Snapshot
        The person's repository just before the press.
    after : Snapshot
        The same repository just after it.
    facts : Facts
        GitHub, the person's folder and configuration, just before the press.
    buttons : Collection[str]
        Every button id of the playground: a fix is only ever one of them, and only files they
        name appear in an explanation.

    Returns
    -------
    Explanation
        ``E0`` (git's own message only) when git refused and no rule proves a cause; no tag when
        the press needs nothing beyond the figure.
    """
    files = frozenset(button.partition(":")[2] for button in buttons) - {""}
    found = _diagnose(press["button"], press["status"], before, after, facts, files)
    fix = FIX_BUTTONS.get(found.tag, "").format(file=found.file)
    line = FIX_LINES.get(found.tag, "").format(file=found.file)
    if found.tag == "E10":
        line = EMAIL_LINE if facts["config"]["name"] else NAME_LINE
    text = EXPLANATIONS[found.tag].format(file=code(found.file)) if found.tag else ""
    return {"tag": found.tag, "file": found.file, "text": text, "fix": fix if fix in buttons else "", "fix_line": line}


def _diagnose(button: str, status: int, before: Snapshot, after: Snapshot, facts: Facts, files: frozenset[str]) -> _Found:
    """
    Pick the rule that explains a press: a lock or a missing folder or repository first, then by the kind of button.

    Parameters
    ----------
    button : str
        The button's id.
    status : int
        The command's exit status.
    before : Snapshot
        The person's repository before.
    after : Snapshot
        The same repository after.
    facts : Facts
        The facts before the press.
    files : frozenset[str]
        The files the playground's buttons name.

    Returns
    -------
    _Found
        The rule, or no tag.
    """
    name, _, path = button.partition(":")
    failed = status != 0
    folder, config = facts["folder"], facts["config"]
    if failed and folder["locked"]:
        found = _Found("E42")
    elif failed and name != "clone" and not folder["usable"]:
        found = _Found("E2")
    elif failed and name != "clone" and not before["exists"]:
        found = _Found("E1")
    elif name == "commit":
        found = _commit(failed, before, after, config, files)
    elif name == "add":
        found = _add(failed, before, after, path, folder)
    elif name in REMOTE_BUTTONS:
        found = _remote(name, failed, before, after, facts["github"], config, files)
    else:
        found = _Found(_other(name, failed, before, facts["github"], path), path)
    return found


def _commit(failed: bool, before: Snapshot, after: Snapshot, config: ConfigFacts, files: frozenset[str]) -> _Found:
    """
    Explain a commit: an unresolved conflict first, then the identity, then what was staged.

    Git 2.43 refuses a commit with unmerged files before it looks at the identity, and checks
    the identity before it looks at what is staged.

    Parameters
    ----------
    failed : bool
        Whether git refused.
    before : Snapshot
        The repository before.
    after : Snapshot
        The repository after.
    config : ConfigFacts
        The configuration before.
    files : frozenset[str]
        The files the playground's buttons name.

    Returns
    -------
    _Found
        The rule, or no tag.
    """
    later_edits = [path for path in staged(before) if path in unstaged(after)]
    found = _Found("E0" if failed else "")
    if failed and conflicted(before):
        found = _Found("E35", conflicted(before)[0])
    elif failed and not (config["name"] and config["email"]):
        found = _Found("E10")
    elif failed and not staged(before) and unstaged(before):
        found = _Found("E8", _first_named(unstaged(before), files))
    elif failed and not staged(before) and untracked(before):
        found = _Found("E7", _first_named(untracked(before), files))
    elif failed and not staged(before) and before["head"] is None:
        found = _Found("E6")
    elif failed and not staged(before):
        found = _Found("E9")
    elif not failed and before["operation"] == "merge":
        found = _Found("E36")
    elif not failed and later_edits:
        found = _Found("E13", later_edits[0])
    return found


def _add(failed: bool, before: Snapshot, after: Snapshot, path: str, folder: FolderFacts) -> _Found:
    """
    Explain an add of one file.

    Parameters
    ----------
    failed : bool
        Whether git refused.
    before : Snapshot
        The repository before.
    after : Snapshot
        The repository after.
    path : str
        The file.
    folder : FolderFacts
        The working folder before.

    Returns
    -------
    _Found
        The rule, or no tag.
    """
    entry = next((file for file in before["files"] if file["path"] == path), None)
    known = entry is not None and (entry["index"] is not None or entry["conflicted"])
    missing = folder["kinds"].get(path, "missing") == "missing"
    tag = "E0" if failed else ""
    if failed and missing and not known:
        tag = "E5"
    elif not failed and path in conflicted(before) and path in folder["marked"]:
        tag = "E38"
    elif not failed and path in conflicted(before):
        tag = "E37"
    elif not failed and missing and known:
        tag = "E14"
    elif not failed and before == after:
        tag = "E12"
    return _Found(tag, path)


def _remote(
    name: str, failed: bool, before: Snapshot, after: Snapshot, github: Snapshot | None, config: ConfigFacts, files: frozenset[str]
) -> _Found:
    """
    Explain a push, fetch or pull: first a missing remote or upstream, then the two histories.

    Parameters
    ----------
    name : str
        ``push``, ``fetch``, ``pull`` or ``pull-no-rebase``.
    failed : bool
        Whether git refused.
    before : Snapshot
        The repository before.
    after : Snapshot
        The repository after.
    github : Snapshot | None
        The stand-in GitHub before.
    config : ConfigFacts
        The configuration before.
    files : frozenset[str]
        The files the playground's buttons name.

    Returns
    -------
    _Found
        The rule, or no tag.
    """
    found = _Found("E0" if failed else "")
    if not config["remote"] and name == "fetch":
        found = _Found("E25")
    elif failed and _unrelated(before, github):
        found = _Found("E43")
    elif failed and not config["remote"]:
        found = _Found("E20" if name == "push" else "E27")
    elif failed and not config["upstream"] and name == "push":
        found = _Found("E21")
    elif failed and not config["upstream"]:
        found = _Found("E45" if _github_main(github) is None else "E46")
    elif failed:
        found = _refused(name, before, after, github, config, files)
    elif before == after:
        found = _Found(_nothing_new(name, before, files))
    elif name in PULLS and _merged_here(before, after, github):
        found = _Found("E47" if name == "pull" else "E32")
    return found


def _refused(name: str, before: Snapshot, after: Snapshot, github: Snapshot | None, config: ConfigFacts, files: frozenset[str]) -> _Found:
    """
    Explain a refused push or pull from the two histories, the working folder and the identity.

    Parameters
    ----------
    name : str
        ``push``, ``fetch``, ``pull`` or ``pull-no-rebase``.
    before : Snapshot
        The repository before.
    after : Snapshot
        The repository after.
    github : Snapshot | None
        The stand-in GitHub before.
    config : ConfigFacts
        The configuration before: a merge makes a commit, so it needs the identity too.
    files : frozenset[str]
        The files the playground's buttons name.

    Returns
    -------
    _Found
        The rule; ``E0`` when no rule proves a cause.
    """
    theirs = _github_main(github)
    missing = theirs is not None and theirs not in _history(before, before["head"])
    ahead = before["head"] is not None and before["head"] not in _history(github, theirs)
    pulling = name in PULLS
    local = [*staged(before), *unstaged(before)]
    in_the_way = [path for path in untracked(before) if path in files]
    identity = config["name"] and config["email"]
    found = _Found("E0")
    if name == "push" and before["head"] is None:
        found = _Found("E19")
    elif name == "push" and before["operation"] == "merge":
        found = _Found("E23")
    elif name == "push" and missing:
        found = _Found("E44" if ahead else "E22")
    elif pulling and before["operation"] == "merge":
        found = _Found("E34")
    elif pulling and theirs is None:
        found = _Found("E28")
    elif name == "pull" and missing and ahead:
        found = _Found("E29")
    elif name == "pull-no-rebase" and missing and ahead and not identity and not local and not in_the_way:
        found = _Found("E10")
    elif pulling and conflicted(after):
        found = _Found("E33", conflicted(after)[0])
    elif pulling and missing and local:
        found = _Found("E30", local[0])
    elif pulling and missing and in_the_way:
        found = _Found("E31", in_the_way[0])
    return found


def _unrelated(before: Snapshot, github: Snapshot | None) -> bool:
    """
    Tell whether a repository and GitHub's were started separately: both have commits, and none in common.

    Parameters
    ----------
    before : Snapshot
        The person's repository.
    github : Snapshot | None
        The stand-in GitHub.

    Returns
    -------
    bool
        True when the two histories share no commit.
    """
    theirs = _history(github, _github_main(github))
    mine = _history(before, before["head"])
    return bool(theirs) and bool(mine) and not theirs & mine


def _merged_here(before: Snapshot, after: Snapshot, github: Snapshot | None) -> bool:
    """
    Tell whether a pull made a merge commit, rather than moving onto one that came from GitHub.

    Parameters
    ----------
    before : Snapshot
        The repository before.
    after : Snapshot
        The repository after.
    github : Snapshot | None
        The stand-in GitHub before.

    Returns
    -------
    bool
        True when HEAD is now on a merge commit that neither repository had before.
    """
    known = _history(github, _github_main(github)) | _history(before, before["head"])
    merge = any(len(commit["parents"]) > 1 for commit in after["commits"] if commit["hash"] == after["head"])
    return merge and after["head"] not in known


def _nothing_new(name: str, before: Snapshot, files: frozenset[str]) -> str:
    """
    Explain a push, fetch or pull that changed nothing.

    Parameters
    ----------
    name : str
        ``push``, ``fetch``, ``pull`` or ``pull-no-rebase``.
    before : Snapshot
        The repository.
    files : frozenset[str]
        The files the playground's buttons name.

    Returns
    -------
    str
        The rule's tag.
    """
    pending = staged(before) or unstaged(before) or [path for path in untracked(before) if path in files]
    tag = "E26"
    if name == "push" and pending:
        tag = "E18"
    elif name == "push":
        tag = "E17"
    elif name == "fetch":
        tag = "E24"
    return tag


def _other(name: str, failed: bool, before: Snapshot, github: Snapshot | None, path: str) -> str:
    """
    Explain init, status, clone, a merge abort, or keeping one side of a conflict.

    Parameters
    ----------
    name : str
        The button's kind.
    failed : bool
        Whether git refused.
    before : Snapshot
        The repository before.
    github : Snapshot | None
        The stand-in GitHub before.
    path : str
        The button's file, or empty.

    Returns
    -------
    str
        The rule's tag, or empty.
    """
    tag = "E0" if failed else ""
    if name == "init" and not failed:
        tag = "E4" if before["exists"] else "E3"
    elif name == "clone" and failed and before["exists"]:
        tag = "E15"
    elif name == "clone" and not failed and github is not None and not github["commits"]:
        tag = "E16"
    elif name == "merge-abort" and failed and before["operation"] != "merge":
        tag = "E41"
    elif name == "merge-abort" and not failed:
        tag = "E40"
    elif name in ("keep-ours", "keep-theirs") and not failed and path in conflicted(before):
        tag = "E39"
    return tag


def _first_named(paths: list[str], files: frozenset[str]) -> str:
    """
    Give the first path a button names.

    Parameters
    ----------
    paths : list[str]
        Paths from a snapshot.
    files : frozenset[str]
        The files the playground's buttons name.

    Returns
    -------
    str
        The path, or empty when none is.
    """
    return next((path for path in paths if path in files), "")


def _github_main(github: Snapshot | None) -> str | None:
    """
    Give the commit GitHub's ``main`` is on.

    Parameters
    ----------
    github : Snapshot | None
        The stand-in GitHub.

    Returns
    -------
    str | None
        Its hash, or None when GitHub has no ``main`` (or there is no GitHub).
    """
    targets = [ref["target"] for ref in github["refs"] if ref["kind"] == "branch" and ref["name"] == "main"] if github else []
    return targets[0] if targets else None


def _history(snap: Snapshot | None, start: str | None) -> set[str]:
    """
    Collect a commit and its ancestors, in a repository that may not be there.

    Parameters
    ----------
    snap : Snapshot | None
        A repository, or None.
    start : str | None
        A commit hash, or None.

    Returns
    -------
    set[str]
        `firstcommit.repomap.history`, or nothing without a repository.
    """
    return history(snap, start) if snap is not None else set()
