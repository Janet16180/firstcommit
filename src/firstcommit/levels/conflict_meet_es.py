"""Two crews meet in Spanish (`conflict_meet`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Dos tripulaciones se encuentran"
CARD = "Trae los commits de un branch al branch donde estás. Si el tuyo no tiene nada nuevo, tu etiqueta avanza; si no, Git junta las dos historias en un commit de merge con dos padres."
SCENE = [
    "Dos tripulaciones trabajaron por separado: una en la ruta, otra en la lista de la tripulación.",
    "Un merge junta sus historias. A veces solo mueve una etiqueta; a veces crea una cápsula con dos padres.",
]

BRIEFING = """
Dos tripulaciones trabajaron por separado. `beacon` agregó una baliza encima de `main`; `scout`
agregó a Alex a la lista de la tripulación mientras `main` extendía la ruta. Trae los dos a
`main`.

La misión termina cuando `main` tenga `beacon` por un fast-forward, tenga `scout` con un commit de
merge, y hayas mirado la historia con `git log --oneline --graph`.
"""

HINTS = [
    "Primero `git merge beacon`: `main` no tiene nada que le falte a `beacon`, así que su etiqueta solo avanza.",
    "Luego `git merge --no-edit scout`: los dos lados tienen commits nuevos, así que Git crea un commit de merge y conserva el mensaje que preparó.",
    "`git log --oneline --graph` dibuja las dos líneas y dónde se juntan.",
]

DEBRIEF = """
`git merge beacon` no creó ningún commit: `main` no tenía nada que le faltara a `beacon`, así que
Git solo avanzó la etiqueta `main` hasta el commit de `beacon`. Git llama a eso un fast-forward.

`git merge --no-edit scout` fue distinto: cada lado tenía commits que al otro le faltaban, así que
Git creó un commit de merge con dos padres, uno en cada línea, y conservó los dos cambios: la ruta
más larga y la lista de la tripulación más larga. `--no-edit` conserva el mensaje que Git preparó;
sin él, Git abre un editor para ese mensaje en una terminal.

Comandos para recordar:

    $ git merge beacon               # main sin nada nuevo: la etiqueta avanza
    $ git merge --no-edit scout      # los dos avanzaron: un commit de merge con dos padres
    $ git log --oneline --graph      # la historia, con sus líneas dibujadas
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="`beacon` está un commit adelante de `main`, y `main` no tiene nada que le falte a `beacon`. ¿Cuántos commits nuevos creará `git merge beacon`?",
        options=("Ninguno: la etiqueta avanza", "Un commit de merge"),
        reveal="Ninguno. Cuando tu branch no tiene nada nuevo, `git merge` solo avanza tu etiqueta hasta el commit del otro branch: un fast-forward.",
    ),
    "forward": kit.StepText(text="Trae `beacon` a `main`."),
    "merge": kit.StepText(text="Trae `scout` a `main`."),
    "graph": kit.StepText(text="Mira la historia, con sus líneas dibujadas."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_FORWARDED = "`main` todavía no tiene `beacon`. Tráelo: `git merge beacon`."
FORWARDED = "`main` avanzó hasta el commit de `beacon`: ningún commit nuevo."
MERGED_BEACON = "`beacon` llegó con un commit de merge, porque `main` ya había avanzado. Vuelve a empezar la misión y haz merge de `beacon` primero."
NOT_MERGED = "`main` todavía no tiene `scout`. Tráelo: `git merge --no-edit scout`."
PAUSED = "Hay un merge en pausa. Termínalo con `git commit --no-edit`, o vuelve atrás con `git merge --abort`."
MERGED = "`main` tiene `scout` con un commit de merge de dos padres: el trabajo de las dos tripulaciones está en él."
LOOKED = "El gráfico muestra las dos líneas que se juntan en el commit de merge."
NOT_LOOKED = "Mira la historia con sus líneas dibujadas: `git log --oneline --graph`."
