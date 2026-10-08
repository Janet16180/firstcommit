"""
Pull requests on the stand-in GitHub: real git for what git does, game records for what only GitHub has.

docs/drafts/chapters-5-9.md, "GitHub, offline and honest". The commits, the changes from where a
branch left its base, whether it merges (``git merge-tree --write-tree``) and the merge itself
(``merge-tree``, ``commit-tree`` with two parents, ``update-ref``) are real git on the bare
repository. A pull request and its reviews are `PullRequest` records, which git never sees; each
open pull request's head is mirrored to ``refs/pull/<n>/head``, as GitHub does. The functions take
the list of records and give a new one; `firstcommit.save` keeps it beside the repository.
"""

from pathlib import Path

from firstcommit import gitcmd, repomap
from firstcommit.records import Commit, PullRequest, PullView, Review, ReviewVerdict, ReviewView

OWNER = "moonbase"
"""The stand-in GitHub's owner, as its address names it (``github.com/moonbase/project.git``)."""
COMMIT_LIMIT = 100


def open_pull(github: Path, pulls: list[PullRequest], *, head: str, base: str, title: str, author: str) -> list[PullRequest]:
    """
    Open a pull request asking to merge one branch of the stand-in GitHub into another.

    Parameters
    ----------
    github : Path
        The bare repository.
    pulls : list[PullRequest]
        The pull requests so far.
    head : str
        The branch asking to be merged.
    base : str
        The branch it asks to join.
    title : str
        The pull request's title.
    author : str
        Who opened it.

    Returns
    -------
    list[PullRequest]
        The pull requests with the new one last, numbered one past the highest; its head is
        mirrored to ``refs/pull/<n>/head``.

    Raises
    ------
    ValueError
        If either branch is missing on the stand-in GitHub, both are the same, or a pull request
        from ``head`` into ``base`` is already open.
    """
    tip = _branch(github, head)
    if not tip or not _branch(github, base) or head == base:
        raise ValueError(f"a pull request needs two different branches of the stand-in GitHub, not {head!r} into {base!r}")
    if any(pull["state"] == "open" and (pull["head"], pull["base"]) == (head, base) for pull in pulls):
        raise ValueError(f"a pull request from {head!r} into {base!r} is already open")
    number = max((pull["number"] for pull in pulls), default=0) + 1
    gitcmd.output(github, "update-ref", f"refs/pull/{number}/head", tip)
    pull: PullRequest = {"number": number, "title": title, "author": author, "head": head, "base": base, "state": "open", "reviews": [], "merge_commit": None}
    return [*pulls, pull]


def mirror(github: Path, pulls: list[PullRequest]) -> None:
    """
    Point each open pull request's ``refs/pull/<n>/head`` at its head branch's commit, as GitHub does after a push.

    Parameters
    ----------
    github : Path
        The bare repository.
    pulls : list[PullRequest]
        The pull requests; one whose head branch is gone keeps its mirror.
    """
    for pull in pulls:
        tip = _branch(github, pull["head"])
        if pull["state"] == "open" and tip:
            gitcmd.output(github, "update-ref", f"refs/pull/{pull['number']}/head", tip)


def review(pulls: list[PullRequest], number: int, *, reviewer: str, verdict: ReviewVerdict, body: str, commit: str) -> list[PullRequest]:
    """
    Add a review to an open pull request.

    Parameters
    ----------
    pulls : list[PullRequest]
        The pull requests.
    number : int
        The one reviewed.
    reviewer : str
        Who reviewed it.
    verdict : ReviewVerdict
        Approved, changes requested, or a comment.
    body : str
        What the reviewer wrote.
    commit : str
        The head commit the reviewer saw.

    Returns
    -------
    list[PullRequest]
        The pull requests, this one with the review added last.

    Raises
    ------
    KeyError
        If no pull request has this number.
    ValueError
        If it is not open.
    """
    pull = _open(pulls, number)
    added: Review = {"reviewer": reviewer, "verdict": verdict, "body": body, "commit": commit}
    return _replaced(pulls, {**pull, "reviews": [*pull["reviews"], added]})


def mergeability(github: Path, base: str, head: str) -> tuple[bool, list[str]]:
    """
    Tell whether merging one branch into another would go through, without touching either.

    Parameters
    ----------
    github : Path
        The bare repository.
    base : str
        The branch merged into.
    head : str
        The branch merged.

    Returns
    -------
    tuple[bool, list[str]]
        True with no paths when it merges cleanly; else False and the conflicted paths, sorted.
    """
    result = gitcmd.run(github, "merge-tree", "--write-tree", "--name-only", "--no-messages", base, head)
    paths = sorted({line for line in result.stdout.split("\n")[1:] if line}) if result.returncode == 1 else []
    return result.returncode == 0, paths


