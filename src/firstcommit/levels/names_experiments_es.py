"""A second course in Spanish (`names_experiments`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Un segundo rumbo"
CARD = "Crea un branch nuevo: una etiqueta sobre el commit donde estás. No se copia ningún archivo y sigues en el branch donde estabas."
SCENE = [
    "La base quiere probar un rumbo nuevo sin tocar `main`.",
    "Un branch es una etiqueta sobre una cápsula. `HEAD` es la etiqueta que llevas: tu próxima cápsula la mueve hacia adelante.",
]

BRIEFING = """
El `main` de la base tiene tres commits. Desde el mando piden probar una sonda en un segundo
rumbo y dejar `main` como está.

La misión termina cuando un branch `scout` tenga un commit con `probe.txt` que `main` no tiene,
estés de vuelta en `main` y hayas mirado la carpeta allí con `ls`.
"""

HINTS = [
    "`git branch scout` crea la etiqueta; `git switch scout` te lleva a ella.",
    'En `scout`, escribe el archivo y haz commit: `echo "Probe: launched" > probe.txt && git add probe.txt && git commit -m "Launch the probe"`.',
    "`git switch main` te lleva de vuelta; `ls` muestra qué tiene la carpeta allí.",
    'Cada línea de la misión, en orden:\n\n    $ git branch scout\n    $ git switch scout\n    $ echo "Probe: launched" > probe.txt && git add probe.txt && git commit -m "Launch the probe"\n    $ git switch main\n    $ ls',
]

DEBRIEF = """
`git branch scout` escribió una etiqueta nueva sobre el commit donde estabas: no se copió ningún
archivo. `git switch scout` llevó `HEAD` a esa etiqueta, y tu commit movió `scout` hacia adelante,
mientras `main` se quedó donde estaba.

De vuelta en `main`, Git reescribió la carpeta de trabajo según el último commit de `main`, así
que `probe.txt` salió de ella. No se perdió nada: la sonda está en el commit de `scout`, y
`git switch scout` la trae de vuelta.

En el trabajo, cada tarea tiene su propio branch, así `main` queda como el equipo lo acordó.

Comandos para recordar:

    $ git branch scout   # una etiqueta nueva sobre el commit donde estás
    $ git switch scout   # ve a ella; la carpeta la sigue
    $ git switch main    # y de vuelta
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Estás por crear un branch `scout`. ¿Qué tendrá la carpeta después?",
        options=("Los mismos archivos, una sola vez", "Una segunda copia de los archivos, para scout"),
        reveal="Los mismos archivos, una sola vez. Un branch es una etiqueta sobre un commit: `git branch scout` escribe una etiqueta nueva y no copia ningún archivo.",
    ),
    "branch": kit.StepText(text="Crea un branch `scout`."),
    "switch": kit.StepText(text="Ve a `scout`."),
    "commit": kit.StepText(text="Haz commit de una sonda en `scout`."),
    "back": kit.StepText(text="Vuelve a `main`."),
    "look": kit.StepText(text="Mira la carpeta en `main`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NO_BRANCH = "Todavía no hay un branch `scout`. Créalo: `git branch scout`."
MADE = "`scout` es una segunda etiqueta sobre el commit donde está `main`. La carpeta no cambió."
NOT_ON = "No estás en `scout`. Ve a él: `git switch scout`."
ON = "Estás en `scout`: tu próximo commit mueve su etiqueta hacia adelante."
NOT_COMMITTED = 'Haz commit de la sonda en `scout`: `echo "Probe: launched" > probe.txt && git add probe.txt && git commit -m "Launch the probe"`.'
COMMITTED = "`scout` avanzó al commit de la sonda; `main` se quedó donde estaba."
PROBE_ON_MAIN = "`main` también tiene `probe.txt`: ese commit fue a `main`. Vuelve a empezar la misión y haz commit de la sonda en `scout`."
NOT_BACK = "Vuelve a `main`: `git switch main`."
STILL_THERE = "`probe.txt` sigue en la carpeta, fuera de todo commit de `main`. Bórralo con `rm probe.txt`: `scout` guarda su copia."
BACK_ON_MAIN = "Estás en `main`, y `probe.txt` salió de la carpeta: vive en el commit de `scout`."
LOOKED = "`ls` muestra solo los archivos de `main`. `git switch scout` traería la sonda de vuelta."
NOT_LOOKED = "Mira la carpeta: `ls`."
