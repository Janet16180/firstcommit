# Share a file with Alex (draft, revision 1, for fact-check)

A figure in the boxes pictures: your computer, GitHub (the practice copy) and Alex's computer side
by side. Each computer stacks its working folder, its open box (the staging area) and its
repository (closed boxes on a timeline). It plays one step at a time, and each step has one
caption that says what Alex can see. Part 1 is how the figure is made, Part 2 the captions with
their claim tags, Part 3 the claims register.

---

## Part 1: how the figure is made

Every drawing is a snapshot of real git: a bare repository (`git init --bare github/project.git`)
and two clones, `you` and `alex`, with your commits as Robin Park and Alex's as Alex Kim, fixed
dates, git 2.43.0, no global or system configuration, `init.defaultBranch=main`. Before the first
step, you committed `README.md` and pushed it, and Alex cloned. After every step the generator
snapshots all three repositories and runs `changes.describe` on each, the same events the game's
feed shows. The arrows that light are the stepping person's commands (`TimePlaces.commands`) from
those events.

Two steps are checked by the generator itself:

- **Alex's `git pull` is shown in two halves.** At that point the generator copies Alex's clone,
  runs `git fetch` in the copy and snapshots it: that is the drawing between the halves. It then
  runs `git merge --ff-only origin/main` in the copy and fails unless the copy now matches,
  snapshot for snapshot, Alex's real clone after the real `git pull`.
- **The refused push.** The generator requires `git push` to fail, and fails unless all three
  snapshots are exactly as they were before it. The figure shows git's own output under the
  command.

The commands, as run:

| Step | Who | Commands |
|---|---|---|
| create | you | `echo 'Meeting at 10.' > notes.txt` |
| add | you | `git add notes.txt` |
| commit | you | `git commit -m 'Add the meeting notes'` |
| push | you | `git push` |
| pull-fetch, pull-merge-half | Alex | `git pull` (its two halves, as above) |
| alex-shares | Alex | `echo 'Bring the slides.' >> notes.txt`, `git commit -am 'Ask for the slides'`, `git push` |
| you-commit | you | `echo 'Start here.' >> README.md`, `git commit -am 'Say where to start'` |
| refused | you | `git push` (refused) |
| pull-merge | you | `git pull --no-rebase --no-edit` |
| push-again | you | `git push` |

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
  appears in Alex's staging area and working folder. Now Alex has it. **[S6]**
- **alex-shares**: Alex adds a line to `notes.txt`, commits and pushes: GitHub's `main` moves onto
  Alex's commit. Alex has the new line; your computer still has the old `notes.txt`. **[S7]**
- **you-commit**: You commit a change of your own, to `README.md`. Alex can't see it, and you
  don't have Alex's new line yet. **[S8]**
- **refused**: Your `git push` is refused: GitHub has Alex's commit, which your repository
  doesn't. Nothing moves, on your computer or on GitHub, and Alex still can't see your commit.
  **[S9]**
- **pull-merge**: `git pull` fetches Alex's commit and merges it with yours: a merge commit joins
  the two timelines, and your `notes.txt` gets Alex's line. Alex can't see your commit yet.
  **[S10]**
- **push-again**: Now `git push` works: GitHub gets your commit and the merge commit, and its
  `main` moves onto them. Alex will have them after the next `git pull`. **[S11]**

Other words: the people are labelled "You" and "Alex", GitHub's column "GitHub (the practice
copy)", the command line "You: $ git push" or "Alex: $ git pull". The arrows' spoken routes name
Alex's places on Alex's side ("fetch: from the remote repository to Alex's repository").

---

## Part 3: claims register

"Seen" is what the generator recorded (git 2.43.0): the feed events of each repository after the
step (`you`, `github`, `alex`), exit statuses, and git's output where it matters.

| Tag | Claim | Check | Seen |
|---|---|---|---|
| S1 | A new file is only in your working folder; Alex's clone and GitHub do not have it | `git status --short` in `you`; `ls` in `alex`; `git -C github/project.git ls-tree -r main --name-only` | events: you `file-created`; github and alex none |
| S2 | `git add` puts a copy in your staging area; Alex and GitHub unchanged | `git ls-files -s notes.txt` in `you`; compare `alex` and GitHub | events: you `file-staged`; github and alex none |
| S3 | `git commit` makes a commit in your repository only: committing shares nothing; GitHub and Alex unchanged | `git -C github/project.git rev-parse main` and Alex's refs before and after | events: you `commit-created`; github and alex none |
| S4 | `git push` moves GitHub's `main` to your commit; Alex's repository and folder unchanged until Alex fetches or pulls | Alex's `git rev-parse main origin/main` and `ls` before and after your push | events: you `remote-updated`, github `push-received`; alex none |
| S5 | `git pull` first fetches: Alex's `origin/main` moves to the new commit; Alex's `main`, staging area and working folder are unchanged at that point | `man git-pull` (fetch, then integrate); the generator's copy after `git fetch` | copy after `git fetch`: alex `remote-updated` only; `main`, files unchanged |
| S6 | Then the merge (a fast-forward here) moves Alex's `main`, and the file appears in Alex's staging area and working folder | Alex's `git ls-files -s`, `ls`, `git rev-parse main` after `git pull` | events from the halfway state: alex `branch-moved`; `notes.txt` in all three areas; the copy's `git merge --ff-only origin/main` matches the real pull exactly |
| S7 | Alex's commit and push move GitHub's `main`; your computer unchanged | your `git rev-parse main origin/main`, `cat notes.txt` | events: github `push-received`, alex `branch-moved`, `remote-updated`; you none |
| S8 | Your new commit is on your computer only; you do not have Alex's commit | GitHub's `main` and Alex's refs unchanged; your `git log` lacks Alex's commit | events: you `commit-created`; github and alex none |
| S9 | Your push is refused because GitHub has a commit you do not; nothing changes on your computer or GitHub | `git push`; exit status; snapshots before and after | exit 1, `! [rejected]        main -> main (fetch first)` with the hint to `git pull`; no events anywhere; all three snapshots identical (asserted) |
| S10 | `git pull --no-rebase` fetches Alex's commit and makes a merge commit with two parents; your `notes.txt` gets Alex's line | `git cat-file -p HEAD` (two parents); `cat notes.txt` | `Merge made by the 'ort' strategy.`, `notes.txt \| 1 +`; events: you `merge-commit-created`, `remote-updated` |
| S11 | The push is accepted and GitHub's `main` moves to the merge commit; GitHub then has your commit and the merge commit; Alex does not until the next pull | `git push`; `git -C github/project.git log --oneline`; Alex's refs | exit 0, `69c7214..20ab79b  main -> main`; events: you `remote-updated`, github `push-received`; alex none |

Notes for the checker:

- In "alex-shares" the feed reports Alex's commit as `branch-moved`, not `commit-created`, when
  the commit and the push are in one step. So only Alex's push arrow lights in that step, and the
  new box appears on Alex's timeline without flying from the open box. Splitting the step into
  three (edit, commit, push) would light each arrow in turn.
- "Alex can't see it" means Alex's computer does not have the file or commit. Someone could look at
  GitHub after a push; the caption for S4 says where the commit is.
