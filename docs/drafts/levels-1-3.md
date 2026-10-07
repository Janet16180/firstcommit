# The first three levels: design (draft 2, for the user's decision)

Chapter 1 teaches one idea: **your project lives in three places on your computer, and you
choose what moves between them** (the working folder, the staging area, the repository; `init`
creates the last two, `add` copies a file into the staging area, `commit` saves a snapshot of the
staging area; `git status` is how you look). Chapter 2 repeats the idea and adds a fourth place,
GitHub, and one command, `git push`. Branches, hashes, identity, `log` and `clone` are not taught
yet.

Draft 2 folds in an independent review: commits are drawn as full snapshots (draft 1 drew the
box itself leaving), the scenes no longer give away the quests' predictions, `git status` is no
longer said to look at GitHub, and the missions' checks are exact.

## 1. The pattern every level follows

| Beat | What happens | Why it teaches |
|---|---|---|
| **1. The scene** (20-25 s, skippable) | A playful animation with no terminal and no map: the level's idea as a story, ending in a small "your turn" interaction. | Builds the picture and the *why* before the player needs them. It shows the rule, never the twist. |
| **2. The guided quest** (map on) | The player types each command; the live map animates what that command changed; one line names it. Before each twist, a **prediction**: "What will happen if...?" | Do, see, name. The twist is discovered, not told: predict, observe, explain. |
| **3. The blindfold mission** (map hidden) | "No map this time." A small task solved with `git status` as the only eyes. On solve the map comes back and replays what the player did: "You called it!" | Removes the scaffolding; the reveal is the reward. |

The scenes use **the map's own symbols** (a file is a page on the desk, the staging area an open
box, a commit a closed box on the shelf, the newest marked "now", GitHub a second shelf in the
cloud), so whatever a scene teaches, the player recognises in the live map.

### The picture of a commit (the rule every animation follows)

As in `docs-draft/four-places.md`: `git add` puts a **copy** of the page in the open box, replacing
the copy that was there; the page stays on the desk. `git commit` closes **a copy of the whole
box** (every file in it, changed or not) onto the shelf; the open box stays, still holding those
copies. So a commit is a snapshot of every file, and the open box after a commit matches the
newest one on the shelf.

### Words: plain first, Git's word in "More"

| Picture | Plain words | Git's word |
|---|---|---|
| page on the desk that Git has never had in the box | new file | untracked |
| page on the desk that differs from its copy in the box | changed, not in the box yet | modified, not staged |
| a copy in the box that differs from the newest saved version | ready to save | staged |
| box, desk and shelf agree | everything saved | working tree clean |
| GitHub's shelf has your newest box too | published | pushed |

Authored text never quotes Git's messages (AUTHORING section 1); the real terminal shows them, and
the level's text refers to them ("the first list `git status` prints").

### Branch and hash words in the terminal: a decision for the user

