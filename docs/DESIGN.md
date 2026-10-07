# First Commit: design

A hands-on game that teaches Git, and how GitHub uses it, to new hires who are starting out.
Working title. Built with the method in `~/learning/GAME_METHODOLOGY.md`, on the shared
infrastructure library `termlab` (`~/learning/termlab`, read its `docs/USING.md`), and shaped by
the lessons of Ring Zero's audit (`~/learning/ring0/docs/AUDIT.md`) and architecture review
(`docs/ENGINE_DESIGN.md` on Ring Zero's `docs/engine-design` branch).

Status: draft for review, revised 2026-10-06. Nothing is built yet.

## 1. Goal and audience

New hires with little or no Git. There is no time budget: the game covers everything a new hire
needs, however long that takes. By the end they can commit, read history, undo safely, branch,
merge, resolve a conflict, push, pull, rebase, follow a pull-request flow and set up Git for real
work on WSL. They can also explain two ideas most tutorials skip: what a hash is and why Git is
built on it, and why binary files, generated files and secrets do not belong in a repository.

Every level runs **explain, then play**: a short lesson, a guided quest in a real terminal, a
free challenge, a debrief, then flashcards spaced over the following days.

## 2. Decisions taken

| Decision | Choice |
|---|---|
| Machines | Windows + WSL, Ubuntu 24.04 (git 2.43, Python 3.12) (user, 2026-10-05 and 2026-10-06) |
| Runtimes | The same game runs directly in WSL or in a Docker container now, and in a VM later; the code must not care which (user, 2026-10-06) |
| Infrastructure | termlab provides the save helpers, lab cleanup, snippet runner, web server shell, web terminal and VM; everything else is this game's own (user, 2026-10-06) |
| Length | As long as needed to cover everything (user, 2026-10-06) |
| Style | Prototype a metro map and a time-travel theme on the same first level; the user picks; the other is deleted (user, 2026-10-05) |
| GitHub chapter | Generic GitHub flow, no company-specific rules (user, 2026-10-05) |
| Source | A repo in the company GitHub org; creating it and pushing need the user's go-ahead (user, 2026-10-05) |
| Hosting | Local only: each player runs the game on their own machine. Making the game public is a possibility for the far future; nothing is built for it now (user, 2026-10-06) |

## 3. Runtimes: one game, several hosts

The game is one uv project. It reads two things from where it runs: `FIRSTCOMMIT_HOME` (default
`~/.firstcommit`) and the port. It never asks whether it is in WSL, a container or a VM. Each
runtime is a small adapter outside the package.

| Runtime | How a player starts it | What it gives | Adapter files |
|---|---|---|---|
| WSL, direct | `uv run firstcommit` from a checkout, with termlab next to it | the simplest; developers use it | none |
| Docker | `deploy/docker/run`: builds the image if needed, then `docker run` with a named volume for the game home | Ubuntu 24.04, git, Python, uv and termlab pinned in one image, so players get exactly the git the lessons were checked against; the player's WSL stays untouched | `deploy/docker/Dockerfile`, `deploy/docker/run` |
| VM (later) | `vm/firstcommit-vm create`, then `serve` | a separate kernel: the real isolation option | `vm/game.env`, `vm/guest-setup.sh`, the two-line wrapper (termlab `docs/VM.md`) |

Notes:
- **Docker networking.** termlab's server listens on 127.0.0.1 only and checks the Host header
  (a security rule in USING.md section 4). Tested 2026-10-06 on Docker Engine 28 in WSL: a server
  bound to 127.0.0.1 inside a container is unreachable through `-p`, and reachable with
  `--network host`. So the container runs with host networking, and termlab needs no change.
  The page link and the Host and Origin checks stay the same as in WSL.
- **A container is packaging, not a security boundary.** It keeps the game's files and git
  apart from the player's WSL, but it shares the kernel and, with host networking, the network.
  Ring Zero chose a VM for isolation for this reason. The image runs as a non-root `player` user.
- **One smoke test per runtime**: the same flow (start the server, open a level, solve it
  through the API, check the save) runs in WSL and in the image; the VM joins later.

## 4. Content

| Type | What it is | Where it lives |
|---|---|---|
| Lesson | 4-8 player-paced slides with a diagram each; any command output shown is real (section 6) | the level module |
| Guided quest | 3-6 steps: run this, look, answer a question about what you saw; checked against the live repo | the level module, steps and checks together |
| Mission | A small incident on a real repo ("you committed on the wrong branch"), with a goal; checked automatically | the level module |
| Debrief | Why Git behaves that way, plus "commands to keep" | the level module |
| Cards | choice, text and "predict the output" flashcards, Leitner boxes | `content/cards/<chapter>.toml` |
| Notes | A one-page cheat sheet per chapter | the same TOML file |

A **level** is one module, `firstcommit/levels/<chapter>_<slug>.py`. It owns everything about
itself, and the page has no level-specific code. The first level of each chapter carries the
lesson and the guided quest; later levels are free challenges. Cards aim at 50% basic, 40%
deeper, 10% advanced.

### Chapters

| id | Title | Teaches | Left to |
|---|---|---|---|
| `start` | Git, GitHub and your first clone | what version control is; Git (a tool) vs GitHub (a hosting service); `git clone` from the lab's "GitHub" | |
| `basics` | The three areas | working folder, staging area, commits; `init`, `status`, `add`, `commit`; identity; the editor; good commit messages | history |
| `hash` | Fingerprints | what a hash function is; blobs, trees, commits; `hash-object`, `cat-file`; content addressing, deduplication, integrity; why a commit's hash covers its whole past; short hashes; GitHub shows the same IDs because they are computed from content, not assigned by a server; SHA-1 and SHA-256 | repo size (`hygiene`) |
| `history` | Reading history | `log`, `show`, `diff` (folder, staged, between commits), `HEAD`, `HEAD~1`, `blame` | undoing |
| `undo` | Undo safely | `restore`, `restore --staged`, `commit --amend`, `revert`, `reset` (with care), `reflog` as a safety net; why not to rewrite pushed history | |
| `branch` | Branches are labels | a branch is a name for a commit hash; `branch`, `switch`, `stash`; fast-forward vs merge commit | conflicts |
| `conflict` | Merge conflicts without panic | why they happen, reading the markers, resolving, `merge --abort` | |
| `remote` | Remotes | `remote -v`, `fetch`, `pull`, `push`, upstream branches, `origin/main`, a rejected push | rebase, pull requests |
| `rebase` | Keeping up to date | merge vs rebase, `pull --rebase`, a conflict during a rebase, never rebasing shared history | |
| `github` | The GitHub flow | branch, push, pull request, review, CI checks; what GitHub's merge, squash and rebase buttons produce in Git | |
| `hygiene` | What not to commit | `.gitignore`; binary, large and generated files; secrets; Git LFS; GitHub's size limits | |
| `setup` | Your real setup | keep repos in the Linux filesystem, not `/mnt/c`; line endings and `.gitattributes`; one Git per repo (WSL's, not Git for Windows); your identity; connecting to GitHub (SSH key or HTTPS with a credential helper, `gh auth login`) done for real, outside the game | |
| `toolbox` | Extra tools | tags, `cherry-pick`, `bisect`, `log -S` | |

`rebase`, `setup` and `toolbox` are new in this revision, since the time budget is gone:
`setup` covers what trips new hires up on WSL, and `toolbox` is optional.

The GitHub chapter is honest about its limits: the game cannot open a real pull request. It
explains GitHub's web side with diagrams checked against docs.github.com, and the player
practises the Git underneath for real (push a branch, fetch a reviewer's fix, see the merge
commit that the merge button would create). The `setup` chapter's real steps (a real identity,
a real SSH key) are a checklist the player runs in their own terminal; the game never touches
their real configuration.

### The two topics the user asked for

- **Hashes.** First the idea, with no Git: `sha256sum` on two files that differ by one letter;
  fixed size, deterministic, one-way, collisions possible in theory but impractical to find for
  a secure hash. Then Git: the player computes `sha1("blob 6\0hello\n")` by hand and gets the
  same ID as `git hash-object` (verified 2026-10-05: `ce013625...464a`, and the SHA-256 variant
  too). A hash playground in the page computes the blob ID with the browser's Web Crypto as you
  type, and the server confirms it with real git.
- **Binary files.** Verified by experiment on git 2.43 (2026-10-05), and taught with this nuance:
  Git can delta-compress binary versions when it packs (5 MB random file, 1 byte changed, 3
  commits: 14.7 MB loose, 4.9 MB after `git gc`), but compressed or generated formats change
  almost every byte per edit (gzip with one line changed: about a full copy per version), deleting
  a file never removes it from history, every clone downloads all of it, and binary files cannot
  be diffed or merged. The player measures this with `git count-objects -vH` in a mission.

## 5. Verification model (correctness first)

Git suits this: its state is plain data, and with a fixed author, committer and date its hashes
are deterministic.

- **Missions**: `setup` builds a real repo; `check` reads state through plumbing (`rev-parse`,
  `for-each-ref`, `cat-file`, `status --porcelain=v2`), never porcelain text; `solve` plays like a
  player with ordinary commands. Tests: setup, wrong states rejected, solve, accepted, lab removed.
- **Snippets**: termlab's runner, with one fixed environment (identity, dates, `LC_ALL=C`, no
  global config), runs every lesson slide that shows output, every predict card and every verify
  snippet, so a hash or output printed in the game is re-checked on every test run.
