# Make First Commit easy to play and add protected CI

First Commit is an educational Git game created with help from AI. This change gives new
players a short path from downloading the project to playing it, and prepares the repository
for reviewed contributions and automated checks.

The README now focuses on `./install.sh`, `./run.sh`, and real screenshots of the mission map,
a guided lesson, the conflict playground, and the field guide. Development and Docker details
live in separate documents. The installer skips apt when its required packages are present,
installs uv, and syncs the locked Python dependencies. Docker setup is optional.

CI scans Git history for credentials, checks the launch scripts, runs lint, type checks, and
the Python and JavaScript tests in the project's Ubuntu test image, then checks the player
image. The workflow runs on pull requests and `main` with read-only permissions; actions and
the scanner are pinned. Container images stay on the CI runner and are not published.

CODEOWNERS assigns all changes to @Janet16180. GitHub rules require passing tests, an up-to-date
branch, resolved review conversations, and the owner's approval. No one can bypass these
rules, force-push, or delete `main`. Because GitHub forbids self-approval, owner-authored PRs
will remain blocked under this policy.

Validation: 3,294 non-Docker tests passed; Ruff and mypy passed; the workflow passed actionlint;
launcher syntax and documentation links passed. A full-history secret scan passed after
reviewing four false positives: an RFC example handshake key and minified xterm class exports.
Docker image validation runs in GitHub Actions.
