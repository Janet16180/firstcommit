# First Commit: status and handoff

A fresh session on the graphic work starts from `docs/briefs/GRAPHICS_SESSION.md`; this file
keeps the full history.

Read this first when resuming, then `docs/DESIGN.md` and `AUTHORING.md`.

## How we work

- The method is `~/learning/GAME_METHODOLOGY.md`: the lead (main session) writes contracts, splits
  work into agents with disjoint file ownership, verifies every claim on disk, integrates and
  reports. Correctness first; every chapter gets an independent fact-checker.
- Engineering rules: `~/.claude/CLAUDE.md` and `AUTHORING.md` section 2.
- Git: `main` holds reviewed work; each phase is a branch (`phase-2-engine`), each agent a branch
  `p2/<name>` in a worktree under `.scratch/wt/<name>` (with a `termlab-firstcommit` link next to
  the worktrees so `../termlab-firstcommit` resolves). Small commits, plain messages, no trailer,
  never push.
- termlab: First Commit uses termlab's `firstcommit` branch, checked out as the worktree
  `~/learning/termlab-firstcommit`; termlab's `main` (`~/learning/termlab`) stays as Ring Zero
  uses it. The user allowed changes on that branch (2026-10-06). Changes so far: `d98edf1`, an
  error reply's whole JSON reaches the game as `error.data`; `aee1388`, a reply body that never
  arrives in time counts as no answer (status 0), like a fetch that fails.

## Decisions

See `docs/DESIGN.md` section 2. Also, 2026-10-06: Docker is the front door for new hires, WSL
direct for development, termlab's VM later (the lead's call, delegated by the user).

## Phase 2 (integrated 2026-10-06, branch `phase-2-engine`, not yet on `main`)

All five agents' work is merged into `phase-2-engine` (aab46d5): the game layer (core), the
repository snapshot, change feed and lesson figures (insight), the routes and page (web), the
Docker adapter (docker) and the template level "Your first commit" (author, then a second,
independent fact-check by checker: 13 more fixes, 2 of them false teaching).

Gates on `phase-2-engine`: ruff, mypy strict (43 files), ESLint clean; pytest 705 passed, nothing
skipped or xfailed, including the Docker smoke tests (`--help` and serving the real game through
localhost from the container) and the page's node tests run from pytest.

The lead played the template level end to end over HTTP on a fresh home (lesson, 8 quest steps
with wrong answers, the automatic check refusing mid-quest, payout of 100 XP, the player's name
only in the game's gitconfig). The web agent played it in Chrome by typing real git commands:
screenshots in `.scratch/wt/web/.scratch/real-t96H/engine-shots/`.

Worktrees of the finished agents stay under `.scratch/wt/` (branches `p2/*`); ask the user before
deleting branches.

Done since: the code review and the security review (both report only), then a fix round
(security lows, review findings). Security L3 waits for the user: drop `SSH_AUTH_SOCK`,
`SSH_AGENT_PID`, `GH_TOKEN`, `GITHUB_TOKEN` and `GH_ENTERPRISE_TOKEN` from the page's shell (the
lead recommends yes).

## Phase 2b: visual explanations (state at the end of 2026-10-07)

The user picked the time-travel theme and asked for picture-first explanations (AUTHORING 3.5)
and an interactive playground. There is no game story; the visuals are the creative part.
Pictures: a file is a page, the staging area an open box, a commit a closed box; the four places
are the working folder, the staging area, your repository and GitHub. Every motion is drawn
from the diff of two real snapshots.

Merged into `phase-2-engine` (tip ff1bdb3; all 1116 tests passed, slow and Docker included):
- The live page: the four places are the map (option A): full-size timelines with closed boxes,
  the key "closed box = commit" under the figure, heading "The three areas" or "The four places"
  (with a GitHub), the feed below, the guide's button in the key. Lighting and captions were
  fact-checked through revision 9 (`docs-draft/four-places.md`, `.scratch/review/`).
