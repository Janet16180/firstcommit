# Contributing to First Commit

First Commit is an educational project. Changes should help someone understand Git through
practice, or make that practice easier to run.

Work on a branch and open a pull request against `main`. Describe the change in plain language,
include a screenshot when the interface changes, and record the checks you ran. Janet is the
sole code owner and reviews contributions. Passing tests do not replace her review.

If you use AI assistance, say what it helped with and verify the result. For lessons, check
the actual Git behavior; a plausible explanation is not enough. The content rules and lesson
contract are in [AUTHORING.md](AUTHORING.md).

## Run the checks

```bash
./install.sh --dev
uv run ruff check
uv run mypy
uv run pytest -q
```

The pytest suite includes the JavaScript tests when Node is installed. CI runs lint, type
checks, and the full suite in the project's Ubuntu 24.04 test image. Tests requiring a Docker
daemon skip inside that image; CI also builds and checks the player image separately.

## Review and delivery

The repository's GitHub rules require the `Tests` check to pass before a PR can merge into
`main`, with the branch up to date. Contributions require approval from @Janet16180. New
commits dismiss older approvals. Force pushes and branch deletion are blocked.

No one may bypass either rule, including the repository owner. GitHub does not allow PR
authors to approve their own PRs, so a PR authored by @Janet16180 cannot merge under this
policy. Changes to repository settings remain under the owner's control.

After a change lands on `main`, CI reruns the checks. A successful run publishes the game
image to `ghcr.io/janet16180/firstcommit`, tagged with the commit SHA and `latest`. Pull
requests have read-only tokens and cannot publish images. The workflow never deploys a public
web server: the game is played locally.
