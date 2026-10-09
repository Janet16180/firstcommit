# Playground 7: Conflict: vim, and Get me out

Starting point: **Conflict**. Stuck in vim, Get me out with its confirmation; then vim done right, the panel waiting and refreshing; and the rare refused Write.

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

### Beat 2

They type `cat checklist.txt`.

The markers, as Git wrote them, in the terminal.

```
project $ cat checklist.txt
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

### Beat 3

They type `vim checklist.txt`.

vim fills the terminal. The strip: Save and quit: Esc, then :wq Enter. On a wide screen also: Type: press i. Leave typing mode: Esc. Quit without saving: Esc, then :q! Enter. On a phone those sit behind "more keys".

### Beat 4

On a phone, they tap more keys.

The other three keys appear.

### Beat 5

They type a few letters, then `:q`, and vim refuses.

vim's own error at the bottom. The player is stuck.

### Beat 6

They press Get me out.

It asks first: Quit vim without saving? Your changes to checklist.txt are lost. Quit without saving, or Keep editing.

### Beat 7

They press Quit without saving.

The page types Esc, `:q!` and Enter into the terminal for them.

### Beat 8

vim quits without saving.

The prompt is back, the strip is gone, and the panel is live again: checklist.txt is as Git wrote it.

### Beat 9

They type `git status`.

Still unmerged: nothing changed.

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

### Beat 10

On the Conflict tab they click Keep: Yours, but do not write yet.

Write is ready.

### Beat 11

Instead they open vim again: `vim checklist.txt`.

The panel greys out, with the editor chips, and the pick is cleared: it was made on text the editor is about to change.

### Beat 12

They press i, delete the markers and Alex's line, then press Esc.

`-- INSERT --` while typing: the strip's Type and Leave typing mode keys.

### Beat 13

They type `:wq` and Enter.

### Beat 14

The prompt is back.

The panel shows checklist.txt as vim saved it: no markers, the Moon course line.

### Beat 15

The rare case, shown once: a Write clicked just as the file changed.

Refused: checklist.txt changed after the panel last read it, so nothing was written and the picks were cleared. Look again is the main button.

*Designer note:* The server's 409. With the panel refreshing on every change this needs a click in the moment between a save and the refresh; it is designed so even that never writes over the editor's work.

### Beat 16

They type `git add checklist.txt`.

```
project $ git add checklist.txt
```

### Beat 17

They type `git commit` and pick Chain.

The merge commit, with its two parents.

```
project $ git commit
[main e4c3ae0] Merge branch 'main' of ../github.com/moonbase/project
```

## Design notes

Nobody gets trapped. The strip shows the one line that matters (save and quit), with the other keys behind "more keys" on a phone. Get me out is red and asks first; it then types Esc, `:q!` and Enter, which leaves without saving from any mode. The panel and the editor work on the same real file: the panel greys while the editor has it, and reads it again when it changes, clearing picks made on the old text. The server still refuses a Write when the file changed after the panel's last read (a 409; rare, shown once at the end): nothing is written, the picks are cleared, and Look again is the main button. vim must be added to the game's image; nano is there already.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