- Lessons: the "places" view (compact, every slide fits 1280x800), per-slide events by the live
  feed's rule, a folded "More" on slides and quest steps.
- "Your first commit" rewritten picture-first: 9 slides, short quest steps, claims V1-V18 checked.
- The map guide (revision 6) and "Share a file with Alex" (share revision 2; in the demo only).
- The two-person playground engine: catalogue, press with before and after, the route, the page
  panel, explanations (`firstcommit.explanations`, from the fact-checked mistakes table). No level
  uses it yet.
- The typed-command parse in TimePlaces (not wired yet).
- termlab's `firstcommit` branch: d98edf1, aee1388.

Parked as WIP when the day ended (resume in this order, at most 3 teammates working at once):
1. Lighting from typed commands (user approved): core (termlab option to choose the terminal's
   shell; the game runs bash with its own rc: a plain prompt and a PROMPT_COMMAND log of
   {line, status}; observe returns the commands since the last observation), then web (the
   terminal setting, api.js, records.json), then timetravel (wire typed lines into live.js, one
   paragraph in the four-places draft). Done: termlab 01ee4e8 (the shell option) and core
   d053403 (the game's bash with prompt `project $ `, the command log, `Observation.commands`;
   `firstcommit shell` already uses it). Next: web adds `shell=game.shell_command` to the
   terminal route, api.js and records.json on d053403; then timetravel wires live.js (its parse
   is 30b2e11, merged). Until web's link, the page's terminal runs the user's $SHELL.
2. Chapter 1 "Git, GitHub and your first clone" (plan approved; written by the author on
   `p2/start` 6f655bb, with `levels/_start.py` helpers and `docs/verification/start.md`; fast
   tier 1140 passed, 1 skipped (the lesson-frames test, waiting for P1); both levels play to the
   debrief at 1280; do not merge before P1 and P2; the test_routes fix that skips `_` helper
   modules is in 6f655bb; author's next steps: move the clone check into
   `kit.cloned_from_github` with tests in test_kit.py, fix the frames test once P1 lands, the
   lesson browser shots (`.scratch/visual-start/run_start.sh <out-dir>`), then the final hash for mapcheck, which checks the claims list at the
   end of the log): `start-git-and-github` (guided:
   a 5-slide lesson in the four places with a practice GitHub, then clone, cd, count files and
   commits, name the remote) and `start-first-clone` (challenge: who added the checklist, from
   `git log`). Needs insight's P1 (a lesson's practice GitHub: `p2/insight` f115816, done;
   Frame and SlideView `github`; web's api.js/records.json link next; decided for next session:
   `LESSON_GITHUB` becomes a Python builder `(Path) -> None` using kit.git, the same function the
   level's setup calls on lab.github, instead of bash lines), guide's P2 (the
   places view with GitHub: `p2/lesson-github` 49fee17, lights clone, commit, push, fetch and pull
   right) and `kit.cloned_from_github` (author). A typed clone keeps git's absolute origin; fine
   while the chapter never pushes or pulls. Open: a four-place lesson slide does not fit 1280x800
   (GitHub stacks below); next, timetravel's wide four-place layout with GitHub beside your
   computer, then guide's full-width four-place slides. P1's slide events must include
   GitHub's changes (as observe does), and a teammate's push belongs on a non-places slide.
3. The playground in a real level (author phase); then the paused re-record (Backlog).
4. A "Restart level" button while playing a level (user, 2026-10-07; small): the level page has
   only "Leave this level", yet hints already say "Restart the level". The playground inside a
   level resets with it; the map page's "Start over" stays as it is.

