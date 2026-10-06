# Share a file with Alex (draft, revision 2, for fact-check)

**Revision 2** applies `.scratch/review/share-check.md` and the lead's notes on it. Everything
new for the checker is marked **(r2)**:

| What | Where |
|---|---|
| S10 is now two steps: your plain `git pull` stops (S10a, new), then `git pull --no-rebase --no-edit` merges (S10b, new words) | Part 1 table, Part 2, Part 3 |
| S7 is now two steps, each lighting its own arrow: Alex commits (S7a), then pushes (S7b) | Part 1 table, Part 2, Part 3 |
| S6 ends "Now Alex's files have it too." | Part 2 |
| Alex's column says "Alex's repository"; both repositories' notes say "closed boxes: the commits" | Part 2 "Other words" |
| The recording: clones reach GitHub by a relative path, as the game's labs now do, so the merge commit's hash belongs to the subject shown; the lessons' own environment; S11's hash | Part 1, Part 3 |
| Below about 800 px the three columns stack | Part 1 |

S1 to S5, S8, S9 and S11's words are unchanged.

A figure in the boxes pictures: your computer, GitHub (the practice copy) and Alex's computer side
by side. Each computer stacks its working folder, its open box (the staging area) and its
repository (closed boxes on a timeline). It plays one step at a time, and each step has one
caption that says what Alex can see. Part 1 is how the figure is made, Part 2 the captions with
their claim tags, Part 3 the claims register.

---

## Part 1: how the figure is made

Every drawing is a snapshot of real git: a bare repository (`git init --bare github/project.git`)
and two clones, `you` and `alex`, with your commits as Robin Park and Alex's as Alex Kim, fixed
dates, git 2.43.0, `init.defaultBranch=main`. Before the first step, you committed `README.md`
and pushed it, and Alex cloned. After every step the generator snapshots all three repositories
and runs `changes.describe` on each, the same events the game's feed shows. The arrows that light
are the stepping person's commands (`TimePlaces.commands`) from those events.

**(r2)** The generator is `tools/demo/share.py` (`uv run python tools/demo/share.py share.json`).
It runs in the lessons' own environment (`firstcommit.demos.environment`: the game's starting
configuration and nothing from the shell that runs it, so no `GIT_*` variable of whoever runs it
applies), in a level's lab layout (`firstcommit.lab.Lab`: your clone is the lab's project,
Alex's its teammate). Right after cloning, each clone is pointed at GitHub by its relative path
(`git remote set-url origin` with `Lab.github_url`), as AUTHORING section 3.2 now asks of every
level, so `git remote -v` in your clone shows `../github/project.git`. Git prints that URL in
push and pull output and writes it into the merge commit's message
(`Merge branch 'main' of ../github/project`), so nothing recorded names the temporary folder:
the merge commit's hash is the same on every run, and the subject shown is the real one. Nothing
is rewritten after recording. Two runs, in two different temporary folders, give byte-identical
recordings. A command written `! git push` must fail, as in a
lesson; any other must succeed. What a command prints is recorded with its errors, in the order
a terminal shows them.

Three steps are checked by the generator itself:

- **Alex's `git pull` is shown in two halves.** At that point the generator copies Alex's clone,
  runs `git fetch` in the copy and snapshots it: that is the drawing between the halves. It then
  runs `git merge --ff-only origin/main` in the copy and fails unless the copy now matches,
  snapshot for snapshot, Alex's real clone after the real `git pull`.
- **The refused push.** The generator requires `git push` to fail, and fails unless all three
  snapshots are exactly as they were before it. The figure shows git's own output under the
  command.
- **(r2) Your plain `git pull` that stops.** The generator requires it to fail, and fails unless
  your clone ends exactly where `git fetch` ends in a copy of it made just before: it fetched,
  and changed nothing else. The figure shows git's own output under the command.

The commands, as run:

| Step | Who | Commands |
|---|---|---|
| create | you | `echo 'Meeting at 10.' > notes.txt` |
| add | you | `git add notes.txt` |
| commit | you | `git commit -m 'Add the meeting notes'` |
| push | you | `git push` |
| pull-fetch, pull-merge-half | Alex | `git pull` (its two halves, as above) |
| **(r2)** alex-commit | Alex | `echo 'Bring the slides.' >> notes.txt`, `git commit -am 'Ask for the slides'` |
| **(r2)** alex-push | Alex | `git push` |
| you-commit | you | `echo 'Start here.' >> README.md`, `git commit -am 'Say where to start'` |
| refused | you | `git push` (must fail) |
| **(r2)** pull-stops | you | `git pull` (must fail) |
| pull-merge | you | `git pull --no-rebase --no-edit` |
| push-again | you | `git push` |

**(r2) Narrow screens.** Below about 800 px the figure is one column: you, then GitHub, then
Alex. Alex's computer is drawn upside down (repository nearest GitHub, working folder last), so
each arrow still joins the two places it moves work between: yours point down towards GitHub,
Alex's up towards it, and a shared file travels down the page from your working folder to
Alex's. The words are the same as in the wide layout.

