# Past versions: the plan

## For the user

**Two new levels.**

- **3-4 Look into the past** (sector 3, after Flight recorder): `git log fuel.txt` finds the
  commits that changed a file, and `git show <hash>:fuel.txt` prints the file exactly as one of
  them recorded it. The player answers the captain's question: what did the fuel read after
  Phobos?
- **8-3 Deleting isn't erasing** (sector 8, after Recall the capsule): a password committed and
  then removed in the next commit is still readable with `git show HEAD~1:keys.txt`. Once
  pushed, it is leaked: change it. It pays off Stowaway, which kept the same password out of a
  commit.

**Review:** a fresh reviewer found both mostly clear and took away both lessons. The key line
was "a later commit cannot remove what an earlier commit recorded". The round 1 notes are fixed:
- clearer counting in 3-4, with the commits that did not touch the file dimmed;
- the terminal shows the hash to copy;
- a lighter picture in 8-3;
- an accurate sentence on rewriting history.

**Decided (the reviewer's view):**
- 3-4 only reads the past; bringing an old version back stays in Time travel.
- 8-3's answer is the password to change, accepted in any case as `orion-7` or as the whole line
  `airlock password: orion-7`.

**For you to confirm:**
- the placement (3-4 in sector 3, 8-3 in sector 8);
- renumbering: Cargo inspection becomes 3-5, and Wrong course, The move log and Night shift
  become 8-4 to 8-6.


> Draft by designer, round 2, 2026-10-08. The storyboards are in this folder (`index.html`,
> `3-4` and `8-3`, each with a `-script.md`). All git output is real:
> `.scratch/sector7-design/past_gen.py` built each lab and typed each line.

## Two levels, one idea each

| Level | Idea | New commands |
|---|---|---|
| **3-4 Look into the past** (ES: Mirar al pasado) | Every commit keeps every file exactly as it was, and you can read it. Reading the past changes nothing. | `git show <hash>`, `git show <hash>:<file>` |
| **8-3 Deleting isn't erasing** (ES: Borrar no es olvidar) | A commit that deletes a file is a new commit without it; the commit before still holds it. A secret that was committed and pushed is leaked: change it. | `git show HEAD~1:<file>`, `git log --oneline -- <file>` |

## Where they go, and why

**3-4 goes into sector 3, The time vault, right after 3-3 Flight recorder.** The challenge, Cargo
inspection, moves from 3-4 to 3-5.

- It needs only what sector 3 has just taught. Flight recorder ends on `git log <file>`, which
  finds the commits that changed a file; 3-4 is the next step, reading the file in one of them.
- The question is answered with a hash copied from `git log`, so it does not need `HEAD~n`.
  `HEAD~n` comes in 8-2, and `HEAD` itself is not named until 5-1.
- It is easy, and "the past is all still there" is the vault's own promise, so it belongs in the
  vault's sector.
- It answers with a typed answer, the way Flight recorder does.

**8-3 goes into sector 8, Time travel, right after 8-2 Recall the capsule.** This fills the
plan's deferred "Old blueprint" slot. Wrong course, The move log and Night shift move to 8-4,
8-5 and 8-6.

- It uses `HEAD~1`, taught in 8-2.
- Its lesson sits beside 8-2's: a revert adds a commit and leaves the old one as it was, and so
  does a delete.
- It needs the mothership and Alex (sector 4). The point is that the commit has left your machine.
- It is the payoff of 2-3 Stowaway: the same password, `orion-7`, now committed. The fix that
  works is the one Stowaway taught, before the commit.

The other option, both levels in sector 8, would leave the easy reading skill until the end of
the game, although it needs nothing from sectors 4 to 8.

## The picture: one picture, one panel

- **The chain, with the commit being looked at ringed.** Beside it is one panel: "fuel.txt as it
  was in 'Log the fuel after Phobos'". It shows exactly what `git show <commit>:<file>` printed.
  When git answers that the file is not in that commit, the panel says "Not there: this commit
  has no keys.txt".
  - Before anything is read, the panel says how to fill it.
  - It always ends "Read from the commit. Your folder is not changed."
- **In sector 3 the chain does not exist yet.** It is born in 5-1, so 3-4 draws the vault zone's
  column of capsules, plain, with no name tags or HEAD mark (the storyboard draws it as a plain
  chain). The panel attaches the same way.
- **In 8-3** it is the chain with the mothership's and Alex's pins, so "Alex has this commit too"
  is visible.

## 3-4 Look into the past

- **Lab:** one repository and no mothership. Six commits by Robin Park, Sam Ortiz and the
  player, each with a fixed date. `fuel.txt` changes in four of them: 90%, 75%, 60% and 40%. No
  message names a number. "Log the fuel after Phobos" is the second newest of the four.
- **Briefing:** the gauge reads 40% tonight. What did it read after the Phobos stop?
- **Steps:**
  1. `git log fuel.txt` lists the four commits. It skips commits that did not touch `fuel.txt`,
     and the picture dims those two. The terminal opens on the Phobos commit's lines, and Rama
     says to copy the first 7 characters of its hash.
  2. Predict: what does `git show <hash>` print? It prints the change: the message, a `-` line
     (taken out) and a `+` line (put in). The `diff`, `index`, `---` and `+++` lines are greyed
     in the terminal.
  3. `git show <hash>`.
  4. `git show <hash>:fuel.txt` prints `fuel: 60%`.
  5. The answer is typed: 60%.
- **Check:**
  - The first three goals read the typed lines, as Flight recorder does.
  - The answer is checked by value: `60%` or `60`. 3-4 only reads; there is no `git restore
    --source`.
  - A wrong answer gets a reaction that points to the Phobos message.
- **Reactions:** `git show <hash> fuel.txt`, with a space instead of a colon, shows what that
  commit changed in the file; with a colon it shows the file itself.
- **Debrief:** it says that bringing an old version back into the folder comes in Time travel.
  `git restore --source` is not taught here; it would fit 8-1 or a field guide card.

## 8-3 Deleting isn't erasing

- **Lab:** the playground lab, with GitHub and Alex. It holds Plot the route and Add the crew
  list, then "Add the airlock keys" (`keys.txt`: `airlock password: orion-7`), then "Remove the
  keys" (`git rm`). Both are pushed, and Alex has pulled.
- **Steps:**
  1. `git log --oneline`.
  2. Predict: can anyone with this history still read the password? Yes.
  3. `git show HEAD:keys.txt` gives the real error `fatal: path 'keys.txt' does not exist in
     'HEAD'`. The panel says "Not there", and Rama frames it as expected: "Right: `HEAD` is the
     newest commit, today's files, and it has no `keys.txt`."
     - During beats 3 to 8 the legend is hidden, so the picture stays light.
  4. `git show HEAD~1:keys.txt` prints the password. Rama: "`HEAD~1` means one commit before
     `HEAD`."
  5. Rama: the mothership and Alex have this commit too.
  6. `git log --oneline keys.txt` fails for real, because the file is not in the folder:
     "ambiguous argument ... Use '--' to separate paths from revisions". This is met on purpose,
     since it is what a player types first. Rama gives it one sentence: a file no longer in your
     folder needs `--` before its name.
  7. `git log --oneline -- keys.txt` lists the add and the remove.
  8. Rama: a later commit cannot remove what an earlier one recorded; treat the password as
     leaked and change it. Rewriting history gets one sentence and is not taught: "Rewriting
     history can hide it from future copies, but not from anyone who already pulled it, so you
     still change the password." Then the tie back to Stowaway.
  9. The answer is typed: the password to change, `orion-7`, accepted in any case, alone or as
     the whole line.
- **Check:**
  - The goals read the typed lines.
  - The answer is checked by value.
  - Reactions cover `HEAD~2`, which is before the keys were added, and a wrong answer.

## Checks

- Taught before tested: `audit.py`, with 3-4 after Flight recorder and 8-3 after 8-2, reports
  0 gaps against the current game tree. Both levels are missions, and no challenge depends on
  them.
- Storyboards were checked at 1280 and 390 wide, with no page errors.

## Open points

None left for the design. The two round 1 questions were decided as above.
