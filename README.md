# First Commit

A hands-on game that teaches Git, and how GitHub uses it, to people who are starting out. Every
level explains first, then lets you play: a short lesson, a guided quest in a real terminal, a
challenge, a debrief, and flashcards spaced over the following days.

Everything runs on your own machine. The game keeps its own Git configuration and its own
practice repositories under `~/.firstcommit`; it never touches your repositories or your
`~/.gitconfig`.

## Play

Work in progress: see [docs/DESIGN.md](docs/DESIGN.md).

## Develop

First Commit depends on [termlab](../termlab), which must sit next to this folder
(`~/learning/termlab`).

```
uv sync
uv run pytest -q
uv run ruff check
uv run mypy
eslint src/firstcommit/web/static tests/js
```

Content rules, the level contract and how to verify every claim: [AUTHORING.md](AUTHORING.md).