- **Target version**: Ubuntu 24.04's git 2.43, the same in WSL and in the image. The full suite
  runs in both runtimes. Git's hints and messages are never relied on word for word.
- **Sources**: git-scm.com reference and Pro Git, git's release notes, docs.github.com, FIPS 180-4
  for SHA. Plus a fresh fact-checker per chapter (methodology phase 4) and a verification log per
  chapter.

## 6. Safety and isolation model

- **The game shell.** The page's terminal (termlab) and `firstcommit shell` start a shell with
  `GIT_CONFIG_GLOBAL=$FIRSTCOMMIT_HOME/gitconfig`, `GIT_CONFIG_NOSYSTEM=1` and
  `GIT_CEILING_DIRECTORIES=$FIRSTCOMMIT_HOME/labs`. The player's own Git settings (credential
  helpers, `push.autoSetupRemote`, aliases, signing) cannot change what a mission does, and a lab
  never falls through to a repository in a parent folder. Both variables were checked 2026-10-05.
  Whatever the player's own shell, the game shell is bash with the game's startup file, so the
  prompt is the game's (the folder's name, never the user or the host), and each command line
  typed there is logged with its exit status in `$FIRSTCOMMIT_HOME/commands.log` for the figure;
  the log holds only commands typed in the game's own terminal and never leaves the game home.
