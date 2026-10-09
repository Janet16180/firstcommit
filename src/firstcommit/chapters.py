"""The chapters of the game, in play order. Keys are the chapter ids used in level and deck file names."""

from firstcommit.records import Language

CHAPTERS: dict[str, dict[Language, str]] = {
    "liftoff": {"en": "Lift-off", "es": "Despegue"},
    "cargo": {"en": "The cargo dock", "es": "El muelle de carga"},
    "vault": {"en": "The time vault", "es": "La bóveda del tiempo"},
    "mothership": {"en": "The mothership", "es": "La nave nodriza"},
    "names": {"en": "Name tags", "es": "Etiquetas"},
    "branch": {"en": "Parallel universes", "es": "Universos paralelos"},
    "conflict": {"en": "Collisions", "es": "Colisiones"},
    "undo": {"en": "Time travel", "es": "Viajes en el tiempo"},
    "start": {"en": "Git, GitHub and your first clone", "es": "Git, GitHub y tu primer clon"},
    "rebase": {"en": "Keeping up to date", "es": "Al día con los demás"},
    "github": {"en": "The GitHub flow", "es": "El flujo de GitHub"},
    "hygiene": {"en": "What not to commit", "es": "Lo que no va en un commit"},
    "setup": {"en": "Your real setup", "es": "Tu equipo de verdad"},
    "toolbox": {"en": "Extra tools", "es": "Herramientas extra"},
}
"""Each chapter's name, by chapter id, in each language."""

BLURBS: dict[str, dict[Language, str]] = {
    "liftoff": {
        "en": "Your first base: what a repository is, and how one starts.",
        "es": "Tu primera base: qué es un repositorio y cómo se empieza uno.",
    },
    "cargo": {
        "en": "The staging area: you choose what goes into your next commit.",
        "es": "El staging area: tú eliges qué entra en tu próximo commit.",
    },
    "vault": {
        "en": "Commits: sealed capsules of your project, and the history they make.",
        "es": "Los commits: cápsulas selladas de tu proyecto y la historia que forman.",
    },
    "mothership": {
        "en": "Remotes, push and pull: your work safe and shared.",
        "es": "Remotos, push y pull: tu trabajo a salvo y compartido.",
    },
    "names": {
        "en": "A branch names one commit, HEAD is where you are, origin/main a bookmark.",
        "es": "Un branch nombra un commit, HEAD es donde estás, origin/main un marcador.",
    },
    "branch": {
        "en": "Branches are labels: work on a second course without touching main.",
        "es": "Los branches son etiquetas: sigue otro rumbo sin tocar main.",
    },
    "conflict": {
        "en": "Merges, and what to do when two changes touch the same part of a file.",
        "es": "Los merges, y qué hacer si dos cambios tocan la misma parte de un archivo.",
    },
    "undo": {
        "en": "Restore, revert, reset and the reflog: take changes back safely.",
        "es": "Restore, revert, reset y el reflog: deshaz cambios sin riesgo.",
    },
    "start": {
        "en": "What Git and GitHub are, and your first clone.",
        "es": "Qué son Git y GitHub, y tu primer clon.",
    },
    "rebase": {
        "en": "Merge or rebase to keep your work up to date.",
        "es": "Merge o rebase para tener tu trabajo al día.",
    },
    "github": {
        "en": "Branches, pull requests and reviews: the GitHub flow.",
        "es": "Branches, pull requests y revisiones: el flujo de GitHub.",
    },
    "hygiene": {
        "en": "What stays out of a repository: generated files, big binaries, secrets.",
        "es": "Lo que no entra en un repositorio: archivos generados, binarios, secretos.",
    },
    "setup": {
        "en": "Git on your own computer, ready for real work.",
        "es": "Git en tu propia computadora, listo para trabajar de verdad.",
    },
    "toolbox": {
        "en": "Tags, cherry-pick, bisect and other handy tools.",
        "es": "Tags, cherry-pick, bisect y otras herramientas útiles.",
    },
}
"""One line under each chapter's name on the map, by chapter id, in the order of `CHAPTERS`, in each language."""

PLAY_ORDER: tuple[str, ...] = (
    "liftoff-aboard",
    "liftoff-flag",
    "cargo-first",
    "cargo-selective",
    "cargo-stowaway",
    "cargo-junk",
    "vault-seal",
    "vault-look",
    "vault-recorder",
    "vault-past",
    "vault-inspection",
    "mothership-contact",
    "mothership-launch",
    "mothership-halves",
    "mothership-incoming",
    "mothership-refused",
    "mothership-recruit",
    "mothership-base7",
    "names-tags",
    "names-any",
    "names-experiments",
    "names-step",
    "names-chart",
    "branch-send",
    "branch-switch",
    "branch-ticket",
    "conflict-meet",
    "conflict-abort",
    "conflict-collision",
    "conflict-mergetool",
    "conflict-docking",
    "undo-scrap",
    "undo-recall",
    "undo-erasing",
    "undo-wrong",
    "undo-movelog",
    "undo-blackbox",
)
"""
The game's levels by id, in the order the map shows them, chapter by chapter.

The map numbers each level by its place in its chapter, so this order is the levels' numbers. A
level left out (a test's own level) comes after the listed ones of its chapter, by difficulty,
then id.
"""
