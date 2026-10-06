# How to read the map (draft, revision 4: picture first)

Draft of the time-travel theme's map guide. Part 1 says where it lives in the game. Part 2 is the
text players read. Part 3 lists every factual claim in part 2 with a way to check it against
git 2.43, and what I saw when I checked it myself (git 2.43.0, `GIT_CONFIG_GLOBAL=/dev/null`,
`GIT_CONFIG_NOSYSTEM=1`, fresh repositories made with `mktemp -d`).

Each factual sentence in part 2 ends with a claim tag such as **[C5]**. Map claims (how the
drawing behaves, not how Git behaves) are tagged **[M1]** and checked against the code.

## Revision 4: picture first (for fact-check)

The user asked for something more visual. Each section now opens with a figure, and the checked
text folds under "More", word for word. Only these are new:

| Tag | Change |
|---|---|
| figures | Each section's figure is drawn by the real map renderer from a tiny real repository: two slides run through `demos.frames` (a set-up, then one command), fixed identity, date and locale. The guide draws the repository after the command and plays the change from the drawing before it. The command under the figure is the slide's own git line. The **Figure** line in each section says what the tiny repository does. |
| K1-K10 | One short caption under each figure, with the Git word in bold, cut from checked sentences (the tags in brackets name them). These are the new words to check. |
| detached | "Now = HEAD"'s detached bullet becomes its own section, "Now without a label = detached HEAD", word for word. |
| intro | unchanged, now with "the past never changes" in bold as it always was in this draft |

## Revision 3: fixes from the revision 2 re-check

The re-check (end of `.scratch/review/map-guide-check.md`) found 18 of 22 changed sentences
correct and 4 imprecise. All four are fixed with the checker's sentences, plus its optional C32
tweak. Only these changed since revision 2:

| Tag | Change |
|---|---|
| M6 | "History a branch shares with `main`"; a line with no tab is history only a merge reaches: a branch merged and then deleted, or someone else's work that `git pull` merged in |
| C31 | `git branch -d` checks the branch you are on, or the archive's copy for a branch you pushed (its upstream), not any other branch |
| C25 | "Committing never moves `origin/main`" |
| C33 | drops "for good"; keeps "the reflog cannot bring them back" |
| C32 | the hash to use is the one in the warning's `git branch` line (in `git reflog`, the newest) |

## Revision 2: what changed after the fact-check

The fact-check (`.scratch/review/map-guide-check.md`) found 25 correct, 6 imprecise, 1 false and
3 misleading claims, plus untagged sentences. Every finding is applied. Only these sentences
changed or are new; everything else is word for word as checked:

| Tag | Change |
|---|---|
| intro (C1) | "moved a label" became "moved or removed a label" |
| C3 | adds "(the very first commit has none)" |
| C4 | a folder's list holds file types (such as executable) too |
| C6 | short hashes: usually seven characters, more in a big project or when seven would match two objects; 40 characters "in most repositories" (SHA-1) |
| C11 | the reflog keeps unlabelled commits about a month after you were last on them; `git gc` also runs on its own |
| C31 (new) | `git branch -d` refuses when no other branch has the commits; `-D` deletes anyway |
| C16 | HEAD has no branch, not the save point; `git switch -c` only before you leave; after leaving, `git branch <name> <hash>` (C32, new) |
| C12 | how the map shows which branch HEAD names (M7, new) |
| C18 | no commit is altered; your label moves onto the merge commit, the other stays |
| C21 | the game gets `origin` from `git clone`, not `git remote add` |
| C23 | `origin/main` moves when you fetch it or push `main`, not on every contact |
| C25 | reworded: "Your commits never move `origin/main`" |
| C27 | `--hard` throws away uncommitted changes to tracked files for good (C33, new), with the line "the past never changes, but your unsaved present can be lost" |
| M1 | the tooltip shows the subject too, and its date is the date the commit was first written |
| M2 | "higher means made later" (rebase keeps old dates) |
| M3 | "timelines", not "lines"; "does not tell you which is older" |
| M4 | a dashed line can appear under any save point whose parent is not drawn; the first commit has no line |
| M6 (new) | the map draws each save point once: shared history sits on `main`'s line, a branch's line starts where it split off, a line with no tab is merged history whose label was deleted |
| U2 | "the amber dial" became "the orange dial" |
| picture | "Timeline = branch" picture: "a line, in ink for `main` and in a colour for each other branch, with a tab naming it" |

