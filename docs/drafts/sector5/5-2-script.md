# 5-2 A name on any commit

Mission. Command: `git branch <name> <commit>`.

## Briefing

Before this mission you ran `git pull`, the step the last mission ended on, so `main` is on Alex's fix, Fix the route. `test-run`, an old name on Start the project, can go. Then the captain wants the commit where the route was first plotted easy to find, under a name `first-route`.

## Goals

1. Read the history: `git log --oneline`.
2. Predict first.
3. Take the old name off: `git branch -d test-run`.
4. Check: `git log --oneline`.
5. Predict first.
6. Name the commit: `git branch first-route <its hash>`.
7. Check: `git log --oneline`.

## Beats

### Beat 1: scene

**Rama:** After your pull, `main` slid up to Alex's fix, and your bookmark and the pin are there too. `test-run` is still on Start the project.

### Beat 2: type

The player types:

```
$ git log --oneline
6b6a005 (HEAD -> main, origin/main) Fix the route
6c35b8f Note the fuel level
61255a6 Add the crew list
205de41 Plot the route
ce9b38c (test-run) Start the project
```

**Rama:** Each line starts with the commit's hash: the way to name a commit to Git. The highlighted line is Start the project, with `test-run` on it.

### Beat 3: say

**Rama:** Each commit remembers the one before it: its parent. The lines on the chain show it. `git log` starts at `main`'s commit and follows those lines down to the first commit: watch them light up.

**Designer note (what the picture does):** The lines light up in gold one by one, from `main`'s commit down to Start the project.

### Beat 4: predict

**Prediction:** You take the name `test-run` off with `git branch -d test-run`. What happens to the Start the project commit?

- It is deleted too
- It stays

Reveal: It stays. A name points at a commit; it is not the commit. And `main` still leads down the lines to it.

### Beat 5: type

The player types:

```
$ git branch -d test-run
Deleted branch test-run (was ce9b38c).
```

**Rama:** Git says which commit the name pointed at: look at "was" and the hash after it. The commit is still there.

**Designer note (what the picture does):** The `test-run` tag disappears; the capsule stays.

### Beat 6: type

The player types:

```
$ git log --oneline
6b6a005 (HEAD -> main, origin/main) Fix the route
6c35b8f Note the fuel level
61255a6 Add the crew list
205de41 Plot the route
ce9b38c Start the project
```

**Rama:** Still five commits. Only a name went. Now find Plot the route, one line up: its hash is the one you need next.

### Beat 7: predict

**Prediction:** You put a new name `first-route` on Plot the route, by its hash. What happens to your folder?

- It shows that commit's files
- Nothing changes

Reveal: Nothing changes. `git branch` only writes a name. `HEAD` stays on `main`, so your files stay as they are.

### Beat 8: type

The player types:

```
$ git branch first-route 205de41
(no output)
```

**Rama:** A name on an old commit, and nothing else moved. Without a hash, `git branch` puts the name where you are.

**Designer note (what the picture does):** A `first-route` tag appears on Plot the route. The HEAD mark does not move.

### Beat 9: type

The player types:

```
$ git log --oneline
6b6a005 (HEAD -> main, origin/main) Fix the route
6c35b8f Note the fuel level
61255a6 Add the crew list
205de41 (first-route) Plot the route
ce9b38c Start the project
```

**Rama:** `git log` shows the new name in brackets on its commit.

### Beat 10: done

**Debrief:**

`git branch -d test-run` took a name off and the commit stayed: names point at commits, they are not the commits. `git branch first-route <hash>` put a name on an old commit without moving you.

Commands to keep:

```
$ git branch -d test-run          # take a name off; the commit stays
$ git branch first-route <hash>   # a name on any commit
```

## Losses


## Rama's reactions

- `git switch first-route`: "You moved `HEAD` onto `first-route`, and your folder now shows that commit's files. `git switch main` brings you back." (allowed, not a loss).

## Design notes (after playing)

**The one idea:** You can take a name off and put a name on any commit. Commits stay as they are; only names come and go.

**On screen:** The chain with the mothership's pin.

**Hidden on purpose:** The desk, Alex.

## Hints and solution (the last hint gives every line)

1. `git branch -d <name>` takes a name off. Each line of `git log --oneline` starts with the commit's hash.
2. `git branch <name> <hash>` puts a name on that commit.
3. Every line of the mission, in order:
   
       $ git log --oneline
       $ git branch -d test-run
       $ git log --oneline
       $ git branch first-route {{route}}
       $ git log --oneline

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
