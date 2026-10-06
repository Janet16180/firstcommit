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

NEXT for phase 2, before merging to `main`:
1. An independent code review of `phase-2-engine` against `~/.claude/CLAUDE.md` and DESIGN
   section 7 (report only).
2. A security review of the game's routes, terminal environment and container (report only).
3. Theme prototypes on the template level: metro map and time travel, for the user to pick.

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
