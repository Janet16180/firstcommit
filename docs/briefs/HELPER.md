# Brief for the helper account

You are helping build First Commit, a browser game that teaches Git to new hires. The project
is `.`. Another session (the lead) runs a small team that
does the visual work; you take four engine and page-wiring jobs that need no graphic design.
Do them one at a time, in the order below.

## Read first

- `~/.claude/CLAUDE.md`: the engineering rules (TDD, type hints, NumPy docstrings, early returns
  only for bad input, one return at the end, let errors raise, design by contract).
- `AUTHORING.md` section 2, and `docs/STATUS.md` "How we work".
- `git log --oneline -15` on the job's start commit, to match the commit style.

## Rules

- One job at a time. Each job gets its own branch and worktree, made from the main checkout:

  ```
  cd .
  git worktree add .scratch/wt/helper-<job> -b p2/helper-<job> <start commit>
  cd .scratch/wt/helper-<job>
  ```

  `uv run` sets up the worktree's environment on first use; `../termlab-firstcommit` resolves
  through the link already in `.scratch/wt`.
- Never push, never merge into `phase-2-engine` or `main`, never touch other branches,
  worktrees or `~/learning/termlab*`, never delete a branch. The lead reviews and merges.
- Change only the files the job lists and their tests. If another file must change, stop and
  say why in your report.
- Tests first: write the failing test, see it fail, then the code. One test file per module.
- Run only the fast checks: `uv run pytest -m "not slow and not docker"`, `uv run ruff check`,
  `uv run mypy`. No Docker, no browser, no Playwright: the machine is shared and the lead runs
  those on merge.
- A test that starts a real shell gives it a temporary HOME and HISTFILE. Job C's start commit
  has a fixture for this in `tests/conftest.py`; lessons already run with their own HOME
  (`demos.environment`). Never let a test touch the user's `~/.bash_history` or any file in
  their home.
- Commits: small, a plain one-line subject like the repo's, no `Co-Authored-By` or any other
  trailer, no emojis.
- Stuck on something complex after a real try: stop, write down what blocks you and what you
  would do with a go-ahead, and move on to the next job.
- When a job is done, write `.scratch/reports/helper-<job>.md` (it is not committed): branch,
  final commit hash, the fast-tier counts, what changed in three to five lines, and what the
  lead should look at closely. Then start the next job.

## Job A: a lesson's practice GitHub built by a Python function

Start commit: `f115816` (branch `p2/insight`). Job name: `lesson-builder`.

Today a level's `LESSON_GITHUB` is text: shell lines that `demos.lesson` runs in the lesson's
shell before the first slide, to create the bare repository `github/project.git`. The decision
is to make it the same Python function the level's `setup` uses to build `lab.github`, so the
lesson and the level build one GitHub from one place.

The new contract: `LESSON_GITHUB: Callable[[Path], None] | None = None`. The function gets the
path of the bare repository to create (`<lesson home>/github/project.git`); its parent folder
exists and the repository does not. It makes commits through `kit.git` with `author=` and
`when=`, so the hashes are the same on every run. Chapter 1's real one is `build_github` in
`src/firstcommit/levels/start_git_and_github.py` on `p2/start` (6f655bb), with
`build_history` in `levels/_start.py`; read them, but do not edit that branch.

Change:
- `src/firstcommit/demos.py`: `lesson(slides, github)` takes the function or None, calls it
  before the shell starts, and the shell runs only the slides. Keep what the lesson gives
  today: the `start` frame (the places after GitHub is built, no commands), `github` on every
  frame, the `RuntimeError` when no bare repository is left at `github/project.git`, and the
  cache (a function is hashable).
- `src/firstcommit/runner.py`: `Level.lesson_github` holds the function or None; a level whose
  `LESSON_GITHUB` is neither gets the problem "LESSON_GITHUB must be a function (Path) -> None".
