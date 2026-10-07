"""The chapters of the game, in play order. Keys are the chapter ids used in level and deck file names."""

CHAPTERS: dict[str, str] = {
    "start": "Git, GitHub and your first clone",
    "basics": "The three areas",
    "hash": "Fingerprints",
    "history": "Reading history",
    "undo": "Undo safely",
    "branch": "Branches are labels",
    "conflict": "Merge conflicts without panic",
    "remote": "Remotes",
    "rebase": "Keeping up to date",
    "github": "The GitHub flow",
    "hygiene": "What not to commit",
    "setup": "Your real setup",
    "toolbox": "Extra tools",
}

BLURBS: dict[str, str] = {
    "start": "What Git and GitHub are, and your first clone.",
    "basics": "The working folder, the staging area and your first commits.",
    "hash": "How Git names every file and commit by its content.",
    "history": "Read the history: what changed, when, and who changed it.",
    "undo": "Take a change back without losing work.",
    "branch": "Branches are names for commits: make them and switch between them.",
    "conflict": "When two changes touch the same lines, and how to settle it.",
    "remote": "Fetch, pull and push: share your history with a remote.",
    "rebase": "Merge or rebase to keep your work up to date.",
    "github": "Branches, pull requests and reviews: the GitHub flow.",
    "hygiene": "What stays out of a repository: generated files, big binaries, secrets.",
    "setup": "Git on your own computer, ready for real work.",
    "toolbox": "Tags, cherry-pick, bisect and other handy tools.",
}
"""One line under each chapter's name on the map, by chapter id, in the order of `CHAPTERS`."""
