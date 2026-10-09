# Orbit: the new frontend and the short levels

The user approved a new look and level style on 2026-10-07: `docs/drafts/orbit-design.html`
("Gitnauta: learn Git in orbit"). It is a self-contained prototype, in Spanish, with git faked in
JavaScript. We keep its look, its screens and its level style, and drop its fake git: the player
types in our real terminal, and the game reads the real repository and the command log
(`Observation.commands`, merged in 1db934a).

This file is the contract between the team. The lead changes it; agents ask the lead when it is
wrong or missing something.

## What we keep from the design

- The pixel style in space: Pixelify Sans, Atkinson Hyperlegible and VT323, hard shadows, the
  colour tokens of its `:root` (light and dark), Rama the pixel robot.
- The map: sectors (chapters) with their mission nodes, a mission card with Play, the "coming
  soon" sectors, the command-card collection.
- The level screen: the four zones (workshop, cargo dock, vault, mothership) with the files and
  capsules that fly between them, the mission panel (brief, goals checked in order, hints that
  cost a star), Rama's comms line, and the terminal across the bottom.
- The completion dock at the bottom (stars, the lesson, Retry / Map / Next) instead of a modal,
  so the terminal and the zones stay visible.
- A level's scene (Rama's short animated explanation) the first time the level opens, with a
  button to replay it.
- Text in English. No emojis anywhere: stars and icons are drawn, not typed characters.
- Fonts and every image ship with the game (no Google Fonts or other network loads at play
  time); the fonts are OFL, keep their licence files next to them.

## The first three levels

The design's first three, on real git:

| Design id | Title | Scene | Goals, in order |
|---|---|---|---|
| 1-1 | Welcome aboard | intro | `ls` succeeded; `git status` was typed (it fails: the folder is not a repository yet) |
| 1-2 | Plant the flag | init | the folder is a repository; `ls -a` succeeded; `git status` succeeded |
| 2-1 | First cargo | stage | `mapa.txt` (English name chosen by the engine) is staged; `git status` succeeded |

In 1-1 the failed `git status` is the lesson: Rama explains that Git only works in a folder it
knows, and that the next mission creates one. Ids, file names and English text are the engine's
to choose, following AUTHORING.md.

## The records the page reads

Changes to `firstcommit.game`'s records, on top of what exists. Every field is always present.

- `LevelSummary` gains `command: str` (the short label, such as ``git init``) and
  `stars: int` (the best result, 0 while not done, else 1 to 3).
