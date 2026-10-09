# Sector 5, Name tags: the plan

> Draft by designer, round 7, 2026-10-08. The storyboards are in this folder (`index.html`, `5-1`
> to `5-5`). Every command's output in them is real git, recorded by
> `.scratch/sector7-design/gen.py`.

## The recommended layout (for the user to confirm)

Name tags becomes a sector of its own, made by **moving** levels, not copying them. It goes
right after the mothership, since `origin/main` needs push and fetch first. Later sectors shift
by one.

| Sector | Levels |
|---|---|
| 4 The mothership | as today, plus **New recruit** (the clone, today's 5-1) moved to 4-6, before the Base 7 challenge (4-7) |
| **5 Name tags** (new) | 5-1 Name tags, 5-2 A name on any commit, 5-3 Two experiments (today's 5-2 "A second course", reworked), 5-4 One step (new), 5-5 Match the chart (challenge) |
| 6 Branches (was 5) | 6-1 Send a course up, 6-2 Edits come along, 6-3 Your first ticket (challenge) |
| 7 Collisions (was 6) | as today |
| 8 Time travel (was 7) | 8-1 Scrap the workshop, 8-2 Recall the capsule, 8-3 Wrong course, 8-4 The move log, 8-5 Night shift (challenge) |

**Why New recruit moves to sector 4.** A clone is getting a repository from the mothership, which
is what sector 4 is about. It also leaves sector 5 opening on its own subject, names. One change
there: New recruit drops its `git branch -a` goal, since branches aren't met yet in sector 4. Name
tags then lists names with `git branch -v`.

**Title and blurb**

| | English | Spanish |
|---|---|---|
| Title | Name tags | Etiquetas |
| Blurb | A branch is a name for one commit, HEAD is where you are, and `origin/main` is your bookmark of the mothership. | Un branch es un nombre para un commit, HEAD es donde estás y `origin/main` es tu marcador de la nave nodriza. |

Glossary additions: bookmark = **el marcador** (the browser word); the move log = **el log de
movimientos**; Night shift = **Turno de noche** (already in the glossary).

## The levels, one idea each

| Level | Kind | The one idea | New commands |
|---|---|---|---|
| 5-1 Name tags | guided, 2 predictions | a branch is a name for one commit; HEAD is "you are here" and rides one; a commit moves only that one; `origin/main` is a bookmark: Alex pushes and the mothership's pin moves ahead, `git fetch` brings the bookmark up to it | `git branch -v` |
| 5-2 A name on any commit | guided, 2 predictions | take a name off, put a name on any commit; each commit points to its parent, so a name leads to every older commit | `git branch -d`, `git branch <name> <commit>` |
| 5-3 Two experiments (ES: Dos experimentos) | guided, prediction, 9 beats | the first experiment (`bright-lights`) was made the day before and `engine.txt` is already written, so the player types six commands; two branches off one commit make the chain fork like a tree; `git switch` moves HEAD between them and the folder follows (a file appears and disappears); `git log --oneline --graph --all` draws the same tree | `git switch`, `git log --oneline --graph --all` |
| 5-4 One step | guided, prediction | `git switch -c` makes a name and moves HEAD onto it: a third experiment off `main`, a third side line on the tree; `git checkout -b` and `git checkout` are the older forms | `git switch -c`, `git checkout -b`, `git checkout` |
| 5-5 Match the chart | challenge | names on a small forked tree where the target says; two traps: HEAD starts on the name to delete, and a new name lands where HEAD is (`git switch -c lights-v2` from `main` puts it on the wrong side line) | none new |

**5-1 opens the sector** with one beat: "New sector: Name tags. Since you met the mothership you
have typed `main` and `origin/main`... This sector says what they are: names." The chain is born
in the next beat.

**One continuing story.** Each level starts where the last ended, with the same commits and the
same hashes. The one exception is 5-5, a new day: it starts from the end of 5-3 (main and the two
experiments), with 5-4's names cleared and `fuel-test` added, `HEAD` on it. In the game, every setup must rebuild that
state with fixed commit dates, playground commit included, so the hashes match from level to
level.

## Left out on purpose

Detached HEAD (8-7 Adrift, optional, can teach it), `HEAD~n` (explained once in 8-2), `git branch
-f`, rebase and cherry-pick. Sector 8's `git reset` is the only other way a name moves.

## What sector 8 sheds

- **8-2:** HEAD needs no definition, only one line on `HEAD~1`.
- **8-3:** becomes "move the name you are on, backwards".
- **8-4:** only `git reflog` and `HEAD@{n}` are new.
- **8-5:** `git branch -D` is explained in its briefing.

## Notes for frontend

- The chain gives each side line its own column (two branches off one commit never share one).
  Rows stay one line high, so the lines meet the capsules; long rows scroll sideways in the chain,
  and hashes hide on a phone and in side-by-side views. Checked at 1280 and 390 wide, and on the
  time-travel sector's side line.

## Notes for engine

- **Accept both forms** wherever a goal reads typed commands or the result: `git switch <name>`
  and `git checkout <name>`; `git switch -c <name>` and `git checkout -b <name>`. Goals that read
  the repository (HEAD on a branch, a branch at a commit) already accept both.
- The game's terminal is a tty, so `git log` and `git reflog` print names in brackets. The
  recordings show them as the terminal does.
- **Proposed:** the playground drops `origin/HEAD` (`git remote set-head origin --delete`), so the
  brackets show only names a player has met. On git 2.43, `git fetch` does not bring it back.
- Hints that name a commit by hash use placeholders (`{{route}}`, `{{crew}}`).
- **Taught before tested** (`.scratch/sector7-design/audit.py`, run in this order): the gap in
  "Your first ticket" (`switch -c`) is closed by 5-4. One old gap remains: 7-4 Docking collision's
  hint uses `git pull --no-rebase --no-edit`, and `--no-edit` is never taught; fix it in 7-1.
- Renumbering touches `chapters.py` (a `names` chapter between `mothership` and `branch`), the
  level modules' ids and docstrings, and `chapters-5-9.md`.

## Checked against the git docs

| Command | What the levels say | Reference |
|---|---|---|
| `git branch -v` | each branch with its commit; `*` marks the current one | git-branch(1) `-v` |
| `git branch <name> <commit>` | a new name there; you stay where you are | git-branch(1) `<start-point>`; the new branch is not checked out |
| `git branch -d` | takes a name off; not the branch HEAD is on | git-branch(1); the real error is in 5-5 |
| `git switch <name>`, `git switch -c <name>` | move HEAD; create and move | git-switch(1) `-c`: create a new branch before switching |
| `git checkout <name>`, `git checkout -b <name>` | the older forms of the same | git-checkout(1); git-switch(1) says switch takes the branch-switching part of checkout |
| `git log --oneline` | names in brackets sit on that commit | git-log(1) `--decorate`, on by default in a terminal |
| `git log --oneline --graph --all` | the whole tree, every branch, drawn with `*`, `|` and `/` | git-log(1) `--graph`, `--all` |

## Borrowed from Learn Git Branching

Ideas only: its teaching order (commits, then branches as names that move on commit, then
HEAD), its marked current branch, and its goal tree next to yours, which 5-5 uses. No code was
ported, so no MIT notice is needed. The forked tree in 5-3 to 5-5 is also its picture: newest at
the top, each branch a side line. One difference from git's own `--graph`: the chain keeps `main` in
the left column, while git puts whichever line it meets first there.
