# 7-4 Merge tools: the technical plan

> Draft by conflicts, 2026-10-08, revised the same day after a review. Design only: no game code
> changed. The script is `script.md`, the storyboard `storyboard.html`. Every git line below comes
> from real git 2.43 runs in a temporary HOME (`recorder/record.py`, outputs in
> `recorder/out/<scene>.txt`), with a prototype of the game's tool (`recorder/tool.py`) that reads
> the file with the game's own `firstcommit.markers`, and a Write played the way this plan
> proposes (a temporary file, then `os.replace`).

## The idea in one paragraph

The game registers its own merge tool, `firstcommit`, in the game's git configuration. When the
player types `git mergetool`, git runs that tool on each file in conflict. The tool tells the page
through the terminal title (as the editor wrappers do), and waits. The page shows the existing
click-to-keep panel, in every level screen and in the playground, over whatever view is open.
Write sends the picks to the server, which rewrites the marker blocks of the real file in one
atomic step. The tool sees no markers left and exits 0; git then adds the file itself. Cancel
types Ctrl-C into the terminal; the tool exits 1, and git puts the file back as it was. The page
never runs git, and git never knows the page exists: it only ran a program and read its exit
status.

## 1. Registering the tool

Six settings, as `GIT_CONFIG_COUNT` entries next to `PLAYER_SETTINGS` (`gitcmd.isolation`), so
they reach every shell the game starts (the level terminal, the playground's two, `firstcommit
shell`) and every game home, old ones too, and outrank whatever the player sets with
`git config --global`:

| Setting | Value | Why (git-mergetool(1), `/usr/lib/git-core/git-mergetool`) |
|---|---|---|
| `merge.tool` | `firstcommit` | the tool plain `git mergetool` runs |
| `mergetool.firstcommit.cmd` | `'<sys.executable>' -m firstcommit mergetool "$MERGED"` | a custom tool; git evaluates it in `sh` with `$MERGED` set to the file's path from the top of the repository |
| `mergetool.firstcommit.trustExitCode` | `true` | without it git ignores the exit status, checks only whether the file's time changed, and may ask "Was the merge successful [y/n]?" (`check_unchanged` in git-mergetool--lib) |
| `mergetool.keepBackup` | `false` | git's default leaves `launch.txt.orig`, an untracked file a beginner did not make (scene 7: `?? launch.txt.orig`) |
| `mergetool.writeToTemp` | `true` | git's default writes `launch_BACKUP_<pid>.txt`, `_BASE_`, `_LOCAL_` and `_REMOTE_` into the working folder while the tool runs (scenes 7, 17); with `true` they go to a folder under `$TMPDIR` |
| `mergetool.prompt` | `false` | no "Hit return to start merge resolution tool" question; git asks it when `prompt` is true or when it guessed the tool because none is set (scene 17), so this guards a player's own setting |

**The temporary folder.** The game's shells set `TMPDIR` to `<game home>/tmp`. git-mergetool
makes `git-mergetool-XXXXXX/` there and removes it when it ends normally; a run killed half-way
(a closed terminal, scene 18) leaves it behind. Every lab reset removes the leftovers: starting or
retrying a level, Start over and Other start in the playground, and `firstcommit reset` all delete
`<game home>/tmp/git-mergetool-*` (only those, so nothing else the player keeps in `TMPDIR` is
touched). One function in `save.py`, called by each of those.

**AUTHORING 3.2** forbids configuration that runs programs. It gains one narrow exception, worded
as: "The game's own merge tool, `firstcommit`, set only in the game's environment
(`GIT_CONFIG_COUNT`), never in a lab's `.git/config` or in any file of a lab." Labs never get it,
and a new `gitcmd` test says so (section 8).

Where the code goes:

- `firstcommit/mergetool.py` (core, testable with plain files): `wait(path, keys) -> int`, the
  loop below, and the exit statuses. It uses `markers.parts` to know whether a block is left.
- `cli.py`: a `mergetool <file>` subcommand that sets the terminal up, calls `mergetool.wait` and
  returns its status. Not listed in `--help` (it is git's to call).
- `gitcmd.py`: `MERGETOOL_SETTINGS` and `TMPDIR`.
- `markers.py` or a small `files.py`: the one atomic write (section 6), shared by the
  playground's and the level's Write.
- `web`: the level route for Write, the panel on every screen, Cancel.

## 2. What the tool does

```
git mergetool
  -> sh evaluates: '<python>' -m firstcommit mergetool "launch.txt"
       file already without markers?   print "launch.txt has no conflict markers left: Git stages it as it is."  exit 0
       set the title  "firstcommit-mergetool launch.txt", and send it again every 2 s while waiting
       print two lines (below)
       terminal: no echo, no line editing, Ctrl-C is a key, not a signal
       every 0.2 s:  no block left                 -> exit 0
                     Ctrl-C read on the terminal   -> exit 1
                     the file is gone or no longer a plain file -> print "launch.txt is gone from the working folder."  exit 1
       on exit: restore the terminal, discard keys typed meanwhile, clear the title
       on a hang-up (the terminal closed): ends at once, as git does
  <- exit 0: git adds launch.txt (no output)
  <- exit 1: git prints "merge of launch.txt failed", puts the file back from its backup, exits 1
```

The two lines it prints (scene 1):

```
Waiting for the merge panel: pick a side for each conflict in launch.txt, then Write.
To stop without changing the file: Cancel in the panel, or Ctrl-C here.
```

**Why Ctrl-C is a key, not a signal.** Recorded in scene 11 with a tool that does not handle it:
Ctrl-C kills git-mergetool itself (exit 130), with no message, and leaves the four temporary
copies in `$TMPDIR/git-mergetool-XXXXXX/`. With the terminal in no-signal mode, the tool reads
Ctrl-C as a byte and exits 1; git then prints `merge of launch.txt failed`, restores the file and
cleans up (scene 3). The page's Cancel button types the same Ctrl-C into the terminal, so there is
one way to cancel and no new endpoint.

**Keys typed while it waits.** With echo off they do not show, and the tool discards them on exit
(`TCSAFLUSH`): scene 9 typed `ls -l` and Enter during the wait, and nothing ran afterwards.

**Without a terminal** (the tests, `kit.type_line`): the tool does not touch the terminal or set
the title, and waits for the file only.

**Exit statuses git understands:** 0 resolved (git adds the file), 1 not resolved (git restores
the file). Only these two.

## 3. The signal to the page, and when it ends

The title is the only signal, on the same channel as the editor wrappers
(`commands.EDITOR_TITLE`), read through xterm.js `onTitleChange`: `firstcommit-mergetool <path>`
while the tool waits, empty when it ends (scene 1's notes list both). Control characters are
dropped from the path, as the wrapper does.

The panel never stays open on its own:

- **It expires.** The tool sends the title again every 2 s. The page keeps a "waiting since"
  time per terminal and treats the tool as gone when no title has come for 5 s, so a tool killed
  without clearing its title (scene 11, scene 18) closes the panel within 5 s.
- **It closes with the terminal.** When the page's terminal connection closes, the page drops
  the panel at once. On the server, termlab closing the pty sends a hang-up to the shell's
  processes; the tool and git-mergetool end with it (scene 18: the file keeps its markers,
  `UU launch.txt`, the merge stays paused, and the temporary folder is left for the next reset).
  The terminal's close is the server's word that no tool waits any more; a new terminal starts
  with no panel.
- **It ends with the tool.** An empty title closes it, after the page shows the written file for
  a moment ("Written from your picks").

So no state can leave a player looking at a panel with no tool behind it, or at a waiting
terminal with no panel: the terminal always shows its two lines, and Ctrl-C there always works.

## 4. What `git mergetool` prints, and the merge after it

The mission's path (scene 1, exact):

```
project $ git merge --no-edit scout
Auto-merging launch.txt
CONFLICT (content): Merge conflict in launch.txt
Automatic merge failed; fix conflicts and then commit the result.
project $ git mergetool
Merging:
launch.txt

Normal merge conflict for 'launch.txt':
  {local}: modified file
  {remote}: modified file
Waiting for the merge panel: pick a side for each conflict in launch.txt, then Write.
To stop without changing the file: Cancel in the panel, or Ctrl-C here.
project $ git status
On branch main
All conflicts fixed but you are still merging.
  (use "git commit" to conclude merge)

Changes to be committed:
	modified:   launch.txt

project $ git commit --no-edit
[main 8642822] Merge branch 'scout'
```

- `git mergetool` adds each file whose tool succeeded (`git add -- "$MERGED"` in
  git-mergetool's `merge_file`), so the mission says plainly: no `git add` this time, and step 3's
  `git status` shows it.
- `git commit --no-edit` then finishes the merge, as in 7-3.
- `{local}` and `{remote}` are git's words for the two sides. Rama says once, the first time a
  player sees them in any level: "In git's words, local is yours and remote is Alex's." Kept in
  the save like the other once-only lines. During a rebase the two swap, but no level opens the
  tool during a rebase before sector 9; the line is merge-only (it fires on `git mergetool` while
  the operation in progress is a merge).

## 5. The edge cases

| Case | What happens (scene) | What the game does |
|---|---|---|
| Cancel in the panel, or Ctrl-C in the terminal | tool exits 1; `merge of launch.txt failed`; file back as before the tool; status 1; the merge is still paused (3) | Rama's line says nothing is lost; run it again (14: the second run works) |
| The player moves to another view without writing | the tool keeps waiting | the panel stays over every view while the title is fresh, so it is there whichever view the player picks |
| The tab closes, the page reloads, the connection drops | hang-up: the tool and git end; the file keeps its markers (18) | the panel closes with the terminal (section 3); Rama on the next terminal: run `git mergetool` again |
| A tool killed without clearing its title | the title stays as it was | the 5 s expiry closes the panel |
| `git mergetool` with no merge going on | `No files need merging`, status 0; no tool, no panel (2) | Rama: start the merge first |
| `git mergetool` after the commit | `No files need merging` (4) | nothing to say |
| `git add launch.txt` with the markers still in, then `git mergetool` | `No files need merging`: git sees no unmerged path (5) | 7-3's message about markers in the staging area |
| The file cleaned by hand (nano, vim) before `git mergetool`, not added | git still runs the tool; it prints "launch.txt has no conflict markers left: Git stages it as it is." and exits 0; git adds it (6) | step 2 then reads the content like any other route |
| One block answered by hand, one left | the panel shows the one left; Write finishes it (10) | none needed |
| The file edited in the terminal meanwhile | not possible in the same terminal: the tool holds it, and keys are dropped (9). An edit from elsewhere that removes the markers counts as an answer; one that keeps them changes the file's hash, and Write answers 409 as in the playground | the panel's existing "Look again" |
| The file deleted while the tool waits | tool exits 1; git restores it from its backup; `UU launch.txt` (13) | none needed |
| Wrong picks | the tool succeeds, git adds the wrong text (16) | step 2's message: `git merge --abort`, then merge and `git mergetool` again; 16 shows abort works after the tool added the file |
| `git mergetool --tool=vimdiff` (or `-t`) | git runs that tool instead; vimdiff is valid once vim is in the image (`git mergetool --tool-help`), and git starts vim directly, so the editor wrapper's title and strip do not appear | Rama's line afterwards (recommended); see "For the user" |
| Two files in conflict | git runs the tool on each in turn; after a cancel it asks "Continue merging other unresolved paths [y/n]?" | not in this mission (one file); the panel lists the file the title names |
| Alex's terminal in the playground runs `git mergetool` | the same tool in Alex's clone | the panel opens over the playground's picture for Alex's repository (person `alex`), from Alex's terminal's title |

## 6. The page and the server

**Everywhere the tool is registered.** The setting reaches every shell the game starts, so the
panel is part of the shared terminal component, not of this level:

- **Level screens**, every level: the panel opens as an overlay over the level's picture area,
  whatever the main view (station, crew, history, sides, black box), and closes as in section 3.
  Write goes to the level route below.
- **Playground**: each terminal (yours, Alex's) carries its own title state; the panel opens for
  that person's repository, and Write goes to the existing `POST /api/playground/resolve` with
  that `person`. The playground's own Conflict tab stays as it is.
- The panel is `keep-panel.js` with a `tool` mode: a gold bar "Merge tool `firstcommit`", Cancel
  next to Write, no nano and vim chips (the terminal is busy), and one footer line, the panel's
  only word on real tools: "A training tool, one click per conflict. Real merge tools show more;
  the debrief says how."
- **Cancel** types `\x03` into the terminal the title came from, as Get me out types the editor's
  keys.

**Observation.** The level's `Observation` gains `marked` (as `PlaygroundObservation` has), built
by the same function (`markers.marked` on each conflict).

**Write, one rule in one place.** `POST /api/resolve {file, read, choices}` acts on the active
level's lab; `POST /api/playground/resolve` keeps its body. Both call one function that holds the
checks of today's `game.resolve_playground` (the path is one of the repository's files in
conflict, a plain file inside the clone, its bytes hash to `read`, one choice per block) and then
writes atomically:

1. `markers.resolve` builds the new bytes.
2. They go to a new temporary file in the same folder (`.launch.txt.<random>`, created with
   `O_EXCL`), with the original file's permission bits, flushed and `fsync`ed.
3. `os.replace(temporary, path)` swaps it in: on the same file system this is one rename, so the
   tool's polling and the page's snapshot see either the old file or the new one, never half of
   it. A symlink at `path` is replaced, not followed (the check already refuses one).
4. On any failure the temporary file is removed and nothing changes.

The temporary file can show for an instant as untracked in a snapshot; its leading dot and the
rename's speed make that unlikely, and the page already ignores a file that comes and goes between
two polls. The recorder plays Write this way (`atomic_write` in `recorder/record.py`).

## 7. The level

`src/firstcommit/levels/conflict_mergetool.py` (id `conflict-mergetool`), with `_es.py` later.

- `TITLE = "Merge tools"`, `DIFFICULTY = 2`, `XP = 180`, `COMMAND = "git mergetool"`, `PAR = 4`,
  `VIEW = "sides"`, `CARD` as in the script, `SCENE` two frames on the existing `collision` art.
- **Setup**, like 7-3's: `launch.txt` committed by you on June 1; `scout` with Alex's commit on
  June 2; `main` with yours on June 3. Fixed dates give the hashes recorded here (`9e75f0a`,
  `c95b381`, `3bd2b29`). Two conflicts, five unchanged lines apart (with three between, git
  joined the two into one block in a first try).
- **Goals** (watch steps, in order, each passing once later ones do, as 7-3's):
  1. `merge`: a merge of `scout` paused, or finished into `main`.
  2. `answer`: `launch.txt` is no longer in conflict and its staged version launches at 05:30
     with both cargo lines, in either order, no markers. Messages for 07:00, for one cargo line,
     and for markers.
  3. `status`: typed `git status` after step 2 passed (looking is the lesson: the tool added the
     file).
  4. `commit`: `main`'s last commit has `scout` in its history and that content.
  `check` returns the last goal, so every safe route to the end state passes.
- **Reactions** (module constants): the table in `script.md`, plus the once-only local and
  remote line (section 4), which is shared, not the level's.
- **Taught before tested.** Typed before this mission: `git merge --no-edit` (7-1),
  `git merge --abort` (7-2), `cat`, `git restore --theirs`, `git add`, `git commit --no-edit`
  (7-3), `git status` (1-1). New here: `git mergetool` only. `git config merge.tool meld` appears
  once, in the debrief, as something to do at work. The panel itself is the playground's.
- **Renumbering.** `chapters.PLAY_ORDER` gets `conflict-mergetool` between
  `conflict-collision` and `conflict-docking`; the map numbers from that order, so Docking
  collision shows as 7-5 with no change to its module. Also: `tests/test_levels.py`'s view table
  (`"conflict-mergetool": "sides"`), `docs/verification/orbit.md` (new section; the 6-4 heading of
  Docking collision is already stale), `chapters-5-9.md`'s sector 7 row, and the "what a player
  knows" tables in `docs/drafts/sector8/player-knows.md`. 7-3 and 7-5 keep the terminal way; a
  player who types `git mergetool` there gets the panel too, and their checks read end states, so
  it passes.

## 8. Tests (with the change, red first)

- `tests/test_mergetool.py`: the loop on plain files: exit 0 when the blocks go, 1 on a Ctrl-C
  byte, 1 when the file is removed, 0 at once for a file without markers; no title without a
  terminal; the title sent again after 2 s.
- The shared write: the result is the resolved bytes with the original mode; a reader polling in
  a loop during many writes never sees a mix of old and new bytes; nothing is left beside the file
  after a write or after a refused one; 409 and 400 as today. The playground's route tests keep
  passing unchanged.
- An integration test that runs real `git mergetool` in a lab with the game's environment, plays
  Write through the shared function, and asserts the file is added and `.orig` and the temporary
  files are absent; one that sends Ctrl-C through a pty and asserts `merge of launch.txt failed`
  and the restored file; one that closes the pty mid-wait and asserts the file keeps its markers.
- The reset: after a hang-up, starting the level again leaves no `git-mergetool-*` in the game
  home's `tmp`.
- The page (node tests): the panel opens on the title in a level screen and in the playground
  (both terminals), closes on an empty title, on 5 s without a resend, and on the terminal's
  close; Cancel sends `\x03` to the right terminal.
- The level harness: the last hint holds `git mergetool`, which waits for a click. The level
  declares `PICKS = {"launch.txt": ("theirs", "both")}` (read only in dev mode and tests, like
  `QUEST_ACTIONS`); the harness types `git mergetool` and, once the tool's first line appears,
  writes the picks through the shared function.
- `gitcmd` tests: the six settings and `TMPDIR` reach every shell; `git config merge.tool` prints
  `firstcommit` even after `git config --global merge.tool meld`; no lab's `.git/config` holds a
  `mergetool.` setting.

## 9. Claims to fact-check before players see them

- "`git mergetool` adds the file when the tool succeeds": git-mergetool `merge_file`; scene 1.
- "git keeps the file as `launch.txt.orig` after each answer": git-mergetool(1),
  `mergetool.keepBackup` "Defaults to true"; scene 7.
- "when no tool is set, it picks one it finds and asks 'Hit return to start merge resolution
  tool'": scene 17 (git 2.43 found vimdiff here).
- "Meld is what `git mergetool` opens once you set `git config merge.tool meld`": `meld` is in
  `git mergetool --tool-help` (git 2.43, "requires a graphical session").
- "In VS Code you usually open its merge editor from the conflicted file or from the Source
  Control view; it can also be set as git's merge tool": checked by the lead against
  https://code.visualstudio.com/docs/sourcecontrol/merge-conflicts ("Resolve in Merge Editor" on
  a conflicted file, "Open in Merge Editor" on a file under Merge Changes in Source Control;
  Complete Merge stages the file, as the game's tool does; VS Code can be set as git's merge
  tool and then opens through `git mergetool`).
- "`git restore --theirs` keeps one side for the whole file": scene 15 (the oxygen line goes).

## For the user

What I propose:

- The game registers `firstcommit` as `merge.tool` with five more settings (`trustExitCode`, no
  `.orig` backups, temporary copies outside the working folder, no prompt), set the way the game
  already sets `core.editor`, in every shell it starts. The temporary folder lives in the game home
  and every lab reset empties it of mergetool leftovers.
- The tool tells the page through the terminal title, sent again every 2 s; the page opens the
  panel in every level screen and in the playground, and closes it when the title clears, after
  5 s without a resend, or when the terminal closes. Write ends the tool with success and git adds
  the file; Cancel types Ctrl-C, which the tool takes as a key, so git restores the file. All of it
  was run for real (`recorder/out/`).
- Write is atomic (a temporary file beside the real one, then `os.replace`), in one function the
  playground's Write and the level's share.
- The mission: four steps (merge, `git mergetool` with two picks, `git status`,
  `git commit --no-edit`), PAR 4, one file with two conflicts that need different answers
  (Alex's, then Both), so `git restore --theirs` cannot solve it. "Real tools differ" is said
  twice: one footer line in the panel, and the full version in the debrief, which also names what
  the game hides (git's `.orig` backups and its "Hit return" question) and that in VS Code the
  merge editor is usually opened from the conflicted file or Source Control, though it can also be
  set as git's merge tool.

Decisions still open (yours to make), with my recommendations:

1. **Must the player use the tool to pass?** Recommended: no. Step 2 reads the answer in the
   staging area, whatever route made it, as every level reads end states; Rama says the tool is
   the point. The other way needs the tool to leave a record for the check.
2. **The panel in 7-3, 7-5 and every other screen.** Recommended: allow it. The setting is in
   every shell, and the panel now opens wherever the tool is registered, so no screen can leave a
   player stuck; 7-3 and 7-5 still teach the terminal way, and their checks read end states.
3. **`git mergetool --tool=vimdiff`** opens vim without the editor strip. Recommended: accept it
   with a Rama line afterwards. (The fuller fix, a `vim` on the shell's PATH that sets the title,
   touches the playground's editor work.)
4. **Step 2, `git config merge.tool`.** Recommended: drop it, as this draft now does (PAR 4);
   `git config merge.tool meld` stays in the debrief only.
5. **One configured program.** Recommended: accept a narrow exception in AUTHORING 3.2: only the
   game's own merge tool, set in the game's environment, never in a lab's `.git/config`.
