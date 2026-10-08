"""Two crews meet in Spanish (`conflict_meet`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Dos tripulaciones se encuentran"
CARD = "Trae los commits de un branch al branch donde estás. Cuando los dos avanzaron, Git junta las dos historias en un commit de merge con dos padres; el otro branch se queda donde estaba."
SCENE = [
    "Dos tripulaciones trabajaron por separado: una en la ruta, otra en la lista de la tripulación.",
    "Un merge junta sus historias, en una cápsula con dos padres.",
]

BRIEFING = """
Dos tripulaciones trabajaron por separado. En `scout`, Alex se agregó a la lista de la
tripulación; mientras tanto, tú extendiste la ruta en `main`. Trae el trabajo de Alex a `main`.

La misión termina cuando `main` tenga `scout` con un commit de merge, y hayas mirado la historia
con `git log --oneline --graph`.
"""

HINTS = [
    "`git merge --no-edit scout`: los dos lados tienen commits nuevos, así que Git crea un commit de merge y conserva el mensaje que preparó.",
    "`git log --oneline --graph` dibuja las dos líneas y dónde se juntan.",
    "Cada línea de la misión, en orden:\n\n    $ git merge --no-edit scout\n    $ git log --oneline --graph",
]

DEBRIEF = """
Cada lado tenía commits que al otro le faltaban, así que `git merge --no-edit scout` creó un solo
commit nuevo, un commit de merge con dos padres: tu último commit en `main` y el de Alex en
`scout`. Conservó los dos cambios, la ruta más larga y la lista de la tripulación más larga. No se
copió nada encima de tus archivos, y `scout` sigue donde estaba: un merge no borra ningún branch.

`--no-edit` conserva el mensaje que Git preparó; sin él, Git abre un editor para ese mensaje en una
terminal.

Comandos para recordar:

    $ git merge --no-edit scout      # los dos avanzaron: un commit de merge con dos padres
    $ git log --oneline --graph      # la historia, con sus líneas dibujadas
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="`main` y `scout` tienen cada uno un commit que al otro le falta. ¿Cuántos commits nuevos creará `git merge scout`?",
        options=("Ninguno", "Uno", "Dos"),
        reveal=(
            "Uno: un commit de merge con dos padres, uno en cada línea. Viste el otro caso en Transmisión entrante: "
            "cuando solo un lado avanzó, Git solo mueve la etiqueta y no crea ningún commit."
        ),
    ),
    "merge": kit.StepText(text="Trae `scout` a `main`."),
    "graph": kit.StepText(text="Mira la historia, con sus líneas dibujadas."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_MERGED = "`main` todavía no tiene `scout`. Tráelo: `git merge --no-edit scout`."
PAUSED = "Hay un merge en pausa. Termínalo con `git commit --no-edit`, o vuelve atrás con `git merge --abort`."
MERGED = "`main` tiene `scout` con un commit de merge de dos padres: el trabajo de las dos tripulaciones está en él."
LOOKED = "El gráfico muestra las dos líneas que se juntan en el commit de merge."
NOT_LOOKED = "Mira la historia con sus líneas dibujadas: `git log --oneline --graph`."
