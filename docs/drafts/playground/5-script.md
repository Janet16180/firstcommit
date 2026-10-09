# Playground 5: Conflict: click to keep

Starting point: **Conflict**. Markers decoded in the playground: choose a side, the page writes the file, the player types git add and git commit.

checklist.txt as the starting point leaves it (real git output):

```
LAUNCH CHECKLIST
1. Seal the hatch
2. Fuel tanks: half
3. Check the radio
<<<<<<< HEAD
4. Course: the Moon
=======
4. Course: Jupiter
>>>>>>> 94b6459f310f9ec74b15d5f70e207bdf95b25026
5. Music: off
6. Shields: on
7. Gloves on
8. Snack: space noodles
9. Wave goodbye to base
```

## Beats

### Beat 1

The playground opens on Conflict, with Alex shown and the Conflict tab picked.

checklist.txt as Git wrote it: one block between markers, your course line and Alex's. One line above says the rest was merged by Git on its own.

### Beat 2

They type `git status`.

Unmerged paths: both modified, checklist.txt.

```
project $ git status
On branch main
Your branch and 'origin/main' have diverged,
and have 1 and 1 different commits each, respectively.
  (use "git pull" if you want to integrate the remote branch with yours)

You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   checklist.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

### Beat 3

They click Keep: Yours.

Alex's course line is struck through and the three marker lines fade. The file is not changed yet: Write is ready.

### Beat 4

They click Write this into checklist.txt.

The panel shows the file as it is now: the Moon course line, no markers. Next: `git add checklist.txt`, then `git commit`. The page never runs git.

### Beat 5

They type `git add checklist.txt`.

Nothing printed: the conflict is marked resolved.

```
project $ git add checklist.txt
```

### Beat 6

They type `git commit` and pick Chain.

The merge commit on top, with two lines down: one to your Moon commit, one to Alex's Jupiter commit.

```
project $ git commit
[main 975bd29] Merge branch 'main' of ../github.com/moonbase/project
```

*Designer note:* `git commit` keeps the merge message Git prepared: no editor opens (the game's core.editor stays `true`).

### Beat 7

They type `git log --oneline --graph`.

Git's drawing of the same diamond.

```
project $ git log --oneline --graph
*   975bd29 (HEAD -> main) Merge branch 'main' of ../github.com/moonbase/project
|\  
| * 94b6459 (origin/main) Head for Jupiter
* | 9b9b67c Head for the Moon
|/  
* 0a8298c Add the launch checklist
* 44c16d0 Add the crew list
* a38b821 Plot the route
* b9e397c Start the project
```

### Beat 8

They type `git push`.

The mothership's pin climbs onto the merge commit.

```
project $ git push
To ../github.com/moonbase/project.git
   94b6459..975bd29  main -> main
```

### Beat 9

Alex's terminal: `git pull`.

Alex fast-forwards to the merge: both stations and the mothership agree.

```
alex: project $ git pull
From ../../github.com/moonbase/project
   94b6459..975bd29  main       -> origin/main
Updating 94b6459..975bd29
Fast-forward
 checklist.txt | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
```

## Design notes

The click-to-keep panel is Markers decoded, with Alex in green. It reads the real file and shows each conflict block with its two sides; one line says the rest was merged by Git on its own, without tagging each line. The marker's long hash is shortened in the panel (the terminal shows it whole). Choosing a side only marks the lines: nothing changes until Write. Write sends the choices to the server, which rewrites only the marker blocks of the real file. The page never runs git: it says what to type next. Under the panel, the editor way is offered as two chips that type `nano checklist.txt` or `vim checklist.txt` at the prompt. A Conflict tab appears while a file has markers, and stays until the merge is committed.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
