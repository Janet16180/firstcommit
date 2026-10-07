# Verification log: Orbit

How every claim in the Orbit records and levels was checked. These are the three levels
`liftoff-aboard`, `liftoff-flag` and `cargo-first`, Rama's shared reactions
(`firstcommit.reactions`), the template level's scene, card and reactions, and the chapter blurbs.
Target: git 2.43.0 on Ubuntu 24.04.5, inside the game's Docker image (`firstcommit:latest`),
checked on 2026-10-07.

**Method.** The experiments ran as one bash script in the image (`docker run --entrypoint bash
firstcommit:latest`), as its `player` user, with the game's isolation: `GIT_CONFIG_GLOBAL`
pointing at a copy of `gitcmd.BASE_CONFIG`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CEILING_DIRECTORIES`
set to the scratch folder, `LC_ALL=C` and `GIT_PAGER=cat`. Each result below is tagged E1 to
E33, in the order the script ran them. Man pages are the installed 2.43 pages, quoted with
`man -P cat <page> | grep -n`. Claims marked *re-checked* run on every test run. The tests run
the level's lines through `kit.type_line` (bash, with the game's git) in
`tests/levels/test_<level>.py`, or through the shared rule tests in `tests/test_reactions.py`.
The image has no man pages, so the pages were read on WSL's git 2.43.0, the same version.

Words follow AUTHORING section 7: working folder, staging area, repository, commit. No text quotes
git's messages; where git's wording matters (status sections, hints), the experiment only counts
the section, and the text describes it.

## Results of the experiments

| Tag | What ran | Result |
|---|---|---|
| E1 | `ls` in a plain folder holding `map.txt` and `journal.txt` | status 0, lists both |
| E2 | `git status`, `add`, `commit`, `log`, `restore`, `branch`, `switch`, `push`, `pull`, `fetch`, `remote` outside any repository | every one exits 128 |
| E3 | the folder after E2 | only the two files: no `.git` was made |
| E4 | `ls -a` before `git init` | `. .. journal.txt map.txt` |
| E5 | `git init`, then `ls`, `ls -a`, `ls -A` | init exits 0; `ls` hides `.git`, `ls -a` and `ls -A` show it; branch `main` (`init.defaultBranch` in the game's config) |
| E6 | `git status` in the new repository | status 0 |
| E7 | `git int` (a typo) | status 1, and no other change |
| E8 | `gti status`, `lss` | status 127, bash's "command not found" |
| E9 | `git status --short` in the new repository | `?? journal.txt`, `?? map.txt` |
| E10 | `git add mapa.txt` (misspelled) | status 128, nothing staged |
| E11 | `git add map.txt nope.txt` | status 128, nothing staged, not even `map.txt` |
| E12 | `git add` with no name | status 0, nothing staged |
| E13 | `git add map.txt` | `A  map.txt`, `?? journal.txt` |
| E14 | `git status` after E13 | one section of changes to be committed, one of untracked files |
| E15 | `git restore --staged map.txt` before the first commit | status 128; `map.txt` stays staged |
| E16 | `git add .` | both files staged |
| E17 | `git rm --cached journal.txt` | status 0; `journal.txt` untracked again, still in the folder |
| E18 | `git status` before the first commit, with a file staged | its hint for unstaging names `git rm --cached` |
| E19 | `git add map.txt` again, the file unchanged | status 0; the `git ls-files -s` entries are the same before and after (compared on WSL's git 2.43.0) |
| E20 | `git add .` from the subfolder `sub/` | stages `sub/a.txt` only; `top.txt` stays untracked |
| E21 | `git commit -m Map` with no name or email set (`user.useConfigOnly`) | status 128, no commit |
| E22 | `git config --global user.name "Robin Park"` | written to the game's config (`GIT_CONFIG_GLOBAL`) |
| E23 | `git commit -q -m 'Add the map'` | status 0; `git log --oneline` lists it with its short hash and message; author Robin Park |
| E24 | `git commit -m again` with nothing new staged | status 1, no commit; the staging area still holds `map.txt` (it is not emptied) |
| E25 | `echo 'Phobos stop' >> map.txt` | ` M map.txt`; the staged id is still HEAD's |
| E26 | stage, change the file again, commit | the commit holds the staged version, the folder keeps the newer one |
| E27 | `git restore map.txt` after an unstaged change | status 0; the folder's change is gone, back to the staged version |
| E28 | `git restore --staged map.txt` after a commit | status 0; the staging area matches HEAD again; the folder keeps its change |
| E29 | `git init` in a repository with two commits | status 0; HEAD and both commits unchanged |
| E30 | `git log` | newest commit first |
| E31 | `git cat-file -p HEAD` | `tree`, `parent`, `author`, `committer` (and the message) |
| E32 | `rm -rf .git`, then `git log` and `git status` | both exit 128 |
| E33 | the folder after E32 | no other object database: the history was only in `.git` |

Man pages: git-init(1) DESCRIPTION, "Running git init in an existing repository is safe. It will
not overwrite things that are already there." git-restore(1), "If neither option is specified,
by default the working tree is restored. Specifying --staged will only restore the index", and
"By default, if --staged is given, the contents are restored from HEAD, otherwise from the index."
git-rm(1) `--cached`: "Use this option to unstage and remove paths only from the index. Working
tree files, whether modified or not, will be left alone." git-log(1), "By default, the commits are
shown in reverse chronological order." git-status(1) DESCRIPTION, "Displays paths that have
differences between the index file and the current HEAD commit, paths that have differences
between the working tree and the index file, and paths in the working tree that are not tracked".
git-commit(1), "Create a new commit containing the current contents of the index and the given
log message". ls(1), `-a`: "do not ignore entries starting with ."; `-A`: "do not list implied .
and ..". bash(1), COMMAND EXECUTION: a command that is not found "returns a status of 127".

## Shared reactions (`firstcommit.reactions.RULES`)

Each rule fires only on its line, outcome, change and repository, so a claim needs to hold only
in that case. *Re-checked*: `tests/test_reactions.py` (which rule fits which line) and, for real
exit statuses, the level tests below.

| Text | Claim | Evidence |
|---|---|---|
| `REPOSITORY_GONE` (event `repository-removed`) | The repository is gone, with its history; Git kept all of it in `.git` | E32, E33 |
| `NEW_REPOSITORY` (`git init`, event `repository-created`) | `git init` made the hidden `.git` folder, where it keeps the history; `ls -a` shows it | E5; git-init(1) |
| `INIT_AGAIN` (`git init`, ok, in a repository) | Running `git init` again is safe and overwrites nothing | E29; git-init(1) |
| `NO_REPOSITORY` (the commands of `NEEDS_REPOSITORY`, failed, no repository) | This command works only inside a repository; `git init` makes this folder one | E2 (all eleven exit 128 outside a repository), E5. **Fixed**: it said "Git works only in a folder it knows", but `git init`, `git clone` and `git config` work anywhere |
| `STATUS` (`git status`, ok) | It lists what is staged, what changed in the working folder since, and the untracked files | git-status(1); E9, E13, E25 |
| `UNSTAGED` (`git restore --staged` or `git rm --cached`, event `file-unstaged`) | Out of the staging area: the next commit will not take that change | E28 (after a commit), E17 (before one); `git rm --cached` of a new file is told as `file-unstaged` (checked with `changes.describe`), while on a committed file it stages a deletion, which is `file-staged`, so the rule does not fire there |
| `RESTORED` (`git restore`, event `file-changed`) | It replaced the file in the working folder; the unstaged changes there are gone | E27; git-restore(1) |
| `STAGED` (`git add`, event `file-staged`) | The next commit takes the file as it is now; change it again and you stage it again | E26; git-add(1) |
| `NOTHING_NEW` (`git add <names>`, ok, nothing staged) | The staging area already matched | E19 |
| `ADD_WHAT` (`git add` alone) | It needs a name, or `.` for everything in this folder and the folders inside it | E12 (exit 0, nothing staged), E20 |
| `NOT_STAGED` (`git add`, failed, in a repository) | Nothing was staged; a name git does not find is the usual cause | E10, E11 (one bad name stages none of the names) |
| `COMMITTED` (`git commit`, event `commit-created`) | A new commit with its own hash and the message; `git log --oneline` lists it | E23 |
| `NOT_COMMITTED` (`git commit`, failed, in a repository) | No commit; nothing new staged or no name and email are the usual causes | E21, E24. **Fixed**: it said "an empty staging area", but after a commit the staging area is not empty (E24), it only holds nothing new |
| `LOG` (`git log`, ok) | Newest commit first; each records its author, date and message, and is named by its hash | E30, E31; git-log(1) |
| `HIDDEN_GIT` (`LIST_HIDDEN`, ok, in a repository) | `.git` is the repository and holds the whole history; a plain `ls` hides dot names | E5, E33; ls(1). `LIST_HIDDEN` matches `-a`, `-A`, `-la`, `--all`, `--almost-all` (*re-checked*) |
| `LS_IN_REPOSITORY` (`ls`, ok, in a repository) | `ls` lists the working folder; `git status` tells which files changed and which are untracked | E1, E9, E25. **Fixed**: it said `git status` tells "which of these files Git tracks", but it never lists unchanged tracked files |
| `LS_NO_REPOSITORY` (`ls`, ok, no repository) | Plain files: Git keeps no history of them yet | E1, E3 |
| `DID_YOU_MEAN_GIT`, `UNKNOWN_COMMAND` (status 127) | The shell knows no command by that name; Tab completes command names | E8; bash(1); completion of the first word is bash's readline (the game's shell also loads bash-completion, `commands.COMPLETION`) |
| `NEW_FILE` (`echo`, `printf`, `touch`, `cat`, `cp`, event `file-created`, in a repository) | Git does not track it yet; `git status` lists it as untracked until `git add` | E9, E13 |
| `CHANGED_FILE` (`echo`, `printf`, `cat`, `sed`, event `file-changed`, in a repository) | What is staged stays as it was until the file is added again | E25 |

## Level `basics-first-commit`: the new records

| Text | Claim | Evidence |
|---|---|---|
| scene `planet` | The `project` folder is a plain folder; Git keeps no history of it yet | the level's `setup` makes an empty folder; *re-checked* by its tests |
| scene `flag` | `git init` makes it a repository, creating the hidden `.git` that keeps the history | E5; git-init(1) |
| scene `zones` | `git add` copies a file into the staging area; `git commit` saves the staging area as a commit | git-add(1); git-commit(1); E23 |
| card `git commit -m "Message"` | Saves what is in the staging area as a new commit, with your message | git-commit(1); E26 |
| reactions on `git config --global user.name|email <value>` | Git puts this name (email) on the commits you make here | E22, E23 (the author is the configured name); a line without a value only reads the setting and gets no reaction (*re-checked*) |

## Level `liftoff-aboard` (Welcome aboard, design 1-1)

*Re-checked* by `tests/levels/test_liftoff_aboard.py`: the real exit statuses of `ls` (0) and
`git status` (128) in the level's folder, and a whole play through the game's API.

| Text | Claim | Evidence |
|---|---|---|
| card `ls` | Lists the files in the folder; `ls -a` lists the hidden ones too, whose names start with a dot | ls(1); E4, E5 |
| scene `timeline` | Git saves a snapshot of the project each time you ask, and you can go back to any you saved | git-commit(1) (a commit records the index's contents); Pro Git 1.3 ("a series of snapshots") |
| scene `terminal` | Mistakes are safe: this is a practice folder | the level runs in its own lab under the game home (AUTHORING 3.2) |
| briefing, `LISTED` | The terminal opens in `project`, holding `map.txt` and `journal.txt`, which no repository keeps | `kit.Lab.project`; the level's `setup`; E1, E3 |
| `NO_REPOSITORY_YET`, `REFUSED` (`git status`, failed, no repository) | Git found no repository; `git status` works only inside one; the next mission makes this folder one | E2; the next level is `liftoff-flag`. **Fixed** like `NO_REPOSITORY`: "Git works only inside a repository" became "`git status` works only inside a repository" |
| debrief | `git status`, like most Git commands, works only inside a repository; here it stopped with an error and changed nothing | E2, E3. **Fixed**: it said "Git works only inside a repository", unscoped |

## Level `liftoff-flag` (Plant the flag, design 1-2)

*Re-checked* by `tests/levels/test_liftoff_flag.py`: `git init` then `ls -a` then `git status`
all exit 0; `git status` before `git init` exits 128; `git int` makes no repository.

| Text | Claim | Evidence |
|---|---|---|
| card, scene `flag` | `git init` makes the folder a repository and creates the hidden `.git` folder | E5; git-init(1) |
| scene `flag` | `.git` holds the whole history, so never delete it | E32, E33 |
| hint | Names that start with a dot are hidden; `ls -a` shows them | ls(1); E4, E5 |
| `WORKS`, step | `git status` works once the folder is a repository | E6 versus E2 |
| goal `hidden` | An `ls -a` counts only after the last `git init` that worked | E4 (before `git init`, there is no `.git` to see) |
| debrief | From now on the repository and every commit made in it live in `.git` | E31, E33 |

## Level `cargo-first` (First cargo, design 2-1)

*Re-checked* by `tests/levels/test_cargo_first.py`: the misspelled `git add mapa.txt` (128,
nothing staged), `git add .` (both staged), `git rm --cached journal.txt` (back to untracked, the
file kept), and `git restore --staged` failing with 128 before the first commit.

| Text | Claim | Evidence |
|---|---|---|
| card | `git add` copies a file, as it is now, into the staging area for the next commit | git-add(1); E26 |
| scene `zones` | Three places on your computer: the working folder, the staging area and the repository | AUTHORING 7's words; the template level's lesson |
| scene `conveyor` | When a file is ready, `git add` puts a copy of it in the staging area | E13 (the file stays in the folder) |
| setup | A new repository whose two files are untracked | E9; *re-checked* |
| hint, debrief, `LOOKED` | `git status` lists `map.txt` as staged for the next commit and `journal.txt` as untracked; a plain `git commit` takes what is staged and leaves the rest | E13, E14, E26 |
| `TOO_MUCH`, `EVERYTHING_STAGED` | `git add .` staged the journal too; `git rm --cached journal.txt` takes it back out and the file stays | E16, E17, E18; git-rm(1). **Fixed**: they first said `git restore --staged journal.txt`, which fails before the first commit (E15) |
| `NOTHING_TO_RESTORE` (`git restore --staged`, failed, in a repository) | `git restore --staged` puts back the last commit's version, and there is no commit yet; before the first commit, `git rm --cached` unstages and keeps the file | git-restore(1) ("restored from HEAD"); E15, E17. Added after the finding above |
| `NO_REPOSITORY` | With `.git` gone the folder is no longer a repository; starting the level again rebuilds it | E32; `game.start` builds a fresh lab (`runner.start_lab`) |

## Chapter blurbs (`firstcommit.chapters.BLURBS`)

| Chapter | Claim | Evidence |
|---|---|---|
| `liftoff` | What a repository is, and how one starts | the chapter's two levels |
| `cargo` | The staging area: you choose what goes into the next commit | git-commit(1); E13, E26 |
| `start` | What Git and GitHub are, and a first clone | DESIGN.md section 4, chapter `start` |
| `basics` | The working folder, the staging area and the first commits | `basics-first-commit` |
| `hash` | Git names every file and commit by its content | gitglossary(7), object ("uniquely identified by the SHA-1 of its contents"; files are blobs, commits are commit objects); DESIGN.md section 4 (the `hash-object` experiment) |
| `history` | What changed, when, and who changed it | git-log(1); DESIGN.md (`log`, `show`, `diff`, `blame`) |
| `undo` | Take a change back without losing work | DESIGN.md (`restore`, `revert`, `reflog` as a safety net); a promise about the chapter, to re-check when it is written |
| `branch` | Branches are names for commits | gitglossary(7), branch ("The tip of the branch is referenced by a branch head"); DESIGN.md |
| `conflict` | When two changes touch the same part of a file, and how to settle it | git-merge(1), HOW CONFLICTS ARE PRESENTED; experiment on WSL's git 2.43.0: one branch changes line 2, the other line 3, and `git merge` stops with a conflict (status 1). **Fixed**: "the same lines" was too narrow, since changes to neighbouring lines conflict too |
| `remote`, `rebase`, `github`, `hygiene`, `setup`, `toolbox` | What each chapter covers | DESIGN.md section 4, the chapters table; promises about chapters, to re-check when they are written |

## Decks `liftoff` and `cargo` (added 2026-10-07)

Every card but one text card has a `verify` snippet or is a `predict` card, so its claim is
*re-checked* on every test run by `tests/test_decks.py`, in the lessons' fixed environment. The
snippets were also run in the image (`firstcommit:latest`, git 2.43.0, with the game's
configuration): every `verify` holds and both `predict` cards print their right option. Each
`verify` was then inverted (its last line negated) and failed, so none passes by accident. The
experiments E1-E33 above back the explanations.

| Card | Claim | Evidence |
|---|---|---|
| `liftoff-ls-lists` | A plain `ls` lists the folder's names and leaves out the hidden ones | ls(1); E1, E4; `verify` |
| `liftoff-status-outside` | `git status` fails in a plain folder and creates nothing; only inside a repository are files listed as untracked | E2, E3, E9; `verify` |
| `liftoff-status-exit-code` | It prints `128`; 127 is the shell's status for a command it cannot find | E2, E8; bash(1); the `predict` code |
| `liftoff-init-creates` | `git init` creates `.git` and no commit, and leaves the files as they are | git-init(1); E5; `verify` |
| `liftoff-hidden-option` | `ls -a` lists dot names with `.` and `..`, `ls -A` without them | ls(1); E4, E5; `verify` |
| `liftoff-init-again` | `git init` again keeps the commits and the files | git-init(1); E29; `verify` |
| `cargo-add-copies` | After `git add`, the file is in the working folder and the staging area, and no commit is made | git-add(1); E13, E26; `verify` |
| `cargo-status-short` | `git status --short` prints `A  map.txt` then `?? journal.txt`; the first column is the staging area, the second the working folder | git-status(1), Short Format ("X shows the status of the index, and Y shows the status of the work tree"); E13; the `predict` code |
| `cargo-add-misspelled` | A name that matches no file stops `git add`, nothing is staged, other names on the line included, and no file is created | E10, E11; `verify` |
| `cargo-unstage-before-commit` | Before the first commit, `git rm --cached` unstages and keeps the file; `git restore --staged` fails then; `git status` suggests `git rm --cached` | git-rm(1), git-restore(1); E15, E17, E18; `verify`. **Fixed** before it shipped: the explanation said a plain `git rm` would delete the file. On WSL's git 2.43.0, `git rm journal.txt` on a newly staged file refuses (status 1, the file and the staging area unchanged), and only `-f` deletes it |
