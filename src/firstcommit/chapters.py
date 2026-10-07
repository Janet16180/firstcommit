"""The chapters of the game, in play order. Keys are the chapter ids used in level and deck file names."""

CHAPTERS: dict[str, str] = {
    "liftoff": "Lift-off",
    "cargo": "The cargo dock",
    "vault": "The time vault",
    "mothership": "The mothership",
    "branch": "Parallel universes",
    "conflict": "Collisions",
    "undo": "Time travel",
    "start": "Git, GitHub and your first clone",
    "rebase": "Keeping up to date",
    "github": "The GitHub flow",
    "hygiene": "What not to commit",
    "setup": "Your real setup",
    "toolbox": "Extra tools",
}

BLURBS: dict[str, str] = {
    "liftoff": "Your first base: what a repository is, and how one starts.",
    "cargo": "The staging area: you choose what goes into your next commit.",
    "vault": "Commits: sealed capsules of your project, and the history they make.",
    "mothership": "Remotes, push and pull: your work safe and shared.",
    "branch": "Branches are labels: work on a second course without touching main.",
    "conflict": "Merges, and what to do when two changes touch the same part of a file.",
    "undo": "Restore, revert, reset and the reflog: take changes back safely.",
    "start": "What Git and GitHub are, and your first clone.",
    "rebase": "Merge or rebase to keep your work up to date.",
    "github": "Branches, pull requests and reviews: the GitHub flow.",
    "hygiene": "What stays out of a repository: generated files, big binaries, secrets.",
    "setup": "Git on your own computer, ready for real work.",
    "toolbox": "Tags, cherry-pick, bisect and other handy tools.",
}
"""One line under each chapter's name on the map, by chapter id, in the order of `CHAPTERS`."""
