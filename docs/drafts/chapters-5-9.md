# Sectors 5 to 9 and the visual progression: the lead's decision

> Approved by the user on 2026-10-08. Wave 2 is being built.

Decided on 2026-10-08 from a second debate between mentor (learning science, visual explanation)
and crew (real situations, story, game feel). Their proposals and rebuttals are in
`.scratch/debate2/`. This file replaces the sector 5 to 7 rows of `chapters-3-7.md` and adds
sectors 8 and 9. The rules of `chapters-3-7.md` and the user's playtest lessons still hold:
Git and GitHub only; every warning explains why, with a picture; evidence before any judgement;
no unexplained jargon; hints end with the exact answer; show the other person.

## The visual grammar

Seven signs mean the same thing in every view. A view with no use for a sign leaves it out:

| Sign | Meaning |
|---|---|
| a person's colour (stripe) and portrait | who made it |
| solid capsule | a commit some label holds |
| ghost capsule | a commit no label holds (it can still be found) |
| tether | a branch linked to its copy on the mothership |
| beacon (blinking, dashed) | something is asked for and waiting |
| amber ring | an operation is paused |
| red crack | a conflict |

"What would happen" moments play in greyscale under "WHAT IF", rewind, never touch the real
state, and come at most once per level, only to explain a warning.

## The view ladder

Each view is born on screen out of one the player knows, with one Rama line. The older view is
always one tap away: a tab row is born in 5-1 with two tabs and gains one tab per new view.
Views are never born in a challenge or a boss. Every birth has a reduced-motion form (two still
frames and a caption). Documents use the V numbers; the screen uses the plain names.

