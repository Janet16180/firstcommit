"""Your first commit: the three areas, and the first commit of a new repository."""

from collections.abc import Callable
from typing import Literal

from firstcommit import kit

TITLE = "Your first commit"
DIFFICULTY = 1
XP = 100

BRANCH = "main"
FILE = "README.md"
EXAMPLE_NAME = "Your Name"
EXAMPLE_EMAIL = "you@example.com"
NAME_COMMAND = f'git config --global user.name "{EXAMPLE_NAME}"'
EMAIL_COMMAND = f"git config --global user.email {EXAMPLE_EMAIL}"
PLAYER = kit.Person("Robin Park", "robin@example.com")
STATUS_FIELDS = {"1": 9, "u": 11, "?": 2}
"""How many space-separated fields each kind of `git status --porcelain=v2` entry has, its path last."""

Area = Literal["folder", "index", "head"]

LESSON = [
    kit.Slide(
        id="history",
        title="Why keep history",
        text="""
A project changes every day: files are added, edited and deleted. A version control system
records those changes over time, so you can see what changed, who changed it and when, and get
an earlier version back.

Git is a version control system. Each version you save is called a commit.
""",
        view="none",
    ),
    kit.Slide(
        id="init",
        title="A folder becomes a repository",
        text="""
`git init` turns the current folder into a repository: it creates a hidden `.git` folder, where
Git keeps the history of the project.

A new repository has no commits yet, but you are already on its first branch. A branch is a line
of development; this chapter uses only one. The game sets Git's `init.defaultBranch` setting to
`main`, so in the game a new repository's first branch is called `main`.
""",
        run="git init\nls -A",
        view="terminal",
    ),
    kit.Slide(
        id="areas",
        title="The three areas",
        text="""
Git works with three areas. The working folder holds the files you see and edit (Git calls it
the working tree). The staging area holds what will go into the next commit (Git calls it the
index). The repository holds the commits.

A new file starts in the working folder only. Git calls it untracked: it is in no commit and
not in the staging area. `git status` lists the files that are untracked, staged, or changed but
not staged.
""",
        run='echo "# Team handbook" > README.md\ngit status',
        view="areas",
    ),
    kit.Slide(
        id="nothing-staged",
        title="Staging comes first",
        text="""
Committing now fails. A plain `git commit` takes the content of the staging area, and the
staging area is still empty: a file being in the working folder is not enough.
""",
        run='! git commit -m "Add the README"',
        view="areas",
    ),
    kit.Slide(
        id="add",
        title="Stage with git add",
        text="""
`git add` copies the file's current content into the staging area. The file stays in the
working folder too.

If you edit the file after `git add`, the staging area keeps the content as it was when you
added it: run `git add` again to stage the new content.
""",
        run="git add README.md\ngit status",
        view="areas",
    ),
    kit.Slide(
        id="commit",
        title="Commit",
        text="""
A plain `git commit` saves the content of the staging area as a new commit, with the author's
name and email, the date and the message given with `-m`. Git answers with a summary that
includes the commit's short hash: the first characters of its hash, the name Git computes for it.

`git status` lists no files any more: the working folder, the staging area and the last commit
hold the same content.
""",
        run='git commit -m "Add the README"\ngit status',
        view="map",
    ),
    kit.Slide(
        id="log",
        title="Read the history",
        text="""
A new commit goes on top of the last one: Git records the last commit as its parent.
`git log --oneline` lists the commits, newest first, one per line: a short hash, then the
message. On a terminal, the newest line also shows `(HEAD -> main)` between them: the branch
`main` points to that commit, and you are on that branch.
""",
        run=(
            'echo "Be kind to each other." >> README.md\n'
            "git add README.md\n"
            'git commit -m "Add the first rule"\n'
            "git log --oneline"
        ),
        view="map",
    ),
]

BRIEFING = """
You are starting a new project, and its history starts today. Turn the empty `project` folder
into a Git repository on the branch `main`, create a `README.md` file and save it in your first
commit.

The level is solved when the last commit on `main` contains `README.md`, and `git status` lists
no untracked, changed or staged files.
"""

