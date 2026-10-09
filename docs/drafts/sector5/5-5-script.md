# 5-5 Match the chart

Challenge. Command: `git branch`.

## Briefing

A new day. Overnight the captain kept your two experiments and cleared the other test names, except one: you left `HEAD` on `fuel-test`. The chart shows how the names should stand for the launch. Make your chain match it. The commits are already right, and so is your `origin/main` bookmark: leave it.

## Goals

1. Your names match the captain's chart.

## Beats

### Beat 1: scene

**Rama:** Left: your chain. Right: the captain's chart. Make your names match.

### Beat 2: type

The player types:

```
$ git log --oneline --graph --all
* f286a29 (quiet-engine) Try a quiet engine
| * a444409 (bright-lights) Try bright lights
|/  
* 6b6a005 (origin/main, main) Fix the route
* 6c35b8f (HEAD -> fuel-test) Note the fuel level
* 61255a6 Add the crew list
* 205de41 (first-route) Plot the route
* ce9b38c Start the project
```

**Designer note (what the picture does):** A challenge: Rama gives no guidance. `--all` shows the whole tree even though `HEAD` is on `fuel-test`.

### Beat 3: type

The player types:

```
$ git branch -d fuel-test
error: cannot delete branch 'fuel-test' used by worktree at '<lab>/project'
```

**Rama:** "Used by worktree" means your folder is showing that branch: `HEAD` is on it. Git will not take off the name `HEAD` is on. Move `HEAD` first.

**Designer note (what the picture does):** The first trap: `HEAD` is on `fuel-test`, so `-d` fails. Rama's line is a reaction to the error.

### Beat 4: type

The player types:

```
$ git switch main
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
```

**Designer note (what the picture does):** The HEAD mark hops to `main`.

### Beat 5: type

The player types:

```
$ git branch -d fuel-test
Deleted branch fuel-test (was 6c35b8f).
```

**Designer note (what the picture does):** `fuel-test` disappears; "names the chart does not have" drops to 0.

### Beat 6: type

The player types:

```
$ git branch release
(no output)
```

**Designer note (what the picture does):** `release` appears on Fix the route, where `HEAD` is; it gets its tick in the chart.

### Beat 7: type

The player types:

```
$ git switch bright-lights
Switched to branch 'bright-lights'
```

**Designer note (what the picture does):** The HEAD mark crosses the tree to `bright-lights`. The second trap was `git switch -c lights-v2` from `main`, which would put the name on the wrong commit.

### Beat 8: type

The player types:

```
$ git switch -c lights-v2
Switched to a new branch 'lights-v2'
```

**Designer note (what the picture does):** `lights-v2` appears on Try bright lights and the HEAD mark hops onto it. Every name in the chart has its tick, and all three counts are green. (`git branch lights-v2` then `git switch lights-v2` works too.)

### Beat 9: type

The player types:

```
$ git log --oneline --graph --all
* f286a29 (quiet-engine) Try a quiet engine
| * a444409 (HEAD -> lights-v2, bright-lights) Try bright lights
|/  
* 6b6a005 (origin/main, release, main) Fix the route
* 6c35b8f Note the fuel level
* 61255a6 Add the crew list
* 205de41 (first-route) Plot the route
* ce9b38c Start the project
```

**Rama:** Your names match the captain's chart, and git's drawing in the terminal agrees: `HEAD -> lights-v2` on the bright-lights experiment.

### Beat 10: done

**Debrief:**

Not one commit changed: only names moved on the tree. You took `HEAD` off `fuel-test` before removing it, put `release` where `HEAD` was, and crossed to the other side line before making `lights-v2`, because a new name always lands where `HEAD` is.

Commands to keep:

```
$ git switch main             # move HEAD off a name before taking it off
$ git branch -d fuel-test     # take a name off
$ git switch -c lights-v2     # a name where HEAD is, and go there
```

## Losses

- A new commit, or `main` moved: "The chart keeps every commit as it is. Restart to try again."

## Rama's reactions

- `git switch -c lights-v2` while on `main`: "`lights-v2` is where `HEAD` was, on `main`'s commit. The chart wants it on Try bright lights: go to `bright-lights` first."
- `git branch -d` on the branch `HEAD` is on: "\"Used by worktree\" means your folder is showing that branch: `HEAD` is on it. Git will not take off the name `HEAD` is on. Move `HEAD` first."

## Design notes (after playing)

**The one idea:** Combines this sector: names on a forked tree where the captain's chart says, commits left as they are.

**On screen:** Your chain on the left, the captain's chart on the right (the target, drawn as the same tree). A name in the chart gets a tick once yours is in place; under the chart, three counts: names in place, `HEAD` in place, names the chart does not have. No to-do list: the player finds each difference by comparing.

**Hidden on purpose:** The mothership's pin, the desk, Alex.

## Hints and solution (the last hint gives every line)

1. Compare the two pictures one name at a time, `HEAD` included.
2. `git branch <name>`, `git branch -d <name>`, `git switch <branch>` and `git switch -c <name>` are all you need. A new name lands where `HEAD` is.
3. Every line of the mission, in order:
   
       $ git switch main
       $ git branch -d fuel-test
       $ git branch release
       $ git switch bright-lights
       $ git switch -c lights-v2

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
