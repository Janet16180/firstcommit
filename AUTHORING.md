# Authoring content for First Commit

First Commit teaches Git to new hires who are starting out: some have never used Git, some have
barely used a terminal. Each chapter is made of:

| Form | Where | Purpose |
|---|---|---|
| Levels | `src/firstcommit/levels/<chapter>_<slug>.py` | Scene, guided quest or challenge on a real repository, and debrief |
| Cards | `src/firstcommit/content/cards/<chapter>.toml` | Spaced-repetition flashcards, including "predict the output" |
| Notes | `notes` in the same TOML file | A one-page cheat sheet for the chapter |
| Verification log | `docs/verification/<chapter>.md` | One line per claim, card and level: how it was verified |

Chapter ids are the keys of `src/firstcommit/chapters.py`. Everything a chapter owns starts with
its id, so authors never touch each other's files.

---

## 1. Correctness comes first

A learning game that teaches something false is worse than no game. The target is **Ubuntu
24.04 with its git 2.43** (the Docker image pins it; WSL's Ubuntu 24.04 ships it).

For every sentence that states a fact, in a scene, step, briefing, hint, debrief, card or note:

1. **Check a primary source** and name it in the card's `source` or in the verification log:
   - the installed manual pages: `man git-commit`, `man gitglossary`, `man git` (environment
     variables), `man gitignore`, `man gitattributes`...; quote with
     `man -P cat git-commit | grep -n ...`;
   - git's release notes in `/usr/share/doc/git/RelNotes/` ("since Git 2.23");
   - git-scm.com: the reference and the Pro Git book (2nd edition);
   - docs.github.com for anything about GitHub;
   - FIPS 180-4 for SHA-1 and SHA-256.
2. **Run an experiment** whenever the claim is observable, then make it permanent: a `predict`
   card or a `verify` snippet re-checks it on every test run (section 3.5).
3. **Do not trust memory** for defaults, flags, numbers, limits or edge cases.
4. **Never quote git's human-readable messages** (hints, errors, `status` wording) in text you
   write: they change between versions. Checks never parse them (section 3.4).
5. **Say when something depends on a version or a setting** ("since Git 2.23", "unless
   `pull.rebase` is set"), and avoid claims that differ between Linux, macOS and Windows unless
   the card is about that difference.
6. **GitHub changes its pages often.** Describe what GitHub does (a pull request, a required
   check, the three merge methods), not where its buttons are or what colour they have.
7. **Name no company, real person or internal URL.** Teammates in the story are fictional and
   use `@example.com` addresses.
8. **Scope every absolute.** "Only", "never", "always", "every" and "after a commit" are almost
   always false for some option (`git commit -a`, `git commit <file>`, `git revert`). Check the
   options that change the claim, then scope it to the exact command you teach ("a plain
   `git commit`"). The options that broke claims in the first level, to check every time:
   `git commit -a`, `git commit <path>`, `--author` and the `GIT_AUTHOR_*` variables, a short
   hash where git needs a full one (`git fetch`), `core.hideDotFiles` on Windows, and commands
   other than `commit` that make commits (`merge`, `revert`, `cherry-pick`).
9. **Every command you write is complete and runnable as written.** `git config --global
   user.name` without a value only reads the setting. Placeholders are obvious and safe to paste
   (`"Your Name"`).
10. **Describe output as the player's terminal shows it.** Some output differs on a terminal:
    `git log --oneline` adds `(HEAD -> main)` there (`log.decorate`, git-config(1)). The player
    sees terminal output; check prose against a real terminal, not against memory or a pipe. To see
    what a terminal shows from a script, run the command under `script` with the pager off:
    `GIT_PAGER=cat script -qec 'git log --oneline' /dev/null` (without `GIT_PAGER=cat` the pager
    waits for a key and the command hangs).

## 2. Code standards (all Python in this repo)

- Simplicity first: flat over nested, guard clauses at the top, one normal return at the end.
  Functions over classes; frozen dataclasses and `TypedDict`s for records.
- Type hints everywhere (mypy strict); NumPy-style docstrings on every function.
- Do not catch exceptions unless you handle a specific, expected case. Never catch bare
  `Exception`.
- Preconditions are bug detectors: a guard raises for a state that should be impossible. A wrong
  answer, an unsolved level or garbage input is an expected outcome: compute the result with an
  `if`/`elif` chain and return once at the end.
- Test names are sentences about behaviour and need no docstring; test helpers do.
- Minimal comments, only for a non-obvious why. No section dividers, no emojis anywhere.
- Standard library only at runtime, plus termlab.
- The page tests (`tests/js`) run on Node 24 LTS or newer: the test image pins Node by version and
  SHA-256 (`ARG NODE_VERSION` in `deploy/docker/Dockerfile`), and `tests/test_page_scripts.py`
  fails on an older local Node. Run them as `node --test tests/js/*.test.js` (Node 24 reads a
  folder argument as a file). Drive timers with a `timers` option and `createClock()` from
  `tests/js/load.js`, never `mock.timers`. To move to a newer Node, change the version and both
  checksums from that release's `SHASUMS256.txt` on nodejs.org.
- **Nothing in the package may know where it runs** (WSL, Docker or a VM): it reads only
  `FIRSTCOMMIT_HOME` and the port it is given.

Before you finish a change:

```
uv run ruff check
uv run mypy
uv run pytest -q
eslint src/firstcommit/web/static tests/js
uv run firstcommit --help
```

## 3. Levels

### 3.1 What makes a good level for a beginner

- **Explain before you ask.** The first level of a chapter has a guided quest, whose scene and
  steps show the new idea before the player uses it; later levels are challenges that reuse
  what the quest taught.
- **One new idea per level.** Name it in the scene and the briefing, practise it in the quest,
  use it in the challenge, explain it again in the debrief.
- **A small story, not trivia**: "a teammate pushed while you were working", "the build folder
  made the repository huge", "you committed on the wrong branch".
- **Real Git only.** The player works on a real repository in a real terminal; the game never
  fakes what git would do. The terminal's prompt is the game's (the folder's name, as in
  `project $ `), and the commands typed there are logged in the game home only, so the figure
  shows the command that really ran.
- **No editor ever opens.** The game's configuration sets `core.editor = true`: a bare
  `git commit` stops and commits nothing (Rama then teaches `-m`), while `git merge`, a merging
  `git pull`, `git revert` and `git commit --no-edit` keep git's prepared message. Write `-m` and
  `--no-edit` in levels and cards; `git tag -a` needs `-m` too.
- **Mistakes are expected.** Wrong answers get a nudge that points at what to look at, never the
  answer and never blame.
- **The check notices success by itself.** Most levels are checked against the repository as the
  player works; a typed answer is for questions about what the player saw.
- **The debrief teaches**: what happened, why Git works that way, where it matters at work, and a
  few "commands to keep".

### 3.2 Safety rules (hard requirements)

- Everything a level creates is under its lab folder. Never write anywhere else.
- No network: the "GitHub" of a level is the bare repository at `lab.github`. Never use an
  `https://`, `ssh://` or `git@` URL, not even in a remote that is never used.
- A clone of `lab.github` reaches it by a relative path: right after cloning, run
  `git remote set-url origin <lab.github_url(clone)>` (`kit.setup_playground` does it for the
  playground's two clones). Otherwise git prints the player's absolute folders in push and pull
  output and writes them into merge commits. `git remote -v` then shows `../github.com/moonbase/project.git`:
  the game's GitHub is a folder next to the player's, and the remote chapter says so.
- Pull requests and reviews exist only on GitHub, so the game keeps them as records beside the
  bare repository (`lab.pulls`, read and written with `save.load_pulls` and `save.write_pulls`),
  and `firstcommit.pulls` opens, reviews and merges them with real git on `lab.github`
  (`merge-tree`, `commit-tree`, `update-ref`), mirroring `refs/pull/<n>/head`. Never fake a
  merge by editing files, and never fake the `gh` tool.
- A level with two people on one remote builds them with `kit.setup_playground(lab)` and
  prepares a state with `kit.press(lab, person, button)`, the same real commands the page's
  buttons run.
- Run git only through `kit.git` / `kit.git_run` (the game's isolation: the player's own
  configuration can never change a level, and a lab never falls through to a repository above
  it). The player's real `~/.gitconfig` and repositories are never read or changed.
- No hooks, no filters, no aliases that run programs, apart from the stand-in GitHub's one
  `post-receive` hook that `kit.on_push` writes for Alex. No root.
- Build every repository with git commands (`init`, `commit`, `clone` from another lab
  repository). Never copy, unpack or download a `.git` folder: its configuration could name
  programs that git runs. The game's own git commands refuse the known ones (`gitcmd.NO_PROGRAMS`),
  but the player's shell does not.
- Under 50 MB of disk per lab (the binary-files level included).

### 3.3 Module contract

File `src/firstcommit/levels/<chapter>_<slug>.py`. Its id is the file name with `_` turned into
`-` (`liftoff_aboard.py` is `liftoff-aboard`), and its chapter is the part before the
first `_`. A new level also goes into `PLAY_ORDER` in `chapters.py`, at its place on the map: the
map numbers each level by that place in its chapter (`tests/test_chapters.py` checks that every
level is listed once).

```python
from firstcommit import kit

TITLE: str                    # short and concrete: "Plant the flag"
DIFFICULTY: int               # 1 first steps, 2 solid, 3 stretch
XP: int                       # guide: 100 for 1, 150-200 for 2, 250-300 for 3
COMMAND: str                  # the short label on the map and the level: "git init"
PAR: int                      # lines a good play types; more than PAR + 3 costs a star
CARD: kit.CommandCard         # the command card the player collects: command and what it does
SCENE: list[kit.SceneFrame] = []        # optional; Rama's scene the first time the level opens
VIEW: View = "station"                  # optional; the level screen's main view (records.View)
TAPE: bool = False                      # optional; True to show the black box's tape of HEAD's moves
PICTURES: kit.Pictures | None = None    # optional; kit.pictures("chain", folder=True, ...): the teaching pictures and their marks
TARGET: kit.Target | None = None        # optional; a challenge's target chart: commits by label, names on them, HEAD's name
REACTIONS: list[kit.ReactionRule] = []  # optional; tried before the shared ones
EVENTS: list[kit.LevelEvent] = []       # optional; changes the level makes during the play
CHALLENGE: bool = False                 # optional; True for a challenge (any order, no guidance)
QUEST: list[kit.Step] = []    # optional; the first level of a chapter has one
BRIEFING: str                 # the situation and what counts as success
QUESTION: str = ""            # optional; set it when the level is solved by a typed answer
PLACEHOLDER: str = ""         # optional; example shape of that answer ("a short hash")
HINTS: list[str]              # 2-4, from a nudge to the answer; each lowers the XP (score.py); the last shows every line
DEBRIEF: str                  # shown once solved

def setup(lab: kit.Lab) -> kit.State: ...
def check(lab: kit.Lab, state: kit.State, answer: str | None, typed: kit.Typed) -> kit.Verdict: ...
def solve(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None: ...
```

- **`setup(lab)`** builds the starting point in `lab.project` (a repository or an empty folder)
  and, for levels with a remote, `lab.github`, then returns a JSON-serialisable state. The lab
  folder exists and is empty. Make commits with `kit.git(..., author=..., when=...)` so their
  hashes are stable when text refers to them, and randomise what the player must find out when
  a fixed answer could be memorised. Store answers as `kit.digest(...)`, never in clear text.
- **`typed`** is every line typed in the game's terminal since the level started, oldest first,
  each with its exit status (`kit.Command`), even lines an observation already showed. A goal
  that depends on what the player typed reads it with `kit.typed(typed, r"git status\b", "ok")`
  (a regular expression matched at the start of the line, and how it ended) or
  `kit.after(typed, r"git init\b")` (the lines after the last one of those that worked). Prefer
  the repository when it can tell: typed lines are for goals such as "you looked with `ls`".
- **`check(lab, state, answer, typed)`** reads the lab and decides. It must not change anything (no
  `add`, no `commit`, no `gc`): read with `kit.snapshot(lab.project)` and read-only commands
  through `kit.git_run`. It is called every couple of seconds while the player works, with
  `answer=None`, and must stay fast and survive any state the player can create: a missing
  folder, a deleted `.git`, a detached HEAD, a merge in progress, garbage answers.
- **Stars.** A solved play earns 3 stars, one less once a hint is used and one less once the
  lines typed in the game's terminal since the level started pass `PAR + 3`, never below 1
  (`score.stars`). Set `PAR` to the lines a player following the level types.
- **XP.** A first solve pays the level's `XP`, less 15% of it for each hint revealed, but never
  less than half (`score.level_reward`); the hint view shows what each hint took off. A replay
  pays nothing.
- **`SCENE`** frames each name a picture the page draws (`kit.Art`) and say one or two short
  sentences. **`CARD`** says what its command does, scoped like any claim. Neither is filled
  from the state: both are shown before the level starts.
- **`VIEW`** is the view the level screen opens on (the view ladder of
  docs/drafts/chapters-5-9.md). The page plays a view's birth the first time a level opens on
  it; the game remembers the views seen (`game.see_view`).
- **`REACTIONS`**: what Rama says about a typed line (`firstcommit.reactions`). A rule matches
  the start of the line (a regular expression), how it ended (`outcome`), an event kind of what
  changed (`event`) and what is true afterwards: a repository is there (`repository`), something
  is staged (`staged`), a remote is named (`remote`), the working folder holds files Git ignores
  (`ignored`), the player is on a given branch (`branch`). A rule may carry a `moment` the page plays (`records.Moment`). The first rule
  that fits speaks; a level's rules come before the shared `reactions.RULES`, so add one only
  when the level can say something more precise.
- **`EVENTS`**: `kit.LevelEvent(id, run, goal="")`. `run(lab, state)` makes a real change with
  `kit.git` or `kit.press` (Alex pushes, a build folder floods the workshop). With no `goal` it
  runs when the level starts, so no line the player types can meet the lab without it, while the
  page's first look still shows the lab as it was before it; with a quest step's id, right after the
  player reaches that goal. The page then animates the change like any other. Each runs once per
  play, and `check` must hold whatever moment the player reaches.
- **`CHALLENGE = True`** makes the level a challenge: its `QUEST` holds only watch steps, the
  goals, written as end states and met in any order; the map shows it as a boss node; its card
  stays hidden until it is solved; and Rama says only what has mood `warn` or `err`. Hint 1
  names the chapters to recall, hint 2 the ideas. A challenge combines at least two earlier
  chapters and teaches nothing new.
- **Lost work is said, not hidden.** When the facts `setup` saved in the state show the player's
  work is gone for good (a file whose only copy was deleted, commits no ref or reflog reaches),
  `check` returns `kit.Verdict(False, message, lost=True)`: the message says what was lost, and
  the page offers to start the level again. The game runs `check` on every automatic poll, so a
  loss is reported at once, even during a guided quest.
- **The last hint gives the whole answer**: a line of prose, then every line that solves the level,
  in order, each on its own `$ ` line, exactly as the player types it (no comments). A player who
  is stuck can always finish. `tests/test_levels.py` types those lines in the lab, one shell
  folder carried from line to line as `cd` leaves it, and asserts every goal passes and `check`
  solves the level; answers and predictions come from `QUEST_ACTIONS`. In a challenge it comes
  after the hints that name the chapters and the ideas.
- **`QUESTION`** is for levels whose goal is something the player finds out ("which commit
  introduced the bug?"). Without it, the page offers no answer box and the level is checked
  against the repository only, with `answer=None`.
- **`solve(lab, state, typed)`** is the reference solution the tests use. It plays like a player:
  ordinary git commands through `kit.git` in `lab.project`, never a stored answer, and each line
  a goal reads typed with `typed.append(kit.type_line(lab.project, "ls"))`, which runs it in bash
  with the game's git and records its exit status. It returns the answer to submit, or None for
  levels checked against the repository.
- **`QUEST`** steps happen in the same lab, in order, and lead to the level's goal, so finishing
  the quest usually solves the level. The server enforces the order. While the quest is
  unfinished, the page's automatic check never ends the level, even when `check` would pass, so
  the player always reaches the last step; a check the player asks for may still solve it
  early. A step is one of three types (`kit.Step` names the three together), each carrying
  exactly what it needs:
  - `kit.AnswerStep(id, text, question, check, command="", placeholder="", more="")`:
    `check(lab, state, answer) -> Verdict` judges the player's answer;
  - `kit.WatchStep(id, text, watch, command="", more="")`: `watch(lab, state, typed) -> Verdict` passes
    once the lab shows the step was done (polled like `check`; same rules);
  - `kit.ReadStep(id, text, command="", more="")`: the player reads, then continues.
  - `kit.ChoiceStep(id, text, question, options, reveal, command="", more="")`: a prediction,
    two or three `options` the page shows as buttons; any option passes at no cost, and `reveal`
    says what really happens. At most one per guided level, where a named myth breaks; a checked
    answer (a hash, an author) is an answer step. Its `QUEST_ACTIONS` entry returns one option.

  Every step may carry `more`: text the page folds under a closed "More" below its text, for
  detail the step does not need, and `look`: commit subjects or `"HEAD"` the page rings in gold
  while the step is current, in a level with `PICTURES`.

  A watch's message is shown live, after every poll, while the player works: write it as the
  next thing to do ("`README.md` is in the working folder; stage it with `git add`"), never as
  an error. One suggested `command` per step: when a task needs two commands, make two steps.
- Text fields may contain `{{key}}` placeholders, filled from the state. In a step's `command`,
  each value is filled as one shell word (`shlex.quote`), so a value read from a repository can
  never run as a second command when the player presses Enter.
- The message of a `check` or a `watch` is shown as it is: it is never filled, because it may
  hold names the player chose (a file named `{{answer}}` must not reveal `state["answer"]`).
  Build it with the values it needs, and put each name the player chose through `kit.code`.
- Every message a `check`, a `watch` or a reaction rule gives is a **module constant**
  (`STAGED = "..."`), so its Spanish can be found by name (section 3.7).

### 3.7 Spanish texts

The game speaks English or Spanish, as the player picks. A level's Spanish lives next to it in
`levels/<chapter>_<slug>_es.py`, which is never read as a level:

```python
from firstcommit import kit

TITLE: str
BRIEFING: str
QUESTION: str                 # only when the English module has one; PLACEHOLDER likewise
HINTS: list[str]              # as many as the English HINTS
DEBRIEF: str
CARD: str                     # the command card's text; its command stays as it is
SCENE: list[str]              # one text per scene frame; the pictures stay
STEPS: dict[str, kit.StepText]  # one per quest step, by step id
STAGED = "..."                # one constant per English message, with the same name
```

`kit.StepText(text, more="", question="", placeholder="", options=(), reveal="")` holds a step's
texts, with exactly the fields its English step has; a prediction's options keep their English
values (the page sends them back), and only their shown text is translated. `runner.load`
refuses a sibling that lacks a text or has one the English module does not, and names it.
`tests/test_levels.py` checks that every message a check or a watch gives on the walk has its
Spanish, and `tests/test_translations.py` that every Spanish text keeps the shape of its
English: the same `{{placeholders}}`, code spans and commands, and as many paragraphs and
bullets.

The shared reactions' Spanish is `reactions_es.py`, a deck's `content/cards/<chapter>.es.toml`
(section 4.1), the chapters' names and blurbs sit next to the English in `chapters.py`, and the
game's own messages in `game.SPANISH`. The changes the page animates and the playground's
explanations stay English.

Write the Spanish as a Latin American teacher would, not word for word, with the words of
`docs/i18n-glossary.md` (section 7). Commands,
file names, branch names, commit messages and git's own output stay as they are.

### 3.4 Reading the lab

`kit.snapshot(path)` returns the repository as the page shows it (`firstcommit.repomap.Snapshot`):
commits, refs, HEAD, the current branch, an operation in progress, and every file's blob id in
the working folder, the staging area and HEAD. Checks and watches should read the snapshot, so
what the player sees and what the game decides cannot disagree. Use `kit.git_run` for anything
else, with plumbing commands (`rev-parse`, `cat-file`, `for-each-ref`, `ls-files`,
`status --porcelain=v2`) whose output is meant for programs. Never parse porcelain text meant
for people.

| Helper | Use |
|---|---|
| `kit.git(cwd, *args, author=, when=, stdin=)` | run git; returns stdout; raises if git fails (setup, solve) |
| `kit.git_run(cwd, *args, ...)` | run git; returns the result whatever the exit status, even when `cwd` was deleted (checks) |
| `kit.snapshot(path)` | the repository in a folder, as the map shows it (`kit.Snapshot`, `kit.FileEntry`, `kit.Commit`, `kit.Ref`) |
| `kit.version(entry, area)` | a file's id and mode in `"head"`, `"index"` or `"folder"`; two areas agree only when their versions are equal (`chmod +x` is a change) |
| `kit.staged(snap)`, `kit.unstaged(snap)`, `kit.untracked(snap)`, `kit.nested(snap)`, `kit.conflicted(snap)`, `kit.mode_changed(snap)` | the paths `git status` lists as changes to be committed, changes not staged (modified, deleted or type changed), untracked files, repositories nested in the folder, unmerged paths, and changes of the executable bit alone; each file's `index_change` and `folder_change` hold the same classification |
| `kit.Person`, `kit.GAME` | commit identities |
| `kit.parse_int(text)` | a typed number, or None (never `isdigit()` + `int()`) |
| `kit.is_hash_of(text, full)` | the player typed this object id, whole or abbreviated |
| `kit.digest(text)`, `kit.answer_is(text, digest)` | store and compare secret answers |
| `kit.in_history(folder, path)` | whether any commit a ref reaches (branches, remote-tracking branches, tags, the stash) holds `path`; read it in `lab.project` and `lab.github` for "the secret is in no capsule, here or on the mothership" |
| `kit.is_ancestor(folder, a, b)`, `kit.reachable(folder, commit)` | whether commit `a` leads to `b`; whether some ref still leads to a commit |
| `kit.setup_github(lab)` | the stand-in GitHub, empty, on `main`, with a reflog (`kit.setup_playground` makes it too) |
| `kit.typed(typed, pattern, outcome)`, `kit.after(typed, pattern)` | whether a line was typed and how it ended; the lines after the last one that worked |
| `kit.on_push(lab, file, text, lines)` | Alex runs shell lines in Alex's clone inside the player's first push that leaves `file` on GitHub's `main` reading `text`: use it instead of a level event when the player's next line must already see Alex's push |
| `kit.switching(branch)`, `kit.creating(branch)` | patterns for those two that accept both forms: `git switch <branch>` or `git checkout <branch>`; `git switch -c <branch>` or `git checkout -b <branch>`. A goal that reads typed lines about moving between branches uses them, never a pattern of its own |
| `kit.type_line(folder, line)` | run a line in bash as the player would, for `solve` and `QUEST_ACTIONS`; returns its `kit.Command` |

### 3.5 Snippets: what git prints outside a terminal

"Predict" cards and "verify" snippets (section 4.1) run with bash, without a terminal, in one
fixed environment (`environment` in `tests/test_decks.py`): an empty folder with the home folder
next to it, the author and committer `Sam Lee <sam@example.com>`, the date 2026-01-15 09:00 UTC,
`LC_ALL=C`, `TERM=dumb`, and only the game's starting global configuration
(`gitcmd.BASE_CONFIG`) plus the settings below that make git print what a terminal shows. So
every hash and line of output a card states is what git really prints, the same on every run.

- Output must be the same on every run and must be text: no `date`, no `ls -l` (it shows
  times), no `$RANDOM`, no binary files printed to the terminal.
- `git clone` saves the absolute path as `origin`, and the folder is a new temporary one each
  run, so a clone that pulls a merge must first run `git remote set-url origin <relative path>`,
  as in 3.2. Otherwise the merge subject, and with it the hash, change every run.

Git prints some things differently without a terminal. Checked on git 2.43 against a real
terminal:

- `log.decorate = short` is set, so `git log`, `git show` and `git reflog` show
  `(HEAD -> main)` and tags as on a terminal (git-config(1): `auto` decorates only there).
- `git merge` and `git pull` open an editor for a merge commit on a terminal, so the snippets
  set `GIT_MERGE_AUTOEDIT=yes` and a plain `git merge topic` that makes a merge commit fails:
  write `--no-edit` or `-m`. `git revert` also opens an editor only on a terminal and cannot be
  made to fail: always write `git revert --no-edit`. `git commit` without `-m` and `git tag -a`
  without `-m` fail in a snippet anyway.
- `git shortlog` with no revision reads its input instead of the history when it is not on a
  terminal: write `git shortlog HEAD`.
- Colours, the pager and progress lines stay off. On a terminal, `push`, `fetch`, `pull` and
  `gc` also print progress (`Enumerating objects`, `Writing objects` with a speed in KiB/s)
  that a snippet does not print, so never quote those lines.
- Everything else a beginner meets prints the same: `init`, `status`, `add`, `commit`,
  `restore`, `rm`, `switch`, `checkout` (with its detached-HEAD advice), `branch`, `diff`,
  `merge` with conflicts, `stash`, `cherry-pick`, `reset`, `clone`, `blame`, `cat-file`.

### 3.6 Testing a level

`tests/test_levels.py` runs, for every level: the module contract, `setup`, a check with no answer
and with wrong answers (both must fail), every quest step's checks against the states a player
passes through, `solve`, a check that passes, the hostile-input list, and the lab cleanup. Put a
level's own tests, such as its wrong-approach feedback, in `tests/levels/test_<chapter>_<slug>.py`.
Then play the level for real in the page, like a player.

What the harness checks, so you know what it will refuse:

- `setup` returns a JSON-serialisable state that has a key for every `{{key}}` in the briefing,
  hints, debrief and steps.
- `check` with no answer and with every answer of the hostile-input list (empty, blank, `"\x00"`,
  `"²"`, `"-1"`, `"9"*5000`, `"word " + "9"*5000`, `--help`, shell syntax, other scripts, 60 000
  characters...) returns a `kit.Verdict` that is not solved, and leaves every file of the lab as
  it was.
- Every answer step refuses the empty answer and the hostile list.
- With `.git` deleted, or the whole project folder deleted, `check` and every step still return a
  `kit.Verdict` instead of raising.
- `solve` then `check` passes, and the lab can be removed.

The quest is walked step by step, as a player would play it. A level with a quest declares the
player's part of each step in `QUEST_ACTIONS`, a module-level name the game reads only in dev
mode (`firstcommit serve --dev`), where a level's page shows its last hint's lines and the answer
of each answer or choice step. An answer action may only read the lab, since dev mode runs it on
the player's live lab. A level that asks its own `QUESTION` also declares `ANSWER(lab, state)`,
which reads that answer from the lab and changes nothing:

```python
def stage_hello(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    kit.git(lab.project, "add", "hello.txt")      # what the player types for this step
    return None                                   # a watch step needs no answer


def look(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    typed.append(kit.type_line(lab.project, "ls"))  # a goal reads this line, so type it for real
    return None


def read_branch(lab: kit.Lab, state: kit.State, typed: list[kit.Command]) -> str | None:
    return kit.git(lab.project, "branch", "--show-current").strip()  # what the player reads and types


QUEST_ACTIONS = {"stage": stage_hello, "look": look, "branch": read_branch}
```

Keys are step ids; every watch step and every answer step needs one (a read step may have one
when the next step depends on it). Each action does what the player would do, with ordinary
commands, and returns the answer to type for an answer step (None otherwise). The harness passes
one list of typed lines through the whole walk, as the game does. For each step in
order, the harness asserts that a watch step fails before its action and passes after it, and
that an answer step refuses the empty answer and accepts the action's answer. So each watch must
notice the very thing its step asks for, and not pass early because of an earlier step.
`kit.typing("git status")` is the action that types one line, the common case, and
`kit.picking(GUESS.options[0])` the one that answers a prediction.

The harness runs the level's `EVENTS` as the game does: those with no goal before the walk and
before `solve`, the others right after their goal's step. A challenge's goals are walked in
quest order too, so order them so that each one is met by its own action: a goal that already
holds at the start is a constraint, and belongs in another goal's text. Setup commits made "by
the player" use `author=kit.PLAYER`, the identity the game's configuration gives the player.
Shared helpers for a level's own tests (start a lab, run its first events, type lines, find a
step, ask Rama) are in `tests/level_helpers.py`.

Two patterns from the Orbit levels (`levels/liftoff_flag.py`, `levels/cargo_first.py`) keep a
level short and consistent:

- **One verdict per goal, reused.** Each watch reads the state its goal is about and says what to
  do next from any state (no repository, a file not staged, a second file staged too...). A later
  goal starts from the earlier goal's verdict, and the mission `check` returns the first goal not
  met, so the advice is the same wherever the player is.
- **`solve` reuses `QUEST_ACTIONS`**: it runs the actions in order, so the reference solution and
  the quest walk cannot drift apart.

## 4. Cards

### 4.1 Format

```toml
notes = """
The chapter's cheat sheet (section 5).
"""

[[card]]
id = "cargo-staging-area"           # "<chapter>-<slug>", unique
kind = "choice"                     # "choice" | "text" | "predict"
level = 1                           # 1 basic, 2 deeper, 3 advanced
prompt = "..."
correct = "..."                     # choice and predict
wrong = ["...", "...", "..."]       # choice and predict: 2 to 5 distractors
explain = """..."""
source = "git-add(1), DESCRIPTION"
verify = """..."""                  # optional bash; exits 0 if the claim holds, 77 if this machine cannot tell

[[card]]
id = "cargo-hello-blob"
kind = "predict"
level = 2
prompt = "What does the last command print?"
code = """
git init -q demo && cd demo
printf 'hello\\n' > hello.txt
git hash-object hello.txt
"""
correct = "ce013625030ba8dba906f756967f9e9ca394464a"
wrong = ["...", "..."]
explain = """..."""
source = "git-hash-object(1)"
```

- **choice**: options are shuffled when shown. Distractors are plausible misconceptions, of the
  same length and style as the right one. The right option may be at most 15 characters longer
  than the longest distractor, and the longest option in at most half of a deck's choice cards
  (the tests enforce both). No "all of the above".
- **predict** and **verify**: the tests run `code` with bash in an empty folder, in the fixed
  environment of section 3.5 (identity, date, `LC_ALL=C`, and the game's starting
  configuration `gitcmd.BASE_CONFIG` as the only global configuration), and
  compare standard output (trailing newlines stripped) with `correct`. They must be
  deterministic and must not depend on git's message wording.
- A **verify** snippet passes only on exit status 0 of its *last* command: bash runs it without
  `-e`, and a `! cmd` line never stops it. Put the claim in the last line (`test ...`,
  `grep -q ...`, `git diff --cached --quiet`), and invert it once by hand to see the snippet fail.
- **text**: short, unambiguous answers; list every reasonable spelling in `accept`.

A deck's Spanish is `<chapter>.es.toml`, with Spanish `notes` and one `[[card]]` per English
card, by `id`: `prompt` and `explain`; for a choice card `correct` and `wrong`, in the English
order (the page still sends, and the game judges, the English option); for a text card
`accept`, the spellings a Spanish speaker may type, and `placeholder` when the English card has
one. A predict card's options are program output and are not translated. Kind, level, source,
code and verify stay in the English deck.

### 4.2 What makes a good card

- Tests understanding: "what happens when...", "why...", "what does this print...".
- Aim at 50% level 1, 40% level 2, 10% level 3.
- `explain` says why the right answer is right and why each tempting wrong one is wrong, in 3-8
  sentences.
- One idea per card. No trick questions: if an expert could argue for two options, rewrite it.

## 5. Notes

One or two screens: the chapter's mental model in a few short paragraphs, then the commands it
taught with one line each. Same correctness bar as everything else.

## 6. Text layout

All text is parsed by `firstcommit.markup` (the page and the command line only render blocks):

- Paragraphs are separated by blank lines and re-wrapped.
- A paragraph whose lines **all** start with whitespace or `$ ` is shown verbatim. Put commands,
  output and file contents there, separated from prose by blank lines.
- Lines starting with `- ` are bullets.
- `backticks` mark commands, file names, branch names and hashes. A code span opened by two or
  more backticks closes on as many, so it can hold a backtick: ``` `` a`b `` ```.
- Anything the player chose (a file name, a branch, a commit subject, a typed answer) goes into a
  message through `kit.code(text)`: it shows as one code span whatever it holds, with control
  characters escaped as git does, so it can never forge a paragraph, a bullet or other code.
- The whole text is dedented first, so a text made *only* of indented lines reads as prose. To
  show output on its own, put one line of prose before it.
- Placeholders are plain text: no backticks.
- Write text flush-left inside its triple quotes. When the first paragraph starts right after
  `"""`, nothing is dedented, so a later paragraph indented to match the code around it becomes
  a verbatim block.

## 7. Words and tone

Beginners learn the words with the ideas, so use one word for one thing, everywhere:

| Say | Not | Git's own term (mention once) |
|---|---|---|
| working folder | working directory, workspace | working tree |
| staging area | stage, cache | index |
| repository | repo (except in commands) | |
| commit (noun and verb) | revision, snapshot (except to explain it) | |
| branch | | branch head |
| hash | SHA, checksum, ID (except to explain it) | object name, object id |

- Define a term the first time it appears in a level; link the idea to what the player just saw.
- Short sentences, active voice. No "simply", "just", "obviously" or "easy".
- English, and Spanish beside it (section 3.7). No emojis.

In Spanish, follow `docs/i18n-glossary.md`: neutral Latin American Spanish, `tú`, the simple
past, and Git's terms in English (commit, push, branch, staging area...). `tests/test_translations.py`
refuses the forms it rules out.
