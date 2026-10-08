# Chapters 3 to 7: the lead's decision

Decided on 2026-10-07 from a three-way debate: teacher (learning science), incidents (real
situations at work) and gamer (game design). Their proposals and rebuttals are in
`.scratch/debate/`. This file is what gets built; the optional levels are kept for after the
playtests.

## Rules every level follows

- **Git and GitHub only.** Shell lines (`ls`, `cat`, `echo ... > file`, `cd`) are given in full
  when they are not the lesson, and no level is about them.
- **No editor ever traps a player.** The game's gitconfig sets `core.editor = true`, so a bare
  `git commit` stops with "Aborting commit due to empty commit message" and commits nothing
  (a shared reaction then teaches `-m`), while `merge`, a merging `pull`, `revert` and
  `commit --no-edit` keep git's prepared message. Levels and cards use `-m` and `--no-edit`.
- **One new idea per level.** Guided levels name commands in their goals; situations tell a
  story and name outcomes; challenges and bosses give the end state only.
- **Predictions** are a choice of two or three buttons, at most one per guided level, any
  answer passes, no star or XP cost. They go only where a named myth breaks (marked P below).
  Checked answers (a hash, an author) use the existing answer step.
- **Checks read end states**, so every safe route passes. Typed lines may be a goal only in
  guided levels and situations where looking is the lesson (`git status` before and after
  `git fetch`), never in a challenge. Typed lines always feed Rama and par.
- **Lost work is said, not hidden.** When setup's saved facts show the player's work is gone
  for good, the level says so and offers Retry.
- **`pull.rebase` stays unset**, as git ships. 4-4 teaches the choice with git's real error;
  `--no-rebase` and `--rebase` both pass. Conflict checks read file content, because ours and
  theirs swap sides under a rebase, and Rama says so the first time it matters.
- **The stand-in GitHub keeps a reflog** (`core.logAllRefUpdates = true`), so a force push can
  be seen and undone.
