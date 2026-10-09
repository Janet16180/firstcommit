# What we teach, and the one picture for each idea

> Draft by designer, 2026-10-08, for the user to approve or reject. It comes before any level or
> screen redesign: first the ideas and their pictures, then the levels. The mockup is
> `docs/drafts/teaching-pictures.html`. Screens from today's game are in
> `.scratch/sector7-design/before/`.

## The recommendation

The game needs **four pictures, not eight views**. Each picture shows one kind of thing, and each
Git idea from sector 5 on is a change to one of them:

| Picture | What it is | Everyday comparison |
|---|---|---|
| **The chain** | the commits, each joined to its parent, with sticky labels on them and a "you are here" ship | a family tree with name tags |
| **The desk** | the working folder and the staging area, with a dashed outline round what Git has a copy of | your desk, and the tray of things ready to file |
| **The move log** | the reflog: every place `HEAD` has been, newest at the top, in git's own order | your browser's history |
| **Two sides** | one conflicted file, your lines and Alex's | two drafts of the same page |

People are not pictures. You are the ship on the chain. The mothership and Alex are **pins** on the
chain ("the mothership has up to here", "Alex has up to here"). Alex's desk is shown only when
Alex's files are the point of the level.

**At most two pictures on screen, one large and one small.** Each picture is drawn once. A commit
never appears in two places.

## One meaning per colour

Each colour means one thing everywhere. Today's game breaks this rule once: Alex is pink
(`--z-re`), the same colour as the mothership (`orbit.css:619`, `orbit.css:857`,
`art-style.css:443`). My first draft also gave Alex teal, which already means the staging area.
The fix: **Alex gets green, a colour no place uses.**

| Colour | Means | Token |
|---|---|---|
| orange | the working folder | `--z-wd` |
| teal | the staging area | `--z-st` |
| violet | your repository, and you | `--z-va` |
| pink | the mothership | `--z-re` |
| **green** | **Alex** (new: `#3D8A18` light, `#A6E05A` dark) | new token, e.g. `--who-alex` |
| red | a new file, a conflict | `--s-new` |
| amber | an edited file | `--s-mod` |
| gold | "look here" (a highlight, never a thing) | `--gold` |

