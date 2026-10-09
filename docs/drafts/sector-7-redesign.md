# Sector 7 redesign: one idea, one picture

> Draft by designer, 2026-10-08, for the user to approve or reject. Nothing here is built yet.
> Screens of today's sector 7 are in `.scratch/sector7-design/before/`; the mockup is
> `docs/drafts/sector-7-mockup.html`.

## The recommendation in one paragraph

Sector 7 asks a beginner to learn four undo commands while the screen shows everything at once:
your station, Alex's band, the chart, a boundary called "black box" and a tape also called "black
box". The boss then needs `git reflog` and `HEAD@{1}`, which no level ever taught. The fix: add one
guided level, **7-4 The flight recorder**, that teaches `git reflog` and `HEAD@{n}` step by step;
move the boss to 7-5; and give every level **one picture** that shows its one idea and nothing else.
A new game-wide rule, **taught before tested**, makes this gap impossible again, and a test keeps it.

## What a first-time player sees today

I played 7-1 to 7-4 in headless Chrome at 1440x900, with the earlier views marked as seen (as for
a player who came through sectors 4 to 6).

| Screen | What the eye goes to | What confuses | Noise |
|---|---|---|---|
| 7-1 scene (`7-1-0-scene-1.png`) | a `main` label and an orange box called "reflog" | the scene shows dashed capsules, `main` and the reflog: ideas from 7-3 and 7-4, not 7-1. The level is about one file | all of it |
| 7-1 play (`7-1-1-open.png`, `-4-restore.png`) | the yellow-striped frame "Black box: what Git keeps" | `notes.txt` sits in the workshop and on the dock at once; the mothership says "out of range"; the WHAT IF is a grey box and a grey searchlight that mean nothing yet. The lines being lost (`power=99`, `overdrive=on`) are only in the terminal | six-item legend, four tabs, the mothership |
| 7-2 play (`7-2-1-open.png`, `-3-revert.png`) | three rows of cards, then two columns of commits | the same commits are drawn four times (your strip, your vault, the mothership, Alex's band). The revert commit looks like any other commit: nothing says "this undoes that". Alex's pull is not visible | the strip, Alex's band, the cargo dock (always empty) |
| 7-3 play (`7-3-1-open.png`, `-4-reset.png`) | the chart, then a tape that appears under it | the tape is born here but nothing asks the player to use it; it is below the fold at 900px. With `rescue` made first, no "ghost" ever appears, so the word in the debrief has no picture | Alex's band (Alex plays no part), the strip, the mothership column |
| 7-4 boss (`7-4-1-open.png`, `-3-reflog.png`) | the 7-1 frame "Black box: what Git keeps", with one commit in it | the frame named "Black box" has nothing to do with the problem; the tape below is also "black box". The tape runs oldest to newest, left to right, while `git reflog` prints newest first, top down, so tick and line never match. Only the chosen tick shows its `HEAD@{n}`. Ghost capsules exist only on the tape, never on the chart | the whole station row, the empty dock, Alex's band |

## Diagnosis, level by level

| Level | The one idea | Does the screen show it, and only it? | Untaught or too abstract |
|---|---|---|---|
| 7-1 Scrap the workshop | `git restore` throws away lines Git has no copy of | No. The lost lines are not drawn; the frame and the WHAT IF are abstract; the scene teaches 7-4 | "black box" as a name for a frame |
| 7-2 Recall the capsule | `git revert` undoes a shared commit by adding one; nothing is removed | Partly. The new commit appears, but its link to the strobe commit does not, and the commits repeat four times | none, but Alex's part is invisible |
| 7-3 Wrong course | `git reset` moves a label; the commits stay | Partly. The label moves on the chart, but the tape and the band compete with it | "ghost" is used in words, never shown; the tape is born with no job; `--soft` and `--mixed` in the debrief |
| 7-4 Black box (boss) | combine: find lost commits, label them, push | No. The biggest thing on screen is unrelated | `git reflog`, `HEAD@{n}` and `git branch <name> <where>` were never taught; the tape's order is the opposite of git's |

The root causes are three: a boss that tests commands no level taught; views that stack instead of
replace; and one name ("black box") for two different pictures.

## The new sector 7

| # | Title | Kind | The one idea | The player types | Prediction | The aha |
|---|---|---|---|---|---|---|
| 7-1 | Scrap the workshop | guided, P | `git restore` replaces a file; lines Git has no copy of are gone | `git diff`, `git restore engine.cfg` | "Could Git give the lines back afterwards?" (kept) | the two red lines dissolve in the workshop, while `notes.txt` glows safe inside the "Git has a copy" box |
| 7-2 | Recall the capsule | situation | `git revert` adds a commit that undoes another; the history keeps both | `git log --oneline`, `git revert HEAD~1`, `git push` | new: "After the revert, how many commits are on `main`: 3 or 4?" | the new capsule lands on top with an arrow back to the strobe one; then the mothership pin and Alex's pin climb onto it |
| 7-3 | Wrong course | situation, P | `git reset` moves a label; the commits stay | `git branch rescue`, `git reset --hard origin/main` | "Where are the two commits after the reset?" (kept) | `main` slides down two capsules; `rescue` stays on top, holding them |
| 7-4 | **The flight recorder** (new) | guided, P | `git reflog` lists every place `HEAD` has been; `HEAD@{1}` means "one move ago"; a label brings a lost commit back | `git log --oneline`, `git reflog`, `git branch survey HEAD@{1}` | "No label holds the two survey commits. Are they still in Git?" | `git log` does not list them, `git reflog` does; when the label lands, the faded capsules fill in solid |
| 7-5 | Black box (boss, was 7-4) | challenge | combines 3, 5, 7: find, label, push by name | `git reflog`, `git branch thrusters HEAD@{3}`, `git push -u origin thrusters` | none (a challenge) | the same picture as 7-4, so the player already knows how to read it |
| 7-6, 7-7 | Old blueprint, Adrift | situation | unchanged, optional | | | |

### 7-4 The flight recorder, in detail

Story: the day after 7-3, you made the same mistake, and this time you forgot the label. Setup:
the playground, two survey commits on `main`, then `git reset --hard origin/main`. The reflog
then reads, newest first: `reset`, `commit: Survey day 2`, `commit: Survey day 1`, `clone`.

Steps, in order:

1. **Predict.** "No label holds your two survey commits now. Are they still in Git?"
   Options: "No, the reset deleted them" / "Yes, Git still has them". Reveal: "Yes. A reset
   moves a label; it deletes no commit. But look what `git log` does."
2. **`git log --oneline`**: "Look for the survey in the history." Rama: "`git log` starts at a
   label and walks back. No label holds the survey, so it is not listed."
3. **`git reflog`**: "Ask the flight recorder where `HEAD` has been." The recorder is born here
   (see the picture below). Rama, once: "It works like your browser's history: every place you
   went, newest at the top, even the tabs you closed. It lives only on your computer."
4. **Answer**: "Which line is your last survey commit?" Options: `HEAD@{0}`, `HEAD@{1}`,
   `HEAD@{3}`. Reveal: "`HEAD@{1}`: where `HEAD` was one move ago, before the reset."
5. **`git branch survey HEAD@{1}`**: "Put the label `survey` on it." Rama: "The faded capsules
   filled in: a label holds them again."

Debrief, short: "`git log` only walks back from labels, so it could not see the survey.
`git reflog` lists every move of `HEAD`, newest first, and `HEAD@{1}` named the commit from one
move ago. `git branch survey HEAD@{1}` put a label on it, and both commits came back. The numbers
count back from now: after your next move, the same commit is `HEAD@{2}`. The recorder lives only
in your repository, and it forgets lost commits after about a month."

Card: `git reflog`: "Lists every place `HEAD` has been, newest first. `HEAD@{1}` is where
`HEAD` was one move ago. A commit no label holds can be found here and labelled again."

### The boss, adjusted

The boss keeps its story (a deleted branch `thrusters`) so it tests transfer, not copying. One
change to setup: after deleting the branch, you also switched to another branch and back, so the
thruster commit is `HEAD@{3}`, not `HEAD@{1}`. The player has to read the list, not repeat 7-4's
answer. Hints end with the exact lines, as now.

## The visual rule

**One picture per level.** Each level opens on one picture that shows its idea. Nothing else
stacks on it: no strip, no band and no tape unless the idea needs them. The tab row stays (older
views are one tap away), but the level never opens two views at once.

**One name, one picture.** "Black box" stops naming two things. 7-1's frame becomes **"Git has a
copy"**, a mode of your station; the reflog view becomes **"Flight recorder"** (glossary:
"registro de vuelo"). "Black box" stays only as the boss's title.

