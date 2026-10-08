"""Match the chart in Spanish (`names_chart`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Igual que el mapa"
CARD = "Quita un nombre de un commit; el commit se queda. Git se niega a quitar el nombre donde está `HEAD`: mueve `HEAD` primero."
SCENE = [
    "A la izquierda, tu cadena. A la derecha, el mapa del capitán. Haz que tus nombres coincidan.",
]

BRIEFING = """
Un día nuevo. Durante la noche el capitán guardó tus dos experimentos y borró los demás nombres
de prueba, menos uno: dejaste `HEAD` en `fuel-test`. El mapa muestra cómo deben quedar los nombres
para el lanzamiento. Haz que tu cadena coincida con él. Los commits ya están bien, y tu marcador
`origin/main` también: déjalo.
"""

HINTS = [
    "Compara los dos dibujos nombre por nombre, `HEAD` incluido.",
    "`git branch <name>`, `git branch -d <name>`, `git switch <branch>` y `git switch -c <name>` son todo lo que necesitas. Un nombre nuevo queda donde está `HEAD`.",
    "Cada línea de la misión, en orden:\n\n    $ git switch main\n    $ git branch -d fuel-test\n    $ git branch release\n    $ git switch bright-lights\n    $ git switch -c lights-v2",
]

DEBRIEF = """
No cambió ni un commit: solo se movieron nombres en el árbol. Sacaste `HEAD` de `fuel-test` antes
de quitarlo, pusiste `release` donde estaba `HEAD` y cruzaste a la otra línea lateral antes de
crear `lights-v2`, porque un nombre nuevo siempre queda donde está `HEAD`.

Comandos para recordar:

    $ git switch main             # mueve HEAD fuera de un nombre antes de quitarlo
    $ git branch -d fuel-test     # quita un nombre
    $ git switch -c lights-v2     # un nombre donde está HEAD, y ve a él
"""

STEPS = {
    "chart": kit.StepText(text="Tus nombres coinciden con el mapa del capitán."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
MATCHED = "Tus nombres coinciden con el mapa del capitán, y el dibujo de git en la terminal está de acuerdo: `HEAD -> lights-v2` en el experimento de las luces."
NOT_MATCHED = "Tus nombres todavía no coinciden con el mapa del capitán."
WRONG_SIDE = "`lights-v2` quedó donde estaba `HEAD`, en el commit de `main`. El mapa lo quiere en Try bright lights: ve primero a `bright-lights`."
COMMITS_CHANGED = "El mapa deja cada commit como está. Vuelve a empezar la misión para intentarlo otra vez."
USED_BY_WORKTREE = '"Used by worktree" significa que tu carpeta muestra ese branch: `HEAD` está en él. Git no quita el nombre donde está `HEAD`. Mueve `HEAD` primero.'
