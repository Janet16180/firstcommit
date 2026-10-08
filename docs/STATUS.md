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

## Handoff, end of 2026-10-08 (read this first)

Plans in force: `docs/drafts/chapters-3-7.md` (rules, wave 1) and `docs/drafts/chapters-5-9.md`
(sectors 5 to 9 and the view ladder, approved by the user). Contract: `docs/briefs/ORBIT.md`.

`phase-2-engine` at 9234c6e has 24 levels in English and Spanish (liftoff,
cargo 2-1 to 2-3, vault, mothership 4-1 to 4-5 plus 4-2b, branch 5-1 to 5-4, conflict 6-1 to 6-4), the
lost panel during a quest, the pager off, any address to the stand-in GitHub, last hints that
solve the level (a harness test types them), 3-2 as an accidental change, Snapshot.remotes and
Reaction.moment. Every tier was green at each merge, Docker included.

The user's decisions today, not yet built or not yet merged (see ORBIT.md and the plans):
- the mothership's address becomes `../github.com/moonbase/project.git`, with Rama's line
  "At work, the same address looks like https://github.com/moonbase/project.git" (not insteadOf:
  git shows the local path everywhere, engine's evidence);
- Node 24 LTS, pinned by checksum, in the Docker test stage (Node 18 broke a page test);
- the challenge alarm is generic, and Base 7 gets its own `meteor` scene;
- each moment plays once per opening of the level screen;
- Robin is a reviewer shown only as a portrait; Alex the teammate who acts.

Team for tomorrow: engine and frontend (named teammates, each in `.scratch/wt/orbit-*`), the
artist subagent (`.claude/agents/artist.md`, a registered type from a new session), at most three
agents working at once. A new session re-briefs them from this file and their branches.

engine's queue, in order (engine's handoff, head 0b712d5): shared ok reactions for git fetch and
git pull; the new mothership address with Rama's line, and the press sample's remotes; meteor in
Art for Base 7 (check frontend's merged art first); Node 24 in the test image; termlab's hint
label; rebase onto the latest `phase-2-engine`; ble.sh (built, NOT merged, waiting for the user: see below); then wave 2 (records for views with ids
station, crew, history, sides, blackbox, board, focus; 2-5 Junk bay; sector 5 with the new 5-4
"Edits come along"; sector 6 reworks; sector 7). Merged tonight at 9234c6e: 2-3's secrets explanation
(8b67f03) and 4-2b "Two halves of a ship" (6a7251d). E10 (the 409) is closed: two play scripts shared a port and a log; runs now use private ports.

ble.sh is built at `p2/orbit-engine` 0b712d5 (one commit after 6a7251d), every tier green on
engine's side, but held for the user to try first:
- it pins 0.4.0-devel3 (0.3.4 has no PREEXEC/POSTEXEC hooks or faces), vendored unmodified with
  its checksum and BSD-3 licence in `src/firstcommit/vendor/`;
- each command takes about 0.5 s longer to return to the prompt than plain bash;
- the first start in a fresh game home leaves one line "ble/term.sh: updating tput cache ...";
- try it: `git switch --detach 0b712d5` in a scratch worktree, then run the game and type a few
  commands. Merge it with a review branch if the delay is acceptable.
The old side branch `p2/orbit-engine-blesh` (b8a5a68) and its worktree are superseded and can be
deleted with the user's go-ahead.

frontend's batch is merged (7e9f7d3: crew view with Alex as a 60% mirror, the artist's six
moments, the unnamed mothership card, reaction moments played once per opening of a level, the
Node 18 timers fix, and Rama's line holding a warn, err or moment reaction until the moment
ends). Its queue: wire the tab row and the strip into the level screen once engine's view
records land (LevelView.view, views_seen, POST /api/view); the V2 fold and V4 unroll births in
5-1 with reduced-motion versions and Rama's birth lines; V3 band; V5 two sides; V6 black box;
ignored files greyed "still on your disk"; grow MOMENT in api.js as engine adds junk-flood,
unreviewed-main, force-break and search-beam (art and captions are ready). Small gaps left: a
warn followed one tick later by a met goal (no moment) is still replaced; in 2-3 the met goal's
note is replaced on the next poll by the next goal's note. Leftovers to tidy: the scratch
worktree `frontend-moments` and the Docker image `frontend-firstcommit:test`.

