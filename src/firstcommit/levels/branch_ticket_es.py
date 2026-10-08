"""Your first ticket in Spanish (`branch_ticket`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Tu primer ticket"
CARD = "Crea un branch nuevo sobre el commit donde estás y te lleva a él. Los cambios que no tienen commit van contigo."
SCENE = [
    "Tu primer ticket: las luces del pasillo están apagadas. Ya encontraste el arreglo.",
    "La regla de la tripulación: nadie hace commit en `main`. Los arreglos suben en su propio branch, para revisión.",
]

BRIEFING = """
Tu primer ticket: las luces del pasillo están apagadas. Encontraste el arreglo, y `lights.cfg` en
tu carpeta de trabajo ya lo tiene, todavía sin commit. La tripulación nunca hace commit en `main`:
un arreglo sube en su propio branch para revisión. Alex también está trabajando.

La misión termina cuando la nave nodriza tenga un branch `fix-lights` con tu arreglo y su `main`
no tenga ningún commit tuyo, y tu `main` sea igual al de la nave nodriza.
"""

HINTS = [
    "Es la bóveda, la nave nodriza y este capítulo: un commit, un push y un pull, y un branch propio.",
    "Tu cambio todavía no está en ningún branch: un branch nuevo creado ahora lo lleva consigo. Haz commit allí, envía ese branch por su nombre y luego pon tu `main` al día con el de la nave nodriza.",
    'Cada línea de la misión, en orden:\n\n    $ git switch -c fix-lights\n    $ git commit -am "Fix the hall lights"\n    $ git push -u origin fix-lights\n    $ git switch main\n    $ git pull',
]

DEBRIEF = """
`git switch -c fix-lights` creó el branch y se llevó tu cambio sin commit: los cambios que no
tienen commit no pertenecen a ningún branch. Hiciste commit del arreglo allí e hiciste push de
`fix-lights` por su nombre, para que el equipo lo revise, mientras el `main` de la nave nodriza
guardó solo el trabajo del equipo. Después, de vuelta en `main`, un pull trajo el commit de Alex.

Ese es tu primer día de trabajo: un branch por ticket, push por su nombre, y `main` al día con
pull, nunca con commits tuyos.

Comandos para recordar:

    $ git switch -c fix-lights          # un branch nuevo; tus cambios van contigo
    $ git commit -am "Fix the hall lights"
    $ git push -u origin fix-lights     # envía el branch del ticket para revisión
    $ git switch main && git pull       # y mantén main al día
"""

STEPS = {
    "review": kit.StepText(text="La nave nodriza tiene `fix-lights` con tu arreglo, y su `main` no tiene ningún commit tuyo."),
    "level": kit.StepText(text="Tu `main` es igual al de la nave nodriza."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
FIX_LOST = "Tu arreglo de `lights.cfg` no está en ningún commit ni en la carpeta de trabajo: se perdió. Vuelve a empezar la misión."
MAIN_TOUCHED = "El `main` de la nave nodriza tiene un commit tuyo: el arreglo se saltó la revisión. Deshacer un commit llega en un capítulo posterior: vuelve a empezar la misión."
ALEX_DROPPED = "El `main` de la nave nodriza ya no tiene el commit de Alex: un push forzado lo reemplazó. Vuelve a empezar la misión."
MINE_ON_MAIN = "Tu `main` tiene un commit tuyo, y la tripulación nunca hace commit en `main`. Mover un commit a otro branch llega en un capítulo posterior: vuelve a empezar la misión."
WAITING = "Alex todavía está en camino. Espera un momento."
UP_FOR_REVIEW = "La nave nodriza tiene `fix-lights` con tu arreglo, y su `main` no tiene ningún commit tuyo."
NOT_UP = "La nave nodriza todavía no tiene un `fix-lights` con tu arreglo."
LEVEL = "Tu `main` es el de la nave nodriza, con el commit de Alex."
NOT_LEVEL = "Tu `main` todavía no es igual al de la nave nodriza."
FORCED = "`--force` reemplazó un branch de la nave nodriza por el tuyo. En un equipo, eso puede borrar el trabajo de alguien."
UNREVIEWED = (
    "Ese push puso tu arreglo directo en el `main` de la nave nodriza, sin revisión. En un equipo, `main` es lo que todos "
    "traen con pull: el próximo pull de Alex lleva tu commit sin revisar a la estación de Alex."
)
