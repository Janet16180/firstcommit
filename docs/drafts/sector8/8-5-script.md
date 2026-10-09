# 8-5 Night shift

Challenge. Command: `git reflog`.

## Briefing

Two nights of thruster tuning went into commits on a branch `thrusters`. Half asleep, you switched to `main` and deleted the branch with `git branch -D thrusters`: the name went, the commits stayed with no name. This morning you pulled Alex's commit `Note the free dock`. Get `thrusters` back, and up to the mothership, before the review.

## Goals

1. Your repository has a branch `thrusters` holding both thruster commits.
2. The mothership has `thrusters` with both commits, and its `main` is untouched.

## Beats

### Beat 1: scene

**Rama:** Alarm on the engine deck: two nights of thruster work vanished with its branch. Nothing was pushed, but `HEAD` keeps a move log. Careful: the move log counts back from now, so its numbers are not the last mission's.

### Beat 2: type

The player types:

```
$ git log --oneline
81eef63 (HEAD -> main, origin/main) Note the free dock
2f97979 Start the project
```

**Designer note (what the picture does):** A challenge: Rama gives no guidance. `git log` lists only `main`'s two commits.

### Beat 3: type

The player types:

```
$ git reflog
81eef63 (HEAD -> main, origin/main) HEAD@{0}: pull: Fast-forward
2f97979 HEAD@{1}: checkout: moving from thrusters to main
832782f HEAD@{2}: commit: Tune the thrusters, day 2
6aa94af HEAD@{3}: commit: Tune the thrusters, day 1
2f97979 HEAD@{4}: checkout: moving from main to thrusters
2f97979 HEAD@{5}: clone: from <lab>/github.com/moonbase/project.git
```

**Designer note (what the picture does):** The move log fills, row by row, in step with the terminal. In a challenge nothing on the chain or in the move log marks the lost commits: the player reads the lines. `checkout: moving from thrusters to main` is a tempting wrong line (it is where `main` was, not the thruster work).

### Beat 4: type

The player types:

```
$ git branch thrusters HEAD@{2}
(no output)
```

**Designer note (what the picture does):** A `thrusters` tag appears with both thruster commits under it, on a side line off `Start the project`. The first goal checks.

### Beat 5: type

The player types:

```
$ git push -u origin thrusters
To ../github.com/moonbase/project.git
 * [new branch]      thrusters -> thrusters
branch 'thrusters' set up to track 'origin/thrusters'.
```

**Rama:** The mothership has `thrusters` with both commits, and its `main` is untouched.

**Designer note (what the picture does):** A mothership pin `thrusters` appears on the thruster commit, next to your `origin/thrusters` bookmark. The second goal checks.

### Beat 6: done

**Debrief:**

`git branch -D` removed a name, not the commits. `git reflog` showed every move of `HEAD`, and `HEAD@{2}`, two moves back, was the last thruster commit. `git branch thrusters HEAD@{2}` gave it its name back, both commits with it, and `git push -u origin thrusters` sent them up for review.

Commands to keep:

```
$ git reflog                       # where HEAD has been
$ git branch thrusters HEAD@{2}    # a name on a commit from the move log
$ git push -u origin thrusters     # and up it goes
```

## Losses

- The commits erased for good, or pushed onto the mothership's `main` (as today).

## Rama's reactions

- `git gc`, `git prune`, `git reflog expire|delete`: the wipe warning (as today).
- A wrong line, such as `git branch thrusters HEAD@{1}`: the first goal stays open with "Your repository has no branch `thrusters` holding both commits." Real output in `out/7-5-wrong.txt`: `git log --oneline thrusters` then lists only `Start the project`.

## Design notes (after playing)

**The one idea:** Combines branches (a name, a push by name) and this sector (the move log finds commits no branch leads to).

**On screen:** The move log, large, empty until `git reflog` is typed. Below it: the chain with the mothership's pins, the thruster commits in a side line of their own.

**Hidden on purpose:** Alex's pin (Alex's note is just a commit on `main`), the desk.

## Hints and solution (the last hint gives every line)

1. This is branches and this sector: commits no branch leads to, a name, and a push by name. A branch can be pushed from anywhere, by name: `git push -u origin thrusters` (or `git push origin thrusters`).
2. The move log lists where `HEAD` has been. Find your last thruster commit there; a branch on it brings both back. Its `HEAD@{n}` and the hash at the start of its line both work. You can push a branch without switching to it.
3. Every line of the mission, in order (the hash of that line works as well as `HEAD@{2}`):
   
       $ git reflog
       $ git branch thrusters HEAD@{2}
       $ git push -u origin thrusters

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
