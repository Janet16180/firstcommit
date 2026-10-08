"""Edits come along in Spanish (`branch_switch`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Los cambios vienen contigo"
CARD = "Te lleva a otro branch y reescribe la carpeta de trabajo para que coincida con él. Los cambios sin commit vienen contigo; Git solo se niega cuando el cambio de branch los sobrescribiría."
SCENE = [
    "Dos rumbos, `main` y `scout`. Tu nuevo ajuste de luces está en la carpeta de trabajo, sin commit.",
    "Un commit pertenece a un branch. Un cambio sin commit todavía no pertenece a ningún branch.",
]

BRIEFING = """
Estás en `main`, y cambiaste el ajuste de luces en `lights.cfg` sin hacer commit. El equipo de
exploración te necesita en `scout`, un branch con una ruta más larga.

La misión termina cuando estés en `scout` con tu cambio de luces, Git se haya negado a un cambio
de branch que sobrescribiría un cambio tuyo, y tus dos cambios estén en un commit en `scout`, con
`main` sin cambios.
"""

HINTS = [
    "`git switch scout` te lleva; `git status` allí muestra si tu cambio vino contigo.",
    'Cambia la ruta en `scout` con `echo "Stop at Phobos" >> route.txt`, y después intenta `git switch main`: `route.txt` es distinto en `main`.',
    'Cada línea de la misión, en orden:\n\n    $ git switch scout\n    $ echo "Stop at Phobos" >> route.txt\n    $ git switch main\n    $ git commit -am "Note the survey route"',
]

DEBRIEF = """
Tu cambio de luces vino contigo a `scout`: un cambio sin commit no pertenece a ningún branch. Se
queda en la carpeta de trabajo mientras cambias de branch, porque `lights.cfg` es igual en los dos
branches y el cambio de branch no tiene nada que sobrescribir.

Tu nota de ruta era distinta. `route.txt` es diferente entre `scout` y `main`, así que volver a
`main` habría reemplazado tu cambio, y Git se negó. Solo se niega para proteger un cambio, y el
cambio se quedó donde estaba.

`git commit -am` puso los dos cambios en un commit en `scout`: ahora pertenecen a ese branch, y
`main` nunca los vio. En el trabajo, haz commit de tus cambios (o descártalos) antes de pasar al
branch de otra persona.

Comandos para recordar:

    $ git switch scout                        # ve a un branch; los cambios sin commit vienen contigo
    $ git commit -am "Note the survey route"  # haz commit de ellos en el branch donde estás
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Pasas a `scout` con `lights.cfg` cambiado y sin commit. ¿Adónde va tu cambio?",
        options=("Se queda atrás, en main", "Viene contigo", "Git lo borra"),
        reveal="Viene contigo: un cambio sin commit no pertenece a ningún branch, así que se queda en la carpeta de trabajo mientras cambias de branch.",
    ),
    "carry": kit.StepText(text="Pasa a `scout`, y mira qué le pasa a tu cambio."),
    "refused": kit.StepText(text="Cambia la ruta en `scout`, y después intenta volver a `main`."),
    "keep": kit.StepText(text="Guarda los dos cambios en `scout`: haz commit de ellos allí."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_ON_SCOUT = "Pasa a `scout`: `git switch scout`."
CARRIED = "Estás en `scout`, y tu cambio de luces vino contigo, todavía sin commit."
LIGHTS_GONE = "Tu cambio de luces desapareció: no estaba en ningún commit, así que nada guardó una copia. Vuelve a empezar la misión."
NOT_REFUSED = 'Cambia la ruta en `scout` (`echo "Stop at Phobos" >> route.txt`), y después intenta `git switch main`.'
REFUSED = "Git se negó a cambiar de branch: `route.txt` es distinto en el otro branch, y el cambio de branch habría sobrescrito tu cambio."
NOT_KEPT = 'Tus cambios todavía no pertenecen a ningún branch. Haz commit de los dos en `scout`: `git commit -am "Note the survey route"`.'
MAIN_TOUCHED = (
    "`main` tiene un commit nuevo, así que los cambios fueron al branch equivocado. Deshacer un commit llega en un "
    "capítulo posterior: vuelve a empezar la misión."
)
KEPT = "Los dos cambios están en un commit en `scout`, y `main` no cambió."
SWITCH_REFUSED = (
    "Git se negó a cambiar de branch: tienes un cambio sin commit, y el otro branch tiene otra versión de ese archivo, así "
    'que cambiar de branch lo sobrescribiría. Dos salidas: haz commit aquí, `git commit -am "Note the survey route"`, '
    "o descarta el cambio, `git restore route.txt`."
)
