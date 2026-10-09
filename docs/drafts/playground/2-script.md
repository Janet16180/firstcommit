# Playground 2: Two branches, every view

Starting point: **Two branches**. One switch, seen through each view in turn: chain, desk, history, graph, move log, crew.

## Beats

### Beat 1

The playground opens on Two branches, on the chain.

main, and two side lines off its commit: `bright-lights` and `quiet-engine`. HEAD rides `main`. With Alex hidden, no pins: the mothership's `main` is where your bookmark says.

### Beat 2

They type `git branch -v`.

Three names and the commit each names; `*` on main.

```
project $ git branch -v
  bright-lights 3c9081a Try bright lights
* main          44c16d0 Add the crew list
  quiet-engine  1942d3b Try a quiet engine
```

### Beat 3

They type `git switch bright-lights`.

The HEAD mark crosses to the bright-lights side line. On a phone the summary reads "HEAD on bright-lights".

```
project $ git switch bright-lights
Switched to branch 'bright-lights'
```

### Beat 4

They pick Desk.

`lights.txt` is in the working folder now: the folder shows bright-lights' commit.

### Beat 5

They pick History.

Your repository beside the mothership, row for row. The two experiments are side lines on your side only: they were never pushed.

### Beat 6

They type `git log --oneline --graph --all`, and pick Graph under More views.

The same drawing as in the terminal, kept up to date in the picture.

```
project $ git log --oneline --graph --all
* 1942d3b (quiet-engine) Try a quiet engine
| * 3c9081a (HEAD -> bright-lights) Try bright lights
|/  
* 44c16d0 (origin/main, main) Add the crew list
* a38b821 Plot the route
* b9e397c Start the project
```

### Beat 7

They pick Move log under More views.

Empty: Type `git reflog` to read the move log.

### Beat 8

They type `git reflog`.

The move log fills with exactly the lines git printed, the switch at the top. Under it, once: Live here: from now on it updates by itself. In missions you type `git reflog` each time.

```
project $ git reflog
3c9081a (HEAD -> bright-lights) HEAD@{0}: checkout: moving from main to bright-lights
44c16d0 (origin/main, main) HEAD@{1}: checkout: moving from quiet-engine to main
1942d3b (quiet-engine) HEAD@{2}: commit: Try a quiet engine
44c16d0 (origin/main, main) HEAD@{3}: checkout: moving from bright-lights to quiet-engine
3c9081a (HEAD -> bright-lights) HEAD@{4}: commit: Try bright lights
44c16d0 (origin/main, main) HEAD@{5}: checkout: moving from main to bright-lights
44c16d0 (origin/main, main) HEAD@{6}: commit: Add the crew list
a38b821 HEAD@{7}: commit: Plot the route
b9e397c HEAD@{8}: clone: from ~/.firstcommit/playground/github.com/moonbase/project.git
```

### Beat 9

They pick Crew.

The mothership over two stations, yours and Alex's, each with its HEAD mark. Alex's station has only main: the experiments are yours alone.

## Design notes

The tabs put Chain, History, Desk and Crew first; Move log and Graph sit under More views. Every view shows the repository as it is now, whatever the player typed. The views are the pictures the levels already teach, so nothing new is drawn for the playground. History shows only the chart (the user's decision): your repository beside the mothership, shared commits on shared rows, and branches as side lines, so a fork is never flattened into one column. Graph is git's own `--graph --all`: no starting point opens on it, since the terminal says the same. The move log stays empty until `git reflog` is typed, as in the missions; from then on it updates by itself, and says so once.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
