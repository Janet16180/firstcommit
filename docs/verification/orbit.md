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
| `NO_REPOSITORY_YET`, `REFUSED`, `REFUSED_EARLIER` (`git status`, failed, no repository) | Git found no repository; `git status` works only inside one; the next mission makes this folder one | E2; the next level is `liftoff-flag`. **Fixed** like `NO_REPOSITORY`: "Git works only inside a repository" became "`git status` works only inside a repository" |
| `ANSWERED`, `ANSWERED_EARLIER` | In a repository, `git status` answers | E6. The `_EARLIER` messages (2026-10-08) say the same thing when `git status` came before the `ls`, so the goal reads right when its turn comes |
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

## A misspelled git command (added 2026-10-08)

Rule `NOT_A_GIT_COMMAND`: a failed `git <word>` whose first word is not a command git knows. Run in
the image (`firstcommit:latest`, git 2.43.0) with the game's configuration:

| What ran | Result |
|---|---|
| `git ad map.txt` in a repository | status 1; git says `ad` is not a git command and suggests similar ones |
| `git stauts` | status 1; the same, with one suggestion |
| `git ad map.txt` outside a repository | status 1: the misspelling is found before any repository is looked for |
| `git help -a` | status 0; git-help(1), `-a`: "Print all the available commands on the standard output." |
| `git --list-cmds=main` | 163 names, the rule's `GIT_COMMANDS`, compared as a set with the constant |

| Text | Claim | Evidence |
|---|---|---|
| `NOT_A_GIT_COMMAND` | Git knows no command by that name; `git help -a` lists every command Git has | the experiments above; git-help(1). The text does not quote git's message or its suggestions (AUTHORING 1, rule 4) |

The rule can only fit a word git does not know: its pattern excludes `GIT_COMMANDS` (git 2.43's
own list in the image) and `OPTIONAL_COMMANDS`. Those are git's commands that git(1) lists but
Ubuntu ships in other packages (on WSL, `git-gui` adds `gui`, `gui--askpass` and `citool`), plus
git-lfs. *Re-checked*: `tests/test_reactions.py` fails every known command with statuses 1, 128
and 129 and expects another reaction or none. It also checks that every command this machine's
`git --list-cmds=main` lists is known, which caught `gui` on WSL. An alias the player defines
would count as unknown when it fails. The game's configuration defines none.

## No editor: `core.editor = true` (added 2026-10-08)

The game's base configuration (`gitcmd.BASE_CONFIG`) sets `core.editor = true`. git-var(1),
`GIT_EDITOR`: "The order of preference is the $GIT_EDITOR environment variable, then core.editor
configuration, then $VISUAL, then $EDITOR". The player's shell drops every inherited `GIT_*`
variable, so `core.editor` wins over the player's own `VISUAL` and `EDITOR`. Run in the image
(`firstcommit:latest`, git 2.43.0) with the game's configuration plus `core.editor = true`:

| What ran | Result |
|---|---|
| bare `git commit`, no name or email set (with or without anything staged) | status 128, identity error, before any editor |
| bare `git commit`, nothing staged | status 1, nothing to commit, no editor |
| bare `git commit`, `map.txt` staged | status 1, aborted for an empty message; no commit, `map.txt` still staged |
| `git commit --amend` with no message option | status 0, the subject kept |
| `git merge other` (not a fast-forward) | status 0, a merge commit with two parents and git's message |
| `git revert HEAD~1` | status 0, `Revert "Add c"` |
| `git pull` with diverged branches, `pull.rebase` unset | status 128, git asks how to reconcile (unchanged by the editor) |
| `git pull --no-rebase` with diverged branches | status 0, a merge commit with two parents and git's message |
| `git merge side` with a conflict, then `git add` and `git commit --no-edit` | merge status 1; the commit status 0, `Merge branch 'side'` |
| `git tag -a v1` without `-m` | status 128: an annotated tag needs `-m` |

*Re-checked*: `tests/test_gitcmd.py` runs the bare commit (an `EDITOR`/`VISUAL` that would leave a
trace never runs, no commit) and the merge, revert and `--no-edit` commit in the player's shell
environment. Lessons keep failing on an editor (`GIT_EDITOR=false` in `demos.environment`), so a
lesson still has to write `--no-edit`.

