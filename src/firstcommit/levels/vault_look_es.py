"""Look before you seal in Spanish (`vault_look`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Mira antes de sellar"
CARD = "Muestra las líneas que cambiaste en la carpeta de trabajo y que no están en el staging area. `git diff --staged` muestra lo que se llevará el próximo commit."
SCENE = [
    "Alguien trabajó en la base durante la noche. Antes de sellar nada, mira qué cambió.",
]

BRIEFING = """
Alguien editó dos archivos durante la noche: un cambio es una corrección de verdad, el otro una
errata. Lee los cambios y sella en una cápsula solo la corrección.

La misión termina cuando hayas leído los cambios con `git diff`, hayas dicho qué archivo tiene la
errata, hayas revisado el staging area con `git diff --staged` y un commit nuevo contenga la
corrección y no la errata.
"""

HINTS = [
    "`git diff` muestra cada línea cambiada dos veces: `-` antes, `+` después.",
    "Agrega solo la corrección con `git add route.txt`, revísala con `git diff --staged` y haz el commit.",
    'Cada línea de la misión, en orden:\n\n    $ git diff\n    $ git add route.txt\n    $ git diff --staged\n    $ git commit -m "Add the Phobos stop"',
]

DEBRIEF = """
`git diff` comparó la carpeta de trabajo con el staging area y mostró las dos ediciones. Cuando
la ruta estuvo en el staging area, `git diff --staged` mostró exactamente lo que se llevaría el
commit: la parada nueva, y no la errata. La errata sigue en `engine.cfg`, en la carpeta de
trabajo, sin sellar en ninguna cápsula.

Comandos para recordar:

    $ git diff            # lo que cambió y no está en el staging area
    $ git diff --staged   # lo que se llevará el próximo commit
"""

STEPS = {
    "diff": kit.StepText(text="Lee qué cambió durante la noche."),
    "typo": kit.StepText(text="Encuentra la errata.", question="¿Qué archivo tiene la errata?", placeholder="un nombre de archivo"),
    "stage": kit.StepText(text="Agrega al staging area solo la corrección."),
    "check": kit.StepText(text="Revisa lo que se llevará el próximo commit."),
    "commit": kit.StepText(text="Sella la corrección en una cápsula."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
WAITING = "Todavía no cambió nada. Espera un momento a las ediciones de la noche."
DIFFED = "`git diff` muestra cada línea cambiada: `-` la línea de antes, `+` la de ahora."
NOT_DIFFED = "Primero lee los cambios: escribe `git diff`."
TYPO_FOUND = "Correcto: `power=99999` es la errata. El cambio de la ruta es la corrección de verdad."
ROUTE_IS_FIX = "`route.txt` tiene la corrección: una parada nueva en la ruta. Vuelve a mirar la línea que `git diff` muestra para `engine.cfg`."
NOT_A_FILE = "Escribe el nombre de uno de los dos archivos que muestra `git diff`."
FIX_STAGED = "La corrección está en el staging area, y la errata se queda en la carpeta de trabajo."
FIX_NOT_STAGED = "Agrega al staging area solo la corrección: `git add route.txt`."
TYPO_STAGED = "La errata de `engine.cfg` también está en el staging area. `git restore --staged engine.cfg` la saca; el archivo conserva la edición."
TYPO_SEALED = (
    "La errata de `engine.cfg` ya está en un commit. Deshacer un commit llega en un capítulo posterior: "
    "vuelve a empezar la misión."
)
CHECKED = "`git diff --staged` muestra lo que se llevará el próximo commit: la parada nueva de la ruta, y nada más."
NOT_CHECKED = "Revisa lo que se llevará el próximo commit: `git diff --staged`."
SEALED = "La corrección está sellada en una cápsula, y la errata no está en ninguna."
NOT_SEALED = 'Sella la corrección en una cápsula: `git commit -m "Add the Phobos stop"`.'
EVERYTHING_STAGED = "Eso también agregó la errata al staging area. `git diff --staged` la muestra; `git restore --staged engine.cfg` la vuelve a sacar."
