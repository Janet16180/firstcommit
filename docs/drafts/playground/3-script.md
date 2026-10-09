# Playground 3: Uncommitted changes

Starting point: **Uncommitted changes**. An edit that is not committed: it comes along on a switch, and git restore throws it away.

## Beats

### Beat 1

The playground opens on Uncommitted changes, on the desk.

notes.txt is edited; the staging area is empty. On a phone: "Desk · HEAD on main · main in step with origin/main · 1 file changed".

### Beat 2

They type `git status`.

modified: notes.txt, not staged.

```
project $ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   notes.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

### Beat 3

They type `git diff`.

The one line they added: `+Fuel: 80%`.

```
project $ git diff
diff --git a/notes.txt b/notes.txt
index e38d7f6..19d1ebd 100644
--- a/notes.txt
+++ b/notes.txt
@@ -1 +1,2 @@
 Notes
+Fuel: 80%
```

### Beat 4

They type `git switch bright-lights`.

Git switched and printed `M notes.txt`: the edit came along. The desk still shows notes.txt edited, and lights.txt marked "came with the switch".

```
project $ git switch bright-lights
Switched to branch 'bright-lights'
M	notes.txt
```

### Beat 5

They pick Chain.

HEAD on the bright-lights side line. Under the chain, one line: in your folder, in no commit yet: notes.txt (modified).

### Beat 6

They type `git status`.

On branch bright-lights, notes.txt still modified.

```
project $ git status
On branch bright-lights
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   notes.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

### Beat 7

They type `git switch main` and pick Desk.

Back on main; the edit came back with them (`M notes.txt` again).

```
project $ git switch main
Switched to branch 'main'
M	notes.txt
Your branch is up to date with 'origin/main'.
```

### Beat 8

They type `git restore notes.txt`.

notes.txt is no longer edited: the Fuel line is gone for good.

```
project $ git restore notes.txt
```

### Beat 9

They type `git status`.

nothing to commit, working tree clean.

```
project $ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

## Design notes

A starting point for the working folder: an edit Git has no copy of, a branch to switch to, and `git restore`. It opens on the desk. `git switch` carries the edit along (`M notes.txt`), which the desk shows: the file stays "edited" while HEAD moves. Stash is out of scope.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
