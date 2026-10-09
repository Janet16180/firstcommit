# 8-1 Scrap the workshop

Mission. Command: `git restore`.

## Briefing

Last night's experiment in `engine.cfg` overheated the engine. Scrap it and go back to the committed settings. Your notes in `notes.txt` are staged for the next commit: keep them.

## Goals

1. Predict first.
2. Look at the experiment: `git diff`.
3. Scrap it: `git restore engine.cfg`.
4. Check your notes are still staged: `git status`.

## Beats

### Beat 1: scene

**Rama:** Last night's experiment overheated the engine. In `engine.cfg`, one line changed and one line was added: the two red lines.

### Beat 2: predict

**Prediction:** You scrap the experiment with `git restore engine.cfg`. Tomorrow you want it back. Can Git give you the two red lines?

- Yes, Git keeps every version of a file
- No, they are gone for good

Reveal: No. Git keeps only what you staged or committed. The dashed line shows it: the staging area and your commits are inside. The red lines exist only in your working folder, so Git never had a copy.

**Designer note (what the picture does):** On the reveal, the dashed outline "Git has a copy" draws itself round the staging area and the commits. The red lines stay outside it.

### Beat 3: type

The player types:

```
$ git diff
diff --git a/engine.cfg b/engine.cfg
index 0703be3..b0ced8c 100644
--- a/engine.cfg
+++ b/engine.cfg
@@ -1 +1,2 @@
-power=80
+power=99
+overdrive=on
```

**Rama:** `git diff` shows what is in your working folder and not staged. `-` is the line Git has, `+` the lines only you have. Look before they go.

**Designer note (what the picture does):** The two red lines blink, the same lines as the `+` lines in the terminal.

### Beat 4: type

The player types:

```
$ git restore engine.cfg
(no output)
```

**Rama:** `git restore` copied Git's copy of `engine.cfg`, `power=80`, over yours. The two red lines are gone for good. `git restore` printed nothing: most git commands are quiet when they work.

**Designer note (what the picture does):** The red lines dissolve. `notes.txt` stays where it was.

### Beat 5: type

The player types:

```
$ git status
On branch main
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   notes.txt
```

**Rama:** Your notes are still staged, ready for the next commit. `git restore` changed only the file you named.

### Beat 6: done

**Debrief:**

`git restore engine.cfg` copied Git's copy over your file: the staged copy when there is one, otherwise the committed one. `engine.cfg` was never staged, so it got the committed `power=80`. The experiment's lines were never staged or committed, so Git had no copy of them, and no command can bring them back.

`notes.txt` was safe all along: it was inside "Git has a copy". Before you scrap a file, `git diff` shows exactly what you are about to lose.

In sector 2, `git restore --staged` took a file out of the staging area and kept your folder's copy as it was. Without `--staged`, `git restore` replaces your folder's copy: that is the one that can lose work.

Commands to keep:

```
$ git diff                 # what is in the working folder and not staged
$ git restore engine.cfg   # scrap it: back to Git's copy
```

## Losses

- `git restore --staged notes.txt` followed by `git restore notes.txt` throws the staged notes away: the level is lost for this play ("Your staged notes are gone: they were in no commit. Start the mission again.").

## Rama's reactions

- Any `git restore` or `git checkout` of a file (not `--staged`): "The experiment's lines are gone for good: Git had no copy of them." The search-beam moment is dropped; the dissolve on the desk says it.

## Design notes (after playing)

**The one idea:** `git restore` puts a file in your working folder back to the version Git has a copy of. Lines Git has no copy of are gone for good.

**On screen:** The desk only: your working folder with `engine.cfg`'s lines drawn, the staging area and your commits. After the prediction, a dashed outline "Git has a copy" draws round the staging area and the commits.

**Hidden on purpose:** The mothership (this level has none), the move log.

## Hints and solution (the last hint gives every line)

1. `git diff` shows the lines in your working folder that are not staged: the experiment.
2. `git restore engine.cfg` copies Git's copy of the file over yours. `engine.cfg` was never staged, so Git's copy is the committed one.
3. Every line of the mission, in order:
   
       $ git diff
       $ git restore engine.cfg
       $ git status

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