Waiting for the user: try ble.sh (above) and decide; delete the old lessons, the map guide, map.js and the theme-time files
(asked, not answered); review `docs/i18n-glossary.md`; playtests with first-time players on
the build of 2026-10-08 (`deploy/docker/run reset`, then `deploy/docker/run`).

## Orbit wave 1 (2026-10-08, merged into `phase-2-engine` at 99f4312)

All 1884 tests, the 19 Docker tests, ruff, mypy and ESLint pass.
- 14 levels in English and Spanish: liftoff (2), cargo (3), vault (4, challenge 3-5),
  mothership (5, boss Base 7). Decks for liftoff, cargo, vault and mothership.
- Spanish: neutral Latin American, Git terms kept in English (`docs/i18n-glossary.md`, a NEVER
  list in `tests/test_translations.py` shared with the page's test). Status.language is the one
  source; POST /api/language switches.
- Engine: `core.editor = true`, the player signs as Cadet, level events, choice steps,
  challenges, lost-work verdicts, history helpers, a reflog on the stand-in GitHub.
- Page: sounds, Atkinson bold buttons, the field guide (fact-checked), the vault as a graph,
  predictions, the challenge look, lost work, conflicts, scene captions in both languages.
- Next: frontend plays wave 1 in Chrome; engine does ble.sh, termlab's label option, then wave 2
  (branch, conflict, undo). The user runs playtests with first-time players on wave 1.
- Still waiting for the user: delete the old lessons and map guide (map.js, theme-time files);
  review `docs/i18n-glossary.md`.

## Orbit (2026-10-07, merged into `phase-2-engine` at 7858432)

The user approved a new look and level style (`docs/drafts/orbit-design.html`); the contract is
`docs/briefs/ORBIT.md`. All 1402 tests, the 19 Docker tests, ruff, mypy and ESLint pass.
- The page's terminal runs the game's bash; typed lines and their exit status reach the game
  (`Observation.commands`, goals read them, Rama reacts to them).
- Three short levels on real git: `liftoff-aboard`, `liftoff-flag`, `cargo-first`, with scenes,
  stars, par, command cards and decks; texts fact-checked in `docs/verification/orbit.md`.
- The Orbit page: map of sectors, level screen (zones, goals, Rama, VT323 terminal), scenes,
  completion dock, collection. Tiny5 headings. The old level and the old page modules are gone.
- termlab `firstcommit` is at 567ba04 (per-look font size, font/woff2).
- Team: named teammates engine and frontend, and the artist subagent (`.claude/agents/artist.md`)
  that whoever needs graphics calls.
- Waiting for the user: delete lessons, answer steps and the map guide (with map.js and the
  theme-time files), drop the empty `basics` chapter, keep the playground; and whether the dock
  should start small.
- Saves from before Orbit do not load: `deploy/docker/run reset`.

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
   `firstcommit shell` already uses it), and web's link on `p2/typed-commands` (the page's
   terminal runs `game.shell_command`, api.js checks `commands`, the smoke flow checks that
   every typed line comes back from `/api/observe`; helper job C is done). Next: timetravel
   wires live.js (its parse is 30b2e11, merged), waiting for the new frontend's design.
2. Before `p2/start` merges, its levels must add `COMMAND`, `PAR` and `CARD`, and take the typed
   lines in watch `(lab, state, typed)`, check `(lab, state, answer, typed)`, `solve` and the
   quest actions (Orbit levels, 3b52dbb). Chapter 1 "Git, GitHub and your first clone" (plan approved; written by the author on
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

Future ideas (the user, 2026-10-07):
- A "What just happened?" button: the game explains the repository's current state in plain
  words, from the facts it already reads, so a lost player has a way out without restarting.
- Publishing and its cost (a one-click download, or a hosted site with one sandbox per player):
  after the first playtests.
- Accessibility pass (screen readers, keyboard only, colour-blind checks, sounds never the only
  signal, text that survives browser zoom): after the content.
- Playtests with first-time players before building past the next five chapters.

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