- **Lab repos pin what their lesson depends on** in their local config (for example
  `push.autoSetupRemote=false` in the upstream mission), so they still behave if the player runs
  git from a normal terminal.
- **"GitHub" is a local bare repository** next to each lab. There is no network, no account and
  no token. The game never touches the player's real repositories or their real `~/.gitconfig`.
- **Writes only under the game home.** Labs are deleted only through termlab's `remove_tree`.
  Budget: under 50 MB of disk per lab. No daemons, no root.
- **Web server and terminal**: termlab's, security-reviewed, used within the rules of its USING.md
  section 4 (validate every body, drop the game's own markers from the shell, no CSP widening).

## 7. Architecture

### Layers

Dependencies point downward only:

```
runtime        WSL (nothing) | deploy/docker/ | vm/ (later)          outside the package
interface      cli.py | web/routes.py, web/static/*                    parse input, render output
orchestration  game.py                                                 every player action, under the save lock
core           levels/*, runner.py, score.py, cards.py, markup.py, gitcmd.py, repomap.py,
               changes.py, demos.py, kit.py
data           save.py (the save's records), records.py (snapshot records), chapters.py
infrastructure termlab: store, sandbox, snippets, web.shell, web.terminal, client.js, terminal.js, VM
```

- `game.py` is the only thing the interfaces call: `status`, `level`, `lesson`, `start`,
  `quest_step`, `check`, `hint`, `observe`, `abort`, `reset`, `due_cards`, `answer_card`,
  `notes`, `shell_environment`, `terminal_folder` and `doctor`. It returns typed records (the
  debrief comes inside `LevelView` and `CheckResult`), raises `UnknownIdError` for an id it does
  not have and `NotPlayingError` when no level is in progress, and re-exports `SaveError` and
  `home`, so an interface never imports `save` or `gitcmd`. Quest progress and the last payout
  live in the save, so the page keeps no game state (only view preferences in `localStorage`),
  and solving from the terminal celebrates correctly. The server also says when the page may
  check a level automatically (`ActiveView.auto_check`).
- `runner.py` reads each level module once into a typed `Level` record and owns the lab
  lifecycle (a fresh lab and its bare "GitHub", cleanup through `termlab.sandbox`).
- `score.py` (pure): ranks, mission reward, hint cost, card XP and streak.
- `cards.py`: loads and validates decks, Leitner scheduling, judging an answer. No printing.
- `markup.py`: the one parser for lesson and debrief text into blocks; the CLI and the page both
  render blocks. `markup.code` writes any text (a file name, a commit subject) as one code span
  that shows it exactly, so a name can never forge the game's own text.
- `gitcmd.py`: every git command the game itself runs: isolated from the player's configuration,
  never running programs a repository names, never opening an editor or asking for a password
  in the terminal.
- `repomap.py`: a snapshot of a repository (commits, parents, refs, HEAD, and the files in the
  folder, the staging area and the last commit), read with plumbing. Each file is also classified
  once, the way `git status` does it (`index_change`, `folder_change`), and the page and the
  levels use that classification instead of comparing areas themselves. The records live in
  `records.py`, so the save can check a saved snapshot. `changes.py` turns two snapshots into the
  "what just happened" events, and `demos.py` runs lesson scripts for the lesson figures.
  The snapshot feeds the live map, which
  is therefore generic: every lab is a Git repo. A mission may also declare its goal as a graph,
  drawn beside the live one (an idea from Learn Git Branching, found by Ring Zero's prior-art
  research).
- `kit.py`: the level authors' toolkit: run git in a lab under the game environment, the fixed
  identity and dates, the three kinds of quest step, the `git status` lists (`untracked`,
  `staged`, `unstaged` and others), `code` for names, answer parsing (short hashes, numbers),
  answer digests.
- `save.py`: the game's records as `TypedDict`s, validated on load, on top of `termlab.store`.
- `web/routes.py`: the route table and terminal settings handed to `termlab.web.shell`; each
  route validates its body (400) and calls one `game` function.

### Axes of change

Orthogonal means each kind of change stays in its own place. This table is the specification;
each phase's review checks the work against it.

| Change | Touches only |
|---|---|
| Add or fix a level | its level module, its cards file, its verification log |
| A scoring rule (XP, hints, ranks, streaks) | `score.py` and its test |
| The look, a theme, the map metaphor | the page's theme and map-renderer files |
| A new player action | `game.py`, one route, one CLI command, the page view that uses it |
| A new runtime (VM, another host) | new files under `deploy/` or `vm/`; nothing in the package |
| Security, terminal or VM plumbing | termlab, with its own review; no game change |
| The save format | `save.py` and its test |
| A git version change | content whose verified output changed, found by the snippet suite |

Enforced by tests:
- an import-graph test: interfaces import only `game`, `markup` and `chapters` from the
  game; core modules import no interface; nothing imports upward; a level imports only `kit`,
  its chapter's helpers and the standard library, minus a short deny-list (processes, network,
  file deletion, dynamic imports: see `tests/test_layers.py`);