---

## Part 2: the captions

- **create**: You made `notes.txt`. It is only in your working folder: Alex can't see it. **[S1]**
- **add**: `git add` put a copy of `notes.txt` in your open box, the staging area. Alex still
  can't see it. **[S2]**
- **commit**: `git commit` closed the box and set it on your timeline: a commit in your
  repository. Alex still can't see it: committing shares nothing, it saves on your computer only.
  **[S3]**
- **push**: `git push` carried the box to GitHub, and GitHub's `main` moved onto it. Alex still
  doesn't have it: it is on GitHub, not on Alex's computer. **[S4]**
- **pull-fetch**: Alex runs `git pull`. First its fetch half: the box arrives in Alex's repository
  and Alex's `origin/main` moves onto it. Alex's working folder hasn't changed yet. **[S5]**
- **pull-merge-half**: Then its merge half: Alex's `main` moves onto the box, and `notes.txt`
  appears in Alex's staging area and working folder. **(r2)** Now Alex's files have it too.
  **[S6]**
- **(r2) alex-commit**: Alex adds a line to `notes.txt` and commits: a new box on Alex's timeline,
  in Alex's repository only. GitHub and your computer don't have it. **[S7a]**
- **(r2) alex-push**: Alex's `git push` carries the box to GitHub, and GitHub's `main` moves onto
  it. Alex has the new line; your computer still has the old `notes.txt`. **[S7b]**
- **you-commit**: You commit a change of your own, to `README.md`. Alex can't see it, and you
  don't have Alex's new line yet. **[S8]**
- **refused**: Your `git push` is refused: GitHub has Alex's commit, which your repository
  doesn't. Nothing moves, on your computer or on GitHub, and Alex still can't see your commit.
  **[S9]**
- **(r2) pull-stops**: Your `git pull` fetches Alex's commit: the box arrives in your repository
  and your `origin/main` moves onto it. Then it stops: both sides have new commits, and since no
  setting (`pull.rebase` or `pull.ff`) says how to join them, git asks you to choose:
  `--no-rebase` merges, `--rebase` rebases. Your `main` and your files don't change, and Alex
  still can't see your commit. **[S10a]**
- **(r2) pull-merge**: `git pull --no-rebase` merges Alex's commit with yours (`--no-edit` takes
  git's own merge message instead of opening an editor): a merge commit joins the two timelines,
  and your `notes.txt` gets Alex's line. Alex can't see your commit yet. **[S10b]**
- **push-again**: Now `git push` works: GitHub gets your commit and the merge commit, and its
  `main` moves onto them. Alex will have them after the next `git pull`. **[S11]**

Other words: the people are labelled "You" and "Alex", GitHub's column "GitHub (the practice
copy)", the command line "You: $ git push" or "Alex: $ git pull". The arrows' spoken routes name
Alex's places on Alex's side ("fetch: from the remote repository to Alex's repository").
**(r2)** Alex's repository is titled "Alex's repository" (yours "Your repository"; "Working
folder" and "Staging area" stay neutral under each person's name), and the note under both
repositories reads "closed boxes: the commits". *Pending:* the titles come from
`theme-time-places.js`, which needs a small hook (an owner for the title, and the note's new
words); the share figure already passes the owner.

---

## Part 3: claims register

