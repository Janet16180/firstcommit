# First Commit in a container: Ubuntu 24.04 with the git and Python the levels are checked
# against, and the game's and termlab's sources copied in. Build it through deploy/docker/run,
# which passes termlab's folder as the named build context "termlab". Two targets: "player",
# the game, and "test", the same image plus uv and the repository, to run the suite.
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
# less 590-2ubuntu2.1, bash-completion 1:2.11-8 and man-db 2.12.0-4build2 on Ubuntu 24.04.5.
RUN rm /etc/dpkg/dpkg.cfg.d/excludes /usr/bin/man \
 && dpkg-divert --quiet --remove --rename /usr/bin/man \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get upgrade --yes \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
    git python3 nano less bash-completion man-db \
 && rm -rf /var/lib/apt/lists/* \
 && git --version | grep '^git version 2\.43\.' \
 && python3 --version | grep '^Python 3\.12\.'

RUN useradd --create-home --shell /bin/bash player \
 && install --directory --owner=player --group=player /home/player/.firstcommit

# termlab's folder may hold __pycache__ folders; they are rebuilt here, since the player cannot
# write next to these files.
COPY --from=termlab src/termlab /opt/firstcommit/lib/termlab
COPY src/firstcommit /opt/firstcommit/lib/firstcommit
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


# The repository and termlab side by side, as on a developer's machine, so the editable path
# source resolves. Dependencies come from PyPI while building; the tests then run offline, on
# the image's own Python.
FROM player AS test
# Ubuntu's nodejs runs the page's node tests (built 2026-10-06 with nodejs 18.19.1+dfsg-6ubuntu5).
USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*
USER player
COPY --from=ghcr.io/astral-sh/uv:0.12.6@sha256:88bc6eb1ccd4b82efd0e1b530caffabddf50dc2bf612e66c14ea25b8ee8a4d3d /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1
COPY --chown=player:player --from=termlab pyproject.toml README.md /home/player/termlab-firstcommit/
COPY --chown=player:player --from=termlab src /home/player/termlab-firstcommit/src
COPY --chown=player:player . /home/player/firstcommit
WORKDIR /home/player/firstcommit
RUN uv sync --frozen
ENV UV_NO_SYNC=1 UV_OFFLINE=1
CMD ["sh", "-c", "uv run ruff check && uv run mypy && uv run pytest -q -rs"]