**The recorder reads like git.** The horizontal tape becomes a vertical list, newest at the top,
one row per `git reflog` line, in git's order and git's words: `HEAD@{n}`, the kind of move, the
hash, and a capsule chip (solid, or faded for a ghost). When the player types `git reflog`, the
rows light up one by one in step with the terminal's lines. Picking a row lights its capsule on
the chart beside it. Every new move pushes the list down one row and renumbers it, which shows
why `HEAD@{n}` shifts.

**Ghosts get one picture, born before they are needed.** A ghost is a faded, dashed capsule on the
chart: "no label holds it; Git still has it". It first appears in 7-3 (if the player resets first,
or in 7-3's "what if you hadn't labelled" moment), and is used in 7-4 and 7-5.

| Level | On screen | Hidden on purpose |
|---|---|---|
| 7-1 | your workshop with `engine.cfg`'s lines drawn (the experiment's two lines in red), and one box "Git has a copy" holding the staging area and the vault | the mothership, the legend, Alex, the strip, the tape. The abstract WHAT IF goes: the red lines dissolving on the real picture says it |
| 7-2 | the chart: one lane `main`, four capsules; three pins at the tip: You, Mothership, Alex (portrait) | the strip, Alex's band (Alex is a pin), the vault and mothership columns, hashes (on hover) |
| 7-3 | the chart: one lane, three capsules, the labels `main`, `origin/main`, `rescue` | the tape, Alex, the strip, the mothership column (`origin/main` is a label) |
| 7-4 | the flight recorder (left, about 60 percent) and a small chart with the faded survey capsules (right) | the zones, the strip, Alex, the mothership |
| 7-5 | the same as 7-4; on push, an `origin/thrusters` label and a tether appear | the zones, the strip, Alex |

