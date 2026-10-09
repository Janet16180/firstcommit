# The playground: the plan

> Draft by designer, round 3, 2026-10-08. The storyboards are in this folder (`index.html`, flows
> `1` to `9`, each with a `-script.md`). Every git output in them is real: the recorder built each
> starting point and typed each line in the person's own clone. Editor screens are drawn; what
> the editor saved was written to the real file, and git read it from there.

## What it is

Free play, with no goals, stars, or Rama coaching. A real terminal, a practice repository with
the stand-in mothership, and a view picker that changes the picture at any time. The player
"just plays and sees how things work". Each starting point prints one suggestion in the
terminal's first line, and that is all the guidance there is.

## The screen

| | 1280 wide | Phone (390) |
|---|---|---|
| Header | Playground, the starting point's name, Start over, Other start; Back to Mission N-M when opened from a card over a level | the same, wrapped |
| Left | the view tabs (Chain, History, Desk, Crew, then Conflict when there is one, and More views: Move log, Graph); "Picture: your repository / Alex's repository" while Alex is shown, for per-person views; one picture | the tabs, then the picture, folded |
| Right | your terminal (violet frame); with Alex shown, Alex's below it (green frame, green prompt `alex: project $`) | ONE terminal; with Alex shown, "Terminal: You / Alex" above it. The picture follows the terminal shown, so a phone has one switch. |
| The picture on a phone | | starts folded into one sticky line above the terminal that names whose state it is, such as "Chain · Alex's repository: HEAD on main · main 1 ahead of origin/main". A tap unfolds it. History is one column there: each commit once, tagged both, yours only or mothership only. |

**Views.** Each view is live: it shows the repository as it is now, whatever the player typed.

