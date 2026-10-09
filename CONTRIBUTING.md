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

The owner can use a review exception when merging through a pull request, since GitHub
does not allow authors to approve their own PRs. This exception applies to repository
administrators; @Janet16180 is currently the only administrator. The separate Tests and
CodeQL requirements cannot be bypassed. Direct pushes to main, force pushes, and branch
deletion remain blocked.

After a change lands on `main`, CI reruns the checks. The workflow builds test and player
images only inside the CI runner. It does not publish images, upload build artifacts, or deploy
the game. All workflow jobs use read-only repository permissions.

## Contributions from forks

Fork this repository, create a branch in your fork, and open a pull request to `Janet16180/firstcommit:main`. You do not need write access. The owner reviews and merges changes after the required checks pass. Approval to run an external contributor's workflow is separate from approval to merge their code.

Project code is licensed under Apache 2.0. Contributions intentionally submitted for inclusion are under the same license, unless explicitly stated otherwise. Third-party components retain their original licenses; see NOTICE.