**The branch lines (U1): I changed the words, not the drawing.** The map draws each save point
exactly once, on one line. Drawing shared history again on every branch's line would show one
commit as if there were copies of it, which contradicts the guide's own rule that one commit can
sit on several timelines at once. So the guide now says how the drawing works (M6). A later
refinement could show a whole timeline on demand, for example by highlighting every commit a tab
reaches while the pointer is on that tab, without drawing any commit twice.

---

## Part 1: where it lives

**Decision (approved): both a short legend and a full guide, the guide one click away.**

- **The legend stays in the key under every map** (lesson figures and the live panel): one
  short line per picture, metaphor next to Git's word, only for what the map shows. It stays
  short, so the graph keeps its room at 1280x800.
- **"How to read the map" is a button at the right end of the key's first line.** It opens the
  full guide (part 2) in a dialog: the browser's own `<dialog>`, which keeps keyboard focus
  inside and closes on Escape, like the game's other dialogs. The dialog scrolls; the map stays
  where it was.
- **First visit:** until the player has opened the guide once, the button carries a small "new"
  mark. Nothing opens by itself: an explainer that pops up would cover the quest text the
  player is reading. "Opened once" is remembered in the browser; if storage is blocked, the
  mark simply shows again next time.

The section "Coming later" is shown from the start, marked as a preview, so the words for
undoing and rewriting are fixed before those chapters exist.

---

## Part 2: the text players read

### How to read the map

Your project's history is drawn here as timelines of save points. Read every picture with one
rule in mind: **the past never changes.** Git never edits a commit. When history seems to
change, Git has written new commits or moved or removed a label, and the old commits are still
exactly as they were. **[C1]**

#### Save point = commit

**Figure `commit`:** a repository with one staged file, then `git commit`: the first save point
appears.

**Caption:** A **commit** is a snapshot of every tracked file, exactly as the staging area held it
when you committed. **[K1: C2]**

*The picture: a ring with a solid core.*

- A commit is a snapshot of every tracked file, exactly as the staging area held it when you
  committed, not as your working folder looked at that moment. **[C2]**
- It also records who made it and when (an author and a committer, each with a date), your
  message, and its parent: the commit it was made on top of (the very first commit has none).
  **[C3]**
- Its name, the hash, is computed from all of that. The files take part through a chain of
  hashes: each file's content has a hash, each folder's list of names, hashes and file types
  (such as executable) has a hash, and the commit records the hash of the top folder. **[C4]**
- So a commit seals everything about itself. Change one letter of one file, the message, a date
  or the parent, and the hash comes out different: that is a different commit. This is why a
  commit can never be edited, only replaced by a new one. **[C5]**
- The map shows the short hash: the first characters of the full hash, which is 40 characters
  long in most repositories. Git usually shows seven; it shows more in a big project, or when
  seven would match two objects. **[C6]**
- Hover a save point to see its full hash, its subject, its author and the date it was first
  written. **[M1]**

#### Lines = parents

**Figure `parents`:** one commit and a staged file, then `git commit`: a second save point grows,
its line drawing down to its parent.

**Caption:** Each line runs from a commit down to its **parent**, the commit it was made on top of.
**[K2: M2, C3]**

*The picture: the lines between save points.*

- Each line runs from a commit down to its parent. A commit is always drawn above its parents,
  so along one line, higher means made later. **[M2]**