HINTS = [
    """
Run `git status` after every command. It names the branch you are on, and lists which files
are untracked, staged or changed.
""",
    """
A new file reaches a commit in two moves: `git add` copies it into the staging area, then
`git commit` saves the staging area as a commit.
""",
    """
In the `project` folder: run `git init`, create `README.md`, run `git add README.md`, then
`git commit -m "Add the README"`. Before the commit, make sure Git knows your name and
email: run `git config --global user.name "Your Name"` and
`git config --global user.email you@example.com`, with your own name and address.
""",
]

DEBRIEF = """
You turned an empty folder into a repository, created a file, staged it and saved it in a
commit. That loop is the heart of daily work with Git: edit, `git add`, `git commit`.

What a commit really is: a commit records a complete snapshot of the project's files, not only
the lines that changed; a plain `git commit` takes that snapshot from the staging area. Next to
the files it stores the author's name and email, the date, the message, and the commit that came
before it (its parent; your first commit has none). Git names the commit with a hash computed
from all of that. Files that did not change are not stored twice: the new commit points to the
content Git already has.

Why the staging area exists: it lets you choose what goes into each commit. When you have
changed three files for two different reasons, you can stage and commit them as two focused
commits, each with its own message. `git status` shows what is staged before you commit, so a
commit holds what you meant it to hold. After a plain `git commit`, the staging area is not
emptied: it matches the new commit, ready for your next change.

At work: the commits you make carry the name and email Git is set to use, so set them once on
your own computer (the chapter "Your real setup" walks you through it).

Commands to keep:

    $ git init                  # make the current folder a repository
    $ git status                # untracked, staged and changed files
    $ git add README.md         # copy a file into the staging area
    $ git commit -m "Message"   # save the staging area as a commit
    $ git log --oneline         # list the commits, newest first
    $ git config --global user.name "Your Name"
    $ git config --global user.email you@example.com
"""

SOLVED = "Your last commit contains `README.md`, and the working folder, the staging area and that commit all agree."


def has_file(snap: kit.Snapshot, area: Area) -> bool:
    """
    Tell whether the quest's file is in one of the three areas.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository.
    area : Area
        ``"folder"`` (the working folder), ``"index"`` (the staging area) or ``"head"`` (the
        last commit).

    Returns
    -------
    bool
        True if `FILE` is there.
    """
    return any(entry["path"] == FILE and entry[area] is not None for entry in snap["files"])


def on_main(snap: kit.Snapshot) -> bool:
    """
    Tell whether the project folder holds a repository whose HEAD is on `BRANCH`.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    bool
        True for a non-bare repository on `BRANCH`, with or without commits.
    """
    return snap["exists"] and not snap["bare"] and snap["branch"] == BRANCH


def untracked(snap: kit.Snapshot) -> list[str]:
    """
    List the files that are in the working folder but not in the staging area, ignored ones aside.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    list[str]
        Their paths.
    """
    return [
        entry["path"]
        for entry in snap["files"]
        if entry["folder"] is not None and entry["index"] is None and not entry["ignored"] and not entry["conflicted"]
    ]


def staged(snap: kit.Snapshot) -> list[str]:
    """
    List the files whose staging-area content differs from the last commit's.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    list[str]
        Their paths.
    """
    return [entry["path"] for entry in snap["files"] if not entry["conflicted"] and entry["index"] != entry["head"]]


def unstaged(snap: kit.Snapshot) -> list[str]:
    """
    List the tracked files whose working-folder content differs from the staging area's.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    list[str]
        Their paths, conflicted files included.
    """
    return [
        entry["path"]
        for entry in snap["files"]
        if entry["conflicted"] or (entry["index"] is not None and entry["folder"] != entry["index"])
    ]


