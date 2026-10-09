# The playground: ready for your review

> Prepared by designer, 2026-10-08. Drafts only: nothing in the game has changed yet.

## What to open

- `docs/drafts/playground/index.html`: nine flows. Step through each with Next and Back. Try one
  at full width and one on a phone (or a narrow window).
- `plan.md`: the full design and the build split.

Every git output in the flows is real, recorded from the starting points the game would build.
Editor screens are drawn, but what they save is written to the real file.

## What it is

Free play with no goals, stars or coaching:

- A real terminal and a practice repository with the stand-in mothership.
- A view picker: Chain, History, Desk and Crew, with Move log and Graph under "More views".
- Alex's own terminal beside yours when you want it.

## Main choices

- **Alex's terminal is hidden by default.** It opens shown in the two starting points about two
  people (Alex is ahead, Conflict). It is a second shell in Alex's clone, signed Alex by Alex's
  own git settings. Your terminal is violet, Alex's green.
- **Colour never changes owner.** Violet is you and green is Alex, whichever repository is
  drawn. Pink is the mothership.
- **Seven starting points:**
  - Empty folder
  - Uncommitted changes
  - Two branches
  - Alex is ahead
  - Both committed (a merge without conflict)
  - Conflict
  - Something lost

  Each names the chapter it uses ("uses Collisions"), and none is locked. Start over and Other
  start ask first, and never touch missions.
- **On a phone** there is one terminal at a time. The picture folds into one line above it ("Chain
  · Your repository: HEAD on main · main in step with origin/main") and unfolds on a tap.
- **Conflicts can be resolved two ways:**
  - **Click to keep.** This is your favourite, Markers decoded: pick a side, and the page writes
    the real file. You then type `git add` and `git commit` yourself, because the page never runs
    git.
  - **In nano or vim.** A strip above the terminal shows the editor's save and quit keys. A red
    "Get me out" button asks first, then quits without saving. The click panel waits while the
    editor has the file, and shows the result after it saves.
- **The move log stays empty until you type `git reflog`,** as in the missions. After that it
  updates by itself, and says so once.
- **How you get there:** a Playground landmark on the map, open from the start; the dev page; and
  "Try it in the playground" on each field guide card. That last one gives a chip that types the
  card's command at your prompt. Opening the playground from a mission leaves the mission as it
  was.

## Reviews so far

| Round | Result |
|---|---|
| 1 | Would use it, "for trying a command before running it on real work, and conflict practice". Alex joins was the best learning flow; click to keep was "the clearest conflict screen I've seen". |
| 2 | 6 clear, 3 mostly clear, none confusing |

Fixed after round 2 (not reviewed again):

- Clearer ownership: your terminal is now violet, and the folded line on a phone says whose
  repository it describes.
- One terminal switch on a phone instead of two.
- The picture starts folded on a phone.
- History is one column on a phone.
- The conflict panel shows the resulting file, and drops picks as soon as an editor opens.
- Starting points: "A few commits" was dropped, because "Two branches" covers it, and "Both
  committed" was added.

## Decisions for you

1. Approve the playground as designed, or say what to change.
2. The game's own History view has the same problem the review found here: two branches off one
   commit look like one straight line. I recommend drawing its branches as side lines, as Chain
   does (details in `plan.md`, "The game's history view"). Yes or no?
3. One change to termlab is needed: serving a second terminal. You have already allowed termlab
   changes; this is a reminder.