Even with the simple map, git prints them: `git status` starts with `On branch main`, `git commit`
prints `[main 1a2b3c4] Your message`, and `git push` prints a line ending `main -> main`. Telling
players to ignore output teaches that output is noise. Proposal: the first time each appears, one
friendly line names it without teaching it ("`main` is the name of your timeline; the seven
characters are the commit's short name. Both get a chapter later.") and nothing ever asks about
them. The alternative, quiet forms (`git commit -q`), would teach commands nobody types at work.

### Simple map (chapters 1 and 2)

A level option `MAP_DETAIL = "simple"`: the live map hides file ids, commit hashes and the
`main`/`HEAD` tags; a commit shows its message; the newest keeps the "now" marker.

### Identity, silently

`git commit` refuses to run without a name and email. The game sets them in its own gitconfig
(the player's display name and an `@example.com` address; never the player's own config). The
"Your real setup" chapter teaches `git config` later.

---

## 2. Level 1 · "Your first commit" (chapter 1, ~6 min)

**Goal:** the three places; `add` copies; `commit` saves a snapshot. **Twist:** `git add` copies
the page; it does not move it.

**Scene "Versions"** (built, approved): `essay_final_FINAL_v2_really_THIS_ONE.docx` and friends
become one file and a timeline; the dial travels back to Tuesday's typo; the player drags the
dial. "Let's make your first commit."

**Guided quest** (6 steps, simple map):

| # | Kind | The player does | The map shows | One line |
|---|---|---|---|---|
| 1 | watch | `git init` | an open box and an empty shelf appear beside the desk | "Your folder has a memory now: a box to fill and a shelf to save on." |
| 2 | watch | `echo "# My project" > README.md` | a page lands on the desk, tagged *new* | "A new page. Git sees it but keeps no copy yet." |
| 3 | **predict** | "You will run `git add README.md`. Afterwards, where is README.md? (a) only in the box (b) on the desk and in the box" | | any answer: "Let's see." |
| 4 | watch | `git add README.md` | a copy flies into the box; the desk keeps its page | "A copy went in the box; your page stayed on the desk." (+ "You called it" if they chose b) |
| 5 | watch | `git commit -m "Add the README"` | a copy of the box closes and slides onto the shelf; "now" lands on it; the open box stays full; a confetti puff | "Your first commit: a snapshot of the box, saved on the shelf." |
| 6 | answer | `git status`; "Is anything waiting to be saved?" (no) | desk, box and shelf glow together | "Desk, box and shelf agree: everything is saved." |

**Blindfold mission "By feel":** "No map this time. Add a second page, `todo.md`, and save it
in a new commit. Your eyes: `git status`." Check: exactly one new commit on top of the quest's
commit; it holds `todo.md` (any content) and the unchanged README; nothing is changed or staged.
Hints (cost XP): "`git status` lists the new page: what puts a copy in the box?" then the two
commands.

**Debrief:** desk → box (`add` copies) → shelf (`commit` saves a snapshot of the box); `git
status` shows where things are.

**Cards:** "After `git add`, where is your file?" · "What does `git commit` save: the desk or the
box?" · "Which command shows what is waiting to be saved?"

---

## 3. Level 2 · "Pack only what you mean" (chapter 1, ~8 min)

**Goal:** the box is a choice: a commit saves the box, not the desk. **Twist:** the box keeps the
copy from the moment you added it; later edits stay on the desk until you add again.

**Scene "Packing day"** (new, ~22 s): the desk holds `README.md` and `todo.md`; the open box
already holds copies of both; the shelf has one box. Both desk pages get scribbled on (they glow).
A hand drags only `todo.md`: a photocopier flash, and its fresh copy replaces the old todo copy in
the box; README's old copy stays in the box. The box's copy closes onto the shelf. Zoom on the new
saved box: new todo, old README. The desk's README still glows. Captions: "Two changes on the
desk." · "Put only the one you mean in the box." · "The commit saves the box: the new todo, and
README as it was." Your turn: the player picks which changed pages to put in the box, presses
"Save", and the zoom shows what the snapshot holds. (The scene does not show editing after
adding: that is the quest's twist.)

**Setup:** one commit with `README.md` and `todo.md`; the box matches it.

**Guided quest** (7 steps):

| # | Kind | The player does | The map shows | One line |
|---|---|---|---|---|
| 1 | watch | add a line to `todo.md` and to `README.md` | both desk pages glow *changed*; box and shelf unchanged | "Two changes, both only on the desk." |
| 2 | watch | `git add todo.md` | todo's new copy replaces the old one in the box | "The box now holds your new todo, and README as it was." |
| 3 | watch | `git commit -m "Update the todo"` | a copy of the box goes onto the shelf; README still glows on the desk | "Saved: the new todo. README's change waits on the desk." |
| 4 | **predict** | "Now: `git add README.md`, then you add one more line to README.md, then commit. Which README is saved? (a) with the last line (b) without it" | | "Let's see." |
| 5 | watch | `git add README.md`, then add one more line to `README.md` | the box gets README's copy; then the desk page changes again and differs from the box | "The box kept the copy from when you added it." |
| 6 | answer | `git status`; "README.md appears in both lists. Which list is about the copy in the box?" (the first: changes to be committed) | desk vs box README pulse | "Box vs last commit: the first list. Desk vs box: the second." |
| 7 | watch | `git commit -m "Update the README"` | the box's copy, without the last line, goes onto the shelf; the desk keeps the last line | "Saved without the last line, as you predicted (or not!). Add again to include it." |

**Blindfold mission "Pick one":** setup puts a prepared change in each file. "No map. Save the
todo change in a commit of its own; leave README's change on the desk." Check: exactly one new
commit on top of the setup's; its todo is the prepared change; its README equals the parent's; the
prepared README change is still on the desk and not in the box. Reveal: the map replays; README
still glows on the desk: "Exactly what you meant. You called it!"

**Debrief:** you choose what goes in the box; `add` copies the file as it is at that moment; a
commit saves the whole box.

**Cards:** "You `git add` a file, edit it, then commit. Which version is saved?" · "How do you save
only one of two changed files?" · "Does a commit hold only the changed files?"

---

## 4. Level 3 · "Publish with push" (chapter 2, ~8 min)

**Goal:** GitHub is a fourth place with its own shelf; a new commit starts on your computer;
`git push` copies your new commits to GitHub. **Twist:** only saved versions travel; changes on the
desk or in the box stay home.

**Scene "Shipping"** (new, ~22 s): your desk, box and shelf on the left; GitHub's shelf in the
cloud on the right, with the same boxes. You save a new box: only your shelf has it ("GitHub
hasn't got this one yet"). `push`: a copy of that box rides up to the cloud; both shelves match,
and yours still has it. Captions: "A new commit starts on your computer." · "`git push` sends
GitHub a copy of your new commits." · "Now both shelves match." Your turn: "Save" and "Push"
buttons. (The scene does not show pushing with unsaved changes: that is the quest's twist.)

**Setup:** a practice GitHub that already holds two commits by a fictional teammate (never empty:
cloning an empty repository makes git 2.43 print "the upstream is gone" later), and the player's
project as a clone of it, so a plain `git push` works. Map: "The four places", simple detail, GitHub
beside your computer.

**Guided quest** (7 steps):

| # | Kind | The player does | The map shows | One line |
|---|---|---|---|---|
| 1 | read | (look at the map) | both shelves hold the same two boxes | "Your computer and GitHub hold the same commits. *origin* is this project's nickname for GitHub." |
| 2 | watch | change `README.md`, `git add`, `git commit -m "..."` | the box lands on **your** shelf only | "Saved on your computer. GitHub hasn't got it yet." |
| 3 | answer | `git status`; "How many commits has your project not published yet?" (1) | | "Git counts what you haven't pushed since you last talked to GitHub, and suggests the next move." |
| 4 | watch | `git push` | a copy of the box flies to GitHub's shelf; yours stays | "Published. Both shelves match." |
| 5 | **predict** | "You change README.md and push again, without a commit. What does GitHub get? (a) your change (b) nothing new" | | "Let's see." |
| 6 | watch | change `README.md`, `git push` | the push arrow stays dark; the desk page glows | "Nothing new travelled: the change was never saved in a commit." |
| 7 | watch | `git add`, `git commit`, `git push` | desk → box → shelf → cloud | "Save, then push. That's the whole loop." |

**Blindfold mission "Ship it"** (a transfer of Levels 2 and 3): setup leaves a prepared change in
`README.md`. "No map. Get this change onto GitHub, and only this one." The game checks GitHub's
practice repository directly (not `git status`): exactly one new commit there, on top of the
previous one, with the prepared README and nothing else changed; nothing left on the desk or in
the box. Reveal: desk → box → shelf → cloud: "Shipped. You called it!"

**Debrief:** four places now; a commit starts on your computer; `git push` copies your new commits
to GitHub; changes not yet committed are not pushed.

**Cards:** "You committed. Is it on GitHub yet?" · "You changed a file and pushed without
committing. What reached GitHub?" · "After a push, is your commit still on your computer?"

---

## 5. What is built and what is new

| Piece | State |
|---|---|
| Versions scene, hidden-map mission with reveal, folded instructions, 5x pace, chapter order | built (`p2/opener` faabd88, being fact-checked) |
| Predict steps | small engine change: an `answer` step flagged `predict` accepts any answer, plays no "wrong" sound, and the next step's line can say "You called it" |
| Simple map, `MAP_DETAIL = "simple"` | new: map.js / theme-time-places.js hide ids, hashes and tags |
| Silent identity | new: the game's gitconfig gets a name and email at profile creation |
| Level 1 content | remove the identity, branch and hash steps; the mission uses only `git status` |
| Level 2 + "Packing day" | new: author + animator |
| Level 3 (chapter 2 rewritten) + "Shipping" | new: needs the practice GitHub as a Python builder (helper job A) and GitHub beside your computer (G1); `p2/start`'s clone levels are parked for a later chapter |

**Build order** (at most 3 teammates at once): (1) opener: Level 1 cuts, silent identity, predict
flag; animator: "Packing day". (2) map teammate: simple map; author: Level 2. (3) G1 and helper A;
animator: "Shipping"; author: Level 3. Each level: shots, fact-check, merge with the slow tier.

## 6. Decisions (the user, 2026-10-06)

1. Branch and hash words in the terminal: named once in a friendly line, never asked about.
2. Predictions: no XP; just "Let's see" and "You called it".
3. Scenes: play automatically the first time; afterwards a "Watch the intro" button.
4. Chapter 2: id `publish`, "Publish your work".
5. Fact-check (checker, faabd88): the scene's files become `.md` (git cannot show line changes in
   a Word file).
