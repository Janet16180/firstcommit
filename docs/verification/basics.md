# Verification log: basics

How every claim in the `basics` chapter was checked. Target: git 2.43.0 (Ubuntu 24.04 package),
checked on WSL on 2026-10-06.

**Method.** Man pages are the installed 2.43 pages, quoted with `man -P cat <page> | grep -n`.
Experiments ran in a scratch folder with `GIT_CONFIG_GLOBAL` pointing at a scratch file holding
`gitcmd.BASE_CONFIG`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CEILING_DIRECTORIES` set to the scratch
folder, `LC_ALL=C`, and a fixed identity and date (the lessons' environment). Terminal output was
checked on a real pseudo-terminal (`script -qc "<command>" /dev/null` with `GIT_PAGER=cat`), not
only through a pipe (AUTHORING section 1, rule 10). Claims marked *re-checked* are re-run on every
test run: by the lesson's `run` lines, a card's `verify` or `code`, or a test in
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
| init | A new repository has no commits yet, but you are already on its first branch | git-init(1), DESCRIPTION: "An initial branch without any commits will be created"; experiment: `git rev-parse --verify HEAD` fails, `git symbolic-ref HEAD` gives `refs/heads/main` and `git status` names `main`, but `git branch` lists nothing and `git rev-parse --verify -q main` fails until the first commit, so the text no longer says the repository "starts with one branch" (fact-check 2) |
| init | A branch is a line of development | gitglossary(7), branch: "A 'branch' is a line of development" |
| init | The game sets `init.defaultBranch` to `main`, so in the game a new repository's first branch is `main` | `gitcmd.BASE_CONFIG` (the game's starting global configuration, written by `game.start` and used by lessons, cards and the player's shell); git-init(1), `--initial-branch` ("the name can be customized via the init.defaultBranch configuration variable"); RelNotes 2.28.0 lines 107-110; experiment: with that file as the global configuration, `git init` gives `refs/heads/main`; *re-checked*: the lesson runs plain `git init`, card `basics-init-command`, test `test_plain_git_init_starts_on_main_with_the_games_starting_settings` |
| areas | Three areas: working folder (working tree), staging area (index), repository | Pro Git 1.3, "the three main sections of a Git project: the working tree, the staging area, and the Git directory"; gitglossary(7), working tree, index |
| areas | A new file is untracked: in no commit and not in the staging area | Pro Git 2.2: "Untracked files are everything else ... not in your last snapshot and are not in your staging area"; git-status(1), DESCRIPTION; *re-checked*: the slide shows `git status` |
| areas | `git status` lists the files that are untracked, staged, or changed but not staged | git-status(1), DESCRIPTION (paths that differ between the index and HEAD, between the working tree and the index, and untracked paths that are not ignored); experiment: an unchanged tracked file and an ignored file are not listed |
| nothing-staged | With only an untracked file, committing fails; a plain `git commit` takes the staging area, which is empty | git-commit(1), DESCRIPTION: "containing the current contents of the index"; experiment: exit status 1, no commit made; *re-checked*: the slide's `! ` line must fail, card `basics-commit-needs-staging` |
| add | `git add` copies the file's current content into the staging area; the file stays in the folder | git-add(1), DESCRIPTION: "updates the index using the current content found in the working tree"; experiment: `git show :README.md` gives the staged content, the file is still there; *re-checked*: card `basics-add-copies` |
| add | After another edit, the staging area keeps the old content; `git add` again stages the new one | git-add(1), DESCRIPTION: "It only adds the content of the specified file(s) at the time the add command is run"; Pro Git 2.2; *re-checked*: card `basics-staged-version` |
| commit | A plain `git commit` saves the staging area with the author's name and email, the date and the `-m` message | git-commit(1), DESCRIPTION, `-m`, COMMIT INFORMATION; experiment: `git cat-file -p HEAD` shows tree, author, committer with date, message |
| commit | Git answers with a summary that includes the short hash | experiment (shown, not quoted: the first output line holds the branch, the short hash and the message); Pro Git 2.2; *re-checked*: the slide shows the real output |
| commit | The short hash is the first characters of the hash | git-log(1), `--abbrev-commit`: "show a prefix that names the object uniquely"; gitrevisions(7), `<sha1>` |
| commit | After this commit, `git status` lists no files (it still names the branch): the three areas hold the same content | gitglossary(7), clean; experiment; *re-checked*: the slide shows `git status`, test `test_the_quest_leads_to_a_solved_level` |
| log | A new commit goes on top of the last one, which Git records as its parent | git-commit(1), DESCRIPTION: "The new commit is a direct child of HEAD"; experiment: `git cat-file -p HEAD` shows a `parent` line; gitglossary(7), parent |
| log | `git log --oneline` lists commits newest first, one per line: short hash, then the message | git-log(1), `--oneline` ("--pretty=oneline --abbrev-commit"), format `oneline` (`<hash> <title-line>`), Commit Ordering ("reverse chronological order"); *re-checked*: the slide's output, card `basics-log-oneline` |
| log | On a terminal, the newest line also shows `(HEAD -> main)` between the hash and the message | git-log(1), `--decorate`: "If auto is specified, then if the output is going to a terminal, the ref names are shown as if short were given ... Default to configuration value of log.decorate if configured, otherwise, auto"; RelNotes 2.13.0 lines 176-177; experiment on a pseudo-terminal: `fecf61d (HEAD -> main) First`, and through a pipe `fecf61d First`; *re-checked*: lesson transcripts use `log.decorate=short` (`demos.TERMINAL_CONFIG`), and the slide shows `ef6e967 (HEAD -> main) Add the first rule` (fact-check 2, after merging phase-2-engine 2166fc6) |

The lesson was run through the real `demos.frames` on the merged branch: every line succeeds
except `! git commit -m "Add the README"`, the `init` output reads `/home/you/project/.git/`, and
each slide's map shows the README in the expected areas. Every card snippet also passes in the
real `demos.environment`.

The quest was played end to end through the real game layer (`game.start`, `game.quest_step`,
`game.check`), with the player's commands run as plain `git` in `gitcmd.shell_environment` and
no identity variables, as in the page's terminal: each step refused its answer or action before
and accepted it after, every nudge read as intended (wrong branch, wrong case, example name,
message instead of hash, extra untracked file), and the level paid 100 XP once solved.

### Guided quest

| Step | Claim | Evidence |
|---|---|---|
| init | `git init` creates a hidden `.git` folder where Git keeps the project's commits; its first branch is `main`, the game's default | git-init(1); gitglossary(7), object database ("The objects usually live in $GIT_DIR/objects/"); as the `init` slide; *re-checked*: the harness's quest walk (`QUEST_ACTIONS["init"]` runs plain `git init`) |
| status | `git status` names the branch and lists the files that are untracked, staged, or changed but not staged | git-status(1), DESCRIPTION; experiment: output starts with the branch; the check compares with the snapshot's `branch`, never with git's text |
| file | `README.md` is the file that tells people what a project is about | docs.github.com, About READMEs: READMEs "communicate important information about your project" and typically say "What the project does" |
| file | `echo` prints a line; `>` creates the file, or replaces everything in it if it exists | bash(1), Redirecting Output: "If the file does not exist it is created; if it does exist it is truncated to zero size" |
| file | Git sees the new file but does not track it yet | experiment (`git status` lists it as untracked); Pro Git 2.2 |
| stage | A new file gets into a commit only through the staging area | git-commit(1): listed paths "must already be known to Git", `-a`: "new files you have not told Git about are not affected"; experiment: `git commit -m x new.txt` and `git commit -i -m x new.txt` on an untracked file both fail and make no commit |
| stage | `git add` usually prints nothing | experiment: empty output; git-add(1), `-v` ("Be verbose") |
| stage | The file is still in the working folder: `git add` copies, it does not move | experiment; git-add(1), DESCRIPTION |
| name | Every commit records who made it, with a name and an email | git-commit(1), COMMIT INFORMATION; experiment: `git cat-file -p HEAD` |
| name | Quotes keep a name with spaces one value | bash(1), QUOTING |
| name | `--global` means for all your repositories on this computer, unless one sets its own | git-config(1), `--global` ("write to global ~/.gitconfig file") and FILES ("User-specific configuration files ... also called 'global'"; "last value found taking precedence", the repository file read last); Pro Git 1.6; experiment: a local `user.name` wins over the global one |
| name | Inside the game, `--global` writes the game's own settings file, not your real one | git(1), GIT_CONFIG_GLOBAL ("if GIT_CONFIG_GLOBAL is set, neither $HOME/.gitconfig nor $XDG_CONFIG_HOME/git/config will be read"); RelNotes 2.32.0 lines 88-93; DESIGN.md section 6 and `gitcmd.isolation`; experiment: with `GIT_CONFIG_GLOBAL` set, `git config --global` wrote that file and created no `~/.gitconfig` |
| name | If the name was set earlier in the game, the step passes at once | the game's settings file persists in the game home (`save.ensure_gitconfig` never overwrites it); *re-checked*: the watch reads `git config --get` |
| name, email | The suggested commands are complete: `git config --global user.name "Your Name"`, `git config --global user.email you@example.com` | AUTHORING section 1, rule 9; experiment: without a value, `git config --global user.name` only reads (exit status 1 when unset); *re-checked*: `test_a_missing_identity_gets_a_complete_command_to_set_it`, and the steps' `command` and the watch messages share `NAME_COMMAND` and `EMAIL_COMMAND` |
| commit | `-m` gives the message | git-commit(1), `-m` |
| hash | Each line of `git log --oneline` is one commit, newest first: short hash, then message; on the terminal the newest line shows `(HEAD -> main)` | as the `log` slide |
| hash | The full hash has 40 characters here | gitglossary(7), object name ("usually represented by a 40 character hexadecimal string"); experiment: `git rev-parse HEAD` is 40 characters |
| hash | Commands such as `git show` accept the short form, as long as no other object's hash starts the same way | gitrevisions(7), `<sha1>`: "a leading substring that is unique within the repository"; experiment: `git show <short hash>` shows the commit, while `git fetch <repository> <short hash>` fails (exit 128) and needs the full hash, so the text gives `git show` as its example instead of saying "wherever" |

Watch and answer checks read `kit.snapshot(lab.project)` and `git config --get` (meant for
scripts) only. Each step's check fails before the player's action and passes after it
(*re-checked* by the harness's quest walk over `QUEST_ACTIONS`, and by the level's own question
tests).

### Feedback messages

| Message | Claim | Evidence |
|---|---|---|
| detached HEAD, `main` exists | `git switch main` goes back to `main` | experiment; RelNotes 2.23.0 line 61 (`git switch`); *re-checked*: `test_a_detached_head_does_not_solve_the_level` |
| detached HEAD, no `main` | `git switch -c main` creates `main` at the current commit | experiment: on a repository that only had `master`, `git switch main` fails (exit 128) and `git switch -c main` works; *re-checked*: `test_a_detached_head_without_main_gets_the_command_that_creates_it` |
| other branch, `main` exists | `git switch main` | experiment: `git branch -m main` fails when `main` exists (exit 128); switching works, also from an unborn branch; *re-checked*: `test_another_branch_while_main_exists_gets_the_switch_command` |
| other branch, no `main` | `git branch -m main` renames the current branch, born or unborn | experiment (unborn `master` and `master` with a commit); *re-checked*: `test_a_repository_on_another_branch_gets_the_rename_command` |
| untracked file | It is in the working folder but not in the staging area; stage and commit it, or delete it | git-status(1); experiment: after `git rm --cached README.md` the file is untracked though still in the last commit, so the message does not say "in no commit" |
| file not staged | A new file gets into a commit only once it is staged | as the `stage` step |
| solved, commit step | "Your last commit contains `README.md`" | the check reads the last commit (`head` in the snapshot), not the first one |
| `git init project` inside `project` | `git init project` creates that folder | git-init(1), DESCRIPTION: "If this directory does not exist, it will be created"; *re-checked*: `test_git_init_project_inside_the_project_folder_gets_its_own_nudge` |
| repository inside `project` | `git status` lists a folder with its own repository as untracked | experiment: `git init project` inside the solved repository gives `?? project/` in `git status --porcelain`; *re-checked*: `test_a_repository_inside_the_project_folder_keeps_the_level_unsolved` |
| something only `git status` lists | Staging and committing clears it | experiment: after `chmod 755 README.md`, `git status --porcelain` gives ` M README.md`; `git add` then `git commit` leave it clean; *re-checked*: `test_a_changed_file_mode_keeps_the_level_unsolved` |
| commit step | `git commit -m "Add the README"`, the complete command (a bare `git commit` opens an editor) | git-commit(1), `-m` and ENVIRONMENT AND CONFIGURATION VARIABLES ("The editor used to edit the commit log message"); experiment: with `GIT_EDITOR` set to a script, a bare `git commit` runs it; *re-checked*: `test_staging_without_committing_leaves_the_level_unsolved` |
| status question, wrong case | Type the name with the same capital and small letters | no claim about case-sensitivity: branches can be stored as files under `.git/refs` (gitrepository-layout(5), refs), and git-config(1), `core.ignoreCase`, names file systems that are not case sensitive (APFS, NTFS), so whether `Main` and `main` differ depends on the file system (not observable on this machine); *re-checked*: `test_a_branch_name_in_the_wrong_case_gets_a_hint_about_case` |
| hash question, too short | Git needs at least 4 characters of a hash | git-rev-parse(1), `--short`: "The minimum length is 4"; experiment: `git show <3 characters>` fails (exit 128), 4 characters show the commit; `kit.MIN_HASH_PREFIX`; *re-checked*: `test_a_hash_start_shorter_than_git_accepts_is_not_called_wrong` |
| hash question, whole line | The short hash is the first word of the line | as the `log` slide; *re-checked*: `test_the_whole_log_line_gets_a_nudge_to_type_only_the_hash` |

### Briefing, hints and debrief

| Where | Claim | Evidence |
|---|---|---|
| briefing | Solved when the last commit on `main` contains `README.md` and `git status` lists nothing untracked, changed or staged | `check` reads the last commit (`head` in the snapshot), then `git status --porcelain=v2` for what the snapshot leaves out (a nested repository, a file mode change); git-status(1), DESCRIPTION and Porcelain Format Version 2; *re-checked*: the wrong-approach tests (no staging, staged only, extra untracked file, staged or unstaged edit, other branch, detached HEAD, bare repository, repository one folder too high, deleted `.git`, a repository inside `project`, a file mode change) |
| hint 1 | `git status` names the branch and lists untracked, staged and changed files | git-status(1), DESCRIPTION; experiment |
| hint 2 | A new file reaches a commit in two moves: `git add`, then `git commit` | git-add(1), git-commit(1), DESCRIPTION; as the `stage` step |
| hint 3 | The listed commands, complete, solve the level | *re-checked*: `test_the_quest_leads_to_a_solved_level`; the harness's `solve` then `check` |
| debrief | A commit records a complete snapshot of the project's files, not only the changed lines; a plain `git commit` takes it from the staging area | git-commit(1), DESCRIPTION; Pro Git 1.3, Snapshots, Not Differences; experiment: the second commit's tree lists the unchanged `b.txt`; *re-checked*: card `basics-commit-records` |
| debrief | A commit stores author name and email, date, message and parent; the first commit has none | `git cat-file -p` on a second commit (tree, parent, author, committer, message) and on the root commit (no `parent` line); gitglossary(7), parent |
| debrief | The commit's hash is computed from all of that | gitglossary(7), object: "uniquely identified by the SHA-1 of its contents"; experiment: same files and message, committer date one second apart, different hashes |
| debrief | Unchanged files are not stored twice | Pro Git 1.3: "if files have not changed, Git doesn't store the file again, just a link to the previous identical file"; experiment: `git ls-tree` gives `b.txt` the same blob id in both commits |
| debrief | The staging area lets you split changes into focused commits | git-add(1), DESCRIPTION ("can be performed multiple times before a commit"); Pro Git 1.3, basic workflow ("selectively stage just those changes you want"); *re-checked*: card `basics-why-staging` |
| debrief | After a plain `git commit`, the staging area matches the new commit and is not emptied | experiment: `git ls-files` still lists every file, `git diff --cached --quiet` succeeds; but after `git commit <path>` other staged changes stay staged (`git diff --cached --quiet` exits 1), hence "plain"; *re-checked*: card `basics-index-after-commit` |
| debrief | The commits you make carry the name and email Git is set to use | git-commit(1), COMMIT INFORMATION (environment variables and `--author` can override, so the text does not say "every"); *re-checked*: card `basics-identity` |
| debrief | The `git config --global` commands set the identity | git-config(1); Pro Git 1.6 |

## Cards (`content/cards/basics.toml`)

12 cards: 8 choice, 2 text, 2 predict; levels 7 / 4 / 1. Answer-length rules checked by script:
no right option exceeds the longest distractor by more than 15 characters, and the right option
is the longest in 1 of 8 choice cards. Every `verify` and `code` snippet passes in the lessons'
environment (`BASE_CONFIG` as the only global configuration) with `bash -c` (no `-e`), and each
fails when its claim is inverted (mutation run).

| Card | Claim | Evidence |
|---|---|---|
| basics-repository-folder | History lives in a hidden `.git` folder in the project folder; `ls` leaves it out because of the leading dot | git-init(1), DESCRIPTION; Pro Git 1.3; git-config(1), `core.hideDotFiles` (Windows also marks `.git` hidden, so the card no longer says "only because"); *verify* |
| basics-commit-needs-staging | Committing with nothing staged makes no commit; a new file reaches a commit only after `git add` | git-commit(1), DESCRIPTION (paths given to `git commit` "must already be known to Git") and `-a` ("new files you have not told Git about are not affected"); experiment: `git commit -m x new.txt` and `git commit -i -m x new.txt` on an untracked file fail; experiment: with nothing staged, `git commit` exits 1 with a status summary and no error line, so the card says "stops without making a commit"; *verify* (commit fails, `HEAD` does not resolve) |
| basics-add-copies | `git add` copies the current content and commits nothing; a later edit needs another add to be staged | git-add(1), DESCRIPTION; *verify* |
| basics-identity | Git records `user.name` and `user.email` as the author of your commits, normally; they are not a login; most commands work without them; local overrides global | git-commit(1), COMMIT INFORMATION ("This name has no effect on authentication"; environment variables override) and `--author`; experiment: `git init`, `git add` and `git status` succeed with no identity set; git-config(1), FILES ("last value found taking precedence"); experiment: global and local name set, `git config --get` returns the local one; *verify* (commit author comes from the settings) |
| basics-init-command | `git init` creates a repository with no commits; the game's `init.defaultBranch` makes its first branch `main`; `-b main` names it whatever the settings | git-init(1), DESCRIPTION and `--initial-branch`; *verify* (plain `git init` under the game's settings, and `-b main` with no settings at all) |
| basics-log-oneline | `--oneline` is `--pretty=oneline --abbrev-commit`, newest first; the line shows the message's title; a terminal adds names such as `(HEAD -> main)` | git-log(1), `--oneline`, `--decorate`; git-commit(1), DISCUSSION: "The text up to the first blank line in a commit message is treated as the commit title"; experiment: a message `line one`, `line two`, blank, `body` shows as `b7d3812 line one line two`; *verify* |
| basics-staged-not-committed | A staged change is not in `git log` until committed | git-log(1), git-commit(1); *predict* output `1`; the explain no longer says "only `git commit` adds a commit" (`git revert --no-edit HEAD` adds one too: experiment, 3 commits after it) |
| basics-commit-records | A commit records a snapshot of the project's files; a plain `git commit` stores the staging area; `git show` computes changes against the parent; untracked files stay out | git-commit(1), git-show(1) DESCRIPTION ("the log message and textual diff"); Pro Git 1.3; *verify* (second commit lists the unchanged file, not the untracked one) |
| basics-why-staging | The staging area lets you choose what goes into each commit | git-add(1); Pro Git 1.3; *verify* (two files, two commits, one file each) |
| basics-staged-version | The commit holds the content staged by `git add`, not the later edit | git-add(1); Pro Git 2.2 ("the version ... as it was when you last ran the git add command is how it will go into the commit"); *verify* |
| basics-index-after-commit | After a plain `git commit` the staging area still lists every tracked file and matches the commit | gitglossary(7), index; git-ls-files(1); experiment on `git commit <path>` as in the debrief; *verify* |
| basics-commit-all-skips-new | `git commit -a` stages tracked files only; new files stay untracked; committing does not clear the staging area | git-commit(1), `-a`: "new files you have not told Git about are not affected"; Pro Git 2.2; experiment: deleting every tracked file then `git commit -a` leaves `git ls-files` empty, so the explain no longer says "never empties"; *predict* output `1` |

## Notes (cheat sheet in `basics.toml`)

Every statement in the notes repeats a claim above: the `.git` folder and the `main` branch
(init slide), the three areas and their git names (areas slide), what `git status` lists (areas
slide), untracked files, `git add` and re-adding to stage new content (add slide), a plain
`git commit` and the staging area afterwards (debrief), the identity, the two complete commands
and the local override (card `basics-identity`), and each command's one-line summary (lesson and
quest). The parent of the first commit: none (debrief, gitglossary(7), parent).

## Fact-check 1 (independent agent, 2026-10-06)

Every finding was reproduced on git 2.43.0 before it was fixed; the evidence is in the rows above.

| Where | Finding | Fix |
|---|---|---|
| slide `nothing-staged`, step `stage`, `commit_move`, card `basics-commit-needs-staging` | "A commit takes the content of the staging area" is false for `git commit <path>` and `-a` | scoped to "a plain `git commit`", or to how a new file gets into a commit |
| slide `areas`, step `status`, debrief, notes | "`git status` shows where each file stands": unchanged and ignored files are not listed | "lists the files that are untracked, staged, or changed but not staged" |
| slide `log`, step `hash`, notes, card `basics-log-oneline`, `check_hash` | on a terminal `git log --oneline` shows `(HEAD -> main)` between hash and message | described in the text; the nudges say the hash starts the line |
| hint 3, identity messages | `git config --global user.name` without a value only reads | complete commands everywhere, from `NAME_COMMAND` and `EMAIL_COMMAND` |
| debrief, card `basics-index-after-commit` | "after a commit the staging area matches it" fails after `git commit <path>` | scoped to a plain `git commit` |
| step `file` | `>` also replaces an existing file's content | said so |
| `tidy_move` | an untracked file may still be in the last commit (`git rm --cached`), and committing it needs `git add` first | "not in the staging area (untracked). Stage and commit what you need" |
| `repository_move` | `git switch main` fails when `main` does not exist; `git branch -m main` fails when it does | advice chosen by whether `main` exists, with `git switch -c main` for a detached HEAD |
| `SOLVED`, commit step | "your first commit" when the check reads the last one | "your last commit" |
| notes | "you must add it again" (`git commit -a` does it for you) | "you add it again to stage the new content" |
| card `basics-staged-not-committed` | "only `git commit` adds one to the history" (`git revert`, `git merge`, `git cherry-pick` add commits) | "it takes `git commit` to add it to the history" |
| card `basics-commit-all-skips-new` | "a commit never empties the staging area" (deleting every tracked file, then `git commit -a`) | "committing does not clear the staging area, so `a.txt` is still listed" |
| card `basics-commit-needs-staging` | "stops with an error": git prints a status summary, no error line | "stops without making a commit" |
| card `basics-log-oneline` | "the first line of its message": the title runs to the first blank line | "its message's title (the text up to the first blank line, usually one line)" |

Found while applying rule 8 to the rest: "hidden only because its name starts with a dot" (false
on Windows, `core.hideDotFiles`), "Nothing is committed until you run `git commit`", "Git writes
them into every commit" (`--author`, environment variables), "`--global` means for every
repository" (a local setting overrides), "every new commit goes on top" (the root commit), "the
first branch is always called `main`" (`git init -b`), and the slide title "A commit takes what
is staged", and "Git accepts the short form wherever it needs a commit" (`git fetch` needs the full
hash). Each was rescoped.

## Fact-check 2 (independent agent, 2026-10-06)

Played blind first through the game API and the game's shell (`firstcommit shell`), then checked
every sentence again. Each finding was reproduced on git 2.43.0. The fixes are in the rows above,
and each new check has a test that fails when the check is inverted (mutation run).

| Where | Finding | Fix |
|---|---|---|
| `check`, `SOLVED` | The level said "the working folder, the staging area and that commit all agree" while `git status` still listed `project/` (a repository made by `git init project`, which the snapshot leaves out) or ` M README.md` (`chmod 755`: the snapshot compares contents, not modes) | `tidy_move` reads `git status --porcelain=v2 -z --no-renames` once the snapshot is clean, with a nudge for a nested repository |
| `check_hash` | A correct hash start of 3 characters got "That is not the start of a commit hash": git needs at least 4 (git-rev-parse(1), `--short`) | its own nudge, from `kit.MIN_HASH_PREFIX` |
| `check_hash`, `check_branch` | The whole pasted line (`e177e43 (HEAD -> main) Add the README`, `On branch main`) got "not the start of a commit hash" and "not the branch you are on" | "Type only the short hash, the first word of the line" and "Type only the name of the branch" |
| `check_branch` | "branch names are case-sensitive" depends on the file system (refs can be files, see the feedback row; AUTHORING rule 5) | "with the same capital and small letters", no claim |
| `commit_move` | "with `git commit`": a bare `git commit` opens an editor, which the level never taught | the complete `git commit -m "Add the README"` |
| `repository_move` | `git init project`, typed inside `project`, got only "There is no repository in the `project` folder yet" | its own nudge: restart, then `git init` with nothing after it |
| slide `init`, card `basics-init-command` | "starts with one branch": `git branch` lists nothing and `main` does not resolve until the first commit | "has no commits yet, but you are already on its first branch" |
| slide `commit` | "`git commit` saves the content of the staging area" unscoped (rule 8), and "`git status` has nothing left to report" while it still prints the branch | "A plain `git commit`", "`git status` lists no files any more" |
| briefing | "a commit on `main` that contains `README.md`": the check reads the last commit (a later `git rm README.md` commit leaves it unsolved) | "the last commit on `main`" |
| card `basics-log-oneline` | The `verify` fails under `log.decorate=short`, which phase-2-engine's lesson environment sets (`cut` keeps `(HEAD -> main)`); the explain called `(HEAD -> main)` "branch names" | `--no-decorate` in the `verify`; "names such as `(HEAD -> main)`" |
| notes | "a message and its parent": the first commit has none | "(the first commit has none)" |
| this log | "lesson transcripts use `log.decorate=short`" was not yet true on this branch's engine | true since phase-2-engine 2166fc6 was merged; the `log` row quotes the decorated transcript |

Reported to the lead, not fixed here (not this chapter's files): `demos.py` built the lessons
folder from the whole `GIT_CEILING_DIRECTORIES` value, so lessons ran outside the ceiling and an
empty slide showed any repository around the game home (fixed on phase-2-engine by 58ae4b5).

Checked and left as they are: "only through the staging area" and "only once it is staged" (with
an untracked file, `git commit <path>`, `-i`, `-o` and `-a` all fail and make no commit); "for
all my repositories on this computer" (Pro Git 1.6: "all of the repositories you work with on your
system"); the `nothing-staged` slide (in the player's shell, a commit before the identity is set
fails for the identity first, but the lessons set one); `git add -N`, `--assume-unchanged` and
`--skip-worktree` states, where the check is stricter than `git status` (none of them is taught).

## Left out

- Git's own default branch name without the game's settings (`master` in 2.43, with a hint on
  standard error; verified, git-init(1)): left to the `setup` chapter, as the lead decided.
- Whether `git commit` fails without a configured identity: it depends on the machine (git falls
  back to `EMAIL`, then the system user name and host name; git-commit(1), COMMIT INFORMATION).
  It failed here, but the text only says to set the identity before committing.
- The usual short-hash length (seven characters here): `core.abbrev` computes it from the
  repository's size (git-config(1)), so the text says "the first characters".
- `git commit --allow-empty`, `git commit <path>` and `-i`: beyond this level; the text scopes its
  claims to a plain `git commit` instead.
- What is inside `.git` (objects, refs): left to the `hash` chapter.
- Merge commits with two parents: left to the `branch` chapter; the debrief says "its parent" for
  the commits this level makes.
