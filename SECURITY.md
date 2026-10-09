# Security

Please report a suspected vulnerability privately through GitHub's **Report a vulnerability**
option when it is available. If it is unavailable, contact @Janet16180 through GitHub before
sharing reproduction details in a public issue. Do not include credentials, personal files,
or real repository data in a report.

Include the affected commit or version, the steps to reproduce the issue, and the impact you
observed. This is a personal educational project; fixes and response times depend on the
maintainer's availability.

## Local execution

First Commit starts real shells and runs real Git commands. The game creates practice
repositories under its own game home and uses its own Git settings. It is not a sandbox for
untrusted commands. Keep the server bound to localhost and keep its access link private.

Docker separates the game's files from your checkout, but the supplied launcher shares the
host network and kernel. See [the Docker notes](docs/DOCKER.md) before using it.

## Repository and workflow access

@Janet16180 owns all source files, workflow files, and repository policies. CI runs on GitHub
hosted runners with read-only repository permissions. Publishing is a separate job that runs
only after tests pass on `main`, with write access limited to GitHub Packages. Third-party
actions are pinned to commit SHAs; Dependabot proposes updates for review.

Do not add credentials to the game, tests, screenshots, or documentation. Use repository or
environment secrets only when a workflow needs them, and never give pull-request test jobs
deployment credentials.
