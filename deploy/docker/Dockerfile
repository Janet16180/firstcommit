# First Commit in a container: Ubuntu 24.04 with the git and Python the levels are checked
# against, and the game's sources copied in. Build it through deploy/docker/run. Two targets:
# "player", the game, and "test", the same image plus uv and the repository, to run the suite.
FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55 AS player

# The base image is minimized: it leaves out manuals and replaces man with a notice. Beginners
# use git help, so manuals come back for the packages installed here (as unminimize does).
#
# The upgrade brings the base image's own packages up to date as well; deploy/docker/run
# repeats this whole step when the image is more than 30 days old.
#
# Ubuntu's archive keeps only the newest build of each package, so exact pins would break the
# build at the next security update. The upstream versions are checked instead. Built
# 2026-10-06 with git 1:2.43.0-1ubuntu7.3, python3.12 3.12.3-1ubuntu0.17, nano 7.2-2ubuntu0.2,
# less 590-2ubuntu2.1, bash-completion 1:2.11-8 and man-db 2.12.0-4build2 on Ubuntu 24.04.5;
# vim 2:9.1.0016-1ubuntu7.20 added 2026-10-08 for the playground, where a player may resolve a
# conflict in vim. Git's own editor stays nano: Ubuntu's "editor" alternative ranks nano above vim.
RUN rm /etc/dpkg/dpkg.cfg.d/excludes /usr/bin/man \
 && dpkg-divert --quiet --remove --rename /usr/bin/man \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get upgrade --yes \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
    git python3 nano vim less bash-completion man-db \
 && rm -rf /var/lib/apt/lists/* \
 && git --version | grep '^git version 2\.43\.' \
 && python3 --version | grep '^Python 3\.12\.'

# While the game's shell runs vim, it hands vim its terminal title in FIRSTCOMMIT_TITLE
# (firstcommit.commands): vim keeps that title, with " insert" added in insert mode, so the page
# can show "Leave typing mode: Esc" then. Ubuntu's /etc/vim/vimrc reads this file.
COPY <<'EOF' /etc/vim/vimrc.local
if !empty($FIRSTCOMMIT_TITLE)
  set title titleold=
  let s:title = escape(substitute($FIRSTCOMMIT_TITLE, '%', '%%', 'g'), ' \')
  execute 'set titlestring=' . s:title
  augroup firstcommit_title
    autocmd!
    autocmd InsertEnter * execute 'set titlestring=' . s:title . '\ insert'
    autocmd InsertLeave * execute 'set titlestring=' . s:title
  augroup END
endif
EOF

RUN useradd --create-home --shell /bin/bash player \
 && install --directory --owner=player --group=player /home/player/.firstcommit

# The source folder may hold __pycache__ folders; they are rebuilt here, since the player cannot
# write next to these files.
COPY src/firstcommit /opt/firstcommit/lib/firstcommit
COPY LICENSE NOTICE /opt/firstcommit/
RUN find /opt/firstcommit/lib -name __pycache__ -prune -exec rm -r {} + \
 && python3 -m compileall -q /opt/firstcommit/lib

# -P keeps the current folder, often a lab the player controls, off the import path.
# -u prints the link at once even when the output is not a terminal.
COPY --chmod=755 <<'EOF' /usr/local/bin/firstcommit
#!/bin/sh
PYTHONPATH=/opt/firstcommit/lib exec python3 -P -u -m firstcommit "$@"
EOF

# firstcommit shell and the page's terminal start $SHELL; docker exec would leave it unset.
ENV LANG=C.UTF-8 HOME=/home/player SHELL=/bin/bash
USER player
WORKDIR /home/player
CMD ["firstcommit", "serve"]


# The repository, as on a developer's machine. Dependencies come from PyPI while building; the
# tests then run offline, on the image's own Python.
FROM player AS test
# Node 24 LTS runs the page's node tests (Ubuntu's nodejs 18 broke one). The release tarball from
# nodejs.org is checked against its SHA-256 from that release's SHASUMS256.txt before unpacking.
ARG NODE_VERSION=24.21.0
ARG NODE_SHA256_X64=fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6
ARG NODE_SHA256_ARM64=6ad1325edbdb5649c379b75a237147a666c95d4f9ae8d340fef2d1575d289ad2
ARG TARGETARCH
USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends ca-certificates curl xz-utils \
 && rm -rf /var/lib/apt/lists/* \
 && case "$TARGETARCH" in \
      amd64) arch=x64 sum=$NODE_SHA256_X64 ;; \
      arm64) arch=arm64 sum=$NODE_SHA256_ARM64 ;; \
      *) echo "no Node build pinned for $TARGETARCH" >&2; exit 1 ;; \
    esac \
 && tarball=node-v$NODE_VERSION-linux-$arch.tar.xz \
 && curl -fsSLo /tmp/$tarball https://nodejs.org/dist/v$NODE_VERSION/$tarball \
 && echo "$sum  /tmp/$tarball" | sha256sum --check --quiet \
 && tar -xJf /tmp/$tarball -C /usr/local --strip-components=1 --no-same-owner \
 && rm /tmp/$tarball \
 && node --version | grep "^v$NODE_VERSION$"
USER player
COPY --from=ghcr.io/astral-sh/uv:0.12.6@sha256:88bc6eb1ccd4b82efd0e1b530caffabddf50dc2bf612e66c14ea25b8ee8a4d3d /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1
COPY --chown=player:player . /home/player/firstcommit
WORKDIR /home/player/firstcommit
RUN uv sync --frozen
ENV UV_NO_SYNC=1 UV_OFFLINE=1
CMD ["sh", "-c", "uv run ruff check && uv run mypy && uv run pytest -q -rs"]
