# The four places (revision 6: the revision 5 re-check applied, for fact-check)

**Revision 6** applies the revision 5 re-check and mapcheck's "Before revision 6" (both in
`.scratch/review/four-places-check.md`). New for the checker, marked **(r6)**: pull's rule is now
mapcheck's: every tracked file ends where the checkout of a pull would leave it, and a file only
in the folder is set aside only while it is there before and after (Part 1, "What lights up").
The reason sentence no longer claims a rebase keeps unsaved work, the limits are restated, and
`add` carries only what `git add` copied (Part 1, motion). Register rows L6 to L9 are new, run on
real git 2.43 labs like L1 to L5 (`rev6_check.py` in my job folder).

**Revision 5** applies the revision 4 re-check (`.scratch/review/four-places-check.md`, item 5).
New for the checker, marked **(r5)**: a merge of your own branch "does not light pull" (a merge
commit lights commit), and the reset sentence says "nothing uncommitted". The figure's rule
changed with it: pull lights only when every file that changed in the staging area or the
working folder also changed between the old tip and the new tip, so a `git reset --hard
origin/main` that throws away an unsaved line is no longer drawn as a pull (Part 1, "What lights
up"; register rows L1, L2 and L5).

**Revision 4** applies the revision 3 re-check. New for the checker, marked **(r4)**: pull lights
only for the branch's own upstream, and not for a reset that drops your commits (Part 1, "What
lights up"); pull's spoken route names the fetch arrow first and the repository's note reads
"closed boxes: the commits" (Part 2); the motion's time bound is restated after the motions were
slowed by about a quarter (Part 1, motion). `git commit -a` and `git push` in one batch now light
add, commit and push, since the feed tells that commit as made here. Register rows L1-L4 were
run on real git 2.43 labs, snapshots and feed (`upstream_check.py` in my job folder), and L5
with them in revision 5.

**Revision 3** draws the figure in the boxes language the user asked for: files are pages,
the staging area is an open box, commits are closed boxes on their timeline. It also draws
pull's merge half beside commit and add, so the arrow and the motion follow the same path in
both layouts. New for the checker, in one round, everything marked **(r3)**:

| What | Where |
|---|---|
| The pages-and-boxes picture and its claims P1-P4, B1-B4 | Part 1 "Drawn from", Part 3 |
| The two notes under the titles, "No commits yet." for an empty GitHub, "No files." | Part 2 |
| Each arrow's spoken route (its `aria-label`) and pull's short drawn label | Part 2 |
| The lighting table (unchanged since revision 2, never checked) | Part 1 |
| The motion paragraph | Part 1 |

The arrow sentences A1-A8 are unchanged from revision 2.

Revision 2 applies `.scratch/review/four-places-check.md`: A2's words and register row, A3, A4,
A5 and A6's words, the pull arrow's route (D1), the lighting rules (D2) and the fetch motion (D3).
The figure code (`theme-time-places.js`) carries these words exactly.

Draft of the "four places" figure: your computer (working folder, staging area, your repository
with `origin/main`) next to GitHub (the remote repository), with labelled arrows. Part 1 is the
design. Part 2 is every word the figure shows. Part 3 is the claims register: each arrow's claim
with a way to check it on git 2.43 and what I saw (git 2.43.0, `GIT_CONFIG_GLOBAL=/dev/null`,
`GIT_CONFIG_NOSYSTEM=1`, `init.defaultBranch=main` as the game sets it, nothing else; fresh
repositories made with `mktemp -d`; script: `arrows.sh` in my job folder, output quoted below).

---

## Part 1: design

**Drawn from what the game already has.** The figure takes the observation the live panel gets
(the project snapshot with its files, and the github snapshot), so it shows the player's own
files and commits:

- **(r3)** *Working folder*: each file is a page, with its name, the short id of its content
  (the blob id) and a colour from that id, so the same content always looks the same and a
  changed file shows another id. Under it, the change git status lists for it there
  ("modified, not staged", "untracked", ...). An untracked file is a page here and in no box
  (P1-P3). A file deleted from the folder is drawn as the gap its page left, while the open box
  still holds it (P4). The pages and words come from the same `areaRows` rule as the three areas
  strip, not a copy of it.
- **(r3)** *Staging area*: an open box, its flaps folded out, holding a page for every tracked
  file, not only the changed ones (B1), with git status's words for this column ("new file,
  staged", "modified, staged", ...). Its note: "open box: the next commit".
- **(r3)** *Your repository*: the commit graph, drawn by the real map renderer at a small size,
  with each commit as a closed box on its timeline, its short hash beside it as its label, the
  branch tabs, HEAD's dial and the dashed `origin/main` tab. Its note: "closed boxes: the commits".
  A commit holds every tracked file, and an unchanged file keeps its id, stored once (B2, B3).
- *GitHub (the practice copy)*: its commit graph, drawn the same way. **(r3)** An empty GitHub
  says "No commits yet." (it has no HEAD you are on, so the map's "You are on main..." would be
  wrong there).
- When there is no remote yet, the GitHub side says so instead of being drawn empty.

**Arrows**, each with its Git word and one short line:

```
            YOUR COMPUTER                                                GITHUB (the practice copy)
  working folder  --add-->   staging area  --commit-->  your repository  --push-->   remote repository
                  <--pull--  (open box)    <--pull--    (closed boxes)   <--fetch--
  <- - - - - - - - - - - - - - o - - - - - - - - - - - o - - - - clone (once) - - - - - - - - - - -
```

**(r3)** Each gap between two places holds a pair of arrows: the one towards GitHub above, the
one back below. The pull arrow is pull's merge half, drawn in two parts beside commit and add:
from your repository to the staging area, then on to the working folder, because the merge moves
your branch and updates the staging area as well as the working folder (D1). Both parts show the
word "pull"; the first part says the whole name and route aloud. Its fetch half is the fetch
arrow, which lights with it. The clone arrow runs from GitHub through your repository and the
staging area to the working folder, with a stop under each. Narrow, the figure stacks: your
computer above, GitHub below, the arrows between the rows pointing up and down, clone up the
right side.

**What lights up.** Every arrow that matches what just happened, from the same change the feed
reports plus your repository's two snapshots, never guessed. **(r4)** They light in a fixed order
(clone, add, commit, push or fetch, pull), which is only the figure's: no caption says which
command ran first.

| What happened (one batch) | Arrows |
|---|---|
| `file-staged` | add |
| `commit-created`, `merge-commit-created`, `commit-replaced` | commit |
| `push-received` (the practice copy's side) | push |
| `remote-updated` without `push-received` | fetch |
| **(r4, r6)** on the same branch and without a push, your branch's new tip reaches the tip of its upstream, `origin/<branch>`, which its old tip did not; it kept its own commits or replayed them on top; and every tracked file ends where the checkout of a pull would leave it | pull (its merge half): fast-forward, merge or rebase, whether or not the fetch was in the same batch |
| the repository appeared with an `origin/` branch (a clone) | clone |

So `git pull` lights fetch and pull; `git pull` or `git merge origin/main` after an earlier
`git fetch` lights pull alone; `git commit -a` lights add and commit; `git commit` and
`git fetch` together light commit and fetch, not pull. A merge commit or staging change made by
a pull belongs to pull, so it does not also light commit or add. A refused push and a diverged
`git pull` that stops after its fetch are shown as they are: nothing, and fetch alone (D4, D5).
**(r4)** `git commit -a` and `git push` in one batch light add, commit and push. Only the
branch's own upstream counts: **(r5)** `git merge feature` on `main`, after `git push -u origin
feature`, does not light pull (a merge commit lights commit), and `git pull` on `feature` takes in
`origin/feature`. `git reset --hard origin/main` lights nothing when it drops commits of yours
or **(r6)** ends anywhere a pull would not. A file whose tip version the pull does not change
keeps its staging-area and folder versions; one it changes takes the new version in both when it
was clean, and keeps both as they were when the new version was already staged; anything else
(an unsaved edit, an untracked file in the way, even with the incoming text) makes `git pull`
refuse. A merge or fast-forward changes only the files the commits changed, and keeps an unsaved
line in any other file (a rebase pull refuses to start while anything is unsaved). A reset
overwrites all of these, and deletes an untracked file in the way of a new one, and so does
`git clean`; a file only in the folder, untracked or ignored, before and after, says nothing
either way. When your branch had no commits of its own and nothing uncommitted, the reset ends
exactly where a fast-forward would, with the same files, and the two snapshots cannot tell them
apart, so it lights pull. **(r6)** The rule misses a real pull when, within one refresh of the
page, you also: stage or edit a tracked file the pull does not touch; stash, pull and pop a file
the pull also changes; or delete an untracked file. It also misses a pull over a file forced into
an ignored folder with `git add -f`. In those batches pull does not light. The upstream is
taken to be `origin/<branch>`, as `git clone` and `git push -u origin <branch>` set it; the
snapshots do not record a branch's upstream setting.

**(r3) Motion** (off under reduced motion), from the two snapshots like the map's motions. Each
lit arrow draws itself, then its work flies along it: a copy of a page, by name and content
colour, or a closed box with its short hash. A group of flights leaves once the one before it has
arrived, and what a flight brings shows in each place as it gets there: a new page appears, and a
known page's old id and colour fade out as the new ones, with git status's words for them, fade
in. `add` drops a copy of the page into the open box; the folder keeps its page. **(r6)** It
carries only files whose new staging-area version was in the folder before the batch, which is
what `git add` copies, so a file a pull checked out in the same refresh does not ride on it. `commit` lifts a
copy of the open box, holding a page for every tracked file, closes it on the way and sets it on
your timeline, where HEAD and the branch slide onto it; the open box keeps its pages. A push
carries the boxes GitHub is missing, oldest first, then GitHub's `main` and your `origin/main`
slide onto them. A fetch carries GitHub's new boxes into your repository and every `origin/`
name and new tag moves or appears; your branch and pages stay still, which is the point of the
picture (D3). A pull plays the fetch, then your branch moves and the changed pages leave your
repository, pass the open box (which updates as they pass) and reach the working folder. Only
commits that are on GitHub fly from GitHub: a merge or rebase commit appears in your repository.
A page the player edits or makes changes where it lies. **(r4)** A command's motion stays within about
two seconds however many files move, because the flights of one group spread over at most
300 ms: about 1.1 s for a push, 1.6 s for a pull, 1.8 s for a pull of many files and 2 s for a
big clone, the longest.

**Where it lives.** **(r5)** In the live panel beside the terminal, in place of the three areas
strip, under the same heading, from the first level on: your computer's three places while the
lab has no GitHub, all four once it has one. It is redrawn when either repository changes, lights
the arrows of what that batch did and plays its motion; the first drawing plays nothing. Later,
also as a lesson figure (a slide view next to `map`, `areas` and `objects`).

---

## Part 2: the words the figure shows

**(r3)** Notes under the titles: "open box: the next commit" (staging area), "closed boxes:
the commits" (your repository). Empty places: "No files.", "No commits yet." (GitHub). **(r5)**
Without a GitHub there is no remote place and no push, fetch, pull or clone arrow, and the figure
is said as `Your computer: Working folder, Staging area, Your repository` (with one, `The four
places: Working folder, Staging area, Your repository, Remote repository`). Pull's two parts each
read "pull". Each arrow's spoken route (`aria-label`), exactly:

- `add: from the working folder to the staging area`
- `commit: from the staging area to your repository`
- `push: from your repository to the remote repository`
- `fetch: from the remote repository to your repository`
- `pull = fetch + merge: the fetch arrow, then from your repository, through the staging area, to the working folder`
- `clone (once): from the remote repository, through your repository and the staging area, to the working folder`

**(r4)** Changed here: pull's route names the fetch arrow first, and your repository's note reads
"closed boxes: the commits" (it was "closed boxes: your commits").

Titles: **Your computer** (with *Working folder*, *Staging area*, *Your repository*) and
**GitHub (the practice copy)** (with *Remote repository*).

- **add**: copies a file's current content from the working folder into the staging area; the
  working folder keeps it. **[A1]**
- **commit**: saves the staging area as a new commit in your repository; the staging area keeps
  its files. Your branch moves onto the new commit, and `origin/main` does not move. **[A2]**
- **push**: sends the commits GitHub is missing and moves GitHub's branch to your commit; your
  `origin/main` moves to match. Git refuses a push that is not a fast-forward unless you force
  it, and a refused push changes nothing on either side. **[A3]**
- **fetch**: downloads the commits you do not have and moves `origin/main` (and the other
  `origin/` names). It changes no branch of yours, no working file and nothing in the staging
  area. **[A4]**
- **pull = fetch + merge**: a fetch, then a merge of `origin/main` into your branch (or a rebase,
  if you ask for one). When your branch has no commits of its own, the merge is a fast-forward:
  your branch slides forward, and the staging area and working folder update to match. When both
  sides have new commits, git fetches, then stops with an error that asks you to choose:
  `git pull --no-rebase` merges, `git pull --rebase` rebases. **[A5]**
- **clone**: downloads every commit, branch and tag from GitHub, names that remote `origin` and
  records its branches as `origin/main` (and other `origin/` names), then makes your own `main`
  from `origin/main` and fills the staging area and the working folder. **[A6]**
- `origin/main` lives in your repository, not on GitHub: it is your note of where GitHub's
  `main` was. **[A7]**
- The practice copy is a bare repository: commits and branches, no working folder. **[A8]**

---

## Part 3: claims register

| Tag | Claim | Check | Seen |
|---|---|---|---|
| A1 | `git add` copies the file's current content into the staging area; the working folder keeps the file | `echo two >> a; git add a; git diff --cached --name-only; ls` | staged `[a]`, folder `[a]`, status `M  a` |
| A2 | `git commit` makes a commit from the staging area; the branch moves; `origin/main` does not | `git commit`; compare `main` and `origin/main` | `main` cb365a3 to 67e7bc0; `origin/main` stayed cb365a3; staging area unchanged (`git ls-files -s` lists `a` and `b`, same blob ids), nothing left to commit (checker: index checksum `24259293` before and after) |
| A3 | `git push` sends missing commits, moves the remote's branch and your `origin/main`; non-fast-forward refused unless forced | archive's `main` and your `origin/main` before and after `git push`; diverge and push (map guide C22, C30) | archive `main` cb365a3 to 67e7bc0; `origin/main` 67e7bc0 |
| A4 | `git fetch` moves `origin/main` only: no branch, no working file, no staging change | someone else pushes; `cp a a.before; git fetch`; compare `main`, `a`, `git diff --cached` | `main` stayed 67e7bc0, `origin/main` to cc85ae2, `a` unchanged, status `## main...origin/main [behind 1]` |
| A5 | `git pull` = fetch then integrate: fast-forward when possible (branch and working file move); diverged, git 2.43 without `pull.rebase` stops after fetching and asks; `--no-rebase` merges | `git pull` when behind; then diverge and `git pull`; then `git pull --no-rebase`; `man git-pull` | ff: `main` to cc85ae2, `a` ends with `three`; diverged: `fatal: Need to specify how to reconcile divergent branches.` with hints `git config pull.rebase false # merge` / `true # rebase`, and `origin/main` had already moved to 1613b94; `--no-rebase`: merge commit 6cc3ea6 with parents 47f70ba 1613b94 |
| A6 | `git clone` copies the repository, names the remote `origin`, makes `origin/main`, makes `main` from it, fills the working folder and staging area | `git clone hub.git me; git remote -v; git branch -vv; git for-each-ref; git status` | `origin .../hub.git (fetch)`; `* main cb365a3 [origin/main] first`; refs `refs/heads/main`, `refs/remotes/origin/HEAD`, `refs/remotes/origin/main`; status clean with `a` in the folder |
| A7 | `origin/main` is a ref in your repository | `git for-each-ref` (above): `refs/remotes/origin/main` in your `.git`; the archive has no such ref | |
| P1 (r3) | The same content always has the same id (blob id); a page's colour comes from that id | Two files with the same text: `git hash-object rules.md copy.md`; `map.js`, `blobHue(blob)` | Both `6b1b585c99...` |
| P2 (r3) | A file changed in the folder shows another id there than in the staging area | `echo 'Ask early.' >> README.md`; `git hash-object README.md`; `git ls-files -s README.md` | folder `83d38e8f8d...`, staging area `f3860383ad...`, status ` M README.md` |
| P3 (r3) | An untracked file is in the folder only: not in the staging area, in no commit | New file, then `git ls-files -s`; after commits, `git ls-tree -r HEAD --name-only` | `ls-files` empty before any `add`; `notes.txt` absent from `ls-tree`, status `?? notes.txt` |
| P4 (r3) | A file deleted from the folder is still in the staging area and the last commit | `rm rules.md`; `git status --short`; `git ls-files -s rules.md`; `git ls-tree HEAD rules.md` | ` D rules.md`; both still list `6b1b585c99...` |
| B1 (r3) | The staging area holds every tracked file, not only the changed ones | Change and stage only README, then `git ls-files -s` | Both `README.md` and `rules.md` listed |
| B2 (r3) | A commit holds every tracked file; an unchanged file keeps its id | `git ls-tree HEAD~1`; `git ls-tree HEAD` after changing only README | `rules.md` `6b1b585c99...` in both commits; README `f386038` then `83d38e8` |
| B3 (r3) | Identical content is stored once | `git cat-file --batch-all-objects --batch-check` after those two commits | 2 commits, 2 trees, 3 blobs: `rules.md`'s blob once though both commits hold it |
| B4 (r3) | After a commit the staging area keeps its files and matches the new commit | `git ls-files -s` before and after `git commit`; `git diff --cached` | Unchanged; `diff --cached` empty (as the checker found for A2) |
| L1 (r5) | Merging a branch of yours into `main` does not light pull, even when that branch is on GitHub; a merge commit lights commit | Lab (clone of a practice copy): `git switch -c feature`, commit, `git push -u origin feature`, `git switch main`; then `git merge feature`; again with a commit of `main`'s own first; the feed's events and `TimePlaces.commands` on the two snapshots | fast-forward: `[branch-moved]`, lit `[]`; merge commit: `[merge-commit-created]`, lit `[commit]` |
| L2 (r5) | `git reset --hard origin/main` lights nothing when it drops a commit of yours; with no commit of yours and nothing uncommitted it ends as a fast-forward does and lights pull | Teammate pushes; commit locally, `git fetch`, then `git reset --hard origin/main`; again with no local commit | dropped a commit: `[branch-moved]`, lit `[]`; only behind, clean: `[branch-moved]`, lit `[pull]` |
| L3 (r4) | A pull lights for the branch's own upstream: `--rebase` on diverged branches, and `git pull` on `feature` tracking `origin/feature` | Diverge, `git pull --rebase`; `git push -u origin feature`, another clone pushes to `feature`, `git pull` | both `[branch-moved, remote-updated]`, lit `[fetch, pull]` |
| L4 (r4) | `git commit -a` and `git push` in one batch light add, commit and push | Edit README, then `git commit -qam 'More' && git push -q` as one batch | events `[commit-created, remote-updated, file-staged, push-received]`, lit `[add, commit, push]` |
| L5 (r5) | A reset that throws away an unsaved line lights nothing; a pull or a merging pull keeps the line and lights pull | Teammate pushes a change to `rules.md`; `git fetch`; append an unsaved line to `README.md`; then `git reset --hard origin/main`, or `git pull`; again diverged (a commit of yours) with `git pull --no-rebase` | reset: `[branch-moved, file-changed]`, lit `[]`; pull: `[branch-moved]`, lit `[pull]`; merging pull: `[merge-commit-created, remote-updated]`, lit `[fetch, pull]` |
| L6 (r6) | A reset over unsaved work in a file the commit changes lights nothing; `git pull` refuses there | Behind by one commit that changes `rules.md` (fetched); then each of: an unsaved line in `rules.md`; the incoming text in `rules.md`, unstaged; the incoming text staged plus an unstaged line; then `git reset --hard origin/main`; and `git pull` on the first state | resets: `[branch-moved, file-unstaged, file-changed]`, `[branch-moved, file-unstaged]`, `[branch-moved, file-changed]`, each lit `[]`; `git pull`: exit 1, "Your local changes to the following files would be overwritten by merge" |
| L7 (r6) | A pull whose incoming text is already staged lights pull, with or without an unstaged line on top, which it keeps | Same state; the incoming text staged; `git pull`; again with an unsaved line added after staging | both `[branch-moved]`, lit `[pull]` |
| L8 (r6) | A reset over an untracked file in the way lights nothing, also when it is identical or deleted, and so does a reset with `git clean`; `git pull` refuses there; a pull plus a new untracked file still lights pull | The incoming commit adds `new1.txt`, `new2.txt` or `doc/x.txt`; an untracked `new1.txt` "mine", `new2.txt` with the same text, or a file `doc`; `git reset --hard origin/main`; also `git reset --hard origin/main && git clean -fd` with `scratch.txt`; `git pull && echo scratch > scratch.txt` | resets: `[branch-moved, file-unstaged, file-changed]`, `[branch-moved, file-unstaged]`, `[branch-moved, file-deleted]`, `[branch-moved, file-deleted]`, each lit `[]`; `git pull` with `new2.txt` in the way: exit 1, "untracked working tree files would be overwritten by merge"; pull plus a new file: `[branch-moved, file-created]`, lit `[pull]` |
| L9 (r6) | In `git add README.md && git pull` (one refresh), add carries README.md only; pull does not light (a stated miss); `git pull --rebase` with anything unsaved refuses before fetching | Fetched, README.md edited, then the batch; diverged with an unsaved line, `git pull --rebase` | `[branch-moved, file-staged]`, lit `[add]`, add carries `[README.md]`; rebase: exit 128, "cannot pull with rebase: You have unstaged changes" |
| A8 | The practice copy is bare: no working folder | `git --git-dir=hub.git rev-parse --is-bare-repository`; `ls hub.git`; `kit.Lab.github` (`<lab>/github/project.git`) | `true`; `HEAD branches config description hooks info objects refs` |