- Across different timelines, height does not tell you which commit is older: the map orders
  commits by their parents, not by the clock. **[M3]**
- A short dashed line that stops under a save point means its parent is not drawn: the history
  goes back further than the map shows (it draws at most the newest 200 commits). The very first
  commit has no parent, so no line leaves it. **[M4]**

#### Timeline = branch

**Figure `branch`:** `main` with two commits, a branch `idea` made there, then `git commit` on
`idea`: `idea`'s tab moves up to the new commit, `main`'s stays.

**Caption:** A **branch** is only a label: a name that points at one commit. The label moves;
commits never do. **[K3: C7, C9]**

*The picture: a line, in ink for `main` and in a colour for each other branch, with a tab naming
it.*

- A branch is only a label: a name that points at one commit. Git stores it as a small file (or
  one line of a shared file, `packed-refs`) holding that commit's hash. **[C7]**
- The timeline is every commit you reach from the label by following parents, back to the
  first commit. **[C8]**
- The map draws each save point once. History a branch shares with `main` sits on `main`'s line,
  so a branch's coloured line starts where it split off, though its timeline runs on down to the
  first commit. A line with no tab is history that only a merge reaches: a branch merged and
  then deleted, or someone else's work that `git pull` merged in. **[M6]**
- When you commit, Git writes the new commit with the labelled commit as its parent, then
  moves the label onto the new commit. The label moves; commits never do. **[C9]**
- One commit can sit on several timelines at once: on every branch that reaches it. **[C10]**
- Deleting a branch removes the label, not its commits. `git branch -d` deletes it only when the
  branch you are on already has its commits (or, for a branch you pushed, the archive's copy has
  them); `git branch -D` deletes the label anyway. **[C31]**
- Commits that no label reaches leave the map. Git keeps them for a while, not for ever: the
  reflog, Git's record of where HEAD has been, remembers them for about a month after you were
  last on them. After that, Git's cleanup, `git gc`, which also runs on its own, can delete
  them. **[C11] [M5]**

#### Now = HEAD

**Figure `now`:** `main` and `idea` each with a commit of their own, HEAD on `main`, then `git
switch idea`: the dial and the HEAD tab travel to `idea`'s commit.

**Caption:** **HEAD** says where you are. Travelling changes no commit: only HEAD moves. **[K4: C12,
C15]**

*The picture: the orange dial, and the HEAD tab pointing at it.*

- HEAD says where you are. Usually it names a branch, and the branch names the commit. On the
  map, the HEAD tab sits next to that branch's filled tab; `git log` writes this as
  `HEAD -> main`. **[C12] [M7]**
- Your next commit attaches here: its parent is HEAD's commit, and the branch HEAD names moves
  onto the new commit. **[C13]**
- `git switch other` moves "now" to another timeline: HEAD then names `other`, and Git updates
  your working folder and staging area to that branch's last commit. Uncommitted changes come
  along when they do not collide with it; when they would be overwritten, Git refuses to switch.
  **[C14]**
- Travelling changes no commit. Switching back and forth leaves every commit and every branch
  where it was; only HEAD moves. **[C15]**

#### Now without a label = detached HEAD

**Figure `detached`:** two commits on `main`, `git switch --detach HEAD~1` and a staged file, then
`git commit`: a save point appears and only the "HEAD (detached)" tab moves onto it; `main` stays.

**Caption:** **Detached HEAD**: HEAD names a commit directly, not a branch, so no label moves when
you commit. **[K5: C16]**

- Detached HEAD: HEAD names a commit directly, not a branch, so no label moves when you commit;
  the map's tab reads "HEAD (detached)". You can commit there, but no branch holds those
  commits. Before you leave, `git switch -c <name>` gives them a label. If you have already left,
  Git's warning shows the hash to use in its `git branch` line (in `git reflog`, take the
  newest), and `git branch <name> <hash>` labels them. **[C16] [C32] [M7]**

#### Timelines joining = merge commit

