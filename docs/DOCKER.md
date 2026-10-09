# Play with Docker

Run these commands from the repository root. For the two-command local setup, see [the README](../README.md).


For container play, run `./install.sh --docker`. If it adds you to the `docker` group, open a
new WSL terminal (or run `newgrp docker`) before starting the container.

The Docker image holds Ubuntu 24.04 with git 2.43 and Python 3.12, the versions every level is
checked against, plus the game. You need Docker Engine installed inside your WSL Ubuntu
([install guide](https://docs.docker.com/engine/install/ubuntu/)); Docker Desktop has not been
tested.

```
deploy/docker/run
```

The first run builds the image, which takes a few minutes. Later runs reuse it and rebuild it by
themselves when the game changes, and rebuild it from scratch, with Ubuntu's latest
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
| `deploy/docker/run --dev` | start the game in dev mode, for the people who build it: each level's page shows its solution (`firstcommit serve --dev` without Docker) |
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
machine with its own kernel, offline by default, is planned (see [DESIGN.md](DESIGN.md),
section 3).