def status_paths(lab: kit.Lab) -> list[str]:
    """
    List the paths `git status` names in the project folder.

    The snapshot compares contents and leaves nested repositories out, so a changed file mode or
    a repository inside the project folder shows up only here.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; the project folder may be missing.

    Returns
    -------
    list[str]
        The paths that are untracked, staged, or changed but not staged; none if git fails.
    """
    result = kit.git_run(lab.project, "status", "--porcelain=v2", "-z", "--no-renames")
    entries = result.stdout.split("\0") if result.returncode == 0 else []
    return [entry.split(" ", STATUS_FIELDS[entry[0]] - 1)[-1] for entry in entries if entry[:1] in STATUS_FIELDS]


def file_names(paths: list[str]) -> str:
    """
    Name a few files for a message.

    Parameters
    ----------
    paths : list[str]
        At least one path.

    Returns
    -------
    str
        The first three paths in backticks, and how many more there are.
    """
    shown = ", ".join(f"`{path}`" for path in paths[:3])
    more = len(paths) - 3
    return shown if more <= 0 else f"{shown} and {more} more"


def repository_move(lab: kit.Lab, snap: kit.Snapshot) -> str:
    """
    Tell the player how to get a repository on `BRANCH` in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    snap : kit.Snapshot
        The project's repository; `on_main` is False for it.

    Returns
    -------
    str
        What to do next.
    """
    has_main = any(ref["kind"] == "branch" and ref["name"] == BRANCH for ref in snap["refs"])
    if not snap["exists"] and kit.snapshot(lab.root)["exists"]:
        move = (
            "You created the repository one folder too high, in the lab folder above `project`. "
            "Restart the level, then run `git init` inside `project`."
        )
    elif not snap["exists"] and kit.snapshot(lab.project / "project")["exists"]:
        move = (
            "The repository is in a new folder `project` inside `project`: `git init project` creates that folder. "
            "Restart the level, then run `git init` with nothing after it."
        )
    elif not snap["exists"]:
        move = "There is no repository in the `project` folder yet. Create one with `git init`."
    elif snap["bare"]:
        move = "This is a bare repository: it has no working folder to edit files in. Restart the level to get an empty folder back."
    elif snap["branch"] is None and has_main:
        move = "You are not on a branch (HEAD is detached). Go back to `main` with `git switch main`."
    elif snap["branch"] is None:
        move = "You are not on a branch (HEAD is detached). Create the branch `main` here with `git switch -c main`."
    elif has_main:
        move = f"You are on the branch `{snap['branch']}`, and this level uses `main`. Switch to it with `git switch main`."
    else:
        move = f"You are on the branch `{snap['branch']}`, and this level uses `main`. Rename it with `git branch -m main`."
    return move


def commit_move(snap: kit.Snapshot) -> str:
    """
    Tell the player what is left before the quest's file is in a commit.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository, on `BRANCH`, whose last commit lacks `FILE`.

    Returns
    -------
    str
        What to do next.
    """
    if has_file(snap, "index"):
        move = '`README.md` is in the staging area. Save the staging area as a commit with `git commit -m "Add the README"`.'
    elif has_file(snap, "folder"):
        move = "Git sees `README.md` in the working folder, but it is not in the staging area yet, and a new file gets into a commit only once it is staged."
    else:
        move = "There is no `README.md` in the `project` folder yet. Create it there."
    return move


def tidy_move(lab: kit.Lab, snap: kit.Snapshot) -> str:
    """
    Tell the player what keeps the repository from being clean.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    str
        What to do next, or an empty string when `git status` lists nothing.
    """
    loose, waiting, edited = untracked(snap), staged(snap), unstaged(snap)
    listed = [] if loose or waiting or edited else status_paths(lab)
    nested = [path for path in listed if path.endswith("/")]
    if loose:
        verb = "is" if len(loose) == 1 else "are"
        move = f"{file_names(loose)} {verb} in the working folder but not in the staging area (untracked). Stage and commit what you need, and delete the rest."
    elif waiting:
        verb = "is" if len(waiting) == 1 else "are"
        move = f"{file_names(waiting)} {verb} staged but not committed yet. Commit, so that your last commit holds what is staged."
    elif edited:
        move = f"{file_names(edited)} changed after the last `git add`. Stage and commit what changed."
    elif nested:
        kind, them = (
            ("is a folder with its own repository", "it")
            if len(nested) == 1
            else ("are folders with their own repositories", "them")
        )
        move = f"{file_names(nested)} {kind}, so `git status` lists {them} as untracked. Delete {them}: this level uses one repository, in `project`."
    elif listed:
        move = f"`git status` still lists {file_names(listed)}. Run `git status` to see what changed, then stage and commit the change."
    else:
        move = ""
    return move