"Seen" is what the generator recorded (git 2.43.0, `tools/demo/share.py`): the feed events of
each repository after the step (`you`, `github`, `alex`), exit statuses, and git's output where it
matters. Commits: `8c50576` Add the README, `40404d5` Add the meeting notes (yours), `69c7214`
Ask for the slides (Alex's), `714a65d` Say where to start (yours), `75b4b62` the merge commit.

| Tag | Claim | Check | Seen |
|---|---|---|---|
| S1 | A new file is only in your working folder; Alex's clone and GitHub do not have it | `git status --short` in `you`; `ls` in `alex`; `git -C github/project.git ls-tree -r main --name-only` | events: you `file-created`; github and alex none |
| S2 | `git add` puts a copy in your staging area; Alex and GitHub unchanged | `git ls-files -s notes.txt` in `you`; compare `alex` and GitHub | events: you `file-staged`; github and alex none |
| S3 | `git commit` makes a commit in your repository only: committing shares nothing; GitHub and Alex unchanged | `git -C github/project.git rev-parse main` and Alex's refs before and after | `[main 40404d5] Add the meeting notes`; events: you `commit-created`; github and alex none |
| S4 | `git push` moves GitHub's `main` to your commit; Alex's repository and folder unchanged until Alex fetches or pulls | Alex's `git rev-parse main origin/main` and `ls` before and after your push | `8c50576..40404d5  main -> main`; events: you `remote-updated`, github `push-received`; alex none |
| S5 | `git pull` first fetches: Alex's `origin/main` moves to the new commit; Alex's `main`, staging area and working folder are unchanged at that point | `man git-pull` (fetch, then integrate); the generator's copy after `git fetch` | copy after `git fetch`: alex `remote-updated` only; `main` 8c50576, files unchanged |
| S6 (r2) | Then the merge (a fast-forward here) moves Alex's `main`, and the file appears in Alex's staging area and working folder; Alex's repository already had the commit after S5 | Alex's `git ls-files -s`, `ls`, `git rev-parse main` after `git pull` | `Updating 8c50576..40404d5`, `Fast-forward`; events from the halfway state: alex `branch-moved`; `notes.txt` 5f0f9bb in all three areas; the copy's `git merge --ff-only origin/main` matches the real pull exactly (asserted) |
| S7a (r2) | Alex's commit is in Alex's repository only; GitHub and your computer unchanged | GitHub's `main`, your refs and `notes.txt` before and after | `[main 69c7214] Ask for the slides`; events: alex `commit-created`; you and github none |
| S7b (r2) | Alex's push moves GitHub's `main` to Alex's commit; your computer unchanged | your `git rev-parse main origin/main`, `cat notes.txt` | `40404d5..69c7214  main -> main`; events: github `push-received`, alex `remote-updated`; you none (your `notes.txt` still 5f0f9bb) |
| S8 | Your new commit is on your computer only; you do not have Alex's commit | GitHub's `main` and Alex's refs unchanged; your `git log` lacks Alex's commit | `[main 714a65d] Say where to start`; events: you `commit-created`; github and alex none |
| S9 | Your push is refused because GitHub has a commit you do not; nothing changes on your computer or GitHub | `git push`; exit status; snapshots before and after | exit 1, `! [rejected]        main -> main (fetch first)` with the hint to `git pull`; no events anywhere; all three snapshots identical (asserted) |
| S10a (r2) | A plain `git pull` on diverged branches fetches (your `origin/main` moves to Alex's commit), then stops, with no `pull.rebase` or `pull.ff` set; your `main`, staging area and working folder unchanged | `man git-pull`: "If the current branch and the remote have diverged, the user needs to specify how to reconcile the divergent branches with --rebase or --no-rebase (or the corresponding configuration option in pull.rebase)"; the generator's copy after `git fetch` | exit 128; `From ../github/project`, `40404d5..69c7214  main       -> origin/main`, hints, `fatal: Need to specify how to reconcile divergent branches.`; `main` stayed 714a65d, `origin/main` 40404d5 to 69c7214; files unchanged; events: you `remote-updated`; ends exactly where the copy's `git fetch` ends (asserted). In a lab of the same shape (both sides one new commit), `git -c pull.ff=false pull`, `-c pull.ff=true` or `-c pull.rebase=false`: exit 0, merged; `-c pull.ff=only`: exit 128, `Not possible to fast-forward, aborting.` |
| S10b (r2) | `git pull --no-rebase` makes a merge commit with two parents; your `notes.txt` gets Alex's line; `--no-edit` takes git's own merge message, and without it git opens an editor for it | `git cat-file -p HEAD` (two parents); `cat notes.txt`; `man git-merge` (`--edit, -e, --no-edit`: "The --no-edit option can be used to accept the auto-generated message") | `Merge made by the 'ort' strategy.`, `notes.txt \| 1 +`; `75b4b62` with parents 714a65d (yours) and 69c7214 (Alex's); `notes.txt` 3748852 in the staging area and folder; events: you `merge-commit-created`; github and alex none. The editor: the checker's run with `GIT_MERGE_AUTOEDIT=yes GIT_EDITOR=false` (revision 1 check) |
| S11 (r2) | The push is accepted and GitHub's `main` moves to the merge commit; GitHub then has your commit and the merge commit; Alex does not until the next pull | `git push`; `git -C github/project.git log --oneline`; Alex's refs | exit 0, `To ../github/project.git`, `69c7214..75b4b62  main -> main`; the merge commit's subject `Merge branch 'main' of ../github/project`; events: you `remote-updated`, github `push-received`; alex none |

Notes for the checker:

- "Alex can't see it" means Alex's computer does not have the file or commit. Someone could look at
  GitHub after a push; the caption for S4 says where the commit is.
- **(r2)** Revision 1's note on "alex-shares" (the feed told a commit pushed in the same step as
  `branch-moved`) no longer applies: the commit and the push are separate steps, and the lit
  arrows per step are now: create none; add add; commit commit; push push; pull-fetch fetch;
  pull-merge-half pull; alex-commit commit; alex-push push; you-commit commit; refused none;
  pull-stops fetch; pull-merge pull; push-again push.
- **(r2)** `git pull` has no `-m` in git 2.43 (`git pull --no-rebase -m '...'` exits 129 with
  "unknown switch `m'"), so the recording cannot fix the merge message; the relative URL makes
  git's own message the same on every run instead.
