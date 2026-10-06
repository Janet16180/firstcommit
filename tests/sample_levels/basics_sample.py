"""
A small level for the game's own tests: commit ``hello.txt`` on a branch named in the state.

It follows the level contract of AUTHORING.md section 3.3 with one step of each kind, and reads
the lab with plumbing only.
"""

from firstcommit import kit

TITLE = "Say hello"
DIFFICULTY = 1
XP = 100
LESSON = [
    kit.Slide(id="init", title="A repository", text="Make one:\n\n    $ git init -q demo", run="git init -q demo", view="terminal"),
    kit.Slide(id="areas", title="Three areas", text="A file lives in three places.", view="areas"),
]
BRIEFING = "Commit `hello.txt` on the branch `{{branch}}`."
HINTS = [
    "A commit takes what is in the staging area.",
    "Stage the file, then commit it.",
    "Type `git add hello.txt`, then `git commit -m 'Say hello'`.",
]
DEBRIEF = "`hello.txt` is now in a commit on `{{branch}}`."


def is_staged(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once ``hello.txt`` is in the staging area.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.

    Returns
    -------
    kit.Verdict
        Whether the file is staged.
    """
    staged = kit.git_run(lab.project, "ls-files", "--stage", "--", "hello.txt").stdout != ""
    return kit.Verdict(staged, "Staged." if staged else "Not staged yet.")


def names_the_branch(lab: kit.Lab, state: kit.State, answer: str) -> kit.Verdict:
    """
    Pass when the player names the branch the repository is on.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.
    answer : str
        What the player typed.

    Returns
    -------
    kit.Verdict
        Whether the answer is the branch.
    """
    right = answer.strip() == state["branch"]
    return kit.Verdict(right, "Right." if right else "Look at the first line of `git status`.")


QUEST = [
    kit.Step(id="look", text="Look at the repository with `git status`.", command="git status"),
    kit.Step(id="stage", text="Stage `hello.txt`.", command="git add hello.txt", watch=is_staged),
    kit.Step(id="branch", text="Find the branch.", question="Which branch is `{{branch}}`?", placeholder="a branch name", check=names_the_branch),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Make a repository with an untracked ``hello.txt``.

    Parameters
    ----------
    lab : kit.Lab
        The empty lab.

    Returns
    -------
    kit.State
        The branch name.
    """
    kit.git(lab.root, "init", "-q", "-b", "trunk", str(lab.project))
    (lab.project / "hello.txt").write_text("hello\n")
    return {"branch": "trunk"}


def check(lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict:
    """
    Pass once ``hello.txt`` is in the last commit of the branch.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.
    answer : str | None
        Ignored: the repository is checked.

    Returns
    -------
    kit.Verdict
        Whether the file is committed on the branch.
    """
    committed = kit.git_run(lab.project, "rev-parse", "--verify", "-q", f"refs/heads/{state['branch']}:hello.txt").returncode == 0
    return kit.Verdict(committed, "Committed." if committed else "`hello.txt` is not in a commit yet.")


def solve(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Stage and commit the file, as a player would.

    Parameters
    ----------
    lab : kit.Lab
        The lab after `setup`.
    state : kit.State
        The level state.

    Returns
    -------
    str | None
        None: the repository is checked.
    """
    kit.git(lab.project, "add", "hello.txt")
    kit.git(lab.project, "commit", "-q", "-m", "Say hello")
    return None


def stage(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Do the player's part of the ``stage`` step.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.

    Returns
    -------
    str | None
        None: a watch step needs no answer.
    """
    kit.git(lab.project, "add", "hello.txt")
    return None


def read_branch(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Do the player's part of the ``branch`` step: read the branch name.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    state : kit.State
        The level state.

    Returns
    -------
    str | None
        The branch name.
    """
    return kit.git(lab.project, "symbolic-ref", "--short", "HEAD").strip()


QUEST_ACTIONS = {"stage": stage, "branch": read_branch}
