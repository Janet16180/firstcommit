# Verification log: basics

How every claim in the `basics` chapter was checked. Target: git 2.43.0 (Ubuntu 24.04 package),
checked on WSL on 2026-10-06.

**Method.** Man pages are the installed 2.43 pages, quoted with `man -P cat <page> | grep -n`.
Experiments ran in a scratch folder with `GIT_CONFIG_GLOBAL` pointing at a scratch file,
`GIT_CONFIG_NOSYSTEM=1`, `GIT_CEILING_DIRECTORIES` set to the scratch folder, `LC_ALL=C`, and a
fixed identity and date (the lessons' environment). Claims marked *re-checked* are re-run on
every test run: by the lesson's `run` lines, a card's `verify` or `code`, or a test in
`tests/levels/test_basics_first_commit.py`.

Sources: Pro Git = *Pro Git*, 2nd edition, on git-scm.com/book (1.1 About Version Control, 1.3
What is Git?, 1.6 First-Time Git Setup, 2.2 Recording Changes to the Repository).

## Level `basics-first-commit`

### Lesson

| Slide | Claim | Evidence |
|---|---|---|
| history | A version control system records changes over time; you can see what changed, who and when, and get an earlier version back | Pro Git 1.1: "records changes to a file or set of files over time so that you can recall specific versions later"; "revert ... compare changes over time, see who last modified something" |
| history | Each version you save is called a commit | gitglossary(7), commit: "used ... in the same places other revision control systems use the words 'revision' or 'version'" |
| init | `git init` creates a hidden `.git` folder where Git keeps the history | git-init(1), DESCRIPTION: "basically a .git directory with subdirectories for objects, refs/heads, refs/tags"; *re-checked*: the slide runs `ls -A` and shows `.git` |
| init | `-b main` names the first branch `main` | git-init(1), `-b`; experiment: `git symbolic-ref HEAD` gives `refs/heads/main`; *re-checked*: card `basics-init-command` |
| init | A branch is a line of development | gitglossary(7), branch: "A 'branch' is a line of development" |
| init | Without `-b`, git 2.43 uses `init.defaultBranch`, or `master` when it is not set | git-init(1), `--initial-branch`: "fall back to the default name (currently master ...; the name can be customized via the init.defaultBranch configuration variable)"; RelNotes 2.28.0 lines 107-110 (the name became configurable); experiment: no setting gives `refs/heads/master` (plus a hint on standard error), `init.defaultBranch = main` gives `refs/heads/main`; *re-checked*: card `basics-init-command` |
| areas | Three areas: working folder (working tree), staging area (index), repository | Pro Git 1.3, "the three main sections of a Git project: the working tree, the staging area, and the Git directory"; gitglossary(7), working tree, index |
| areas | A new file is untracked: in no commit and not in the staging area | Pro Git 2.2: "Untracked files are everything else ... not in your last snapshot and are not in your staging area"; git-status(1), DESCRIPTION; *re-checked*: the slide shows `git status` |
| areas | `git status` shows where each file stands | git-status(1), DESCRIPTION (index vs HEAD, working tree vs index, untracked paths) |
| nothing-staged | Committing with only an untracked file fails; a commit takes the staging area, which is empty | git-commit(1), DESCRIPTION: "containing the current contents of the index"; experiment: exit status 1, no commit made; *re-checked*: the slide's `! ` line must fail, card `basics-commit-needs-staging` |
| add | `git add` copies the file's current content into the staging area; the file stays in the folder | git-add(1), DESCRIPTION: "updates the index using the current content found in the working tree"; experiment: `git show :README.md` gives the staged content, the file is still there; *re-checked*: card `basics-add-copies` |
| add | After another edit, run `git add` again; the staging area keeps the content as it was | git-add(1), DESCRIPTION: "It only adds the content of the specified file(s) at the time the add command is run"; Pro Git 2.2; *re-checked*: card `basics-staged-version` |
| commit | A commit saves the staging area with the author's name and email, the date and the `-m` message | git-commit(1), DESCRIPTION, `-m`, COMMIT INFORMATION; experiment: `git cat-file -p HEAD` shows tree, author, committer with date, message |
| commit | Git answers with a summary that includes the short hash | experiment (shown, not quoted: the first output line holds the branch, the short hash and the message); Pro Git 2.2; *re-checked*: the slide shows the real output |
| commit | The short hash is the first characters of the hash | git-log(1), `--abbrev-commit`: "show a prefix that names the object uniquely"; gitrevisions(7), `<sha1>` |
| commit | After the commit, `git status` has nothing to report: the three areas hold the same content | gitglossary(7), clean; experiment; *re-checked*: the slide shows `git status`, test `test_the_quest_leads_to_a_solved_level` |
| log | A new commit goes on top of the one before | git-commit(1), DESCRIPTION: "The new commit is a direct child of HEAD"; experiment: `git cat-file -p HEAD` shows a `parent` line |
| log | `git log --oneline` lists commits newest first: short hash, then the message | git-log(1), `--oneline` ("--pretty=oneline --abbrev-commit"), format `oneline` (`<hash> <title-line>`), Commit Ordering ("reverse chronological order"); *re-checked*: the slide's output, card `basics-log-oneline` |

The lesson was run line by line in the lessons' environment: every line succeeds except
`! git commit -m "Add the README"` (exit status 1). Output shown on the `init` slide includes the
demonstration folder's absolute path.

### Guided quest

| Step | Claim | Evidence |
|---|---|---|
| init | `git init` creates a hidden `.git` folder where Git keeps every commit; `-b main` names the first branch | git-init(1); gitglossary(7), object database ("The objects usually live in $GIT_DIR/objects/"); *re-checked*: test `test_a_watch_step_passes_only_once_the_player_has_done_it[init]` |
| status | `git status` names the branch you are on and where each file stands | git-status(1), DESCRIPTION; experiment: output starts with the branch; the check compares with the snapshot's `branch`, never with git's text |
| file | `README.md` is the file that tells people what a project is about | docs.github.com, About READMEs: READMEs "communicate important information about your project" and typically say "What the project does" |
| file | `echo` prints a line, `>` writes it into the file, creating it | bash(1), Redirecting Output: "If the file does not exist it is created; if it does exist it is truncated to zero size" |
| file | Git sees the new file but does not track it yet | experiment (`git status` lists it as untracked); Pro Git 2.2 |
| stage | `git add` usually prints nothing | experiment: empty output; git-add(1), `-v` ("Be verbose") |
| stage | The file is still in the working folder: `git add` copies, it does not move | experiment; git-add(1), DESCRIPTION |
| name | Every commit records who made it, with a name and an email | git-commit(1), COMMIT INFORMATION; experiment: `git cat-file -p HEAD` |
| name | Quotes keep a name with spaces one value | bash(1), QUOTING |
| name | `--global` means for every repository of yours on this computer | git-config(1), `--global` ("write to global ~/.gitconfig file") and FILES ("User-specific configuration files ... also called 'global'"); Pro Git 1.6: "Git will always use that information for your user on that system" |
| name | Inside the game, `--global` writes the game's own settings file, not your real one | git(1), GIT_CONFIG_GLOBAL ("if GIT_CONFIG_GLOBAL is set, neither $HOME/.gitconfig nor $XDG_CONFIG_HOME/git/config will be read"); RelNotes 2.32.0 lines 88-93; DESIGN.md section 6 and `gitcmd.isolation`; experiment: with `GIT_CONFIG_GLOBAL` set, `git config --global` wrote that file and created no `~/.gitconfig` |
| name | If the name was set earlier in the game, the step passes at once | the game's settings file persists in the game home (`save.py`); *re-checked*: the watch reads `git config --get` |
| commit | `-m` gives the message | git-commit(1), `-m` |
| hash | Each line of `git log --oneline` is one commit, newest first: short hash, then message | as the `log` slide |
| hash | The full hash has 40 characters here | gitglossary(7), object name ("usually represented by a 40 character hexadecimal string"); experiment: `git rev-parse HEAD` is 40 characters |
| hash | Git accepts the short form as long as no other object's hash starts the same way | gitrevisions(7), `<sha1>`: "a leading substring that is unique within the repository" |

Watch and answer checks read `kit.snapshot(lab.project)` and `git config --get` (meant for
scripts) only. Each step's check fails before the player's action and passes after it
(*re-checked* by the parametrised test and the two question tests).

### Briefing, hints and debrief

| Where | Claim | Evidence |
|---|---|---|
| briefing | Solved when a commit on `main` contains `README.md` and nothing is untracked, changed or staged | `check`; *re-checked*: the wrong-approach tests (no staging, staged only, extra untracked file, staged or unstaged edit, other branch, detached HEAD, bare repository, deleted `.git`) |
| hint 1 | `git status` names the branch and lists untracked, staged and changed files | git-status(1), DESCRIPTION; experiment |
| hint 2 | `git add` copies into the staging area, `git commit` saves the staging area | git-add(1), git-commit(1), DESCRIPTION |
| hint 3 | The four commands solve the level | *re-checked*: `test_the_quest_leads_to_a_solved_level`, `test_solve_solves_the_level_and_passes_every_step` |
| debrief | A commit records a snapshot of every staged file, not only the changed lines | git-commit(1), DESCRIPTION; Pro Git 1.3, Snapshots, Not Differences; experiment: the second commit's tree lists the unchanged `b.txt`; *re-checked*: card `basics-commit-records` |
| debrief | A commit stores author name and email, date, message and parent; the first commit has none | `git cat-file -p` on a second commit (tree, parent, author, committer, message) and on the root commit (no `parent` line); gitglossary(7), parent |
| debrief | The commit's hash is computed from all of that | gitglossary(7), object: "uniquely identified by the SHA-1 of its contents"; experiment: same files and message, committer date one second apart, different hashes |
| debrief | Unchanged files are not stored twice | Pro Git 1.3: "if files have not changed, Git doesn't store the file again, just a link to the previous identical file"; experiment: `git ls-tree` gives `b.txt` the same blob id in both commits |
| debrief | The staging area lets you split changes into focused commits | git-add(1), DESCRIPTION ("can be performed multiple times before a commit"); Pro Git 1.3, basic workflow ("selectively stage just those changes you want"); *re-checked*: card `basics-why-staging` |
| debrief | After a commit, the staging area matches it and is not emptied | experiment: `git ls-files` still lists every file, `git diff --cached --quiet` succeeds; *re-checked*: card `basics-index-after-commit` |
| debrief | Every commit carries the name and email Git is set to use | git-commit(1), COMMIT INFORMATION; *re-checked*: card `basics-identity` |
| debrief | `git config --global user.name` and `user.email` set the identity | git-config(1); Pro Git 1.6 |

## Cards (`content/cards/basics.toml`)

12 cards: 8 choice, 2 text, 2 predict; levels 7 / 4 / 1. Answer-length rules checked by script:
no right option exceeds the longest distractor by more than 15 characters, and the right option
is the longest in 1 of 8 choice cards. Every `verify` and `code` snippet passes in the lessons'
environment with `bash -c` (no `-e`), and each fails when its claim is inverted (mutation run).

| Card | Claim | Evidence |
|---|---|---|
| basics-repository-folder | History lives in a hidden `.git` folder in the project folder | git-init(1), DESCRIPTION; Pro Git 1.3; *verify* |
| basics-commit-needs-staging | Committing with nothing staged makes no commit; a new file reaches a commit only after `git add` | git-commit(1), DESCRIPTION (paths given to `git commit` "must already be known to Git") and `-a` ("new files you have not told Git about are not affected"); experiment: `git commit -m x new.txt` on an untracked file fails and makes no commit; *verify* (commit fails, `HEAD` does not resolve) |
| basics-add-copies | `git add` copies the current content; nothing is committed; a later edit needs another add | git-add(1), DESCRIPTION; *verify* |
| basics-identity | Every commit records `user.name` and `user.email` as its author; they are not a login; most commands work without them; local overrides global | git-commit(1), COMMIT INFORMATION ("This name has no effect on authentication"); experiment: `git init`, `git add` and `git status` succeed with no identity set; git-config(1), FILES ("last value found taking precedence"); experiment: global and local name set, `git config --get` returns the local one; *verify* (commit author comes from the settings) |
| basics-init-command | `git init` creates a repository; `-b main` vs `init.defaultBranch` vs `master` | git-init(1); *verify* (with `-b main` and with no settings) |
| basics-log-oneline | `--oneline` is `--pretty=oneline --abbrev-commit`, newest first | git-log(1); *verify* |
| basics-staged-not-committed | A staged change is not in `git log` until committed | git-log(1), git-commit(1); *predict* output `1` |
| basics-commit-records | A commit records the staged files' snapshot; `git show` computes changes against the parent; untracked files stay out | git-commit(1), git-show(1) DESCRIPTION ("the log message and textual diff"); Pro Git 1.3; *verify* (second commit lists the unchanged file, not the untracked one) |
| basics-why-staging | The staging area lets you choose what goes into each commit | git-add(1); Pro Git 1.3; *verify* (two files, two commits, one file each) |
| basics-staged-version | The commit holds the content staged by `git add`, not the later edit | git-add(1); Pro Git 2.2 ("the version ... as it was when you last ran the git add command is how it will go into the commit"); *verify* |
| basics-index-after-commit | After a commit the staging area still lists every tracked file and matches the commit | gitglossary(7), index; git-ls-files(1); *verify* |
| basics-commit-all-skips-new | `git commit -a` stages tracked files only; new files stay untracked | git-commit(1), `-a`: "new files you have not told Git about are not affected"; Pro Git 2.2; *predict* output `1` |

## Notes (cheat sheet in `basics.toml`)

Every statement in the notes repeats a claim above: the `.git` folder (init slide), the three
areas and their git names (areas slide), untracked files, `git add` and re-adding (add slide),
the staging area after a commit (debrief), the identity and the local override (card
`basics-identity`), and each command's one-line summary (lesson and quest).

## Left out

- Whether `git commit` fails without a configured identity: it depends on the machine (git falls
  back to `EMAIL`, then the system user name and host name; git-commit(1), COMMIT INFORMATION).
  It failed here, but the text only says to set the identity before committing.
- The usual short-hash length (seven characters here): `core.abbrev` computes it from the
  repository's size (git-config(1)), so the text says "the first characters".
- `git commit --allow-empty`: its exact behaviour (same tree as the parent) is beyond this level.
- What is inside `.git` (objects, refs): left to the `hash` chapter.
