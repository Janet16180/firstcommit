# 8-3 Deleting isn't erasing

Mission. Command: `git show HEAD~1:<file>`.

## Briefing

Last night a commit took the airlock keys by mistake, so you removed them in the next commit. Both went up to the mothership, and Alex has pulled. The captain asks: is the airlock password safe?

## Goals

1. Read the history: `git log --oneline`.
2. Predict first.
3. Look for the keys in the newest commit: `git show HEAD:keys.txt`.
4. Look in the commit before it: `git show HEAD~1:keys.txt`.
5. Find every commit that touched the keys: `git log --oneline -- keys.txt`.
6. Answer the captain: the password to change.

## Beats

### Beat 1: scene

**Rama:** Back in the cargo dock you kept a password out of a commit with `git restore --staged`. Last night one got in: `keys.txt`, with the airlock password. You removed it in the next commit and pushed both. Alex has pulled.

### Beat 2: type

The player types:

```
$ git log --oneline
88b2a3d (HEAD -> main, origin/main) Remove the keys
f3a8bc6 Add the airlock keys
44c16d0 Add the crew list
a38b821 Plot the route
b9e397c Start the project
```

**Rama:** Remove the keys on top; Add the airlock keys just below. Both are on the mothership and at Alex's station: look at the pins.

### Beat 3: predict

**Prediction:** `keys.txt` is gone from your folder and from the newest commit. Can anyone with this history still read the password?

- Yes
- No

Reveal: Yes. Removing the file made a new commit without it. The commit before was not changed: it still holds `keys.txt` as it was. Look.

### Beat 4: type

The player types:

```
$ git show HEAD:keys.txt
fatal: path 'keys.txt' does not exist in 'HEAD'
```

**Rama:** Right, as expected: `HEAD` is the newest commit, today's files, and it has no `keys.txt`. That part of the fix worked.

### Beat 5: type

The player types:

```
$ git show HEAD~1:keys.txt
airlock password: orion-7
```

**Rama:** `HEAD~1` means one commit before `HEAD`: here, Add the airlock keys. There is the password, exactly as it was committed.

**Designer note (what the picture does):** The ring moves down one commit; the panel fills with the password.

### Beat 6: say

**Rama:** The mothership has this commit, and so does Alex: see the pins. Anyone who clones the project later gets it too, and can type the same line.

### Beat 7: type

The player types:

```
$ git log --oneline keys.txt
fatal: ambiguous argument 'keys.txt': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
```

**Rama:** A file that is no longer in your folder needs `--` before its name, as git's last line says.

**Designer note (what the picture does):** A real error, met on purpose: it is what a player types first.

### Beat 8: type

The player types:

```
$ git log --oneline -- keys.txt
88b2a3d (HEAD -> main, origin/main) Remove the keys
f3a8bc6 Add the airlock keys
```

**Rama:** Two commits touched `keys.txt`: the one that added it and the one that removed it.

### Beat 9: say

**Rama:** So a later commit cannot remove what an earlier commit recorded. The password reached the mothership: treat it as leaked, and change it. Rewriting history can hide it from future copies, but not from anyone who already pulled it, so you still change the password. That is why, in Stowaway, the keys never went into a commit at all.

### Beat 10: say

**Rama:** The captain will change the airlock password now, and needs to know which one leaked. Type the password to change in the answer box.

### Beat 11: done

**Debrief:**

Removing `keys.txt` made a new commit without it; the commit before still holds the file as it was. `git show HEAD~1:keys.txt` read it, and `git log -- keys.txt` found every commit that touched it. Once a secret is committed and pushed, it is leaked: change the secret. The real fix comes before the commit, as in Stowaway: keep it out of the staging area.

Commands to keep:

```
$ git show HEAD~1:keys.txt            # a file as the commit before HEAD recorded it
$ git log --oneline -- keys.txt       # every commit that touched a file, even a deleted one
```

## Losses


## Rama's reactions

- `git show HEAD~2:keys.txt`: "Two commits back is before the keys were added: that commit has no `keys.txt`. Try one back."
- A wrong answer: "That is not what `keys.txt` held. Read it again with `git show HEAD~1:keys.txt`." The answer is accepted in any case, as `orion-7` or as the whole line `airlock password: orion-7`.

## Design notes (after playing)

**The one idea:** A commit that deletes a file is a new commit without it; the older commit still holds the file as it was. Anyone with the history can read it, so a secret that was committed and pushed is leaked: change it. Payoff of 2-3 Stowaway, where the keys never went into a commit.

**On screen:** The chain with the mothership's and Alex's pins, the commit looked at ringed, and beside it one panel: keys.txt as that commit recorded it, or "not there".

**Hidden on purpose:** Rewriting history (one sentence, not taught), the desk, the move log.

## Hints and solution (the last hint gives every line)

1. `git show HEAD:keys.txt` reads the file in the newest commit; `HEAD~1` is the commit before it.
2. For a file that is no longer in your folder, put `--` before its name: `git log --oneline -- keys.txt`.
3. Every line of the mission, in order:
   
       $ git log --oneline
       $ git show HEAD:keys.txt
       $ git show HEAD~1:keys.txt
       $ git log --oneline -- keys.txt
   
   Then answer: orion-7.

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
