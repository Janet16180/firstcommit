# 8-4 The move log

Mission. Command: `git reflog`.

## Briefing

The next day, the same mistake: two survey commits on `main`. This time you moved `main` back with `git reset --hard origin/main` and forgot to name them. Find the two commits and put a branch `survey` on them.

## Goals

1. Look for them in the history: `git log --oneline`.
2. Read the move log: `git reflog`.
3. Put a branch `survey` on Survey day 2.
4. Predict first.
5. Go there: `git switch survey`.
6. Read the move log again: `git reflog`.

## Beats

### Beat 1: scene

**Rama:** The next day, the same mistake: two survey commits on `main`. This time you moved `main` back and forgot to name them. The chain shows only `Start the project`: no branch leads to the survey commits, and you have not looked for them yet.

### Beat 2: type

The player types:

```
$ git log --oneline
59e52f5 (HEAD -> main, origin/main) Start the project
```

**Rama:** `git log` starts at `HEAD` and walks back through the parents. The survey commits came after `Start the project`, and no branch leads to them, so `git log` cannot list them.

### Beat 3: type

The player types:

```
$ git reflog
59e52f5 (HEAD -> main, origin/main) HEAD@{0}: reset: moving to origin/main
0be9911 HEAD@{1}: commit: Survey day 2
ec56de1 HEAD@{2}: commit: Survey day 1
59e52f5 (HEAD -> main, origin/main) HEAD@{3}: clone: from <lab>/github.com/moonbase/project.git
```

**Rama:** `git log` is the story of your commits. `git reflog` is the story of your moves: every place `HEAD` has been, newest at the top. Think of your browser's history, which lists even the pages you closed. It lives only on your computer.

**Designer note (what the picture does):** The move log is born. Its rows light up one by one, in step with the terminal's lines. As the two `commit` rows light, two faded, dashed capsules appear above `Start the project` on the chain.

### Beat 4: say

**Rama:** Read it from the bottom up. `clone`: your first move, when the repository was made. Two `commit`s: the survey commits you made before the reset. `reset`: the move back, which is where you are now. The top and bottom lines name the same commit: you stood on `Start the project` twice. The names in brackets on some lines show where names sit now, not where they were then.

### Beat 5: say

**Rama:** After its hash, each line has a name for that place: `HEAD@{0}` is where you are now, `HEAD@{1}` where you were one move ago, and so on back. `HEAD~1` walks back along the parents; `HEAD@{1}` walks back through your own moves. Find Survey day 2, and use its name to put a branch `survey` on it.

**Designer note (what the picture does):** Picking a row in the move log rings its capsule on the chain.

### Beat 6: type

The player types:

```
$ git branch survey HEAD@{1}
(no output)
```

**Rama:** A name on Survey day 2, and both survey commits are solid again: Survey day 1 is its parent. They were never gone.

**Designer note (what the picture does):** A `survey` tag lands on the faded capsule; both capsules fill in solid. In the move log, "no name" disappears from both rows.

### Beat 7: predict

**Prediction:** Next you go to the branch with `git switch survey`. After that, which number will the line `commit: Survey day 2` have?

- Still `HEAD@{1}`
- `HEAD@{2}`
- `HEAD@{0}`

Reveal: `HEAD@{2}`. Going to a branch is a move, so it becomes the newest line, `HEAD@{0}`, and every older line counts one further back.

### Beat 8: type

The player types:

```
$ git switch survey
Switched to branch 'survey'
```

**Rama:** You are on `survey`, and `survey.txt` is back in your folder. Read the move log again.

**Designer note (what the picture does):** The HEAD mark hops from `main` to `survey`.

### Beat 9: type

The player types:

```
$ git reflog
0be9911 (HEAD -> survey) HEAD@{0}: checkout: moving from main to survey
59e52f5 (origin/main, main) HEAD@{1}: reset: moving to origin/main
0be9911 (HEAD -> survey) HEAD@{2}: commit: Survey day 2
ec56de1 HEAD@{3}: commit: Survey day 1
59e52f5 (origin/main, main) HEAD@{4}: clone: from <lab>/github.com/moonbase/project.git
```

**Rama:** One new line on top, and every number grew by one, as predicted: Survey day 2 was `HEAD@{1}`, now it is `HEAD@{2}`. The numbers count back from now, so read the move log right before you use it, or use the hash at the start of the line instead: it never shifts. The new line says `checkout`: that is the older name of `git switch`.

**Designer note (what the picture does):** A new row slides in at the top; the others move down and renumber. The picked row keeps its commit: its name changes from `HEAD@{1}` to `HEAD@{2}`.

### Beat 10: done

**Debrief:**

`git log` only walks back from `HEAD` through the parents, so it could not see the survey. `git reflog` lists every move of `HEAD`, newest first, and `HEAD@{1}` named the commit from one move ago. `git branch survey HEAD@{1}` put a name on it, and both commits came back.

The hash at the start of each line works too, and unlike `HEAD@{n}` it never shifts. The move log lives only in your repository, and Git keeps commits no branch leads to for about 30 days. A branch keeps them for good.

Commands to keep:

```
$ git reflog                    # every place HEAD has been
$ git branch survey HEAD@{1}    # a name on a commit from the move log
```

## Losses

- The lost commits erased for good (`git gc --prune=now` with an expired reflog, or `git reflog expire`): "The survey commits are gone for good. Start the mission again."

## Rama's reactions

- `git gc`, `git prune`, `git reflog expire|delete`: the warning from today's black-box level ("Give them a name first").
- `git branch survey HEAD@{0}` (wrong line): "`survey` is on `Start the project`, where you are now. Survey day 2 is one move back: `HEAD@{1}`."

## Design notes (after playing)

**The one idea:** `git reflog` is the move log: every place HEAD has been, newest first. `HEAD@{1}` means "where HEAD was one move ago". A branch name brings a lost commit back.

**On screen:** The move log, large: one row per `git reflog` line, in git's order. Below it: the chain, where the lost commits appear faded once the move log lists them.

**Hidden on purpose:** The mothership, Alex, the desk.

## Hints and solution (the last hint gives every line)

1. `git log` only walks back from where you are. `git reflog` lists every place HEAD has been, even commits no branch leads to.
2. Find the line `commit: Survey day 2` in the move log; the `HEAD@{n}` after its hash names that commit. `git branch survey` followed by that name puts a name on it.
3. Every line of the mission, in order:
   
       $ git log --oneline
       $ git reflog
       $ git branch survey HEAD@{1}
       $ git switch survey
       $ git reflog

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