A person's colour never comes alone: Alex's pin and band always carry Alex's name or portrait,
so a reader who cannot tell green from orange still knows who it is. Moving Alex from pink to green
changes shipped pages (two sides, the strip, Alex's station art). That is a game-wide change for
the user to approve.

The "Git has a copy" outline is drawn in neutral ink, not green, so green stays free.

## What I saw today

I played sector 7 (7-1 to 7-4) and two history levels (5-2 "A second course", 6-1 "Two crews meet").

- In 5-2 and 6-1 **the history chart is empty**: the History tab shows the folded strip and a
  blank bar, so "a branch is a label" has no picture at all (`5-2-1-open.png`, `6-1-3-merge.png`).
  This looks like a bug in levels with no mothership. The CSS rule that hides the workshop and dock
  in history (`orbit.css:935`) also hides the black box wrapper that now holds the vault. Frontend
  should check this whatever we decide here.
- In crew levels (7-2, 7-3) one commit is drawn up to four times: the strip's vault card, the
  chart's vault column, the mothership column and Alex's band.
- "Black box" names two different pictures, a frame (7-1) and a tape (7-3, 7-4). The tape runs the
  opposite way to `git reflog`'s output.
- Ghosts, `HEAD@{n}` and the reflog appear in words before any picture or guided level teaches them.

## The ideas, one by one

Each idea has five parts: the sentence, the misconception, the picture, the change when you type,
and what else is on screen.

### 1. A commit is a snapshot with a parent

- **Sentence:** A commit is a saved photo of the whole project, and each one remembers the photo
  before it.
- **Misconception:** "A commit saves only my change", or "a commit belongs to a branch".
- **Picture:** the chain. A capsule with its message, and a line down to its parent. Clicking it
  opens the files it holds (all of them, not a diff).
  Not drawn: the hash (on hover only), author details (a colour stripe is enough), file lists.
- **When you type** `git commit`: a new capsule lands on top of the one you are on, its line
  drawn to it. The label you are on and the ship ride up with it. The staged files on the desk
  fly into it.
- **On screen:** the chain (large) and the desk (small).

### 2. A branch is a movable label

- **Sentence:** A branch is a name tag stuck on one commit; when you commit, your tag moves up to
  the new one.
- **Misconception:** "A branch is a copy of my files", or "a folder".
- **Picture:** a tag on a capsule. Two branches on the same commit are two tags on one capsule.
  The chain splits into two lines only when the histories really split.
  Not drawn: a coloured lane per branch before it has its own commits; copies of files.
- **When you type** `git branch scout`: a second tag appears on the same capsule. Nothing else
  moves: no new capsule, no files. Then `git commit` on `scout`: only the `scout` tag climbs, and
  `main` stays.
- **On screen:** the chain alone.

### 3. HEAD is "you are here"

- **Sentence:** `HEAD` marks where you are standing: usually on a branch's tag, and your folder
  shows that commit's files.
- **Misconception:** "HEAD is the newest commit", or "HEAD is a branch".
- **Picture:** the ship, sitting on the tag you are on. If you stand on a bare commit (detached),
  the ship sits on the capsule itself, with no tag under it.
  Not drawn: the word HEAD as a separate label (the ship is HEAD; its tooltip says so).
- **When you type** `git switch main`: the ship hops from `scout`'s tag to `main`'s. On the desk,
  the files change to match: `probe.txt` flies back into `scout`'s capsule.
- **On screen:** the chain (large) and the desk (small). Here the desk is part of the idea.

### 4. `origin/main` is what you last saw of the mothership

- **Sentence:** `origin/main` is your note of where the mothership's `main` was the last time you
  checked; it does not update by itself.
- **Misconception:** "`origin/main` is live", or "push and pull happen automatically".
- **Picture:** a hollow tag `origin/main` on the chain (your note), and a red **mothership pin**
  where the mothership really is. Most of the time they sit together. When they differ, that gap
  is the lesson.
  Not drawn: a second column with the mothership's own copy of every commit.
- **When you type** `git fetch`: new capsules arrive faded in from the top, and the hollow
  `origin/main` tag jumps to the mothership pin. Your `main` does not move. `git push`: your
  capsules rise, and the mothership pin and `origin/main` climb to your `main`. `git pull` is the
  fetch, then the merge.
- **On screen:** the chain alone. The pin is the mothership.

### 5. Diverged histories

- **Sentence:** When you and the mothership both added a commit after the same one, the chain
  forks into a Y, and Git cannot simply put one on top of the other.
- **Misconception:** "Git will just add mine on top", or "a refused push is an error".
- **Picture:** a Y: two capsules with the same parent, `main` on one and `origin/main` on the
  other. The counts "1 ahead, 1 behind" sit by the fork.
  Not drawn: the shared history below the fork (folded into "+N").
- **When you type** `git push`: your capsule flies up, hits the pin and bounces back, and the Y
  stays. `git fetch` reveals the second arm.
- **On screen:** the chain alone.

### 6. A merge joins two lines

- **Sentence:** A merge makes a new commit with two parents, so both lines of work are in it.
- **Misconception:** "A merge copies one side over the other", or "it deletes the branch".
- **Picture:** the Y closes into a diamond. The new capsule has two lines down, one in each
  person's colour.
  Not drawn: the files (the result is just a commit); the merged branch's tag does not disappear.
- **When you type** `git merge scout`: a capsule appears on top with two parent lines, and `main`'s
  tag climbs onto it. `scout`'s tag stays where it was. If only one side had moved, there is no new
  capsule: `main`'s tag just slides up (a fast-forward).
- **On screen:** the chain alone. With a conflict, the chain is small and two sides is large.

### 7. Restore, revert, reset: three different undos

- **Sentence:** `restore` changes a file on your desk, `revert` adds a commit that undoes an older
  one, and `reset` moves a tag back. Each one changes a different thing.
- **Misconception:** "Undo means delete", "Git can always give my lines back", and "reset deletes
  commits".
- **Picture:** the same rule every time: **one kind of thing moves.**

  | Command | What moves | Where you see it |
  |---|---|---|
  | `git restore file` | a file's lines, on the desk | the desk |
  | `git revert <commit>` | a new capsule lands on top, its pattern the mirror of the one it undoes, with a thin line back to it | the chain |
  | `git reset --hard <where>` | a tag slides down; the capsules stay where they were | the chain |

  Not drawn: anything that does not move in that command.
- **When you type** `git restore engine.cfg`: the file's unsaved lines, drawn on the desk in red,
  dissolve. They sit outside the dashed outline "Git has a copy", so nothing can bring them back.
  `git revert HEAD~1`: the mirror capsule lands, and the pins climb onto it after a push and a pull.
  `git reset --hard origin/main`: `main`'s tag slides down two capsules, and the capsules stay.
- **On screen:** one picture per command: the desk for restore, the chain for revert and reset.

### 8. The reflog is the move log

- **Sentence:** Git writes down every place `HEAD` has been, newest first; `HEAD@{1}` means "where
  I was one move ago".
- **Misconception:** "`git log` shows everything", and "what I cannot see is gone".
- **Picture:** the move log, a list that matches `git reflog`'s output line for line: `HEAD@{n}`,
  what happened (commit, switch, reset), and a small capsule chip, solid or faded.
  Not drawn: a horizontal tape (it reads in the opposite order to git); timestamps; other people's
  move logs (each copy has its own).
- **Name:** "the move log" (Spanish "el log de movimientos"): the log of HEAD's own moves, next to
  `git log`, the log of commits. It maps to the command's name (ref-log). Not "diary" or "trail"
  (they need HEAD explained first and match no git word), not "flight recorder" (3-3's title, for
  `git log`), and not "black box" (1-2's name for `.git`). The sector 7 boss, once "Black box",
  becomes "Night shift", so each name means one thing in the whole game.
- **When you type** `git reflog`: the rows light up one by one with the terminal's lines. Any other
  move adds a new row at the top and pushes the rest down, so every `HEAD@{n}` grows by one, and you
  can see why the numbers shift. Picking a row lights its capsule on the chain.
- **On screen:** the move log (large) and the chain (small).

### 9. A lost commit is a ghost, not gone

- **Sentence:** A commit with no tag on it is hidden from `git log`, but Git keeps it for a while,
  and a new tag brings it back.
- **Misconception:** "Deleting a branch or resetting deletes the commits."
- **Picture:** a faded, dashed capsule, still joined to its parent by a faint line. Ghosts are
  drawn only in levels from the reset level on, where they are the point.
  Not drawn: ghosts in ordinary levels (they would confuse more than help).
- **When you type** `git reset --hard origin/main` with no tag on the old commits: the capsules
  lose their tag and fade to ghosts. Then `git branch survey HEAD@{1}`: a tag lands on the ghost,
  and it fills back in solid, its parent with it.
- **On screen:** the chain, with the move log when the level asks you to find the ghost.

## How the pictures combine

| Kind of level | Large | Small | Hidden |
|---|---|---|---|
| sectors 1 to 3 (files, staging, commits) | the desk | the chain (from the first commit) | pins, move log |
| branches and switching (5-2, 5-4) | the chain | the desk, because files change on a switch | the move log, Alex's desk |
| mothership, fetch, push, pull (4-x, 5-3, 8-5) | the chain with the mothership pin | none | the desk, unless a file matters |
| teammates (Alex) | the chain with Alex's pin | Alex's desk, only when Alex's files matter | your desk |
| merge (6-1) | the chain | none | everything else |
| conflict (6-2 to 6-4) | two sides | the chain | the desk |
| restore (7-1) | the desk with "Git has a copy" | none | the chain |
| revert, reset (7-2, 7-3) | the chain | none | the desk, the move log |
| reflog, ghosts (7-4, 7-5) | the move log | the chain | the desk |

## Today's views, mapped

| Today | Becomes | Why |
|---|---|---|
| Your station (V1) | **the desk**; its vault becomes the chain | one place per thing |
| Crew view (V3) | **drop** as a standing view; Alex becomes a pin, and Alex's desk appears only when needed | Alex is secondary |
| Station strip (V2) | **drop**; the small desk replaces it | the strip repeats the vault and the mothership |
| Crew band (V3 band) | **drop**; Alex's pin on the chain | it repeats the chain |
| History (V4) | **the chain**, one chain with the mothership as a pin and `origin/*` tags | no second column, so no commit is drawn twice |
| Two sides (V5) | **keep, with three changes** (below) | it shows one idea, but every line looks equally broken |
| Black box boundary (V6, 7-1) | **merge into the desk**, as the dashed outline "Git has a copy" | it is a property of the desk, not a view |
| Tape (V6, 7-3) | **the move log**, vertical, in git's order | it must match the terminal |

The tab row can then be at most four tabs: Desk, Chain, Move log, Two sides. Each is born in the
level that first needs it.

## Two sides: three changes (from the conflict prototypes)

The conflicts agent's prototypes (`docs/drafts/conflict-poc/`, from `index.html`) end on the same
merge picture as idea 6: one parent line in each person's colour. They also show three things
"two sides" needs:

1. Mark only the clashing lines with the red crack; today every line has the same weight.
2. Show the lines Git already merged on its own, so a conflict does not look like the whole file
   failed.
3. Tie each half to the `<<<<<<< HEAD` / `>>>>>>> branch` text the player sees with `cat`
   (their `markers.html`).

A risk to say in the levels: `git restore --theirs` takes the other side's whole file, including
lines Git had merged cleanly from your side. In their real conflict, `restore --ours` undid
Alex's merged change.

## Then, the levels (outline only, after these pictures are approved)

- Add a guided level before the sector 7 boss that teaches `git reflog`, `HEAD@{n}` and
  `git branch <name> <where>`, with the move log born there. The boss becomes 7-5.
- Game-wide rule, **taught before tested**: a challenge may only need commands an earlier guided
  level typed. A test checks it; today it finds three gaps (7-4, 5-5 `switch -c`, 6-4
  `--no-edit`). The script is `.scratch/sector7-design/taught.py`.
- Each sector 7 level opens on one picture as in the table above. The details are in
  `docs/drafts/sector-7-redesign.md`, to be revised once these pictures are decided.

## Decisions for the user

1. Four pictures (chain, desk, move log, two sides) replace today's eight views and bands.
2. Alex and the mothership become pins on the chain, not stations of their own.
3. Ghosts are drawn only from the reset level on.
4. The move log is a vertical list in git's order, replacing the horizontal tape the artist drew this
   week.
5. Two everyday comparisons in Rama's lines: a family tree with name tags (the chain) and your
   browser's history (the move log).