**Figure `merge`:** `main` and `idea` each with a commit of their own, then `git merge --no-edit
idea` on `main`: a merge commit appears and both lines draw into it.

**Caption:** A **merge commit** is a commit with two parents (Git allows more). **[K6: C17]**

*The picture: a save point with an outer ring, where two lines meet.*

- A merge commit is a commit with two parents (Git allows more). The first parent is the commit
  you were on; the second is the tip of the branch you merged in. **[C17]**
- Its snapshot combines the changes of both timelines. No commit is altered: every commit keeps
  its hash. Only your branch's label moves, onto the merge commit; the other branch's label
  stays where it was. **[C18]**
- When your branch has no commits of its own since the other one split off, `git merge` makes
  no merge commit: it slides your label forward to the other tip. This is a fast-forward (ask
  for a merge commit anyway with `--no-ff`). **[C19]**

#### Milestone = tag

**Figure `tag`:** one commit tagged `v1` and a staged file, then `git commit`: `main` moves up, `v1`
stays.

**Caption:** A **tag** is a label that stays put: new commits do not move it. **[K7: C20]**

*The picture: a pennant.*

- A tag is a label that stays put: new commits do not move it. Moving a tag on purpose takes
  `git tag -f`. **[C20]**

#### Shared archive = remote

**Figure `archive`:** a practice copy (`git init --bare`) cloned, one commit pushed, a second made,
then `git push`: drawn is the practice copy, whose `main` moves up to the pushed commit.

**Caption:** A **remote** is another repository that yours knows by a name. `git push` sends it the
commits it is missing. **[K8: C21, C22]**

*The picture: the GitHub panel. In the game it is a practice copy on your machine that stands in
for GitHub.*

- A remote is another repository that yours knows by a name. `git clone` names the one you
  cloned from `origin`; that is how your repository in the game gets it. **[C21]**
- `git push` sends the commits the archive is missing, then moves the archive's branch label.
  Git refuses a push that is not a fast-forward, one that would leave out commits the
  archive's branch already has, unless you force it. **[C22]**

#### Last seen in the archive = remote-tracking branch

**Figure `seen`:** your clone and a teammate's clone of the practice copy; the teammate pushes a
commit, then you run `git fetch`: your `origin/main` moves up to it, your `main` stays.

**Caption:** **`origin/main`** is your repository's note of where `main` was in the archive when you
last fetched it or pushed it. **[K9: C23]**

*The picture: the dashed tab `origin/main`.*

- `origin/main` is your repository's note of where `main` was in the archive when you last
  fetched it or pushed it. Git moves it when you fetch, pull (which fetches first) or push
  `main`; it never moves on its own. **[C23]**
- When someone else pushes, the archive changes but your `origin/main` does not, until your
  next fetch. On the map, `origin/main` shows what you last saw, not what is there now. **[C24]**
- Committing never moves `origin/main`: `git switch origin/main` refuses, and
  `git switch --detach origin/main` visits it with a detached HEAD. **[C25]**

#### Coming later: undoing and rewriting, in the same words

**Caption:** A preview: later chapters teach these. The rule still holds: no commit is ever
edited. **[K10: the preview line below, unchanged]**

*A preview: later chapters teach these. The rule still holds: no commit is ever edited.*

- `git revert <commit>` adds a new save point whose changes cancel an old one. The old one stays
  on the timeline. **[C26]**
- `git reset <commit>` moves your branch's label, and HEAD with it, back to an earlier save
  point. The later commits are not edited: if no label reaches them they leave the map, and
  `git reflog` still lists them for a while. `--soft` leaves the staging area and the working
  folder as they are, `--mixed` (the default) resets the staging area, and `--hard` resets
  both. **[C27]**
- The past never changes, but your unsaved present can be lost: `--hard` throws away
  uncommitted changes to tracked files, and the reflog cannot bring them back, because it only
  remembers commits. **[C33]**