The user's second account can take four engine jobs, briefed in `docs/briefs/HELPER.md`:
A the lesson's GitHub as a Python builder (P1's switch), B `kit.cloned_from_github`, C the
page's terminal running the game's shell (web's link in item 1), D the Restart level button.
Before waking a teammate for one of them, look for the helper's branch `p2/helper-<job>` or its
report `.scratch/reports/helper-<job>.md`; review and merge its reported hash with the slow tier.
While the helper works on this machine, keep at most 2 teammates running.

Team rules (the user's, 2026-10-07): named teammates, never one-shot subagents, at most 3
working at once; agents run the fast tier, the lead the slow tier on merge; fact-check only text
players will see soon; one short report per job; when stuck on something complex, ask the user
for what would unblock it.

Shared with the user: the Four Places Demo (https://claude.ai/artifact/72KsUGhDae4pErRzU7Kzrv,
version 4, with the Alex walkthrough), Commit Shape Choice
(https://claude.ai/artifact/GB9XGi8bZC5oz21zDja7du), and the playground mock as a local file
(`.scratch/wt/playground/docs/drafts/playground-mock.html`, older button set).

Playtest: Docker on port 8890 still runs the ebe0fff build; the user asked to restart only for a
bigger change (typed-command lighting or chapter 1).

Waiting for the user: rings or boxes (the live page and lessons already show boxes; rings are
one switch, `LIVE_COMMIT`), security L3, and the situations new hires hit (for chapter content).
The user says the layout responds well, so no more screen-size work.

## Lessons for the method (to fold into GAME_METHODOLOGY.md)

- A subagent that an agent starts (for example an author's own fact-checker) hands its report
  to the lead's session, not to the agent that started it. The author waited for a report that
  never reached it; the lead found out by checking the files on disk and forwarded it. Tell
  agents that their own subagents report to the lead, or ask them not to start any.
- The first fact-check of the template level found 7 false statements in one beginner level;
  the patterns became AUTHORING section 1, rules 8-10.

- A lead change to a shared value (GIT_CEILING_DIRECTORIES became a list) broke a consumer that
  parsed the variable back into a path. The suite stayed green because every test home lived in
  /tmp, with no repository above it; a player whose home is a dotfiles repository would have seen
  their own files in lesson figures. Core caught it by reasoning about the merge. Rules: derive
  nothing from an environment variable you also build (keep one named constant), and test the
  isolation with the game home inside a repository.

- With eight agents, parallel full suites (each building the Docker image) and Playwright
  browsers overloaded the machine; the user noticed. Rule since 2026-10-06: every browser run
  under `flock .scratch/locks/browser.lock`. Tests in two tiers (the user's call, 2026-10-07):
  agents run only the fast tier, `uv run pytest -m "not slow and not docker"` (about 20 s, node
  tests included), plus ruff and mypy; the slow tier (`slow` and `docker` markers: property
  tests over real git, the Docker image) runs once, by the lead, when merging into
  `phase-2-engine`, under `flock .scratch/locks/docker.lock`. A test that takes 0.5 s or more
  gets the `slow` marker. Give this rule in the first brief.
- Merge the hash an agent reports, never its branch name: a branch moves while its agent keeps
  working. The lead once merged `p2/core` mid-step and pulled in an unfinished records change
  (4 red tests); the merge was redone from the reported hash. When one change needs edits in
  several owners' files, land it as a chain (each owner merges the previous link's hash and
  fixes their own tests), and merge only the last link.
- Screenshots of the game page: reset the prompt after every reload and refuse to save if the
  visible terminal shows "@" (a reload once brought back the user's prompt with their email).

- Revert checks (break the code on purpose, expect a test to fail): a same-size mutation restored
  within the same second leaves Python's .pyc of the mutant valid (it checks only mtime to the
  second and size), so the suite can run the wrong code. Run them with
  `PYTHONDONTWRITEBYTECODE=1`, delete the module's .pyc after each write and restore, and print
  which test failed, so a "caught" names its catcher (found by insight, 2026-10-07).

- Tests that start real shells must give them a temporary HOME and HISTFILE. On 2026-10-07
  core's terminal-log tests ran bash with the user's real HOME: an inner `bash --norc` appended
  24 test lines to the user's ~/.bash_history and cut it to bash's default 500 lines. The shared
  fixture now isolates HOME and fails a test if ~/.bash_history changes.

## Backlog (decided later, not now)

- Playground re-record, paused 2026-10-07 at `p2/playground-design` 3378348 (WIP port of the
  recorder and mock onto `firstcommit.playground` and `firstcommit.explanations`). To resume:
  merge insight's final tip (0cc86dd or later, never 2a2e9b1 alone: older texts), run
  `uv run python tools/playground_errors.py docs/drafts/playground-errors.md` and
  `uv run python tools/playground_mock.py src/firstcommit/web/static docs/drafts/playground-mock.html`,
  check the mock under the browser lock, then mapcheck re-checks.
- Playground layout, when it goes into a real level: at 1280 the result box (.pg-result) sits
  below the live pane's fold after a press; scroll it into view or put it beside the bars.
- At 390 px the top bar (.player, .prefs) makes every page 827 px wide. Left as is: the game
  needs a terminal, so it is for laptops; revisit only if phones become a target.

- repomap `outer` field (path to an enclosing repository, e.g. ".."), proposed by insight, for a
  generic "Git sees a repository one folder up" hint on the map. Deferred: no second use yet.
- termlab's `snippets.run` decodes output as text with universal newlines, so a `\r` becomes
  `\n`. demos works around it (writes output to a file read as bytes) without touching termlab.
  A termlab option to keep raw output would be the user's call.

- For the `history` chapter author: long `git log` and `git diff` output still opens the pager
  (`less`); teach `q`, Space and `/` there. Short output no longer stops in the pager
  (`core.pager = less -FRX` in the game's config, git's own default when LESS is unset).

- For the `remote` chapter author (from the map guide fact-check): a plain `git pull` on
  diverged branches fails on git 2.43 ("Need to specify how to reconcile divergent branches").
  Decided: the game's config leaves `pull.rebase` unset, as git ships, and the chapter teaches the
  choice (`--no-rebase` / `--rebase`); the playground's Pull button shows the real error.

- repomap does not see uncommitted changes inside a submodule (`git status` reports them). No
  chapter teaches submodules yet; revisit if one does.

## Level polish for "Your first commit" (from the checker's blind playtest)

Done in the fix round (checker, p2/level-check, merged at b522bb5): the identity steps come
before the first file, so a commit tried too early fails on the empty staging area instead of
git's identity error; `readme.md` in another letter case gets its own nudge; the briefing says
the terminal opens in the empty `project` folder; the commit step says that without `-m` Git
opens an editor. Left for the second basics level ("A message that helps"): teaching the editor
itself (write, save, quit).

## Folded instructions (merged 2026-10-06, bdc5202; all 1116 tests passed)

While playing a level the player can fold the instructions ("« Hide"): the map and terminal take
the whole width (the three areas then fit in one row at 1280) and a one-line card in the map's
heading row names the current step, flashes when it changes, has Continue on read steps and
"Answer" (opens on the answer box). The choice is kept in localStorage
(`firstcommit.instructions`). Code: `practice.js`, `app.css`; tests in `tests/js/practice.test.js`;
screenshot script `.scratch/visual-fold/run_fold.sh <out-dir>`.

## Next

0. The user's next request, after the current work: rethink the start of the game (which level,
   chapter 1 or "Your first commit", still to be asked). The lead proposed "do first": one or
   two slides naming the places, a guided quest where each typed command animates the live map,
   then a challenge with the map hidden and revealed on solve (needs a level option to hide the
   live panel). The user has not picked a shape yet; ask before spawning the agent.
1. Resume the parked work above, in order, with at most 3 teammates.
2. The user plays with the new look (restart the playtest when a bigger change lands); then merge
   `phase-2-engine` to `main` (ask first).
3. Ask the user before deleting branches: `p2-integrate`, `p2/theme-metro`, `p2/boxes-live`,
   `p2/core-press-wip` and the finished `p2/*` branches once merged.
4. The VM adapter (`vm/game.env`, `vm/guest-setup.sh`, wrapper) on termlab's VM.