### Mockups

7-1, after `git restore engine.cfg`:

```
+-------------------------+    +============ Git has a copy ============+
| Workshop                |    |  Staging area         Vault            |
|                         |    |  +--------------+     +--------------+ |
|  engine.cfg             |    |  | notes.txt    |     | [] Set the   | |
|   power=80              |    |  |  (safe)      |     |    engine    | |
|   ~power=99~   . . .    |    |  +--------------+     +--------------+ |
|   ~overdrive=on~  . .   |    +========================================+
+-------------------------+
  Rama: "Those two lines were never staged or committed. No copy anywhere."
```

7-3, the reset:

```
   capsule            labels
     [] Survey day 2  <- rescue          (stays)
     |
     [] Survey day 1
     |
     [] Start         <- origin/main
                      <- main   (slid down from the top)

  Rama: "main moved. The capsules did not."
```

7-4, after `git reflog`:

```
 FLIGHT RECORDER  (newest first, like git reflog)    |  CHART
 ----------------------------------------------------+--------------------------
 HEAD@{0}  reset    6c06ded  []                      |   :: Survey day 2  (faded)
>HEAD@{1}  commit   03242e9  ::  Survey day 2  <-----+---:: Survey day 1  (faded)
 HEAD@{2}  commit   bcee460  ::  Survey day 1        |   [] Start  <- main
 HEAD@{3}  clone    6c06ded  []                      |
                                                     |
 [] solid: a label holds it    :: faded: no label holds it, Git still has it
```

The HTML mockup draws these three screens in the game's colours.

### Fit with the history view redesign (p2/history-view)

Views' principle is "one place per thing, the chart is the hero, Alex secondary"; this proposal
follows it. Two points to agree on, asked of views and not answered yet: (1) today's draft chart
draws your vault and the mothership as two columns joined by dashed "same commit" lines; 7-2 and
7-3 here need one chain, with the mothership as a label (`origin/main`) or a pin, so each commit is
drawn once; (2) the ghost capsule (faded, dashed) should be a sign of that chart, not of the tape.

## Plain-language texts

- Short sentences; one idea per sentence; the simple past for what just happened ("`main` moved",
  "Git kept them"), as the glossary asks for Spanish ("`main` se movió", "Git los guardó").
- Git terms stay in English: reflog, `HEAD`, `HEAD@{1}`, branch, reset, revert.
- Say "label" when it is the picture, "branch" when it is the command, as the game does today.
- Drop from 7-3's debrief: `--soft` and `--mixed`, ghosts and the reflog (7-4 teaches them).
- Change 7-1's scene to the "Git has a copy" box and the workshop (today it shows the reflog).
- Change 7-2's scene captions: today they show unrelated hashes and "liftoff", "Phobos stop".