- the package never reads anything about its runtime: no `docker`, `qemu` or `wsl` in package
  code, and the smoke test runs unchanged in each runtime;
- every quest question has a check, and every theme covers every level and step id.

### Lessons from Ring Zero, built in from day one

| Ring Zero finding | Rule here |
|---|---|
| ARCH-1, DRY-9: rules in the CLI and the server | every rule below the interfaces; `game.py` is their only entry |
| ENGINE_DESIGN R2: quest progress, auto-check and payout kept in the browser | quest progress and the last payout in the save; the server enforces step order |
| ARCH-7, JS-1, JS-5 to JS-7, decision 5: a level spread over four files and hard-wired in the page | one module per level; the server sends it; the page has no level ids; theme flavour keyed by id |
| ENGINE_DESIGN R4: the mission contract as an untyped module | a typed `Level` record, read once |
| ARCH-6: scoring over four modules | `score.py` |
| ARCH-4, DBC-3, DBC-7: raw dict records, unvalidated save files | `TypedDict` records, validated on load, errors that name the file |
| ARCH-5: the quiz core printed and read input | core modules do no I/O |
| JS-8: markup parsed twice | `markup.py` only; one fixture for pytest and `node --test` |
| ARCH-3, R5: the web built labs through the CLI | labs built in-process (git labs have no daemons to orphan) |
| DBC-2, DBC-8, JS-2, JS-3: unchecked bodies, arguments and replies | validate at each boundary; `client.js` errors carry the HTTP status |
| B4, DRY-1: numbers parsed four ways | `kit` parses every answer |
| B5, DRY-8, TDD-3, ARCH-12, R7 | solved by termlab (`store.home`, `sandbox.remove_tree`, the shell) |
| PY-1, S1: no lint config, no git | git, ruff, mypy strict, ESLint and pinned dev tools from the first commit |
| TDD-2, TDD-12, "6 of 7 reverts stayed green" | one test file per module; property tests; each documented rule has a test that fails when the rule is reverted |
| JS-9, JS-10, JS-12 | small pure page functions under `node --test`; no globals shared between scripts |
| ARCH-10: an unused lock rule | no unlocking; the map suggests an order |