def next_move(lab: kit.Lab, snap: kit.Snapshot) -> str:
    """
    Tell the player what to do next to solve the level.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    str
        What to do next, or an empty string when the level is solved.
    """
    if not on_main(snap):
        move = repository_move(lab, snap)
    elif not has_file(snap, "head"):
        move = commit_move(snap)
    else:
        move = tidy_move(lab, snap)
    return move


def progress(lab: kit.Lab, snap: kit.Snapshot, done: bool, success: str) -> kit.Verdict:
    """
    Judge a watch step on the repository.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    snap : kit.Snapshot
        The project's repository.
    done : bool
        Whether the step's goal is reached.
    success : str
        What to say when it is.

    Returns
    -------
    kit.Verdict
        The success message, or what to do next.
    """
    return kit.Verdict(done, success if done else next_move(lab, snap))


def configured(lab: kit.Lab, key: str) -> str:
    """
    Read a setting as git would use it for a commit in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; the project folder may be missing.
    key : str
        A configuration key such as ``user.name``.

    Returns
    -------
    str
        Its value, or an empty string when it is not set.
    """
    result = kit.git_run(lab.project, "config", "--get", key)
    return result.stdout.strip() if result.returncode == 0 else ""


def identity(lab: kit.Lab, key: str, example: str, what: str, command: str) -> kit.Verdict:
    """
    Judge a quest step that sets the player's name or email.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    key : str
        ``user.name`` or ``user.email``.
    example : str
        The example value in the step's suggested command.
    what : str
        ``"name"`` or ``"email"``, for the messages.
    command : str
        The complete command that sets it, with the example value.

    Returns
    -------
    kit.Verdict
        Passes once git finds a value other than the example.
    """
    value = configured(lab, key)
    if not value:
        message = f"Git does not know your {what} yet. Set it with `{command}`, using your own {what}."
    elif value == example:
        message = f"Your {what} is set to the example, `{example}`. Run `{command}` again with your own {what}."
    else:
        message = f"Git will now write your {what} into the commits you make."
    return kit.Verdict(bool(value) and value != example, message)