- `git commit --amend` writes a new commit in place of the last one and moves the label to it.
  The old commit is still in the reflog. **[C28]**
- `git rebase` copies save points onto a new base. Each copy has a new parent, so it gets a new
  hash. The label moves to the copies; the originals stay exactly as they were until Git's
  cleanup removes them. **[C29]**
- This is why rewriting commits that others already have causes trouble: they still have the
  originals, and Git refuses to push the rewritten branch unless you force it. **[C30]**

---

## Part 3: claims register

"Check" says how to verify on git 2.43; "Seen" is what my own run printed. Rows marked **(r2)**
are new or changed in revision 2; for those, the fact-check report's transcripts are evidence
too, cited as "FC".

| Tag | Claim | Check | Seen |
|---|---|---|---|
| C1 (r2) | Git never edits a commit; apparent history changes are new commits or moved or removed labels; old commits unchanged | Follows from C5. Amend, reset, rebase, revert and `git branch -D` each leave the old commit object: `git cat-file -t <old>` | `commit` printed for the old hash after amend, reset, rebase, branch deletion |
| C2 | Snapshot = every tracked file as staged, not the working folder | `echo two >> f; git add f; echo three >> f; git commit -m x; git show HEAD:f` | `HEAD:f` had `one two`, working copy `one two three`; untracked file absent from `git ls-tree -r HEAD` |
| C3 (r2) | Commit records author and committer (each with a date), message, parent(s); the first commit has none | `git cat-file -p HEAD`; `git log --format='%h [%p]' \| tail -1` | `tree`, `parent`, `author ...`, `committer ...`, message; first commit printed `parents=[]` |
| C4 (r2) | Hash computed from all of it; files via blob hashes, folders via tree hashes that include file types; commit records the top tree | `git cat-file commit HEAD \| git hash-object -t commit --stdin` equals `git rev-parse HEAD`; `git cat-file -p HEAD^{tree}` lists modes, types, hashes, names; `chmod +x f; git add f; git write-tree` gives a new tree | Equal hashes; FC C4: new tree after `chmod +x` alone |
| C5 | Any change (file, message, date, parent) gives a different hash | `git commit --amend -m other` and `git commit --amend --no-edit --date=...` each change `git rev-parse HEAD` | Three different hashes for the same tree |
| C6 (r2) | Short hash = first characters of the full hash; 40 characters in most repositories (SHA-1, the default; SHA-256 has 64); usually 7, more in a big project or when 7 would match two objects | `man git-config`, `core.abbrev` ("auto": computed from the number of packed objects, minimum 4); FC C6: 8 characters with 17006 packed objects, and two blobs sharing 7 characters shown with 8 | 7 characters in a small repository |
| C7 | A branch is a file (or a `packed-refs` line) holding a hash | `cat .git/refs/heads/main`; `git pack-refs --all; cat .git/packed-refs` | 40-character hash |
| C8 | Timeline = commits reachable from the label by parents | `git log main` (`man git-log`, "reachable from the given commits") | |
| C9 | Commit: new commit's parent is the old tip, then the label moves | `git log -1 --format=%p` equals the old `git rev-parse main` | Equal |
| C10 | A commit can be on several branches | `git branch other HEAD~1; git branch --contains HEAD~1` | Both `main` and `other` listed |
| C11 (r2) | Unlabelled commits: kept while the reflog names them, about a month (30 days) after HEAD was last on them; then `git gc`, which also runs automatically, can delete them | `man git-config`: `gc.reflogExpireUnreachable` 30 days, `gc.pruneExpire` 2 weeks; `man git-gc`: porcelain commands "run git gc automatically" when the repository has grown; `GIT_TRACE=1 git commit` shows `git maintenance run --auto` | FC C11: a branch deleted 6 weeks after its last commit was gone at the next `git gc` |
| C31 (r3) | `git branch -d` deletes only when the current branch (HEAD) has the commits, or the branch's upstream does; `-D` deletes the label anyway | `man git-branch`, `-d`: "fully merged in its upstream branch, or in HEAD if no upstream was set"; commit on `x`, switch to `main`, `git branch -d x`, then `git branch -D x`; FC re-check: refused although branch `y` had the commits; deleted with a warning when merged to `origin/x` only | `error: the branch 'x' is not fully merged.`; `Deleted branch x (was 65b6f98).` |
| C12 (r2) | HEAD usually names a branch; `git log` writes it `HEAD -> main` | `cat .git/HEAD`; `git log --oneline --decorate -1` | `ref: refs/heads/main`; `(HEAD -> main)` |
| C13 | Next commit's parent is HEAD's commit; the named branch moves | Commit on another branch, compare `%p` with HEAD before | Equal |
| C14 | Switch updates working folder and staging area; carries non-colliding changes; refuses when they would be overwritten | Untracked file survives `git switch`; a modified tracked file that differs between branches makes switch fail | `error: Your local changes to the following files would be overwritten by checkout` |
| C15 | Switching changes no commit and no branch | Compare `git rev-parse main other` before and after switching back and forth | Unchanged |
| C16 (r2) | Detached HEAD names a commit, not a branch; committing moves no label; no branch holds those commits; `git switch -c` labels them before you leave | `git switch --detach HEAD~1; cat .git/HEAD`; commit; `git branch --contains HEAD`; `man git-checkout`, DETACHED HEAD ("If we have not yet moved away from commit f ... git switch -c foo") | HEAD file held a hash; `git switch --detach main` then `git log --decorate -1` printed `(HEAD, main)`: the commit had a label, HEAD had none |
| C32 (r3) | After leaving, the warning's `git branch` line (or the newest in `git reflog`) gives the hash; `git branch <name> <hash>` labels it | FC re-check: with two commits left behind, the warning lists both and its `git branch` line names the newest | Commit while detached, `git switch main`, then `git branch rescue <hash>` | Warning `you are leaving 1 commit behind` with `git branch <new-branch-name> b17907e`; `git log -1 rescue` showed `b17907e lost`. FC C16: `git switch -c` after leaving labels the current commit instead |
| C17 | Merge commit: two parents, first = commit you were on, second = merged tip | `git cat-file -p HEAD` after `git merge feature` | Two `parent` lines in that order |
| C18 (r2) | Merging alters no commit; your label moves onto the merge commit; the other label stays | `git rev-parse feature main` before and after | `feature` unchanged; `main` moved to the merge commit (FC C18) |
| C19 | Fast-forward: no merge commit, the label slides; `--no-ff` forces one | `man git-merge`, FAST-FORWARD MERGE; merge a branch that is ahead | No new commit; last commit had one parent |
| C20 | A tag does not move on commit; moving needs `-f` | `git tag v1; git commit ...; git rev-parse v1`; `git tag v1 HEAD` | Tag unchanged; `fatal: tag 'v1' already exists`; `-f` moved it |
| C21 (r2) | `git clone` names the remote it cloned from `origin`; the game's players get it that way | `git clone ...; git remote`; `docs/DESIGN.md`, chapter `start`: "`git clone` from the lab's 'GitHub'" | `origin` |
| C22 | Push sends missing commits and moves the remote branch; non-fast-forward refused unless forced | Push after a commit the archive lacks, then after diverging | `! [rejected] main -> main (non-fast-forward)` |
| C23 (r2) | `origin/main` moves when you fetch (or pull) it or push `main`; not on other contact; never on its own | Push another branch: `origin/main` unchanged; push `main`: it moves; `git fetch` moves it; FC C23: `ls-remote`, `remote show`, `fetch origin feature` leave it | `origin/main 2e7f619` after pushing `rescue`; `f8eb2d4` after pushing `main` |
| C24 | Someone else's push does not move your `origin/main` until you fetch | Second clone pushes; compare `origin/main` with the archive's `main` before and after `git fetch` | Different before, equal after |
| C25 (r3) | Committing never moves `origin/main`; `git switch origin/main` refuses; `--detach` visits | Run both; commit while detached at `origin/main` | `fatal: a branch is expected, got remote branch 'origin/main'`; FC C25: `origin/main` unchanged after the commit |
| C26 | Revert adds a commit that cancels; the old one stays | `git revert --no-edit HEAD`; `git rev-list --count` +1; old hash still in `git log` | Count 3 to 4, file content back to before |
| C27 | Reset moves the label (and HEAD); later commits not edited, in reflog; `--soft`/`--mixed`/`--hard` | `git reset --hard HEAD~1; git cat-file -t <old>; git reflog`; modes with `git status --short` | `commit`; reflog `reset: moving to HEAD~1`; `MM f` (soft), ` M f` (mixed), clean (hard) |
| C33 (r3) | `--hard` discards uncommitted changes to tracked files; the reflog cannot bring them back (it records commits only); a change already staged may survive as a dangling blob until cleanup | `echo dirty >> f; echo u > untracked.txt; git reset --hard`; `git diff`; search `git reflog` | No tracked change left; `untracked.txt` still there; 0 reflog mentions. `man git-reset`, `--hard`: "Any changes to tracked files in the working tree since <commit> are discarded" |
| C28 | Amend writes a new commit, moves the label; old in reflog | `git commit --amend`; `git reflog` | `commit (amend)` entry and the old hash below it |
| C29 | Rebase copies with new hashes; the label moves; originals unchanged until cleanup | `git rebase main` on a topic branch; `git cat-file -t <old tip>`; `ORIG_HEAD` | New hashes; old tip still a commit on no branch; `ORIG_HEAD` = old tip |
| C30 | Pushing rewritten commits is refused unless forced | Push, amend, push again | `! [rejected] topic -> topic (non-fast-forward)`; `--force-with-lease` accepted |
| M1 (r2) | Tooltip: full hash, subject, author name, author date (the date first written; amend and rebase keep it) | `map.js`, `tooltip(commit)`; `repomap.COMMIT_FORMAT` uses `%at`; amend with `GIT_AUTHOR_DATE=2026-01-01` | Author date `2026-01-01 10:00:00` unchanged after amend; FC C29: rebase keeps the author date |
| M2 (r2) | A commit is drawn above its parents; along one line, higher = made later | `map.js`, `order()` ("children before parents"); FC M2: 0 edges with the parent not below | |
| M3 (r2) | Across timelines, height does not tell which is older | `map.js`, `order()` keeps `git log --topo-order`; FC M3: a newer commit drawn lower | |
| M4 (r2) | A dashed line under any save point whose parent is not drawn; at most 200 commits; no line from the first commit | `map.js`, edge kind `cut`; `repomap.MAX_COMMITS`; FC M4: a dashed line high up for an old merged branch | |
| M5 | The map draws commits reachable from branches, tags, remote-tracking branches and HEAD | `repomap._commits`: `git log --branches --tags --remotes` plus HEAD | |
| M6 (r3) | Each save point drawn once; history shared with `main` on `main`'s line; a branch's line starts at its split; a line with no tab = history only a merge reaches (a merged then deleted branch, or work `git pull` merged in) | FC re-check: a `git pull --no-rebase` merge drew "theirs" on a line with no tab; two side branches sharing a commit put it on the line of the name that sorts first | `map.js` header ("each branch tip ... claims the commits of its first-parent line that no earlier tip claimed"; trunk names claim first); FC U1 layouts | |
| M7 (r2, new) | The HEAD tab sits next to the filled tab of the branch it names; detached, the tab reads "HEAD (detached)" | `map.js`, `labelsOf` (HEAD first, then its branch with `current`); `theme-time.css`, `.map-label.is-current .tt-chip` (filled); `words.detachedHead` | |