Spanish notes (for `docs/i18n-glossary.md`):

| English | Spanish | Note |
|---|---|---|
| Git has a copy | Git tiene una copia | the 7-1 box |
| flight recorder | el registro de vuelo | already in the glossary; the view's name |
| `HEAD@{1}`: where HEAD was one move ago | `HEAD@{1}`: donde estuvo `HEAD` hace un movimiento | simple past "estuvo" |
| ghost capsule | la cápsula fantasma | 7-4's Spanish already says "fantasmas" |
| your browser's history | el historial de tu navegador | the one place "historial" is right: it is the browser's word, not Git's history (still "la historia") |
| the faded capsules filled in | las cápsulas apagadas se llenaron | |

## The game-wide rule

**Taught before tested.** A challenge or boss may only need command shapes that an earlier guided
level's last hint typed. A shape is the subcommand, its flags, and any revision syntax:
`branch HEAD@{n}`, `revert HEAD~n`, `push -u origin`, `switch -c`.

Engine turns this into one test: walk the levels in play order, parse each last hint's `$` lines
into shapes, and fail when a challenge uses a shape no earlier non-challenge level used. I ran that
check today (`.scratch/sector7-design/taught.py`, 20 lines); it finds three gaps:

| Level | Untaught shape | Fix |
|---|---|---|
| 7-4 Black box | `reflog`, `branch <name> HEAD@{n}` | the new 7-4 |
| 5-5 Your first ticket | `switch -c` | teach it in 5-2 or 5-4 (`git switch -c` as the short form) |
| 6-4 Docking collision | `pull --no-rebase --no-edit` | add `--no-edit` to 6-1's line, or drop it from 6-4's hint |

Two companion rules for the page, checked by review rather than a test: **a sign is born in a
guided level** (never first seen in a challenge), and **a level's scene shows only that level's
idea**.

## Who does what

Engine (levels, texts, tests):

- New level 7-4 `The flight recorder` (EN and ES), with its tests and verification notes. Note: play
  order sorts by difficulty then id, and difficulties are 1 to 3, so engine picks an id or an order
  field that puts it after 7-3 and before the boss.
- 7-5 boss: one more move in setup (`HEAD@{3}`), hints and debrief updated.
- 7-3: tape off (`TAPE = False`), the debrief trimmed, the ghost wording moved to 7-4.
- 7-1: scene frames that show the box and the workshop; the "black box" wording becomes "Git has a
  copy".
- 7-2: a prediction step ("3 or 4 commits?"); scene captions fixed.
- The **taught before tested** test, and fixes for 5-5 and 6-4.
- Records: the per-level picture is the existing `view`; add `recorder` as a view name and drop
  the tape from 7-3.

Frontend, with the artist:

- One picture per level: a level opens on its view only; no strip, band or tape stacked unless the
  view says so.
- 7-1: "Git has a copy" box with the workshop's file lines drawn; the dissolve of the red lines.
- 7-2: the undo arrow from the revert capsule to the one it undoes; You, Mothership and Alex pins.
- The ghost capsule on the chart (faded, dashed), shared with views' history chart.
- The flight recorder: a vertical list in git's order, rows lit in step with `git reflog`'s output,
  a picked row lighting its capsule.
- New scene art for 7-1 and 7-4.

Changes to `chapters-5-9.md`: the sector 7 rows as above (five essential levels, 7-6 and 7-7
optional); the V6 row split into "Git has a copy" (a mode of your station, 7-1) and "Flight
recorder" (born in 7-4, the new level); the ghost sign's birth in 7-3; the taught-before-tested
rule next to the visual grammar.

## Decisions only the user can make

1. Add a level: sector 7 grows from four essential levels to five. (Recommended.)
2. Replace the horizontal recorder tape the artist drew this week (commits `42e9da8`, `9e46fda`)
   with a vertical list in git's order. (Recommended: matching the terminal matters more than the
   tape look.)
3. Allow one everyday comparison from outside Git, the browser's history, in one Rama line in 7-4.
4. The names: "Git has a copy" for 7-1's box, "Flight recorder" for the reflog view, "Black box"
   only as the boss's title.