- `ChapterSummary` gains `blurb: str` (one line under the sector's name).
- `Status` gains `collection: list[CommandCard]` (one per finished level, in play order). A
  chapter with no levels is a "coming soon" sector; the page derives that from `chapters`.
- `CommandCard` is new: `{level: str, command: str, text: list[Block]}`.
- `LevelView` gains:
  - `command: str` and `par: int`;
  - `scene: list[{art: Art, text: list[Block]}]`, empty when the level has none;
    `Art` is a `Literal` of the scene pictures the artist has drawn (start with the design's:
    space, timeline, terminal, planet, flag, zones, conveyor);
  - `scene_seen: bool`;
  - `card: CommandCard`.
  The goals are the existing `steps` (watch steps), and the lesson shown in the dock is the
  existing `debrief`.
- `ActiveView` gains `commands: int` (lines typed since the level started) and `stars: int`
  (the stars still in play: 3, one less once a hint is used, one less once `commands` passes
  `par + 3`, never below 1).
- `CheckResult` gains `stars: int` (0 while unsolved) and `new_card: CommandCard | None` (set
  the first time the level is solved).
- `Observation` gains `reactions: list[Reaction]`, one per typed line Rama has something to say
  about, oldest first: `Reaction = {line: str, mood: "info" | "ok" | "warn" | "err", text:
  list[Block]}`.
- New route `POST /api/scene {level}` marks a level's scene seen and replies `{}`; `game.reset`
  forgets it.

Guarantees the page relies on:

- A goal can depend on what was typed: a level's watch and check functions receive every line
  typed since the level started, `(lab, state, typed)`, even after `observe` has returned them. The page keeps polling as now (`observe`, then `step(null)`
  for a watch step, then the automatic check).
- Reactions come from the game, never from the page. A reaction reads the typed line, its exit
  status and what changed in the repository; the same rule serves every level, and a level may
  add its own (1-1's `git status`).
- Stars are counted by the game; the page only shows them.
- Saves from before Orbit do not load: the error names `firstcommit reset` (or
  `deploy/docker/run reset`). The game is not released, so there is no migration.

## The user's decisions of 2026-10-07 (after the first three levels)

- XP stays, next to stars. Revised later the same day: a hint lowers the XP a play pays, it
  does not remove it all (stars still count as above); the hint's cost shown on the page says so.
- termlab may change as needed on its `firstcommit` branch (engine does it): a terminal font
  size option, so the page's terminal can use VT323 at the design's size, and `font/woff2`.
- Each Orbit chapter gets a flashcard deck.
- The old version goes: the level `basics-first-commit`, its deck, and the time theme's page
  modules. Git history keeps them. Done on 2026-10-08, with the old lessons and the map guide.
- The headings get another pixel font with a capital C that cannot be read as an O (artist
  proposes, frontend ships it).

## The user's decisions of 2026-10-07 (evening)

- Scope: the game teaches Git and GitHub only. No lessons on the terminal, Linux or editors;
  shell commands appear only where a Git level needs them, and no editor ever traps a player.
- Spanish: every player-facing text exists in English and Spanish, with a language choice.
- Terminal: syntax highlighting as the player types, with ble.sh shipped with the game.
- Sounds (8-bit, Web Audio), a more readable font for buttons, and infographics instead of the
  command collection (all commands; Git's states and how files move between them).
- Every few levels, a challenge without guidance: the end state only, never the steps, mixing
  ideas from earlier chapters. The next five chapters come from a three-way debate (teacher,
  incidents, gamer) decided by the lead.
- Later, in this order: playtests with first-time players; accessibility; publishing.

## Chapters 3 to 7

`docs/drafts/chapters-3-7.md` holds the decision from the debate: the rules every level follows,
the challenges, the 23 essential levels in two waves, and what the engine, the page and the art
need. Wave 1 (11 levels, through Base 7) is merged first, for the playtests with new players.

## Who does what

Two named teammates, engine and frontend, plus the artist subagent they call. Each teammate works in its own worktree on its own
branch from `phase-2-engine`, never pushes, never merges, and ends each job with one short report
to the lead. The lead reviews, runs the slow and Docker tiers, and merges.

- **engine** (`p2/orbit-engine`): everything outside `web/static`. The records above, with
  `tests/js/records.json` and `tests/test_page_scripts.py` kept in step; the save changes (best
  stars, scenes seen, the level's typed lines); stars; reactions; `/api/scene` in routes.py; the
  three levels with their tests and verification notes. First milestone: the records commit,
  filled for the existing level, so the frontend can build on it.
- **frontend** (`p2/orbit-frontend`): `web/static` except the art files, and `tests/js`. The
  page's layout, screens, routing, api.js shapes, the terminal at the bottom, the dock, the
  zones drawn from real snapshots and lit from typed lines (TimePlaces' parse, 30b2e11). Starts
  with the visual shell, which needs no new record, then rebases on engine's records commit.
  Replaces the time theme; the old modules stay until the new page plays all three levels,
  then one commit removes them (removed on 2026-10-08).
- **artist** (`.claude/agents/artist.md`): a subagent, not a teammate. Whoever needs a new
  or changed image or animation (usually frontend) calls it directly with what to draw and
  where it appears; it draws on its own and reports back to its caller. It owns only
  `web/static/art-*.js` and `web/static/art-*.css`, with their node tests: Rama, the sprites,
  the scene pictures and the keyframe animations, in the design's style. The caller uses what
  it exports and never draws its own art. It commits on the caller's branch, so its work
  reaches the lead with the caller's.

## Rules for everyone

- `~/.claude/CLAUDE.md` and AUTHORING.md: TDD, small commits with plain messages and no
  trailers, the fast tier before each report (`uv run pytest -q -m "not slow and not docker"`,
  `node --test` for page modules, `uv run ruff check`, `uv run mypy`).
- Tests that start shells get a temporary HOME and HISTFILE (the `typist` fixture).
- Change only your own files. When another file must change, ask the lead.
