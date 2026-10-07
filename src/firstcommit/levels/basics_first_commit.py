"""
Your first commit: the three places, and the first commit of a new repository.

The lesson is picture-first (AUTHORING.md section 3.5): each slide shows one change in the four
places figure, and its text only reads the picture; details are folded into ``more``. It has
nine slides, one more than the 4-8 of AUTHORING.md, because "an empty box makes no commit" is the
beginner's biggest misconception and gets a picture of its own (nothing moves).
"""

import shlex
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

Area = Literal["folder", "index", "head"]

LESSON = [
    kit.Slide(
        id="history",
        title="Why keep history",
        text="""
Your project folder is empty, and Git keeps nothing for it yet. Git can save versions of your
project as closed boxes, called commits, and you can get any of them back.
""",
        more="""
A project changes every day: files are added, edited and deleted. A version control system
records those changes over time, so you can see what changed, who changed it and when. Git is a
version control system.

The picture shows three places on your computer: the working folder, the staging area and your
repository. The next slides fill them, one command at a time.
""",
        view="places",
    ),
    kit.Slide(
        id="init",
        title="The folder becomes a repository",
        text="""
`git init` turns the folder into a repository. The open box, the staging area, is empty, and
your repository has no closed boxes yet.
""",
        more="""
`git init` creates a hidden `.git` folder, which `ls -A` shows: Git keeps your repository there,
and the staging area too once you add a file.

A new repository has no commits yet, but you are already on its first branch. A branch is a line
of development; this chapter uses only one. The game sets Git's `init.defaultBranch` setting to
`main`, so in the game a new repository's first branch is called `main`.
""",
        run="git init",
        view="places",
    ),
    kit.Slide(
        id="file",
        title="A new file is a page",
        text="""
A new file appears as a page in the working folder. It is untracked: it is in neither box yet.
""",
        more="""
A page shows the file's name and a short id of its content. The same content always gets the
same id and colour, so a page that changes gets a new one.

`git status` lists the file as untracked. Git's own name for the working folder is the working
tree.
""",
        run='echo "# Team handbook" > README.md',
        view="places",
    ),
    kit.Slide(
        id="nothing-staged",
        title="An empty box makes no commit",
        text="""
The open box is empty, so `git commit` has nothing to close. No closed box appears: a page in
the working folder is not enough.
""",
        more="""
A plain `git commit` takes the content of the staging area, and a new file gets there only with
`git add`. Here Git makes no commit and says why.
""",
        run='! git commit -m "Add the README"',
        view="places",
    ),
    kit.Slide(
        id="add",
        title="git add copies the page",
        text="""
`git add` drops a copy of the page into the open box. The working folder keeps its page.
""",
        more="""
`git add` copies the file's content as it is at that moment, and usually prints nothing. The open
box holds a page for every file the next commit will contain, not only the changed ones. Git's
own name for the staging area is the index.
""",
        run="git add README.md",
        view="places",
    ),
    kit.Slide(
        id="commit",
        title="git commit closes the box",
        text="""
`git commit` closes a copy of the open box and sets it in your repository: your first commit,
labelled with its short hash. The open box keeps its page, ready for the next commit.
""",
        more="""
A plain `git commit` saves the content of the staging area as a new commit, with the author's
name and email, the date and the message given with `-m`. Your branch, `main`, now points to it.

The short hash is the first characters of the commit's hash, the name Git computes from all of
that. `git status` now lists no files: the three places hold the same content.
""",
        run='git commit -m "Add the README"',
        view="places",
    ),
    kit.Slide(
        id="edit",
        title="A new version of the page",
        text="""
Editing the file changes its page in the working folder: a new id and colour. The open box and
the closed box still hold the old version.
""",
        more="""
`>>` adds a line at the end of the file. `git status` lists the file as modified but not staged.
A plain `git commit` now would make no commit: the open box still holds what the last closed box
holds.
""",
        run='echo "Be kind to each other." >> README.md',
        view="places",
    ),
    kit.Slide(
        id="add-again",
        title="Stage the new version",
        text="""
`git add` drops the new version into the open box, in place of the old one. The closed box keeps
the old version.
""",
        more="""
The staging area keeps a file's content as it was at the last `git add`, so after another edit
you add the file again. `git status` now lists it as modified and staged.
""",
        run="git add README.md",
        view="places",
    ),
    kit.Slide(
        id="second-commit",
        title="Two saved versions",
        text="""
Each closed box is a saved version of your project: a commit. The new one sits on top of the
first, its parent. `git log --oneline` lists them newest first, each with its short hash and
message.
""",
        more="""
On a terminal, and here, the newest line also shows `(HEAD -> main)`: your branch points to that
commit, and you are on it. Any saved version can come back: `git show HEAD~1:README.md` prints
the README as the first commit saved it.
""",
        run='git commit -m "Add the first rule"\ngit log --oneline',
        view="places",
    ),
]