def merge(github: Path, pulls: list[PullRequest], number: int, merger: gitcmd.Person, when: str | None) -> list[PullRequest]:
    """
    Merge an open pull request on the stand-in GitHub, as its merge button does: a commit with two parents on the base.

    Parameters
    ----------
    github : Path
        The bare repository.
    pulls : list[PullRequest]
        The pull requests.
    number : int
        The one to merge.
    merger : gitcmd.Person
        Who merges it: the merge commit's author and committer.
    when : str | None
        The merge commit's date, or None for now.

    Returns
    -------
    list[PullRequest]
        The pull requests, this one merged with its merge commit.

    Raises
    ------
    KeyError
        If no pull request has this number.
    ValueError
        If it is not open, or it conflicts with its base; nothing changes then.
    """
    pull = _open(pulls, number)
    base, head = _branch(github, pull["base"]), _branch(github, pull["head"]) or _pull_head(github, number)
    result = gitcmd.run(github, "merge-tree", "--write-tree", "--no-messages", base, head)
    if result.returncode != 0:
        raise ValueError(f"pull request #{number} has conflicts with {pull['base']!r}")
    tree = result.stdout.split("\n", 1)[0]
    message = f"Merge pull request #{number} from {OWNER}/{pull['head']}\n\n{pull['title']}\n"
    commit = gitcmd.output(github, "commit-tree", tree, "-p", base, "-p", head, author=merger, when=when, stdin=message).strip()
    gitcmd.output(github, "update-ref", f"refs/heads/{pull['base']}", commit, base)
    return _replaced(pulls, {**pull, "state": "merged", "merge_commit": commit})


def board(github: Path, pulls: list[PullRequest]) -> list[PullView]:
    """
    Read every pull request as the review board draws it.

    Parameters
    ----------
    github : Path
        The bare repository.
    pulls : list[PullRequest]
        The pull requests.

    Returns
    -------
    list[PullView]
        One per pull request, in number order.
    """
    return [_view(github, pull) for pull in sorted(pulls, key=lambda pull: pull["number"])]


def _view(github: Path, pull: PullRequest) -> PullView:
    """
    Read one pull request as the board draws it.

    Parameters
    ----------
    github : Path
        The bare repository.
    pull : PullRequest
        The pull request.

    Returns
    -------
    PullView
        Its record with its commits, files, mergeability and reviews as they stand now.
    """
    head = _branch(github, pull["head"]) or _pull_head(github, pull["number"])
    merged = pull["merge_commit"]
    base = f"{merged}^1" if merged else _branch(github, pull["base"])
    commits = _commits(github, f"{base}..{head}")
    files = [line for line in gitcmd.run(github, "diff", "--name-only", f"{base}...{head}").stdout.split("\n") if line]
    mergeable, conflicts = (True, []) if merged else mergeability(github, pull["base"], head)
    reviews: list[ReviewView] = [
        {"reviewer": entry["reviewer"], "verdict": entry["verdict"], "body": entry["body"], "commit": entry["commit"], "outdated": entry["commit"] != head}
        for entry in pull["reviews"]
    ]
    return {
        "number": pull["number"],
        "title": pull["title"],
        "author": pull["author"],
        "head": pull["head"],
        "base": pull["base"],
        "state": pull["state"],
        "head_commit": head,
        "commits": commits,
        "files": files,
        "mergeable": mergeable,
        "conflicts": conflicts,
        "reviews": reviews,
    }


def _commits(github: Path, revisions: str) -> list[Commit]:
    """
    List the commits of a range, newest first.

    Parameters
    ----------
    github : Path
        The bare repository.
    revisions : str
        A range such as ``main..fix``.

    Returns
    -------
    list[Commit]
        At most `COMMIT_LIMIT` commits.
    """
    result = gitcmd.run(github, "log", "-z", "--topo-order", f"--max-count={COMMIT_LIMIT}", f"--format={repomap.COMMIT_FORMAT}", revisions, "--")
    return repomap.parsed_commits(result)


def _branch(github: Path, name: str) -> str:
    """
    Give the commit a branch of the stand-in GitHub points at.

    Parameters
    ----------
    github : Path
        The bare repository.
    name : str
        The branch's name.

    Returns
    -------
    str
        Its hash, or empty when there is no such branch.
    """
    result = gitcmd.run(github, "rev-parse", "-q", "--verify", f"refs/heads/{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else ""


def _pull_head(github: Path, number: int) -> str:
    """
    Give the commit a pull request's mirrored head points at.

    Parameters
    ----------
    github : Path
        The bare repository.
    number : int
        The pull request's number.

    Returns
    -------
    str
        Its hash, or empty when there is no mirror.
    """
    result = gitcmd.run(github, "rev-parse", "-q", "--verify", f"refs/pull/{number}/head")
    return result.stdout.strip() if result.returncode == 0 else ""


def _open(pulls: list[PullRequest], number: int) -> PullRequest:
    """
    Find an open pull request by number.

    Parameters
    ----------
    pulls : list[PullRequest]
        The pull requests.
    number : int
        The number.

    Returns
    -------
    PullRequest
        The pull request.

    Raises
    ------
    KeyError
        If no pull request has this number.
    ValueError
        If it is not open.
    """
    found = next((pull for pull in pulls if pull["number"] == number), None)
    if found is None:
        raise KeyError(f"no pull request #{number}")
    if found["state"] != "open":
        raise ValueError(f"pull request #{number} is not open: it is {found['state']}")
    return found


def _replaced(pulls: list[PullRequest], changed: PullRequest) -> list[PullRequest]:
    """
    Give the pull requests with one replaced by its changed record.

    Parameters
    ----------
    pulls : list[PullRequest]
        The pull requests.
    changed : PullRequest
        The new record, matched by number.

    Returns
    -------
    list[PullRequest]
        The pull requests in the same order.
    """
    return [changed if pull["number"] == changed["number"] else pull for pull in pulls]