| Text | Claim | Evidence |
|---|---|---|
| `NO_MESSAGE` (bare `git commit`, failed, in a repository, something staged) | No commit was made; every commit needs a message; in the game no editor opens; `-m` gives it | the table above. The rule needs something staged afterwards, since a bare commit with nothing staged fails the same way (status 1) for another reason and keeps `NOT_COMMITTED`. Lines with `-m`, `-F`, `-C`, `-c`, `--no-edit`, `--amend` and the like never get it (*re-checked*) |

## The stand-in GitHub keeps a reflog (added 2026-10-08)

`kit.setup_github` (and `kit.setup_playground`, which uses it) sets `core.logAllRefUpdates = true`
on the bare repository. git-config(1), `core.logAllRefUpdates`: "This value is true by default in
a repository that has a working directory associated with it, and false by default in a bare
repository." In the image, a fresh `git init --bare` repository has no such setting (`git config
core.logAllRefUpdates` exits 1). *Re-checked* by `tests/test_playground.py`: after a push and a
forced push back, `main@{1}` and `main@{2}` on the stand-in GitHub name the commits before.

## Spanish texts (added 2026-10-07)

The Spanish of `liftoff-aboard`, `liftoff-flag` and `cargo-first` (`levels/*_es.py`), the shared
reactions (`reactions_es.py`), the `liftoff` and `cargo` decks (`content/cards/*.es.toml`), the
game's own messages (`game.SPANISH`) and the chapters' names and blurbs (`chapters.py`).

Each Spanish text was read against its English one, claim by claim. No Spanish text makes a claim
its English text does not make, and none drops a scope ("solo dentro de un repositorio" for "only
inside a repository", "antes del primer commit" for "before the first commit"), so the evidence
recorded above for each English text covers its Spanish too. Commands, file names, options, code
spans, placeholders and verbatim commands are kept exactly; only the comments after `#` in a
verbatim block are translated. `tests/test_translations.py` checks this for every pair (code
spans, placeholders, verbatim commands, paragraph and bullet counts), and
`tests/test_levels.py` that every message a level gives on its walk has its Spanish.

Git's output stays in English: the image (`firstcommit:latest`, git 2.43.0) has no Spanish
messages for git (`/usr/share/locale/es/LC_MESSAGES/` is empty, `locale -a` lists only `C`,
`C.utf8` and `POSIX`, `LANG=C.UTF-8`). The Spanish texts never quote git, as the English ones
don't, so they hold whatever language git speaks.

Where the Spanish words it differently from a word-for-word translation:

| Text | English | Spanish | Why it says the same |
|---|---|---|---|
| `reactions.NOT_STAGED`, `NOT_COMMITTED` | "... are the usual causes" | "lo habitual es ..." | the same causes, the same hedge |
| `reactions.UNKNOWN_COMMAND` | "The shell knows no command" | "La terminal no conoce ningún comando" | the player knows the place they type in as the terminal; the claim is about the command not being found (status 127) |
| `liftoff` deck, `liftoff-status-exit-code` | "127 is what the shell gives for a command it cannot find" | "127 es lo que da la terminal cuando no encuentra el comando" | as above; bash's status 127, recorded for the English card |
| `cargo` deck, `cargo-unstage-before-commit` | "`git commit journal.txt` would commit it" | "`git commit journal.txt` haría un commit con él" | the same claim |
| `chapters.CHAPTERS["rebase"]` | "Keeping up to date" | "Al día con los demás" | a coming chapter; names the same idea |

Words: `docs/i18n-glossary.md` (neutral Latin American Spanish; Git's terms kept in English, such
as commit, push, branch and staging area). Re-read after the glossary sweep: the sweep changed
words and tenses, never a claim.

## Wave 1 of chapters 3 to 7 (added 2026-10-07)

Experiments run in the image (`firstcommit:latest`, git 2.43.0) with the game's configuration
(`init.defaultBranch = main`, `core.editor = true`, `user.useConfigOnly = true`), numbered on from
E33:

| Tag | What ran | Result |
|---|---|---|
| E34 | a new repository with `engine.cfg`, `route.txt` and `keys.txt`; `git add engine.cfg route.txt` | status 0; `A  engine.cfg`, `A  route.txt`, `?? keys.txt` |
| E35 | `git add .` there, then `git rm --cached keys.txt` | both 0; all three staged, then `keys.txt` untracked again and still in the folder |
| E36 | `git add engine.cfg nosuch.txt` | status 128; nothing new staged |
| E37 | one commit of `engine.cfg` and `route.txt`, both changed since, `keys.txt` new; `git add .`; `git status` | all three staged; git's hint for unstaging names `git restore --staged <file>...` |
| E38 | then `git restore --staged keys.txt` | status 0; `keys.txt` untracked and still in the folder; the other two still staged |
| E39 | the same with `git rm --cached keys.txt` | status 0; the same result |
| E40 | the same with `git rm keys.txt` | status 1; git refuses (the file has staged changes, use `--cached` to keep it); nothing changed |
| E41 | `rm keys.txt` (the shell), then `git restore keys.txt` | after `rm`: `AD keys.txt`; the restore exits 0 and the file is back, as staged |
| E42 | `rm keys.txt`, then `git restore --staged keys.txt`, then `git restore keys.txt` | the first restore exits 0, and the file is in no area; the second exits 1: git knows no such path |
| E44 | four commits, two of them changing `oxygen.cfg`; `git log oxygen.cfg` and `git log -- oxygen.cfg` | both exit 0 and list only those two, newest first, the commit that created the file among them |
| E45 | `git log -1` | a `commit` line with the full hash, then `Author:` and `Date:` lines, then the message |
| E46 | `git log -p -1 oxygen.cfg` | the change itself: `-O2=21`, `+O2=17` |
| E47 | `git log nosuch.txt` | status 128: git cannot tell it from a revision and suggests `--` |
| E48 | a repository with two commits next to an empty bare `../github/project.git`; `git remote add origin ../github/project.git`, then `git remote -v` | both exit 0; `-v` lists `origin` twice, `(fetch)` and `(push)`; the bare repository still has no ref |
| E49 | `git remote add origin ...` again | status 3: the remote already exists |
| E50 | `git remote set-url origin https://...`, then back to `../github/project.git` | both exit 0; `-v` shows each address in turn |
| E51 | `git remote add mothership ...`, then `git remote remove mothership` | both exit 0; `git remote` lists the names |
| E52 | GitHub with one commit, two clones; Alex (in one clone) commits a line to `notes.txt` and pushes; in the other, `git status` | `Your branch is up to date with 'origin/main'` |
| E53 | then `git fetch`, `git status` | fetch 0, `origin/main` moves to Alex's commit; status says behind `origin/main` by 1 commit and can be fast-forwarded, and suggests `git pull` |
| E54 | then `git pull`, with no name or email set | status 0, a fast-forward: `main` at Alex's commit, Alex's line in `notes.txt`; up to date again. A fast-forward makes no commit, so it needs no identity |
| E43 | `git restore --staged .` | status 0; nothing staged; the two files keep their changes in the folder, `keys.txt` untracked |

### Level `cargo-selective` (Selective cargo, 2-2)

*Re-checked* by `tests/levels/test_cargo_selective.py`: naming the two files, one at a time,
`git add .` and `git rm --cached keys.txt`, `git restore --staged` failing with 128 before the
first commit, and keys that reach a commit.

| Text | Claim | Evidence |
|---|---|---|
| card | `git add <file> <file>` stages the files named, and only those; the others stay as they are | E34; git-add(1) `<pathspec>...` |
| hints | `git add` takes several names on one line, separated by spaces | E34 |
| debrief, `LOADED`, `LOOKED` | the two files staged by name; `keys.txt` untracked in the working folder; `git add .` would have taken the keys too | E34, E35 |
| `KEYS_STAGED`, `EVERYTHING_STAGED` | `git add .` stages every file, `keys.txt` too; `git rm --cached keys.txt` takes it out and the file stays | E16, E35; git-rm(1) `--cached` |
| `NOTHING_TO_RESTORE` | as cargo-first's: `git restore --staged` fails before the first commit | E15 |
| `KEYS_COMMITTED` (lost) | a committed `keys.txt` is in the history; taking a commit back is taught later | `kit.in_history` (every ref); chapters-3-7 puts revert and reset in chapter 7 |
| `NO_REPOSITORY` | as cargo-first's | E32 |

### Level `cargo-stowaway` (Stowaway, 2-3)

*Re-checked* by `tests/levels/test_cargo_stowaway.py`: the night shift's add (a level event), both
ways to unstage, `git rm` refused, the deleted file restored from the staging area, the deleted
and unstaged file lost, `git restore --staged .`, and keys that reach a commit.

| Text | Claim | Evidence |
|---|---|---|
| card | `git restore --staged <file>` takes the file out of the staging area, back to its version in the last commit; the working folder keeps the file | E38; git-restore(1) ("restored from HEAD", "Specifying --staged will only restore the index") |
| briefing | `git add .` staged the keys with the engine and the route | E37 |
| hint 1, `LOOKED` | `git status` names the command that unstages a file | E37 |
| debrief | the last commit has no `keys.txt`, so restoring the staging area from it takes the keys out; the folder untouched, the file untracked; the other two still staged | E38; git-restore(1) |
| `RM_REFUSED` (`git rm` without `--cached`, failed) | Git refused; without `--cached`, `git rm` deletes the file from the working folder too; `git restore --staged` unstages only | E40; git-rm(1) ("remove files from the working tree and from the index", `--cached`) |
| `DELETED` | after `rm keys.txt` the file is still staged; `git restore keys.txt` copies it back from the staging area | E41; git-restore(1) ("otherwise from the index") |
| `KEYS_LOST` (lost) | in neither area and in no commit, that copy is lost; unstaging never needs deleting | E42 (the blob may linger in the object database, but nothing names it; recovering it is not taught, so the scope is "that copy") |
| `CARGO_UNSTAGED` | `git add engine.cfg route.txt` stages them again | E43, E34 |
| `KEYS_COMMITTED`, `NO_REPOSITORY` | as cargo-selective's | `kit.in_history`; E32 |

### Level `vault-recorder` (Flight recorder, 3-3)

*Re-checked* by `tests/levels/test_vault_recorder.py`: seven commits, only the first and the
culprit touch `oxygen.cfg`; the culprit's place moves between plays; whole, abbreviated and
upper-case hashes pass; the first commit, the decoy whose message names the oxygen, text that is
no hash and a hash of no commit each get their own message; the author by full or first name.

| Text | Claim | Evidence |
|---|---|---|
| card, hint 2, debrief | `git log <file>` lists only the commits that changed the file, newest first, each with hash, author, date and message | E44, E45; git-log(1) `[--] <path>...` ("Show only commits that are enough to explain how the files that match the specified paths came to be") |
| hint 1, `READ` | `git log` lists every commit newest first, with hash, author, date and message | E30, E45 |
| hint 3 | the `commit` line holds the hash, the `Author` line the name | E45 |
| `SET_UP` | the first commit created `oxygen.cfg` with the right setting | setup; E44 lists it |
| `OTHER_COMMIT` | that commit did not touch `oxygen.cfg` | the check answers it only for a commit `git log oxygen.cfg` does not list (setup) |
| `NOT_A_HASH` | at least the first 4 characters of the hash | `kit.MIN_HASH_PREFIX`; git-rev-parse(1) accepts a unique prefix of 4 or more |
| debrief | a message can say little or mislead; the changes never do | the decoy commit; E46 shows the change itself |
| scene | someone changed the setting some days ago; every commit records who changed what and when | setup's dates; E31 (author, committer) |

### Level `mothership-contact` (Make contact, 4-1)

*Re-checked* by `tests/levels/test_mothership_contact.py`: adding and listing, the mothership still
empty afterwards, a list before the add, an `https://` address fixed with `set-url`, a second add
refused with status 3, another name.

| Text | Claim | Evidence |
|---|---|---|
| card | `git remote add` gives another repository's address a short name in yours; nothing is sent | E48; git-remote(1) `add` ("Add a remote named <name> for the repository at <URL>") |
| prediction reveal, debrief | naming a remote only writes its address in your repository's configuration; nothing travels | E48 (no ref on the bare repository); git-remote(1) |
| hint 2, `LISTED` | `git remote -v` lists each remote's name with its address, once for fetching and once for pushing | E48 |
| `REMOTE_EXISTS` | `origin` already exists; `git remote set-url` changes its address | E49, E50 |
| `WRONG_URL`, `HTTPS_URL` | `set-url` points `origin` at the mothership | E50 |
| debrief | at work the address is the one GitHub shows for the project, such as `https://github.com/<you>/<project>.git`; `origin` is the usual name | GitHub's docs, "About remote repositories" (HTTPS URLs); git-clone(1) names the remote `origin` by default |

### Level `mothership-incoming` (Incoming transmission, 4-3)

*Re-checked* by `tests/levels/test_mothership_incoming.py`: Alex's push as a level event, your
`origin/main` left behind, nothing counting before the push, status, fetch, status, pull, the
second look before the fetch not counting, and a pull first.

| Text | Claim | Evidence |
|---|---|---|
| card | `git fetch` updates `origin/main`; your `main` and files stay as they are | E53; git-fetch(1) ("Fetch branches and/or tags ... from one or more other repositories"; remote-tracking branches are updated) |
| prediction reveal, `LOOKED`, hint 1 | `git status` compares your `main` with `origin/main`, which changes only when you fetch (or pull) | E52, E53; git-status(1) `--ahead-behind` (compares with the upstream branch) |
| `FETCHED`, `BEHIND`, debrief | after the fetch, `git status` says behind by one | E53 |
| hint 2, `PULLED`, debrief | `git pull` fetches again and brings Alex's commit into `main`, and Alex's line into `notes.txt` | E54; git-pull(1) ("Incorporates changes from a remote repository into the current branch ... runs git fetch") |
| scene | your repository knows only what it heard the last time it asked | E52, E53 |

### Deck `vault`

Every choice and text card carries a `verify` snippet and the predict card its `code`;
`tests/test_decks.py` runs them with bash in an empty folder with the lessons' environment, so
each claim is *re-checked* on every run of the deck tests (with this machine's git, 2.43.0 on WSL like the image's).

| Card | Claim | Evidence |
|---|---|---|
| `vault-commit-local` | a commit is only in your repository until you push | `verify`: the bare remote has no ref after the commit; git-push(1) |
| `vault-commit-takes-staged` | a commit takes the staging area only; an untracked file stays out | `verify`; git-commit(1) ("the current contents of the index") |
| `vault-log-order` | `git log` lists newest first; `--format=%s` prints the subjects | `code` and `correct`; E30 |
| `vault-diff-after-add` | a plain `git diff` compares the working folder with the staging area; `--staged` the staging area with the last commit | `verify`; git-diff(1) ("changes relative to the index", `--staged` "relative to the named <commit>", HEAD by default) |
| `vault-bare-commit` | in the game a bare `git commit` makes no commit and the file stays staged; outside, git opens an editor | `verify` with `core.editor=true`; the "No editor" section above |
| `vault-log-file` | `git log <file>` lists only the commits that changed it; `--` marks a file; `-p` and `--oneline` | `verify`; E44, E46; git-log(1) |
| `vault-short-hash` | a unique start of a hash names the commit; `--oneline` prints one long enough | `verify`; gitrevisions(7) `<sha1>` ("a leading substring that is unique within the repository") |
| notes | as the cards above, plus `-m` gives the message on the line | git-commit(1) `-m` |

### Deck `mothership`

Checked the same way as the vault deck: each `verify` snippet runs in `tests/test_decks.py`.

| Card | Claim | Evidence |
|---|---|---|
| `mothership-remote-add` | `git remote add` only names the address; nothing reaches the remote | `verify`; E48 |
| `mothership-push-commits` | an edit in no commit is not sent; the remote's `main` stays | `verify`: the remote's `main` and its `route.txt` unchanged after the push |
| `mothership-status-stale` | `git status` compares with `origin/main` as of the last fetch, so it says up to date until a fetch | `verify` (counted with `git rev-list`, not git's wording); E52, E53 |
| `mothership-fetch-changes` | `git fetch` moves `origin/main`; `main` and the files stay; `git pull` brings the commits in | `verify`; E53, E54 |
| `mothership-push-upstream` | `git push -u origin main` records `origin/main` as the upstream; `--set-upstream` is the long name | `verify`; git-push(1) `-u, --set-upstream` |
| `mothership-refused-push` | a refused push changes nothing here or on the remote; pull first, then push | `verify`: both tips unchanged; git-push(1) NOTE ABOUT FAST-FORWARDS |
| notes | as the cards above; a remote is GitHub at work and a folder in the game | `Lab.github_url`; the cards |

## The player signs as Cadet (added 2026-10-07)

`gitcmd.BASE_CONFIG` sets `user.name = Cadet` and `user.email = cadet@example.com` and keeps
`user.useConfigOnly = true`; `gitcmd.ensure_config` adds both to an older game config that has
neither. *Re-checked* by `tests/test_gitcmd.py`: a commit in the player's shell is by
`Cadet <cadet@example.com>`; after `git config --global user.name` and `user.email` in that shell
(they write the game's config, E22), the next commit is by the player's name; an older config is
signed once and keeps its other settings; one with only a name is left alone. With the identity
unset (the playground tests), a commit still stops as before (E21).
