# First Commit: status and handoff

Read this first when resuming, then `docs/DESIGN.md` and `AUTHORING.md`.

## How we work

- The method is `~/learning/GAME_METHODOLOGY.md`: the lead (main session) writes contracts, splits
  work into agents with disjoint file ownership, verifies every claim on disk, integrates and
  reports. Correctness first; every chapter gets an independent fact-checker.
- Engineering rules: `~/.claude/CLAUDE.md` and `AUTHORING.md` section 2.
- Git: `main` holds reviewed work; each phase is a branch (`phase-2-engine`), each agent a branch
  `p2/<name>` in a worktree under `.scratch/wt/<name>` (with a `termlab` link next to the
  worktrees so `../termlab` resolves). Small commits, plain messages, no trailer, never push.
- termlab (`~/learning/termlab`) is never changed without the user's go-ahead (user, 2026-10-06).

## Decisions

See `docs/DESIGN.md` section 2. Also, 2026-10-06: Docker is the front door for new hires, WSL
direct for development, termlab's VM later (the lead's call, delegated by the user).

## Phase 2 (in progress, branch `phase-2-engine`)

Lead, done: skeleton, tooling, contracts (`gitcmd`, `kit`, `save` records, `repomap`, `changes`,
`markup`, `demos`, `game` API, `cards.CardKind`, `chapters`), `AUTHORING.md`, tests for `gitcmd`
and `kit`. Found and fixed: the page's polling could take `index.lock` through `git status`;
every game git command now runs with `GIT_OPTIONAL_LOCKS=0` (git(1)), tested red then green.

IN FLIGHT (launched 2026-10-06; each brief is in the lead's session; relaunch from these specs
after checking the branch's log):

| Agent | Branch | Owns | Spec in short |
|---|---|---|---|
| insight | `p2/insight` | `repomap.py`, `changes.py`, `demos.py` + tests | snapshot via plumbing (three areas as blob ids), objects, "what just happened" events, lesson frames with `demos.environment` |
| core | `p2/core` | `save`, `score`, `cards`, `markup`, `runner`, `game`, `cli` + tests, `tests/test_levels.py`, `tests/test_decks.py`, `tests/test_layers.py`, `tests/fixtures/markup.json` | the game layer per DESIGN section 7; exception for "no level in progress" -> 409 |
| web | `p2/web` | `web/routes.py`, `web/static/*`, `tests/test_routes.py`, `tests/js/*`, `.eslintrc.json` | termlab routes and terminal; level-agnostic page; neutral `map.js` with a theme hook |
| docker | `p2/docker` | `deploy/docker/*`, `.dockerignore`, `tests/test_docker.py`, README "Play with Docker" | ubuntu:24.04 by digest, git 2.43, `--network host`, named volume, `run` script |
| author | `p2/level` | `levels/basics_first_commit.py`, `content/cards/basics.toml`, `docs/verification/basics.md`, `tests/levels/` | the template level "Your first commit" |

Integration order: insight -> core -> web -> author -> docker smoke. Merge insight into core,
web and level as soon as it lands.

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

## Backlog (decided later, not now)

- repomap `outer` field (path to an enclosing repository, e.g. ".."), proposed by insight, for a
  generic "Git sees a repository one folder up" hint on the map. Deferred: no second use yet.
- termlab's `snippets.run` decodes output as text with universal newlines, so a `\r` becomes
  `\n`. demos works around it (writes output to a file read as bytes) without touching termlab.
  A termlab option to keep raw output would be the user's call.

- For the `history` chapter author: long `git log` and `git diff` output still opens the pager
  (`less`); teach `q`, Space and `/` there. Short output no longer stops in the pager
  (`core.pager = less -FRX` in the game's config, git's own default when LESS is unset).

- repomap does not see uncommitted changes inside a submodule (`git status` reports them). No
  chapter teaches submodules yet; revisit if one does.

## Level polish for "Your first commit" (from the checker's blind playtest)

- A beginner who commits before setting a name sees git's identity error, which the lesson never
  shows (the lesson environment sets an identity). Mention it on the commit slide or step.
- A bare `git commit` opens an editor (nano). The nudges give the full `-m` command, but the
  second basics level ("A message that helps") should teach the editor: how to write, save, quit.
- `readme.md` in lower case gets "There is no `README.md`"; point at the letter case.
- Expect `git init project` typed inside `project` (the briefing says "turn the project folder
  into a repository"); it now has its own nudge, but consider rewording the briefing.

## Next

1. Integrate and verify phase 2 (all gates in WSL and in the image; play the level end to end).
2. A fresh fact-checker for the basics level and cards.
3. Theme prototypes on the template level: metro map and time travel; the user picks.
4. Security review of the routes, the terminal environment and the container.
5. Chapter authors in parallel, each followed by a fact-checker.
6. The VM adapter (`vm/game.env`, `vm/guest-setup.sh`, wrapper) on termlab's VM.