- **Alex** is the teammate (they/them). Alex acts through `kit.press`, at setup or live.
- **Staged scenarios are real git.** What the design animated as a story (the stowaway riding
  the conveyor, Alex's capsule docking, three capsules vanishing) is a real change made by a
  level event, after the page's first observation, so the page animates what really happened.

## Challenges

One closes each chapter from 3 on, one every four or five levels. The brief and goals give only
the end state, written as facts ("`keys.txt` is in no capsule, here or on the mothership"). No
goal names a command, the command card stays hidden until solved, goals tick in any order, and
Rama speaks only about danger (`--force`, a committed secret) and errors. Hint 1 names the
chapters to recall, hint 2 the ideas; each lowers the XP a little. A challenge opens with the
alarm scene and shows as a boss node on the map. Every challenge combines at least two earlier
chapters and introduces nothing new.

## The levels

E = essential, built now. O = optional, written up in the debate files, built after playtests.
P = has a prediction.

| Ch | Level | Title | The one idea | Kind | Scene or staged scenario | E/O |
|---|---|---|---|---|---|---|
| cargo | 2-2 | Selective cargo | you stage file by file; the keys stay out | guided | staged: the keys file pulses in the workshop | E |
| cargo | 2-3 | Stowaway | unstaging keeps the file (setup commits first) | situation | staged: the night shift's `git add .` carries the keys onto the dock | E |
| cargo | 2-4 | Stale copy | the dock holds the file as it was when added | guided, P | two copies side by side | O |
| cargo | 2-5 | Junk bay | `.gitignore` keeps generated files out | situation | staged: a build folder floods the workshop | O |
| vault | 3-1 | Seal the capsule | a commit seals the dock, on this computer only | guided, P | scene: capsule, chain; the mothership stays dark | E |
| vault | 3-2 | Look before you seal | `git diff` and `git diff --staged` | guided | staged: overnight edits, one typo | E |
| vault | 3-3 | Flight recorder | history is readable: find the commit, its hash and author | situation (answer) | staged: an oxygen alarm; the found capsule glows | E |
| vault | 3-4 | Forgot one | `commit --amend --no-edit` before anyone sees it | situation | the capsule reopens and reseals | O |
| vault | 3-5 | Cargo inspection | cargo and vault: one clean capsule, the secret in none | challenge | alarm; staged: a stowaway arrives | E |
| mothership | 4-1 | Make contact | a remote is a name for an address; nothing travels | guided, P | scene: orbit; the antenna lights, nothing flies | E |
| mothership | 4-2 | Launch | push copies commits, only commits | guided, P | scene: rocket; an uncommitted edit stays behind | E |
| mothership | 4-2b | Two halves of a ship | two people work at once on different parts; Git puts the pieces together | guided | crew view; live: Alex pushes the engine half; launch moment when both halves meet | E |
| mothership | 4-3 | Incoming transmission | status knows the mothership only as of the last fetch | situation, P | scene: pull; staged: Alex's capsule docks | E |
| mothership | 4-4 | Push refused | a refused push loses nothing; pull with `--no-rebase` or `--rebase` | situation | live: Alex pushes after your commit; your capsule bounces | E |
| mothership | 4-5 | Base 7 | liftoff to mothership from a plain folder, the debris left out | boss | scene: alarm with the meteorite; the zones start empty | E |
| branch | 5-1 | New recruit | a clone holds the whole history; `main` and `origin/main` are labels | guided (answer) | staged: an outpost blinks; the chain copies down | E |
| branch | 5-2 | A second course | a branch is a label; switching swaps the workshop | guided, P | scene: fork; the label slides, files swap | E |
| branch | 5-3 | Send a course up | push sends one branch, by name | guided | only that branch's chain rises | E |
| branch | 5-4 | Your first ticket | a branch pushed for review, `main` untouched here and there | challenge | alarm; live: Alex pushes to `main` meanwhile | E |
| branch | 5-5 | Urgent call | uncommitted work is on no branch: stash or a WIP commit | situation | staged: the captain's call; git refuses the switch | O |
| conflict | 6-1 | Two crews meet | a merge joins two histories in a capsule with two parents (or just slides the label) | guided, P | scene: merge; two chains join | E |
| conflict | 6-2 | Abort the docking | `git merge --abort` is the safe door | situation | staged: a paused merge flashing amber | E |
| conflict | 6-3 | Collision | a conflict is a question: read both, choose, add, commit | guided | scene: collision; the file cracks | E |
| conflict | 6-4 | Docking collision | a refused push, a conflict, and Alex moves again | boss | alarm; live: Alex pushes again after your merge | E |
| undo | 7-1 | Scrap the workshop | `git restore` replaces the working copy; unsaved lines are gone | guided, P | scene: blackbox (what Git keeps); the edit dissolves | E |
| undo | 7-2 | Recall the capsule | revert undoes a shared commit by adding one | situation | staged: a bad capsule on the mothership; an inverted capsule rises | E |
| undo | 7-3 | Wrong course | reset moves a label; the capsules stay | situation, P | `main` slides back; a branch keeps the capsules | E |
| undo | 7-4 | Black box | the reflog finds lost commits; rescue and launch | boss | alarm, blackbox; staged: a real `reset --hard`, three capsules vanish | E |
| undo | 7-5 | Old blueprint | one file back from an old capsule | situation | a file flies out of an old capsule | O |
| undo | 7-6 | Adrift | a detached HEAD needs a label | situation | HEAD floats free | O |

23 essential levels, built in two waves:
- **Wave 1:** cargo 2-2 and 2-3, the vault's essentials and the whole mothership chapter
  (11 levels, ending on Base 7). It is merged first, so the user can playtest it with new
  players while wave 2 is built.
- **Wave 2:** branches, collisions and time travel (12 levels), adjusted by what the playtests
  show.

Chapter ids: `vault`, `mothership`, `branch`, `conflict`, `undo`. The old roadmap chapters they
replace (`basics`, `hash`, `history`, `remote`) leave `chapters.py`; the rest stay as coming
sectors.

## What the engine and the page need

Engine:
- `core.editor = true` in the game's gitconfig, and a shared reaction for a bare `git commit`.
- `core.logAllRefUpdates = true` on the stand-in GitHub.
- Level events: actions a level runs at a moment (after the first observation, or when a goal
  is reached), for Alex's live pushes and the staged scenarios.
- A choice step for predictions (any answer passes) next to the answer step.
- A challenge flag: goals in any order, the card hidden until solved, Rama limited to danger
  and errors, the alarm scene, a boss node.
- A lost-work verdict with Retry, read from facts setup saved.
- Kit helpers: "this path is in no reachable commit" (local and the stand-in GitHub, every ref),
  ancestry checks.

Page:
- The vault drawn as a graph: branch labels, `HEAD`, `origin/main`, merge capsules with two
  parents, a paused merge and a conflicted file.
- The mothership zone live: what it holds, and what this repository last heard from it.
- The prediction buttons, the answer box, the challenge look (boss node, gold dock).
- New zone motions: a refused push bouncing, a clone copying the chain, labels sliding, two
  chains joining, a conflict cracking, an inverted capsule for revert, capsules fading off and
  back for reset and reflog.

Art: the prototype's capsule, chain, orbit, rocket, pull and alarm pictures, and new ones for
fork, merge, collision and blackbox.

## The user's playtest decisions (2026-10-08)

- **2-3 Stowaway explains why secrets stay out.** When the keys reach the staging area, Rama
  says why: whatever is staged goes into the next commit, and a commit is forever. A one-time
  "what would happen" moment plays: a ghost capsule seals with the keys inside, rises to the
  mothership, and copies land at other crew stations with the keys glowing, captioned that
  everyone who can see the repository can read it, in every copy, forever; then it rewinds.
  Rama adds that deleting the file later does not help, because the old commit still has it.
  The debrief names passwords, API keys and tokens, and points to `.gitignore` as the tool,
  taught later. Every claim is fact-checked.
- **The crew view.** In any level with a teammate, the zones show two stations, yours and
  Alex's (each with workshop, staging area and vault), with the mothership between them.
  Capsules rise from one station and land at the other. It is drawn from the real snapshots of
  both clones (`Observation.teammate`).
- **New level 4-2b "Two halves of a ship"**, after Launch: you own `nav.cfg`, Alex owns
  `engine.cfg`; you push your half, Alex pushes theirs live, you pull; both stations hold the
  whole ship and a launch moment plays. Rama names Git's point: two people, at the same time,
  on different parts, and Git puts the pieces together.
- **Hints go to the answer:** every level's last hint gives the exact commands; each hint
  lowers the XP, never below half.
- **3-2 is about an accidental change**, never a "typo": a crew note says what was meant to
  change, and `git diff` shows what else did.
- **Remote addresses:** any address that reaches the stand-in GitHub passes. A real-looking
  `https://github.com/...` address through `url.<base>.insteadOf` is being checked in the
  image before the user decides.
