# 7-4 Merge tools

Mission, guided. Command: `git mergetool`. Sector 7, Collisions: after 7-3 Collision. Docking
collision, the boss, becomes 7-5. Main view: Two sides (V5); the merge panel opens over it while
the tool runs.

Every line of terminal output below comes from real git 2.43 runs
(`recorder/record.py`, outputs in `recorder/out/`). The lines starting "Waiting for the merge
panel" and "To stop without changing the file" are printed by the game's tool, not by git.

## The lab

`launch.txt` on `main`, as the three commits leave it:

- *Write the launch plan* (you, June 1): window 06:00, cargo water and fuel cells.
- On `scout`, *The window closes early: launch at 05:30, and pack a spare antenna* (Alex, June 2).
- On `main`, *Launch at 07:00 and pack oxygen* (you, June 3).

The merge stops with two conflicts in one file: the launch window, and the last cargo line.

## Scene

1. (collision) Two crews changed the launch plan, and it cracked in two places.
2. (collision) You know the terminal way. Today Git opens a tool for you: one click per conflict.

## Briefing

You moved the launch to 07:00 and packed oxygen, on `main`. Alex, on `scout`, moved it to 05:30
and packed a spare antenna: the launch window closes early. Bring `scout` into `main`, and answer
both conflicts with a merge tool: Alex's launch time, and both cargo lines.

The mission is done when `main`'s last commit holds `scout`'s work, launches at 05:30 and packs
both the oxygen and the spare antenna, with no conflict markers.

## Quest steps

1. **Bring `scout` into `main`.** Command: `git merge --no-edit scout`.
   Done: "The merge stopped: `launch.txt` has two conflicts."
2. **Open the merge tool, and answer each conflict.** Command: `git mergetool`.
   Text: In the panel, keep Alex's launch time and both cargo lines, then press Write.
   Done: "`launch.txt` launches at 05:30 and packs both, with no markers."
3. **See what the tool did.** Command: `git status`.
   Done: "`launch.txt` is in the staging area (the cargo dock): the tool added it for you."
4. **Finish the merge.** Command: `git commit --no-edit`.
   Done: "`main`'s last commit holds `scout`'s work, launches at 05:30 and packs both."

## Rama on the way

- When the tool starts waiting: "Git opened the game's merge tool: the panel. Your terminal waits
  until you press Write."
- The first time a player sees `git mergetool`'s `{local}` and `{remote}` lines (once per player,
  in any level): "In git's words, local is yours and remote is Alex's."
- When the tool has finished: "The tool wrote `launch.txt`, and Git added it to the staging area
  (the cargo dock). No `git add` this time."

## Rama on the expected mistakes

| The player | What happens | Rama |
|---|---|---|
| runs `git mergetool` before the merge | `No files need merging` | Nothing to answer yet: Git opens a merge tool only for files in conflict. Start the merge first: `git merge --no-edit scout`. |
| presses Cancel in the panel, or Ctrl-C | `merge of launch.txt failed` | You stopped the tool, so Git put `launch.txt` back as it was, markers and all. Nothing is lost. Run `git mergetool` again when you are ready. |
| keeps Yours for the window | `launch.txt` staged with 07:00 | `launch.txt` launches at 07:00, after the window closes. To answer again: `git merge --abort`, then `git merge --no-edit scout` and `git mergetool`. |
| keeps one side for the cargo | one cargo line staged | Only one cargo line made it into `launch.txt`; the trip needs both. To answer again: `git merge --abort`, then `git merge --no-edit scout` and `git mergetool`. |
| types `git restore --theirs launch.txt` (7-3's way) | Alex's whole file: 05:30, but the oxygen is gone | That keeps Alex's side of the whole file, so your oxygen line went too. Here each conflict needs its own answer: `git mergetool`. |
| types `git add launch.txt` after the tool | nothing printed | The tool already added `launch.txt`. Adding it again changes nothing. |
| types `git commit --no-edit` before answering | git refuses | Git cannot commit while a file is in conflict. Answer it first: `git mergetool`. |
| types `git mergetool --tool=<name>` | git opens that program instead of the panel; for `vimdiff`, vim with no key strip | `--tool` picks another program for this one run. In the game, plain `git mergetool` opens the panel. |
| closes the tab, or loses the connection, while the tool waits | the tool and git end; the file keeps its markers; the merge stays paused | Your terminal restarted, so the merge tool stopped. `launch.txt` is as it was: run `git mergetool` again. |
| commits a wrong answer | `main` holds it | `main`'s last commit does not launch at 05:30 with both cargo lines. Leave the mission and start it again, and pick Alex's time and Both. |

## Hints

1. `git merge --no-edit scout` stops with two conflicts in `launch.txt`. Then `git mergetool`
   opens the game's merge panel.
2. In the panel, keep Alex's launch window and Both cargo lines, then press Write. The tool adds
   `launch.txt` itself, so the next line is `git commit --no-edit`.
3. Every line of the mission, in order. In the panel, pick Alex's, then Both, then press Write:

```
$ git merge --no-edit scout
$ git mergetool
$ git status
$ git commit --no-edit
```

## The panel's footer

One line under Write, the only place besides the debrief that says how real tools differ:
"A training tool, one click per conflict. Real merge tools show more; the debrief says how."

## Command card

`git mergetool`: opens the merge tool that `merge.tool` names on each file in conflict, one after
the other. When the tool reports success, Git adds the file to the staging area. In the game it
opens the game's own panel.

## Debrief

`git mergetool` opened a merge tool on the file in conflict: here, the game's panel. You answered
each conflict on its own, Write saved the file, and when the tool finished, Git added
`launch.txt` to the staging area itself. `git commit --no-edit` finished the merge, as in 7-3.
`git restore --theirs` could not have done it: it keeps one side for the whole file.

Real tools differ. The panel is a training tool: one click per conflict, made to learn with. At
work, people answer conflicts in their editor's merge view or in a merge tool. In VS Code you
usually open its merge editor from the conflicted file or from the Source Control view; it can
also be set as git's merge tool. A tool such
as Meld is what `git mergetool` opens once you set your own: `git config merge.tool meld`. Real
tools show more of the file and let you write an answer line by line, for when neither side alone
is right.

The game also hides two things git does on its own. It keeps the file as it was, markers and
all, as `launch.txt.orig` after each answer, until you delete it. And when no tool is set, it
picks one it finds and asks "Hit return to start merge resolution tool" before opening it.

The terminal way from 7-3 works everywhere, with or without a tool, and so does
`git merge --abort`.

Commands to keep:

```
$ git mergetool   # open the merge tool on each file in conflict; it adds each answer
```
