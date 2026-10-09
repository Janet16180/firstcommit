# 5-4 One step

Mission. Command: `git switch -c`.

## Briefing

A third experiment: dim lights, from `main`, where you are. `dim.txt` is already in your folder. Rama has a shorter command to show you, and then the older ones you will see in tutorials and at work.

## Goals

1. Predict first.
2. Try the short command: `git switch -c dim-lights`.
3. Commit `dim.txt`.
4. Draw the tree: `git log --oneline --graph --all`.
5. Go to `quiet-engine`, the older way: `git checkout quiet-engine`.
6. The short command, the older way: `git checkout -b night-watch`.
7. List your branches: `git branch -v`.

## Beats

### Beat 1: scene

**Rama:** Last time, starting an experiment took two commands: `git branch quiet-engine`, then `git switch quiet-engine`. Today's command is `git switch -c dim-lights`. The `-c` means create.

### Beat 2: predict

**Prediction:** You type `git switch -c dim-lights` while on `main`. Where is `HEAD` afterwards?

- On `main`
- On `dim-lights`
- On a new commit

Reveal: On `dim-lights`. Git makes the name `dim-lights` on the commit you are on, then moves `HEAD` onto it: both of last time's commands in one. No commit is made.

### Beat 3: type

The player types:

```
$ git switch -c dim-lights
Switched to a new branch 'dim-lights'
```

**Rama:** "A new branch", and you are on it, in one step.

**Designer note (what the picture does):** A `dim-lights` tag appears beside `main`; the HEAD mark hops onto it.

### Beat 4: type

The player types:

```
$ git add dim.txt
(no output)
```

**Rama:** Staged.

### Beat 5: type

The player types:

```
$ git commit -m "Try dim lights"
[dim-lights 2ea5abc] Try dim lights
 1 file changed, 1 insertion(+)
 create mode 100644 dim.txt
```

**Rama:** A third side line off the same commit.

**Designer note (what the picture does):** A third column appears.

### Beat 6: type

The player types:

```
$ git log --oneline --graph --all
* 2ea5abc (HEAD -> dim-lights) Try dim lights
| * f286a29 (quiet-engine) Try a quiet engine
|/  
| * a444409 (bright-lights) Try bright lights
|/  
* 6b6a005 (origin/main, main) Fix the route
* 6c35b8f Note the fuel level
* 61255a6 Add the crew list
* 205de41 (first-route) Plot the route
* ce9b38c Start the project
```

**Rama:** Git's drawing grows a third line too. It draws the same lines a little differently from the chain: the newest experiment comes first, and each side line closes with its own `|/`. Match the two pictures by name, not by place. Your new experiment is lit in both.

### Beat 7: say

**Rama:** You will also meet `git checkout`, in tutorials and at work. It is older and does many jobs, even restoring files, so Git added `git switch` for just one job: moving between branches. `git checkout <name>` is the same as `git switch <name>`, and `git checkout -b <name>` the same as `git switch -c <name>`. Use `switch`; read `checkout` when you see it. Try them.

### Beat 8: type

The player types:

```
$ git checkout quiet-engine
Switched to branch 'quiet-engine'
```

**Rama:** Same as `git switch quiet-engine`.

**Designer note (what the picture does):** The HEAD mark hops to `quiet-engine`.

### Beat 9: type

The player types:

```
$ git checkout -b night-watch
Switched to a new branch 'night-watch'
```

**Rama:** Same as `git switch -c night-watch`: a new name where you are, and you on it.

**Designer note (what the picture does):** A `night-watch` tag appears beside `quiet-engine`; the HEAD mark hops onto it.

### Beat 10: type

The player types:

```
$ git branch -v
  bright-lights a444409 Try bright lights
  dim-lights    2ea5abc Try dim lights
  first-route   205de41 Plot the route
  main          6b6a005 Fix the route
* night-watch   f286a29 Try a quiet engine
  quiet-engine  f286a29 Try a quiet engine
```

**Rama:** Six names now. `night-watch` and `quiet-engine` name the same commit.

### Beat 11: done

**Debrief:**

`git switch -c dim-lights` made the name where you were and moved `HEAD` onto it; your commit then grew a third side line. `git checkout -b` and `git checkout` are the older forms of `git switch -c` and `git switch`: they do the same, and the game accepts either.

Commands to keep:

```
$ git switch -c dim-lights      # a new branch, and go there
$ git checkout -b dim-lights    # the same, older form
$ git checkout main             # the same as git switch main
```

## Losses


## Rama's reactions


## Design notes (after playing)

**The one idea:** `git switch -c <name>` makes a new name where you are and moves `HEAD` onto it, in one step. `git checkout -b` and `git checkout` are the older forms.

**On screen:** The chain, and git's drawing of the tree after the third experiment.

**Hidden on purpose:** The desk (`dim.txt` is mentioned, not drawn), the mothership's pin, Alex.

## Hints and solution (the last hint gives every line)

1. `git switch -c <name>` is `git branch <name>` and `git switch <name>` together.
2. `git checkout <name>` does what `git switch <name>` does; `git checkout -b <name>` does what `git switch -c <name>` does.
3. Every line of the mission, in order:
   
       $ git switch -c dim-lights
       $ git add dim.txt
       $ git commit -m "Try dim lights"
       $ git log --oneline --graph --all
       $ git checkout quiet-engine
       $ git checkout -b night-watch
       $ git branch -v

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
