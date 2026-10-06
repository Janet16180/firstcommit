# First Commit

A hands-on game that teaches Git, and how GitHub uses it, to people who are starting out. Every
level explains first, then lets you play: a short lesson, a guided quest in a real terminal, a
challenge, a debrief, and flashcards spaced over the following days.

Everything runs on your own machine. The game keeps its own Git configuration and its own
practice repositories under `~/.firstcommit`; it never touches your repositories or your
`~/.gitconfig`.

## Play

Work in progress: see [docs/DESIGN.md](docs/DESIGN.md).

## Play with Docker

The Docker image holds Ubuntu 24.04 with git 2.43 and Python 3.12, the versions every lesson is
checked against, plus the game and termlab. You need Docker Engine installed inside your WSL
Ubuntu ([install guide](https://docs.docker.com/engine/install/ubuntu/)); Docker Desktop has not
been tested. termlab's `firstcommit` branch must sit next to this folder, as for development.

```
deploy/docker/run
```

The first run builds the image, which takes a few minutes. Later runs reuse it and rebuild it by
themselves when the game or termlab changes, and rebuild it from scratch, with Ubuntu's latest
updates, once it is more than 30 days old, so git's security fixes reach you. The game then
prints a link: open it in your Windows browser. Ctrl-C stops the game, and your progress stays.

| Command | What it does |
|---|---|
| `deploy/docker/run` | build the image if needed, then start the game |
| `deploy/docker/run shell` | open a terminal in the running game, with the game's Git settings |
| `deploy/docker/run reset` | delete your saved game and practice repositories (it asks first) |
| `deploy/docker/run build` | build the image without starting the game |
| `deploy/docker/run update` | rebuild the image now from scratch, with Ubuntu's latest updates |
| `FIRSTCOMMIT_PORT=8851 deploy/docker/run` | start the game on another port |
| `deploy/docker/run test` | for developers: run ruff, mypy and the tests inside the container, offline |

Your progress and practice repositories live in the Docker volume `firstcommit-home`, which the
container sees as `~/.firstcommit`. They survive restarts and rebuilds until you run `reset`. If
the game says its port is in use, start it again with another `FIRSTCOMMIT_PORT`: the game's own
hint shows the command for playing without Docker.

**What the container keeps apart.** The game sees only its own files: its volume and the image.
Your WSL home, your repositories and your `~/.gitconfig` are not mounted (the only file shared is
your time zone, read-only, so dates match your clock). The git version is always the image's, and
nothing of your WSL setup (shell configuration, aliases, Git settings) reaches the game. Nothing is
installed in your WSL besides Docker.

**What it does not.** A container is packaging, not a security boundary:

- It shares your WSL's Linux kernel with everything else you run there.
- It shares your WSL's network. The game's server listens on 127.0.0.1 only, and a container with
  its own network could not be reached through that address, so the container uses the host's
  network. The game and the shell in the page can therefore reach every service on your WSL's
  localhost, and everything your WSL can reach.
- Being allowed to use Docker gives root-level power over your WSL: Docker's documentation says
  so about the `docker` group.

The game runs as an ordinary user, `player`, without sudo, without Linux capabilities and without
any way to gain privileges (`--cap-drop ALL`, `no-new-privileges`). For real isolation, a virtual
machine with its own kernel, offline by default, is planned (see [docs/DESIGN.md](docs/DESIGN.md),
section 3).

## Develop

First Commit depends on termlab, on its `firstcommit` branch, checked out next to this folder
as `../termlab-firstcommit`. termlab's `main` stays as Ring Zero uses it. From a termlab clone at
`~/learning/termlab`:

```
git -C ~/learning/termlab worktree add ../termlab-firstcommit firstcommit
```

```
uv sync
uv run pytest -q
uv run ruff check
uv run mypy
eslint src/firstcommit/web/static tests/js
```

Content rules, the level contract and how to verify every claim: [AUTHORING.md](AUTHORING.md).
