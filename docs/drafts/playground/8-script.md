# Playground 8: Something lost

Starting point: **Something lost**. The move log, empty until git reflog is typed: the deleted branch's commits have no name, and one command names them again.

## Beats

### Beat 1

The playground opens on Something lost, on the Move log.

Empty: Type `git reflog` to read the move log.

### Beat 2

They type `git log --oneline --all`.

Three commits: the thruster tests are not there. No name leads to them.

```
project $ git log --oneline --all
44c16d0 (HEAD -> main, origin/main) Add the crew list
a38b821 Plot the route
b9e397c Start the project
```

### Beat 3

They type `git reflog`.

The move log fills with the lines git printed. Two say "no name". Under it, once: Live here: from now on it updates by itself.

```
project $ git reflog
44c16d0 (HEAD -> main, origin/main) HEAD@{0}: checkout: moving from thrusters to main
fd1588f HEAD@{1}: commit: Test the right thruster
f4b87c0 HEAD@{2}: commit: Test the left thruster
44c16d0 (HEAD -> main, origin/main) HEAD@{3}: checkout: moving from main to thrusters
44c16d0 (HEAD -> main, origin/main) HEAD@{4}: commit: Add the crew list
a38b821 HEAD@{5}: commit: Plot the route
b9e397c HEAD@{6}: clone: from ~/.firstcommit/playground/github.com/moonbase/project.git
```

### Beat 4

They pick Chain.

The two thruster commits, faded and dashed: in Git, but no name leads to them.

### Beat 5

They type `git branch thrusters HEAD@{1}`.

The two commits turn solid, with `thrusters` on the newer one.

```
project $ git branch thrusters HEAD@{1}
```

### Beat 6

They type `git log --oneline --graph --all`.

thrusters is back, two commits above main.

```
project $ git log --oneline --graph --all
* fd1588f (thrusters) Test the right thruster
* f4b87c0 Test the left thruster
* 44c16d0 (HEAD -> main, origin/main) Add the crew list
* a38b821 Plot the route
* b9e397c Start the project
```

## Design notes

Something lost opens on the move log, empty: the answer is not given before the player looks. `git log --all` does not show the lost commits; `git reflog` does, and fills the move log with exactly its lines. From then on the move log updates by itself, and says so once. The move log is one picture: the chain is on its own tab, where the no-name commits now show, faded and dashed.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
