"""Selective cargo in Spanish (`cargo_selective`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Carga selectiva"
CARD = "Agrega al staging area los archivos que nombras, y solo esos: los demás se quedan en la carpeta de trabajo tal como están."

BRIEFING = """
La próxima carga son los ajustes del motor y la ruta. En la carpeta también está `keys.txt`, con
la contraseña de la esclusa: nunca debe salir de esta base.

La misión termina cuando `engine.cfg` y `route.txt` estén en el staging area, `keys.txt` no lo
esté y hayas mirado con `git status`.
"""

HINTS = [
    "`git add` acepta varios nombres en una misma línea, separados por espacios.",
    "Escribe `git add engine.cfg route.txt` y luego `git status`.",
    "Cada línea de la misión, en orden:\n\n    $ git add engine.cfg route.txt\n    $ git status",
]

DEBRIEF = """
Agregaste los dos archivos al staging area por su nombre, y `keys.txt` se quedó en la carpeta de
trabajo, sin seguimiento. Nombrar los archivos es la forma de elegir qué entra en un commit:
`git add .` también se habría llevado las llaves.

Comandos para recordar:

    $ git add engine.cfg route.txt   # agrega al staging area los archivos que nombras
    $ git rm --cached keys.txt       # saca un archivo del staging area, antes del primer commit
"""

STEPS = {
    "stage": kit.StepText(text="Agrega al staging area los ajustes del motor y la ruta, y solo esos."),
    "look": kit.StepText(text="Mira el staging area con `git status`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOADED = "`engine.cfg` y `route.txt` están en el staging area, y `keys.txt` se queda en la carpeta de trabajo."
NOT_LOADED = "Agrega al staging area los ajustes del motor y la ruta por su nombre: `git add engine.cfg route.txt`."
ONE_MISSING = "Uno de los dos está en el staging area. Agrega también el otro: `git add` recibe su nombre."
KEYS_STAGED = (
    "`keys.txt` está en el staging area, y la contraseña debe quedarse aquí. `git rm --cached keys.txt` lo saca "
    "del staging area; el archivo se queda en la carpeta de trabajo."
)
KEYS_COMMITTED = (
    "`keys.txt` ya está en un commit, así que la contraseña está en la historia de este repositorio. Deshacer un commit "
    "llega en un capítulo posterior: vuelve a empezar la misión."
)
LOOKED = "`git status` muestra el motor y la ruta en el staging area, y las llaves sin seguimiento."
NOT_LOOKED = "Ahora mira con `git status`: lista lo que está en el staging area y lo que no."
EVERYTHING_STAGED = (
    "Eso agregó al staging area todos los archivos de la carpeta, también `keys.txt`. `git rm --cached keys.txt` vuelve a sacar las llaves; "
    "la próxima vez, nombra los archivos que quieres."
)
NOTHING_TO_RESTORE = (
    "`git restore --staged` vuelve a poner la versión de tu último commit, y este repositorio todavía no tiene ningún commit. "
    "Antes del primer commit, `git rm --cached keys.txt` saca un archivo del staging area y lo deja en la carpeta de trabajo."
)
