# 8-3 Wrong course

Mission. Command: `git reset --hard`.

## Briefing

You made two survey commits on `main` by mistake: they belong on a branch of their own, and the mothership has not seen them. Keep them on a branch `rescue`, and get `main` back to where the mothership's `main` is.

## Goals

1. Keep your commits on a branch: `git branch rescue`.
2. Predict first.
3. Move `main` back: `git reset --hard origin/main`.
4. Check: `git log --oneline`.

## Beats

### Beat 1: scene

**Rama:** Two survey commits landed on `main` by mistake. The mothership's pin is two commits below: it has not seen them. Your folder has `survey.txt`, from those commits.

### Beat 2: type

The player types:

```
$ git branch rescue
(no output)
```

**Rama:** `rescue` is a second name on the same commit. Nothing else changed: no new commit, no file. `HEAD` still rides `main`.

**Designer note (what the picture does):** A `rescue` tag appears beside `main` on Survey day 2.

### Beat 3: say

**Rama:** Next: `git reset --hard origin/main`. `git reset` moves the branch you are on, `main`, to another commit: here, the one your `origin/main` bookmark is on, Start the project.

### Beat 4: say

**Rama:** `--hard` also makes your folder match that commit. Without `--hard`, the branch moves and your files stay as they are.

### Beat 5: predict

**Prediction:** After the reset, how many commits will `git log --oneline` list?

- 1
- 3

Reveal: 1. `git log` starts at `HEAD` and walks down the parents. `HEAD` rides `main`, which will be on `Start the project`, the oldest commit. The two survey commits sit above it, where only `rescue` leads.

### Beat 6: type

The player types:

```
$ git reset --hard origin/main
HEAD is now at 59e52f5 Start the project
```

**Rama:** `main` slid down two commits, and `HEAD` rode it: "HEAD is now at" names where you are. The commits did not move: `rescue` still holds them. `survey.txt` left your folder.

**Designer note (what the picture does):** The `main` tag and the HEAD mark slide down two commits, next to `origin/main` and the mothership's pin. `survey.txt` fades out of the folder row.

### Beat 7: type

The player types:

```
$ git log --oneline
59e52f5 (HEAD -> main, origin/main) Start the project
```

**Rama:** One commit, as predicted. `git log` walks down from `HEAD`, and nothing below `Start the project` leads up to the survey commits. They are still in Git: `rescue` leads to them.

### Beat 8: whatif

**Rama:** What if you had not made the branch? No branch would lead to the two commits. You just saw them, so the picture draws them faded rather than hiding them. Git keeps commits no branch leads to for about 30 days, then may delete them, and `git log` would not list them. The next mission finds commits like these.

**Designer note (what the picture does):** Greyscale, under WHAT IF: the same reset without `rescue`. The two capsules fade to dashed outlines. Then it rewinds to the real state.

### Beat 9: done

**Debrief:**

`git reset --hard origin/main` moved the branch you were on, `main`, back down the chain, and made your folder match that commit. It deleted no commit: your two commits are still there, held by `rescue`.

Without `--hard`, reset moves the branch and leaves your files as they are. Use reset only on commits nobody else has: on a branch others have pulled, `git revert` is the safe undo.

Commands to keep:

```
$ git branch rescue              # a name on the commits first
$ git reset --hard origin/main   # then move main back
```

## Losses

- The two survey commits pushed onto the mothership's `main` (kept as today).

## Rama's reactions

- `git reset`: "`main` moved back. The commits it left are still in Git."
- A reset before the branch: the goal text says "No branch leads to your two commits now, but Git still has them. The next mission shows how to find them; for now, start again with Restart."

## Design notes (after playing)

**The one idea:** `git reset` moves the branch you are on. The commits it leaves stay in Git. `--hard` also makes your folder match.

**On screen:** The chain with the mothership's pin, and under it a small row with the files in your working folder. One WHAT IF beat in greyscale shows the same reset with no `rescue`.

**Hidden on purpose:** Alex (Alex plays no part), the staging area, the move log (it has a job in 8-4).

## Hints and solution (the last hint gives every line)

1. `git branch rescue` puts a new name on the commit you are on, so the two commits keep a name.
2. `git reset --hard origin/main` moves the branch you are on, `main`, to where `origin/main` is, and makes your files match.
3. Every line of the mission, in order:
   
       $ git branch rescue
       $ git reset --hard origin/main
       $ git log --oneline

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