| V | Plain name on screen | Shows | Hides on purpose | Born | How, and Rama's line |
|---|---|---|---|---|---|
| V1 | Your station | the four zones | zones not switched on yet | 1-2 | `git init` powers the zones on. "Powering up your station." |
| V3 | Crew view | your station, the mothership in the middle, Alex's station as a smaller mirror (about 60 percent) | nothing: Alex's four places match yours | 4-2b | Alex's station slides in from the right. "Comms link to Alex's station: open." |
| V2 | Station strip (and crew strip) | each station as one row of cards: up to three file names, three capsules and "+N", an "on no branch" tag on edited files, badges | hashes, branch names, file contents, older capsules | 5-1 | **The fold**, together with the unroll: the zones shrink into their cards. "You know every room now." |
| V4 | History | lanes, labels, the HEAD ship, tethers, merge capsules, portraits; a hash on hover | the workshop and staging area, folded into the strip | 5-1 | **The unroll**: the vault card unrolls into the chart. "Here's the chart of every course." |
| V3 band | Crew band | Alex's strip as a thin band along the top | Alex's details | 5-3 | the crew view flattens when another view takes the stage |
| V5 | Two sides | one conflicted file as "You" and "Alex" halves, the crew note pinned, the result line | every other file | 6-3 | **The crack opens like a book** (6-2 shows only the crack and the amber ring). "Your scanner has a docking mode: both sides, line by line." |
| V6 | Black box | first a boundary around what Git keeps (staging area, vault, mothership; the workshop outside), then a tape of label moves you can scrub | unsaved lines: they never make a tick (7-1's lesson) | 7-1 (boundary), 7-3 (tape) | "Before anyone travels in time: a flight recorder." |
| V7 | GitHub (stand-in) | the review board: bays, gangways, the conversation, commits, files changed | the staging area and hashes; your station stays in the crew strip above | 8-1 | **The hatch**: the mothership card opens and the board slides out. "The mothership patched us into its review board." |
| V8 | Your branch and main | History's mode with two lanes, the fork point, shared history folded to "+N", ahead and behind counts, your branch's tether | every other branch | 8-5 | **The focus**: every other lane dims away. "Locking the scope on your course and main." |
| (the bridge) | every tab lit | the whole tab row, none chosen for the player | nothing | 9-5 only | the final boss lets the player choose; at the end the tabs fold away, the strip unfolds into the four zones for one beat, and the ship jumps |

Review board signs: waiting for review is a dashed gangway with a blinking tip; changes
requested is a comment pin in the reviewer's colour with "!"; approved is a green check in the
reviewer's colour; conflicts with main is a red crack across the gangway; merged is a solid
gangway with a seal.

## GitHub, offline and honest

The review board is a page the game draws and labels "GitHub (stand-in)". Everything that looks
like git on it is real git on the stand-in GitHub (a bare repository): commits, the diff from
where the branch left main, mergeability (`git merge-tree --write-tree`), and the merge itself
(`merge-tree`, `commit-tree` with two parents, `update-ref`). What only GitHub has (pull
requests, reviews, comments) is a game record kept beside the repositories, which git never
sees, as on GitHub. `refs/pull/<n>/head` is mirrored. Board actions are page buttons; the game
never fakes the `gh` tool. Every claim about GitHub's website is fact-checked against
docs.github.com before players see it.

## People

Alex is the teammate who writes code and acts live. Robin is the reviewer, shown only as a
portrait on the board, never with a station. Nobody swaps roles within a level. Both are
they/them.

## The levels

E = essential, O = optional (written up in the debate files, built after playtests).
P = prediction. Kinds: guided, situation, challenge, boss.

| Sector | Level | Title | The one idea | Kind | Main view | The visual | E/O |
|---|---|---|---|---|---|---|---|
| 2 | 2-5 | Junk bay | `.gitignore` keeps generated files out of `status` and `git add .` | situation | V1, workshop large | crates flood the workshop, then grey behind an ignore field, "still on your disk"; WHAT IF: a ghost `git add .` sends the crates to every station | E |
| 5 | 5-1 | New recruit | a clone brings the whole history; `main` and `origin/main` are labels | guided, answer, P | V2 + V4 born | capsules descend with author stripes; the fold and the unroll; two labels land on the top capsule | E (built; add the prediction and the views) |
| 5 | 5-2 | A second course | a branch is a label; switching rewrites the folder | guided, P | V4 | a second label slides onto the same capsule; the HEAD ship hops; `probe.txt` flies home into `scout`'s capsule | E (built) |
| 5 | 5-3 | Send a course up | push sends one branch, by name | guided | V4, V3 band born | a plain push fizzles "0 capsules"; only `scout`'s lane rises; a tether draws; Alex's band learns of the branch | E (built) |
| 5 | 5-4 | Edits come along | uncommitted edits are on no branch: switching carries them, and git refuses only to overwrite them | guided, P | V4, strip | the edited card rides with the ship, tagged "on no branch"; a blocked switch bumps back | E (new) |
| 5 | 5-5 | Your first ticket | combines 3, 4, 5: a branch pushed for review, main untouched here and there | challenge | V4, V3 band | Alex's capsule rises live; your branch parks beside main; WHAT IF on a lost verdict: the unreviewed capsule lands at Alex's | E (built as 5-4; hints end with the answer) |
| 6 | 6-1 | Two crews meet | a merge joins two histories in a capsule with two parents | guided, P | V4 | the second parent line sweeps across in Alex's colour; the fast-forward of 4-3 is only recalled | E (built; rework to one idea) |
| 6 | 6-2 | Abort the docking | a paused merge can always be called off | situation | V4 | an amber ring and a crack on the card; abort retracts the link and seals the crack; a crew note says why to abort | E (built; add the crew note) |
| 6 | 6-3 | Collision | a conflict is a question: read both, choose with the evidence, add, commit | guided | V5 born | the crack opens into "You" and "Alex", the crew note pinned; the answer fuses them in the chosen colour | E (built; halves named by person) |
| 6 | 6-4 | Docking collision | combines 4, 6: a refused push, a conflict, Alex moves again | boss | V4, V3 band, V5 | two bounces, the scanner, the final dock reaching Alex's station; WHAT IF on `--force`: Alex's chain breaks | E (built) |
| 7 | 7-1 | Scrap the workshop | `restore` replaces the working copy; unsaved lines are gone | guided, P | V6 boundary born, workshop expanded | the edit dissolves outside the box; WHAT IF: a search beam sweeps the box and finds nothing | E |
| 7 | 7-2 | Recall the capsule | revert undoes a shared commit by adding one | situation | V4, V3 band | WHAT IF: reset and force break Alex's chain; then the inverted twin rises and lands at Alex's | E |
| 7 | 7-3 | Wrong course | reset moves a label; the capsules stay (one reset mode) | situation, P | V4 + V6 tape born | main slides back and leaves a tick; `rescue` holds the capsules, or they turn to ghosts | E |
| 7 | 7-4 | Black box | combines 3, 5, 7: the reflog finds lost commits; rescue and launch | boss | V6 full width | ghosts at their ticks; a label on a ghost fills it back in; the rescue rises to the mothership | E |
| 7 | 7-5, 7-6 | Old blueprint, Adrift | one file from an old capsule; a detached HEAD needs a label | situation | V6, V4 | a file flies out of an old capsule; the HEAD ship floats free | O |
| 8 | 8-1 | Request to dock | a pull request asks to merge a branch; it lives on GitHub; opening it changes no branch | guided, P | V7 born | a bay forms with a blinking dashed gangway; the mothership's main pulses "unchanged"; Robin's portrait | E |
| 8 | 8-2 | Changes requested | a pull request follows its branch | situation, P | V7, V3 band | the new capsule slots into the same bay; Robin's pin turns "outdated"; the check flies in | E |
| 8 | 8-3 | A second pair of eyes | fetch a teammate's branch, look, and review it against the ticket: request changes | situation | V7, V4 small | Alex's lane drops into your history on fetch; review stays locked until you have looked; your pin lands on the accidental line | E |
| 8 | 8-4 | Docked | the merge happens on GitHub; pull to get it; then delete the labels, the work stays | guided, P | V7, V3 band | the merge capsule seals on the mothership only; "behind" badges at both stations; labels pop, capsules stay; `branch -d` refuses until you pull | E |
| 8 | 8-5 | Main moved on | your branch doesn't follow main: fetch, merge `origin/main` in | situation, P | V8 born | `git pull` lights only the tether; `origin/main` jumps ahead; the "behind" count clears; WHAT IF on the rebase-then-pull path: twin capsules, "the same work twice" | E |
| 8 | 8-6 | Review day | combines 5, 6, 7, 8 | boss | V7, V3 band, V8, V5 | your "request changes" makes Alex push live; your own request cracks red when main moves, heals, docks | E |
| 8 | 8-O1, 8-O2 | Your own copy, Junk in the review | forks; `git rm --cached` for a committed build folder | situation | V3 with two motherships; V7 | the gangway crosses between boards; the file count rolls from 302 to 2 | O |
| 9 | 9-1 | Captain's call | `git stash` sets work aside in a local locker | situation, P | V4, locker card on the strip | the blocked switch bumps back; the edit flies into the locker; a push leaves the locker behind | E |
| 9 | 9-2 | Replay the course | a rebase replays your commits as new commits, on your own branch | guided, answer, P | V8 | copies lift and land, ghosts stay behind, hash stamps roll | E |
| 9 | 9-3 | Lease, not force | a rebased, pushed branch needs `--force-with-lease`, never on main | situation, P | V8, V3 band | WHAT IF: twin capsules; the padlock checks the hash and opens | E |
| 9 | 9-4 | Leak drill | a pushed secret is burned: change it first; deleting it later doesn't unpublish it | situation | V3 full, V6 below | 2-3's moment for real: the keys glow at every station, grey out when the key is changed; a new commit and `.gitignore` stop the spread; "copies remain, that's why the key had to change" | E |
| 9 | 9-5 | Launch window | combines 7, 8, 9 | boss | the bridge, the player's choice | preflight fails; the inverted capsule docks through review; the captain plants `v1.0` (a story beat, not a goal); the fold back to the four zones; the jump | E |
| 9 | 9-O1 to 9-O4 | Who turned it up?, Plant the flag, Needle in the log, Hotfix pick | blame and show; tags; `log -S`; cherry-pick | situation | V4 with line badges; V4; V6; V4 | portrait badges per line; a flag that travels only by name; the tape scrubs to a removed line; one capsule copied with a new hash | O (blame first) |

The leak drill never teaches amend or a forced push: taking a secret out of history is a
separate, team-wide step, later and optional. Rebase is taught only on the player's own pull
request branch. The shared reaction to a refused switch names both ways out with exact lines.

## Waves

- **Wave 2, then the next user playtest:** 2-5; sector 5 (5-1 to 5-5, with the new 5-4 and the
  reworks); sectors 6 and 7. That is 14 essential levels, 10 new or reworked, plus the views
  V1 to V6: the crew view's mirror, the fold, history, the band, two sides and the black box.
  The playtest's main question is whether the fold keeps the player's footing.
- **Wave 3, after that playtest:** sectors 8 and 9, 11 essential levels, and V7 and V8.

## What the engine and the page need

Engine:
- a per-level main view, and the views seen kept in the save;
- reflog entries with old and new positions for the tape, and commits held only by the reflog
  for ghosts;
- the merge base, and ahead and behind counts, for V8;
- ignored files reported in the snapshot, so the page can grey them;
- both sides of a conflicted file, with the people;
- pull request records and board actions, and the merge on the stand-in GitHub;
- events fired by page actions (a review), and events on a refused command;
- a lock until the evidence step is done.

Page and art: the view ladder and each birth animation; the crew view's mirror; the tab row;
the review board; the moments (`secret-leak`, `launch`, `junk-flood`, `force-break`,
`search-beam`, `twins`, `copies-remain`, `unreviewed-main`); new scenes for each sector's
opening; portraits for Alex, Robin and the captain.
