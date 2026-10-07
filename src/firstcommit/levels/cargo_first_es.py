"""First cargo in Spanish (`cargo_first`)."""

from firstcommit import kit

TITLE = "Primera carga"
CARD = "Copia un archivo, tal como está ahora, de la carpeta de trabajo al área de preparación, listo para tu próximo commit."
SCENE = [
    "Cada base de Git tiene tres lugares en tu computadora: la carpeta de trabajo, el área de preparación y el repositorio.",
    "En la carpeta de trabajo trabajas con libertad. Cuando un archivo está listo, `git add` pone una copia suya en el área de preparación.",
    "El área de preparación es el muelle de carga: tú eliges qué sube a él. Los archivos con contraseñas se quedan fuera.",
]

BRIEFING = """
El mapa está listo para guardarse. Ponlo en el área de preparación, y solo el mapa: el diario
todavía no está listo.

La misión termina cuando `map.txt` esté preparado, `journal.txt` no lo esté y hayas mirado con
`git status`.
"""

HINTS = [
    "`git add` recibe el nombre del archivo: `git add map.txt`.",
    "Mira `git status`: lista `map.txt` como preparado para tu próximo commit, y `journal.txt` como sin seguimiento. ¿Por qué?",
]

DEBRIEF = """
`git add` copió el mapa de la carpeta de trabajo al área de preparación. Ahora `git status` lista
`map.txt` como preparado para tu próximo commit, y `journal.txt` como sin seguimiento: un
`git commit` a secas se lleva lo preparado y deja el resto.

Comandos para recordar:

    $ git add map.txt   # prepara un archivo
    $ git status        # mira qué está preparado y qué no
"""

STEPS = {
    "stage": kit.StepText(text="Pon el mapa en el área de preparación."),
    "look": kit.StepText(text="Mira el área de preparación con `git status`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` ha desaparecido. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOADED = "`map.txt` está en el área de preparación, y `journal.txt` se queda en la carpeta de trabajo."
NOT_LOADED = "`map.txt` solo está en la carpeta de trabajo: prepáralo con `git add map.txt`."
TOO_MUCH = (
    "`journal.txt` también está preparado, y esta carga es solo el mapa. `git rm --cached journal.txt` lo saca "
    "del área de preparación; el archivo se queda en la carpeta de trabajo."
)
LOOKED = "`git status` muestra el mapa preparado y el diario sin seguimiento."
NOT_LOOKED = "Ahora mira con `git status`: lista lo que está preparado y lo que no."
EVERYTHING_STAGED = (
    "Eso preparó todos los archivos de la carpeta, también el diario. En esta misión solo entra el mapa: "
    "`git rm --cached journal.txt` vuelve a sacar el diario."
)
NOTHING_TO_RESTORE = (
    "`git restore --staged` vuelve a poner la versión de tu último commit, y este repositorio todavía no tiene ningún commit. "
    "Antes del primer commit, `git rm --cached journal.txt` saca un archivo del área de preparación y lo deja en la carpeta de trabajo."
)