def watch_init(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once the project folder is a repository on `BRANCH`.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    snap = kit.snapshot(lab.project)
    return progress(lab, snap, on_main(snap), "The `project` folder is now a repository, on the branch `main`.")


def check_branch(lab: kit.Lab, state: kit.State, answer: str) -> kit.Verdict:
    """
    Check the branch name the player read in `git status`.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    answer : str
        What the player typed.

    Returns
    -------
    kit.Verdict
        Right when it names the branch HEAD is on.
    """
    snap = kit.snapshot(lab.project)
    typed = answer.strip()
    branch = snap["branch"] or ""
    if not on_main(snap):
        message = repository_move(lab, snap)
    elif not typed:
        message = "Type the name of the branch that `git status` says you are on."
    elif typed == branch:
        message = "Right: you are on the branch `main`."
    elif typed.casefold() == branch.casefold():
        message = "Almost: type the name exactly as `git status` shows it, with the same capital and small letters."
    elif typed.split()[-1] == branch:
        message = "Type only the name of the branch, without the words before it."
    else:
        message = "That is not the branch you are on. Read the top of what `git status` prints: it names the branch."
    return kit.Verdict(on_main(snap) and typed == branch, message)


def watch_file(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once the quest's file is in the working folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    snap = kit.snapshot(lab.project)
    return progress(
        lab,
        snap,
        on_main(snap) and has_file(snap, "folder"),
        "`README.md` is in the working folder. A new file stays untracked until you stage it.",
    )


def watch_stage(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once the quest's file is in the staging area.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    snap = kit.snapshot(lab.project)
    return progress(
        lab,
        snap,
        on_main(snap) and has_file(snap, "index"),
        "`README.md` is in the staging area, ready to be committed.",
    )


def watch_name(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once git knows the player's name.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    return identity(lab, "user.name", EXAMPLE_NAME, "name", NAME_COMMAND)


def watch_email(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once git knows the player's email.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    return identity(lab, "user.email", EXAMPLE_EMAIL, "email", EMAIL_COMMAND)


def watch_commit(lab: kit.Lab, state: kit.State) -> kit.Verdict:
    """
    Pass once the last commit on `BRANCH` contains the quest's file.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    kit.Verdict
        The step's verdict.
    """
    snap = kit.snapshot(lab.project)
    return progress(
        lab,
        snap,
        on_main(snap) and has_file(snap, "head"),
        "Your last commit on `main` contains `README.md`.",
    )


def check_hash(lab: kit.Lab, state: kit.State, answer: str) -> kit.Verdict:
    """
    Check the short hash the player read in `git log --oneline`.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    answer : str
        What the player typed.

    Returns
    -------
    kit.Verdict
        Right when it starts the hash of one of the repository's commits.
    """
    snap = kit.snapshot(lab.project)
    commits = snap["commits"]
    typed = answer.strip()
    words = typed.split()
    right = any(kit.is_hash_of(answer, commit["hash"]) for commit in commits)
    if not commits:
        message = next_move(lab, snap)
    elif not typed:
        message = "Type the short hash that starts your commit's line in `git log --oneline`."
    elif right:
        message = "Right: that is the start of your commit's hash. Git names every commit this way."
    elif any(typed == commit["subject"] for commit in commits):
        message = "That is your commit's message. Its short hash is at the start of the same line."
    elif len(words) > 1 and any(kit.is_hash_of(words[0], commit["hash"]) for commit in commits):
        message = "Type only the short hash, the first word of the line."
    elif any(commit["hash"].startswith(typed.lower()) for commit in commits):
        message = f"Git needs at least {kit.MIN_HASH_PREFIX} characters of a hash. Type the whole short hash that `git log --oneline` shows."
    else:
        message = "That is not the start of a commit hash in this repository. Run `git log --oneline`: each line starts with a short hash."
    return kit.Verdict(right, message)


QUEST = [
    kit.Step(
        id="init",
        text="""
Your terminal is open in an empty folder called `project`. To give it a history, make it a Git
repository:

    $ git init

`git init` creates a hidden `.git` folder: that is where Git keeps the project's commits.
Its first branch is called `main`, the name the game sets as the default.
""",
        command="git init",
        watch=watch_init,
    ),
    kit.Step(
        id="status",
        text="""
`git status` is the command you will run most. It names the branch you are on and lists the
files that are untracked, staged, or changed but not staged. Run it now. The repository has no
files and no commits yet, so it has little to report.
""",
        command="git status",
        question="Which branch does `git status` say you are on?",
        placeholder="a branch name",
        check=check_branch,
    ),
    kit.Step(
        id="file",
        text="""
Give the project its first file, a `README.md`, the file that tells people what a project is
about:

    $ echo "# My project" > README.md

`echo` prints a line of text, and `>` writes it into the file: it creates the file, or replaces
everything in it if the file already exists. Run `git status` again: Git sees the new file, but
does not track it yet.
""",
        command='echo "# My project" > README.md',
        watch=watch_file,
    ),
    kit.Step(
        id="stage",
        text="""
A new file gets into a commit only through the staging area, so copy it there:

    $ git add README.md

`git add` usually prints nothing. Run `git status` once more: `README.md` is now staged, ready
for the next commit. It is still in your working folder too: `git add` copies, it does not move.
""",
        command="git add README.md",
        watch=watch_stage,
    ),
    kit.Step(
        id="name",
        text="""
Every commit records who made it, with a name and an email. Tell Git your name, keeping the
quotes so that a name with spaces stays one value:

    $ git config --global user.name "Your Name"

Replace `Your Name` with your own. `--global` means "for all my repositories on this computer,
unless one of them sets its own". Inside the game, it writes the game's own settings file
instead of your real one, so nothing outside the game changes. At work you will run the same
commands in your own terminal; the chapter "Your real setup" walks you through it. If you
already set your name earlier in the game, this step passes at once.
""",
        command=NAME_COMMAND,
        watch=watch_name,
    ),
    kit.Step(
        id="email",
        text="""
Now your email. Use the address you will use for work:

    $ git config --global user.email you@example.com

Replace `you@example.com` with your own address.
""",
        command=EMAIL_COMMAND,
        watch=watch_email,
    ),
    kit.Step(
        id="commit",
        text="""
Save the staging area as your first commit, with a message that says what it does:

    $ git commit -m "Add the README"

`-m` gives the message. Git answers with a short summary of the new commit, and the map shows
your first commit on `main`.
""",
        command='git commit -m "Add the README"',
        watch=watch_commit,
    ),
    kit.Step(
        id="hash",
        text="""
List the history:

    $ git log --oneline

Each line is one commit, newest first: a short hash, then the message. On your terminal, the
newest line also shows `(HEAD -> main)` between them: your branch points to that commit.

The short hash is the start of the commit's full hash, which has 40 characters here. Commands
such as `git show` accept the short form in place of the full hash, as long as no other object
in the repository has a hash that starts the same way.
""",
        command="git log --oneline",
        question="What is your commit's short hash?",
        placeholder="a short hash",
        check=check_hash,
    ),
]


def setup(lab: kit.Lab) -> kit.State:
    """
    Create the empty project folder the player turns into a repository.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab; its folder exists and is empty.

    Returns
    -------
    kit.State
        An empty state: the level has nothing to remember.
    """
    lab.project.mkdir()
    return {}


def check(lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict:
    """
    Solved when `README.md` is committed on `main` and nothing is untracked, staged or changed.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).
    answer : str | None
        Ignored: the level is checked against the repository.

    Returns
    -------
    kit.Verdict
        Whether the level is solved, and what to do next if not.
    """
    move = next_move(lab, kit.snapshot(lab.project))
    return kit.Verdict(not move, move or SOLVED)


def solve(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Play the level like a player: create the repository, the file, and the first commit.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab, as `setup` left it.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: the level is checked against the repository.
    """
    for action in (init_repository, write_readme, stage_readme, commit_readme):
        action(lab, state)
    return None


def init_repository(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Run ``git init`` in the project folder.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    kit.git(lab.project, "init")
    return None


def read_branch(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Read the branch HEAD is on, as `git status` names it.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        The branch name to type.
    """
    return kit.git(lab.project, "branch", "--show-current").strip()


def write_readme(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Create the quest's file.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    (lab.project / FILE).write_text("# My project\n")
    return None


def stage_readme(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Stage the quest's file.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    kit.git(lab.project, "add", FILE)
    return None


def set_name(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Set the player's name in the game's global settings.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    kit.git(lab.project, "config", "--global", "user.name", PLAYER.name)
    return None


def set_email(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Set the player's email in the game's global settings.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    kit.git(lab.project, "config", "--global", "user.email", PLAYER.email)
    return None


def commit_readme(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Commit what is staged.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        None: a watch step takes no answer.
    """
    kit.git(lab.project, "commit", "-m", "Add the README", author=PLAYER)
    return None


def read_short_hash(lab: kit.Lab, state: kit.State) -> str | None:
    """
    Read the last commit's short hash from the first column of ``git log --oneline``.

    Parameters
    ----------
    lab : kit.Lab
        The level's lab.
    state : kit.State
        The level's state (unused).

    Returns
    -------
    str | None
        The short hash to type.
    """
    return kit.git(lab.project, "log", "--oneline", "-1").split()[0]


QUEST_ACTIONS: dict[str, Callable[[kit.Lab, kit.State], str | None]] = {
    "init": init_repository,
    "status": read_branch,
    "file": write_readme,
    "stage": stage_readme,
    "name": set_name,
    "email": set_email,
    "commit": commit_readme,
    "hash": read_short_hash,
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
