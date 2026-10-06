# Authoring content for First Commit

First Commit teaches Git to new hires who are starting out: some have never used Git, some have
barely used a terminal. Each chapter is made of:

| Form | Where | Purpose |
|---|---|---|
| Levels | `src/firstcommit/levels/<chapter>_<slug>.py` | Lesson, guided quest and challenge on a real repository |
| Cards | `src/firstcommit/content/cards/<chapter>.toml` | Spaced-repetition flashcards, including "predict the output" |
| Notes | `notes` in the same TOML file | A one-page cheat sheet for the chapter |
| Verification log | `docs/verification/<chapter>.md` | One line per claim, card and level: how it was verified |

Chapter ids are the keys of `src/firstcommit/chapters.py`. Everything a chapter owns starts with
its id, so authors never touch each other's files.

---

## 1. Correctness comes first

A learning game that teaches something false is worse than no game. The target is **Ubuntu
24.04 with its git 2.43** (the Docker image pins it; WSL's Ubuntu 24.04 ships it).

For every sentence that states a fact, in a slide, step, briefing, hint, debrief, card or note:

1. **Check a primary source** and name it in the card's `source` or in the verification log:
   - the installed manual pages: `man git-commit`, `man gitglossary`, `man git` (environment
     variables), `man gitignore`, `man gitattributes`...; quote with
     `man -P cat git-commit | grep -n ...`;
   - git's release notes in `/usr/share/doc/git/RelNotes/` ("since Git 2.23");
   - git-scm.com: the reference and the Pro Git book (2nd edition);
   - docs.github.com for anything about GitHub;
   - FIPS 180-4 for SHA-1 and SHA-256.
2. **Run an experiment** whenever the claim is observable, then make it permanent: a lesson's
   `run` lines, a `predict` card or a `verify` snippet re-check it on every test run.
3. **Do not trust memory** for defaults, flags, numbers, limits or edge cases.
4. **Never quote git's human-readable messages** (hints, errors, `status` wording) in text you
   write: they change between versions. A lesson may *show* them, because its figures come
   from the real git (section 3.5); checks never parse them (section 3.4).
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
   `git commit`").
9. **Every command you write is complete and runnable as written.** `git config --global
   user.name` without a value only reads the setting. Placeholders are obvious and safe to paste
   (`"Your Name"`).
10. **Describe output as the player's terminal shows it.** Some output differs on a terminal:
    `git log --oneline` adds `(HEAD -> main)` there (`log.decorate`, git-config(1)). Lessons show
    terminal output; check prose against a real terminal, not against memory or a pipe.

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

- **Explain before you ask.** The first level of a chapter has a lesson and a guided quest;
  later levels are challenges that reuse what the quest taught.
- **One new idea per level.** Name it in the lesson, practise it in the quest, use it in the
  challenge, explain it again in the debrief.
- **A small story, not trivia**: "a teammate pushed while you were working", "the build folder
  made the repository huge", "you committed on the wrong branch".
- **Real Git only.** The player works on a real repository in a real terminal; the game never
  fakes what git would do.
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
- Run git only through `kit.git` / `kit.git_run` (the game's isolation: the player's own
  configuration can never change a level, and a lab never falls through to a repository above
  it). The player's real `~/.gitconfig` and repositories are never read or changed.
- No hooks, no filters, no aliases that run programs. No root.
- Under 50 MB of disk per lab (the binary-files level included).

### 3.3 Module contract

File `src/firstcommit/levels/<chapter>_<slug>.py`. Its id is the file name with `_` turned into
`-` (`basics_first_commit.py` is `basics-first-commit`), and its chapter is the part before the
first `_`.

```python
from firstcommit import kit

TITLE: str                    # short and concrete: "Your first commit"
DIFFICULTY: int               # 1 first steps, 2 solid, 3 stretch
XP: int                       # guide: 100 for 1, 150-200 for 2, 250-300 for 3
LESSON: list[kit.Slide] = []  # optional; the first level of a chapter has one
QUEST: list[kit.Step] = []    # optional; the first level of a chapter has one
BRIEFING: str                 # the situation and what counts as success
QUESTION: str = ""            # optional; set it when the level is solved by a typed answer
PLACEHOLDER: str = ""         # optional; example shape of that answer ("a short hash")
HINTS: list[str]              # 2-4, from a nudge to almost the answer; each costs XP
DEBRIEF: str                  # shown once solved

def setup(lab: kit.Lab) -> kit.State: ...
def check(lab: kit.Lab, state: kit.State, answer: str | None) -> kit.Verdict: ...
def solve(lab: kit.Lab, state: kit.State) -> str | None: ...
```

- **`setup(lab)`** builds the starting point in `lab.project` (a repository or an empty folder)
  and, for levels with a remote, `lab.github`, then returns a JSON-serialisable state. The lab
  folder exists and is empty. Make commits with `kit.git(..., author=..., when=...)` so their
  hashes are stable when text refers to them, and randomise what the player must find out when
  a fixed answer could be memorised. Store answers as `kit.digest(...)`, never in clear text.
- **`check(lab, state, answer)`** reads the lab and decides. It must not change anything (no
  `add`, no `commit`, no `gc`): read with `kit.snapshot(lab.project)` and read-only commands
  through `kit.git_run`. It is called every couple of seconds while the player works, with
  `answer=None`, and must stay fast and survive any state the player can create: a missing
  folder, a deleted `.git`, a detached HEAD, a merge in progress, garbage answers.
- **`QUESTION`** is for levels whose goal is something the player finds out ("which commit
  introduced the bug?"). Without it, the page offers no answer box and the level is checked
  against the repository only, with `answer=None`.
- **`solve(lab, state)`** is the reference solution the tests use. It plays like a player:
  ordinary git commands through `kit.git` in `lab.project`, never a stored answer. It returns
  the answer to submit, or None for levels checked against the repository.
- **`QUEST`** steps happen in the same lab, in order, and lead to the level's goal, so finishing
  the quest usually solves the level. The server enforces the order. Step kinds (`kit.Step`):
  - an *answer* step has a `question` and `check(lab, state, answer) -> Verdict`;
  - a *watch* step has `watch(lab, state) -> Verdict`, which passes once the lab shows the step
    was done (polled like `check`; same rules);
  - a *read* step has neither.
- Text fields may contain `{{key}}` placeholders, filled from the state.

### 3.4 Reading the lab

`kit.snapshot(path)` returns the repository as the map shows it (`firstcommit.repomap.Snapshot`):
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
| `kit.Person`, `kit.GAME` | commit identities |
| `kit.parse_int(text)` | a typed number, or None (never `isdigit()` + `int()`) |
| `kit.is_hash_of(text, full)` | the player typed this object id, whole or abbreviated |
| `kit.digest(text)`, `kit.answer_is(text, digest)` | store and compare secret answers |

### 3.5 Lessons

A lesson is a list of `kit.Slide`s. Each slide has a short text and an optional `run`: shell
lines added to the lesson's demonstration repository. The game runs every slide's `run` lines
in order in an empty folder, with a fixed identity, date and locale, and only the game's
starting global configuration (`gitcmd.BASE_CONFIG`) plus the settings below that make git
print what a terminal shows. It shows each of the slide's commands with its real output, plus
a figure (`view`): the repository map, the three areas, the object database, the commands
only, or nothing. So every hash and line of output a lesson shows is what git really prints.

- Each non-blank line of `run` is one command. The whole lesson runs in one bash shell, so
  `cd`, variables and `$?` carry over to the next line and the next slide. Keep a command on
  one line (no here-documents, no `if` or `for` spread over lines); join steps with `&&`.
- A line that starts with `! ` is expected to fail (`! git commit -m "x"` before anything is
  staged); any other failing line is a bug in the lesson and fails the tests. So is a `! `
  line that succeeds, a line that ends the shell (`exit`), and a slide that ends outside the
  lesson's home folder.
- The lesson starts in the empty folder `/home/you/project`, with `HOME` at `/home/you`: the
  real folder is temporary, and every path under it is shown under `/home/you`, so two runs
  print the same thing. The author and committer are `Sam Lee <sam@example.com>`, the date is
  2026-01-15 09:00 UTC, with `LC_ALL=C`, `TERM=dumb` and umask 022.
  `firstcommit.demos.environment` defines it; predict cards and verify snippets use the same.
- A command's output is its standard output and error together, in order. A slide's figure
  shows the repository the shell is in after the slide's last line (from a subfolder, the
  repository's top).
- Output must be the same on every run and must be text: no `date`, no `ls -l` (it shows
  times), no `$RANDOM`, no binary files printed to the terminal.
- Write files with plain shell (`echo "hello" > hello.txt`), so the reader can follow along.
- 4-8 slides; one idea each; text of 2-5 short sentences.

Lessons run without a terminal, and git prints some things differently then. Checked on git
2.43 against a real terminal:

- `log.decorate = short` is set, so `git log`, `git show` and `git reflog` show
  `(HEAD -> main)` and tags as on a terminal (git-config(1): `auto` decorates only there).
- Carriage returns are applied as a terminal applies them: `git rebase` leaves only its last
  line, not its `Rebasing (1/1)` counter.
- `git merge` and `git pull` open an editor for a merge commit on a terminal, so the lessons
  set `GIT_MERGE_AUTOEDIT=yes` and a plain `git merge topic` that makes a merge commit fails:
  write `--no-edit` or `-m`, and tell the player about the editor. `git revert` also opens an
  editor only on a terminal and cannot be made to fail: always write `git revert --no-edit`.
  `git commit` without `-m` and `git tag -a` without `-m` fail in a lesson anyway.
- `git shortlog` with no revision reads its input instead of the history when it is not on a
  terminal: write `git shortlog HEAD`.
- Colours, the pager and progress lines stay off. On a terminal, `push`, `fetch`, `pull` and
  `gc` also print progress (`Enumerating objects`, `Writing objects` with a speed in KiB/s)
  that a lesson does not show, so never quote those lines.
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
player's part of each step in `QUEST_ACTIONS`, a module-level name the game itself never reads:

```python
def stage_hello(lab: kit.Lab, state: kit.State) -> str | None:
    kit.git(lab.project, "add", "hello.txt")      # what the player types for this step
    return None                                   # a watch step needs no answer


def read_branch(lab: kit.Lab, state: kit.State) -> str | None:
    return kit.git(lab.project, "branch", "--show-current").strip()  # what the player reads and types


QUEST_ACTIONS = {"stage": stage_hello, "branch": read_branch}
```

Keys are step ids; every watch step and every answer step needs one (a read step may have one
when the next step depends on it). Each action does what the player would do, with ordinary
commands, and returns the answer to type for an answer step (None otherwise). For each step in
order, the harness asserts that a watch step fails before its action and passes after it, and
that an answer step refuses the empty answer and accepts the action's answer. So each watch must
notice the very thing its step asks for, and not pass early because of an earlier step.

## 4. Cards

### 4.1 Format

```toml
notes = """
The chapter's cheat sheet (section 5).
"""

[[card]]
id = "basics-staging-area"          # "<chapter>-<slug>", unique
kind = "choice"                     # "choice" | "text" | "predict"
level = 1                           # 1 basic, 2 deeper, 3 advanced
prompt = "..."
correct = "..."                     # choice and predict
wrong = ["...", "...", "..."]       # choice and predict: 2 to 5 distractors
explain = """..."""
source = "git-add(1), DESCRIPTION"
verify = """..."""                  # optional bash; exits 0 if the claim holds, 77 if this machine cannot tell

[[card]]
id = "basics-hello-blob"
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
- **predict** and **verify**: the tests run `code` with bash in an empty folder, with the same
  fixed environment as the lessons (`demos.environment`: identity, date, `LC_ALL=C`, and the
  game's starting configuration `gitcmd.BASE_CONFIG` as the only global configuration), and
  compare standard output (trailing newlines stripped) with `correct`. They must be
  deterministic and must not depend on git's message wording.
- **text**: short, unambiguous answers; list every reasonable spelling in `accept`.

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
- `backticks` mark commands, file names, branch names and hashes.
- The whole text is dedented first, so a text made *only* of indented lines reads as prose. To
  show output on its own, put one line of prose before it.

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
- English only. No emojis.