- **Chain:** the chain from the levels. Alex's green pin shows only while Alex is shown. The
  mothership's pink pin shows while Alex is shown, or when it is not where your `origin/main`
  bookmark says. A line under the chain names work that is in no commit yet ("In your folder, in
  no commit yet: notes.txt (modified)", in git's word).
- **History:** only the chart (the user's decision), your repository beside the mothership, shared
  commits on shared rows. Each side is drawn with the chain's columns, so a branch is a side line
  and a fork is never flattened into one column.
- **Desk:** working folder, staging area, commits.
- **Move log:** `git reflog`'s lines, and nothing else (one picture per view). It stays empty
  until the player types `git reflog`, as in the missions. From then on it updates by itself, and
  says so once: "Live here: from now on it updates by itself. In missions you type `git reflog`
  each time." Commits no name leads to show on the chain from then on, faded and dashed.
- **Crew:** the mothership over both stations.
- **Graph:** git's own `git log --oneline --graph --all`, kept up to date. No starting point opens
  on it: the terminal says the same.
- **Conflict:** a tab of its own, shown only while a file has conflict markers, and kept until
  the merge is committed.

**Whose repository.** Chain, Desk, Move log and Graph draw one repository: yours, or Alex's
while Alex is shown. The Desk marks a file that arrived with a switch ("came with the switch")
and strikes one that left. History and Crew always show both people. Crew marks HEAD at each station.

**Colour never changes owner.** Violet always means you and green always means Alex, whichever
repository is drawn. In Alex's repository, Alex's capsules and filled tag are green, and the pin
for your `main` is violet. Pink is the mothership.

**The legend** folds behind "i", and lists only the marks on screen.

## Alex's terminal

It is hidden by default, behind a toggle that reads "Show Alex's terminal" or "Hide Alex's
terminal". Where there is no mothership (Empty folder) there is no toggle at all:

- A learner alone gets the full width.
- Showing Alex is a choice the player makes when they want a second person.

The two starting points about two people open with it shown: Alex is ahead, and Conflict. The
toggle is remembered per starting point.

How Alex's shell is set up:

- A second bash, run as the same Linux user, in Alex's clone (`teammate/project`).
- Its own HOME, with its own `.hushlogin`.
- Its own `GIT_CONFIG_GLOBAL`, with user.name Alex, user.email alex@example.com and the game's
  usual settings (`core.editor true`, `core.pager cat`).
- Its own history and command log.

Alex's commits are signed Alex because Alex's git configuration says so. The playground's old
button bar is not shown in free play: the two terminals replace it.

## Starting points

All use fixed dates, so a start is the same commits with the same hashes every time.

| id | Title | What it holds | Opens on | Alex | Tag |
|---|---|---|---|---|---|
| `empty` | Empty folder | README.md and notes.txt, no repository, no mothership | Desk | off (no mothership) | |
| `changes` | Uncommitted changes | main with notes.txt edited and not committed, and a branch `bright-lights` to switch to | Desk | hidden | uses Parallel universes, Time travel |
| `branches` | Two branches | main plus `bright-lights` and `quiet-engine`, forked off main's commit | Chain | hidden | uses Name tags |
| `alex-ahead` | Alex is ahead | Alex pushed two commits you have not fetched | History | shown | uses The mothership |
| `both` | Both committed | You committed a change to notes.txt; Alex pushed a change to route.txt, already fetched, so main and origin/main have diverged. `git pull --no-rebase` or `git merge origin/main` makes a merge commit, with no conflict | History | hidden | uses Collisions |
| `conflict` | Conflict | You and Alex changed the course line; your `git pull --no-rebase` stopped with markers in checklist.txt | Conflict | shown | uses Collisions |
| `lost` | Something lost | Two commits on `thrusters`, then the branch deleted | Move log (empty until `git reflog`) | hidden | uses Time travel |

- The playground is **open from the start** (the user's decision). A start that uses commands
  from a later chapter names the chapter ("uses Collisions"); none is locked. Stash is out of
  scope, so Uncommitted changes practises `git restore` and edits that come along on a switch.
- **Start over** rebuilds the current start.
- **Choose another** opens the picker.
- Both ask first. They say what is erased (the files and commits here, Alex's too) and what is
  never touched (missions).
- After the first visit, the playground opens where the player left it.

## Merge conflicts, two ways

**Click to keep** (flow 5), ported from Markers decoded, with Alex in green, not pink:

1. The panel reads the real file, and reads it again whenever it changes. It shows each conflict block with its two sides. One line says
   that the lines outside the markers were merged by Git on its own; those lines carry no tags.
   The marker's long hash is shortened in the panel; the terminal shows it whole.
2. Choosing Yours, Alex's or Both only marks lines; nothing changes until **Write**.
3. Write sends the choices to the server, which rewrites only the marker blocks of the real file.
4. The page never runs git. It says "Now type `git add checklist.txt`, then `git commit`".

The panel and an editor work on the same real file:

- While an editor has the file open, the panel is greyed and says it waits.
- The moment an editor opens the file, picks are cleared and the nano and vim chips grey out.
- Once the markers are gone (after Write, or after an editor saves), the panel shows the
  resulting file as it is now, with "no markers left" and the next commands.
- If a Write still reaches the server after the file changed, the server refuses with a 409 and
  nothing is written. The picks are cleared and **Look again** becomes the main button (flow 7,
  shown once as the rare case).

Under the panel, the editor way is offered as two chips, `nano checklist.txt` and
`vim checklist.txt`. Each types its command at the prompt.

**An editor** (flows 6 and 7): `nano checklist.txt` or `vim checklist.txt`, typed by the player.

- While an editor runs, a gold strip above that terminal says how to save and how to quit, in
  that editor's keys.
- vim's strip says "Save and quit: Esc, then :wq Enter" first. "Type: press i", "Leave typing
  mode: Esc" and "Quit without saving" follow on a wide screen, and sit behind "more keys" on a
  phone, so the strip is two lines there. In vim's INSERT mode "Leave typing mode: Esc" is never
  hidden.
- **Get me out** is red and asks first: "Quit vim without saving? Your changes to checklist.txt
  are lost." The choices are Quit without saving, or Keep editing. It then types the editor's
  quit-without-saving keys for the player: for vim, Esc, `:q!` and Enter; for nano, Ctrl+X then
  N.
- How the page knows: the shell's startup wraps `nano`, `vim` and `vi` so they set the terminal
  title while they run. The page sees it through xterm.js `onTitleChange`. No polling, no files.
- The strip never mentions Ctrl+W (nano's search): the browser takes it to close the tab.
- Git itself still never opens an editor (`core.editor` stays `true`); a merge's `git commit`
  keeps git's prepared message. Only the player opens an editor.
- vim must be added to the image; nano is there already.

## How it is reached

- **The map:** a Playground landmark beside the sectors (flow 1).
- **The dev page:** a Playground section with one link per starting point.
- **The field guide:** each command card links to the start that suits it (flow 9):
  `#/playground?start=<id>&view=<view>&try=<command, URL-encoded>`.
  - `view` is optional.
  - `try` shows a chip, "Try: git switch -c test", on your terminal right above the prompt.
    Clicking it types the command at the prompt and does not press Enter. The chip disappears
    once its command has run.
  - Agreed with the guide teammate: each card carries `playground: {start, view?, try}`, and
    `try` is a concrete one-line command that works in that start. The guide adds the data, and
    a test that every start is known, once the `#/playground` route exists.

    | Start | Cards and their tries |
    |---|---|
    | empty | `ls -a`; `git init`; .gitignore (no try) |
    | changes | `git status`; `git diff`; `git add notes.txt`; `git commit -am "Note the fuel"`; `git restore notes.txt`; `git restore --staged notes.txt` (after `git add`); `git rm --cached notes.txt` |
    | branches | `git log --oneline`; `git branch test`; `git branch first HEAD~2`; `git branch -d quiet-engine` (refuses: not fully merged, which is the lesson); `git branch -v`; `git switch bright-lights`; `git switch -c test`; `git checkout quiet-engine`; `git checkout -b test`; `git log --oneline --graph --all`; `git revert HEAD`; `git reset --hard HEAD~1`; `git push`; `git push -u origin bright-lights`; remote add (no try) |
    | alex-ahead | `git fetch`; `git pull`; `git clone ../github.com/moonbase/project.git ../copy` |
    | both | `git pull --no-rebase`; `git merge origin/main` |
    | conflict | `git merge --abort`; `git restore --theirs checklist.txt`; `git commit --no-edit` (after `git add`); the conflict walkthrough (no try, view crew) |
    | lost | `git reflog` |

    The starts must hold exactly these names:
    - Every terminal opens in the project folder.
    - The mothership is `origin`, at `../github.com/moonbase/project.git`.
    - The files are README.md, notes.txt, route.txt and crew.txt.
    - branches has `bright-lights` (lights.txt) and `quiet-engine` (engine.txt), off main's commit.
    - changes has `bright-lights`.
    - lost's HEAD@{1} is "Test the right thruster".
- **Leaving a level:** opening the playground from a card over a level does not end the level.
  The playground has its own lab and its own terminals, and "Back to Mission N-M" returns to the
  level as it was.

## What to build

| Unit | Who | What | Reuses |
|---|---|---|---|
| T1 | termlab | Serve several terminal endpoints, each with its own `TerminalSettings`, sharing one `max_terminals`. Paths: `/api/terminal` (levels, unchanged), `/api/terminal/playground`, `/api/terminal/playground-alex`. The user allowed changing termlab. | `termlab.web.shell`, `terminal` |
| E1 | engine | Starting-point registry and setups; the playground's own lab under `FIRSTCOMMIT_HOME/playground`, apart from the active level; a save record `{start, alex_shown, view, whose}` | `kit.setup_playground`, the levels' fixed-date helpers |
| E2 | engine | Two playground shells: yours and Alex's, each with its own environment, home, git configuration, prompt, history and command log. The startup's editor wrappers set the title. | `game.shell_environment`, `commands.startup`, `gitcmd.shell_environment` |
| E3 | engine | `GET /api/playground` (starts with titles, blurbs, uses, the current one and prefs); `POST /api/playground/start {start}`; `POST /api/playground/prefs {view, alex, whose}`; `GET /api/playground/observe` | `Observation`; add Alex's own reflog, conflicts, texts and graph; graph always on |
| E4 | engine | `POST /api/playground/resolve {file, read, choices}`. `read` is the hash of the text the panel showed. The server parses the marker blocks and writes each one's chosen sides (yours, theirs, both). It answers 409 when the file changed, and 400 when the number of choices does not match the blocks. | `MARKER` in playground.py |
| E5 | image | Add `vim`; pin it in the Dockerfile's version comment | |
| F1 | frontend | The playground screen: header, view tabs, Whose switch, the picture slot | chain.js, desk.js, move-log.js, git-graph.js, zone-panel.js (crew), the history chart, sides.js |
| F2 | frontend | The second terminal, the toggle, the phone's You / Alex switch | the level screen's terminal |
| F3 | frontend | The click-to-keep panel | Markers decoded; the guide's conflict walkthrough |
| F4 | frontend | The editor strip and Get me out | |
| F5 | frontend | The starting-point picker, Start over and its confirmation, the map landmark, the dev page section, the try chip | starmap.js, dev.js, dialog.js |
| G1 | guide | "Try it in the playground" on each command card | field-guide.js |

Order:

1. T1 first.
2. Then E1 to E3, together with F1 and F2.
3. E4 with F3, and E5 with F4, can run in parallel with step 2.
4. F5 and G1 last.

## The game's history view (same fork problem)

The game's History view has the problem the review found here. Its chart (zone-panel.js
"chart" mode, rows from `Zones.rows`) puts the vault in one column in topological order, so two
experiments off one commit stack as if one came after the other.

Recommended change for the game:

- Draw each side of the chart with chain.js's `layout` and `wires`: column 0 for main's line,
  one column per side line.
- Keep the shared rows and the tethers.
- Above the chart, one line: "Your repository beside the mothership. Side lines are branches;
  Chain shows one repository in detail."
- A cheaper stopgap, if the chart cannot take columns yet: show only the commits reachable from
  `main` and `origin/main`, with "+N commits on other branches: see Chain" under it. Never stack
  a fork into one column.

## Open points

- **The guide's command-to-start mapping** awaits the guide teammate's reply.