- `src/firstcommit/game.py`: pass it through, if the type changes anything there.
- `AUTHORING.md`: the `LESSON_GITHUB` line in the module table and the paragraph with its
  example (section 3.5), rewritten for the function, the example using `kit.git`.
- Tests: rewrite the existing `LESSON_GITHUB` tests in `tests/test_demos.py`,
  `tests/test_runner.py` and `tests/test_game.py` for the function form, including a function
  that creates nothing (RuntimeError) and a value that is not a function (the runner's problem).

Done when no shell lines are left for `LESSON_GITHUB` and the fast checks pass.

## Job B: move the clone check into kit

Start commit: `6f655bb` (branch `p2/start`). Job name: `clone-check`.

`cloned_from_github(lab, folder)` in `src/firstcommit/levels/_start.py` tells whether a
repository's `origin` is the lab's practice GitHub. Move it, unchanged in behavior, to
`src/firstcommit/kit.py` (approved by the lead), with its tests moved from
`tests/levels/test_start_helpers.py` to `tests/test_kit.py`. Every caller (`clone_move` in
`_start.py`, and any other `grep` finds) uses `kit.cloned_from_github`. Write the tests in
`tests/test_kit.py` first and see them fail before moving the function.

Done when `levels/_start.py` no longer defines it and the fast checks pass.

## Job C: the page's terminal runs the game's own shell

Done on `p2/typed-commands` (2026-10-07); do not start it.

Start commit: `d053403` (branch `p2/core`). Job name: `terminal-shell`.

The game now has its own bash (`game.shell_command()`: prompt `project $ `, and a log of every
command typed, read back as `Observation.commands`). termlab's `TerminalSettings` has a `shell`
option for it (already in `~/learning/termlab-firstcommit` at 01ee4e8; do not change termlab).
The page's terminal does not use it yet, so it still opens the user's own shell.

Change:
- `src/firstcommit/web/routes.py`: `TERMINAL` gets `shell=game.shell_command`, with a test in
  `tests/test_routes.py` that the terminal's command is the game's shell.
- `src/firstcommit/web/static/api.js`: the `OBSERVATION` shape check gets
  `commands: list of {line: text, status: number}`, with the helpers the file already uses.
- `tests/js/records.json`: the observation sample gets a `commands` list, for example
  `[{"line": "git add README.md", "status": 0}]`. `tests/test_page_scripts.py` checks the
  samples against `game.Observation`, and the node tests in `tests/js` use them.

Not in this job: lighting the four places from typed lines (`live.js`); a teammate does that
after you.

## Job D: a "Restart level" button while playing

Start commit: the tip of `phase-2-engine` when you start (`git rev-parse phase-2-engine`; put
that hash in your report). Job name: `restart-level`.

While playing a level, the page has only "Leave this level", yet some hints already say
"Restart the level" (for example after `git init` in the wrong folder). Add a button with that
wording next to Leave.

Change:
- `src/firstcommit/web/static/practice.js`: a "Restart level" button beside `.leave`, with the
  same classes (`btn btn-ghost btn-small`; no new CSS). It asks first with `Dialog.confirm`:
  title "Restart this level?", text "Your practice repository is built again from the start.
  Your progress is kept.", confirm "Restart", cancel "Keep playing". On yes, it stops the run
  the way `leave` does and calls a new `onRestart` option.
- `src/firstcommit/web/static/level.js`: pass `onRestart: () => start(page, null)`.
  `game.start` already ends the level in progress and builds a fresh lab, and the page's
  terminal is keyed by `active.started`, so the new start gets a new shell in the new folder.
- Tests: `tests/js/practice.test.js` (follow the existing Leave test), and
  `tests/js/level.test.js` for the wiring: restart confirmed starts the level again; cancelled
  changes nothing.

Not in this job: the map page's "Start over", which erases all progress and stays as it is.

## After the four jobs

Write `.scratch/reports/helper-done.md` with the four branches and hashes, and stop.
