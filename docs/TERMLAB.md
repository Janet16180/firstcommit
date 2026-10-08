# termlab inside First Commit

`src/firstcommit/termlab/` is the game's plumbing: the local web server, the page's terminal, the
save helpers, lab cleanup and the snippet runner. It was copied in on 2026-10-08 from the termlab
library (`~/learning/termlab`, branch `firstcommit`, commit d31e575), which Ring Zero still uses
on its `main`. Changes made here do not flow back to the library, nor the library's to the game.
termlab's VM was left in the library; it assumes termlab is a repository of its own.

## The pieces

| Piece | Module | What it gives the game |
|---|---|---|
| Save helpers | `termlab.store` | an absolute home folder, a lock across processes, atomic JSON files |
| Lab cleanup | `termlab.sandbox` | delete a lab folder, never outside the home, never through a link |
| Snippets | `termlab.snippets` | run the shell snippets a lesson makes claims about, in tests |
| Web server shell | `termlab.web.shell` | a local server: token link, Host and Origin checks, security headers, static files, routes |
| Web terminal | `termlab.web.terminal`, `static/terminal.js` | a real shell in the page: a pty behind a WebSocket, with xterm.js |

`static/client.js` (the access key and the JSON API) is the page's side of the web server shell.

termlab knows nothing of the game: it imports only the standard library and itself
(`tests/test_layers.py` checks it), and every name the game cares about (its home variable, token
header, subprotocol, command, ports) is a setting. The game's rules, levels, records, page and
command line stay out of it.

- **store.** Read, change and write under one `lock`, so the command line and the web server never
  lose each other's update. The file names, the records and their validation are the game's
  (`save.py`).
- **sandbox.** Every deletion of a lab goes through `remove_tree`. The lab layout and the setup and
  teardown order are the game's (`runner.py`).
- **snippets.** A snippet runs in `bash --noprofile --norc`, with no input, in its own session
  (its whole process group is killed on timeout), and with exactly the environment given.
  Output is decoded as text with universal newlines, so a `\r` becomes `\n`.

### Web server shell: `termlab.web.shell`

`web/routes.py` hands it the route table, the terminals' settings and the game's names.

- It binds 127.0.0.1 and prints `http://localhost:PORT/#token=...`. `serve` returns 1 with a hint
  when the port is busy, and 0 after Ctrl-C. Tests use `create_server(0, ...)` and run
  `serve_forever` on a thread.
- Routes are keyed by method (`GET` or `POST`) and a path under `/api/`. `GET /api/terminal`
  belongs to the terminal. `create_server` raises ValueError for a route nobody could reach.
- `more_terminals` serves more terminals beside it, by path (the playground's
  `/api/terminal/playground` and `/api/terminal/playground-alex`), each with its own settings.
  They share one limit: each names the same `max_terminals` as `terminal`, and the server allows
  that many open at once on all paths together.
- A GET route gets the query, first value of each name. A POST route gets the JSON body, or `{}`
  when the body is missing, larger than `max_body`, not JSON or not an object. It returns a status
  and a JSON-serialisable dict.
- Every `/api/` request needs the token header (the terminal's WebSocket carries the key as a
  subprotocol instead), and a POST from another origin is refused. A request without the key, or
  with a foreign Host or Origin, gets a 403; an unknown route a 404.
- `/` serves `static_dir/index.html`, and `/static/<name>` any file directly in `static_dir` or in
  `SHARED_STATIC` (termlab's own `web/static/`). A page file named like a shared one makes
  `create_server` raise.
- Every response carries the security headers. The CSP allows scripts only from the page's own
  files (no inline scripts, no `onclick` attributes), styles from itself, inline styles and
  `style_sources`, and fonts from `font_sources`.

### Web terminal: `termlab.web.terminal`

`environment` and `start_folder` are called for each new terminal, so they follow the game's
state. If either raises, the page gets close code 1011 ("cannot start a shell") and the error goes
to the server's log. `player_env` keeps the server's environment except the variables of the
server's own terminal (`TMUX`, `COLUMNS`, `TERM_PROGRAM` and the like) and the names in `drop`, and
sets `HOME`, `PWD` and `TERM=xterm-256color`. `shell`, when given, is called for each new terminal
and returns the command to run (the game's own bash startup). Closing the page hangs it up.

### The page: `client.js` and `terminal.js`

The page loads xterm.js and these two scripts before its own. Each defines one global.

- `createClient({ header, storageKey, command, timeoutMs = 15000, onLocked })` returns
  `{ token(), api(path, body, timeoutMs) }`. It takes the key from the link's fragment, keeps it in
  localStorage under `storageKey` and removes it from the address bar. `api` POSTs JSON with a
  body and GETs without one, and resolves with the parsed JSON of a 2xx reply. Otherwise the
  Error's `status` is 0 when no reply came in time, 403 when the key was refused (the key is
  forgotten and `onLocked` called), or the HTTP status, with the reply as `data`.
- `createTerminal({ protocol, token, command, looks, storagePrefix, onUnreachable, maxTerminals = 3,
  roomAbove = 300, openFromHeight = 820, labels = {}, path = "/api/terminal", onTitle })` returns
  `{ element, start(), setLook(name, label), setLabels(labels), type(text), run(line), keys(raw), dispose() }`.
  - `looks` maps names to `{ fontFamily, fontSize, theme }`; the first is the default.
  - `labels` gives the words of the status, the toggle and the paste and copy hint:
    `{ connecting, connected, hide, show, hint }`, English for any left out.
  - `type()` types a command without Enter and drops control characters; `run()` does the same,
    then presses Enter once.
  - `keys(raw)` sends keys exactly as given, control keys included, for the game's own buttons
    (Get me out). It trusts its caller: never pass it text the player or a level wrote.
  - `path` opens one of the server's `more_terminals`; give each pane its own `storagePrefix`.
  - `onTitle(title)` hears each title the shell sets (OSC 0 or 2), `""` when cleared.
  - The game styles the pane's classes: `term-dock`, `term-grip`, `term-panel`, `term-head`,
    `term-title`, `term-status` (with `data-state`), `term-actions`, `term-hint`, `term-toggle`,
    `term-host` and `is-closed`.

## Security rules

- **Bind 127.0.0.1 only.** Use `create_server` or `serve`; never start another listener, and never
  forward the port off the machine.
- **The token travels only in the link's fragment**, then in the token header. Never put it in a
  query string, a cookie, a log line, the page's HTML or a URL the page fetches.
- **Host and Origin are compared exactly** with this server's names and port. No regex or wildcard
  allowlists, extra host names or a proxy in front.
- **Validate every body in the route.** A malformed body arrives as `{}`, and any field may have
  any JSON type: check types and ranges and answer 400. Treat the query of a GET the same way.
- **The environment callable decides what the page's shell sees.** Drop the game's own secrets and
  markers from it, and remember the shell runs as the player, with their files.
- **Do not widen the CSP.** Add a style or font source only for a file the page really loads, and
  keep every script in a file.

## Changing it

- Test first, in `tests/test_termlab_<module>.py` and `tests/js/termlab-*.test.js`; the shared
  test site and helpers are in `tests/termlab_helpers.py` and `tests/conftest.py`.
- Keep it standard library only and free of game rules; add a setting only when the game needs a
  value other than today's.
- A change to the web shell, the terminal or the page scripts is security-relevant: have it
  reviewed before merging.
