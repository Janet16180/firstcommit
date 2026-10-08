"""Look before you seal in Spanish (`vault_look`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Mira antes de sellar"
CARD = "Muestra las líneas que cambiaste en la carpeta de trabajo y que no están en el staging area. `git diff --staged` muestra lo que se llevará el próximo commit."
SCENE = [
    "Alguien trabajó en la base durante la noche. Antes de sellar nada, mira qué cambió.",
]

BRIEFING = """
Alguien editó dos archivos durante la noche. La tripulación de la noche dejó una nota: solo
`route.txt` debía cambiar, para agregar una parada. Lee los cambios y sella en una cápsula solo
el cambio de la ruta.

La misión termina cuando hayas leído los cambios con `git diff`, hayas dicho qué archivo cambió
por accidente, hayas revisado el staging area con `git diff --staged` y un commit nuevo contenga
el cambio de la ruta y no el otro.
"""

HINTS = [
    "`git diff` muestra cada línea cambiada dos veces: `-` antes, `+` después.",
    "Agrega solo la ruta con `git add route.txt`, revísala con `git diff --staged` y haz el commit.",
    'Cada línea de la misión, en orden:\n\n    $ git diff\n    $ git add route.txt\n    $ git diff --staged\n    $ git commit -m "Add the Phobos stop"',
]

DEBRIEF = """
`git diff` comparó la carpeta de trabajo con el staging area y mostró las dos ediciones. Cuando
la ruta estuvo en el staging area, `git diff --staged` mostró exactamente lo que se llevaría el
commit: la parada nueva, y no el cambio accidental. Ese cambio sigue en `engine.cfg`, en la
carpeta de trabajo, sin sellar en ninguna cápsula.

En el trabajo, mirar `git diff` antes de cada commit atrapa los cambios que nunca quisiste hacer.

Comandos para recordar:

    $ git diff            # lo que cambió y no está en el staging area
    $ git diff --staged   # lo que se llevará el próximo commit
"""

STEPS = {
    "diff": kit.StepText(text="Lee qué cambió durante la noche."),
    "accident": kit.StepText(text="Encuentra el cambio que nadie pidió.", question="¿Qué archivo cambió por accidente?", placeholder="un nombre de archivo"),
    "stage": kit.StepText(text="Agrega al staging area solo la ruta."),
    "check": kit.StepText(text="Revisa lo que se llevará el próximo commit."),
    "commit": kit.StepText(text="Sella el cambio de la ruta en una cápsula."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
WAITING = "Todavía no cambió nada. Espera un momento a las ediciones de la noche."
DIFFED = "`git diff` muestra cada línea cambiada: `-` la línea de antes, `+` la de ahora."
NOT_DIFFED = "Primero lee los cambios: escribe `git diff`."
ACCIDENT_FOUND = "Correcto: `engine.cfg` cambió por accidente, a `power=85sdfghjkl`. La nota solo pedía la parada nueva de la ruta."
ROUTE_IS_MEANT = "`route.txt` tiene el cambio que pide la nota: una parada nueva. Vuelve a mirar la línea que `git diff` muestra para `engine.cfg`."
NOT_A_FILE = "Escribe el nombre de uno de los dos archivos que muestra `git diff`."
ROUTE_STAGED = "El cambio de la ruta está en el staging area, y el accidental se queda en la carpeta de trabajo."
ROUTE_NOT_STAGED = "Agrega al staging area solo la ruta: `git add route.txt`."
ACCIDENT_STAGED = "El cambio accidental de `engine.cfg` también está en el staging area. `git restore --staged engine.cfg` lo saca; el archivo conserva la edición."
ACCIDENT_SEALED = (
    "El cambio accidental de `engine.cfg` ya está en un commit. Deshacer un commit llega en un capítulo posterior: "
    "vuelve a empezar la misión."
)
CHECKED = "`git diff --staged` muestra lo que se llevará el próximo commit: la parada nueva de la ruta, y nada más."
NOT_CHECKED = "Revisa lo que se llevará el próximo commit: `git diff --staged`."
SEALED = "El cambio de la ruta está sellado en una cápsula, y el accidental no está en ninguna."
NOT_SEALED = 'Sella el cambio de la ruta en una cápsula: `git commit -m "Add the Phobos stop"`.'
EVERYTHING_STAGED = "Eso también agregó el cambio accidental al staging area. `git diff --staged` lo muestra; `git restore --staged engine.cfg` lo vuelve a sacar."
