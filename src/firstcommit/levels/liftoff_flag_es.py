"""Plant the flag in Spanish (`liftoff_flag`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Planta la bandera"
CARD = "Convierte la carpeta actual en un repositorio nuevo: Git crea dentro la carpeta oculta `.git`."
SCENE = [
    "Esta carpeta es solo una carpeta. Git todavía no guarda ninguna historia de ella.",
    "Con `git init` plantas la bandera: Git crea una carpeta oculta llamada `.git`.",
    "`.git` es la caja negra de la base. Toda la historia vive ahí, así que nunca la borres.",
]

BRIEFING = """
Convierte esta carpeta en un repositorio, para que Git empiece a guardar su historia.

La misión termina cuando la carpeta sea un repositorio, hayas visto su carpeta oculta `.git` con
`ls -a` y `git status` funcione.
"""

HINTS = [
    "El comando que crea un repositorio es `git init`.",
    "Los nombres que empiezan con punto están ocultos. `ls -a` los muestra.",
]

DEBRIEF = """
`git init` creó la carpeta oculta `.git`. A partir de ahora Git puede guardar la historia de esta
carpeta: el repositorio, y cada commit que hagas en él, viven en `.git`.

Comandos para recordar:

    $ git init      # convierte esta carpeta en un repositorio
    $ ls -a         # lista todos los archivos, también los ocultos
"""

STEPS = {
    "init": kit.StepText(text="Planta la bandera: convierte esta carpeta en un repositorio."),
    "hidden": kit.StepText(text="Encuentra la caja negra oculta."),
    "status": kit.StepText(text="Comprueba con `git status` que Git ya conoce la carpeta."),
}

PLANTED = "La bandera está plantada: esta carpeta ya es un repositorio."
NOT_PLANTED = "Esta carpeta todavía no es un repositorio: planta la bandera con `git init`."
SEEN = "Viste `.git`, la carpeta oculta donde Git guarda la historia."
NOT_SEEN = "`.git` está oculta. Lista la carpeta con `ls -a` para verla."
WORKS = "`git status` ya funciona: Git conoce esta carpeta."
NOT_WORKING = "Compruébalo con `git status`: en un repositorio, funciona."
