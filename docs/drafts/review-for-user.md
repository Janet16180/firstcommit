# Name tags and Time travel: ready for your review

> Prepared by designer, 2026-10-08 (updated after the fifth review). Drafts only: nothing in the game has changed yet.

## What to open

- **Sector 5, Name tags** (new, five levels): `docs/drafts/sector5/index.html`
- **Sector 8, Time travel** (today's sector 7, five levels): `docs/drafts/sector8/index.html`

Each level is a storyboard you step through with Next and Back. Next to it is a plain-text script
(`*-script.md`). Every command's output is real git, recorded from real repositories. Play sector
5 first, as a player would.

## What changed, and why

You said the time-travel sector was hard to follow: too many things on screen, and `git reflog`
never taught. The cause went deeper.

1. **The game never said what a branch, HEAD or `origin/main` is.** A new sector, Name tags, now
   says it before anything moves a name:
   - **5-1 Name tags:** a branch is a name for one commit; HEAD is "you are here"; `origin/main`
     is your bookmark of the mothership.
   - **5-2 A name on any commit:** names can be put on and taken off; the commits stay.
   - **5-3 Two experiments:** two branches off one commit; the chain forks into a tree, and
     `git switch` jumps between them while the folder changes. `git log --oneline --graph --all`
     draws the same tree in the terminal.
   - **5-4 One step:** a third experiment, made with `git switch -c` in one step, with
     `git checkout -b` and `git checkout` shown as the older forms you will meet at work.
   - **5-5 Match the chart:** a challenge where you make the names on a small forked tree match
     a target picture.
2. **One picture per idea, each thing drawn once.**
   - **The chain** (commits, name tags, the HEAD mark, pins for the mothership and Alex)
     replaces the stacked vault, mothership and Alex rows.
   - **The desk** (working folder and staging area) is used in 8-1.
   - **The move log** (`git reflog`, one row per line, newest first) is used in 8-4 and 8-5.
3. **Time travel teaches before it tests.** A new guided level, 8-4 "The move log", teaches
   `git reflog` and `HEAD@{n}` before the boss. Every prediction asks a real question. A check
   confirms that every challenge needs only commands taught earlier. The ticket challenge's
   `git switch -c` gap is now closed by 5-4; one older gap remains, in Collisions (`--no-edit`).

## What the fresh reviewers said

A new reader with no context played the storyboards each round.

| Round | Time travel | Name tags |
|---|---|---|
| 1 | 4 of 5 mostly clear; the move-log level confusing in parts | all mostly clear |
| 2 | 1 clear, the rest mostly clear, none confusing | 2 clear, 1 mostly clear |
| 3 | 3 clear, 2 mostly clear, none confusing | (reviewed together with round 2) |
| 4 (both sectors in order, a different model) | 8-1 clear; 8-2 to 8-5 mostly clear; none confusing | 5-2, 5-3, 5-4 clear; 5-1, 5-5 mostly clear |
| 5 (sector 5 with the tree) | (not changed since round 4) | 5-2, 5-3, 5-4 clear; 5-1, 5-5 mostly clear; none confusing |

Every reviewer solved both challenges unaided. The round 4 reviewer correctly explained what a
branch, HEAD and `origin/main` are, `git switch -c` and its older form `git checkout -b`, and the
difference between `git log` and `git reflog`.

Round 5 reviewed your request for a tree: 5-3 makes two experiments that fork the chain, 5-4
adds a third, and the challenge is a small forked tree. The reviewer understood the fork, why the
folder changes on each switch, and git's own drawing of the tree (`git log --oneline --graph
--all`).

**Fixed after round 5 (not reviewed again):**

- **5-3 is shorter:** 9 beats instead of 17. The first experiment was made "yesterday", and
  `engine.txt` is already written, so the player types six commands. The prediction ("is
  `engine.txt` still in your folder?") and the folder row stay; the folder row now stays on
  screen for the whole level, so nothing jumps.
- **Names never get cut off.** On a narrow screen a commit's name tags wrap onto a second line
  and the lines between commits follow; terminal lines wrap on phones instead of running off
  the edge.
- **A side line no longer runs past another experiment.** Each side line goes straight down its
  own column and turns into the commit it starts from just above it.
- **5-5 is no longer a checklist.** Each name in the captain's chart gets a tick once yours is
  in place, and three counts sit under it (names in place, HEAD in place, names the chart does
  not have). The player finds each difference by comparing.
- **5-1:** HEAD gets a beat of its own, after the names.
- **5-2:** the briefing says the pull happened before the mission, and when Rama explains
  parents, the lines light up one by one from `main` down to the first commit.
- **5-4:** the briefing no longer gives away the prediction, and Rama says git draws the same
  tree a little differently, so match the two pictures by name.
- Gold rings are only on the beat that pairs the chain with git's drawing.
- In every script, the hints and the solution now come last, after the design notes, so a
  reader does not see the answer first.

Earlier refinements, reviewed in rounds 4 and 5:

- **One new idea per beat.** HEAD's mark first, then the filled tag. `HEAD~1` gets a beat of its
  own after `git log`. Reset and `--hard` are now two beats.
- **The move log looks exactly like the terminal.** Each row is the line `git reflog` printed,
  and the matching terminal line lights up.
- **The 8-5 warning moved.** "The numbers count back from now" is now in its first beat, and
  the briefing is shorter.
- **Smaller fixes:**
  - 5-4 says why `switch` exists and to prefer it over `checkout`.
  - The gold ring now means only "look here", never a tag.
  - The designer captions are hidden behind a "designer notes" box.

## Decided

1. **Alex is green** across the whole game.
2. **Names:** "the move log" for `git reflog` ("el log de movimientos"); "Night shift" ("Turno de
   noche") for the time-travel boss; 8-4 is "The move log".

## For you to confirm: the layout

| Sector | Levels |
|---|---|
| 4 The mothership | as today, plus New recruit (the clone) moved here, before Base 7 |
| **5 Name tags** (new) | Name tags, A name on any commit, Two experiments (today's "A second course", reworked with a fork), One step (new), Match the chart |
| 6 Branches | Send a course up, Edits come along, Your first ticket |
| 7 Collisions | as today |
| 8 Time travel | Scrap the workshop, Recall the capsule, Wrong course, The move log, Night shift |

Proposed title and blurb for the new sector: **Name tags** / **Etiquetas**. "A branch is a name
for one commit, HEAD is where you are, and `origin/main` is your bookmark of the mothership."

After you confirm, the build spec for engine and frontend follows.
