# Playground 1: Open and choose

Starting point: **Empty folder**. From the map to a starting point, a first commit, and Start over.

## Beats

### Beat 1

The player opens the map.

Beside the eight sectors, a landmark: Playground, free play.

### Beat 2

They pick the Playground.

### Beat 3

The playground asks where to start.

Seven starting points. Those that use commands from later chapters name the chapter ("uses Collisions"); none is locked.

*Designer note:* The first time only. Afterwards the playground opens where the player left it; Choose another brings the picker back.

### Beat 4

They choose Empty folder.

### Beat 5

The playground opens on the desk.

Two files in the working folder, "not in a repository". Your terminal says where you are and suggests `git init`. There is no Alex toggle: Alex joins only where there is a mothership to share. On a phone the picture starts folded into one line above the terminal.

*Designer note:* No goals, no stars, no Rama coaching: one suggestion in the terminal's first line, and that is all.

### Beat 6

They type `git status`.

Git's real answer: not a git repository.

```
project $ git status
fatal: not a git repository (or any of the parent directories): .git
```

### Beat 7

They type `git init`.

The desk's files turn "new: Git has no copy". The Commits zone says no commits yet.

```
project $ git init
Initialized empty Git repository in ~/.firstcommit/playground/project/.git/
```

### Beat 8

They type `git add README.md notes.txt`.

Both files move into the staging area. On a phone the one-line summary says "2 files changed".

```
project $ git add README.md notes.txt
```

### Beat 9

They type `git commit -m "Start my project"`.

The first commit lands in the Commits zone; the staging area empties.

```
project $ git commit -m "Start my project"
[main (root-commit) 7ead23f] Start my project
 2 files changed, 2 insertions(+)
 create mode 100644 README.md
 create mode 100644 notes.txt
```

### Beat 10

They type `git log --oneline` and pick the Chain view.

One capsule, `main` on it, HEAD riding it. The legend sits folded behind "i", and lists only what is on screen.

```
project $ git log --oneline
7ead23f (HEAD -> main) Start my project
```

### Beat 11

They press Start over.

The playground asks first: everything here goes back to how Empty folder began; missions are not touched.

### Beat 12

They confirm.

A fresh lab and a fresh terminal: two files, no repository, as at the start.

## Design notes

The playground is a landmark on the map, open from the start. The picker shows every starting point; those that use later chapters name the chapter, and none is locked. Empty opens on the desk, because the first thing to see is files that Git does not hold yet. With no mothership, Alex's toggle is off and says why. Start over always asks first, and says what it erases and what it never touches. On a phone the picture folds into one line above the terminal ("Desk · no repository yet"); a tap unfolds it.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
