# Field guide: branch and merge cards, the visual plan

> Draft by the guide-visuals agent, 2026-10-08, design only, for the user to approve. The mock is
> `storyboard.html` in this folder (open it in a browser; the Light / dark button switches
> theme). No game code changed.

## The idea in one line

Each card answers "what moved?" with a picture of the chain (commits, name tags, `HEAD`) and,
when files change, the working folder under it, before and after. The terminal under the picture is
real git output, and the lines that match the picture are underlined in violet.

## Shared rules for every card

- **One story for all seven cards.** *Start the project*, *Plot the route*, then a branch `scout`
  with *Ready the probe*, and *Fill the tanks* on `main`. Every repository is rebuilt with fixed
  dates, so a commit has the same hash on every card (`e9db21e` is always *Plot the route*). A
  reader who opens two cards sees the same chain.
- **The teaching-picture model** (`docs/drafts/teaching-pictures.md`): newest commit at the top,
  violet squares for your commits, a branch is a name tag on a commit, `HEAD ▶` before the tag
  you are on. A commit's subject is in italics. The chain forks into a second column only when
  the histories really split.
- **Three marks, one meaning each.** Gold means "what this command changed" and nothing else: a
  new tag, a tag or `HEAD` that moved, a new commit and its lines, a file that arrived. A violet
  dashed ring or underline means "look here" (a terminal line that matches the picture, the
  commit a refusal is about). Red, a dashed red frame and a red underline, means git refused.
- **The working folder row** ("Working folder (workshop)") has a neutral grey border: the game's
  workshop orange sits too close to gold, so gold stays on the files that changed. It sits under the chain only on the
  cards where files change: `git switch` and `git merge`. On `git branch` and `git switch -c` it
  is there to say "unchanged", since "a branch copies my files" is the myth to break.
- **Changed / Same.** Under the before and after, two short lines: what changed and what did not.
  Each label is a word, not only a colour.
- **Refusals are pictures too.** When git refuses, the frame has a dashed red edge, the word
  "Refused" (or the reason), the unchanged chain and git's own error. Alternatives are joined by
  "or", steps by an arrow.
- **Real output, recorded on a terminal.** `record.sh` (copy in `recorder/`) runs each line under
  `script(1)` with a temporary HOME and the game's git settings, so the output is what the
  game's terminal shows: names in brackets in `git log`, `ls` in columns, lines in a terminal's
  order. The one rewrite is the temporary folder's path, shown as `/home/you`. `recorder/check.py`
  confirms every terminal on the page is, character for character, recorded output.

## The cards

### 1. `git branch <name>`

- **Picture.** Before and after, one row each: *Plot the route* with `HEAD ▶ main`; after, a
  second tag `scout` lit on the same commit. The folder row says "unchanged".
- **Teaches.** A branch is only a name on the commit you are on. No new commit, `HEAD` stays,
  no files copied. The terminal's `(HEAD -> main, scout)` is the same picture in git's words.
- **Leaves out.** `git branch <name> <commit>` (5-2 teaches it; a related link), `-v`, remote
  branches.
- **Under the after frame**, one line: "HEAD is on `main`, not on `scout`", so
  `(HEAD -> main, scout)` is not read as HEAD on both.
- **Mistake.** Expecting to be on the new branch: `git branch` still shows `* main`.

### 2. `git switch <branch>` (older: `git checkout <branch>`)

- **Picture.** Three steps on a straight chain (`scout` one commit ahead of `main`): before, on
  `main`; `git switch scout`, `HEAD` hops and `probe.txt` appears in the folder; `git switch
  main`, `probe.txt` leaves, with the words "in scout's commit" so nobody thinks it is lost.
- **Teaches.** `HEAD` moves; the folder follows the commit `HEAD` is on; commits and tags do not
  move.
- **A folded part: "When you have edits you have not committed".** Two outcomes, joined by "or":
  the edit comes along (git prints `M	notes.txt`), or git refuses because the other branch holds
  that file differently (`Aborting`, nothing moved; one line glosses git's word "stash" as
  setting edits aside, not needed yet). This is the snag beginners hit first; the
  mission "Edits come along" is built on it.
- **Leaves out.** Detached `HEAD`, `git switch -`, stash (git's message names it; the card does
  not explain it).

### 3. `git switch -c <branch>` (older: `git checkout -b <branch>`)

- **Picture.** A sum first: `git branch lights` + `git switch lights` = `git switch -c lights`.
  Then before and after: a new tag `lights` with `HEAD` on it, `main` left where it was, folder
  unchanged.
- **Teaches.** One step for the two commands the reader already knows; edits not yet committed
  come along (why it is the fix for "I started on `main` by mistake").
- **Terminal.** Both forms side by side; they print the same words.
- **Mistake.** Leaving out `-c`: `fatal: invalid reference: lights`.

### 4. `git branch -d <branch>`

- **Picture.** The success first. Before, stated up front: "after the merge, `main` holds
  `scout`'s commits". After, the `scout` tag is struck through and lit, the commit still solid
  because `main` leads to it. Then git's `Deleted branch scout (was e6af58d).`
