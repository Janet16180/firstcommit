# Start here: First Commit, the graphic work (fresh session)

Paste this into the new session:

```
Read ./docs/briefs/GRAPHICS_SESSION.md and continue the
graphic work of First Commit as the lead, starting with G1.
```

## 1. The project

First Commit is a browser game that teaches Git and GitHub to new hires: a page with lessons,
quests and challenges beside a real terminal, and a live picture of the player's repository.

- Code: `.`. Work branch `phase-2-engine` (`main` holds only
  the design; merging into it needs the user's OK). Python 3 + uv; the page is plain JS in
  `src/firstcommit/web/static`, tested with node from pytest.
- termlab (the terminal library) is used from `~/learning/termlab-firstcommit`, branch
  `firstcommit`. Game-specific termlab changes go only there; never touch termlab `main`.
- Run the game on a throwaway home:
  `FIRSTCOMMIT_HOME=$(mktemp -d) uv run firstcommit serve --port 8877` (it prints a link with a
  token). The user's playtest is Docker: `docker stop firstcommit` (an old build may still run),
  then `FIRSTCOMMIT_PORT=8890 deploy/docker/run play`. Restart it only when a change is big
  enough for the user to see.
- Read before working: `docs/STATUS.md` (full history, backlog, lessons), `AUTHORING.md` 3.5
  (the picture-first lesson rules), `docs-draft/four-places.md` (what lights up and why,
  revision 8, fact-checked), `docs/DESIGN.md`, `~/learning/GAME_METHODOLOGY.md`.

## 2. The user's rules

- Picture first: every explanation leads with a figure drawn from real data, short text, and
  animation; detail folds under "More". Every motion is the difference between two real
  snapshots; nothing is invented.
- Team: named teammates (Agent with a `name`), never one-shot subagents; at most 3 working at
  once (2 while the user's helper account works on this machine); disjoint file ownership; short
  jobs; one short report per job. Verify claims on disk before telling the user.
- Tests: teammates run only the fast tier, `uv run pytest -m "not slow and not docker"`, plus
  `uv run ruff check` and `uv run mypy`. The lead runs the slow tier when merging, under
  `flock .scratch/locks/docker.lock`. Every browser run goes under
  `flock .scratch/locks/browser.lock` (the machine is shared; the user saw CPU and RAM overload).
- Merge the hash a teammate reports, never a branch name.
- Fact-check only text players will see soon (a checker replays each claim on real git 2.43).
- Screenshots: the terminal must never show the user's prompt or email. After every page load,
  type `exec bash --norc --noprofile` then `PS1='$ '`, and refuse to save when the terminal shows
  "@", "janetrivera" or ".claude" (the saved scripts below do this).
- A test that starts a real shell gets a temporary HOME and HISTFILE; never touch the user's
  home files (a test once truncated `~/.bash_history`).
- Never push. Ask before deleting branches or anything hard to undo. Commits: a short plain
  subject, no `Co-Authored-By` or any trailer, no emojis. Answer in English.
- Stuck on something complex: stop and ask the user for what would unblock it.
- The engineering rules in `~/.claude/CLAUDE.md` (TDD, type hints, NumPy docstrings, single
  return, design by contract) apply to every change.

## 3. The picture language (built and merged)

- The four places: working folder (files are pages, each with its blob id), staging area (an
  open box), your repository (closed boxes on timelines, each a commit with its short hash), and
  GitHub. Arrows for add, commit, push, fetch, pull and clone light from what really changed.
- The live page (option A): the places are the live map, at full size, with the key "closed
  box = commit" under the figure; heading "The three areas", or "The four places" with a GitHub;
  the "what just happened" feed below.
- Lessons: a "places" slide draws the compact places; each slide's events come from the live
  feed's rule; every places slide fits 1280x800 when there is no GitHub.
- "Your first commit" is picture-first (9 slides). The map guide ("How to read the map") opens
  from the key. "Share a file with Alex" runs in the demo only.
- The two-person playground (you and Alex, same buttons) works end to end, but no level uses it.
- Commits are drawn as closed boxes; rings are one switch (`LIVE_COMMIT` in `theme-time.js`)
  if the user picks them.

| File (`src/firstcommit/web/static/`) | What it draws |
|---|---|
| `theme-time.js`, `theme-time.css` | the time-travel look, `TimeTheme.live`, `LIVE_COMMIT` |
| `theme-time-places.js` | the four places and their arrows; the typed-command parse (30b2e11) |
| `theme-time-motion.js` | motions between two snapshots |
| `theme-time-guide.js`, `.css` | the map guide |
| `theme-time-share.js`, `.css` | you, GitHub and Alex (playground and demo) |
| `live.js` | the live panel beside the terminal |
| `lesson.js` | the lesson player |
| `playground.js` | the playground's buttons and results |

Shared with the user: the Four Places Demo, https://claude.ai/artifact/72KsUGhDae4pErRzU7Kzrv
(version 4, source `.scratch/demo/four-places-v4.html`; publish an artifact as one bundled HTML
file), and Commit Shape Choice, https://claude.ai/artifact/GB9XGi8bZC5oz21zDja7du.

## 4. The graphic work, in order

**G1. Four places that fit 1280x800 with GitHub.** With a GitHub, a lesson's places slide
stacks GitHub below your computer and does not fit. Draw GitHub beside your computer (a wide
four-place layout in `theme-time-places.js` and `theme-time.css`), then make the lesson's
four-place slides full width (`lesson.js`). Guide's `p2/lesson-github` 49fee17 already draws a
slide's GitHub and plays its push, fetch, pull or clone; build on it. Check at 1280x800 and
1920x1080, light and dark.

**G2. Chapter 1's lesson.** "Git, GitHub and your first clone" is written on `p2/start`
6f655bb (a 5-slide lesson in the four places with a practice GitHub, a guided clone, and the
challenge "Who added the checklist?"). It needs: the lesson's practice GitHub as a Python
builder (`p2/insight` f115816 plus helper job A), `kit.cloned_from_github` (helper job B),
49fee17 and G1. Land them as a chain, fix the lesson-frames test that is skipped until then,
take the lesson screenshots (`.scratch/visual-start/run_start.sh <out-dir>`), have a checker
replay the claims at the end of `docs/verification/start.md`, then merge with the slow tier.
Do not merge `p2/start` before that.

**G3. Arrows from the commands the player types.** The game now runs its own bash (prompt
`project $ `) and logs each typed line with its status, returned as `Observation.commands`
(`p2/core` d053403). `TimePlaces` can already parse typed lines (30b2e11: it splits on `&&`,
`||`, `;` and `|`, a failed command lights nothing, and it falls back to snapshots when nothing
was typed). After helper job C links the page's terminal to that shell, wire
`Observation.commands` into `live.js`, add one paragraph to `docs-draft/four-places.md`, and
have that paragraph fact-checked.

**G4. The playground in a real level.** Write a level that uses it (author's job), and fix its
layout: at 1280 the result box (`.pg-result`) lands below the fold after a press; scroll it into
view or put it beside the button bars. Then resume the paused re-record of the playground mock
(steps in `docs/STATUS.md`, Backlog; branch `p2/playground-design` 3378348).

## 5. Engine jobs (not graphic)

`docs/briefs/HELPER.md` holds four jobs for the user's second account: A the lesson's GitHub
as a Python builder, B `kit.cloned_from_github`, C the page's terminal running the game's shell,
D a "Restart level" button. Before starting any of them, look for its branch
`p2/helper-<job>` or its report `.scratch/reports/helper-<job>.md`; if the helper did it, review
and merge its reported hash. If nobody took them, do A, B and C before G2 and G3 need them.

## 6. Branches

All under `.scratch/wt/<name>` (a `termlab-firstcommit` link there resolves the path). Start a
teammate from a named hash with
`git worktree add .scratch/wt/<name> -b p2/<name> <hash>`.

| Branch | Hash | State |
|---|---|---|
| `phase-2-engine` | see `git log -1` | everything merged; 1116 tests passed on the last full run |
| `p2/start` | 6f655bb | chapter 1, waiting for G2 |
| `p2/insight` | f115816 | a lesson's practice GitHub (still as shell lines) |
| `p2/lesson-github` | 49fee17 | lesson slides drawn with GitHub |
| `p2/core` | d053403 | the game's own bash and `Observation.commands` |
| `p2/playground-design` | 3378348 | paused re-record (WIP) |
| `p2/core-press-wip` | f278233 | old WIP, superseded |
| `p2/theme-metro`, `p2/boxes-live` | e44f2df, c156a29 | rejected or superseded prototypes |
| `p2/level-visual`, `p2/theme-share` | dbb2134, a6191a5 | only merge commits; content already merged |

The finished ones can be deleted once the user agrees.

## 7. Tools

- Screenshots go through Playwright from `~/learning/ring0/.venv/bin/python`, under the browser
  lock. Saved scripts: `.scratch/visual-first-commit/run_visual.sh <out-dir>` ("Your first
  commit" at 1280; `SERVE_FROM=<checkout>` picks the code to serve) and
  `.scratch/visual-start/run_start.sh <out-dir>` (chapter 1, serves `.scratch/wt/start`). Both
  start a server on a throwaway home, reset the prompt and refuse leaky shots.
- Reviews and fact-checks so far: `.scratch/review/`.
- Revert checks (break the code on purpose to see a test fail): run with
  `PYTHONDONTWRITEBYTECODE=1`, or a stale `.pyc` runs the wrong code.

## 8. Waiting for the user

- Rings or boxes for commits (boxes are used everywhere now).
- Security L3: drop `SSH_AUTH_SOCK`, `SSH_AGENT_PID`, `GH_TOKEN`, `GITHUB_TOKEN` and
  `GH_ENTERPRISE_TOKEN` from the page's shell (recommended yes).
- Real situations new hires get stuck on, to shape the next chapters.
- Merging `phase-2-engine` into `main`, and deleting finished branches.
- Whether to remove the 24 test lines at the end of `~/.bash_history` (their call; offer
  `cp ~/.bash_history ~/.bash_history.bak && head -n -24 ~/.bash_history.bak > ~/.bash_history`).
