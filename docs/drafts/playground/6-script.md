# Playground 6: Conflict: in nano

Starting point: **Conflict**. The same conflict, resolved in nano, with the save-and-quit strip above the terminal and the panel waiting.

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

The playground opens on Conflict, on the Conflict tab.

Under the panel, the editor way: two chips, `nano checklist.txt` and `vim checklist.txt`.

### Beat 2

They type `git status`.

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

They click the `nano checklist.txt` chip and press Enter.

nano fills the terminal. A gold strip above it: Save: Ctrl+O, then Enter. Quit: Ctrl+X. And Get me out. The panel greys out: checklist.txt is open in nano.

### Beat 4

They delete the three marker lines and both course lines, and type one of their own.

`4. Course: the Moon, then Jupiter`. nano marks the file modified.

### Beat 5

They press Ctrl+O, as the strip says.

nano asks for the file name, already filled in.

### Beat 6

They press Enter.

Wrote 10 lines.

### Beat 7

They press Ctrl+X.

The prompt is back and the strip is gone. The panel read the file again and shows it as it is now: the one course line they wrote, no markers. Next: `git add`, then `git commit`.

### Beat 8

They type `git add checklist.txt`.

```
project $ git add checklist.txt
```

### Beat 9

They type `git commit` and pick Chain.

The merge commit, with its two parents.

```
project $ git commit
[main 360bf71] Merge branch 'main' of ../github.com/moonbase/project
```

## Design notes

While an editor runs in a terminal, a strip above that terminal says how to save and how to quit, in that editor's keys. The shell's startup wraps nano, vim and vi so they set the terminal's title while they run; the page sees the title and shows the strip, and hides it when the prompt is back. While the editor has the file, the click-to-keep panel is greyed and says it waits; when the file changes it reads it again. Get me out, in red, asks first, then types the editor's quit-without-saving keys. The strip never mentions Ctrl+W (nano's search), which the browser takes to close the tab.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