- **A folded part: "When git refuses".** Two outcomes, joined by "or": not merged (git compares
  with the branch you are on; *Ready the probe* is ringed and labelled "not in main"), and you
  are on it (git's "used by worktree" glossed as the folder you are working in).
- **Teaches.** It removes a name, never a commit; git protects work the branch you are on does not
  hold yet.
- **Leaves out.** The upstream rule (with an upstream set, git checks against it), what `-D`
  leaves behind beyond one sentence (ghosts and the reflog belong to the time-travel sector), and
  remote branches.

### 5. `git merge <branch>`: fast-forward and merge commit

- **Picture.** Two folded parts, each a before and after with the folder row:
  - Only `scout` moved on: `main`'s tag slides up to *Ready the probe*. No new square.
    `probe.txt` arrives in the folder. git says `Fast-forward`.
  - Both moved on: the fork closes. A new square, the merge commit *Merge branch 'scout'*, with
    two lit lines down to its two parents, glossed once as "the two commits it joins"; `main` climbs onto it, `scout` stays. git says `Merge made by the
    'ort' strategy.`
- **Teaches.** You merge into the branch you are on; the first line of the output tells you which
  case happened; the other branch is not deleted.
- **Leaves out.** Conflicts (the guide's conflict section, already approved, is linked from the
  card as today), `--ff-only` and `--no-ff`, "Already up to date.", the word "ort".

### 6. `git merge --no-edit <branch>`

- **Picture.** The first line links back to the `git merge` card for what a merge commit is. A
  two-row table (plain `git merge` and `--no-edit`), then the message git prepares,
  drawn as an editor window, with its real text (`Merge branch 'scout'` and the `#` lines), and an
  arrow to the merge commit carrying that first line.
- **Teaches.** A merge commit needs a message; git writes one; `--no-edit` takes it as it is.
  A fast-forward never asks.
- **Said plainly.** In the game no editor ever opens (`core.editor = true`), so a plain `git merge`
  already behaves like `--no-edit`. The card says so, so the reader is not puzzled, and says what
  happens on their own computer.
- **Mistake.** Stuck in vim on a work machine: `:wq`. After a conflict, `git commit --no-edit`
  finishes the merge the same way.

### 7. `git log --oneline --graph --all`

- **Picture: a decoder.** git's drawing on the left, the chain on the right, line for line: row n
  of the picture is line n of the output, with matching stripes. Connector lines like `|/` and
  `|\` get an empty row with only the wire passing through. A small key: `*` a commit, `|` a line
  down, `/` and `\` a fork or a join, `(HEAD -> main)` you are here, `(scout)` a name.
- **Above it**, one line: newest at the top, in git's drawing and in the picture.
- **Folded parts.** The same decoder after the merge (`*   ` and `|\`), with the two lines
  labelled "main's line" and "scout's line"; and "Without `--all`": *Ready the probe* is missing
  from the output, "not gone, not asked for", and the picture beside it draws it faintly.
- **Teaches.** The terminal's graph is the guide's chain, so the reader can read it alone later.
- **Leaves out.** Colours, `--decorate` options, dates and authors, long histories.
- **On a phone.** The two halves stack (terminal above, chain below); the stripes still pair lines.

## What changes from today's cards

Today's cards (`guide-text.js`, `guide-pictures.js`) already draw before and after chains. This
proposal adds, for these seven cards only:

1. the working folder row under a chain (the desk and the chain in one picture);
2. steps (more than two frames) and "or" frames for outcomes;
3. a terminal per frame where a refusal is the point;
4. the decoder for `git log --graph`;
5. outputs recorded on a terminal, in one shared story.

Two things found while recording, for whoever builds this:

- **Today's `guide-git.js` is recorded without a terminal**, so its `git log` lines have no names
  in brackets, while the player's terminal shows `(HEAD -> main, scout)`. The capture
  (`tests/guide_capture.py`) can run each line under a pty, as `record.sh` does.
- **On a terminal, a plain `git merge` with the game's settings briefly prints**
  `hint: Waiting for your editor to close the file...` and then erases it (carriage return and
  ESC [K). The storyboard shows the screen's final state; a transcript taken byte for byte would
  show the hint. The capture should do the same.

## Files

- `storyboard.html`: the mock, self-contained, generated by `recorder/build.py` from the
  transcripts and `recorder/storyboard.css`.
- `recorder/record.sh`, `recorder/screen.py`: the recorder. `recorder/check.py`: the check that
  every terminal on the page is recorded output. To rebuild:
  `recorder/record.sh /tmp/out && python3 -I recorder/build.py /tmp/out storyboard.html`.

## For the user

What I propose:

- Seven cards, one picture each, all in one small story with the same commits and hashes, so the
  reader sees one chain across the branch and merge cards.
- The working folder appears under the chain on `git switch` and `git merge`, where files change,
  and says "unchanged" on `git branch` and `git switch -c`.
- `git merge` shows both cases side by side: fast-forward (the tag slides, no new commit) and
  merge commit (a new commit with two parents).
- `git log --graph` gets a line-for-line decoder: git's drawing beside the chain.
- Refusals (switch with edits, `branch -d` not merged or on it) are pictures with git's real
  error, in a folded part of the card, closed by default.

Decisions only you can make:

1. **One shared story, or keep each card's own?** Today's cards use different commits per card
   (*Add the star map*, `test-run`, and so on). One story means re-recording these seven cards.
2. **Record on a terminal?** Names in brackets and `ls` in columns match what players see, but
   change the outputs of today's cards too.
3. **`git merge --no-edit`: its own card, or a part of the `git merge` card?** In the game it
   behaves like a plain merge, so a part of the merge card may be enough.