BRIEFING = """
You are starting a new project, and its history starts today. Your terminal opens in the empty
`project` folder: make that folder a Git repository on the branch `main`, then create a
`README.md` file in it and save it in your first commit.

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
        The first three paths as code, shown exactly, and how many more there are.
    """
    shown = ", ".join(kit.code(path) for path in paths[:3])
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
        move = f"You are on the branch {kit.code(snap['branch'])}, and this level uses `main`. Switch to it with `git switch main`."
    else:
        move = f"You are on the branch {kit.code(snap['branch'])}, and this level uses `main`. Rename it with `git branch -m main`."
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
    misnamed = [
        entry
        for entry in snap["files"]
        if entry["path"] != FILE and entry["path"].casefold() == FILE.casefold() and entry["folder"] is not None
    ]
    if has_file(snap, "index"):
        move = '`README.md` is in the staging area. Save the staging area as a commit with `git commit -m "Add the README"`.'
    elif has_file(snap, "folder"):
        move = "Git sees `README.md` in the working folder, but it is not in the staging area yet, and a new file gets into a commit only once it is staged."
    elif misnamed:
        name = misnamed[0]["path"]
        rename = "git mv" if misnamed[0]["index"] is not None else "mv"
        move = (
            f"There is no `README.md` yet, but there is {kit.code(name)}: the level needs the name `README.md`, "
            f"with the same capital and small letters. Rename it with {kit.code(f'{rename} {shlex.quote(name)} {FILE}')}."
        )
    else:
        move = "There is no `README.md` in the `project` folder yet. Create it there."
    return move


def tidy_move(snap: kit.Snapshot) -> str:
    """
    Tell the player what keeps the repository from being clean.

    Parameters
    ----------
    snap : kit.Snapshot
        The project's repository.

    Returns
    -------
    str
        What to do next, or an empty string when `git status` lists nothing.
    """
    clashing = kit.conflicted(snap)
    loose = kit.untracked(snap)
    waiting = kit.staged(snap)
    chmodded = kit.mode_changed(snap)
    deleted = [entry["path"] for entry in snap["files"] if entry["folder_change"] == "deleted"]
    edited = [path for path in kit.unstaged(snap) if path not in chmodded and path not in deleted]
    repositories = [f"{path}/" for path in kit.nested(snap)]
    if clashing:
        verb, them = ("is", "it") if len(clashing) == 1 else ("are", "them")
        move = f"{file_names(clashing)} {verb} in conflict: edit {them} to keep the content you want, then stage and commit {them}."
    elif loose:
        verb = "is" if len(loose) == 1 else "are"
        move = f"{file_names(loose)} {verb} in the working folder but not in the staging area (untracked). Stage and commit what you need, and delete the rest."
    elif waiting:
        verb = "is" if len(waiting) == 1 else "are"
        move = f"{file_names(waiting)} {verb} staged but not committed yet. Commit, so that your last commit holds what is staged."
    elif FILE in deleted:
        move = "`README.md` is deleted from the working folder, and the level needs it. Bring it back with `git restore README.md`."
    elif deleted:
        verb, them = ("is", "it") if len(deleted) == 1 else ("are", "them")
        move = f"{file_names(deleted)} {verb} deleted from the working folder, and the deletion is not staged. Stage and commit {them}, as any other change."
    elif edited:
        verb = "is" if len(edited) == 1 else "are"
        move = f"{file_names(edited)} {verb} changed in the working folder, and the change is not staged. Stage and commit what changed."
    elif chmodded:
        whose = "its" if len(chmodded) == 1 else "their"
        move = f"`git status` still lists {file_names(chmodded)}: only {whose} executable permission changed. Stage and commit the change."
    elif repositories:
        kind, them = (
            ("is a folder with its own repository", "it")
            if len(repositories) == 1
            else ("are folders with their own repositories", "them")
        )
        move = f"{file_names(repositories)} {kind}, so `git status` lists {them} as untracked. Delete {them}: this level uses one repository, in `project`."
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
        move = tidy_move(snap)
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