## 8. Look and feel

Two cheap prototypes on the `basics` first level, then the user picks:
- **Metro map**: commits are stations labelled with their real short hash and message, branches
  are coloured lines, a merge is an interchange, HEAD is the "you are here" pin.
- **Time travel**: commits are save points on a timeline, branches are alternate timelines, HEAD
  is the time machine.

Both draw the same `repomap` snapshot, live, as the player types in the terminal. The three areas
(folder, staging area, last commit) appear as a strip under the map. The page should be calm and
very readable for new hires. The metaphor never hides the facts: every drawn object shows its
real name and hash.

## 9. Build plan (methodology phases)

1. Phase 2, lead: the uv project on termlab, tooling, `save`, `score`, `cards`, `markup`, `kit`,
   `runner`, `game`, the routes and page shell, `AUTHORING.md`, the test harness and the Docker
   adapter; then the template level `basics_first_commit` end to end, in WSL and in the image.
   Test-first throughout.
2. Two theme agents build the prototypes on the template level in parallel; the user picks.
3. Security review of this game's routes, terminal environment and container.
4. Chapter authors in parallel (disjoint files), then a fresh fact-checker per chapter as each one
   finishes. Recurring findings become rules in `AUTHORING.md` plus tests.
5. Put it in front of a real beginner, not only the user, and add teaching where they struggle.
6. Release: the company repo, and the VM adapter when the user wants it.

## 10. Open questions

1. **The front door for new hires.** Docker (one command, pinned git; needs Docker Engine in their
   WSL) or WSL direct (needs uv and both repositories)? termlab is a path dependency, so the old
   "`python3 -m firstcommit`, nothing to install" promise is gone either way; the image bakes
   termlab in.
2. **The new chapters** `rebase`, `setup` and `toolbox`: keep, trim or add?
3. **Name**: "First Commit" is a working title.

None of these blocks phase 2: both runtime adapters are planned anyway, and the template level is
in `basics`.

A far-future public release is not designed for. Two habits keep it possible at no cost: content
names no company, person or internal URL (the GitHub chapter is already generic), and third-party
files keep their licences next to them (termlab already ships xterm's).
