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

Picture-first since 2026-10-06 (AUTHORING.md section 3.5): each slide shows one change in the
places figure (the last one too, so a commit is one picture throughout: mapcheck's fix), its `text` reads the picture in at most three
sentences, and details sit in its folded `more`. *Re-checked* by
`test_each_slide_changes_exactly_the_place_it_is_about` (on the real `demos.frames`) and the
level's other lesson tests. The figure's words (working folder, staging area as the open box,
your repository with its closed boxes, pages with a content id and colour) are the four-places
draft's (`docs-draft/four-places.md`, P1-P4, B1-B4, A1-A2).

| Slide | Claim | Evidence |
|---|---|---|
| history | The project folder is empty and Git keeps nothing for it yet | the lesson starts in the empty `/home/you/project` (AUTHORING 3.5); *re-checked*: the first frame has no repository and no files |
| history | Git can save versions of a project as closed boxes, called commits, and you can get any of them back | Pro Git 1.1: "records changes to a file or set of files over time so that you can recall specific versions later"; gitglossary(7), commit; the last slide gets one back (`git show HEAD~1:README.md`) |
| history (more) | A version control system records changes over time: what changed, who and when; Git is one | Pro Git 1.1: "revert ... compare changes over time, see who last modified something" |
| init | `git init` turns the folder into a repository; the staging area is empty and there are no commits yet | git-init(1), DESCRIPTION ("An initial branch without any commits will be created"); experiment in `demos.environment`: after `git init`, `git ls-files` lists nothing and `git rev-parse -q --verify HEAD` fails |
| init (more) | `git init` creates a hidden `.git` folder, which `ls -A` shows; Git keeps the repository there, and the staging area too once you add a file | git-init(1), DESCRIPTION ("basically a .git directory"); experiment: `ls -A .git` after `git init` lists `HEAD branches config description hooks info objects refs` and no `index`; `.git/index` exists after the first `git add` (git treats the missing file as an empty staging area, so the text says "is empty", not that `git init` makes one) |
| init (more) | A new repository has no commits yet, but you are already on its first branch; a branch is a line of development; the game's `init.defaultBranch` makes it `main` | as before (fact-check 2): git-init(1); gitglossary(7), branch; `gitcmd.BASE_CONFIG`; *re-checked*: test `test_plain_git_init_starts_on_main_with_the_games_starting_settings` |
| file | A new file appears as a page in the working folder; it is untracked, in neither box | Pro Git 2.2 (untracked); experiment: `git status --short` gives `?? README.md`, `git ls-files` lists nothing; four-places P3 |
| file (more) | A page shows the name and a short id of the content; the same content always gets the same id and colour, so a page that changes gets a new one | four-places P1 (same text, same blob id: experiment, `git hash-object README.md copy.md` gives `f3860383ad...` twice) and P2; `map.js` `blobHue(blob)` |
| file (more) | `git status` lists it as untracked; Git's own name for the working folder is the working tree | experiment; gitglossary(7), working tree |
| nothing-staged | The open box is empty, so `git commit` makes no commit; a page in the working folder is not enough | git-commit(1), DESCRIPTION ("containing the current contents of the index"); experiment: exit status 1, no commit; *re-checked*: the slide's `! ` line must fail, and the frame shows no change |
| nothing-staged (more) | A plain `git commit` takes the staging area; a new file gets there only with `git add`; Git says why it made no commit | git-commit(1) items 1-4 (paths "must already be known to Git"; `-a` leaves new files alone); experiment: the transcript shows git's explanation (shown, not quoted) |
| add | `git add` drops a copy of the page into the open box; the working folder keeps its page | four-places A1; git-add(1), DESCRIPTION; experiment: `git status --short` gives `A  README.md`, the file is still there; *re-checked*: the frame changes the staging area only |
| add (more) | `git add` copies the content at that moment and usually prints nothing; the open box holds a page for every file the next commit will contain; Git's own name is the index | git-add(1), DESCRIPTION ("It only adds the content ... at the time the add command is run"); experiment: no output; four-places B1; gitglossary(7), index |
| commit | `git commit` closes a copy of the open box and sets it in your repository, labelled with its short hash; the open box keeps its page | four-places A2 and B4 (the staging area keeps its files); experiment: `git ls-files -s` lists `f3860383ad...` before and after the commit, `git status --short` lists nothing; *re-checked*: the frame changes the commits only |
| commit (more) | A plain `git commit` saves the staging area with name, email, date and `-m` message; `main` points to it; the short hash is the start of the hash Git computes from all of that; `git status` now lists no files | git-commit(1), DESCRIPTION, COMMIT INFORMATION; gitglossary(7), object; git-log(1), `--abbrev-commit`; experiment (`git cat-file -p HEAD`; a one-second date change gives another hash) |
| edit | Editing the file changes its page in the working folder (new id and colour); the open box and the closed box keep the old version | four-places P2; experiment: after `echo "Be kind to each other." >> README.md`, `git hash-object README.md` gives `b43b4feb76...` while `git ls-files -s` and `git ls-tree HEAD` still give `f3860383ad...`; *re-checked*: the frame changes the working folder only |
| edit (more) | `>>` adds a line at the end; `git status` lists the file as modified but not staged; a plain `git commit` now would make no commit | bash(1), Appending Redirected Output; experiment: ` M README.md`; `git commit -q -m x` exits 1 and `git rev-list --count HEAD` stays 1 (so the text does not say a commit "would save the old version") |
| add-again | `git add` drops the new version into the open box in place of the old one; the closed box keeps the old version | experiment: `git ls-files -s` gives `b43b4feb76...`, `git ls-tree HEAD` still `f3860383ad...`; *re-checked*: the frame changes the staging area only |
| add-again (more) | The staging area keeps a file's content as at the last `git add`; `git status` lists it as modified and staged | git-add(1), DESCRIPTION; experiment: `M  README.md` |
| second-commit | Each closed box is a saved version (a commit); the new one sits on top of the first, its parent; `git log --oneline` lists them newest first with short hash and message | git-commit(1) ("a direct child of HEAD"); experiment: `git cat-file -p HEAD` shows `parent f862e40...`; git-log(1), Commit Ordering; *re-checked*: the slide's real output `ef6e967 (HEAD -> main) Add the first rule` / `f862e40 Add the README` |
| second-commit (more) | On a terminal and in the lesson the newest line shows `(HEAD -> main)`; `git show HEAD~1:README.md` prints the README as the first commit saved it | git-log(1), `--decorate`; `demos.TERMINAL_CONFIG` (`log.decorate=short`); experiment: prints `# Team handbook` |

The lesson was run through the real `demos.frames`: every line succeeds except
`! git commit -m "Add the README"`, and each frame changes exactly the place its slide is about
(none, repository, working folder, none, staging area, commits, working folder, staging area,
commits).

### Guided quest

Each step's `text` says what to do in at most two sentences, in the figure's words; the page
shows its `command` in its own box, and the rest is in its folded `more` (*re-checked* by
`test_every_quest_step_says_what_to_do_in_two_sentences_and_leaves_the_command_to_its_box` and
`test_gits_own_terms_and_the_details_are_folded_into_more`).

| Step | Claim | Evidence |
|---|---|---|
| init | Make the empty `project` folder a repository with `git init`; the terminal opens there | the lab's `project` folder is empty after `setup`, and the game's terminal opens there (`game.terminal_folder`); *re-checked*: `test_setup_leaves_an_empty_folder_with_no_repository` |
| init (more) | `git init` creates a hidden `.git` folder where Git keeps your repository; its first branch is `main`, the game's default | as the `init` slide; *re-checked*: the harness's quest walk (`QUEST_ACTIONS["init"]` runs plain `git init`) |
| status | `git status` names the branch you are on | git-status(1); experiment: output starts with the branch; the check compares with the snapshot's `branch`, never with git's text |
| status (more) | It also lists the files that are untracked, staged, or changed but not staged; the new repository has none | git-status(1), DESCRIPTION; experiment |
| name | Every commit records who made it | git-commit(1), COMMIT INFORMATION; experiment: `git cat-file -p HEAD` |
| name (more) | Quotes keep a name with spaces one value; `--global` means for all your repositories on this computer unless one sets its own; inside the game it writes the game's own settings file; a name set earlier passes the step at once | as before: bash(1), QUOTING; git-config(1), `--global` and FILES; git(1), GIT_CONFIG_GLOBAL; RelNotes 2.32.0 lines 88-93; `save.ensure_gitconfig` |
| name, email | The suggested commands are complete | AUTHORING section 1, rule 9; *re-checked*: `test_a_missing_identity_gets_a_complete_command_to_set_it`; the steps' `command` and messages share `NAME_COMMAND` and `EMAIL_COMMAND` |
| file | The new file's page appears in the working folder | the live figure draws a page for every file in the working folder (four-places Part 1, P3) |
| file (more) | `README.md` tells people what a project is about; `echo` prints a line and `>` creates the file or replaces its content; `git status` lists it as untracked | docs.github.com, About READMEs; bash(1), Redirecting Output ("truncated to zero size"); experiment |
| stage | `git add` drops a copy of the page into the open box | four-places A1 |
| stage (more) | `git add` usually prints nothing; the working folder keeps its page; a new file gets into a commit only through the staging area | experiment; git-add(1); git-commit(1) (`git commit -m x new.txt` and `git commit -i -m x new.txt` on an untracked file fail) |
| commit | `git commit` saves the staging area as your first commit | git-commit(1), DESCRIPTION |
| commit (more) | `-m` gives the message; without it Git opens a text editor; a closed box appears in your repository, on `main` | as before (git-commit(1), ENVIRONMENT AND CONFIGURATION VARIABLES; `git var GIT_EDITOR` experiment); four-places A2 (the live figure) |
| hash | `git log --oneline` lists the history with each commit's short hash | git-log(1), `--oneline` |
| hash (more) | One commit per line, newest first, short hash then message, with `(HEAD -> main)` on the terminal's newest line; 40-character full hash; `git show` accepts the short form | as before: git-log(1), `--decorate`; gitglossary(7), object name; gitrevisions(7), `<sha1>`; the `git fetch` experiment |

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
| conflicted file | Edit it to keep the content you want, then stage and commit it | git-merge(1), HOW TO RESOLVE CONFLICTS: "Edit the files into shape and git add them to the index. Use git commit or git merge --continue to seal the deal"; experiment: after a conflicting `git merge`, `git status --porcelain` gives `UU README.md`; editing, `git add README.md` and `git commit -m` make a merge commit with two parents and a clean status; *re-checked*: `test_a_conflicted_file_keeps_the_level_unsolved` (fails when the conflict rule is removed) |
| `README.md` deleted from the folder | `git restore README.md` brings it back | git-restore(1), DESCRIPTION: "otherwise from the index"; RelNotes 2.23.0 line 61; experiment: after `rm README.md`, `git restore README.md` exits 0 and the status is clean; *re-checked*: `test_a_readme_deleted_from_the_folder_gets_the_command_that_brings_it_back` |
| another file deleted from the folder | The deletion is not staged; stage and commit it | git-status(1), DESCRIPTION; RelNotes 2.0.0 line 106: "\"git add <path>\" is the same as \"git add -A <path>\" now"; experiment: `git add notes.txt` on the deleted file gives `D  notes.txt`, then a commit leaves the status clean; *re-checked*: `test_another_file_deleted_from_the_folder_is_named_as_a_deletion` |
| changed, not staged | The file is changed in the working folder and the change is not staged | git-status(1), DESCRIPTION ("paths that have differences between the working tree and the index file"); the old "changed after the last `git add`" was false after `git add` then `git restore --staged` (experiment: ` M README.md` with no change since that `git add`); *re-checked*: `test_a_change_unstaged_with_restore_is_not_said_to_follow_the_last_add` |
| `readme.md` instead of `README.md` | The level needs the name `README.md`; `mv readme.md README.md` renames an untracked file and `git mv readme.md README.md` a staged one | experiment: `mv readme.md README.md` leaves `?? README.md`; `git add Readme.MD` then `git mv Readme.MD README.md` gives `A  README.md`; the name is shell-quoted (`shlex.quote`) and shown with `kit.code`; *re-checked*: `test_a_readme_in_the_wrong_letter_case_gets_the_command_that_renames_it`, `test_a_readme_in_the_wrong_letter_case_is_named_as_the_player_wrote_it` |
| any message naming a file or branch | Shows the player's name exactly | `kit.code`; *re-checked*: `test_a_file_name_the_player_chose_is_shown_exactly`, `test_a_branch_name_the_player_chose_is_shown_exactly` |

### Briefing, hints and debrief

| Where | Claim | Evidence |
|---|---|---|
| briefing | Your terminal opens in the empty `project` folder | `game.terminal_folder` names the lab's `project` folder while a level is active; the page's terminal (`web/routes.py`) and `firstcommit shell` open there |
| briefing | Solved when the last commit on `main` contains `README.md` and `git status` lists nothing untracked, changed or staged | `check` reads the last commit (`head` in the snapshot) and the snapshot's status lists (`kit.conflicted`, `kit.untracked`, `kit.staged`, `kit.unstaged`, `kit.mode_changed`, `kit.nested`), which classify each file as `git status` does; git-status(1), DESCRIPTION; *re-checked*: the wrong-approach tests (no staging, staged only, extra untracked file, staged or unstaged edit, a file deleted from the folder, a conflict, other branch, detached HEAD, bare repository, repository one folder too high, deleted `.git`, a repository inside `project`, a file mode change) |
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

## Fix round (code review M2, M7 R34, L7, L10; playtest polish; 2026-10-06)

- The quest now asks for the name and email before the first file, so a commit tried before
  staging fails for the empty staging area, as the `nothing-staged` slide shows, not for a
  missing identity (git-commit(1), COMMIT INFORMATION: without `user.name` and `user.email`, git
  falls back to `EMAIL` and the system user name; in the playtest that name was empty, and the
  commit stopped with an error). No step text changed.
- `solve` runs every quest step's action in the quest's order (AUTHORING section 3.6), the
  identity steps included; `test_the_reference_solution_plays_every_quest_step_identity_included`.
- Left for the second basics level ("A message that helps"): teaching the editor itself (write,
  save, quit). This level only warns that a bare `git commit` opens one.

## Picture-first rewrite (2026-10-06): changed claims for mapcheck

The lesson went from 7 slides of paragraphs to 9 slides of one change each, and the quest steps
from paragraphs to one or two sentences plus the command; everything else moved, unchanged,
into the folded `more`. New or reworded claims, each with its row above:

| # | Where | New or reworded claim | Kind |
|---|---|---|---|
| V1 | slide `history` | The project folder is empty and Git keeps nothing for it yet; Git can save versions as closed boxes, called commits, and you can get any of them back | reads the first frame; Pro Git 1.1 |
| V2 | slide `history`, more | The picture shows three places on your computer, filled one command at a time by the next slides | the figure (places view) |
| V3 | slide `init` | The open box, the staging area, is empty, and your repository has no closed boxes yet | experiment; nuance: `.git/index` appears only with the first `git add` |
| V4 | slide `init`, more | Git keeps the repository in `.git`, and the staging area too once you add a file | experiment (no `.git/index` after `git init`) |
| V5 | slide `file` | A new file appears as a page in the working folder; untracked, in neither box | four-places P3 |
| V6 | slide `file`, more | A page shows the name and a short id of its content; same content, same id and colour; a changed page gets a new one | four-places P1, P2 |
| V7 | slide `nothing-staged` | The open box is empty, so `git commit` has nothing to close; no closed box appears; a page in the folder is not enough | experiment; the frame shows no change |
| V8 | slide `add` | `git add` drops a copy of the page into the open box; the working folder keeps its page | four-places A1 and its motion |
| V9 | slide `add`, more | The open box holds a page for every file the next commit will contain, not only the changed ones | four-places B1 |
| V10 | slide `commit` | `git commit` closes a copy of the open box and sets it in your repository, labelled with its short hash; the open box keeps its page | four-places A2, B4 and the commit motion |
| V11 | slide `edit` | Editing changes the page in the working folder (new id and colour); the open box and the closed box keep the old version | four-places P2; experiment |
| V12 | slide `edit`, more | A plain `git commit` now would make no commit | experiment (exit 1) |
| V13 | slide `add-again` | `git add` drops the new version into the open box in place of the old one; the closed box keeps the old version | experiment |
| V14 | slide `second-commit` | Each closed box is a saved version; the new one sits on top of the first, its parent; `git log --oneline` lists them newest first | git-commit(1); the places view's timeline of closed boxes; the slide's real output |
| V15 | slide `second-commit`, more | `git show HEAD~1:README.md` prints the README as the first commit saved it | experiment |
| V16 | quest `file` | The new file's page appears in the working folder (the live figure) | four-places Part 1 |
| V17 | quest `stage` | `git add` drops a copy of the page into the open box | four-places A1 |
| V18 | quest `commit`, more | A closed box appears in your repository, on `main` (was "the map shows your first commit") | four-places A2 |

The briefing, hints, debrief, feedback messages and cards are unchanged by this rewrite.

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