QUEST: list[kit.Step] = [
    kit.WatchStep(
        id="init",
        text="""
Make the empty `project` folder a repository.
""",
        more="""
Your terminal is open in the `project` folder. `git init` creates a hidden `.git` folder, where
Git keeps your repository. Its first branch is called `main`, the name the game sets as the
default.
""",
        command="git init",
        watch=watch_init,
    ),
    kit.AnswerStep(
        id="status",
        text="""
Run `git status`: it names the branch you are on.
""",
        more="""
`git status` also lists the files that are untracked, staged, or changed but not staged. The
repository has no files and no commits yet, so it has little to report. You will run it often.
""",
        command="git status",
        question="Which branch does `git status` say you are on?",
        placeholder="a branch name",
        check=check_branch,
    ),
    kit.WatchStep(
        id="name",
        text="""
Every commit records who made it. Set your name, with your own in place of `Your Name`.
""",
        more="""
Keep the quotes, so that a name with spaces stays one value. `--global` means "for all my
repositories on this computer, unless one of them sets its own". Inside the game, it writes the
game's own settings file instead of your real one, so nothing outside the game changes. At work
you will run the same commands in your own terminal; the chapter "Your real setup" walks you
through it. If you already set your name earlier in the game, this step passes at once.
""",
        command=NAME_COMMAND,
        watch=watch_name,
    ),
    kit.WatchStep(
        id="email",
        text="""
Now set your email, with your own address in place of `you@example.com`.
""",
        more="""
Use the address you will use for work.
""",
        command=EMAIL_COMMAND,
        watch=watch_email,
    ),
    kit.WatchStep(
        id="file",
        text="""
Create the project's first file. Its page appears in the working folder.
""",
        more="""
A `README.md` is the file that tells people what a project is about. `echo` prints a line of
text, and `>` writes it into the file: it creates the file, or replaces everything in it if the
file already exists. `git status` lists the new file as untracked.
""",
        command='echo "# My project" > README.md',
        watch=watch_file,
    ),
    kit.WatchStep(
        id="stage",
        text="""
Drop a copy of the page into the open box.
""",
        more="""
`git add` usually prints nothing. The working folder keeps its page: `git add` copies, it does
not move. A new file gets into a commit only through the staging area.
""",
        command="git add README.md",
        watch=watch_stage,
    ),
    kit.WatchStep(
        id="commit",
        text="""
Close the box: save the staging area as your first commit.
""",
        more="""
`-m` gives the message; without it, Git opens a text editor for you to write one. Git answers
with a short summary of the new commit, and a closed box appears in your repository, on `main`.
""",
        command='git commit -m "Add the README"',
        watch=watch_commit,
    ),
    kit.AnswerStep(
        id="hash",
        text="""
List the history, then type your commit's short hash.
""",
        more="""
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
    Play the level like a player: every quest step's action, in order (AUTHORING section 3.6).

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
    for quest_step in QUEST:
        QUEST_ACTIONS[quest_step.id](lab, state)
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
    "name": set_name,
    "email": set_email,
    "file": write_readme,
    "stage": stage_readme,
    "commit": commit_readme,
    "hash": read_short_hash,
}
"""The player's part of each quest step, for the level tests (AUTHORING.md section 3.6); the game never reads it."""
