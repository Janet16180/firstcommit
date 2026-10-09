# 5-3 Two experiments

Mission. Command: `git switch`.

## Briefing

Yesterday you started one experiment, `bright-lights`, on its own branch, and came back to `main`. Today the captain wants a second one, `quiet-engine`, tried beside it; `engine.txt` is already written and waiting in your folder. `main` stays as it is.

## Goals

1. Put a name on `main`'s commit: `git branch quiet-engine`.
2. Go there: `git switch quiet-engine`.
3. Commit `engine.txt` there.
4. Predict first.
5. Switch to the other experiment: `git switch bright-lights`.
6. Draw the tree: `git log --oneline --graph --all`.

## Beats

### Beat 1: scene

**Rama:** Yesterday's experiment is the side line on the right: `bright-lights` and its commit, Try bright lights, joined to Fix the route. You are back on `main`. The row under the chain is your working folder: `engine.txt` is waiting there, not in Git yet.

**Designer note (what the picture does):** The chain already has one side line. The folder row stays under the chain for the whole level, so the layout never jumps.

### Beat 2: type

The player types:

```
$ git branch quiet-engine
(no output)
```

**Rama:** A second name on `main`'s commit. `HEAD` is still on `main`.

### Beat 3: type

The player types:

```
$ git switch quiet-engine
Switched to branch 'quiet-engine'
```

**Rama:** `HEAD` moved to `quiet-engine`. Your folder did not change: both names are on the same commit, and `engine.txt` is not in Git yet, so a switch leaves it alone.

**Designer note (what the picture does):** The HEAD mark hops to `quiet-engine`.

### Beat 4: type

The player types:

```
$ git add engine.txt
(no output)
```

**Rama:** Staged for the next commit.

### Beat 5: type

The player types:

```
$ git commit -m "Try a quiet engine"
[quiet-engine f286a29] Try a quiet engine
 1 file changed, 1 insertion(+)
 create mode 100644 engine.txt
```

**Rama:** `quiet-engine` moved up to the new commit, and `main` stayed. Two side lines off the same commit: the chain forks, like a tree. Each experiment has its own name and its own commit.

**Designer note (what the picture does):** A second side line appears, in its own column, left of the first.

### Beat 6: predict

**Prediction:** You switch to `bright-lights`. Is `engine.txt` still in your folder?

- Yes
- No

Reveal: No. The folder shows `bright-lights`' commit: `lights.txt` comes back and `engine.txt` goes. Both files are safe in their commits.

### Beat 7: type

The player types:

```
$ git switch bright-lights
Switched to branch 'bright-lights'
```

**Rama:** `HEAD` jumped across the tree to the other experiment, and the folder followed: `lights.txt` in, `engine.txt` out.

**Designer note (what the picture does):** The HEAD mark hops from one side line to the other. In the folder row, `engine.txt` is struck through and `lights.txt` appears.

### Beat 8: type

The player types:

```
$ git log --oneline --graph --all
* f286a29 (quiet-engine) Try a quiet engine
| * a444409 (HEAD -> bright-lights) Try bright lights
|/  
* 6b6a005 (origin/main, main) Fix the route
* 6c35b8f Note the fuel level
* 61255a6 Add the crew list
* 205de41 (first-route) Plot the route
* ce9b38c Start the project
```

**Rama:** The same tree, drawn by git in the terminal. Each `*` is a commit, and `|` and `/` are the lines between them. `--all` shows every branch, not just the line you are on. Your two experiments are lit in both pictures.

**Designer note (what the picture does):** The only gold rings in the level: they pair each experiment on the chain with its line in git's drawing.

### Beat 9: done

**Debrief:**

Two branches made from the same commit made the chain fork. `git switch` moved `HEAD` from one experiment to the other, and each time your folder changed to show that branch's commit. A commit moves only the name `HEAD` is on, so `main` never moved.

`git log --oneline --graph --all` draws the whole tree in the terminal, every branch included.

Commands to keep:

```
$ git switch bright-lights            # move HEAD to another branch
$ git log --oneline --graph --all     # the whole tree, drawn
```

## Losses

- A commit while still on `main`: "`main` moved, and the captain wanted it left as it is. Restart to try again."

## Rama's reactions

- `git checkout <name>`: "That works too: `git checkout <name>` is the older form of `git switch <name>`."

## Design notes (after playing)

**The one idea:** Two branches off the same commit make the chain fork like a tree. `git switch` moves `HEAD` between them, and your folder changes each time. `git log --oneline --graph --all` draws the same tree in the terminal.

**On screen:** The chain, with a row of the files in your working folder under it, the whole level; at the end, git's own drawing of the tree beside it.

**Hidden on purpose:** The mothership's pin (nothing goes up), Alex.

## Hints and solution (the last hint gives every line)

1. `git branch <name>` makes a name where you are; `git switch <name>` moves `HEAD` onto it.
2. `git add engine.txt`, then `git commit -m`, while on `quiet-engine`.
3. Every line of the mission, in order:
   
       $ git branch quiet-engine
       $ git switch quiet-engine
       $ git add engine.txt
       $ git commit -m "Try a quiet engine"
       $ git switch bright-lights
       $ git log --oneline --graph --all

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
