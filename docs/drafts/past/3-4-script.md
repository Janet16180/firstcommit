# 3-4 Look into the past

Mission. Command: `git show <commit>:<file>`.

## Briefing

Tonight the fuel gauge reads 40%. The captain wants to know what it read after the Phobos stop, a few days ago. Nobody wrote it down, but the vault keeps every commit.

## Goals

1. Find the commits that changed the fuel log: `git log fuel.txt`.
2. Predict first.
3. Look at the Phobos commit: `git show <hash>`.
4. Read the fuel log as it was then: `git show <hash>:fuel.txt`.
5. Answer the captain.

## Beats

### Beat 1: scene

**Rama:** The gauge says 40% tonight. The question is about a few days ago. Every commit in the vault keeps every file as it was when the commit was made, so the answer is in there.

### Beat 2: type

The player types:

```
$ git log fuel.txt
commit 3d36fa9f9a1453f35bc7a48e98ce42349fa5c7a3 (HEAD -> main)
Author: Sam Ortiz <sam@example.com>
Date:   Mon Apr 6 21:30:00 2026 +0000

    Log the fuel tonight

commit ccf94851a5a48045b27ccbc2005bd27b840515f7
Author: Cadet <cadet@example.com>
Date:   Sun Apr 5 21:30:00 2026 +0000

    Log the fuel after Phobos

commit 91139328d68bfa890a0bba006b31f3f9dde4a7d7
Author: Robin Park <robin@example.com>
Date:   Fri Apr 3 21:30:00 2026 +0000

    Log the fuel after the Moon

commit f0a3d683cab5fe8f80ea269d9f21b01392b7014a
Author: Robin Park <robin@example.com>
Date:   Wed Apr 1 21:30:00 2026 +0000

    Set up the base
```

**Rama:** `git log fuel.txt` skips the commits that did not touch `fuel.txt`: four of the six are left, newest first. The second is the Phobos stop. Copy the first 7 characters of its hash, the long code after `commit`: `ccf9485`.

**Designer note (what the picture does):** The two commits that did not touch fuel.txt are dimmed on the chain. The Phobos capsule is ringed, and the terminal shows and lights its five lines.

### Beat 3: predict

**Prediction:** You type `git show` and the Phobos commit's hash. What does it print?

- `fuel.txt` as it was then
- What that commit changed
- Every file in the project

Reveal: What that commit changed: its message, then the change itself, where a `-` line is what was taken out and a `+` line what was put in. To read a whole file as it was, the next step adds the file's name.

### Beat 4: type

The player types:

```
$ git show ccf9485
commit ccf94851a5a48045b27ccbc2005bd27b840515f7
Author: Cadet <cadet@example.com>
Date:   Sun Apr 5 21:30:00 2026 +0000

    Log the fuel after Phobos

diff --git a/fuel.txt b/fuel.txt
index 91a9891..3ffe04c 100644
--- a/fuel.txt
+++ b/fuel.txt
@@ -1 +1 @@
-fuel: 75%
+fuel: 60%
```

**Rama:** The change: `-` took out `75%`, `+` put in `60%`; the lines above them only say which file. That answers tonight's question, but only because the file is one line. For a whole file as it was, put a colon and the file's name after the hash.

### Beat 5: type

The player types:

```
$ git show ccf9485:fuel.txt
fuel: 60%
```

**Rama:** The fuel log exactly as the Phobos commit recorded it. Your folder still says 40%: reading the past changes nothing.

**Designer note (what the picture does):** The panel beside the chain fills with what git printed, titled with the ringed commit.

### Beat 6: say

**Rama:** Answer the captain: what did the gauge read after Phobos? Type it in the answer box.

### Beat 7: done

**Debrief:**

Every commit keeps every file exactly as it was. `git log fuel.txt` found the commits that changed the file, and `git show <hash>:fuel.txt` printed it as one of them recorded it, while your folder stayed as it was. The past is all still there.

In Time travel you will also bring an old version back into your folder.

Commands to keep:

```
$ git log fuel.txt              # the commits that changed one file
$ git show <hash>               # what a commit changed
$ git show <hash>:fuel.txt      # the file as that commit recorded it
```

## Losses


## Rama's reactions

- `git show <hash> fuel.txt` (a space, not a colon): "With a space, git shows what that commit changed in `fuel.txt`. With a colon, the file itself as it was."
- A wrong answer: "That is what the gauge read at another stop. Find the commit whose message names Phobos."

## Design notes (after playing)

**The one idea:** Every commit keeps every file exactly as it was. `git log <file>` finds the commits that changed it; `git show <commit>:<file>` prints the file as that commit recorded it. Reading the past changes nothing.

**On screen:** The vault's commits (the station's vault zone in sector 3; drawn here as a straight chain), the commit the player looks at ringed, and beside it one panel: the file as it was then.

**Hidden on purpose:** HEAD~n (taught in sector 8), `git restore --source` (mentioned in the debrief as coming in Time travel), the mothership.

## Hints and solution (the last hint gives every line)

1. `git log fuel.txt` lists only the commits that changed `fuel.txt`. The Phobos one says so in its message.
2. Put the commit's hash, a colon and the file's name together: `git show <hash>:fuel.txt`. The first 7 characters of the hash are enough.
3. Every line of the mission, in order:
   
       $ git log fuel.txt
       $ git show ccf9485
       $ git show ccf9485:fuel.txt
   
   Then answer: 60%.

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
