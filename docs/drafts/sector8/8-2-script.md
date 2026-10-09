# 8-2 Recall the capsule

Mission. Command: `git revert`.

## Briefing

Yesterday you pushed a commit that set the station's lights to strobe, then a good one with the night route. Alex pulled both, and the strobe is giving everyone headaches. Undo the strobe for the whole crew, and keep the night route.

## Goals

1. Predict first.
2. Find the strobe commit: `git log --oneline`.
3. Undo it with a new commit: `git revert HEAD~1`.
4. Send the undo up: `git push`.

## Beats

### Beat 1: scene

**Rama:** Yesterday you pushed the strobe commit, then the night route. The pins show the mothership and Alex have both.

### Beat 2: predict

**Prediction:** `main` has 4 commits now. You undo the strobe with `git revert`. How many will it have afterwards?

- 3: the strobe commit is taken out
- 4: the strobe commit is replaced
- 5: a new commit is added

Reveal: 5. `git revert` never takes a commit out. It adds a new one that does the opposite, so the history Alex already has stays true.

### Beat 3: type

The player types:

```
$ git log --oneline
8ca2a79 (HEAD -> main, origin/main) Add the night route
6b208b4 Try strobe lights
78fc827 Set the station lights
4f936a1 Start the project
```

**Rama:** Newest first. The strobe commit is second from the top.

**Designer note (what the picture does):** The strobe capsule is ringed on the chain, the same commit as the highlighted terminal line.

### Beat 4: say

**Rama:** Git can name it from `HEAD`: `HEAD~1` is one step back along the parents, the commit just before the one you are on.

### Beat 5: type

The player types:

```
$ git revert HEAD~1
[main 800a558] Revert "Try strobe lights"
 Date: Thu Oct 8 10:55:09 2026 -0600
 1 file changed, 1 insertion(+), 1 deletion(-)
```

**Rama:** A new commit landed on top, the mirror of the strobe one. The strobe commit is still there, and so is the night route. `main` and `HEAD` moved up onto the new commit; the mothership's pin and Alex's pin did not, because they don't have it yet.

**Designer note (what the picture does):** A striped capsule lands on top, and a gold arc bends from it back to the strobe capsule: "undoes".

### Beat 6: type

The player types:

```
$ git push
To ../github.com/moonbase/project.git
   8ca2a79..800a558  main -> main
```

**Rama:** The mothership has your undo. Your push only added a commit on top of what the mothership already had.

**Designer note (what the picture does):** The mothership's pin climbs onto the undo capsule, and so does your `origin/main` bookmark.

### Beat 7: event

Event: Alex pulled.

**Rama:** Alex pulled, and the undo reached Alex's station the normal way. Everyone's lights are steady again.

**Designer note (what the picture does):** Alex's pin climbs onto the undo capsule. HEAD, the mothership and Alex now sit on the same commit.

### Beat 8: done

**Debrief:**

`git revert HEAD~1` did not remove the strobe commit: it made a new commit that does the opposite. The history now tells the whole story, the strobe and its undo.

Because nothing in the shared history changed, `git push` went through, and Alex's next `git pull` brought the undo. That is why revert is the undo for a commit others already have. The next mission's `git reset` is for commits only you have.

In the game, `git revert` keeps the message Git suggests (`Revert "Try strobe lights"`). On your own computer it first opens an editor showing that message: save and close it, or type `git revert --no-edit HEAD~1` to skip the editor.

Commands to keep:

```
$ git log --oneline     # find the commit to undo
$ git revert HEAD~1     # a new commit that undoes it
$ git push              # everyone gets the undo by pulling
```

## Losses

- A forced push that drops the shared commits from the mothership ("`--force` replaced the mothership's `main`... Start the mission again.").

## Rama's reactions

- `git reset`: warns that the mothership and Alex still have the commits, with the WHAT IF "force-break" moment (kept, only on that path).
- `git push --force`: the error reaction and the same moment (kept).

## Design notes (after playing)

**The one idea:** `git revert` undoes a commit others already have by adding a new commit. Nothing is taken out of the history. Also: what HEAD is, and `HEAD~1`.

**On screen:** The chain: every commit once, your branch names on it, the HEAD mark, and two pins: where the mothership's `main` is and where Alex's `main` is. Alex matters here because Alex receives the undo.

**Hidden on purpose:** The desk (no file matters here), the move log.

## Hints and solution (the last hint gives every line)

1. `git log --oneline` lists the commits, newest first: the strobe one is second from the top, `HEAD~1`.
2. `git revert HEAD~1` makes a new commit that undoes it; `git push` sends that commit up.
3. Every line of the mission, in order:
   
       $ git log --oneline
       $ git revert HEAD~1
       $ git push

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
