"""Selective cargo in Spanish (`cargo_selective`)."""

from firstcommit import kit

TITLE = "Carga selectiva"
CARD = "Prepara los archivos que nombras, y solo esos: los demás se quedan en la carpeta de trabajo tal como están."

BRIEFING = """
La próxima carga son los ajustes del motor y la ruta. En la carpeta también está `keys.txt`, con
la contraseña de la esclusa: nunca debe salir de esta base.

La misión termina cuando `engine.cfg` y `route.txt` estén preparados, `keys.txt` no lo esté y
hayas mirado con `git status`.
"""

HINTS = [
    "`git add` acepta varios nombres en una misma línea, separados por espacios.",
    "Escribe `git add engine.cfg route.txt` y luego `git status`.",
]

DEBRIEF = """
Preparaste los dos archivos por su nombre, y `keys.txt` se quedó en la carpeta de trabajo, sin
seguimiento. Nombrar los archivos es la forma de elegir qué entra en un commit: `git add .` se
habría llevado también las llaves.

Comandos para recordar:

    $ git add engine.cfg route.txt   # prepara los archivos que nombras
    $ git rm --cached keys.txt       # saca un archivo del área de preparación, antes del primer commit
"""

STEPS = {
    "stage": kit.StepText(text="Prepara los ajustes del motor y la ruta, y solo esos."),
    "look": kit.StepText(text="Mira el área de preparación con `git status`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` ha desaparecido. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOADED = "`engine.cfg` y `route.txt` están preparados, y `keys.txt` se queda en la carpeta de trabajo."
NOT_LOADED = "Prepara los ajustes del motor y la ruta por su nombre: `git add engine.cfg route.txt`."
ONE_MISSING = "Uno de los dos está preparado. Prepara también el otro: `git add` recibe su nombre."
KEYS_STAGED = (
    "`keys.txt` está preparado, y la contraseña debe quedarse aquí. `git rm --cached keys.txt` lo saca "
    "del área de preparación; el archivo se queda en la carpeta de trabajo."
)
KEYS_COMMITTED = (
    "`keys.txt` ya está en un commit, así que la contraseña está en la historia de este repositorio. Deshacer un commit "
    "llega en un capítulo posterior: vuelve a empezar la misión."
)
LOOKED = "`git status` muestra el motor y la ruta preparados, y las llaves sin seguimiento."
NOT_LOOKED = "Ahora mira con `git status`: lista lo que está preparado y lo que no."
EVERYTHING_STAGED = (
    "Eso preparó todos los archivos de la carpeta, también `keys.txt`. `git rm --cached keys.txt` vuelve a sacar las llaves; "
    "la próxima vez, nombra los archivos que quieres."
)
NOTHING_TO_RESTORE = (
    "`git restore --staged` vuelve a poner la versión de tu último commit, y este repositorio todavía no tiene ningún commit. "
    "Antes del primer commit, `git rm --cached keys.txt` saca un archivo del área de preparación y lo deja en la carpeta de trabajo."
)
