# First Commit in a container: Ubuntu 24.04 with the git and Python the lessons are checked
# against, and the game's and termlab's sources copied in. Build it through deploy/docker/run,
# which passes termlab's src folder as the named build context "termlab".
FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55

# The base image is minimized: it leaves out manuals and replaces man with a notice. Beginners
# use git help, so manuals come back for the packages installed here (as unminimize does).
#
# Ubuntu's archive keeps only the newest build of each package, so exact pins would break the
# build at the next security update. The upstream versions are checked instead. Built
# 2026-10-06 with git 1:2.43.0-1ubuntu7.3, python3.12 3.12.3-1ubuntu0.17, nano 7.2-2ubuntu0.2,
# less 590-2ubuntu2.1, bash-completion 1:2.11-8 and man-db 2.12.0-4build2 on Ubuntu 24.04.5.
RUN rm /etc/dpkg/dpkg.cfg.d/excludes /usr/bin/man \
 && dpkg-divert --quiet --remove --rename /usr/bin/man \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
    git python3 nano less bash-completion man-db \
 && rm -rf /var/lib/apt/lists/* \
 && git --version | grep '^git version 2\.43\.' \
 && python3 --version | grep '^Python 3\.12\.'

RUN useradd --create-home --shell /bin/bash player \
 && install --directory --owner=player --group=player /home/player/.firstcommit

# The named context brings termlab's own __pycache__ folders along; they are rebuilt here, since
# the player cannot write next to these files.
COPY --from=termlab termlab /opt/firstcommit/lib/termlab
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
