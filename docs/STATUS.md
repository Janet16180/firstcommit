# First Commit: status and handoff

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

## Phase 2b: visual explanations (in progress, 2026-10-06)

The user picked the time-travel theme (over metro) and asked for picture-first explanations
(AUTHORING 3.5: a figure from real git, at most three short sentences) and an interactive
playground: two people on one remote, each with the same buttons (edit, add, commit, push,
fetch, pull, status), common mistakes detected, then the same problem for real in the terminal.
There is no game story; the visuals are the creative part.

Pictures: a file is a page, the staging area an open box, a commit a closed box. The four
places are the working folder, the staging area, your repository and GitHub; Alex is an SVG
person, not an emoji. Every motion is drawn from the diff of two real snapshots.

Agents and branches (worktrees under `.scratch/wt/`):
- timetravel, `p2/theme-time`: the theme, motions (`TimeMotion.playMap`), the four places
  figure, the demo generator `tools/demo/`, and the page integration (live-map motion hook from
  metro's c156a29, the guide's button in the key, index.html).
- guide, `p2/theme-guide`: "How to read the map" as tiny figures served by `game.guide()`
  (`/api/guide`); its text is generated from `docs/drafts/map-guide.md` by
  `tools/guide_text.py --check`.
- share, `p2/theme-share`: "Share a file with Alex" (13 steps, `tools/demo/share.py`,
  `docs/drafts/share.md`); next, the two-person playground figure.
- playground, `p2/playground-design`: the playground's design and its mistakes table, recorded
  from real git (`docs/drafts/playground-errors.*`); then insight writes
  `explain(press, before, after)` from it.
- Merged into `phase-2-engine`: `firstcommit.playground` and `lab.py` (insight), `game.press`
  and the teammate in `observe` (core, d1d7726). web is adding `POST /api/press`.
- mapcheck re-runs every claim of every draft on git 2.43 (`.scratch/review/`). Order: four
  places revision 4, share revision 2, then the playground mistakes table.
- metro, `p2/theme-metro` and `p2/boxes-live`: the earlier metro look; the boxes and cardboard
  live-map variants wait for the user's choice.

Merged into `phase-2-engine` (fc8e000, 924 passed with Docker, mypy over `tools` too): the theme
in the live page (the map's motion, the guide's button in the key), the guide at revision 6, and
the Alex walkthrough at share revision 2, all fact-checked. Next for timetravel: four places
revision 5, then the four places replacing the "Three areas" table in the live page. The agents
keep working on their branches and merge `phase-2-engine` back.

Shared with the user (private artifacts): the Four Places Demo
(https://claude.ai/artifact/72KsUGhDae4pErRzU7Kzrv, published from `tools/demo/build.py` output
with the page skeleton stripped; the share walkthrough is left out until its check passes) and
Commit Shape Choice (https://claude.ai/artifact/GB9XGi8bZC5oz21zDja7du).

Waiting for the user: rings or boxes for commits in the live map (the lead recommends plain
boxes, one picture of a commit everywhere), and security L3.

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

## Backlog (decided later, not now)

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

## Next

1. Finish phase 2b (above): the page integration, `/api/press`, the playground figure and its
   explanations, each draft through mapcheck; merge the theme branches.
2. The user plays the template level with the new look; then merge `phase-2-engine` to `main`
   (ask first).
3. Chapter authors in parallel, picture first, each followed by a fact-checker. Chapter 1 has
   only the template level today.
4. The VM adapter (`vm/game.env`, `vm/guest-setup.sh`, wrapper) on termlab's VM.
